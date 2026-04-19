from decimal import Decimal


class NumericMixin:
    @staticmethod
    def _normalize_numeric(value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return int(value)
        if isinstance(value, float):
            return float(value)
        return value
