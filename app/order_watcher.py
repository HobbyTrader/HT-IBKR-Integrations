from dataclasses import dataclass
import logging
import sys
from time import time
from typing import List

from app.dto.market_order_dto import MarketOrderDTO
from app.dto.strategy_dto import StrategyDTO
from app.utils.logger import LoggerManager

LoggerManager()
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class WatcherArguments:
    tags: List[str]
    all_must_match: bool

def get_arguments() -> WatcherArguments:
    if len(sys.argv) > 1:
        logger.info(f"Starting with arguments: TAGS = {sys.argv[1]}")
        tags = sys.argv[1].split(',')
        if len(sys.argv) > 2:
            logger.info(f"Starting with arguments: ALL_MATCH {sys.argv[2]}")
            all_must_match = sys.argv[2].lower() == 'true'
        else:
            all_must_match = False
    else:
        logger.info("Starting without arguments.")
    
    return WatcherArguments(tags=tags, all_must_match=all_must_match)

def main():
    strategy_dto = StrategyDTO()
    market_order_dto = MarketOrderDTO()
    
    args = get_arguments()
    strategies = strategy_dto.get_strategies_by_tags(args.tags, args.all_must_match)
    
    for strategy in strategies:
        # TODO : If outside market hours, skip watching and exit
        logger.info(f"Watching strategy: {strategy.name} (ID: {strategy.id})")
        orders_today = market_order_dto.get_market_orders_by_strategy_today(strategy.id)
    
    logger.info("Order watcher started")
    
    while True:
        # Placeholder for order watching logic
        logger.info("Watching orders...")
        # TODO: Implement order checking and processing logic here
        
        # TODO : Get all openned orders and refresh their status (Only 1 call to IBKR API for all orders!!!!!!). can wait for the multiple callbacks
        # TODO : For each openned order, check if it needs to be modified or cancelled
        # TODO : For each openned order, check if it has been filled and update positions accordingly
        
        # Sleep for a defined interval before checking again
        
        # TODO : Get sleeping time from config
        time.sleep(300)  # Sleep for 5 minutes
        
        # TODO : Add graceful shutdown handling before market closing hours
        
        
if __name__ == "__main__":
    main()