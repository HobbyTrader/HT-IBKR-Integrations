import unittest
import json
from unittest.mock import Mock, patch

from vendor.ibapi.common import BarData
from vendor.ibapi.contract import Contract

from app.data.instrument import Instrument


class TestInstrument(unittest.TestCase):
    """Test Instrument class."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_instrument_data = {
            "id": 1,
            "symbol": "AAPL",
            "sectype": "STK",
            "currency": "USD",
            "exchange": "SMART",
            "strategy_id": 5,
            "market_price": 150.0,
            "avg_volume": 1000000.0,
            "stop_loss_price": 145.0,
            "take_profit_price": 157.5,
            "volume_buy": 100,
            "is_candidate": True,
        }

    # ------------------------------------------------------------------ Creation

    def test_instrument_creation(self):
        """Test creating an Instrument."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        self.assertEqual(instrument.id, 1)
        self.assertEqual(instrument.symbol, "AAPL")
        self.assertEqual(instrument.sectype, "STK")
        self.assertEqual(instrument.currency, "USD")
        self.assertEqual(instrument.exchange, "SMART")
        self.assertEqual(instrument.strategy_id, 0)
        self.assertEqual(instrument.market_price, 0.0)
        self.assertEqual(instrument.avg_volume, 0.0)
        self.assertEqual(instrument.volume_buy, 0)
        self.assertFalse(instrument.is_candidate)

    def test_instrument_creation_with_optional_fields(self):
        """Test creating an Instrument with optional fields."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
            strategy_id=5,
            market_price=150.0,
            volume_buy=100,
            is_candidate=True,
        )
        self.assertEqual(instrument.strategy_id, 5)
        self.assertEqual(instrument.market_price, 150.0)
        self.assertEqual(instrument.volume_buy, 100)
        self.assertTrue(instrument.is_candidate)

    # ------------------------------------------------------------------ from_row

    def test_from_row_valid(self):
        """Test creating Instrument from valid row."""
        row = (1, "AAPL", "STK", "USD", "SMART")
        instrument = Instrument.from_row(row)
        
        self.assertEqual(instrument.id, 1)
        self.assertEqual(instrument.symbol, "AAPL")
        self.assertEqual(instrument.sectype, "STK")
        self.assertEqual(instrument.currency, "USD")
        self.assertEqual(instrument.exchange, "SMART")

    def test_from_row_with_extra_columns(self):
        """Test from_row ignores extra columns."""
        row = (1, "AAPL", "STK", "USD", "SMART", "extra1", "extra2")
        instrument = Instrument.from_row(row)
        
        self.assertEqual(instrument.id, 1)
        self.assertEqual(instrument.symbol, "AAPL")

    def test_from_row_insufficient_columns(self):
        """Test from_row raises ValueError with insufficient columns."""
        row = (1, "AAPL", "STK")  # Only 3 columns, needs 5
        
        with self.assertRaises(ValueError) as context:
            Instrument.from_row(row)
        
        self.assertEqual(str(context.exception), "Invalid row")

    # ------------------------------------------------------------------ JSON serialization

    def test_to_json(self):
        """Test converting Instrument to JSON."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        json_str = instrument.to_json()
        recovered = json.loads(json_str)
        
        self.assertEqual(recovered["id"], 1)
        self.assertEqual(recovered["symbol"], "AAPL")
        self.assertEqual(recovered["sectype"], "STK")

    def test_from_json_dict(self):
        """Test creating Instrument from dictionary."""
        instrument = Instrument.from_json(self.valid_instrument_data)
        
        self.assertEqual(instrument.id, 1)
        self.assertEqual(instrument.symbol, "AAPL")
        self.assertEqual(instrument.market_price, 150.0)
        self.assertTrue(instrument.is_candidate)

    def test_from_json_string(self):
        """Test creating Instrument from JSON string."""
        json_str = json.dumps(self.valid_instrument_data)
        instrument = Instrument.from_json(json_str)
        
        self.assertEqual(instrument.id, 1)
        self.assertEqual(instrument.symbol, "AAPL")

    # ------------------------------------------------------------------ to_contract

    def test_to_contract(self):
        """Test converting Instrument to IBAPI Contract."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        contract = instrument.to_contract()
        
        self.assertIsInstance(contract, Contract)
        self.assertEqual(contract.symbol, "AAPL")
        self.assertEqual(contract.secType, "STK")
        self.assertEqual(contract.currency, "USD")
        self.assertEqual(contract.exchange, "SMART")

    # ------------------------------------------------------------------ set_market_price

    def test_set_market_price_with_history(self):
        """Test setting market price from daily history."""
        bar1 = Mock(spec=BarData)
        bar1.close = 150.0
        bar2 = Mock(spec=BarData)
        bar2.close = 152.5
        bar3 = Mock(spec=BarData)
        bar3.close = 155.0
        
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        instrument.daily_history = [bar1, bar2, bar3]
        
        instrument.set_market_price()
        
        # Should use the last bar's close price
        self.assertEqual(instrument.market_price, 155.0)

    @patch("app.data.instrument.logger")
    def test_set_market_price_no_history(self, mock_logger):
        """Test set_market_price with no history logs warning."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        instrument.daily_history = []
        
        instrument.set_market_price()
        
        mock_logger.warning.assert_called_once()
        self.assertEqual(instrument.market_price, 0.0)  # Not changed

    # ------------------------------------------------------------------ calculate_avg_volume

    def test_calculate_avg_volume(self):
        """Test calculating average volume."""
        bar1 = Mock(spec=BarData)
        bar1.volume = 1000
        bar2 = Mock(spec=BarData)
        bar2.volume = 1500
        bar3 = Mock(spec=BarData)
        bar3.volume = 2000
        bar4 = Mock(spec=BarData)
        bar4.volume = 2500
        
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        instrument.daily_history = [bar1, bar2, bar3, bar4]
        
        instrument.calculate_avg_volume(3)
        
        # Average of last 3 bars: (1500 + 2000 + 2500) / 3 = 2000
        self.assertEqual(instrument.avg_volume, 2000.0)

    def test_calculate_avg_volume_all_bars(self):
        """Test calculating average volume with all bars."""
        bar1 = Mock(spec=BarData)
        bar1.volume = 1000
        bar2 = Mock(spec=BarData)
        bar2.volume = 2000
        
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        instrument.daily_history = [bar1, bar2]
        
        instrument.calculate_avg_volume(2)
        
        # Average of all bars: (1000 + 2000) / 2 = 1500
        self.assertEqual(instrument.avg_volume, 1500.0)

    @patch("app.data.instrument.logger")
    def test_calculate_avg_volume_no_history(self, mock_logger):
        """Test calculate_avg_volume with no history logs warning."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        instrument.daily_history = []
        
        instrument.calculate_avg_volume(3)
        
        mock_logger.warning.assert_called_once()
        self.assertEqual(instrument.avg_volume, 0.0)  # Not changed

    # ------------------------------------------------------------------ set_stop_loss_price

    def test_set_stop_loss_price(self):
        """Test setting stop loss price."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        
        instrument.set_stop_loss_price(145.567)
        
        # Should be rounded to 2 decimals
        self.assertEqual(instrument.stop_loss_price, 145.57)

    def test_set_stop_loss_price_rounding(self):
        """Test stop loss price rounding."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        
        instrument.set_stop_loss_price(145.123)
        self.assertEqual(instrument.stop_loss_price, 145.12)

    # ------------------------------------------------------------------ set_take_profit_price

    def test_set_take_profit_price(self):
        """Test setting take profit price."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        
        instrument.set_take_profit_price(157.893)
        
        # Should be rounded to 2 decimals
        self.assertEqual(instrument.take_profit_price, 157.89)

    def test_set_take_profit_price_rounding(self):
        """Test take profit price rounding."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        
        instrument.set_take_profit_price(157.456)
        self.assertEqual(instrument.take_profit_price, 157.46)

    # ------------------------------------------------------------------ set_volume_buy

    def test_set_volume_buy(self):
        """Test setting volume to buy."""
        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        
        instrument.set_volume_buy(100)
        
        self.assertEqual(instrument.volume_buy, 100)


    # ------------------------------------------------------------------ store_history

    @patch("app.data.instrument.HistoryDTO")
    @patch("app.data.instrument.History.from_bar")
    def test_store_history_calls_dto_for_each_bar(self, mock_from_bar, mock_history_dto):
        """Test store_history calls HistoryDTO.save_history for each bar."""
        bar1 = Mock(spec=BarData)
        bar1.date = "2024-01-01 09:30"
        bar1.open = 100.0
        bar1.high = 105.0
        bar1.low = 99.0
        bar1.close = 102.0
        bar1.volume = 1000
        bar1.wap = 101.0

        bar2 = Mock(spec=BarData)
        bar2.date = "2024-01-02 09:30"
        bar2.open = 102.0
        bar2.high = 106.0
        bar2.low = 101.0
        bar2.close = 104.0
        bar2.volume = 1100
        bar2.wap = 103.0

        instrument = Instrument(
            id=1,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        instrument.daily_history = [bar1, bar2]

        fake_hist1 = Mock()
        fake_hist2 = Mock()
        mock_from_bar.side_effect = [fake_hist1, fake_hist2]

        instrument.store_history()

        self.assertEqual(mock_from_bar.call_count, 2)
        mock_from_bar.assert_any_call(1, "AAPL", bar1)
        mock_from_bar.assert_any_call(1, "AAPL", bar2)

        dto_instance = mock_history_dto.return_value
        self.assertEqual(dto_instance.save_history.call_count, 2)
        dto_instance.save_history.assert_any_call(fake_hist1)
        dto_instance.save_history.assert_any_call(fake_hist2)


if __name__ == "__main__":
    unittest.main()