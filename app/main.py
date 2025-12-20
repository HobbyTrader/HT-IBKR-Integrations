import logging
import string
import secrets

from typing import List
from concurrent.futures import ThreadPoolExecutor, wait

from app.data.instrument import Instrument
from app.data.strategy import Strategy
from app.dto.strategie_dto import StrategieDTO
from app.dto.scanner_dto import ScannerDTO

from app.services.scanner import ScannerService
from app.services.market import MarketService
from app.services.order import OrderService

# from app.utils.ordercoordinator import OrderCoordinator

logger = logging.getLogger(__name__)

def generate_key(length=10) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

# def fire_generate_orders(instrument, clientId=None):
#     order_service = OrderService(clientId) if clientId is not None else OrderService()
#     with order_service as order_serv:
#         order_serv.PlaceBracketOrder(instrument)

def main():
    strategie_dto = StrategieDTO()
    logger.info("[MAIN] - Starting HT-IBKR-Integrations Application")
    
    # Get strategies
    # strategies = strategie_dto.get_active_strategies()
    strategies: List[Strategy] = []
    strategies.append(strategie_dto.get_strategy_by_id(1))
    
    for strategy in strategies:
        # coordinator = OrderCoordinator() 
        
        logger.info(f"STRATEGY - {strategy}")
        exec_key = generate_key()
        logger.info(f"EXEC KEY - {exec_key}")
        # Get scanner market data
        with ScannerService(strategy.id, exec_key) as scanner_serv:
            scanner_serv.get_scannerResult(strategy)
    
        # Get the instrument candidates to perform the orders    
        scanner_dto = ScannerDTO()
        scanner_results = scanner_dto.get_instrumentsByExecKey(exec_key)
        
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
                
            if(instrument.is_candidate):
                with OrderService(1) as order_serv:
                    order_serv.PlaceBracketOrder(instrument)
                instrument_candidates.append(instrument)
                scanner_dto.set_order_candidate(exec_key, instrument.id, instrument.is_candidate)
                # Stop if reached max candidates defined in strategy - MAX_TRADES_PER_DAY
                if(len(instrument_candidates) >= strategy.details.max_trades_per_day):
                    break
                
                
                
        # Generate orders for candidates
        # for instrument in instrument_candidates:
        #     logger.info(f"INSTRUMENT CANDIDATE - {instrument}")
            
        #     # Get market data for order candidates
        #     with OrderService() as order_serv:
        #         order_serv.PlaceBracketOrder(instrument)
            
            
        # with ThreadPoolExecutor(max_workers=4) as executor:
        #     futures = [
        #         executor.submit(fire_generate_orders, instrument, clientId = coordinator.get_next_clientId()) 
        #         for instrument in instrument_candidates]
        #     wait(futures)
            
        # coordinator.wait_all_orders()


    logger.info("HT-IBKR-Integrations Application Finished")
    

if __name__ == "__main__":
    main()