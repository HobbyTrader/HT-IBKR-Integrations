import logging

from app.utils.ibapiconnector import IBApiConnector
from vendor.ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

class AccountService(IBApiConnector):
    def __init__(self, clientId : int=0): 
        super().__init__()
        
    # ============================================================================
    # IBKR WRAPPER CALLBACKS
    # ============================================================================
    @iswrapper
    def accountSummary(self, reqId: int, account: str, tag: str,
                       value: str, currency: str):
        logger.debug(f"[AccountService] - Account Summary. ReqId: {reqId}, Account: {account}, Tag: {tag}, Value: {value}, Currency: {currency}.")
        # Here you can process the account summary data as needed
        
    @iswrapper
    def accountSummaryEnd(self, reqId: int):
        logger.debug(f"[AccountService] - Account Summary End. ReqId: {reqId}.")
        # Here you can handle the end of account summary data transmission
        
    @iswrapper
    def updateAccountValue(self, key: str, value: str, currency: str,
                           accountName: str):
        logger.debug(f"[AccountService] - Update Account Value. Key: {key}, Value: {value}, Currency: {currency}, Account Name: {accountName}.")
        # Here you can process the updated account value as needed
        
    @iswrapper
    def updateAccountTime(self, timeStamp: str):
        logger.debug(f"[AccountService] - Update Account Time. TimeStamp: {timeStamp}.")
        # Here you can process the updated account time as needed
        
    @iswrapper
    def updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName):
        logger.debug(f"[AccountService] - Update Portfolio. Contract: {contract}, Position: {position}, MarketPrice: {marketPrice}, MarketValue: {marketValue}, AverageCost: {averageCost}, UnrealizedPNL: {unrealizedPNL}, RealizedPNL: {realizedPNL}, AccountName: {accountName}.") 
    
    @iswrapper
    def accountDownloadEnd(self, accountName: str):
        logger.debug(f"[AccountService] - Account Download End. AccountName: {accountName}.")
        # Here you can handle the end of account data transmission
    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================    
    def get_accounts_start(self, account_id: str=""):
        """Request current account information from IBKR."""
        self.reqAccountUpdates(True, account_id)
        logger.debug("[AccountService] - Requested current account information from IBKR.")
        
    def get_accounts_stop(self, account_id: str=""):
        """Stop account information updates from IBKR."""
        self.reqAccountUpdates(False, account_id)
        logger.debug("[AccountService] - Stopped account information updates from IBKR.")