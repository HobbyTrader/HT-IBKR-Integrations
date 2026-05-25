import logging
import threading
from typing import Any, Dict, List, Optional

from app.utils.ibapiconnector import IBApiConnector
from ibapi.contract import Contract
from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)


class PortfolioService(IBApiConnector):
    def __init__(self, clientId: int = 0):
        super().__init__()
        self.CLIENT_ID = clientId
        self.portfolio_updates: List[Dict[str, Any]] = []
        self.account_summaries: List[Dict[str, Any]] = []
        self.open_positions: List[Dict[str, Any]] = []
        self._events: Dict[str, threading.Event] = {}

    def _clear_event(self, event_name: str) -> None:
        self._events[event_name] = threading.Event()

    def _get_event(self, event_name: str) -> threading.Event:
        event = self._events.get(event_name)
        if event is None:
            event = threading.Event()
            self._events[event_name] = event
        return event

    def _wait_for_event(self, event_name: str, timeout: float = 10.0) -> bool:
        return self._get_event(event_name).wait(timeout)

    # ========================================================================
    # IBKR WRAPPER CALLBACKS
    # ========================================================================
    @iswrapper
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        payload = {
            "req_id": reqId,
            "account": account,
            "tag": tag,
            "value": value,
            "currency": currency,
        }
        logger.debug(
            "[PortfolioService] - Account Summary. ReqId: %s, Account: %s, Tag: %s, Value: %s, Currency: %s.",
            reqId,
            account,
            tag,
            value,
            currency,
        )
        self.account_summaries.append(payload)

    @iswrapper
    def accountSummaryEnd(self, reqId: int):
        logger.debug("[PortfolioService] - Account Summary End. ReqId: %s.", reqId)
        self._get_event(f"account_summary_end_{reqId}").set()

    @iswrapper
    def updatePortfolio(
        self,
        contract: Contract,
        position,
        marketPrice,
        marketValue,
        averageCost,
        unrealizedPNL,
        realizedPNL,
        accountName,
    ):
        payload = {
            "contract": contract,
            "position": position,
            "market_price": marketPrice,
            "market_value": marketValue,
            "average_cost": averageCost,
            "unrealized_pnl": unrealizedPNL,
            "realized_pnl": realizedPNL,
            "account_name": accountName,
        }
        logger.debug(
            "[PortfolioService] - Update Portfolio. Contract: %s, Position: %s, MarketPrice: %s, MarketValue: %s, AverageCost: %s, UnrealizedPNL: %s, RealizedPNL: %s, AccountName: %s.",
            contract,
            position,
            marketPrice,
            marketValue,
            averageCost,
            unrealizedPNL,
            realizedPNL,
            accountName,
        )
        self.portfolio_updates.append(payload)

    @iswrapper
    def accountDownloadEnd(self, accountName: str):
        logger.debug("[PortfolioService] - Account Download End. AccountName: %s.", accountName)
        self._get_event("account_download_end").set()

    @iswrapper
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        payload = {
            "account": account,
            "contract": contract,
            "position": position,
            "average_cost": avgCost,
        }
        logger.debug(
            "[PortfolioService] - Position. Account: %s, Contract: %s, Position: %s, AvgCost: %s.",
            account,
            contract,
            position,
            avgCost,
        )
        self.open_positions.append(payload)

    @iswrapper
    def positionEnd(self):
        logger.debug("[PortfolioService] - PositionEnd.")
        self._get_event("position_end").set()

    # ========================================================================
    # PUBLIC METHODS
    # ========================================================================
    def request_portfolio_updates(self, account_id: str = "") -> None:
        self.reqAccountUpdates(True, account_id)
        logger.debug("[PortfolioService] - Requested portfolio updates from IBKR.")

    def stop_portfolio_updates(self, account_id: str = "") -> None:
        self.reqAccountUpdates(False, account_id)
        logger.debug("[PortfolioService] - Stopped portfolio updates from IBKR.")

    def request_account_summary(self, group_name: str = "All", tags: str = "NetLiquidation,TotalCashValue,GrossPositionValue,AvailableFunds,BuyingPower,UnrealizedPnL,RealizedPnL") -> int:
        req_id = self.nextRequestId()
        self.reqAccountSummary(req_id, group_name, tags)
        logger.debug(
            "[PortfolioService] - Requested account summary from IBKR. ReqId: %s, Group: %s, Tags: %s.",
            req_id,
            group_name,
            tags,
        )
        return req_id

    def stop_account_summary(self, req_id: int) -> None:
        self.cancelAccountSummary(req_id)
        logger.debug("[PortfolioService] - Stopped account summary from IBKR. ReqId: %s.", req_id)

    def request_positions(self) -> None:
        self.reqPositions()
        logger.debug("[PortfolioService] - Requested open positions from IBKR.")

    def stop_positions(self) -> None:
        self.cancelPositions()
        logger.debug("[PortfolioService] - Stopped open positions request from IBKR.")

    def collect_portfolio_snapshot(
        self,
        account_id: str = "",
        group_name: str = "All",
        tags: str = "NetLiquidation,TotalCashValue,GrossPositionValue,AvailableFunds,BuyingPower,UnrealizedPnL,RealizedPnL",
        timeout: float = 10.0,
    ) -> Dict[str, List[Dict[str, Any]]]:
        self.portfolio_updates.clear()
        self.account_summaries.clear()
        self.open_positions.clear()
        self._clear_event("account_download_end")
        self._clear_event("position_end")

        req_id: Optional[int] = None

        try:
            self.request_portfolio_updates(account_id)
            self.request_positions()
            req_id = self.request_account_summary(group_name, tags)

            self._wait_for_event("account_download_end", timeout)
            self._wait_for_event("position_end", timeout)
            self._wait_for_event(f"account_summary_end_{req_id}", timeout)
        finally:
            self.stop_portfolio_updates(account_id)
            self.stop_positions()
            if req_id is not None:
                self.stop_account_summary(req_id)

        return {
            "portfolio_updates": list(self.portfolio_updates),
            "account_summaries": list(self.account_summaries),
            "positions": list(self.open_positions),
        }