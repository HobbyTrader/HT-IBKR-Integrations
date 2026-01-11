import logging

from app.utils.ibapiconnector import IBApiConnector
from vendor.ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class PositionService(IBApiConnector):
    def __init__(self, clientId : int=0): 
        super().__init__()
    
    # ============================================================================
    # IBKR WRAPPER CALLBACKS
    # ============================================================================
    @iswrapper
    def position(self, account: str, contract, position: float,
                 avgCost: float):
        logger.debug(f"[PositionService] - Position. Account: {account}, Contract: {contract}, Position: {position}, AvgCost: {avgCost}.")
        # Here you can process the position data as needed
        
    @iswrapper
    def positionEnd(self):
        logger.debug("[PositionService] - PositionEnd.")
        # Here you can handle the end of position data transmission
    
    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================        
    def get_positions(self):
        """Request current positions from IBKR."""
        self.reqPositions()
        logger.debug("[PositionService] - Requested current positions from IBKR.")