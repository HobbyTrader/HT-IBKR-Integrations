from dataclasses import dataclass
import logging
import sys
from time import time, sleep
from typing import List

from app.dto.market_order_dto import MarketOrderDTO
from app.dto.strategy_dto import StrategyDTO
from app.services.order import OrderService
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
    
    # Initialize OrderService for IBKR operations
    order_service = None
    liquidation_executed = False
    
    try:
        while True:
            # Placeholder for order watching logic
            logger.info("Watching orders...")
            
            for strategy in strategies:
                # Don't check orders if market is already closed
                check_market_hours = strategy.is_market_open_now()
                if not check_market_hours:
                    logger.info(f"Market is closed for strategy {strategy.name}. Skipping order checks.")
                    break
                
                # Check if it's time to cancel orders and sell positions before market close
                if strategy.is_time_to_sell_before_close():
                    if not liquidation_executed:
                        logger.info(f"Time to liquidate positions for strategy {strategy.name} before market close.")
                        
                        # Initialize OrderService if not already done
                        if order_service is None:
                            order_service = OrderService(clientId=999)  # Use unique client ID for watcher
                            order_service.open_connection()
                            sleep(2)  # Wait for connection to establish
                        
                        # Cancel all open orders and sell all positions
                        order_service.cancel_orders_and_sell_positions()
                        liquidation_executed = True
                        logger.info("Liquidation completed. Continuing to monitor...")
                
                strategy_orders = get_orders_by_strategy(full_orders_from_DB, strategy.id)
                logger.info(f"Strategy {strategy.name} has {len(strategy_orders)} orders today.")
                
                # TODO : Implement logic to check order statuses via IBKR API   
                    
            # TODO : Get all openned orders and refresh their status (Only 1 call to IBKR API for all orders!!!!!!). can wait for the multiple callbacks
            # TODO : For each openned order, check if it needs to be modified or cancelled
            # TODO : For each openned order, check if it has been filled and update positions accordingly
            
            # Sleep for a defined interval before checking again        
            # TODO : Get sleeping time from config
            sleep(300)  # Sleep for 5 minutes
            
    except KeyboardInterrupt:
        logger.info("Order watcher interrupted by user.")
    except Exception as e:
        logger.exception(f"Error in order watcher: {e}")
    finally:
        # Clean up connection
        if order_service is not None:
            logger.info("Closing IBKR connection...")
            order_service.close_connection()
        logger.info("Order watcher stopped.")
        
        
if __name__ == "__main__":
    main()