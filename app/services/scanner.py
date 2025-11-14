import time
import logging

from app.utils.ibapiconnector import IBApiConnector
from app.services.market import MarketService
from app.dto.scanner_dto import ScannerDTO
from app.data.strategy import Strategy
from app.data.instrument import Instrument

from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class ScannerService(IBApiConnector):
    def __init__(self, strategy_id=None, exec_key:str=None): 
        super().__init__()
        self.scanner_dto = ScannerDTO(strategy_id)
        self.exec_key = exec_key
        logger.debug("[ScannerService] - Scanner initialzed")

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
        logger.debug(f"[ScannerService] - ScannerDataEnd. reqId: {reqId}.")
        # self.scanner_dto.finalize_request(reqId)
        
    def get_parameters(self):
        self.reqScannerParameters()
        time.sleep(5)

    def get_scannerResult(self, strategy: Strategy):
        logger.debug("[ScannerService] - Scanner Data requested")
        scannerSubscription = strategy.details.to_scannerSubscription()
        scannerOptions = strategy.details.to_scannerOptions()
        filterTagValues = strategy.details.to_tagValueList()
        self.reqScannerSubscription(self.nextId(), scannerSubscription, scannerOptions, filterTagValues)
        time.sleep(1)

    