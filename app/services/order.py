import time
import logging

from app.data.instrument import Instrument
from app.data.strategy import Strategy

from app.utils.ibapiconnector import IBApiConnector
from app.utils.logger import LoggerManager

from ibapi.utils import iswrapper
from ibapi.order import Order   

logger = logging.getLogger(__name__)

class OrderService(IBApiConnector):
    def __init__(self): 
        super().__init__()
        logger.debug("[OrderService] - Order initialzed")
    
    @iswrapper  
    def nextValidId(self, orderId: int):
        self.orderId = orderId
        logger.debug(f"[OrderService] - Next Valid Id: {orderId}.")
    
    @iswrapper 
    def openOrder(self, orderId, contract, order, orderState):
        # TODO: Add order in database for watcher
        return super().openOrder(orderId, contract, order, orderState)
    
    @iswrapper
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId,
                    parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        return super().orderStatus(orderId, status, filled, remaining, avgFillPrice,
                                  permId, parentId, lastFillPrice, clientId,
                                  whyHeld, mktCapPrice)
        
       
    # Create Braket Order
    def PlaceBracketOrder(self,
        instrument: Instrument):
        
        parentOrderId = self.nextId()
        # Define quantity based on strategy and on volume exchanged
        quantity = instrument.volume_buy

        #This will be our main or “parent” order
        parent = Order()
        parent.orderId = parentOrderId
        parent.action = "BUY"
        # Buy market price!!!
        parent.orderType = "MKT"
        # Define quantity from the strategy
        parent.totalQuantity = quantity
        #The parent and children orders will need this attribute set to False to prevent accidental executions.
        #The LAST CHILD will have it set to True,
        parent.transmit = False

        takeProfit = Order()
        takeProfit.orderId = self.nextId()
        takeProfit.action = "SELL"
        takeProfit.orderType = "LMT"
        # Sell 100% at take profit limit price
        takeProfit.totalQuantity = quantity
        # Based on the buy price and the strategy
        takeProfit.lmtPrice = instrument.take_profit_price  # Placeholder for buy price
        takeProfit.parentId = parentOrderId
        takeProfit.transmit = False

        stopLoss = Order()
        stopLoss.orderId = self.nextId()
        stopLoss.action = "SELL"
        stopLoss.orderType = "STP"
        #Stop trigger price
        # Based on the market price and the strategy
        stopLoss.auxPrice = instrument.stop_loss_price  # Placeholder for buy price
        stopLoss.totalQuantity = quantity
        stopLoss.parentId = parentOrderId
        #In this case, the low side order will be the last child being sent. Therefore, it needs to set this attribute to True
        #to activate all its predecessors
        stopLoss.transmit = True
        
        contract = instrument.to_contract()

        self.placeOrder(parent.orderId, contract, parent)
        self.placeOrder(takeProfit.orderId, contract, takeProfit)
        self.placeOrder(stopLoss.orderId, contract, stopLoss)