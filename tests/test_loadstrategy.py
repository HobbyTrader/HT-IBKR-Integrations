import unittest
import json
import logging
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path

from app.loadstrategy import insert_strategy, main
from app.data.strategy import Strategy, StrategyDetail
from app.dto.strategy_dto import StrategyDTO


class TestLoadStrategy(unittest.TestCase):
    """Test suite for loadstrategy module."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_strategy_json = {
            "name": "US Stock High Open Gap Scan",
            "tags": ["US", "STOCK", "OPEN_GAP"],
            "details": {
                "instrument": "STK",
                "locationCode": "STK.US.MAJOR",
                "scanCode": "HIGH_OPEN_GAP",
                "scan_options": [],
                "filter_options": [
                    {
                        "name": "volumeAbove",
                        "value": "10000"
                    },
                    {
                        "name": "priceAbove",
                        "value": "5"
                    },
                    {
                        "name": "priceBelow",
                        "value": "100"
                    },
                    {
                        "name": "openGapPercAbove",
                        "value": "5"
                    },
                    {
                        "name": "openGapPercBelow",
                        "value": "55"
                    }
                ],
                "maxResults": 50,
                "minutes_to_order": 3,
                "max_shares_to_invest_per_trade": 1000,
                "min_shares_to_invest_per_trade": 100,
                "max_price_per_trade": 5000,
                "min_price_per_trade": 1000,
                "max_trades_per_day": 5,
                "opening_hours": "09:30-16:00",
                "min_open_trade_gap_percentage": 2.0,
                "max_open_trade_gap_percentage": 10.0,
                "max_volume_percent": 1.0,
                "stop_loss_percent": 95.0,
                "take_profit_percent": 110.0,
                "increase_position_candidate_percentage": 0.5
            }
        }
        
        self.sample_strategies_file = {
            "strategies": [
                self.sample_strategy_json,
                {
                    "name": "EU-DE Stock High Open Gap Scan",
                    "tags": ["EU", "STOCK", "OPEN_GAP"],
                    "details": {
                        "instrument": "STOCK.EU",
                        "locationCode": "STK.EU.IBIS",
                        "scanCode": "HIGH_OPEN_GAP",
                        "scan_options": [],
                        "filter_options": [
                            {
                                "name": "volumeAbove",
                                "value": "10000"
                            },
                            {
                                "name": "priceAbove",
                                "value": "5"
                            },
                            {
                                "name": "priceBelow",
                                "value": "100"
                            },
                            {
                                "name": "openGapPercAbove",
                                "value": "10"
                            },
                            {
                                "name": "openGapPercBelow",
                                "value": "40"
                            }
                        ],
                        "maxResults": 50,
                        "minutes_to_order": 3,
                        "max_shares_to_invest_per_trade": 1000,
                        "min_shares_to_invest_per_trade": 100,
                        "max_price_per_trade": 5000,
                        "min_price_per_trade": 1000,
                        "max_trades_per_day": 5,
                        "opening_hours": "09:30-16:00",
                        "min_open_trade_gap_percentage": 2.0,
                        "max_open_trade_gap_percentage": 10.0,
                        "stop_loss_percent": 95.0,
                        "take_profit_percent": 110.0,
                        "max_volume_percent": 1.0,
                        "increase_position_candidate_percentage": 0.8
                    }
                }
            ]
        }

    # ============================================================================
    # TEST insert_strategy FUNCTION
    # ============================================================================

    @patch('app.loadstrategy.logger')
    def test_insert_strategy_new_strategy(self, mock_logger):
        """Test inserting a new strategy that doesn't exist."""
        # Arrange
        mock_dto = Mock(spec=StrategyDTO)
        mock_dto.get_strategy_by_name.return_value = None
        
        # Act
        insert_strategy(mock_dto, self.sample_strategies_file)
        
        # Assert
        self.assertEqual(mock_dto.save_strategy.call_count, 2)
        mock_dto.update_strategy.assert_not_called()
        mock_logger.info.assert_called()

    @patch('app.loadstrategy.logger')
    def test_insert_strategy_existing_strategy(self, mock_logger):
        """Test updating an existing strategy."""
        # Arrange
        mock_dto = Mock(spec=StrategyDTO)
        existing_strategy = Mock()
        existing_strategy.id = 1
        existing_strategy.name = "Test Strategy"
        mock_dto.get_strategy_by_name.return_value = existing_strategy
        
        # Act
        insert_strategy(mock_dto, self.sample_strategies_file)
        
        # Assert
        self.assertEqual(mock_dto.update_strategy.call_count, 2)
        mock_dto.save_strategy.assert_not_called()
        mock_logger.info.assert_called()

    @patch('app.loadstrategy.logger')
    def test_insert_strategy_empty_list(self, mock_logger):
        """Test with empty strategies list."""
        # Arrange
        mock_dto = Mock(spec=StrategyDTO)
        empty_strategies = {"strategies": []}
        
        # Act
        insert_strategy(mock_dto, empty_strategies)
        
        # Assert
        mock_dto.save_strategy.assert_not_called()
        mock_dto.update_strategy.assert_not_called()

    @patch('app.loadstrategy.logger')
    def test_insert_strategy_no_strategies_key(self, mock_logger):
        """Test with missing 'strategies' key."""
        # Arrange
        mock_dto = Mock(spec=StrategyDTO)
        invalid_data = {}
        
        # Act
        insert_strategy(mock_dto, invalid_data)
        
        # Assert
        mock_dto.save_strategy.assert_not_called()
        mock_dto.update_strategy.assert_not_called()

    @patch('app.loadstrategy.Strategy')
    @patch('app.loadstrategy.logger')
    def test_insert_strategy_handles_exception(self, mock_logger, mock_strategy_class):
        """Test exception handling during strategy insertion."""
        # Arrange
        mock_dto = Mock(spec=StrategyDTO)
        mock_dto.get_strategy_by_name.side_effect = Exception("Database error")
        
        # Act & Assert
        with self.assertRaises(Exception):
            insert_strategy(mock_dto, self.sample_strategies_file)

    # ============================================================================
    # TEST main FUNCTION
    # ============================================================================

    @patch('app.loadstrategy.files')
    @patch('app.loadstrategy.StrategyDTO')
    @patch('app.loadstrategy.insert_strategy')
    @patch('app.loadstrategy.logger')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_with_valid_json_file(self, mock_file, mock_logger, mock_insert, mock_dto_class, mock_files):
        """Test main function with valid JSON file."""
        # Arrange
        mock_file.return_value.read.return_value = json.dumps(self.sample_strategies_file)
        mock_files.return_value.joinpath.return_value = "app/strategies/Stock_us.json"
        
        with patch('sys.argv', ['loadstrategy', 'Stock_us.json']):
            # Act
            main()
        
        # Assert
        mock_insert.assert_called_once()
        mock_logger.info.assert_called()

    @patch('app.loadstrategy.logger')
    @patch('sys.exit')
    def test_main_no_arguments(self, mock_exit, mock_logger):
        """Test main function with no arguments."""
        # Arrange
        with patch('sys.argv', ['loadstrategy']):
            # Act
            main()
        
        # Assert
        mock_exit.assert_called_once_with(1)

    @patch('app.loadstrategy.files')
    @patch('app.loadstrategy.logger')
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_main_file_not_found(self, mock_file, mock_logger, mock_files):
        """Test main function with non-existent file."""
        # Arrange
        mock_files.return_value.joinpath.return_value = "nonexistent.json"
        
        with patch('sys.argv', ['loadstrategy', 'nonexistent.json']):
            # Act & Assert
            with self.assertRaises(FileNotFoundError):
                main()

    @patch('app.loadstrategy.files')
    @patch('app.loadstrategy.logger')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_main_invalid_json(self, mock_file, mock_logger, mock_files):
        """Test main function with invalid JSON content."""
        # Arrange
        mock_files.return_value.joinpath.return_value = "app/strategies/invalid.json"
        
        with patch('sys.argv', ['loadstrategy', 'invalid.json']):
            # Act & Assert
            with self.assertRaises(json.JSONDecodeError):
                main()

    @patch('app.loadstrategy.files')
    @patch('app.loadstrategy.StrategyDTO')
    @patch('app.loadstrategy.insert_strategy')
    @patch('app.loadstrategy.logger')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_with_absolute_path(self, mock_file, mock_logger, mock_insert, mock_dto_class, mock_files):
        """Test main function with absolute file path."""
        # Arrange
        absolute_path = "/Users/test/strategies/Stock_us.json"
        mock_file.return_value.read.return_value = json.dumps(self.sample_strategies_file)
        
        with patch('sys.argv', ['loadstrategy', absolute_path]):
            # Act
            main()
        
        # Assert
        mock_files.assert_not_called()  # Should not use files() for absolute paths
        mock_insert.assert_called_once()

    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================

    @patch('app.loadstrategy.StrategyDTO')
    @patch('app.loadstrategy.logger')
    def test_integration_insert_multiple_strategies(self, mock_logger, mock_dto_class):
        """Integration test for inserting multiple strategies."""
        # Arrange
        mock_dto = Mock(spec=StrategyDTO)
        mock_dto.get_strategy_by_name.return_value = None
        mock_dto_class.return_value = mock_dto
        
        # Act
        insert_strategy(mock_dto, self.sample_strategies_file)
        
        # Assert
        self.assertEqual(mock_dto.save_strategy.call_count, 2)
        
        # Verify both strategies were processed
        calls = mock_dto.save_strategy.call_args_list
        self.assertEqual(len(calls), 2)


