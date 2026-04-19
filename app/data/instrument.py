from __future__ import annotations

import json
import logging

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List

from app.data.numeric_mixin import NumericMixin

if TYPE_CHECKING:
    from ibapi.common import BarData
    from ibapi.contract import Contract

logger = logging.getLogger(__name__)

@dataclass    
class Instrument(NumericMixin):
    id: int
    symbol: str
    sectype: str
    currency: str
    exchange: str
    strategy_id: int = 0
    daily_history: List[Any] = field(default_factory=list)
    market_price: float = 0.0
    avg_volume: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    volume_buy: int = 0
    is_candidate: bool = False
    
    @classmethod
    def from_row(cls, row: tuple):
        # Expecting row to have at least 5 elements: id, symbol, sectype, currency, exchange  
        if len(row) < 5:
            raise ValueError("Invalid row")
        return cls(*row[:5])

    def to_payload(self) -> dict:
        return {
            "id": self._normalize_numeric(self.id),
            "symbol": self.symbol,
            "sectype": self.sectype,
            "currency": self.currency,
            "exchange": self.exchange,
            "strategy_id": self._normalize_numeric(self.strategy_id),
            "daily_history": [],
            "market_price": self._normalize_numeric(self.market_price),
            "avg_volume": self._normalize_numeric(self.avg_volume),
            "stop_loss_price": self._normalize_numeric(self.stop_loss_price),
            "take_profit_price": self._normalize_numeric(self.take_profit_price),
            "volume_buy": self._normalize_numeric(self.volume_buy),
            "is_candidate": self.is_candidate,
        }
  
    def to_json(self) -> str:
        return json.dumps(self.to_payload(), separators=(",", ":"))
    
    def to_contract(self) -> Contract:
        from ibapi.contract import Contract

        contract = Contract()
        contract.conId = self.id
        contract.symbol = self.symbol
        contract.secType = self.sectype
        contract.currency = self.currency
        contract.exchange = self.exchange
        return contract
    
    @classmethod
    def from_json(cls, json_str_or_dict):
        if isinstance(json_str_or_dict, str):
            data = json.loads(json_str_or_dict)
        else:
            data = json_str_or_dict  # Already a dict
        return cls(**data)
        
    def set_market_price(self):
        if not self.daily_history or len(self.daily_history) == 0:
            logger.warning(f"[Instrument] - No daily history data for {self.symbol} to get market price.")
            return
        # Return the closing price of the most recent bar as the market price
        self.market_price = self.daily_history[-1].close
        logger.debug(f"[Instrument] - Set market price for {self.symbol}: {self.market_price}")
        
    def calculate_avg_volume(self, item_num: int):
        if not self.daily_history or len(self.daily_history) == 0:
            logger.warning(f"[Instrument] - No daily history data for {self.symbol} to calculate average volume.")
            return
        # Calcul de la moyenne du volume des transactions échangées pour ne pas dépasser un certain seuil.
        # But de ne pas trop impacter le marché avec nos ordres.
        total_volume = sum(bar.volume for bar in self.daily_history[-item_num:])
        self.avg_volume = total_volume / item_num
        logger.debug(f"[Instrument] - Calculated avg volume for {self.symbol}: {self.avg_volume}")
            
    def set_stop_loss_price(self, price: float):
        self.stop_loss_price = round(price, 2)
        logger.debug(f"[Instrument] - Set stop loss price for {self.symbol}: {self.stop_loss_price}")   
        
    def set_take_profit_price(self, price: float):
        self.take_profit_price = round(price, 2)
        logger.debug(f"[Instrument] - Set take profit price for {self.symbol}: {self.take_profit_price}")
        
    def set_volume_buy(self, volume: int):
        self.volume_buy = volume
        logger.debug(f"[Instrument] - Set volume to buy for {self.symbol}: {self.volume_buy}")
        
    def store_history(self):
        from app.data.history import History
        from app.dto.history_dto import HistoryDTO

        # Placeholder for storing instrument history
        logger.debug(f"[Instrument] - Storing instrument history for {self.symbol}.")
        for bar in self.daily_history:
            logger.debug(f"[Instrument History] - {self.symbol} - Time: {bar.date}, Open: {bar.open}, High: {bar.high}, Low: {bar.low}, Close: {bar.close}, Volume: {bar.volume}, WAP: {bar.wap}")
            hist = History.from_bar(self.id, self.symbol, bar)
            hist_dto = HistoryDTO()
            hist_dto.save_history(hist)