from dataclasses import dataclass
import logging
import sys
from time import time
from typing import List

from app.dto.market_order_dto import MarketOrderDTO
from app.dto.strategy_dto import StrategyDTO
from app.utils.logger import LoggerManager

LoggerManager("WATCHER")
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

def get_orders_by_strategy(orders: List, strategy_id: int):
    """Get all orders for a specific strategy."""
    return [order for order in orders if order.strategy_id == strategy_id]

def get_orders_by_status(orders: List, status: str):
    """Get all orders with a specific status."""
    return [order for order in orders if order.order_status == status]

def get_orders_by_status(orders: List, statuses: List[str]):
    """Get all orders with any of the specified statuses.
    
    Args:
        orders: List of MarketOrder objects
        statuses: List of status strings to filter by (e.g., ["NEW", "OPEN", "PARTIALLY_FILLED"])
    
    Returns:
        List of orders matching any of the provided statuses
    """
    return [order for order in orders if order.order_status in statuses]

def main():
    strategy_dto = StrategyDTO()
    market_order_dto = MarketOrderDTO()
    logger.info("Order watcher started")
    
    args = get_arguments()
    strategies = strategy_dto.get_strategies_by_tags(args.tags, args.all_must_match)
    
    full_orders_from_DB = [
        order
        for strategy in strategies
        for order in market_order_dto.get_market_orders_by_strategy_today(strategy.id)
    ]
    
    logger.info(f"Found {len(full_orders_from_DB)} orders to watch for strategies with tags {args.tags}")    
    
    while True:
        # Placeholder for order watching logic
        logger.info("Watching orders...")
        
        for strategy in strategies:
            # Don't check orders if market is already closed
            check_market_hours = strategy.is_market_open_now()
            if not check_market_hours:
                logger.info(f"Market is closed for strategy {strategy.name}. Skipping order checks.")
                break
            
            # TODO : Add logic to update order statuses via IBKR API
            
            # Cancel orders and SELL everything before market close?
            if(strategy.is_time_to_sell_before_close()):
                logger.info(f"Time to sell before market close for strategy {strategy.name}. Cancelling orders and selling positions.")
                # TODO : Implement logic to cancel all open orders and sell all positions via IBKR API
                continue
            
            strategy_orders = get_orders_by_strategy(full_orders_from_DB, strategy.id)
            logger.info(f"Strategy {strategy.name} has {len(strategy_orders)} orders today.")
            
            # TODO : Implement logic to check order statuses via IBKR API   
                
        # TODO : Get all openned orders and refresh their status (Only 1 call to IBKR API for all orders!!!!!!). can wait for the multiple callbacks
        # TODO : For each openned order, check if it needs to be modified or cancelled
        # TODO : For each openned order, check if it has been filled and update positions accordingly
        
        # Sleep for a defined interval before checking again        
        # TODO : Get sleeping time from config
        time.sleep(300)  # Sleep for 5 minutes
        
        # TODO : Add graceful shutdown handling before market closing hours
        
        
if __name__ == "__main__":
    main()