class TestStrategyFromJson(unittest.TestCase):
    """Test Strategy.from_json method used by loadstrategy."""

    def test_from_json_with_dict(self):
        """Test creating Strategy from dictionary."""
        # Arrange
        strategy_dict = {
            "name": "Test Strategy",
            "tags": ["US", "STOCK"],
            "details": {
                "instrument": "STK",
                "locationCode": "STK.US.MAJOR",
                "scanCode": "HIGH_OPEN_GAP",
                "scan_options": [],
                "filter_options": [
                    {
                        "name": "volumeAbove",
                        "value": "10000"
                    },
                    {
                        "name": "priceAbove",
                        "value": "5"
                    },
                    {
                        "name": "priceBelow",
                        "value": "100"
                    },
                    {
                        "name": "openGapPercAbove",
                        "value": "5"
                    },
                    {
                        "name": "openGapPercBelow",
                        "value": "55"
                    }
                ],
                "maxResults": 50,
                "minutes_to_order": 3,
                "max_shares_to_invest_per_trade": 1000,
                "min_shares_to_invest_per_trade": 100,
                "max_price_per_trade": 5000,
                "min_price_per_trade": 1000,
                "max_trades_per_day": 5,
                "opening_hours": "09:30-16:00",
                "min_open_trade_gap_percentage": 2.0,
                "max_open_trade_gap_percentage": 10.0,
                "max_volume_percent": 1.0,
                "stop_loss_percent": 95.0,
                "take_profit_percent": 110.0,
                "increase_position_candidate_percentage": 0.5
            }
        }
        
        # Act
        strategy = Strategy.from_json(strategy_dict)
        
        # Assert
        self.assertEqual(strategy.name, "Test Strategy")
        self.assertEqual(strategy.tags, ["US", "STOCK"])

    def test_from_json_with_string(self):
        """Test creating Strategy from JSON string."""
        # Arrange
        strategy_json = json.dumps({
            "name": "Test Strategy",
            "tags": ["US", "STOCK"],
            "details": {
               "instrument": "STK",
                "locationCode": "STK.US.MAJOR",
                "scanCode": "HIGH_OPEN_GAP",
                "scan_options": [],
                "filter_options": [
                    {
                        "name": "volumeAbove",
                        "value": "10000"
                    },
                    {
                        "name": "priceAbove",
                        "value": "5"
                    },
                    {
                        "name": "priceBelow",
                        "value": "100"
                    },
                    {
                        "name": "openGapPercAbove",
                        "value": "5"
                    },
                    {
                        "name": "openGapPercBelow",
                        "value": "55"
                    }
                ],
                "maxResults": 50,
                "minutes_to_order": 3,
                "max_shares_to_invest_per_trade": 1000,
                "min_shares_to_invest_per_trade": 100,
                "max_price_per_trade": 5000,
                "min_price_per_trade": 1000,
                "max_trades_per_day": 5,
                "opening_hours": "09:30-16:00",
                "min_open_trade_gap_percentage": 2.0,
                "max_open_trade_gap_percentage": 10.0,
                "max_volume_percent": 1.0,
                "stop_loss_percent": 95.0,
                "take_profit_percent": 110.0,
                "increase_position_candidate_percentage": 0.5
            }
        })
        
        # Act
        strategy = Strategy.from_json(strategy_json)
        
        # Assert
        self.assertEqual(strategy.name, "Test Strategy")
        self.assertIsInstance(strategy.tags, list)


if __name__ == '__main__':
    unittest.main()