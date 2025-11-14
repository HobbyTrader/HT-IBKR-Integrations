import time
import logging

from app.utils.ibapiconnector import IBApiConnector
from app.data.instrument import Instrument
# from app.dto.market_dto import marketDTO

from ibapi.client import *
from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class MarketService(IBApiConnector):
    def __init__(self, instrument: Instrument): 
        super().__init__()
        # self.market_dto = marketDTO()
        self.instrument = instrument
        logger.debug("[MarketService] - Market initialzed")
        
    @iswrapper  
    def realtimeBar(self, reqId: int, time: int, open_: float, high: float, low: float, close: float, volume: int, wap: float, count: int):
        logger.debug(f"[MarketService] - RealtimeBar. reqId: {reqId}, time: {time}, open: {open_}, high: {high}, low: {low}, close: {close}, volume: {volume}, wap: {wap}, count: {count}.")
        # self.market_dto.saveRealtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        
    @iswrapper
    def historicalData(self, reqId: int, bar):
        logger.debug(f"[MarketService] - HistoricalData. reqId: {reqId}, bar: {bar}.")
        self.instrument.daily_history.append(bar)
        # self.market_dto.saveHistoricalData(reqId, bar)
        
    def get_realtime_bars(self, contract: Contract):
        logger.debug("[MarketService] - Realtime Bars requested")
        self.reqHistoricalData(self.nextId(), contract,"", "1 D", "30 secs", "TRADES",1,1, False, [])
        time.sleep(10)
        
    def get_historical_day_data(self):
        logger.debug("[MarketService] - Historical Data requested")
        contract = Contract()
        contract.symbol = self.instrument.symbol
        contract.secType = self.instrument.sectype
        contract.currency = self.instrument.currency
        contract.exchange = self.instrument.exchange
        self.reqHistoricalData(self.orderId, contract,"", "1 D", "30 secs", "TRADES",0,1, False, [])
        time.sleep(2)