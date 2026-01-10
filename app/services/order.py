import time
import logging
import threading

from app.data.instrument import Instrument
from app.data.market_order import MarketOrder

from app.dto.market_order_dto import MarketOrderDTO

from app.utils.ibapiconnector import IBApiConnector

from ibapi.utils import iswrapper
from ibapi.order import Order
from ibapi.contract import Contract
from ibapi.order_cancel import OrderCancel
from decimal import Decimal

logger = logging.getLogger(__name__)

class OrderService(IBApiConnector):
    def __init__(self, clientId : int=0): 
        super().__init__()
        self.order_events = {}
        self.CLIENT_ID = clientId
        self.order_dto = MarketOrderDTO()
        self.positions = {}  # Store positions: {(account, symbol): {'contract': Contract, 'position': Decimal, 'avgCost': float}}
        self.positions_received = threading.Event()
        logger.info(f"[OrderService] - Order initialzed - Client ID: {clientId}")
        
    def store_order(self, order: Order, instrument: Instrument):
        market_order = MarketOrder()
        market_order.from_order(order, instrument)
        
        logger.debug(f"[OrderService] - START - Stored order in DB: {market_order}" )
        
        t = threading.Thread(
            target=self.order_dto.save_market_order, 
            args=(market_order,)
        )
        t.start()
        
        logger.debug(f"[OrderService] - Stored order in DB: {market_order}" )
    
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
        targetOrder = self.create_target_order_LMT(instrument, quantity, parentOrderId)
        
        target_events = threading.Event()
        self.order_events[targetOrder.orderId] = target_events
        events.append(target_events)        
        self.store_order(targetOrder, instrument)        
        self.placeOrder(targetOrder.orderId, contract, targetOrder)
        
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
        for order_id in [parentOrder.orderId, stopLossOrder.orderId, targetOrder.orderId]:
            self.order_events.pop(order_id, None)

    def get_active_orders(self):
        # Placeholder for fetching active orders from IBKR
        logger.info("[OrderService] - Fetching active orders...")
        self.reqAllOpenOrders() 
        
    def get_comlpeted_orders(self):
        # Placeholder for fetching completed orders from IBKR
        logger.info("[OrderService] - Fetching completed orders...")
        self.reqCompletedOrders()
    
    # ============================================================================
    # POSITION TRACKING CALLBACKS
    # ============================================================================
    @iswrapper
    def position(self, account: str, contract: Contract, position: Decimal, avgCost: float):
        """Callback for receiving position data."""
        logger.info(f"[OrderService] - Position. account: {account}, symbol: {contract.symbol}, position: {position}, avgCost: {avgCost}")
        key = (account, contract.symbol)
        self.positions[key] = {
            'contract': contract,
            'position': position,
            'avgCost': avgCost
        }
        return super().position(account, contract, position, avgCost)
    
    @iswrapper
    def positionEnd(self):
        """Callback indicating all positions have been received."""
        logger.info(f"[OrderService] - Position End. Total positions: {len(self.positions)}")
        self.positions_received.set()
        return super().positionEnd()
    
    # ============================================================================
    # ORDER CANCELLATION AND POSITION LIQUIDATION
    # ============================================================================
    def cancel_all_open_orders(self):
        """Cancel all open orders using IBKR's global cancel."""
        logger.info("[OrderService] - Cancelling all open orders...")
        order_cancel = OrderCancel()
        self.reqGlobalCancel(order_cancel)
        logger.info("[OrderService] - Global cancel order sent to IBKR.")
    
    def get_all_positions(self, timeout: float = 10.0) -> dict:
        """Request and return all current positions."""
        logger.info("[OrderService] - Requesting all positions...")
        self.positions.clear()
        self.positions_received.clear()
        
        self.reqPositions()
        
        # Wait for positions to be received
        if self.positions_received.wait(timeout=timeout):
            logger.info(f"[OrderService] - Received {len(self.positions)} positions.")
            return self.positions.copy()
        else:
            logger.warning(f"[OrderService] - Timeout waiting for positions after {timeout} seconds.")
            return self.positions.copy()
    
    def sell_all_positions(self):
        """Create market sell orders for all open positions."""
        logger.info("[OrderService] - Selling all positions...")
        positions = self.get_all_positions()
        
        if not positions:
            logger.info("[OrderService] - No positions to sell.")
            return
        
        for key, pos_data in positions.items():
            account, symbol = key
            position_size = pos_data['position']
            contract = pos_data['contract']
            
            # Only sell long positions (position > 0)
            if position_size > 0:
                logger.info(f"[OrderService] - Creating sell order for {symbol}, quantity: {position_size}")
                
                # Create market sell order
                sell_order = Order()
                sell_order.orderId = self.nextId()
                sell_order.action = "SELL"
                sell_order.orderType = "MKT"
                sell_order.totalQuantity = float(position_size)
                sell_order.transmit = True
                
                # Place the order
                self.placeOrder(sell_order.orderId, contract, sell_order)
                logger.info(f"[OrderService] - Placed sell order {sell_order.orderId} for {symbol}")
            else:
                logger.debug(f"[OrderService] - Skipping {symbol} (position: {position_size})")
    
    def cancel_orders_and_sell_positions(self):
        """Cancel all open orders and sell all positions."""
        logger.info("[OrderService] - Starting cancel orders and sell positions...")
        
        # Step 1: Cancel all open orders
        self.cancel_all_open_orders()
        
        # Wait a moment for cancellations to process
        time.sleep(2)
        
        # Step 2: Sell all positions
        self.sell_all_positions()
        
        logger.info("[OrderService] - Cancel orders and sell positions completed.")
        