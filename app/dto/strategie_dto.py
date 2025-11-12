import logging

from app.data.strategy import Strategy, StrategyDetail
from app.utils.sqllitemanager import SQLiteManager
from app.utils.logger import LoggerManager

logger = logging.getLogger(__name__)

class StrategieDTO:
    def __init__(self):
        self.dbconn = SQLiteManager()
        
    def row_to_strategy(self, row) -> Strategy:
        # Convert a database row to a Strategy object
        logger.debug(f"[StrategieDTO] - Converting row to Strategy: {row}")
        id = row[0]
        name = row[1]
        details_json = row[2]
        details_obj = StrategyDetail.from_json(details_json)
        return Strategy(id=id, name=name, details=details_obj)
    
    def saveStrategy(self, strategy: Strategy):
        cursor = self.dbconn.get_cursor()
        logger.debug(f"[StrategieDTO] - save Strategy.")
        cursor.execute("""INSERT INTO strategies (strategy_name, strategy_details) VALUES (?, ?)""",
                            (strategy.name, strategy.details.to_json()))
        self.dbconn.get_connection().commit()
    
    def getActiveStrategies(self):
        cursor = self.dbconn.get_cursor()
        cursor.execute("SELECT strategy_id, strategy_name, strategy_details FROM strategies where is_active = 1")
        rows = cursor.fetchall()
        
        strategies = []
        for row in rows:
            # Create Strategy object
            strategy = self.row_to_strategy(row)
            strategies.append(strategy)
        
        return strategies
    
    def getStrategyByName(self, strategy_name):
        cursor = self.dbconn.get_cursor()
        cursor.execute("SELECT * FROM strategies WHERE strategy_name = ?", (strategy_name,))
        row = cursor.fetchall()
        return self.row_to_strategy(row) if row else None
    
    def deactivateStrategy(self, strategy_id):
        cursor = self.dbconn.get_cursor()
        logger.debug(f"[StrategieDTO] - Deactivating Strategy ID: {strategy_id}.")
        cursor.execute("UPDATE strategies SET is_active = 0, update_date = CURRENT_TIMESTAMP WHERE strategy_id = ?", (strategy_id,))
        self.dbconn.get_connection().commit()
    
    
    