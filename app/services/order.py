import time
import logging
import threading

from app.data.instrument import Instrument
from app.data.strategy import Strategy
from app.data.market_order import MarketOrder

from app.dto.market_order_dto import MarketOrderDTO

from app.utils.ibapiconnector import IBApiConnector

from ibapi.utils import iswrapper
from ibapi.order import Order   

logger = logging.getLogger(__name__)

class OrderService(IBApiConnector):
    def __init__(self, clientId : int=0): 
        super().__init__()
        self.order_events = {}
        self.CLIENT_ID = clientId
        logger.info(f"[OrderService] - Order initialzed - Client ID: {clientId}")
        
    def store_order(self, order: Order, instrument: Instrument):
        order_dto = MarketOrderDTO()
        market_order = MarketOrder()
        market_order.from_order(order, instrument)
        
        logger.info(f"[OrderService] - START - Stored order in DB: {market_order}" )
        
        t = threading.Thread(
            target=order_dto.save_market_order, args=(market_order,)
        )
        t.start()
        
        logger.info(f"[OrderService] - Stored order in DB: {market_order}" )
    
    @iswrapper  
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.orderId = orderId
        logger.debug(f"[OrderService] - END - Next Valid Id: {orderId}.")
    
    @iswrapper 
    def openOrder(self, orderId, contract, order, orderState):
        logger.info(f"[OrderService] - Open Order. orderId: {orderId}, contract: {contract}, order: {order}, orderState: {orderState}.")
        
        # TODO: Add order in database for watcher
        return super().openOrder(orderId, contract, order, orderState)
    
    @iswrapper
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId,
                    parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        logger.info(f"[OrderService] - Order Status. orderId: {orderId}, status: {status}, filled: {filled}, remaining: {remaining}, avgFillPrice: {avgFillPrice}, permId: {permId}, parentId: {parentId}, lastFillPrice: {lastFillPrice}, clientId: {clientId}, whyHeld: {whyHeld}, mktCapPrice: {mktCapPrice}.")
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice,
                                  permId, parentId, lastFillPrice, clientId,
                                  whyHeld, mktCapPrice)
        # Mark order as confirmed (Submitted/Filled/PreSubmitted)
        if orderId in self.order_events and status in ['Submitted', 'Filled', 'PreSubmitted']:
            self.order_events[orderId].set()  # Signal completion
            logger.debug(f"Order {orderId} confirmed: {status}")
        
       
    # Create Braket Order
    def PlaceBracketOrder(self,
        instrument: Instrument):
        events = []
        # Define quantity based on strategy and on volume exchanged
        quantity = int(instrument.volume_buy)
        
        contract = instrument.to_contract()
        parentOrderId = self.nextId()

        #This will be our main or “parent” order
        parent = Order()
        parent.orderId = parentOrderId
        parent.action = "BUY"
        # Buy market price!!!
        parent.orderType = "MKT"
        
        # Buy at Limit price
        # parent.orderType = "LMT"
        # parent.lmtPrice = instrument.market_price  # Placeholder for buy price
        
        # Define quantity from the strategy
        parent.totalQuantity = quantity
        #The parent and children orders will need this attribute set to False to prevent accidental executions.
        #The LAST CHILD will have it set to True,
        parent.transmit = False
        buy_events = threading.Event()
        self.order_events[parent.orderId] = buy_events
        events.append(buy_events)
        
        self.store_order(parent, instrument)
        
        self.placeOrder(parent.orderId, contract, parent)

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
        
        target_events = threading.Event()
        self.order_events[takeProfit.orderId] = target_events
        events.append(target_events)
        
        self.store_order(takeProfit, instrument)
        
        self.placeOrder(takeProfit.orderId, contract, takeProfit)

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
        
        stop_events = threading.Event()
        self.order_events[stopLoss.orderId] = stop_events
        events.append(stop_events)
        
        self.store_order(stopLoss, instrument)
        
        self.placeOrder(stopLoss.orderId, contract, stopLoss)
        
        # Wait for ALL 3 orders to be confirmed (10s timeout each)
        logger.info("Waiting for all 3 orders to be confirmed...")
        # for i, event in enumerate(events):
        for i, event in self.order_events.items():
            success = event.wait(timeout=10.0)
            if not success:
                logger.error(f"Order {i} timeout!")
                # self.cancelOrder(parent.orderId, parent)
                # self.cancelOrder(takeProfit.orderId)
                # self.cancelOrder(stopLoss.orderId)
                time.sleep(2)
                # raise TimeoutError("Order confirmation timeout")
                
        # Cleanup
        for order_id in [parent.orderId, stopLoss.orderId, takeProfit.orderId]:
            self.order_events.pop(order_id, None)

        
        