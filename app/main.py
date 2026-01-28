import logging
import string
import secrets
import sys
import threading

from typing import List, Optional
from dataclasses import dataclass

from app.data.strategy import Strategy
from app.data.instrument import Instrument

from app.dto.strategy_dto import StrategyDTO
from app.dto.scanner_dto import ScannerDTO

from app.services.scanner import ScannerService
from app.services.market import MarketService
from app.services.order import OrderService

from app.utils.logger import LoggerManager

LoggerManager()
logger = logging.getLogger(__name__)
    
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
            
def main():  
    scanner_dto = ScannerDTO()
    strategy_dto = StrategyDTO()  
    logger.info("[MAIN] - Starting HT-IBKR-Integrations Application")
    arguments = get_arguments()  
    
    # Get strategies to process
    strategies = get_strategies(arguments.tags, arguments.all_must_match, strategy_dto)
    
    for strategy in strategies:
        instrument_candidates = []
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
                      
            # Get market data for all scanner results (History, etc) and set candidate status
            get_instrument_market_data(instrument)
                
            strategy.apply_strategy_on_instrument(instrument)
            
            # Update the candidate status in the scanner results table asynchronously
            update_scanner_result_candidate(exec_key, instrument, scanner_dto)
                
            if(instrument.is_candidate):                
                # Place orders for the candidates (specify any clientId if needed to separate order streams)
                with OrderService(1) as order_serv:
                    order_serv.place_bracket_order(instrument)
                    
                instrument_candidates.append(instrument)
                
                # Stop if reached max candidates defined in strategy - MAX_TRADES_PER_DAY
                if(len(instrument_candidates) >= strategy.details.max_trades_per_day):
                    break
                
    logger.info("HT-IBKR-Integrations Application Finished")
    
if __name__ == "__main__":
    main()