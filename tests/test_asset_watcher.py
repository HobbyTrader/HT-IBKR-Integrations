import unittest
from unittest.mock import Mock, patch

from app.asset_watcher import (
    _applied_partial_sell_rules,
    get_applicable_partial_sell_rules,
    process_partial_sells,
)
from app.data.market_order import MarketOrder
from app.data.strategy import PartialSellRule, Strategy, StrategyDetail
from app.dto.market_order_dto import MarketOrderDTO


def _build_strategy_with_partial_rules() -> Strategy:
    details = StrategyDetail(
        instrument="STK",
        locationCode="STK.US.MAJOR",
        scanCode="HIGH_OPEN_GAP",
        scan_options=[],
        filter_options=[],
        maxResults=10,
        minutes_to_order=1,
        max_shares_to_invest_per_trade=1000,
        min_shares_to_invest_per_trade=1,
        max_volume_percent=1.0,
        max_price_per_trade=10000,
        min_price_per_trade=100,
        max_trades_per_day=5,
        stop_loss_percent=95.0,
        take_profit_percent=110.0,
        partial_sell_rules=[
            PartialSellRule(
                rule_id=1,
                target_percentage=30.0,
                quantity_percentage=30.0,
                stop_loss_adjustment_percentage=0.0,
            )
        ],
    )
    return Strategy(name="Watcher Partial Sell Test", tags=["TEST"], details=details)


class TestAssetWatcherPartialSellRules(unittest.TestCase):
    def setUp(self):
        _applied_partial_sell_rules.clear()

    def test_get_applicable_partial_sell_rules_excludes_already_applied_rule(self):
        strategy = _build_strategy_with_partial_rules()
        instrument_id = 12345

        first_eval = get_applicable_partial_sell_rules(strategy, 30.0, instrument_id)
        self.assertEqual(len(first_eval), 1)
        self.assertEqual(first_eval[0][0], 1)

        _applied_partial_sell_rules[instrument_id] = {1}

        second_eval = get_applicable_partial_sell_rules(strategy, 30.0, instrument_id)
        self.assertEqual(second_eval, [])

    @patch("app.asset_watcher.modify_bracket_order_after_partial_sell")
    @patch("app.asset_watcher.place_partial_sell_order")
    def test_process_partial_sells_does_not_apply_same_rule_twice(
        self,
        mock_place_partial_sell_order,
        mock_modify_bracket,
    ):
        strategy = _build_strategy_with_partial_rules()

        instrument = Mock()
        instrument.id = 999
        instrument.symbol = "TEST"
        instrument.take_profit_price = 110.0
        instrument.stop_loss_price = 95.0

        buy_order = MarketOrder(
            order_id=10,
            order_action="BUY",
            order_parent_id=0,
            order_price=100.0,
            order_quantity=100,
            order_status="Filled",
        )

        sell_order = MarketOrder(
            order_id=11,
            order_action="SELL",
            order_parent_id=10,
            order_type="LMT",
            order_price=120.0,
            order_quantity=100,
            order_status="Submitted",
        )

        market_order_dto = Mock(spec=MarketOrderDTO)
        market_order_dto.get_market_orders_by_parent_order.return_value = [buy_order, sell_order]

        order_service = Mock()

        process_partial_sells(
            instrument=instrument,
            strategy=strategy,
            order_service=order_service,
            buy_order=buy_order,
            current_price=130.0,
            market_order_dto=market_order_dto,
        )

        self.assertEqual(mock_place_partial_sell_order.call_count, 1)
        self.assertEqual(_applied_partial_sell_rules[instrument.id], {1})

        process_partial_sells(
            instrument=instrument,
            strategy=strategy,
            order_service=order_service,
            buy_order=buy_order,
            current_price=131.0,
            market_order_dto=market_order_dto,
        )

        self.assertEqual(mock_place_partial_sell_order.call_count, 1)
        self.assertEqual(mock_modify_bracket.call_count, 1)


if __name__ == "__main__":
    unittest.main()
