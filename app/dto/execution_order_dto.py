import logging

from typing import List

from app.data.execution_order import ExecutionOrder
from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class ExecutionOrderDTO:
    def __init__(self):
        self.dbconn = SQLiteManager()
    
    # ============================================================================
    # ROW TO OBJECT METHODS
    # ============================================================================ 
    def row_to_execution_order(self, row) -> ExecutionOrder:
        # Convert a database row to a Strategy object
        logger.debug(f"[ExecutionOrderDTO] - Converting row to ExecutionOrder: {row}")
        id = row[0]
        exec_id = row[1]
        order_id = row[2]
        side = row[3]
        shares = row[4]
        price = row[5]
        execution_time = row[6]
        create_date = row[7]
        update_date = row[8]
                
        return ExecutionOrder(
            id=id,
            exec_id=exec_id,    
            order_id=order_id,
            side=side,
            shares=shares,
            price=price,
            execution_time=execution_time,
            create_date=create_date,
            update_date=update_date
        )
    
    # ============================================================================
    # SAVE METHODS (INSERT)
    # ============================================================================     
    def save_execution_order(self, execution_order: ExecutionOrder):
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[ExecutionOrderDTO] - save ExecutionOrder. ExecutionOrder: {execution_order}")
        cursor.execute(
            """INSERT INTO executions (
                exec_id,
                order_id, 
                side, 
                shares, 
                price, 
                execution_time) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
            ( execution_order.exec_id,
             execution_order.order_id, 
             execution_order.side, 
             execution_order.shares, 
             execution_order.price, 
             execution_order.execution_time))
        self.dbconn.conn.commit()   
    
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
    
        
    