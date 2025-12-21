import logging

from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class MarketOrderDTO:
    def __init__(self):
        self.dbconn = SQLiteManager()
        
    def save_market_order(self, market_order):
        cursor = self.dbconn.conn.cursor()
        logger.debug(f"[MarketOrderDTO] - save MarketOrder. MarketOrder: {market_order}")
        cursor.execute(
            """INSERT INTO market_orders (strategy_id, order_details, order_status, order_quantity, order_currency, order_price, order_type, order_action, order_parent_id, create_date, update_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (market_order.strategy_id, market_order.order_details, market_order.order_status, market_order.order_quantity, market_order.order_currency, market_order.order_price, market_order.order_type, market_order.order_action, market_order.order_parent_id))
        self.dbconn.conn.commit()
        
    def get_market_order_by_id(self, order_id):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        return row
    
    def get_all_market_orders(self):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders")
        rows = cursor.fetchall()
        return rows
    
    def get_market_orders_by_strategy(self, strategy_id):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE strategy_id = ?", (strategy_id,))
        rows = cursor.fetchall()
        return rows 
    
    def get_market_orders_by_status(self, order_status):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE order_status = ?", (order_status,))
        rows = cursor.fetchall()
        return rows 
    
    def get_market_orders_by_create_date(self, create_date):
        cursor = self.dbconn.conn.cursor()
        cursor.execute("SELECT * FROM market_orders WHERE create_date >= ?", (create_date,))
        rows = cursor.fetchall()
        return rows
    
    def update_market_order_status(self, order_id, new_status):
        cursor = self.dbconn.conn.cursor()
        cursor.execute(
            "UPDATE market_orders SET order_status = ?, update_date = CURRENT_TIMESTAMP WHERE order_id = ?",
            (new_status, order_id))
        self.dbconn.conn.commit()
        
    