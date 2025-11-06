import sys
import json

from app.core import load_config
from app.utils.logger import LoggerManager
from app.utils.sqllitemanager import SQLiteManager

def main(logger: LoggerManager, json_file_path: str):
    dbconn = SQLiteManager(logger, config.get("database"))
    cursor = dbconn.conn.cursor()
    
    # Load JSON data from the file
    with open(json_file_path, 'r') as file:
        stategies = json.load(file)
        
    return
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python loadstrategy.py <path_to_json_file>")
        sys.exit(1)
        
    config = load_config()
    logger = SQLiteManager.initialize(config.get("logging"))
    json_file_path = sys.argv[1]
    # dbconn = initDatabase(logger, config.get("database"))
    
    main(logger, json_file_path)