import sys
import json
import logging
from importlib.resources import files

from app.utils.logger import LoggerManager
from app.data.strategy import Strategy
from app.dto.strategie_dto import StrategieDTO


logger = logging.getLogger(__name__)

def insert_strategy(dto, strategies):
    for strategy in strategies.get("strategies", []):
        logger.info(f"STRATEGY - {strategy}")
        dto.saveStrategy(Strategy.from_json(strategy))
       

def main(json_file_path: str):
    strategie_dto = StrategieDTO()
    
    # Load JSON data from the file
    with open(json_file_path, 'r') as file:
        strategies = json.load(file)
        logger.info(f"Loaded {len(strategies)} strategies from {json_file_path} - {strategies}")
        insert_strategy(strategie_dto, strategies)
        
    return
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python loadstrategy.py <path_to_json_file>")
        sys.exit(1)
        
    json_file_path = files('app.strategies').joinpath(sys.argv[1])
    
    main(json_file_path)