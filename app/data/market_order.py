import datetime
import logging

from dataclasses import dataclass, field

from vendor.ibapi.order import Order

from app.data.instrument import Instrument   


logger = logging.getLogger(__name__)

@dataclass
class MarketOrder:
    id: int = 0
    order_id: int = 0
    strategy_id: int = 0
    order_contract_id: int = 0
    order_symbol: str = ""
    order_status: str = ""
    order_quantity: int = 0
    order_currency: str = ""
    order_price: float = 0.0
    order_type: str = ""
    order_action: str = ""
    order_parent_id: int = 0
    create_date: datetime = field(default_factory=datetime.now)
    update_date: datetime = field(default_factory=datetime.now)
    
    def from_order_row(self, row: tuple):
        (self.id, self.order_id, self.strategy_id, self.order_contract_id, self.order_symbol, 
         self.order_status, self.order_quantity, self.order_currency, self.order_price, self.order_type,
         self.order_action, self.order_parent_id) = row

    def from_order(self, order: Order, contract_id: int, symbol:str, strategy_id: int, currency: str):
        self.order_id = order.orderId
        self.order_contract_id = contract_id
        self.order_symbol = symbol
        self.strategy_id = strategy_id
        self.order_quantity = order.totalQuantity
        self.order_currency = currency
        # En fonction de l'ordre, se baser sur limited price ou autre
        match order.orderType:
            case "STP":
                self.order_price = order.auxPrice
            case "LMT":
                self.order_price = order.lmtPrice
            case _:
                self.order_price = 0.0
        
        self.order_type = order.orderType
        self.order_action = order.action
        self.order_parent_id = order.parentId
    
    