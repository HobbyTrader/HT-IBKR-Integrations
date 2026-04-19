import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@staticmethod
def _parse_datetime(date_string: str | None) -> datetime:
    """
    Parse datetime string from SQLite to datetime object.
    
    Args:
        date_string: Date string from database (can be None)
        
    Returns:
        datetime object (returns current time if None or invalid)
    """
    if date_string is None or date_string == "":
        return datetime.now()
    
    # If it's already a datetime object, return it
    if isinstance(date_string, datetime):
        return date_string
    
    # Try common SQLite datetime formats
    formats = [
        '%Y-%m-%d %H:%M:%S',      # 2026-01-24 15:30:00
        '%Y-%m-%d %H:%M:%S.%f',   # 2026-01-24 15:30:00.123456
        '%Y-%m-%d',               # 2026-01-24
        '%Y%m%d %H:%M:%S',        # 20260124 15:30:00
        '%Y%m%d',                 # 20260124
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except (ValueError, TypeError):
            continue
    
    # If no format matches, log warning and return current time
    logger.warning(f"Unable to parse datetime string: '{date_string}', using current time")
    return datetime.now()