from dataclasses import dataclass
import logging
import sys
import threading
import subprocess
from time import time
from typing import List

from app.dto.market_order_dto import MarketOrderDTO
from app.dto.strategy_dto import StrategyDTO
from app.services.order import OrderService
from app.utils import load_config_scheduler
from app.utils.logger import LoggerManager
from app.close_open_positions import close_position_from_strategy

LoggerManager("WATCHER")
logger = logging.getLogger(__name__)

_stop_event = threading.Event()

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

def get_orders_by_status(orders: List, statuses: List[str]):
    """Get all orders with any of the specified statuses.
    
    Args:
        orders: List of MarketOrder objects
        statuses: List of status strings to filter by (e.g., ["NEW", "OPEN", "PARTIALLY_FILLED"])
    
    Returns:
        List of orders matching any of the provided statuses
    """
    return [order for order in orders if order.order_status in statuses]

def update_order_status():
    with OrderService() as order_serv:
        order_serv.get_active_orders()
        order_serv.get_completed_orders()
        
def scheduler_stop():
    logger.info("Scheduler stop requested.")
    _stop_event.set()

def fire_and_forget_close_positions(strategy_id: int | None = None) -> None:
    cmd = [sys.executable, "app/close_open_positions.py"]
    if strategy_id is not None:
        cmd.append(str(strategy_id))
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        
def main():
    strategy_dto = StrategyDTO()
    market_order_dto = MarketOrderDTO()
    logger.info("Order watcher started")
    
    args = get_arguments()
    strategies = strategy_dto.get_strategies_by_tags(args.tags, args.all_must_match)
           
    for strategy in strategies:
        # Don't check orders if market is already closed
        if not strategy.is_market_open_now():
            logger.info(f"Market is closed for strategy {strategy.name}. Skipping order checks and stopping the watcher")
            scheduler_stop()
            break
        
        # Cancel orders and SELL everything before market close?
        if(strategy.is_time_to_sell_before_close()):
            logger.info(f"Time to sell before market close for strategy {strategy.name}. Cancelling orders and selling positions.")
            
            #Execute in an asynchronous thread to avoid blocking the main loop and allow other strategies to be processed
            # t = threading.Thread(
            #     target=close_position_from_strategy, #from close_open_position.py script
            #     args=(strategy.id,)
            # )
            # t.start()
            
            #Start the close position process in a separate process to avoid blocking the main loop and allow other strategies to be processed
            fire_and_forget_close_positions(strategy.id)
            
        else:
            update_order_status()  
        
            today_strategy_orders = market_order_dto.get_market_orders_by_strategy_today(strategy.id)
            logger.info(f"Strategy {strategy.name} has {len(today_strategy_orders)} orders today.")
            
            for order in today_strategy_orders:
                logger.info(f"Order ID: {order.order_id}, Contract ID: {order.contract_id}, Status: {order.order_status}")
                # TODO: Check current market value in order to sell if 30%, 70% of target reached and adapt stop loss and target orders in consequence. See details in strategy.
                # TODO: Get initialtarget price from DB.
                #       Based on the current price sell part of the position. Take the value from the strategy (e.g., sell 50% of position at 30% gain, move stop loss to break even at 30% gain, sell remaining 50% at 70% gain, etc.)
                #       Adapt stop loss and target orders in consequence. See details in strategy.
            
        
def run_scheduler():
    config_scheduler_watcher = load_config_scheduler().get("watcher", {})
    logger.info(f"Loaded scheduler configuration for watcher: {config_scheduler_watcher}")
    
    if not config_scheduler_watcher.get("enabled", False):
        logger.info("Watcher scheduler is disabled in configuration. Only 1 execution will be performed.")
        main()
        scheduler_stop()
        return
    
    interval = config_scheduler_watcher.get("interval", 300)
    logger.info(f"Starting watcher scheduler with interval {interval} seconds.")
    
    while not _stop_event.is_set():
        main()
        logger.info(f"Watcher scheduler sleeping for {interval} seconds...")
        _stop_event.wait(interval)
               
if __name__ == "__main__":
    run_scheduler()