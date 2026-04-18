import time
import logging
import threading

from typing import List

from app.data.instrument import Instrument
from app.utils.ibapiconnector import IBApiConnector
from app.dto.scanner_dto import ScannerDTO
from app.data.strategy import Strategy

from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class ScannerService(IBApiConnector):
    def __init__(self, strategy_id=None, exec_key:str=None): 
        super().__init__()
        self.scanner_dto = ScannerDTO(strategy_id)
        self.exec_key = exec_key
        self.scanner_result_event = {}
        logger.debug("[ScannerService] - Scanner initialzed")

    # ============================================================================
    # IBKR WRAPPER CALLBACKS
    # ============================================================================
    @iswrapper
    def scannerParameters(self, xml: str):
        logger.debug("ScannerParameters received.")
        open('log/scanner.xml', 'w').write(xml)

    @iswrapper
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        logger.debug(f"[ScannerService] - ScannerData. reqId: {reqId}, rank: {rank}, contractDetails: {contractDetails}, distance: {distance}, benchmark: {benchmark}, projection: {projection}, legsStr: {legsStr}.")
        self.scanner_dto.save_details(reqId, rank, contractDetails, self.exec_key)
       
    @iswrapper
    def scannerDataEnd(self, reqId):
        event = self.scanner_result_event.get(reqId)
        if event:
            event.set()
        logger.debug(f"[ScannerService] - ScannerDataEnd. reqId: {reqId}.")
    
    # ============================================================================
    # Public methods
    # ============================================================================    
    def get_parameters(self):
        self.reqScannerParameters()
        time.sleep(5)

    def get_scanner_result(self, strategy: Strategy) -> List[Instrument]:
        logger.debug("[ScannerService] - Scanner Data requested")
        evt = threading.Event()
        scannerSubscription = strategy.details.to_scannerSubscription()
        scannerOptions = strategy.details.to_scannerOptions()
        filterTagValues = strategy.details.to_tagValueList()
        request_id = self.nextRequestId()
        self.scanner_result_event[request_id] = evt
        
        self.reqScannerSubscription(request_id, scannerSubscription, scannerOptions, filterTagValues)
        
        evt.wait(timeout=10)
        self.scanner_result_event.pop(request_id, None)
        
        return self.scanner_dto.get_instruments_by_exec_key(self.exec_key)

    