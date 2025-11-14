import logging

from app.utils.sqllitemanager import SQLiteManager
from app.utils.logger import LoggerManager

logger = logging.getLogger(__name__)

class MarketDTO:
    def __init__(self):
        dbconn = SQLiteManager()