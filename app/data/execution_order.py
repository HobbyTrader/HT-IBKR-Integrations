from datetime import datetime
import logging

from dataclasses import dataclass, field

from app.data.numeric_mixin import NumericMixin
from ibapi.execution import Execution

from app.data.instrument import Instrument   


logger = logging.getLogger(__name__)

@dataclass
class ExecutionOrder(NumericMixin):
    id: int = 0
    exec_id: str = ""
    order_id: int = 0
    contract_symbol: str = ""
    side: str = ""
    shares: float = 0.0
    price: float = 0.0
    execution_time: datetime = field(default_factory=datetime.now)
    create_date: datetime = field(default_factory=datetime.now)
    update_date: datetime = field(default_factory=datetime.now)
    
    
    def from_execution_row(self, row: tuple):
        (self.id, self.exec_id, self.order_id, self.contract_symbol, self.side, self.shares, self.price, self.execution_time,
         self.create_date, self.update_date) = row

    def from_execution(self, execution: Execution):
        self.exec_id = execution.execId
        self.order_id = execution.orderId
        # IB execDetails returns cumulative quantity and average price for the order.
        self.shares = getattr(execution, "cumQty", execution.shares)
        self.price = getattr(execution, "avgPrice", execution.price)
        self.execution_time = execution.time
    
    