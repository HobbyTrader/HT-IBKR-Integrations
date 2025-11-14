import logging
import string
import secrets

from app.data.instrument import Instrument
from app.data.strategy import Strategy
from app.dto.strategie_dto import StrategieDTO
from app.dto.scanner_dto import ScannerDTO

from app.services.scanner import ScannerService
from app.services.market import MarketService
from app.services.order import OrderService

logger = logging.getLogger(__name__)

def generate_key(length=10) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def main():
    strategie_dto = StrategieDTO()
    logger.info("[MAIN] - Starting HT-IBKR-Integrations Application")
    
    # Get strategies
    # strategies = strategie_dto.getActiveStrategies()
    strategies = list[Strategy]()
    strategies.append(strategie_dto.get_strategyById(3))
    
    for strategy in strategies:
        logger.info(f"STRATEGY - {strategy}")
        exec_key = generate_key()
        logger.info(f"EXEC KEY - {exec_key}")
        # Get scanner market data
        with ScannerService(strategy.id, exec_key) as scanner_serv:
            scanner_serv.get_scannerResult(strategy)
    
        # Get the instrument candidates to perform the orders    
        scanner_dto = ScannerDTO()
        scanner_results = scanner_dto.get_instrumentByExecKey(exec_key)
        
        candidate_count = strategy.details.max_trades_per_day
        for instrument in scanner_results:
            logger.info(f"SCANNER RESULT - {instrument}")
                      
            # Get market data for all scanner results
            with MarketService(instrument) as market_serv:
                market_serv.get_historical_day_data()
                logger.debug(f"DAILY HISTORY for {instrument.symbol} - {instrument.daily_history}")
                is_candidate = instrument.is_order_candidate()
                scanner_dto.set_orderCandidate(exec_key, instrument.id, is_candidate)
                # Stop if reached max candidates defined in strategy - MAX_TRADES_PER_DAY
                if(is_candidate):
                    candidate_count -= 1
                if(candidate_count <= 0):
                    break
                
        # Generate orders for candidates
        # instrument_candidates = scanner_dto.get_instrument_candidates(exec_key)
        # for instrument in instrument_candidates:
        #     logger.info(f"INSTRUMENT CANDIDATE - {instrument}")
            
        #     # Get market data for order candidates
        #     with OrderService(strategy.id) as order_serv:
        #         order_serv.buy_order(instrument)
        #         order_serv.create_stoploss(instrument)
        #         order_serv.create_takeprofit(instrument)


    logger.info("HT-IBKR-Integrations Application Finished")
    

if __name__ == "__main__":
    
    main()