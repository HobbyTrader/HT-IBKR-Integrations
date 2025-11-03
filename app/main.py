import time
import threading

from app.core import load_config
from app.core.ibapi import IBApi

from ibapi.wrapper import EWrapper
from ibapi.client import *
from ibapi.ticktype import TickTypeEnum
from ibapi.tag_value import *

from app.services.scanner import ScannerService
from app.utils.logger import LoggerManager


def main():
    config = load_config()

    LoggerManager.initialize(config.get("logging"))
    logger = LoggerManager.get_logger()
    logger.info("Logging initialized successfully.")

    logger.info("Starting HT-IBKR-Integrations Application")

    # Initialize services

    scanner = ScannerService(config.get("IBKR"))
    scanner.connect(config["IBKR"]["HOST"], config["IBKR"]["PORT"], config["IBKR"]["CLIENTID"])
    
    threading.Thread(target=scanner.run).start()
    time.sleep(1)

    # logging.info("Requesting Market Data...")
    scanner.get_parameters()

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
    scanner.disconnect()

    # myContract = Contract()
    # myContract.symbol = "AAPL"
    # myContract.secType = "STK"
    # myContract.currency = "USD"
    # myContract.exchange = "SMART"

    # app.reqContractDetails(app.nextId(), myContract)

    

    # app.reqMarketDataType(3)  # 3 = Delayed 10-20min
    # app.reqMktData(app.nextId(), myContract, "225,232", False, False, [])

    # # app.reqRealTimeBars(app.nextId(), myContract, 5, "TRADES", False, [])
    # app.reqHistoricalData(app.nextId(), myContract, "", "1 D", "5 mins", "TRADES", 1, 1, False, [] )

    # time.sleep(5)  # Wait for responses

   

    logger.info("HT-IBKR-Integrations Application Finished")
    

if __name__ == "__main__":
    main()