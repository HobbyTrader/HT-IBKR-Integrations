import logging
import threading
from typing import Optional

from app.dto.execution_order_dto import ExecutionOrderDTO
from app.utils.ibapiconnector import IBApiConnector
from ibapi.execution import ExecutionFilter
from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class ExecutionService(IBApiConnector):
    def __init__(self, clientId : int=0): 
        super().__init__()
        self.CLIENT_ID = clientId
        self.execution_order_dto = ExecutionOrderDTO()
        self._execution_details_end_event: Optional[threading.Event] = None
        
    # ============================================================================
    # IBKR WRAPPER CALLBACKS
    # ============================================================================
    @iswrapper
    def execDetails(self, reqId: int, contract, execution):
        logger.debug(f"[ExecutionService] - Exec Details. ReqId: {reqId}, Contract: {contract}, Execution: {execution}.")
        updated_rows = self.execution_order_dto.upsert_execution_from_ib(
            exec_id=getattr(execution, "execId", ""),
            order_id=getattr(execution, "orderId", 0),
            contract_symbol=getattr(contract, "symbol", ""),
            side=getattr(execution, "side", ""),
            shares=getattr(execution, "cumQty", 0.0),
            price=getattr(execution, "avgPrice", 0.0),
            execution_time=getattr(execution, "time", None),
        )
        logger.info(
            "[ExecutionService] - Updated executions table for order_id=%s (rows=%s) using avgPrice=%s, cumQty=%s, time=%s",
            getattr(execution, "orderId", 0),
            updated_rows,
            getattr(execution, "avgPrice", 0.0),
            getattr(execution, "cumQty", 0.0),
            getattr(execution, "time", None),
        )

    @iswrapper
    def execDetailsEnd(self, reqId: int):
        logger.debug("[ExecutionService] - Exec Details End. ReqId: %s", reqId)
        if self._execution_details_end_event:
            self._execution_details_end_event.set()
        
    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================    
    def get_executions(self, reqId: int = 1, execution_filter: ExecutionFilter | None = None, timeout: float = 10.0):
        """Request execution reports from IBKR."""
        self._execution_details_end_event = threading.Event()
        if execution_filter is None:
            execution_filter = ExecutionFilter()

        self.reqExecutions(reqId, execution_filter)
        logger.debug("[ExecutionService] - Requested execution reports from IBKR.")

        self._execution_details_end_event.wait(timeout=timeout)
        self._execution_details_end_event = None
    
