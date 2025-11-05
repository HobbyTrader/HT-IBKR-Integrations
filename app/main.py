import time
import threading

from app.core import load_config
from app.core.sqllite import SQLiteManager

from ibapi.wrapper import EWrapper
from ibapi.client import *
# from ibapi.ticktype import TickTypeEnum
from ibapi.tag_value import *

from app.services.scanner import ScannerService
from app.utils.logger import LoggerManager

# Initialize Logger
def initLogger(config):
    LoggerManager.initialize(config)
    logger = LoggerManager.get_logger()
    logger.info("[MAIN] - Logging initialized successfully.")
    return logger

# Initialize Database
def initDatabase(logger: LoggerManager, config):
    dbconn = SQLiteManager(logger, config)
    logger.info("[MAIN] - Database initialized successfully.")
    return dbconn.get_connection()

def main(logger: LoggerManager, dbconn: SQLiteManager):
    logger.debug("[MAIN] - Starting HT-IBKR-Integrations Application")

    # Get scanner market data
    ibkr_config = config.get("IBKR", {})
    with ScannerService(ibkr_config, logger, dbconn) as scanner:
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "HIGH_OPEN_GAP" # Top % Gainers After Hours

        scan_options = []   

        filter_options = [
            TagValue("volumeAbove", "10000"),
            TagValue("priceAbove", "10"),
            TagValue("priceBelow", "50"),]

        scanner.get_scannerResult(scanSub, scan_options, filter_options)
    
    # Request realtime market data in time bars
    
    # myContract = Contract()
    # myContract.symbol = "AAPL"
    # myContract.secType = "STK"
    # myContract.currency = "USD"
    # myContract.exchange = "SMART"

    # app.reqContractDetails(app.nextId(), myContract)

    

    # app.reqMarketDataType(3)  # 3 = Delayed 10-20min
    # app.reqMktData(app.nextId(), myContract, "225,232", False, False, [])

    # app.reqRealTimeBars(app.nextId(), myContract, 5, "TRADES", False, [])
    # app.reqHistoricalData(app.nextId(), myContract, "", "1 D", "5 mins", "TRADES", 1, 1, False, [] )


    logger.debug("HT-IBKR-Integrations Application Finished")
    

if __name__ == "__main__":
    config = load_config()
    logger = initLogger(config.get("logging"))
    dbconn = initDatabase(logger, config.get("database"))
    
    main(logger, dbconn)