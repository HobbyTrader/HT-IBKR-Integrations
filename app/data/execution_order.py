import logging

from dataclasses import dataclass

from vendor.ibapi.execution import Execution

from app.data.instrument import Instrument   


logger = logging.getLogger(__name__)

@dataclass
class ExecutionOrder:
    id: int = 0
    exec_id: str = ""
    order_id: int = 0
    side: str = ""
    shares: float = 0.0
    price: float = 0.0
    execution_time: str = ""
    create_date: str = ""
    update_date: str = ""
    
    
    def from_execution_row(self, row: tuple):
        (self.id, self.exec_id, self.order_id, self.side, self.shares, self.price, self.execution_time, 
         self.create_date, self.update_date) = row

    def from_execution(self, execution: Execution):
        self.exec_id = execution.execId
        self.order_id = execution.orderId
        self.shares = execution.shares
        self.price = execution.price
        self.execution_time = execution.time
    
    