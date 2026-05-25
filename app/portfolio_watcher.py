from dataclasses import dataclass
import argparse
import logging
import re
import threading
import time

from app.services.portfolio import PortfolioService
from app.utils import load_config_ibapi, load_config_scheduler
from app.utils.logger import LoggerManager

LoggerManager("PORTFOLIO_WATCHER")
logger = logging.getLogger(__name__)

_stop_event = threading.Event()

PORTFOLIO_WATCHER_CLIENT_ID_BASE = 2050000000
PORTFOLIO_WATCHER_CLIENT_ID_SPAN = 80000000


# def _sanitize_symbol_for_filename(symbol: str) -> str:
#     sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", symbol or "UNKNOWN")
#     return sanitized.strip("._-") or "UNKNOWN"


# def setup_portfolio_execution_log(account_id: str) -> None:
#     safe_account_id = _sanitize_symbol_for_filename(account_id)
#     timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
#     log_filename = f"PORTFOLIO_WATCHER_{safe_account_id}_{timestamp}.log"
#     log_path = LoggerManager.add_file_handler(log_filename)
#     logger.info("Portfolio execution log file initialized: %s", log_path)


@dataclass(frozen=True)
class PortfolioWatcherArguments:
    account_id: str
    client_id: int
    group_name: str
    account_summary_tags: str


def generate_portfolio_watcher_client_id(account_id: str) -> int:
    account_part = sum(ord(char) for char in (account_id or "")) % 1000000
    timestamp_part = int(time.time_ns()) % 100000
    seed = (account_part * 100000) + timestamp_part
    return PORTFOLIO_WATCHER_CLIENT_ID_BASE + (seed % PORTFOLIO_WATCHER_CLIENT_ID_SPAN)


def get_arguments() -> PortfolioWatcherArguments:
    config_ibapi = load_config_ibapi()
    default_account_id = config_ibapi.get("ACCOUNTID")

    parser = argparse.ArgumentParser(description="Watch portfolio status from IBKR")
    parser.add_argument("--account-id", default=default_account_id)
    parser.add_argument("--client-id", type=int, default=None)
    parser.add_argument("--group-name", default="All")
    parser.add_argument(
        "--account-summary-tags",
        default="NetLiquidation,TotalCashValue,GrossPositionValue,AvailableFunds,BuyingPower,UnrealizedPnL,RealizedPnL",
    )
    parsed = parser.parse_args()

    client_id = parsed.client_id
    if client_id is None:
        client_id = generate_portfolio_watcher_client_id(parsed.account_id)

    return PortfolioWatcherArguments(
        account_id=parsed.account_id,
        client_id=client_id,
        group_name=parsed.group_name,
        account_summary_tags=parsed.account_summary_tags,
    )


def scheduler_stop() -> None:
    logger.info("Portfolio watcher stop requested.")
    _stop_event.set()


def main() -> None:
    args = get_arguments()

    if not args.account_id:
        logger.error("No account ID provided. Stopping portfolio watcher.")
        scheduler_stop()
        return

    # setup_portfolio_execution_log(args.account_id)

    logger.info(
        "Portfolio watcher started for account %s clientId=%s groupName=%s",
        args.account_id,
        args.client_id,
        args.group_name,
    )

    with PortfolioService(clientId=args.client_id) as portfolio_service:
        snapshot = portfolio_service.collect_portfolio_snapshot(
            account_id=args.account_id,
            group_name=args.group_name,
            tags=args.account_summary_tags,
        )

    logger.info(
        "Portfolio snapshot collected for account %s: portfolio_updates=%s account_summaries=%s positions=%s",
        args.account_id,
        len(snapshot["portfolio_updates"]),
        len(snapshot["account_summaries"]),
        len(snapshot["positions"]),
    )


def run_scheduler() -> None:
    config_scheduler_portfolio = load_config_scheduler().get("portfolio_watcher", {})
    logger.info("Loaded scheduler configuration for portfolio watcher: %s", config_scheduler_portfolio)

    if not config_scheduler_portfolio.get("enabled", False):
        logger.info("Portfolio watcher scheduler is disabled in configuration. Only 1 execution will be performed.")
        main()
        scheduler_stop()
        return

    interval = config_scheduler_portfolio.get("interval", 300)
    logger.info("Starting portfolio watcher scheduler with interval %s seconds.", interval)

    while not _stop_event.is_set():
        main()
        if _stop_event.is_set():
            break
        logger.info("Portfolio watcher scheduler sleeping for %s seconds...", interval)
        _stop_event.wait(interval)


if __name__ == "__main__":
    run_scheduler()