import logging

from app.utils.sqllitemanager import SQLiteManager
from app.utils.logger import LoggerManager

logger = logging.getLogger(__name__)

class ScannerDTO:
    def __init__(self, strategy_id=None):
        self.dbconn = SQLiteManager()
        self.strategy_id = strategy_id
    
    def saveDetails(self, reqId, rank, contractDetails):
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ScannerDTO] - save ScannerData.")
        cursor.execute("""INSERT INTO scanner_results (req_id, rank, strategy_id, contract_id, contract_symbol, contract_sectype, contract_currency, contract_trading_class, contract_exchange) VALUES (?,?, ?, ?, ?, ?, ?, ?, ?)""",
            (reqId, rank, self.strategy_id, contractDetails.contract.conId, contractDetails.contract.symbol, contractDetails.contract.secType, contractDetails.contract.currency, contractDetails.contract.tradingClass, contractDetails.contract.exchange))
        self.dbconn.conn.commit()
    
    def getDetails(self):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM scanner_results")
        results = cursor.fetchall()
        return results
    
    def getDetailsByReqId(self, reqId, rank):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM scanner_results WHERE req_id = ? and rank = ?", (reqId, rank))
        results = cursor.fetchall()
        return results