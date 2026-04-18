import logging
import string
import secrets
import sys
import threading
import subprocess
import base64

from typing import List, Optional
from dataclasses import dataclass

from app.data.strategy import Strategy
from app.data.instrument import Instrument

from app.dto.strategy_dto import StrategyDTO
from app.dto.scanner_dto import ScannerDTO
from app.dto.market_order_dto import MarketOrderDTO

from app.services.scanner import ScannerService
from app.services.market import MarketService
from app.services.order import OrderService

from app.utils.logger import LoggerManager
from app.utils import load_config_scheduler

LoggerManager()
logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_instrument_candidates = []
_instrument_candidate_ids = set()

TERMINAL_RETRYABLE_BUY_STATUSES = {"REJECTED", "CANCELLED", "APICANCELLED", "INACTIVE"}
    
@dataclass(frozen=True)
class ScanArguments:
    tags: List[str]
    all_must_match: bool

def generate_key(length=10) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def get_arguments() -> ScanArguments:
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
        tags = None
        all_must_match = False
    
    return ScanArguments(tags=tags, all_must_match=all_must_match)
        
def get_strategies(tags: List[str], all_must_match: bool, strategy_dto: Optional[StrategyDTO] = None) -> List[Strategy]:
    if strategy_dto is None:
        strategy_dto = StrategyDTO()
        
    if tags:
        return strategy_dto.get_strategies_by_tags(tags, all_must_match)
    else:
        return strategy_dto.get_active_strategies()
    
def get_scanner_results(strategy: Strategy, exec_key: str) -> List[Instrument]:        
    with ScannerService(strategy.id, exec_key) as scanner_serv:
        instruments = scanner_serv.get_scanner_result(strategy)
    
    return instruments

def get_instrument_market_data(instrument: Instrument) -> None:
    with MarketService(instrument) as market_serv:
        market_serv.get_historical_day_data()
        logger.debug(f"DAILY HISTORY for {instrument.symbol} - {instrument.daily_history}")
        
def update_scanner_result_candidate(exec_key: str, instrument: Instrument, scanner_dto: Optional[ScannerDTO] = None) -> None:
    if scanner_dto is None:
        scanner_dto = ScannerDTO()
        
    t = threading.Thread(
        target = scanner_dto.set_order_candidate, 
        args=(exec_key, instrument.id, instrument.is_candidate)
    )
    t.start()

def clean_non_candidates(exec_key: str, scanner_dto: Optional[ScannerDTO] = None) -> None:
    if scanner_dto is None:
        scanner_dto = ScannerDTO()
        
    scanner_dto.clean_non_candidates(exec_key)
   
def scheduler_stop():
    logger.info("Scheduler stop requested.")
    _stop_event.set()

def update_order_status():
    with OrderService() as order_serv:
        order_serv.get_active_orders()
        order_serv.get_completed_orders()


def has_buy_order_today(instrument: Instrument, market_order_dto: Optional[MarketOrderDTO] = None) -> bool:
    if market_order_dto is None:
        market_order_dto = MarketOrderDTO()

    todays_orders = market_order_dto.get_market_orders_by_contract_id_today(instrument.id)
    for order in todays_orders:
        if (order.order_action or "").upper() != "BUY":
            continue

        order_status = (order.order_status or "").upper()
        if order_status in TERMINAL_RETRYABLE_BUY_STATUSES:
            continue

        logger.info(
            "Instrument %s already has a BUY order today (order_id=%s, status=%s). Skipping.",
            instrument.symbol,
            order.order_id,
            order.order_status,
        )
        return True

    return False

def build_instrument_payload_b64(instrument: Instrument) -> str:
    payload_json = instrument.to_json()
    return base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("ascii")

def build_strategy_payload_b64(strategy: Strategy) -> str:
    payload_json = strategy.to_json()
    return base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("ascii")

def launch_asset_watcher(instrument: Instrument, strategy: Strategy) -> None:
    logger.info(f"Launching asset watcher for")
    logger.debug(f"Launching asset watcher for {instrument.symbol} and strategy {strategy.name} - {instrument}")
    cmd = [
        sys.executable,
        "-m",
        "app.asset_watcher",
        "--instrument-b64",
        build_instrument_payload_b64(instrument),
        "--strategy-b64",
        build_strategy_payload_b64(strategy),
    ]
    subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
                          
