import logging

from app.data.instrument import Instrument
from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class ScannerDTO:
    def __init__(self, strategy_id=None):
        self.dbconn = SQLiteManager()
        self.strategy_id = strategy_id
    
    def save_details(self, reqId, rank, contractDetails, exec_key:str="AAA"):
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ScannerDTO] - save ScannerData.")
        cursor.execute("""INSERT INTO scanner_results (req_id, rank, strategy_id, contract_id, contract_symbol, contract_sectype, contract_currency, contract_trading_class, contract_exchange,exec_key) VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (reqId, rank, self.strategy_id, contractDetails.contract.conId, contractDetails.contract.symbol, contractDetails.contract.secType, contractDetails.contract.currency, contractDetails.contract.tradingClass, contractDetails.contract.exchange, exec_key))
        self.dbconn.conn.commit()
        
    def set_orderCandidate(self, exec_key, contract_id, is_order_candidate):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("""UPDATE scanner_results SET is_order_candidate = ?, update_date = CURRENT_TIMESTAMP WHERE exec_key = ? AND contract_id = ?""",
            (is_order_candidate, exec_key, contract_id))
        self.dbconn.conn.commit()
    
    def get_details(self):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM scanner_results")
        results = cursor.fetchall()
        return results
    
    def get_instrumentByExecKey(self, exec_key:str) -> list[Instrument]:
        cursor = self.dbconn.conn.cursor()
        # select specific columns to map into Instrument
        cursor.execute(
            "SELECT contract_id, contract_symbol, contract_sectype, contract_currency, contract_exchange FROM scanner_results WHERE exec_key = ? ORDER BY rank ASC",
            (exec_key,)
        )
        rows = cursor.fetchall()
        instruments: list[Instrument] = []
        for r in rows:
            inst = Instrument()
            try:
                inst.id = r[0]
                inst.symbol = r[1]
                inst.sectype = r[2]
                inst.currency = r[3]
                inst.exchange = r[4]
            except Exception:
                # In case schema changes, skip malformed rows
                logger.error(f"[ScannerDTO] - Malformed row in get_instrumentByExecKey: {r}")
                continue
            instruments.append(inst)
        return instruments
    
    def get_instrument_candidates(self, exec_key:str) -> list:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM scanner_results WHERE is_order_candidate = 1 and exec_key = ?", (exec_key))
        results = cursor.fetchall()
        return results
    
    