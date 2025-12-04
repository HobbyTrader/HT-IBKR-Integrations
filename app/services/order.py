import time
import logging

from app.data.instrument import Instrument
from app.data.strategy import Strategy

from app.utils.ibapiconnector import IBApiConnector
from app.utils.logger import LoggerManager

from ibapi.utils import iswrapper
from ibapi.order import Order, OrderType, Action    

logger = logging.getLogger(__name__)

class OrderService(IBApiConnector):
    def __init__(self): 
        super().__init__()
        logger.debug("[OrderService] - Order initialzed")
    
    @iswrapper 
    def openOrder(self, orderId, contract, order, orderState):
        return super().openOrder(orderId, contract, order, orderState)
    
    @iswrapper
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId,
                    parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        return super().orderStatus(orderId, status, filled, remaining, avgFillPrice,
                                  permId, parentId, lastFillPrice, clientId,
                                  whyHeld, mktCapPrice)
        
    # def buy_order(self, instrument: Instrument, strategy: Strategy):
    #     logger.info(f"[OrderService] - Placing buy order for {instrument}")
    #     # Implementation of buy order logic goes here
    #     self.placeOrder(self.nextId(),instrument.to_contract(),strategy.to_order())
    
    # def create_stoploss(self, order_candidate):
    #     logger.info(f"[OrderService] - Creating stoploss for {order_candidate}")
    #     # Implementation of stoploss logic goes here
    #     self.placeOrder(self.nextId(),CONTRACT,)
    #     pass    
    
    # def create_takeprofit(self, order_candidate):
    #     logger.info(f"[OrderService] - Creating takeprofit for {order_candidate}")
    #     # Implementation of takeprofit logic goes here
    #     self.placeOrder(self.nextId(),CONTRACT,ORDER)
    #     pass
    
    # Create Braket Order
    def PlaceBracketOrder(self,
        parentOrderId:int, 
        instrument: Instrument,
        strategy: Strategy) -> list[Order]:
        
        quantity = strategy.details.max_shares_to_invest_per_trade
        market_price = instrument.get_market_price()

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
        takeProfit.orderId = parent.orderId + 1
        takeProfit.action = "SELL"
        takeProfit.orderType = "LMT"
        # Sell 100% at take profit limit price
        takeProfit.totalQuantity = quantity
        # Based on the buy price and the strategy
        takeProfit.lmtPrice = strategy.get_take_profit_price(market_price)  # Placeholder for buy price
        takeProfit.parentId = parentOrderId
        takeProfit.transmit = False

        stopLoss = Order()
        stopLoss.orderId = parent.orderId + 2
        stopLoss.action = "SELL"
        stopLoss.orderType = "STP"
        #Stop trigger price
        # Based on the market price and the strategy
        stopLoss.auxPrice = strategy.get_stop_loss_price(market_price)  # Placeholder for buy price
        stopLoss.totalQuantity = quantity
        stopLoss.parentId = parentOrderId
        #In this case, the low side order will be the last child being sent. Therefore, it needs to set this attribute to True
        #to activate all its predecessors
        stopLoss.transmit = True
        
        contract = instrument.to_contract()

        self.placeOrder(parent.orderId, contract, parent)
        self.placeOrder(takeProfit.orderId, contract, takeProfit)
        self.placeOrder(stopLoss.orderId, contract, stopLoss)