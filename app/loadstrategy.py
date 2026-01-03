import sys
import json
import logging
from importlib.resources import files

from app.utils.logger import LoggerManager
from app.data.strategy import Strategy
from app.dto.strategy_dto import StrategyDTO

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
       

def main(json_file_path: str = None):
    """Load strategies from JSON file.
    
    Args:
        json_file_path: Optional path to JSON file. If not provided, uses sys.argv[1].
    """
    logger.info("Starting strategy loader...")
    
    # If no path provided, try to get from command-line arguments
    if json_file_path is None:
        if len(sys.argv) < 2:
            logger.error("No file path provided")
            print("Usage: loadstrategy <path_to_json_file>")
            return sys.exit(1)
        json_file_path = sys.argv[1]
    
    # Resolve file path from package resources
    if not json_file_path.startswith('/'):
        json_file_path = files('app.strategies').joinpath(json_file_path)
    
    strategy_dto = StrategyDTO()
    
    # Load JSON data from the file
    with open(json_file_path, 'r') as file:
        strategies = json.load(file)
        logger.info(f"Loaded {len(strategies.get('strategies', []))} strategies from {json_file_path}")
        insert_strategy(strategy_dto, strategies)
    
if __name__ == "__main__":    
    main()