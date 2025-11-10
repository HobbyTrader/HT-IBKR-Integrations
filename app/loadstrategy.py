import sys
import json
import logging
from importlib.resources import files


from app import load_config
from app.utils.logger import LoggerManager
from app.utils.sqllitemanager import SQLiteManager


logger = logging.getLogger(__name__)

def insert_strategy(cursor, strategies):
    for strategy in strategies.get("strategies", []):
        logger.info(f"STRATEGY - {strategy}")
        cursor.execute("""
            INSERT INTO strategies (strategy_name, strategy_details)
            VALUES (?, ?)
        """, (
            strategy.get("name"),
            json.dumps(strategy.get("details"), indent=2)
        ))
    cursor.connection.commit()

def main(json_file_path: str):
    dbconn = SQLiteManager()
    cursor = dbconn.conn.cursor()
    
    # Load JSON data from the file
    with open(json_file_path, 'r') as file:
        strategies = json.load(file)
        logger.info(f"Loaded {len(strategies)} strategies from {json_file_path} - {strategies}")
        insert_strategy(cursor, strategies)
        
    return
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python loadstrategy.py <path_to_json_file>")
        sys.exit(1)
        
    json_file_path = files('app.strategies').joinpath(sys.argv[1])
    # dbconn = initDatabase(logger, config.get("database"))
    
    main(json_file_path)