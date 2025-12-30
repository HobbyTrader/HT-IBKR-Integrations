import logging
from typing import List

from app.data.strategy import Strategy, StrategyDetail
from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class StrategieDTO:
    def __init__(self):
        self.dbconn = SQLiteManager()
        
    def row_to_strategy(self, row) -> Strategy:
        # Convert a database row to a Strategy object
        logger.debug(f"[StrategieDTO] - Converting row to Strategy: {row}")
        id = row[0]
        name = row[1]
        tags = row[2]
        details_json = row[3]
        logger.debug(f"[StrategieDTO] - Strategy details JSON: {details_json}")
        details_obj = StrategyDetail.from_json(details_json)
        return Strategy(id=id, name=name, details=details_obj)
    
    def save_strategy(self, strategy: Strategy):
        cursor = self.dbconn.get_cursor()
        logger.debug(f"[StrategieDTO] - save Strategy.")
        cursor.execute("""INSERT INTO strategies (strategy_name, strategy_tags, strategy_details) VALUES (?, ?, ?)""",
                            (strategy.name, str(strategy.tags), strategy.details.to_json()))
        self.dbconn.get_connection().commit()
    
    def get_active_strategies(self)-> list[Strategy]:
        cursor = self.dbconn.get_cursor()
        cursor.execute("SELECT strategy_id, strategy_name, strategy_tags, strategy_details FROM strategies where is_active = 1")
        rows = cursor.fetchall()
        
        strategies = []
        for row in rows:
            # Create Strategy object
            strategy = self.row_to_strategy(row)
            strategies.append(strategy)
        
        return strategies
    
    def get_strategy_by_name(self, strategy_name):
        cursor = self.dbconn.get_cursor()
        cursor.execute("SELECT * FROM strategies WHERE strategy_name = ?", (strategy_name,))
        first = cursor.fetchone()
        if not first:
            return None
        
        return self.row_to_strategy(first) 
    
    def get_strategy_by_id(self, strategy_id) -> Strategy:
        cursor = self.dbconn.get_cursor()
        cursor.execute("SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,))
        row = cursor.fetchone()
        if row:
            return self.row_to_strategy(row)
        else:
            return None
        
    def get_strategies_by_tags(self, tags: List[str], all_must_match: bool=False) -> List[Strategy]:
        cursor = self.dbconn.get_cursor()
        logger.debug(f"[StrategieDTO] - Getting Strategies by tags: {tags}")
        # Convert tags to a list of strings if it's a single string
        if isinstance(tags, str):
            tags = [tags]
            
        # Create condition for SQL query based on all_must_match flag
        str_condition = ["strategy_tags LIKE ?"] * len(tags) 
        condition = ' AND '.join(str_condition) if all_must_match else ' OR '.join(str_condition)
        params = [f'%{tag}%' for tag in tags]
        
        logger.info(f"[StrategieDTO] - SQL Condition: {condition}, Params: {params}")

        cursor.execute(f"SELECT strategy_id, strategy_name, strategy_tags, strategy_details FROM strategies WHERE {condition}", params)
        
        rows = cursor.fetchall()
        
        strategies = []
        for row in rows:
            # Create Strategy object
            strategy = self.row_to_strategy(row)
            strategies.append(strategy)
        
        return strategies

    def deactivate_strategy(self, strategy_id):
        cursor = self.dbconn.get_cursor()
        logger.debug(f"[StrategieDTO] - Deactivating Strategy ID: {strategy_id}.")
        cursor.execute("UPDATE strategies SET is_active = 0, update_date = CURRENT_TIMESTAMP WHERE strategy_id = ?", (strategy_id,))
        self.dbconn.get_connection().commit()
        
    def update_strategy(self, strategy_id, strategy: Strategy):
        cursor = self.dbconn.get_cursor()
        logger.debug(f"[StrategieDTO] - Updating Strategy ID: {strategy_id}.")
        cursor.execute("UPDATE strategies SET strategy_name = ?, strategy_tags = ?, strategy_details = ?, update_date = CURRENT_TIMESTAMP WHERE strategy_id = ?",
                       (strategy.name, str(strategy.tags), strategy.details.to_json(), strategy_id))
        self.dbconn.get_connection().commit()
    
    # def get_all_schedules(self):
    #     cursor = self.dbconn.get_cursor()
    #     cursor.execute("SELECT * FROM strategies")
    #     rows = cursor.fetchall()
    #     return rows
    