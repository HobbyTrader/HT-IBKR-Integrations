from dataclasses import dataclass
import argparse
import base64
import json
import logging
import threading

from typing import Dict, Optional, Set

from app.data.instrument import Instrument
from app.data.strategy import Strategy
from app.dto.market_order_dto import MarketOrderDTO
from app.utils import load_config_scheduler
from app.utils.logger import LoggerManager

LoggerManager("ASSET_WATCHER")
logger = logging.getLogger(__name__)

try:
    from app.services.order import OrderService
    _order_service_import_error = None
except ModuleNotFoundError as exc:
    if exc.name == "ibapi":
        OrderService = None
        _order_service_import_error = exc
    else:
        raise

_stop_event = threading.Event()
_order_status_cache: Dict[int, str] = {}

TERMINAL_ORDER_STATUSES: Set[str] = {"Filled", "Cancelled", "ApiCancelled", "Inactive"}


@dataclass(frozen=True)
class AssetWatcherArguments:
    instrument: Optional[Instrument]
    strategy: Optional[Strategy]


def parse_instrument_b64(encoded_payload: Optional[str]) -> Optional[Instrument]:
    if not encoded_payload:
        return None

    try:
        payload_json = base64.urlsafe_b64decode(encoded_payload.encode("ascii")).decode("utf-8")
        payload_dict = json.loads(payload_json)
        return Instrument.from_json(payload_dict)
    except Exception as exc:
        logger.error(f"Unable to decode instrument payload: {exc}")
        return None


def parse_strategy_b64(encoded_payload: Optional[str]) -> Optional[Strategy]:
    if not encoded_payload:
        return None

    try:
        payload_json = base64.urlsafe_b64decode(encoded_payload.encode("ascii")).decode("utf-8")
        payload_dict = json.loads(payload_json)
        return Strategy.from_json(payload_dict)
    except Exception as exc:
        logger.error(f"Unable to decode strategy payload: {exc}")
        return None


def get_arguments() -> AssetWatcherArguments:
    parser = argparse.ArgumentParser(description="Watch orders for one instrument only")
    parser.add_argument("--instrument-b64", required=True)
    parser.add_argument("--strategy-b64", default=None)
    parsed = parser.parse_args()

    instrument = parse_instrument_b64(parsed.instrument_b64)
    strategy = parse_strategy_b64(parsed.strategy_b64)
    return AssetWatcherArguments(instrument=instrument, strategy=strategy)


def scheduler_stop() -> None:
    logger.info("Asset watcher stop requested.")
    _stop_event.set()


def update_order_status() -> None:
    if OrderService is None:
        logger.error(
            "Asset watcher cannot refresh order status because ibapi is not available in the current Python environment: %s",
            _order_service_import_error,
        )
        scheduler_stop()
        return

    with OrderService() as order_serv:
        order_serv.get_active_orders()
        order_serv.get_completed_orders()


def sync_order_cache(current_order_ids: Set[int]) -> None:
    stale_order_ids = set(_order_status_cache) - current_order_ids
    for order_id in stale_order_ids:
        _order_status_cache.pop(order_id, None)


def has_active_orders(orders) -> bool:
    return any(order.order_status not in TERMINAL_ORDER_STATUSES for order in orders)


def main() -> None:
    args = get_arguments()
    instrument = args.instrument
    strategy = args.strategy

    if instrument is None:
        logger.error("No instrument provided. Stopping asset watcher.")
        scheduler_stop()
        return

    market_order_dto = MarketOrderDTO()
    logger.info(
        "Asset watcher started for instrument %s (%s) strategy=%s",
        instrument.symbol,
        instrument.id,
        strategy.name if strategy else "None",
    )

    update_order_status()

    orders = market_order_dto.get_market_orders_by_contract_id_today(instrument.id)
    logger.info(f"Instrument {instrument.symbol} has {len(orders)} orders today.")

    current_order_ids = {order.order_id for order in orders}
    sync_order_cache(current_order_ids)
    for order in orders:
        previous_status = _order_status_cache.get(order.order_id)
        if previous_status != order.order_status:
            logger.info(
                "Order state changed for instrument %s: order_id=%s, action=%s, status=%s",
                instrument.symbol,
                order.order_id,
                order.order_action,
                order.order_status,
            )
        _order_status_cache[order.order_id] = order.order_status

    if not orders:
        logger.info(f"No orders found for instrument {instrument.symbol}. Stopping asset watcher.")
        scheduler_stop()
        return

    if not has_active_orders(orders):
        logger.info(f"All orders for instrument {instrument.symbol} are terminal. Stopping asset watcher.")
        scheduler_stop()


def run_scheduler() -> None:
    config_scheduler_watcher = load_config_scheduler().get("watcher", {})
    logger.info(f"Loaded scheduler configuration for asset watcher: {config_scheduler_watcher}")

    if not config_scheduler_watcher.get("enabled", False):
        logger.info("Watcher scheduler is disabled in configuration. Only 1 execution will be performed.")
        main()
        scheduler_stop()
        return

    interval = config_scheduler_watcher.get("interval", 300)
    logger.info(f"Starting asset watcher scheduler with interval {interval} seconds.")

    while not _stop_event.is_set():
        main()
        if _stop_event.is_set():
            break
        logger.info(f"Asset watcher scheduler sleeping for {interval} seconds...")
        _stop_event.wait(interval)


if __name__ == "__main__":
    run_scheduler()