def main():  
    global _instrument_candidates
    global _instrument_candidate_ids
    
    scanner_dto = ScannerDTO()
    strategy_dto = StrategyDTO()  
    market_order_dto = MarketOrderDTO()
    logger.info("[MAIN] - Starting HT-IBKR-Integrations Application")
    arguments = get_arguments()  
    
    # Get strategies to process
    strategies = get_strategies(arguments.tags, arguments.all_must_match, strategy_dto)
    
    for strategy in strategies:
        exec_key = generate_key()
        logger.info(f"STRATEGY - {strategy.id} {strategy.name} - EXEC KEY - {exec_key}")
        
        # TODO: Add check on opening hours of the strategy to skip if outside allowed time
        # TODO: Add check on max trades per day already placed and keep track of trades placed today
        # TODO: Add final check on open positions to close them before market close
        # TODO: Review stop loss order if price gap up during the day. See details in strategy.
        # TODO: Add current open order status check to avoid placing duplicate orders
        # TODO: Add cleanup of scanner table for the non candidates after processing
        
        # Get scanner market data
        scanner_results = get_scanner_results(strategy, exec_key)
            
        for instrument in scanner_results:
            logger.info(f"SCANNER RESULT - {instrument}")

            # Check if instrument already has a BUY order in market_orders today.
            if has_buy_order_today(instrument, market_order_dto):
                continue
            
            # Check if instrument already candidate previously in the day to avoid placing multiple orders for the same instrument
            if instrument.id in _instrument_candidate_ids:
                logger.info(f"Instrument {instrument.symbol} already processed as candidate for strategy {strategy.name}. Skipping.")
                continue
            # Get market data for all scanner results (History, etc) and set candidate status
            get_instrument_market_data(instrument)
                
            strategy.apply_strategy_on_instrument(instrument)
            
            # Update the candidate status in the scanner results table asynchronously
            update_scanner_result_candidate(exec_key, instrument, scanner_dto)
                
            if(instrument.is_candidate):                
                # Place orders for the candidates (specify any clientId if needed to separate order streams)
                with OrderService() as order_serv:
                    logger.info(f"Placing order for {instrument.symbol} for strategy {strategy.name}")
                    order_placed = order_serv.place_bracket_order(instrument)
                    logger.info(f"Order placed for {instrument.symbol} for strategy {strategy.name}: {order_placed}- {instrument}")
                    # Launch watcher only for accepted orders.
                    if order_placed:
                        launch_asset_watcher(instrument, strategy)
                    else:
                        logger.warning(f"Order for {instrument.symbol} was rejected. Asset watcher will not be started.")
                    
                if order_placed:
                    _instrument_candidates.append(instrument)
                    _instrument_candidate_ids.add(instrument.id)
                
                # Stop if reached max candidates defined in strategy - MAX_TRADES_PER_DAY
                if(len(_instrument_candidates) >= strategy.details.max_trades_per_day):
                    logger.info(f"Reached max candidates for strategy {strategy.id} - {strategy.name}. Stopping processing more scanner results.")
                    scheduler_stop()
                    break
        
        clean_non_candidates(exec_key, scanner_dto)
        update_order_status()
        

def run_scheduler():
    config_scheduler_scanner = load_config_scheduler().get("scanner", {})
    logger.info(f"Loaded scheduler configuration for scanner: {config_scheduler_scanner}")
    
    if not config_scheduler_scanner.get("enabled", False):
        logger.info("Scanner scheduler is disabled in configuration. Only 1 execution will be performed.")
        main()
        scheduler_stop()
        return
    
    interval = config_scheduler_scanner.get("interval", 60)
    logger.info(f"Starting scheduler with interval {interval} seconds.")
    
    while not _stop_event.is_set():
        main()
        logger.info(f"Scheduler sleeping for {interval} seconds...")
        _stop_event.wait(interval)
        
                
    logger.info("HT-IBKR-Integrations Application Finished")
            
if __name__ == "__main__":
    run_scheduler()