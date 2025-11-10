import time
import logging

from app.utils.ibapiconnector import IBApiConnector
from app.utils.sqllitemanager import SQLiteManager

from ibapi.client import *
from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class ScannerService(IBApiConnector):
    def __init__(self): 
        super().__init__()
        self.dbconn = SQLiteManager()
        logger.debug("[ScannerService] - Scanner initialzed")

    @iswrapper
    def scannerParameters(self, xml: str):
        logger.debug("ScannerParameters received.")
        open('log/scanner.xml', 'w').write(xml)

    @iswrapper
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ScannerService] - ScannerData. reqId: {reqId}, rank: {rank}, contractDetails: {contractDetails}, distance: {distance}, benchmark: {benchmark}, projection: {projection}, legsStr: {legsStr}.")
        cursor.execute("""INSERT INTO scanner_results (req_id, rank, contract_id, contract_symbol, contract_sectype, contract_currency, trading_class, exchange) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (reqId, rank, contractDetails.contract.conId, contractDetails.contract.symbol, contractDetails.contract.secType, contractDetails.contract.currency, contractDetails.contract.tradingClass, contractDetails.contract.exchange))
        self.dbconn.conn.commit()

    def get_parameters(self):
        self.reqScannerParameters()
        time.sleep(5)

    def get_scannerResult(self, scannerSubscription, scannerOptions, filterTagValues):
        logger.debug("[ScannerService] - Scanner Data requested")
        self.reqScannerSubscription(self.nextId(), scannerSubscription, scannerOptions, filterTagValues)
        time.sleep(10)

    