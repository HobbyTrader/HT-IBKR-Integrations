import logging

from typing import List

from app.data.instrument import Instrument
from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class ScannerDTO:
    def __init__(self, strategy_id=None):
        self.dbconn = SQLiteManager()
        self.strategy_id = strategy_id
        
    # ============================================================================
    # ROW TO OBJECT METHODS
    # ============================================================================ 
    def rows_to_instruments(self, rows) -> List[Instrument]:
        instruments: List[Instrument] = []
        for r in rows:
            try:
                inst = Instrument.from_row(r)
            except Exception:
                # In case schema changes, skip malformed rows
                logger.error(f"[ScannerDTO] - Malformed row in rows_to_instruments: {r}")
                continue
            instruments.append(inst)
        return instruments
    
    # ============================================================================
    # SAVE METHODS (INSERT)
    # ============================================================================     
    def save_details(self, reqId, rank, contractDetails, exec_key:str="AAA") -> int:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ScannerDTO] - save ScannerData. ContractDetails: {contractDetails}")
        cursor.execute(
            """INSERT INTO scanner_results (req_id, rank, strategy_id, contract_id, contract_symbol, contract_sectype, contract_currency, contract_trading_class, contract_exchange,exec_key) VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (reqId, rank, self.strategy_id, contractDetails.contract.conId, contractDetails.contract.symbol, contractDetails.contract.secType, contractDetails.contract.currency, contractDetails.contract.tradingClass, contractDetails.contract.exchange, exec_key))
        self.dbconn.conn.commit()        
        id = cursor.lastrowid
        logger.debug(f"[ScannerDTO] - ScannerData saved with ID: {id}")
        return id
    
    # ============================================================================
    # UPDATE METHODS (UPDATE)
    # ============================================================================     
    def set_order_candidate(self, exec_key, contract_id, is_order_candidate):
        cursor = self.dbconn.conn.cursor()
        cursor.execute(
            """UPDATE scanner_results SET is_order_candidate = ?, update_date = CURRENT_TIMESTAMP WHERE exec_key = ? AND contract_id = ?""",
            (is_order_candidate, exec_key, contract_id))
        self.dbconn.conn.commit()
        
    # ============================================================================
    # UPDATE METHODS (UPDATE)
    # ============================================================================     
    def clean_non_candidates(self, exec_key):
        cursor = self.dbconn.conn.cursor()
        cursor.execute(
            """DELETE FROM scanner_results WHERE is_order_candidate = 0 AND exec_key = ?""",
            (exec_key,))
        self.dbconn.conn.commit()
    
    # ============================================================================
    # GET METHODS (SELECT)
    # ============================================================================     
       
    def get_details(self):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM scanner_results")
        results = cursor.fetchall()
        return results
    
    def get_instruments_by_exec_key(self, exec_key:str) -> List[Instrument]:
        cursor = self.dbconn.conn.cursor()
        # select specific columns to map into Instrument
        cursor.execute(
            """SELECT contract_id, contract_symbol, contract_sectype, contract_currency, contract_exchange FROM scanner_results WHERE exec_key = ? ORDER BY rank ASC""",
            (exec_key,)
        )
        rows = cursor.fetchall()
        return self.rows_to_instruments(rows)
    
    def get_instruments_candidates(self, exec_key:str) -> List[Instrument]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute(
            "SELECT contract_id, contract_symbol, contract_sectype, contract_currency, contract_exchange FROM scanner_results WHERE is_order_candidate = 1 and exec_key = ? ORDER BY rank ASC", 
            (exec_key,)
        )
        rows = cursor.fetchall()
        return self.rows_to_instruments(rows)
    
    def get_contract_id_by_symbol(self, symbol: str) -> int:
        cursor = self.dbconn.conn.cursor()
        cursor.execute(
            "SELECT contract_id FROM scanner_results WHERE contract_symbol = ? LIMIT 1", 
            (symbol,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    
    