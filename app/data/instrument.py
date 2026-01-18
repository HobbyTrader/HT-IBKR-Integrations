import json
import logging

from dataclasses import dataclass, field
from typing import List

from vendor.ibapi.common import BarData
from vendor.ibapi.contract import Contract

logger = logging.getLogger(__name__)

@dataclass    
class Instrument:
    id: int
    symbol: str
    sectype: str
    currency: str
    exchange: str
    strategy_id: int = 0
    daily_history: List[BarData] = field(default_factory=list)
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
  
    def to_json(self) -> str:
        return json.dumps(self.__dict__)
    
    def to_contract(self) -> Contract:
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