import time
import logging
import threading

from app.data.instrument import Instrument
from app.data.market_order import MarketOrder

from app.dto.market_order_dto import MarketOrderDTO

from app.utils.ibapiconnector import IBApiConnector

#from vendor.ibapi.order_cancel import OrderCancel
#from vendor.ibapi.utils import iswrapper
#from vendor.ibapi.order import Order   
#from vendor.ibapi.contract import Contract
from ibapi.order_cancel import OrderCancel
from ibapi.utils import iswrapper
from ibapi.order import Order   
from ibapi.contract import Contract



logger = logging.getLogger(__name__)

class OrderService(IBApiConnector):
    def __init__(self, clientId : int=0): 
        super().__init__()
        self.order_events = {}
        self.CLIENT_ID = clientId
        self.order_dto = MarketOrderDTO()
        logger.info(f"[OrderService] - Order initialzed - Client ID: {clientId}")
        
    def store_order(self, order: Order, instrument: Instrument):
        market_order = MarketOrder()
        market_order.from_order(order, instrument.id, instrument.symbol, instrument.strategy_id, instrument.currency)
        
        logger.debug(f"[OrderService] - START - Stored order in DB: {market_order}" )
        
        t = threading.Thread(
            target=self.order_dto.save_market_order, 
            args=(market_order,)
        )
        t.start()
        
        logger.debug(f"[OrderService] - Stored order in DB: {market_order}" )
        
    def store_sell_order(self, order: Order, contract: Contract, strategy_id: int):
        market_order = MarketOrder()
        market_order.from_order(order, contract.conId, contract.symbol, strategy_id, contract.currency)
        
        logger.debug(f"[OrderService] - START - Stored SELL order in DB: {market_order}" )
        
        t = threading.Thread(
            target=self.order_dto.save_market_order, 
            args=(market_order,)
        )
        t.start()
        
        logger.debug(f"[OrderService] - Stored SELL order in DB: {market_order}" )
        
    def update_order(self, order: Order):
        logger.debug(f"[OrderService] - START - Update order in DB: {order.orderId}" )
        
        t = threading.Thread(
            target=self.order_dto.update_market_order,
            args=(order,)
        )
        t.start()
        
        logger.debug(f"[OrderService] - Update order in DB: {order.orderId}" )
    
    # ============================================================================
    # IBKR WRAPPER CALLBACKS
    # ============================================================================
    @iswrapper  
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.orderId = orderId
        logger.debug(f"[OrderService] - END - Next Valid Id: {orderId}.")
    
    @iswrapper 
    def openOrder(self, orderId, contract, order, orderState):
        logger.info(f"[OrderService] - Open Order. orderId: {orderId}, contract: {contract}, order: {order}, orderState: {orderState}.")
        
        t = threading.Thread(
            target=self.order_dto.update_market_order_status,
            args=(orderId, orderState.status)
        )
        t.start()
        
        return super().openOrder(orderId, contract, order, orderState)
    
    @iswrapper
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId,
                    parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        logger.info(f"[OrderService] - Order Status. orderId: {orderId}, status: {status}, filled: {filled}, remaining: {remaining}, avgFillPrice: {avgFillPrice}, permId: {permId}, parentId: {parentId}, lastFillPrice: {lastFillPrice}, clientId: {clientId}, whyHeld: {whyHeld}, mktCapPrice: {mktCapPrice}.")
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice,
                                  permId, parentId, lastFillPrice, clientId,
                                  whyHeld, mktCapPrice)
        
        t = threading.Thread(
            target=self.order_dto.update_market_order_status,
            args=(orderId, status)
        )
        t.start()
        
        # Mark order as confirmed (Submitted/Filled/PreSubmitted)
        if orderId in self.order_events and status in ['Submitted', 'Filled', 'PreSubmitted']:
            self.order_events[orderId].set()  # Signal completion
            logger.debug(f"Order {orderId} confirmed: {status}")
    
    @iswrapper
    def completedOrder(self, contract, order, orderState):
        logger.info(f"[OrderService] - Completed Order. contract: {contract}, order: {order}, orderState: {orderState}.")
        t = threading.Thread(
            target=self.order_dto.update_market_order_status,
            args=(order.orderId, orderState.status)
        )
        t.start()
        return super().completedOrder(contract, order, orderState)
    
    @iswrapper
    def completedOrdersEnd(self):
        logger.info(f"[OrderService] - Completed Orders End.")
        return super().completedOrdersEnd()
    
    # ============================================================================
    # ORDER CREATION METHODS
    # ============================================================================
    def create_parent_order_MKT(self, orderId: int, quantity: int) -> Order:
        parent = Order()
        parent.orderId = orderId
        parent.action = "BUY"
        parent.orderType = "MKT"
        parent.totalQuantity = quantity
        parent.transmit = False
        return parent   
    
    def create_parent_order_LMT(self, orderId: int, instrument: Instrument, quantity: int) -> Order:
        parent = Order()
        parent.orderId = orderId
        parent.action = "BUY"
        parent.orderType = "LMT"
        parent.lmtPrice = instrument.market_price  # Placeholder for buy price
        parent.totalQuantity = quantity
        parent.transmit = False
        return parent   
    
    def create_target_order_LMT(self, instrument: Instrument, quantity: int, parentOrderId: int) -> Order:
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
        return takeProfit
    
    def create_stop_order_STP(self, instrument: Instrument, quantity: int, parentOrderId: int) -> Order:
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
        return stopLoss
    
    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================
    # Create Bracket Order
    def place_bracket_order(self,
        instrument: Instrument):
        events = []
        # Define quantity based on strategy and on volume exchanged
        quantity = int(instrument.volume_buy)
        
        contract = instrument.to_contract()
        parentOrderId = self.nextId()

        #This will be our main or “parent” order with MKT type
        parentOrder = self.create_parent_order_MKT(parentOrderId, quantity)
        
        # This will be our main or “parent” order with LMT type (not used for the moment)
        # parent = self.create_parent_order_LMT(parentOrderId, instrument, quantity)
        
        buy_events = threading.Event()
        self.order_events[parentOrder.orderId] = buy_events
        events.append(buy_events)        
        self.store_order(parentOrder, instrument)        
        self.placeOrder(parentOrder.orderId, contract, parentOrder)

        #This will be our “take profit” order, a LMT order to sell at a higher price
        targetOrder1 = self.create_target_order_LMT(instrument, int(quantity/3), parentOrderId)
        targetOrder1.lmtPrice = targetOrder1.lmtPrice - 0.05  # Adjust take profit price for first target
        targetOrder2 = self.create_target_order_LMT(instrument, int(quantity/3), parentOrderId)
        targetOrder2.lmtPrice = targetOrder2.lmtPrice - 0.02 # Standard take profit price for second target
        targetOrder3 = self.create_target_order_LMT(instrument, quantity - 2*(int(quantity/3)), parentOrderId)
        
        target_events1 = threading.Event()
        self.order_events[targetOrder1.orderId] = target_events1
        events.append(target_events1)        
        self.store_order(targetOrder1, instrument)        
        self.placeOrder(targetOrder1.orderId, contract, targetOrder1)
        
        # target_events2 = threading.Event()
        # self.order_events[targetOrder2.orderId] = target_events2
        # events.append(target_events2)        
        # self.store_order(targetOrder2, instrument)        
        # self.placeOrder(targetOrder2.orderId, contract, targetOrder2)       
        
        # target_events3 = threading.Event()
        # self.order_events[targetOrder3.orderId] = target_events3
        # events.append(target_events3)        
        # self.store_order(targetOrder3, instrument)        
        # self.placeOrder(targetOrder3.orderId, contract, targetOrder3)
        
        #This will be our “stop loss” order, a STP order to sell at a lower price
        stopLossOrder = self.create_stop_order_STP(instrument, quantity, parentOrderId)
        
        stop_events = threading.Event()
        self.order_events[stopLossOrder.orderId] = stop_events
        events.append(stop_events)        
        self.store_order(stopLossOrder, instrument)        
        self.placeOrder(stopLossOrder.orderId, contract, stopLossOrder)
        
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
        for order_id in [parentOrder.orderId, stopLossOrder.orderId, targetOrder1.orderId]:
            self.order_events.pop(order_id, None)

    def sell_open_position(self, contract: Contract, quantity: int, strategy_id: int):
        sellOrderId = self.nextId()
        
        sellOrder = Order()
        sellOrder.orderId = sellOrderId
        sellOrder.action = "SELL"
        sellOrder.orderType = "MKT"
        sellOrder.totalQuantity = quantity
        sellOrder.transmit = True
        
        sell_events = threading.Event()
        self.order_events[sellOrder.orderId] = sell_events   
        self.placeOrder(sellOrder.orderId, contract, sellOrder)     
        self.store_sell_order(sellOrder, contract, strategy_id)        
        
        logger.info(f"Waiting for sell order {sellOrder.orderId} to be confirmed...")
        success = sell_events.wait(timeout=10.0)
        if not success:
            logger.error(f"Sell order {sellOrder.orderId} timeout!")
            time.sleep(2)
        
        # Cleanup
        self.order_events.pop(sellOrder.orderId, None)

    def get_active_orders(self):
        # Placeholder for fetching active orders from IBKR
        logger.info("[OrderService] - Fetching active orders...")
        self.reqAllOpenOrders() 
        
    def get_comlpeted_orders(self):
        # Placeholder for fetching completed orders from IBKR
        logger.info("[OrderService] - Fetching completed orders...")
        self.reqCompletedOrders()
        
    def cancel_all_orders(self):
        # Placeholder for cancelling all orders in IBKR
        logger.info("[OrderService] - Cancelling all orders...")
        self.reqGlobalCancel()
        
    def cancel_order_by_id(self, order_id: int):
        # Placeholder for cancelling specific order in IBKR
        logger.info(f"[OrderService] - Cancelling order by ID: {order_id}...")
        self.cancelOrder(order_id, OrderCancel())
        