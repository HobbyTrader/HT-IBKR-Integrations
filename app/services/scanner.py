import time

from app.core.ibapiconnector import IBApiConnector

from ibapi.wrapper import EWrapper
from ibapi.client import *
from ibapi.utils import iswrapper

class ScannerService(IBApiConnector):
    def __init__(self, config, logger, dbconn) :
        super().__init__(config, logger)
        self.logger.debug("[ScannerService] - Scanner initialzed")

    @iswrapper
    def scannerParameters(self, xml: str):
        self.logger.debug("ScannerParameters received.")
        open('log/scanner.xml', 'w').write(xml)

    @iswrapper
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        self.logger.debug(f"[ScannerService] - ScannerData. reqId: {reqId}, rank: {rank}, contractDetails: {contractDetails}, distance: {distance}, benchmark: {benchmark}, projection: {projection}, legsStr: {legsStr}.")

    def get_parameters(self):
        self.reqScannerParameters()
        time.sleep(5)

    def get_scannerResult(self, scannerSubscription, scannerOptions, filterTagValues):
        self.logger.debug("[ScannerService] - Scanner Data requested")
        self.reqScannerSubscription(self.nextId(), scannerSubscription, scannerOptions, filterTagValues)
        time.sleep(10)

    