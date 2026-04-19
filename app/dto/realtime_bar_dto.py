import logging

from typing import List
from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class RealtimeBarDTO:
    def __init__(self):
        self.dbconn = SQLiteManager()

    # ============================================================================
    # SAVE METHODS (INSERT)
    # ============================================================================
    def save_realtime_bar(self, req_id: int, time: int, open_: float, high: float, low: float, close: float, volume: int, wap: float, count: int) -> int:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[RealtimeBarDTO] - save RealtimeBar. req_id: {req_id}, time: {time}")
        cursor.execute(
            """INSERT INTO realtime_bars (
                req_id,
                bar_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                wap,
                bar_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                req_id,
                time,
                open_,
                high,
                low,
                close,
                int(volume),
                float(wap),
                count
            )
        )
        self.dbconn.conn.commit()
        id = cursor.lastrowid
        logger.debug(f"[RealtimeBarDTO] - RealtimeBar saved with ID: {id}")
        return id

    # ============================================================================
    # GET METHODS (SELECT)
    # ============================================================================
    def get_bars_by_req_id(self, req_id: int) -> List[dict]:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[RealtimeBarDTO] - get RealtimeBars by req_id: {req_id}")
        cursor.execute(
            """SELECT
                id,
                req_id,
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
               FROM realtime_bars WHERE req_id = ?
               ORDER BY bar_time ASC""",
            (req_id,)
        )
        rows = cursor.fetchall()
        logger.debug(f"[RealtimeBarDTO] - Retrieved {len(rows)} realtime bar records for req_id: {req_id}")
        return rows

    def get_all_bars(self) -> List[dict]:
        cursor = self.dbconn.conn.cursor()
        logger.debug("[RealtimeBarDTO] - get all RealtimeBars")
        cursor.execute(
            """SELECT
                id,
                req_id,
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
               FROM realtime_bars
               ORDER BY bar_time ASC"""
        )
        rows = cursor.fetchall()
        logger.debug(f"[RealtimeBarDTO] - Retrieved {len(rows)} realtime bar records")
        return rows
