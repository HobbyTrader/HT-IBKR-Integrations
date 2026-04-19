import logging

from typing import List
from datetime import datetime

from app.data.history import History
from app.utils.sqllitemanager import SQLiteManager
from app.utils.date_helper import _parse_datetime

logger = logging.getLogger(__name__)

class HistoryDTO:   
    def __init__(self):
        self.dbconn = SQLiteManager()
    
    # ============================================================================
    # ROW TO OBJECT METHODS
    # ============================================================================ 
    def row_to_history(self, row) -> History:
        # Convert a database row to a History object
        logger.debug(f"[HistoryDTO] - Converting row to History: {row}")
        id = row[0]
        instrument_id = row[1]
        symbol = row[2]
        bar_time = row[3]
        open_price = row[4]
        high_price = row[5]
        low_price = row[6]
        close_price = row[7]
        volume = row[8]
        wap = row[9]
        bar_count = row[10]
        create_date = row[11]
        update_date = row[12]
                
        return History(
            id=id,
            instrument_id=instrument_id,
            symbol=symbol,
            bar_time=_parse_datetime(bar_time),
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            wap=wap,
            bar_count=bar_count,
            create_date=_parse_datetime(create_date),
            update_date=_parse_datetime(update_date)
        )
    # ============================================================================
    # SAVE METHODS (INSERT)
    # ============================================================================     
    def save_history(self, history: History) -> int:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[HistoryDTO] - save History. History: {history}")
        cursor.execute(
            """INSERT INTO history (
                instrument_id,
                symbol,
                bar_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                wap,
                bar_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                history.instrument_id,
                history.symbol,
                history.bar_time,
                history.open_price,
                history.high_price,
                history.low_price,
                history.close_price,
                int(history.volume),
                float(history.wap),
                history.bar_count
            )
        )
        self.dbconn.conn.commit()
        id = cursor.lastrowid
        logger.debug(f"[HistoryDTO] - History saved with ID: {id}")
        return id
    # ============================================================================
    # GET METHODS (SELECT)
    # ============================================================================     
    def get_history_by_instrument(self, instrument_id: int) -> List[History]:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[HistoryDTO] - get History by instrument_id: {instrument_id}")
        cursor.execute(
            """SELECT 
                id,
                instrument_id,
                symbol,
                bar_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                wap,
                bar_count,
                create_date,
                update_date
               FROM history WHERE instrument_id = ?""",
            (instrument_id,)
        )
        rows = cursor.fetchall()
        histories = [self.row_to_history(row) for row in rows]
        logger.debug(f"[HistoryDTO] - Retrieved {len(histories)} history records for instrument_id: {instrument_id}")
        return histories
    
    def get_history_by_symbol(self, symbol: str) -> History:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[HistoryDTO] - get History by symbol: {symbol}")
        cursor.execute(
            """SELECT 
                id,
                instrument_id,
                symbol,
                bar_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                wap,
                bar_count,
                create_date,
                update_date
               FROM history WHERE symbol = ?""",
            (symbol,)
        )
        row = cursor.fetchone()
        if row:
            history = self.row_to_history(row)
            logger.debug(f"[HistoryDTO] - Retrieved History: {history}")
            return history
        else:
            logger.debug(f"[HistoryDTO] - No History found with symbol: {symbol}")
            return None
        
    def get_history_by_symbol_and_after_date(self, symbol: str, after_date: datetime) -> List[History]:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[HistoryDTO] - get History by symbol: {symbol} after date: {after_date}")
        cursor.execute(
            """SELECT  
                id,
                instrument_id,
                symbol,
                bar_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                wap,
                bar_count,
                create_date,
                update_date     
               FROM history WHERE symbol = ? AND bar_time >= ?""",
            (symbol, after_date.strftime("%Y-%m-%d %H:%M:%S"))
        )
        rows = cursor.fetchall()
        histories = [self.row_to_history(row) for row in rows]
        logger.debug(f"[HistoryDTO] - Retrieved {len(histories)} history records for symbol: {symbol} after date: {after_date}")
        return histories