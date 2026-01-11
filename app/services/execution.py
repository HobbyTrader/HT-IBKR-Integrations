import logging

from app.utils.ibapiconnector import IBApiConnector
from vendor.ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class ExecutionService(IBApiConnector):
    def __init__(self, clientId : int=0): 
        super().__init__()
        
    # ============================================================================
    # IBKR WRAPPER CALLBACKS
    # ============================================================================
    @iswrapper
    def execDetails(self, reqId: int, contract, execution):
        logger.debug(f"[ExecutionService] - Exec Details. ReqId: {reqId}, Contract: {contract}, Execution: {execution}.")
        # Here you can process the execution details as needed
        
    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================    
    def get_executions(self, reqId: int=1, filter = None):
        """Request execution reports from IBKR."""
        self.reqExecutions(reqId, filter)
        logger.debug("[ExecutionService] - Requested execution reports from IBKR.")
        
    