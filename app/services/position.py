import logging
import threading

from typing import List

from app.utils.ibapiconnector import IBApiConnector
from ibapi.contract import Contract
from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class PositionService(IBApiConnector):
    def __init__(self, clientId : int=0): 
        super().__init__()
        self.position_result_event = {}
        self.open_positions : List[Contract] = []
    
    # ============================================================================
    # IBKR WRAPPER CALLBACKS
    # ============================================================================
    @iswrapper
    def position(self, account: str, contract, position: float,
                 avgCost: float):
        logger.debug(f"[PositionService] - Position. Account: {account}, Contract: {contract}, Position: {position}, AvgCost: {avgCost}.")
        # Here you can process the position data as needed
        self.open_positions.append(contract)
        
    @iswrapper
    def positionEnd(self):
        event = self.position_result_event.get('position_end')
        if event:
            event.set()
        logger.debug("[PositionService] - PositionEnd.")
        # Here you can handle the end of position data transmission
    
    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================        
    def get_open_positions(self) -> List[Contract]:
        """Request current positions from IBKR."""
        evt = threading.Event()
        self.reqPositions()
        logger.debug("[PositionService] - Requested current positions from IBKR.")
        evt.wait(timeout=10)
        self.position_result_event.pop('position_end', None)
        return self.open_positions