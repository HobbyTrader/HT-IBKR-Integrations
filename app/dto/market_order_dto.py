import logging

from typing import List

from app.data.market_order import MarketOrder
from app.utils.date_helper import _parse_datetime
from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class MarketOrderDTO:
    def __init__(self):
        self.dbconn = SQLiteManager()
    
    # ============================================================================
    # ROW TO OBJECT METHODS
    # ============================================================================ 
    def row_to_market_order(self, row) -> MarketOrder:
        # Convert a database row to a Strategy object
        logger.debug(f"[MarketOrderDTO] - Converting row to MarketOrder: {row}")
        id = row[0]
        order_id = row[1]
        strategy_id = row[2]
        order_contract_id = row[3]
        order_symbol = row[4]
        order_status = row[5]
        order_quantity = row[6]
        order_currency = row[7]
        order_price = row[8]
        order_type = row[9]
        order_action = row[10]
        order_parent_id = row[11]
        create_date = row[12]
        update_date = row[13]
                
        return MarketOrder(
            id=id,
            order_id=order_id,
            strategy_id=strategy_id,
            order_contract_id=order_contract_id,
            order_symbol=order_symbol,
            order_status=order_status,
            order_quantity=order_quantity,
            order_currency=order_currency,
            order_price=order_price,
            order_type=order_type,
            order_action=order_action,
            order_parent_id=order_parent_id,
            create_date=_parse_datetime(create_date),
            update_date=_parse_datetime(update_date)
        )
    
    # ============================================================================
    # SAVE METHODS (INSERT)
    # ============================================================================     
    def save_market_order(self, market_order: MarketOrder) -> int:
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[MarketOrderDTO] - save MarketOrder. MarketOrder: {market_order}")
        cursor.execute(
            """INSERT INTO market_orders (
                order_id,
                strategy_id, 
                order_contract_id,
                order_symbol,
                order_status, 
                order_quantity, 
                order_currency, 
                order_price, 
                order_type, 
                order_action, 
                order_parent_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
             market_order.order_id,
             market_order.strategy_id, 
             market_order.order_contract_id, 
             market_order.order_symbol,
             market_order.order_status, 
             market_order.order_quantity, 
             market_order.order_currency, 
             market_order.order_price, 
             market_order.order_type, 
             market_order.order_action, 
             market_order.order_parent_id))
        self.dbconn.conn.commit()
        id = cursor.lastrowid
        logger.debug(f"[MarketOrderDTO] - MarketOrder saved with ID: {id}")
        return id
    
    # ============================================================================
    # GET METHODS (SELECT)
    # ============================================================================     
    def get_market_order_by_id(self, order_id) -> MarketOrder:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        return self.row_to_market_order(row) if row else None
    
    def get_all_market_orders(self) -> List[MarketOrder]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders")
        rows = cursor.fetchall()
        return [self.row_to_market_order(row) for row in rows]
    
    def get_market_orders_by_strategy(self, strategy_id) -> List[MarketOrder]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE strategy_id = ?", (strategy_id,))
        rows = cursor.fetchall()
        return [self.row_to_market_order(row) for row in rows]
    
    def get_market_orders_by_strategy_today(self, strategy_id) -> List[MarketOrder]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE strategy_id = ? AND DATE(create_date) = DATE('now')", (strategy_id,))
        rows = cursor.fetchall()
        return [self.row_to_market_order(row) for row in rows]
    
    def get_market_orders_by_contract_id_today_parent(self, contract_id) -> List[MarketOrder]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE order_contract_id = ? AND order_parent_id = 0 AND DATE(create_date) = DATE('now')", (contract_id,))
        rows = cursor.fetchall()
        return [self.row_to_market_order(row) for row in rows]

    def get_market_orders_by_contract_id_today(self, contract_id) -> List[MarketOrder]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE order_contract_id = ? AND DATE(create_date) = DATE('now')", (contract_id,))
        rows = cursor.fetchall()
        return [self.row_to_market_order(row) for row in rows]
    
    def get_market_orders_by_parent_order(self, parent_order_id) -> List[MarketOrder]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute(
            "SELECT * FROM market_orders WHERE order_id = ? OR order_parent_id = ?",
            (parent_order_id, parent_order_id),
        )
        rows = cursor.fetchall()
        return [self.row_to_market_order(row) for row in rows]
    
    def get_market_orders_by_status(self, order_status) -> List[MarketOrder]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE order_status = ?", (order_status,))
        rows = cursor.fetchall()
        return [self.row_to_market_order(row) for row in rows]  
    
    def get_market_orders_by_create_date(self, create_date) -> List[MarketOrder]:
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE create_date >= ?", (create_date,))
        rows = cursor.fetchall()
        return [self.row_to_market_order(row) for row in rows]
    
    # ============================================================================
    # UPDATE METHODS (UPDATE)
    # ============================================================================ 
    def update_market_order_status(self, order_id, new_status):
        cursor = self.dbconn.conn.cursor()
        cursor.execute(
            "UPDATE market_orders SET order_status = ?, update_date = CURRENT_TIMESTAMP WHERE order_id = ? AND LOWER(order_status) != 'rejected'",
            (new_status, order_id))
        self.dbconn.conn.commit()

    def update_related_market_order_status(self, parent_order_id, new_status):
        cursor = self.dbconn.conn.cursor()
        cursor.execute(
            "UPDATE market_orders SET order_status = ?, update_date = CURRENT_TIMESTAMP WHERE order_id = ? OR order_parent_id = ?",
            (new_status, parent_order_id, parent_order_id),
        )
        self.dbconn.conn.commit()
        
    