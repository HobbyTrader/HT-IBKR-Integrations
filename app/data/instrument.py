import json
import logging

from ibapi.common import BarData

logger = logging.getLogger(__name__)

# @dataclass
# class InstrumentHistory:
#     date: str
#     open: float
#     high: float
#     low: float
#     close: float
#     volume: int
#     wap: float
    
#     def to_json(self) -> str:
#         return json.dumps(self.__dict__)
    
#     @classmethod
#     def from_json(cls, json_str_or_dict):
#         if isinstance(json_str_or_dict, str):
#             data = json.loads(json_str_or_dict)
#         else:
#             data = json_str_or_dict  # Already a dict
#         return cls(**data)
    
class Instrument:
    def __init__(self, id: int = None, symbol: str = None, sectype: str = None, 
                 currency: str = None, exchange: str = None):
        self.id = id
        self.symbol = symbol
        self.sectype = sectype
        self.currency = currency
        self.exchange = exchange
        self.daily_history: list[BarData] = []
    
    def to_json(self) -> str:
        return json.dumps(self.__dict__)
    
    @classmethod
    def from_json(cls, json_str_or_dict):
        if isinstance(json_str_or_dict, str):
            data = json.loads(json_str_or_dict)
        else:
            data = json_str_or_dict  # Already a dict
        return cls(**data)

    def is_order_candidate(self) -> bool:
        if not self.daily_history or len(self.daily_history) < 4:
            logger.warning(f"[Instrument] - Not enough daily history data for {self.symbol} to determine order candidacy.")
            return False
        
        # If avg wap of 1st 3 minutes is higher than the opening price then we have a buying candidate
        item_num = min(6, len(self.daily_history)-1)
        logger.debug(f"[Instrument] - Evaluating order candidacy for {self.symbol} with {len(self.daily_history)} daily history items.")
        waps = [bar.wap for bar in self.daily_history[1:7]]
        logger.debug(f"[Instrument] - open value {self.daily_history[0].open}: AVG - {sum(waps)/(item_num)} : SUM {sum(waps)} : NUM {item_num}")
        if (self.daily_history[0].open < sum(waps)/(item_num)):
            return True
        else:
            return False
        