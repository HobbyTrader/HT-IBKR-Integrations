import time
import logging

from app.utils.ibapiconnector import IBApiConnector
from app.utils.logger import LoggerManager

from app.dto.market_dto import marketDTO

from ibapi.client import *
from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class MarketService(IBApiConnector):
    def __init__(self): 
        super().__init__()
        self.market_dto = marketDTO()
        logger.debug("[MarketService] - Market initialzed")