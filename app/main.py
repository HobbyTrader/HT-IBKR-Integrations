import logging
import string
import secrets
import sys
import threading

from typing import List

from app.data.strategy import Strategy
from app.data.instrument import Instrument

from app.dto.strategie_dto import StrategieDTO
from app.dto.scanner_dto import ScannerDTO

from app.services.scanner import ScannerService
from app.services.market import MarketService
from app.services.order import OrderService

from app.utils.logger import LoggerManager

# from app.utils.ordercoordinator import OrderCoordinator
LoggerManager()
logger = logging.getLogger(__name__)
tags = []
all_must_match = False

def generate_key(length=10) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def main():
    all_must_match = False
    if len(sys.argv) > 1:
        logger.info(f"Starting with arguments: TAGS = {sys.argv[1]}")
        tags = sys.argv[1].split(',')
        if len(sys.argv) > 2:
            logger.info(f"Starting with arguments: ALL_MATCH {sys.argv[2]}")
            all_must_match = sys.argv[2].lower() == 'true'
    else:
        logger.info("Starting without arguments.")
        
    strategie_dto = StrategieDTO()
    logger.info("[MAIN] - Starting HT-IBKR-Integrations Application")
    
    # Get strategies to process
    strategies: List[Strategy] = []
    if tags:
        strategies: List[Strategy] = strategie_dto.get_strategies_by_tags(tags, all_must_match)
    else:
        # strategies = strategie_dto.get_active_strategies()
        strategies.append(strategie_dto.get_strategy_by_id(1))
    
    for strategy in strategies:
        exec_key = generate_key()
        logger.info(f"STRATEGY - {strategy} - EXEC KEY - {exec_key}")
        # Get scanner market data
        with ScannerService(strategy.id, exec_key) as scanner_serv:
            scanner_serv.get_scanner_result(strategy)
    
        # Get the instrument candidates to perform the orders    
        scanner_dto = ScannerDTO()
        scanner_results = scanner_dto.get_instruments_by_exec_key(exec_key)
        
        instrument_candidates = [ ]
        for instrument in scanner_results:
            logger.info(f"SCANNER RESULT - {instrument}")
                      
            # Get market data for all scanner results
            with MarketService(instrument) as market_serv:
                market_serv.get_historical_day_data()
                logger.debug(f"DAILY HISTORY for {instrument.symbol} - {instrument.daily_history}")
                # Change this call and make the method in Strategy. 
                # Take the strategy into account to select candidates
                # Do the same to define the quantity to buy
                strategy.apply_strategy_on_instrument(instrument)
                
                # Update the candidate status in the scanner results table asynchronously
                t = threading.Thread(
                    target=scanner_dto.set_order_candidate, args=(exec_key, instrument.id, instrument.is_candidate)
                )
                t.start()
                
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