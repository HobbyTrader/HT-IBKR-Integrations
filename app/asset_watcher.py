from dataclasses import dataclass
import argparse
import base64
from datetime import datetime
import json
import logging
import re
import threading

from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from app.data.instrument import Instrument
from app.data.strategy import Strategy
from app.data.market_order import MarketOrder
from app.dto.market_order_dto import MarketOrderDTO
from app.services.market import MarketService
from app.utils import load_config_scheduler
from app.utils.logger import LoggerManager

if TYPE_CHECKING:
    from app.services.order import OrderService

LoggerManager("ASSET_WATCHER")
logger = logging.getLogger(__name__)

from app.services.order import OrderService

_stop_event = threading.Event()
_order_status_cache: Dict[int, str] = {}
_applied_partial_sell_rules: Dict[int, Set[int]] = {}  # Track which partial sell rules have been applied per instrument
_instrument_log_handler_initialized = False

TERMINAL_ORDER_STATUSES: Set[str] = {"Filled", "Cancelled", "ApiCancelled", "Inactive"}


def _sanitize_symbol_for_filename(symbol: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", symbol or "UNKNOWN")
    return sanitized.strip("._-") or "UNKNOWN"


def setup_instrument_execution_log(symbol: str) -> None:
    """Add an extra per-process log file that includes the instrument symbol in its name."""
    global _instrument_log_handler_initialized
    if _instrument_log_handler_initialized:
        return

    safe_symbol = _sanitize_symbol_for_filename(symbol)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"ASSET_WATCHER_{safe_symbol}_{timestamp}.log"

    log_path = LoggerManager.add_file_handler(log_filename)
    _instrument_log_handler_initialized = True

    logger.info("Instrument execution log file initialized: %s", log_path)


@dataclass(frozen=True)
class AssetWatcherArguments:
    instrument: Optional[Instrument]
    strategy: Optional[Strategy]
    client_id: int
    market_client_id: int


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
    parser.add_argument("--client-id", type=int, default=1001)
    parser.add_argument("--market-client-id", type=int, default=None)
    parsed = parser.parse_args()

    instrument = parse_instrument_b64(parsed.instrument_b64)
    strategy = parse_strategy_b64(parsed.strategy_b64)

    market_client_id = parsed.market_client_id
    if market_client_id is None:
        # Backward-compatible fallback for older launchers that only pass --client-id.
        market_client_id = 1100000000 + (int(parsed.client_id) % 900000000)

    return AssetWatcherArguments(
        instrument=instrument,
        strategy=strategy,
        client_id=parsed.client_id,
        market_client_id=market_client_id,
    )


def scheduler_stop() -> None:
    logger.info("Asset watcher stop requested.")
    _stop_event.set()


def update_order_status(client_id: int) -> None:
    with OrderService(clientId=client_id) as order_serv:
        order_serv.get_active_orders()
        order_serv.get_completed_orders()


def sync_order_cache(current_order_ids: Set[int]) -> None:
    stale_order_ids = set(_order_status_cache) - current_order_ids
    for order_id in stale_order_ids:
        _order_status_cache.pop(order_id, None)


def has_active_orders(orders) -> bool:
    return any(order.order_status not in TERMINAL_ORDER_STATUSES for order in orders)


def get_buy_order(orders: List[MarketOrder]) -> Optional[MarketOrder]:
    """Extract the BUY order (parent order) from the orders list."""
    for order in orders:
        if order.order_action == "BUY" and order.order_parent_id == 0:
            return order
    return None


def calculate_price_change_percentage(buy_price: float, current_price: float) -> float:
    """Calculate the percentage change from buy price to current price."""
    if buy_price <= 0:
        return 0.0
    return ((current_price - buy_price) / buy_price) * 100.0


def get_applicable_partial_sell_rules(strategy: Strategy, price_change_pct: float, instrument_id: int) -> List[Tuple]:
    """
    Get partial sell rules that should be applied based on current price change.
    Returns list of tuples: (rule_id, target_percentage, quantity_percentage, stop_loss_adjustment_percentage)
    """
    if not strategy or not strategy.details or not strategy.details.partial_sell_rules:
        return []
    
    applied_rules = _applied_partial_sell_rules.get(instrument_id, set())
    applicable_rules = []
    
    for rule in strategy.details.partial_sell_rules:
        # Only apply rule if price change exceeds target and rule hasn't been applied yet
        if price_change_pct >= rule.target_percentage and rule.rule_id not in applied_rules:
            applicable_rules.append((
                rule.rule_id,
                rule.target_percentage,
                rule.quantity_percentage,
                rule.stop_loss_adjustment_percentage
            ))
    
    return applicable_rules


def calculate_partial_sell_quantity(original_quantity: int, quantity_percentage: float) -> int:
    """Calculate the quantity to sell based on the percentage."""
    return int(original_quantity * quantity_percentage / 100.0)


def calculate_new_stop_loss_price(
    original_stop_loss_price: float,
    buy_price: float,
    stop_loss_adjustment_percentage: float
) -> float:
    """Calculate the new stop loss price after partial sell adjustment."""
    # The adjustment moves the stop loss up (towards the buy price or above)
    # For example, if stop_loss_adjustment_percentage is 5%, we move it 5% closer to break-even
    adjustment_amount = buy_price * (stop_loss_adjustment_percentage / 100.0)
    new_stop_loss = original_stop_loss_price + adjustment_amount
    return round(new_stop_loss, 2)


def get_remaining_quantity(buy_order: MarketOrder, total_sold: int) -> int:
    """Calculate the remaining quantity after partial sells."""
    return buy_order.order_quantity - total_sold


def get_sell_orders(orders: List[MarketOrder], buy_order: MarketOrder) -> List[MarketOrder]:
    """Extract all SELL orders (take profit and stop loss) for a given buy order."""
    sell_orders = []
    for order in orders:
        if order.order_action == "SELL" and order.order_parent_id == buy_order.order_id:
            sell_orders.append(order)
    return sell_orders


def place_partial_sell_order(
    instrument: Instrument,
    strategy: Strategy,
    order_service: OrderService,
    quantity_to_sell: int,
    take_profit_price: float
) -> Optional[MarketOrder]:
    """
    Place a partial sell order for the given quantity.
    Returns the MarketOrder if successful, None otherwise.
    """
    if quantity_to_sell <= 0:
        logger.warning(f"[AssetWatcher] - Invalid quantity to sell: {quantity_to_sell}")
        return None
    
    try:
        from ibapi.order import Order
        
        contract = instrument.to_contract()
        order_id = order_service.nextId()
        
        # Create a SELL LMT order
        sell_order = Order()
        sell_order.orderId = order_id
        sell_order.action = "SELL"
        sell_order.totalQuantity = quantity_to_sell
        sell_order.orderType = "LMT"
        sell_order.lmtPrice = take_profit_price
        
        logger.info(
            f"[AssetWatcher] - Placing partial sell order for {instrument.symbol}: "
            f"qty={quantity_to_sell}, price={take_profit_price}"
        )
        
        order_service.placeOrder(order_id, contract, sell_order)
        order_service.store_sell_order(sell_order, contract, instrument.strategy_id)
        
        return MarketOrder(
            order_id=order_id,
            order_contract_id=instrument.id,
            order_symbol=instrument.symbol,
            order_quantity=quantity_to_sell,
            order_currency=instrument.currency,
            order_price=take_profit_price,
            order_type="LMT",
            order_action="SELL",
            strategy_id=instrument.strategy_id
        )
    except Exception as exc:
        logger.error(f"[AssetWatcher] - Failed to place partial sell order: {exc}")
        return None


def modify_bracket_order_after_partial_sell(
    order_service: "OrderService",
    instrument: Instrument,
    buy_order: MarketOrder,
    sell_orders: List[MarketOrder],
    quantity_sold: int,
    new_stop_loss_price: float
) -> bool:
    """
    Modify the bracket order after a partial sell:
    1. Reduce the quantity in take profit and stop loss orders
    2. Update the stop loss price
    
    Returns True if modification was successful, False otherwise.
    """
    try:
        from ibapi.order import Order
        
        remaining_quantity = get_remaining_quantity(buy_order, quantity_sold)
        
        if remaining_quantity <= 0:
            logger.warning(
                f"[AssetWatcher] - No remaining quantity for {instrument.symbol} after partial sell. "
                "All shares have been sold."
            )
            return False
        
        contract = instrument.to_contract()
        
        # Modify each sell order (take profit and stop loss)
        for sell_order in sell_orders:
            modified_order = Order()
            modified_order.orderId = sell_order.order_id
            modified_order.action = sell_order.order_action
            modified_order.totalQuantity = remaining_quantity
            modified_order.orderType = sell_order.order_type
            
            if sell_order.order_type == "STP":
                # Update stop loss order
                modified_order.auxPrice = new_stop_loss_price
                logger.info(
                    f"[AssetWatcher] - Modifying stop loss order {sell_order.order_id}: "
                    f"qty={remaining_quantity}, price={new_stop_loss_price}"
                )
            elif sell_order.order_type == "LMT":
                # Update take profit order
                modified_order.lmtPrice = sell_order.order_price
                logger.info(
                    f"[AssetWatcher] - Modifying take profit order {sell_order.order_id}: "
                    f"qty={remaining_quantity}, price={sell_order.order_price}"
                )
            
            order_service.placeOrder(modified_order.orderId, contract, modified_order)
        
        logger.info(
            f"[AssetWatcher] - Successfully modified bracket order for {instrument.symbol}: "
            f"remaining_qty={remaining_quantity}, new_stop_loss={new_stop_loss_price}"
        )
        return True
    except Exception as exc:
        logger.error(f"[AssetWatcher] - Failed to modify bracket order: {exc}")
        return False


def process_partial_sells(
    instrument: Instrument,
    strategy: Strategy,
    order_service: OrderService,
    buy_order: MarketOrder,
    current_price: float,
    market_order_dto: MarketOrderDTO
) -> None:
    """
    Check and process partial sell rules for the given instrument.
    """
    if not strategy or not strategy.details:
        return
    
    buy_price = buy_order.order_price
    if buy_price <= 0:
        logger.warning(f"[AssetWatcher] - Invalid buy price for {instrument.symbol}: {buy_price}")
        return
    
    # Calculate price change percentage
    price_change_pct = calculate_price_change_percentage(buy_price, current_price)
    
    logger.debug(
        f"[AssetWatcher] - {instrument.symbol}: buy_price={buy_price}, "
        f"current_price={current_price}, change={price_change_pct:.2f}%"
    )
    
    # Get applicable partial sell rules
    applicable_rules = get_applicable_partial_sell_rules(strategy, price_change_pct, instrument.id)
    
    if not applicable_rules:
        return
    
    # Get sell orders to modify
    all_orders = market_order_dto.get_market_orders_by_parent_order(buy_order.order_id)
    sell_orders = get_sell_orders(all_orders, buy_order)
    
    # Track total quantity sold in this execution
    total_quantity_sold_this_round = 0
    
    # Process each applicable rule
    for rule_id, target_pct, qty_pct, stop_loss_adj_pct in applicable_rules:
        quantity_to_sell = calculate_partial_sell_quantity(buy_order.order_quantity, qty_pct)
        
        logger.info(
            f"[AssetWatcher] - Applying partial sell rule {rule_id} for {instrument.symbol}: "
            f"target={target_pct}%, qty_to_sell={quantity_to_sell}, "
            f"stop_loss_adj={stop_loss_adj_pct}%"
        )
        
        # Place the partial sell order
        place_partial_sell_order(
            instrument,
            strategy,
            order_service,
            quantity_to_sell,
            instrument.take_profit_price
        )
        
        total_quantity_sold_this_round += quantity_to_sell
        
        # Mark rule as applied
        if instrument.id not in _applied_partial_sell_rules:
            _applied_partial_sell_rules[instrument.id] = set()
        _applied_partial_sell_rules[instrument.id].add(rule_id)
    
    # If any rules were applied, modify the bracket order
    if total_quantity_sold_this_round > 0 and sell_orders:
        # Calculate new stop loss price
        original_stop_loss_price = instrument.stop_loss_price
        avg_stop_loss_adjustment = sum(
            adj_pct for _, _, _, adj_pct in applicable_rules
        ) / len(applicable_rules) if applicable_rules else 0
        
        new_stop_loss_price = calculate_new_stop_loss_price(
            original_stop_loss_price,
            buy_price,
            avg_stop_loss_adjustment
        )
        
        # Modify the bracket order
        modify_bracket_order_after_partial_sell(
            order_service,
            instrument,
            buy_order,
            sell_orders,
            total_quantity_sold_this_round,
            new_stop_loss_price
        )


def get_latest_current_price(instrument: Instrument, market_client_id: int) -> float:
    """Fetch the latest market price from IBKR via MarketService."""
    try:
        market_service = MarketService(instrument)
        market_service.open_connection(clientId=market_client_id)
        try:
            return market_service.get_latest_market_price()
        finally:
            market_service.close_connection()
    except Exception as exc:
        logger.error(
            "[AssetWatcher] - Failed to retrieve latest market price for %s from MarketService: %s",
            instrument.symbol,
            exc,
        )
        return float(instrument.market_price or 0.0)


def main() -> None:
    args = get_arguments()
    instrument = args.instrument
    strategy = args.strategy
    client_id = args.client_id
    market_client_id = args.market_client_id

    if instrument is None:
        logger.error("No instrument provided. Stopping asset watcher.")
        scheduler_stop()
        return

    setup_instrument_execution_log(instrument.symbol)

    market_order_dto = MarketOrderDTO()
    logger.info(
        "Asset watcher started for instrument %s (%s) strategy=%s clientId=%s marketClientId=%s",
        instrument.symbol,
        instrument.id,
        strategy.name if strategy else "None",
        client_id,
        market_client_id,
    )

    update_order_status(client_id)

    orders = market_order_dto.get_market_orders_by_contract_id_today_parent(instrument.id)
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
        return

    # ============================================================================
    # PARTIAL SELL LOGIC
    # ============================================================================
    
    # Only process partial sells if strategy is provided
    if strategy and strategy.details and strategy.details.partial_sell_rules:
        try:
            with OrderService(clientId=client_id) as order_service:
                # Get the buy order
                buy_order = get_buy_order(orders)

                if buy_order and buy_order.order_status != "Rejected":
                    # Always refresh with latest market price from IBKR.
                    current_price = get_latest_current_price(instrument, market_client_id)
                    if current_price <= 0:
                        logger.warning(
                            f"[AssetWatcher] - No valid market price for {instrument.symbol}. "
                            "Skipping partial sell processing."
                        )
                    else:
                        logger.info(
                            f"[AssetWatcher] - Processing partial sells for {instrument.symbol}: "
                            f"buy_price={buy_order.order_price}, current_price={current_price}"
                        )

                        # Process partial sells
                        process_partial_sells(
                            instrument,
                            strategy,
                            order_service,
                            buy_order,
                            current_price,
                            market_order_dto
                        )
                elif buy_order:
                    logger.debug(
                        f"[AssetWatcher] - Buy order rejected {instrument.symbol}. "
                        f"Status: {buy_order.order_status}"
                    )
                else:
                    logger.warning(f"[AssetWatcher] - No buy order found for {instrument.symbol}")
        except Exception as exc:
            logger.error(f"[AssetWatcher] - Error processing partial sells: {exc}", exc_info=True)


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
