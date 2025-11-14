import json
from dataclasses import dataclass, asdict
from ibapi.scanner import ScannerSubscription
from ibapi.tag_value import TagValue

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
    scan_options: list
    filter_options: list[FilterOption]
    maxResults: int
    minutes_to_order: int
    max_shares_to_invest_per_trade: int
    min_shares_to_invest_per_trade: int
    max_price_per_trade: int
    min_price_per_trade: int
    max_trades_per_day: int
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str_or_dict):
        if isinstance(json_str_or_dict, str):
            data = json.loads(json_str_or_dict)
        else:
            data = json_str_or_dict  # Already a dict
        # Manually convert nested filter_options dicts to FilterOption instances
        filter_opts = [FilterOption(**fo) for fo in data.get('filter_options', [])]
        data['filter_options'] = filter_opts
        return cls(**data)
    
    def to_scannerSubscription(self):
        scanSub = ScannerSubscription()
        scanSub.instrument = self.instrument
        scanSub.locationCode = self.locationCode
        scanSub.scanCode = self.scanCode
        return scanSub
    
    def to_scannerOptions(self):
        return self.scan_options
    
    def to_tagValueList(self) -> list[TagValue]:
        return [fo.to_tagValue() for fo in self.filter_options]
    
@dataclass
class Strategy:
    name: str
    details: StrategyDetail
    id: int = None
    is_active: bool = True
    created_at: str = None
    updated_at: str = None
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str_or_dict):
        if isinstance(json_str_or_dict, str):
            data = json.loads(json_str_or_dict)
        else:
            data = json_str_or_dict  # Already a dict
        details = StrategyDetail.from_json(data['details'])
        return cls(name=data['name'], details=details)