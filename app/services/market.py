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
        self._market_data_events = {}
        self._latest_market_prices = {}
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

    @iswrapper
    def tickPrice(self, reqId: int, tickType: int, price: float, attrib):
        """Capture market data ticks and signal the waiting request once a usable price arrives."""
        super().tickPrice(reqId, tickType, price, attrib)

        # 4=LAST, 1=BID, 2=ASK, 68=DELAYED_LAST, 66=DELAYED_BID, 67=DELAYED_ASK
        if price is None or price <= 0:
            return

        if tickType in {4, 1, 2, 66, 67, 68}:
            self._latest_market_prices[reqId] = float(price)
            evt = self._market_data_events.get(reqId)
            if evt:
                evt.set()
    
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

    def get_latest_market_price(self, timeout_seconds: float = 5.0) -> float:
        """
        Request a fresh market price from IBKR and return it.
        Falls back to the instrument's current market_price if no tick arrives in time.
        """
        req_id = self.nextRequestId()
        evt = threading.Event()
        self._market_data_events[req_id] = evt

        contract = self.instrument.to_contract()
        # Empty genericTickList and snapshot=False gives streaming ticks; we cancel once we get a price.
        self.reqMktData(req_id, contract, "", False, False, [])

        try:
            evt.wait(timeout=timeout_seconds)
            latest_price = self._latest_market_prices.get(req_id)
            if latest_price and latest_price > 0:
                self.instrument.market_price = latest_price
                return latest_price

            logger.warning(
                "[MarketService] - Timed out waiting for market price tick for %s. Falling back to existing market_price=%s",
                self.instrument.symbol,
                self.instrument.market_price,
            )
            return float(self.instrument.market_price or 0.0)
        finally:
            self.cancelMktData(req_id)
            self._market_data_events.pop(req_id, None)
            self._latest_market_prices.pop(req_id, None)