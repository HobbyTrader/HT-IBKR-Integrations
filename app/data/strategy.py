import json
import logging

from typing import List, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, time

from vendor.ibapi.scanner import ScannerSubscription
from vendor.ibapi.tag_value import TagValue
from app.data.instrument import Instrument
from app.utils.timeencoder import TimeEncoder

logger = logging.getLogger(__name__)

@dataclass
class FilterOption:
    name: str
    value: str
    
    def to_tagValue(self) -> TagValue:
        return TagValue(self.name, self.value)
    
@dataclass
class StrategyDetail:
    instrument: str
    locationCode: str
    scanCode: str
    scan_options: List[Any] 
    filter_options: List[FilterOption] 
    maxResults: int
    minutes_to_order: int
    max_shares_to_invest_per_trade: int
    min_shares_to_invest_per_trade: int
    max_volume_percent: float
    max_price_per_trade: int
    min_price_per_trade: int
    max_trades_per_day: int
    stop_loss_percent: float
    take_profit_percent: float
    opening_hours : List[str] = field(default_factory=list)
    open_hour : time = None
    close_hour : time = None
    open_days: List[str] = field(default_factory = lambda: ["MON", "TUE", "WED", "THU", "FRI"])
    min_open_trade_gap_percentage: float = 0.0
    max_open_trade_gap_percentage: float = 0.0
    increase_position_candidate_percentage: float = 0.0
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), cls=TimeEncoder)
    
    @classmethod
    def from_json(cls, json_str_or_dict):
        if isinstance(json_str_or_dict, str):
            data = json.loads(json_str_or_dict)
        else:
            data = json_str_or_dict  # Already a dict
        # Manually convert nested filter_options dicts to FilterOption instances
        filter_opts = [FilterOption(**fo) for fo in data.get('filter_options', [])]
        data['filter_options'] = filter_opts
        
        # Parse opening_hours and extract open_hour and close_hour
        opening_hours = data.get('opening_hours', [])
        if opening_hours and len(opening_hours) >= 2:
            try:
                data['open_hour'] = time.fromisoformat(opening_hours[0])
                data['close_hour'] = time.fromisoformat(opening_hours[1])
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing opening_hours: {opening_hours}. Error: {e}")
                data['open_hour'] = None
                data['close_hour'] = None
        else:
            data['open_hour'] = None
            data['close_hour'] = None
        
        return cls(**data)
    
    def to_scannerSubscription(self):
        scanSub = ScannerSubscription()
        scanSub.instrument = self.instrument
        scanSub.locationCode = self.locationCode
        scanSub.scanCode = self.scanCode
        return scanSub
    
    def to_scannerOptions(self):
        return self.scan_options
    
    def to_tagValueList(self) -> List[TagValue]:
        return [fo.to_tagValue() for fo in self.filter_options]
    
@dataclass
class Strategy:
    name: str
    tags: List[str] = field(default_factory=lambda: [])
    details: StrategyDetail = None
    id: int = None
    is_active: bool = True
    created_at: str = None
    updated_at: str = None
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), cls=TimeEncoder)
    
    @classmethod
    def from_json(cls, json_str_or_dict):
        if isinstance(json_str_or_dict, str):
            data = json.loads(json_str_or_dict)
        else:
            data = json_str_or_dict  # Already a dict
        details = StrategyDetail.from_json(data['details'])
        tags = data.get('tags', [])
        return cls(name=data['name'], tags=tags, details=details)
    
    
    def get_stop_loss_price(self, buy_price: float) -> float:
        # Placeholder logic for calculating stop loss price
        return float(buy_price) * float(self.details.stop_loss_percent) / 100.0  # e.g., 5% below buy price
    
    def get_take_profit_price(self, buy_price: float) -> float:
        # Placeholder logic for calculating take profit price
        return float(buy_price) * float(self.details.take_profit_percent) / 100.0 # e.g., 10% above buy price
    
    def get_volume_buy(self, avg_volume: float, price: float) -> int:
        # Calculate volume to buy based on average volume and strategy limits
        quantity = min(self.details.max_shares_to_invest_per_trade, 
                       int(float(avg_volume) * float(self.details.max_volume_percent) / 100.0),
                       int(float(self.details.max_price_per_trade) / float(price)))
        logger.info(f"[Strategy] - Calculated quantity to invest: {quantity} shares based on max investment of {avg_volume} and market price {price}.")
        return quantity       
    
    def apply_strategy_on_instrument(self, instrument: Instrument):
        instrument.strategy_id = self.id
        
        # Placeholder logic to determine if an instrument meets strategy criteria
        # Implement actual checks based on strategy details
        if not instrument.daily_history or len(instrument.daily_history) < 4:
            logger.warning(f"[Instrument] - Not enough daily history data for {instrument.symbol} to determine order candidacy.")
            instrument.is_candidate = False
            return 
        
        # If avg wap of last 20 values (=10 minutes) is higher than the opening price then we have a buying candidate
        # Take the avg exchanged volume into account as well. 
        item_num = min(20, len(instrument.daily_history)-1)
        logger.debug(f"[Instrument] - Evaluating order candidacy for {instrument.symbol} with {len(instrument.daily_history)} daily history items.")
        waps = [bar.wap for bar in instrument.daily_history[-item_num:]]
        avg_price = sum(waps)/(item_num)
        volumes = [bar.volume for bar in instrument.daily_history[-item_num:]]
        logger.debug(f"[Instrument] - [{instrument.symbol}] - open value {instrument.daily_history[-item_num].open}: PRICE AVG - {avg_price} : VOLUME AVG {sum(volumes)/(item_num)}")
        if (instrument.daily_history[-item_num].open * (1 + (self.details.increase_position_candidate_percentage / 100.0)) < avg_price):
            instrument.calculate_avg_volume(item_num)
            instrument.set_market_price()            
            instrument.set_volume_buy(self.get_volume_buy(instrument.avg_volume, instrument.market_price))
            
            if (instrument.volume_buy * instrument.market_price < self.details.min_price_per_trade):
                logger.debug(f"[Instrument] - {instrument.symbol} does not meet strategy criteria for order candidacy due to low amount to invest: {instrument.volume_buy * instrument.market_price} < {self.details.min_price_per_trade}.")
                instrument.is_candidate = False
                return
            
            instrument.set_stop_loss_price(self.get_stop_loss_price(instrument.market_price))
            instrument.set_take_profit_price(self.get_take_profit_price(instrument.market_price))
            
            instrument.is_candidate = True
            instrument.store_history()
        else:
            logger.debug(f"[Instrument] - {instrument.symbol} does not meet strategy criteria for order candidacy due to insufficient price increase.")
            instrument.is_candidate = False
        return
    
    def is_market_open_now(self) -> bool:
        """Check if the market is open now based on strategy opening hours and days."""
        now = datetime.now()
        current_day = now.strftime("%a").upper()  # e.g., "MON", "TUE"
        current_time = now.time()
        
        if current_day not in self.details.open_days:
            logger.info(f"[Strategy] - Market is closed today ({current_day}) for strategy {self.name}.")
            return False
        
        try:
            opening_str, closing_str = self.details.opening_hours
            opening_time = time.fromisoformat(opening_str)
            closing_time = time.fromisoformat(closing_str)
        except Exception as e:
            logger.error(f"[Strategy] - Invalid opening hours format for strategy {self.name}: {self.details.opening_hours}. Error: {e}")
            return False
        
        if opening_time <= current_time <= closing_time:
            return True
        else:
            logger.info(f"[Strategy] - Current time {current_time} is outside of market hours ({opening_time} - {closing_time}) for strategy {self.name}.")
            return False
        
        