import logging

from app.utils.sqllitemanager import SQLiteManager

logger = logging.getLogger(__name__)

class MarketOrderDTO:
    def __init__(self):
        dbconn = SQLiteManager()