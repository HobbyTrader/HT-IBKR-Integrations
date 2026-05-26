import logging
from decimal import Decimal

from typing import List

from app.data.execution_order import ExecutionOrder
from app.utils.date_helper import _parse_datetime
from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class ExecutionOrderDTO:
    def __init__(self):
        self.dbconn = SQLiteManager()
        self._ensure_contract_symbol_column()

    def _ensure_contract_symbol_column(self) -> None:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='executions'")
        if cursor.fetchone() is None:
            return

        cursor.execute("PRAGMA table_info(executions)")
        columns = {row[1] for row in cursor.fetchall()}
        if "contract_symbol" not in columns:
            logger.info("[ExecutionOrderDTO] - Adding missing executions.contract_symbol column.")
            cursor.execute("ALTER TABLE executions ADD COLUMN contract_symbol TEXT NOT NULL DEFAULT ''")
            self.dbconn.conn.commit()
    
    # ============================================================================
    # ROW TO OBJECT METHODS
    # ============================================================================ 
    def row_to_execution_order(self, row) -> ExecutionOrder:
        # Convert a database row to a Strategy object
        logger.debug(f"[ExecutionOrderDTO] - Converting row to ExecutionOrder: {row}")
        id = row[0]
        exec_id = row[1]
        order_id = row[2]
        contract_symbol = row[3]
        side = row[4]
        shares = row[5]
        price = row[6]
        execution_time = row[7]
        create_date = row[8]
        update_date = row[9]
                
        return ExecutionOrder(
            id=id,
            exec_id=exec_id,    
            order_id=order_id,
            contract_symbol=contract_symbol,
            side=side,
            shares=shares,
            price=price,
            execution_time=_parse_datetime(execution_time),
            create_date=_parse_datetime(create_date),
            update_date=_parse_datetime(update_date)
        )
    
    # ============================================================================
    # SAVE METHODS (INSERT)
    # ============================================================================     
    @staticmethod
    def _normalize_sql_value(value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    def save_execution_order(self, execution_order: ExecutionOrder) -> int:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ExecutionOrderDTO] - save ExecutionOrder. ExecutionOrder: {execution_order}")
        shares = self._normalize_sql_value(execution_order.shares)
        price = self._normalize_sql_value(execution_order.price)
        cursor.execute(
            """INSERT INTO executions (
                exec_id,
                order_id, 
                contract_symbol,
                side, 
                shares, 
                price, 
                execution_time) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            ( execution_order.exec_id,
             execution_order.order_id, 
             execution_order.contract_symbol,
             execution_order.side, 
             shares,
             price,
             execution_order.execution_time))
        self.dbconn.conn.commit()   
        id = cursor.lastrowid
        logger.debug(f"[ExecutionOrderDTO] - ExecutionOrder saved with ID: {id}")
        return id
    
    # ============================================================================
    # GET METHODS (SELECT)
    # ============================================================================     
    def get_execution_orders_by_order_id(self, order_id: int) -> List[ExecutionOrder]:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ExecutionOrderDTO] - get ExecutionOrders by order_id: {order_id}")
        cursor.execute(
            """SELECT 
                id,
                exec_id,
                order_id,
                contract_symbol,
                side,
                shares,
                price,
                execution_time,
                create_date,
                update_date
               FROM executions
               WHERE order_id = ?""",
            (order_id,))
        rows = cursor.fetchall()
        execution_orders = [self.row_to_execution_order(row) for row in rows]
        return execution_orders
    
    def get_all_execution_orders(self) -> List[ExecutionOrder]:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ExecutionOrderDTO] - get all ExecutionOrders.")
        cursor.execute(
            """SELECT 
                id,
                exec_id,
                order_id,
                contract_symbol,
                side,
                shares,
                price,
                execution_time,
                create_date,
                update_date
               FROM executions""")
        rows = cursor.fetchall()
        execution_orders = [self.row_to_execution_order(row) for row in rows]
        return execution_orders
    
    def get_today_execution_orders(self) -> List[ExecutionOrder]:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ExecutionOrderDTO] - get today's ExecutionOrders.")
        cursor.execute(
            """SELECT 
                id,
                exec_id,
                order_id,
                contract_symbol,
                side,
                shares,
                price,
                execution_time,
                create_date,
                update_date
               FROM executions
               WHERE DATE(execution_time) = DATE('now','localtime')""")
        rows = cursor.fetchall()
        execution_orders = [self.row_to_execution_order(row) for row in rows]
        return execution_orders
    
    # ============================================================================
    # UPDATE METHODS (UPDATE)
    # ============================================================================ 
    def update_execution_by_order_id(self, order_id: int, contract_symbol: str, shares: float, price: float, execution_time) -> int:
        cursor = self.dbconn.conn.cursor()
        shares = self._normalize_sql_value(shares)
        price = self._normalize_sql_value(price)
        logger.debug(
            "[ExecutionOrderDTO] - update ExecutionOrder by order_id=%s contract_symbol=%s shares=%s price=%s execution_time=%s",
            order_id,
            contract_symbol,
            shares,
            price,
            execution_time,
        )
        cursor.execute(
            """UPDATE executions
               SET shares = ?,
                   price = ?,
                   execution_time = ?,
                   update_date = datetime('now')
               WHERE order_id = ? AND contract_symbol = ?""",
            (shares, price, execution_time, order_id, contract_symbol),
        )
        self.dbconn.conn.commit()
        return cursor.rowcount

    def upsert_execution_from_ib(
        self,
        exec_id: str,
        order_id: int,
        contract_symbol: str,
        side: str,
        shares: float,
        price: float,
        execution_time,
    ) -> int:
        updated_rows = self.update_execution_by_order_id(
            order_id=order_id,
           contract_symbol=contract_symbol,
            shares=shares,
            price=price,
            execution_time=execution_time,
        )
        if updated_rows > 0:
            return updated_rows

        execution_order = ExecutionOrder(
            exec_id=exec_id,
            order_id=order_id,
            contract_symbol=contract_symbol,
            side=side,
            shares=shares,
            price=price,
            execution_time=execution_time,
        )
        self.save_execution_order(execution_order)
        return 1
        
    
