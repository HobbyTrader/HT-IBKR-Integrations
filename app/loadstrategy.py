import sys
import json
import logging
from importlib.resources import files

from app.utils.logger import LoggerManager
from app.data.strategy import Strategy
from app.dto.strategie_dto import StrategieDTO

LoggerManager()
logger = logging.getLogger(__name__)

def insert_strategy(dto, strategies):
    for strategy_json in strategies.get("strategies", []):
        logger.info(f"STRATEGY - {strategy_json}")
        strategy = Strategy.from_json(strategy_json)
        strategy_db = dto.get_strategy_by_name(strategy.name)
        if strategy_db:
            logger.info(f"Strategy {strategy.name} already exists. Update existing strategy.")
            dto.update_strategy(strategy_db.id, strategy)
            continue
        dto.save_strategy(strategy)
       

def main():
    logger.info("Starting strategy loader...")
    if len(sys.argv) != 2:
        print("Usage: python loadstrategy.py <path_to_json_file>")
        sys.exit(1)
        
    json_file_path = files('app.strategies').joinpath(sys.argv[1])
    strategie_dto = StrategieDTO()
    
    # Load JSON data from the file
    with open(json_file_path, 'r') as file:
        strategies = json.load(file)
        logger.info(f"Loaded {len(strategies)} strategies from {json_file_path} - {strategies}")
        insert_strategy(strategie_dto, strategies)
        
    return
    
if __name__ == "__main__":    
    main()