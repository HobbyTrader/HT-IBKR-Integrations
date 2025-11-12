import logging

from ibapi.wrapper import EWrapper
from ibapi.client import *
# from ibapi.ticktype import TickTypeEnum
from ibapi.tag_value import *

from app.dto.strategie_dto import StrategieDTO
from app.dto.scanner_dto import ScannerDTO
from app.services.scanner import ScannerService
from app.services.market import MarketService
from app.utils.logger import LoggerManager
from app.utils.sqllitemanager import SQLiteManager


logger = logging.getLogger(__name__)


def main():
    strategie_dto = StrategieDTO()
    logger.info("[MAIN] - Starting HT-IBKR-Integrations Application")
    
    # Get strategies
    strategies = strategie_dto.getActiveStrategies()
    for strategy in strategies:
        logger.info(f"STRATEGY - {strategy}")

        # Get scanner market data
        with ScannerService(strategy.id) as scanner:
            scanner.get_scannerResult(strategy)
        
    
    # instrument_candidates = scanner_dto.getDetailsByReqId()
    
    # Request realtime market data in time bars
    
    # myContract = Contract()
    # myContract.symbol = "LPTX"
    # myContract.secType = "STK"
    # myContract.currency = "USD"
    # myContract.exchange = "SMART"
    
    # with MarketService() as app:
    #     app.get_realtime_bars(myContract)

    # app.reqContractDetails(app.nextId(), myContract)

    

    # app.reqMarketDataType(3)  # 3 = Delayed 10-20min
    # app.reqMktData(app.nextId(), myContract, "225,232", False, False, [])

    # app.reqRealTimeBars(app.nextId(), myContract, 5, "TRADES", False, [])
    # app.reqHistoricalData(app.nextId(), myContract, "", "1 D", "1 mins", "TRADES", 1, 1, False, [] )


    logger.info("HT-IBKR-Integrations Application Finished")
    

if __name__ == "__main__":
    
    main()