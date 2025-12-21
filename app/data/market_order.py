import logging

from dataclasses import dataclass, asdict, field


logger = logging.getLogger(__name__)

@dataclass
class MarketOrder:
    order_id: int = 0
    strategy_id: int = 0
    order_details: str = ""
    order_status: str = ""
    order_quantity: int = 0
    order_currency: str = ""
    order_price: float = 0.0
    order_type: str = ""
    order_action: str = ""
    order_parent_id: int = 0
    create_date: str = ""
    update_date: str = ""
    
    
    