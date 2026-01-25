import logging

from dataclasses import dataclass, field
from datetime import datetime

from app.utils.date_helper import _parse_datetime
from vendor.ibapi.common import BarData

logger = logging.getLogger(__name__)

@dataclass    
class History:
    id: int
    instrument_id: int
    symbol: str = ""
    bar_time: datetime = field(default_factory=datetime.now)
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    close_price: float = 0.0
    volume: int = 0
    wap: float = 0.0
    bar_count: int = 0
    create_date: datetime = field(default_factory=datetime.now)
    update_date: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_row(cls, row: tuple):
        if len(row) < 12:
            raise ValueError("Invalid row for History")
        instrument_id = row[0]
        symbol = row[1]
        bar_time = _parse_datetime(row[2])
        open_price = row[3]
        high_price = row[4]
        low_price = row[5]
        close_price = row[6]
        volume = row[7]
        wap = row[8]
        bar_count = row[9]
        create_date = _parse_datetime(row[10])
        update_date = _parse_datetime(row[11])
        return cls(instrument_id, symbol, bar_time, open_price, high_price, low_price, close_price, volume, wap, bar_count, create_date, update_date)
    
    @classmethod
    def from_bar(cls, instrument_id: int, symbol:str, bar: BarData):
        return cls(
            instrument_id=instrument_id,
            symbol=symbol,
            bar_time=_parse_datetime(bar.date),
            open_price=bar.open,
            high_price=bar.high,    
            low_price=bar.low,
            close_price=bar.close,
            volume=bar.volume,
            wap=bar.wap,
            bar_count=bar.barCount)