import time
import logging
import threading

from app.utils.ibapiconnector import IBApiConnector
from app.data.instrument import Instrument
# from app.dto.market_dto import marketDTO
from app.dto.realtime_bar_dto import RealtimeBarDTO

from ibapi.client import *
from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class MarketService(IBApiConnector):
    def __init__(self, instrument: Instrument): 
        super().__init__()
        # self.market_dto = marketDTO()
        self.realtime_bar_dto = RealtimeBarDTO()
        self.instrument = instrument
        self.Historical_events = {}
        logger.debug("[MarketService] - Market initialzed")
    
    # ============================================================================
    # IBKR WRAPPER CALLBACKS
    # ============================================================================    
    @iswrapper  
    def realtimeBar(self, reqId: int, time: int, open_: float, high: float, low: float, close: float, volume: int, wap: float, count: int):
        logger.debug(f"[MarketService] - RealtimeBar. reqId: {reqId}, time: {time}, open: {open_}, high: {high}, low: {low}, close: {close}, volume: {volume}, wap: {wap}, count: {count}.")
        # self.market_dto.saveRealtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        self.realtime_bar_dto.save_realtime_bar(reqId, time, open_, high, low, close, volume, wap, count)
        
    @iswrapper
    def historicalData(self, reqId: int, bar):
        logger.debug(f"[MarketService] - HistoricalData. reqId: {reqId}, bar: {bar}.")
        self.instrument.daily_history.append(bar)
        # self.market_dto.saveHistoricalData(reqId, bar)
        
    @iswrapper
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        event = self.Historical_events.get(self.instrument.symbol)
        if event:
            event.set()
        logger.debug(f"[MarketService] - HistoricalDataEnd. reqId: {reqId}, start: {start}, end: {end}.")
    
    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================    
    def get_realtime_bars(self):
        logger.debug("[MarketService] - Realtime Bars requested")
        contract = self.instrument.to_contract()
        self.reqRealTimeBars (self.nextId(), contract, 5, "MIDPOINT", True, [])
        
        
    def get_historical_day_data(self):
        logger.debug("[MarketService] - Historical Data requested")
        evt = threading.Event()
        self.Historical_events[self.instrument.symbol] = evt
        contract = self.instrument.to_contract()
        self.reqHistoricalData(self.orderId, contract,"", "3600 S", "30 secs", "TRADES",0,1, True, [])
        
        evt.wait(timeout=15)
        self.Historical_events.pop(self.instrument.symbol, None)