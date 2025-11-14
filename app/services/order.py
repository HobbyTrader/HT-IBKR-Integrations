import time
import logging

from app.utils.ibapiconnector import IBApiConnector
from app.utils.logger import LoggerManager

from ibapi.utils import iswrapper

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
        
    def buy_order(self, order_candidate):
        logger.info(f"[OrderService] - Placing buy order for {order_candidate}")
        # Implementation of buy order logic goes here
        self.placeOrder(self.nextId(),CONTRACT,ORDER)
    
    def create_stoploss(self, order_candidate):
        logger.info(f"[OrderService] - Creating stoploss for {order_candidate}")
        # Implementation of stoploss logic goes here
        self.placeOrder(self.nextId(),CONTRACT,ORDER)
        pass    
    
    def create_takeprofit(self, order_candidate):
        logger.info(f"[OrderService] - Creating takeprofit for {order_candidate}")
        # Implementation of takeprofit logic goes here
        self.placeOrder(self.nextId(),CONTRACT,ORDER)
        pass