import unittest
import json
from datetime import time, datetime, timedelta
from unittest.mock import Mock, patch

from app.data.strategy import Strategy, StrategyDetail, FilterOption
from app.data.instrument import Instrument


class TestFilterOption(unittest.TestCase):
    """Test FilterOption class."""

    def test_filter_option_creation(self):
        """Test creating a FilterOption."""
        fo = FilterOption(name="priceAbove", value="10")
        self.assertEqual(fo.name, "priceAbove")
        self.assertEqual(fo.value, "10")

    def test_filter_option_to_tagvalue(self):
        """Test FilterOption.to_tagValue conversion."""
        fo = FilterOption(name="priceAbove", value="10")
        tag = fo.to_tagValue()
        self.assertEqual(tag.tag, "priceAbove")
        self.assertEqual(tag.value, "10")


class TestStrategyDetail(unittest.TestCase):
    """Test StrategyDetail class."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_detail_dict = {
            "instrument": "STK",
            "locationCode": "US",
            "scanCode": "TOP_PERC_GAINERS",
            "opening_hours": ["09:30:00", "16:00:00"],
            "scan_options": [],
            "filter_options": [{"name": "priceAbove", "value": "5"}],
            "maxResults": 100,
            "minutes_to_order": 5,
            "max_shares_to_invest_per_trade": 100,
            "min_shares_to_invest_per_trade": 10,
            "max_volume_percent": 10.0,
            "max_price_per_trade": 5000,
            "min_price_per_trade": 500,
            "max_trades_per_day": 5,
            "stop_loss_percent": 3.0,
            "take_profit_percent": 5.0,
        }

    def test_strategy_detail_creation(self):
        """Test creating a StrategyDetail."""
        detail = StrategyDetail(
            instrument="STK",
            locationCode="US",
            scanCode="TOP_PERC_GAINERS",
            opening_hours=["09:30:00", "16:00:00"],
            open_hour=time(9, 30, 0),
            close_hour=time(16, 0, 0),
            scan_options=[],
            filter_options=[],
            maxResults=100,
            minutes_to_order=5,
            max_shares_to_invest_per_trade=100,
            min_shares_to_invest_per_trade=10,
            max_volume_percent=10.0,
            max_price_per_trade=5000,
            min_price_per_trade=500,
            max_trades_per_day=5,
            stop_loss_percent=3.0,
            take_profit_percent=5.0,
        )
        self.assertEqual(detail.instrument, "STK")
        self.assertEqual(detail.locationCode, "US")
        self.assertEqual(detail.open_hour, time(9, 30, 0))
        self.assertEqual(detail.close_hour, time(16, 0, 0))

    def test_strategy_detail_from_json_dict(self):
        """Test creating StrategyDetail from dictionary."""
        detail = StrategyDetail.from_json(self.valid_detail_dict)
        self.assertEqual(detail.instrument, "STK")
        self.assertEqual(detail.locationCode, "US")
        self.assertEqual(detail.open_hour, time(9, 30, 0))
        self.assertEqual(detail.close_hour, time(16, 0, 0))
        self.assertEqual(len(detail.filter_options), 1)
        self.assertIsInstance(detail.filter_options[0], FilterOption)

    def test_strategy_detail_from_json_string(self):
        """Test creating StrategyDetail from JSON string."""
        json_str = json.dumps(self.valid_detail_dict)
        detail = StrategyDetail.from_json(json_str)
        self.assertEqual(detail.instrument, "STK")
        self.assertEqual(detail.open_hour, time(9, 30, 0))
        self.assertEqual(detail.close_hour, time(16, 0, 0))

    def test_strategy_detail_from_json_invalid_opening_hours(self):
        """Test from_json with invalid opening_hours format."""
        invalid_dict = self.valid_detail_dict.copy()
        invalid_dict["opening_hours"] = ["invalid", "time"]
        
        detail = StrategyDetail.from_json(invalid_dict)
        self.assertIsNone(detail.open_hour)
        self.assertIsNone(detail.close_hour)

    def test_strategy_detail_from_json_missing_opening_hours(self):
        """Test from_json with missing opening_hours."""
        incomplete_dict = self.valid_detail_dict.copy()
        del incomplete_dict["opening_hours"]
        
        detail = StrategyDetail.from_json(incomplete_dict)
        self.assertIsNone(detail.open_hour)
        self.assertIsNone(detail.close_hour)

    def test_strategy_detail_from_json_single_opening_hour(self):
        """Test from_json with only one opening hour."""
        incomplete_dict = self.valid_detail_dict.copy()
        incomplete_dict["opening_hours"] = ["09:30:00"]
        
        detail = StrategyDetail.from_json(incomplete_dict)
        self.assertIsNone(detail.open_hour)
        self.assertIsNone(detail.close_hour)

    def test_strategy_detail_to_json(self):
        """Test converting StrategyDetail to JSON."""
        detail = StrategyDetail.from_json(self.valid_detail_dict)
        json_str = detail.to_json()
        recovered = json.loads(json_str)
        
        self.assertEqual(recovered["instrument"], "STK")
        self.assertEqual(recovered["locationCode"], "US")

    def test_strategy_detail_to_scanner_subscription(self):
        """Test converting StrategyDetail to ScannerSubscription."""
        detail = StrategyDetail.from_json(self.valid_detail_dict)
        sub = detail.to_scannerSubscription()
        
        self.assertEqual(sub.instrument, "STK")
        self.assertEqual(sub.locationCode, "US")
        self.assertEqual(sub.scanCode, "TOP_PERC_GAINERS")

    def test_strategy_detail_to_tag_value_list(self):
        """Test converting filter_options to TagValue list."""
        detail = StrategyDetail.from_json(self.valid_detail_dict)
        tags = detail.to_tagValueList()
        
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].tag, "priceAbove")
        self.assertEqual(tags[0].value, "5")

    def test_strategy_detail_to_scanner_options(self):
        """Test getting scanner options."""
        detail = StrategyDetail.from_json(self.valid_detail_dict)
        opts = detail.to_scannerOptions()
        self.assertEqual(opts, [])


class TestStrategy(unittest.TestCase):
    """Test Strategy class."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_strategy_dict = {
            "name": "GapOpen",
            "tags": ["US", "STOCK"],
            "details": {
                "instrument": "STK",
                "locationCode": "US",
                "scanCode": "TOP_PERC_GAINERS",
                "opening_hours": ["09:30:00", "16:00:00"],
                "scan_options": [],
                "filter_options": [{"name": "priceAbove", "value": "5"}],
                "maxResults": 100,
                "minutes_to_order": 5,
                "max_shares_to_invest_per_trade": 100,
                "min_shares_to_invest_per_trade": 10,
                "max_volume_percent": 10.0,
                "max_price_per_trade": 5000,
                "min_price_per_trade": 500,
                "max_trades_per_day": 5,
                "stop_loss_percent": 3.0,
                "take_profit_percent": 5.0,
            },
        }

    def test_strategy_creation(self):
        """Test creating a Strategy."""
        strategy = Strategy(name="GapOpen", tags=["US", "STOCK"])
        self.assertEqual(strategy.name, "GapOpen")
        self.assertEqual(strategy.tags, ["US", "STOCK"])
        self.assertTrue(strategy.is_active)

    def test_strategy_from_json_dict(self):
        """Test creating Strategy from dictionary."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        self.assertEqual(strategy.name, "GapOpen")
        self.assertEqual(strategy.tags, ["US", "STOCK"])
        self.assertIsNotNone(strategy.details)
        self.assertEqual(strategy.details.instrument, "STK")

    def test_strategy_from_json_string(self):
        """Test creating Strategy from JSON string."""
        json_str = json.dumps(self.valid_strategy_dict)
        strategy = Strategy.from_json(json_str)
        self.assertEqual(strategy.name, "GapOpen")
        self.assertEqual(strategy.tags, ["US", "STOCK"])

    def test_strategy_to_json(self):
        """Test converting Strategy to JSON."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        json_str = strategy.to_json()
        recovered = json.loads(json_str)
        
        self.assertEqual(recovered["name"], "GapOpen")
        self.assertEqual(recovered["tags"], ["US", "STOCK"])

    def test_strategy_get_stop_loss_price(self):
        """Test calculating stop loss price."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        buy_price = 100.0
        stop_loss = strategy.get_stop_loss_price(buy_price)
        
        # stop_loss_percent is 3.0
        expected = 100.0 * 3.0 / 100.0  # = 3.0
        self.assertEqual(stop_loss, expected)

    def test_strategy_get_take_profit_price(self):
        """Test calculating take profit price."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        buy_price = 100.0
        take_profit = strategy.get_take_profit_price(buy_price)
        
        # take_profit_percent is 5.0
        expected = 100.0 * 5.0 / 100.0  # = 5.0
        self.assertEqual(take_profit, expected)

    def test_strategy_get_volume_buy(self):
        """Test calculating volume to buy."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        avg_volume = 1000.0
        price = 50.0
        
        volume = strategy.get_volume_buy(avg_volume, price)
        
        # min of:
        # - max_shares_to_invest_per_trade = 100
        # - avg_volume * max_volume_percent / 100 = 1000 * 10 / 100 = 100
        # - max_price_per_trade / price = 5000 / 50 = 100
        self.assertEqual(volume, 100)

    def test_strategy_get_volume_buy_limited_by_max_price(self):
        """Test volume calculation limited by max_price_per_trade."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        avg_volume = 1000.0
        price = 100.0  # High price
        
        volume = strategy.get_volume_buy(avg_volume, price)
        
        # Limited by max_price_per_trade / price = 5000 / 100 = 50
        self.assertEqual(volume, 50)

    @patch("app.data.strategy.datetime")
    def test_strategy_is_market_open_now_during_hours(self, mock_datetime):
        """Test is_market_open_now during market hours."""
        # Mock current time to 10:00 AM on Monday
        mock_now = Mock()
        mock_now.time.return_value = time(10, 0, 0)
        mock_now.strftime.return_value = "MON"
        mock_datetime.now.return_value = mock_now
        
        strategy = Strategy.from_json(self.valid_strategy_dict)
        self.assertTrue(strategy.is_market_open_now())

    @patch("app.data.strategy.datetime")
    def test_strategy_is_market_open_now_outside_hours(self, mock_datetime):
        """Test is_market_open_now outside market hours."""
        # Mock current time to 8:00 AM (before market opens)
        mock_now = Mock()
        mock_now.time.return_value = time(8, 0, 0)
        mock_now.strftime.return_value = "MON"
        mock_datetime.now.return_value = mock_now
        
        strategy = Strategy.from_json(self.valid_strategy_dict)
        self.assertFalse(strategy.is_market_open_now())

    @patch("app.data.strategy.datetime")
    def test_strategy_is_market_open_now_weekend(self, mock_datetime):
        """Test is_market_open_now on weekend."""
        # Mock current time to Saturday
        mock_now = Mock()
        mock_now.time.return_value = time(10, 0, 0)
        mock_now.strftime.return_value = "SAT"
        mock_datetime.now.return_value = mock_now
        
        strategy = Strategy.from_json(self.valid_strategy_dict)
        self.assertFalse(strategy.is_market_open_now())

    def test_strategy_apply_strategy_on_instrument_insufficient_history(self):
        """Test apply_strategy_on_instrument with insufficient history."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        strategy.id = 1
        
        instrument = Mock(spec=Instrument)
        instrument.symbol = "TEST"
        instrument.daily_history = []  # No history
        
        strategy.apply_strategy_on_instrument(instrument)
        
        # Should return without setting is_candidate
        self.assertFalse(instrument.is_candidate)

    def _create_mock_instrument_with_history(self, bars, avg_volume=1000.0, market_price=100.0, volume_buy=50):
        """Helper to create a properly mocked instrument."""
        instrument = Mock()
        instrument.symbol = "TEST"
        instrument.daily_history = bars
        instrument.avg_volume = avg_volume
        instrument.market_price = market_price
        instrument.volume_buy = volume_buy
        
        # Set up side effects to update attributes when methods are called
        instrument.calculate_avg_volume = Mock(
            side_effect=lambda x: setattr(instrument, 'avg_volume', avg_volume)
        )
        instrument.set_market_price = Mock(
            side_effect=lambda: setattr(instrument, 'market_price', market_price)
        )
        instrument.set_volume_buy = Mock(
            side_effect=lambda v: setattr(instrument, 'volume_buy', v)
        )
        instrument.set_stop_loss_price = Mock()
        instrument.set_take_profit_price = Mock()
        instrument.store_history = Mock()
        
        return instrument

    def test_strategy_apply_strategy_on_instrument_not_candidate(self):
        """Test apply_strategy_on_instrument when instrument doesn't meet criteria."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        strategy.id = 1
        now_str = datetime.now().strftime("%Y%m%d %H:%M:%S")
        
        # Create mock bars where avg wap is NOT above open price
        bars = [
            Mock(open=100.0, wap=99.5, volume=50, date=now_str),
            Mock(open=100.0, wap=99.3, volume=50, date=now_str),
            Mock(open=100.0, wap=99.2, volume=50, date=now_str),
            Mock(open=100.0, wap=99.1, volume=50, date=now_str)
        ]
        
        instrument = self._create_mock_instrument_with_history(
            bars, avg_volume=50.0, market_price=1, volume_buy=1
        )
        
        strategy.apply_strategy_on_instrument(instrument)
        
        self.assertFalse(instrument.is_candidate)
        instrument.store_history.assert_called_once()

    def test_strategy_apply_strategy_on_instrument_candidate(self):
        """Test with helper function."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        strategy.id = 1
        now_str = datetime.now().strftime("%Y%m%d %H:%M:%S")
        
        bars = [
            Mock(open=100.0, wap=102.0, volume=1000, date=now_str),
            Mock(open=100.0, wap=103.0, volume=1200, date=now_str),
            Mock(open=100.0, wap=104.0, volume=1100, date=now_str),
            Mock(open=100.0, wap=105.0, volume=1300, date=now_str),
        ]
        
        instrument = self._create_mock_instrument_with_history(
            bars, avg_volume=1150.0, market_price=105.0, volume_buy=50
        )
        
        strategy.apply_strategy_on_instrument(instrument)
        
        self.assertTrue(instrument.is_candidate)
        instrument.store_history.assert_called_once()

    def test_strategy_apply_strategy_on_instrument_rejects_stale_last_bar(self):
        """Test apply_strategy_on_instrument rejects stale history bar older than 2 minutes."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        strategy.id = 1

        stale_str = (datetime.now() - timedelta(minutes=3)).strftime("%Y%m%d %H:%M:%S")
        bars = [
            Mock(open=100.0, wap=102.0, volume=1000, date=stale_str),
            Mock(open=100.0, wap=103.0, volume=1200, date=stale_str),
            Mock(open=100.0, wap=104.0, volume=1100, date=stale_str),
            Mock(open=100.0, wap=105.0, volume=1300, date=stale_str),
        ]

        instrument = self._create_mock_instrument_with_history(
            bars, avg_volume=1150.0, market_price=105.0, volume_buy=50
        )

        strategy.apply_strategy_on_instrument(instrument)

        self.assertFalse(instrument.is_candidate)
        instrument.store_history.assert_called_once()

    @patch("app.data.strategy.datetime")
    def test_strategy_apply_strategy_on_instrument_stale_when_current_1602_and_last_bar_0945(self, mock_datetime):
        """Verify minute-based stale check: 16:02 current minute vs 09:45 bar minute marks instrument non-candidate."""
        strategy = Strategy.from_json(self.valid_strategy_dict)
        strategy.id = 1

        mock_now = Mock()
        mock_now.minute = 2
        mock_datetime.now.return_value = mock_now

        bars = [
            Mock(open=100.0, wap=102.0, volume=1000, date="20260602 09:45:00"),
            Mock(open=100.0, wap=103.0, volume=1200, date="20260602 09:45:00"),
            Mock(open=100.0, wap=104.0, volume=1100, date="20260602 09:45:00"),
            Mock(open=100.0, wap=105.0, volume=1300, date="20260602 09:45:00"),
        ]

        instrument = self._create_mock_instrument_with_history(
            bars, avg_volume=1150.0, market_price=105.0, volume_buy=50
        )

        strategy.apply_strategy_on_instrument(instrument)

        self.assertFalse(instrument.is_candidate)
        instrument.store_history.assert_called_once()


if __name__ == "__main__":
    unittest.main()