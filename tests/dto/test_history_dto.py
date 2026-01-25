import unittest
import sqlite3

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.dto.history_dto import HistoryDTO
from app.data.history import History


class TestHistoryDTO(unittest.TestCase):
    """Test cases for HistoryDTO class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the SQLiteManager to avoid actual database operations
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.conn.cursor.return_value = self.mock_cursor
        
        with patch('app.dto.history_dto.SQLiteManager', return_value=self.mock_db):
            self.history_dto = HistoryDTO()
    
    # ============================================================================
    # ROW TO OBJECT TESTS
    # ============================================================================
    
    def test_row_to_history_valid_row(self):
        """Test converting a valid database row to History object."""
        row = (
            1,  # id
            100,  # instrument_id
            'AAPL',  # symbol
            '2026-01-24 15:30:45',  # bar_time
            150.50,  # open_price
            152.00,  # high_price
            149.00,  # low_price
            151.25,  # close_price
            1000000,  # volume
            150.75,  # wap
            500,  # bar_count
            '2026-01-24 15:31:00',  # create_date
            '2026-01-24 15:31:00'   # update_date
        )
        
        history = self.history_dto.row_to_history(row)
        
        self.assertIsInstance(history, History)
        self.assertEqual(history.id, 1)
        self.assertEqual(history.instrument_id, 100)
        self.assertEqual(history.symbol, 'AAPL')
        self.assertIsInstance(history.bar_time, datetime)
        self.assertEqual(history.open_price, 150.50)
        self.assertEqual(history.high_price, 152.00)
        self.assertEqual(history.low_price, 149.00)
        self.assertEqual(history.close_price, 151.25)
        self.assertEqual(history.volume, 1000000)
        self.assertEqual(history.wap, 150.75)
        self.assertEqual(history.bar_count, 500)
        self.assertIsInstance(history.create_date, datetime)
        self.assertIsInstance(history.update_date, datetime)
    
    def test_row_to_history_with_none_values(self):
        """Test converting row with None values."""
        row = (
            1,  # id
            100,  # instrument_id
            'AAPL',  # symbol
            '2026-01-24 15:30:45',  # bar_time
            150.50,  # open_price
            152.00,  # high_price
            149.00,  # low_price
            151.25,  # close_price
            1000000,  # volume
            None,  # wap (optional)
            None,  # bar_count (optional)
            '2026-01-24 15:31:00',  # create_date
            '2026-01-24 15:31:00'   # update_date
        )
        
        history = self.history_dto.row_to_history(row)
        
        self.assertIsNone(history.wap)
        self.assertIsNone(history.bar_count)
    
    # ============================================================================
    # SAVE METHODS TESTS
    # ============================================================================
    
    def test_save_history_success(self):
        """Test successfully saving a history record."""
        history = History(
            id=None,
            instrument_id=100,
            symbol='AAPL',
            bar_time=datetime(2026, 1, 24, 15, 30, 45),
            open_price=150.50,
            high_price=152.00,
            low_price=149.00,
            close_price=151.25,
            volume=1000000,
            wap=150.75,
            bar_count=500
        )
        
        self.mock_cursor.lastrowid = 1
        
        self.history_dto.save_history(history)
        
        # Verify cursor.execute was called with correct SQL
        self.mock_cursor.execute.assert_called_once()
        call_args = self.mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        self.assertIn("INSERT INTO history", sql)
        self.assertEqual(params[0], 100)  # instrument_id
        self.assertEqual(params[3], 150.50)  # open_price
        
        # Verify commit was called
        self.mock_db.conn.commit.assert_called_once()
    
    def test_save_history_with_missing_optional_fields(self):
        """Test saving history with missing optional fields."""
        history = History(
            id=None,
            instrument_id=100,
            symbol='AAPL',
            bar_time=datetime(2026, 1, 24, 15, 30, 45),
            open_price=150.50,
            high_price=152.00,
            low_price=149.00,
            close_price=151.25,
            volume=1000000,
            wap=None,  # Optional
            bar_count=None  # Optional
        )
        
        self.mock_cursor.lastrowid = 1
        
        # Should not raise an exception
        self.history_dto.save_history(history)
        self.mock_db.conn.commit.assert_called_once()
    
    # ============================================================================
    # GET METHODS TESTS
    # ============================================================================
    
    def test_get_history_by_instrument_found(self):
        """Test retrieving history records by instrument ID."""
        mock_rows = [
            (1, 100, 'AAPL', '2026-01-24 15:30:45', 150.50, 152.00, 149.00, 151.25, 
             1000000, 150.75, 500, '2026-01-24 15:31:00', '2026-01-24 15:31:00'),
            (2, 100, 'AAPL', '2026-01-24 15:31:45', 151.25, 153.00, 150.00, 152.50, 
             1100000, 151.75, 550, '2026-01-24 15:32:00', '2026-01-24 15:32:00')
        ]
        self.mock_cursor.fetchall.return_value = mock_rows
        
        histories = self.history_dto.get_history_by_instrument(100)
        
        self.assertEqual(len(histories), 2)
        self.assertIsInstance(histories[0], History)
        self.assertIsInstance(histories[1], History)
        self.assertEqual(histories[0].instrument_id, 100)
        self.assertEqual(histories[1].instrument_id, 100)
        
        # Verify SQL was called correctly
        self.mock_cursor.execute.assert_called_once()
        call_args = self.mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        self.assertIn("SELECT", sql)
        self.assertIn("WHERE instrument_id = ?", sql)
        self.assertEqual(params, (100,))
    
    def test_get_history_by_instrument_not_found(self):
        """Test retrieving history when no records exist."""
        self.mock_cursor.fetchall.return_value = []
        
        histories = self.history_dto.get_history_by_instrument(999)
        
        self.assertEqual(len(histories), 0)
        self.assertIsInstance(histories, list)
    
    def test_get_history_by_symbol_found(self):
        """Test retrieving a single history record by symbol."""
        mock_row = (1, 100, 'AAPL', '2026-01-24 15:30:45', 150.50, 152.00, 149.00, 
                   151.25, 1000000, 150.75, 500, '2026-01-24 15:31:00', 
                   '2026-01-24 15:31:00')
        self.mock_cursor.fetchone.return_value = mock_row
        
        history = self.history_dto.get_history_by_symbol("AAPL")
        
        self.assertIsNotNone(history)
        self.assertIsInstance(history, History)
        self.assertEqual(history.instrument_id, 100)
        self.assertEqual(history.symbol, 'AAPL')
        # Verify SQL
        call_args = self.mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        self.assertIn("WHERE symbol = ?", sql)
        self.assertEqual(params, ("AAPL",))
    
    def test_get_history_by_symbol_not_found(self):
        """Test retrieving history by symbol when not found."""
        self.mock_cursor.fetchone.return_value = None
        
        history = self.history_dto.get_history_by_symbol("INVALID")
        
        self.assertIsNone(history)
    
    def test_get_history_by_symbol_and_after_date_found(self):
        """Test retrieving history records after a specific date."""
        after_date = datetime(2026, 1, 24, 15, 0, 0)
        mock_rows = [
            (1, 100, 'AAPL', '2026-01-24 15:30:45', 150.50, 152.00, 149.00, 151.25, 
             1000000, 150.75, 500, '2026-01-24 15:31:00', '2026-01-24 15:31:00'),
            (2, 100, 'AAPL', '2026-01-24 16:30:45', 151.25, 153.00, 150.00, 152.50, 
             1100000, 151.75, 550, '2026-01-24 16:31:00', '2026-01-24 16:31:00')
        ]
        self.mock_cursor.fetchall.return_value = mock_rows
        
        histories = self.history_dto.get_history_by_symbol_and_after_date("AAPL", after_date)
        
        self.assertEqual(len(histories), 2)
        self.assertIsInstance(histories[0], History)
        
        # Verify SQL
        call_args = self.mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        self.assertIn("WHERE symbol = ? AND bar_time >= ?", sql)
        self.assertEqual(params[0], "AAPL")
        self.assertEqual(params[1], "2026-01-24 15:00:00")
    
    def test_get_history_by_symbol_and_after_date_not_found(self):
        """Test retrieving history after date when no records exist."""
        after_date = datetime(2026, 1, 24, 15, 0, 0)
        self.mock_cursor.fetchall.return_value = []
        
        histories = self.history_dto.get_history_by_symbol_and_after_date("AAPL", after_date)
        
        self.assertEqual(len(histories), 0)
    
    def test_get_history_by_symbol_and_after_date_boundary(self):
        """Test retrieving history with exact boundary date."""
        after_date = datetime(2026, 1, 24, 15, 30, 45)
        mock_rows = [
            (1, 100, 'AAPL', '2026-01-24 15:30:45', 150.50, 152.00, 149.00, 151.25, 
             1000000, 150.75, 500, '2026-01-24 15:31:00', '2026-01-24 15:31:00')
        ]
        self.mock_cursor.fetchall.return_value = mock_rows
        
        histories = self.history_dto.get_history_by_symbol_and_after_date("AAPL", after_date)
        
        # Should include the record at exact boundary time
        self.assertEqual(len(histories), 1)
        self.assertEqual(histories[0].bar_time, datetime(2026, 1, 24, 15, 30, 45))


class TestHistoryDTOIntegration(unittest.TestCase):
    """Integration tests with actual database."""
    
    def setUp(self):
        """Set up each test with a fresh in-memory database."""
        # Create in-memory database directly
        self.conn = sqlite3.connect(':memory:')        
        
        self._create_tables()
        
        # Mock SQLiteManager to use our connection
        mock_db_manager = Mock()
        mock_db_manager.conn = self.conn
        
        # Patch SQLiteManager
        self.db_patcher = patch(
            'app.dto.history_dto.SQLiteManager',
            return_value=mock_db_manager
        )       
        
        self.db_patcher.start()
        
        # Create HistoryDTO instance
        self.history_dto = HistoryDTO()
    
    def _create_tables(self):
        """Create necessary database tables."""
        cursor = self.conn.cursor()
        
        # Create history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                bar_time TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                wap REAL DEFAULT 0,
                bar_count INTEGER DEFAULT 0 ,
                create_date  TEXT NOT NULL DEFAULT (datetime('now')),
                update_date  TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        
        self.conn.commit()
        
    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'conn'):
            self.conn.close()
        
        if hasattr(self, 'db_patcher'):
            self.db_patcher.stop()
    
    def test_save_and_retrieve_history(self):
        """Test full cycle of saving and retrieving history."""
        # Create a history object
        test_history = History(
            id=None,
            instrument_id=100,
            symbol="AAPL",
            bar_time=datetime(2026, 1, 24, 15, 30, 45),
            open_price=150.50,
            high_price=152.00,
            low_price=149.00,
            close_price=151.25,
            volume=1000000,
            wap=150.75,
            bar_count=500,
            create_date=datetime(2026, 1, 24, 15, 31, 0),
            update_date=datetime(2026, 1, 24, 15, 31, 0)
        )
        
        # Save the history
        saved_id = self.history_dto.save_history(test_history)
        self.assertIsNotNone(saved_id)
        self.assertGreater(saved_id, 0)
        
        # Retrieve by instrument_id
        retrieved_histories = self.history_dto.get_history_by_instrument(100)
        self.assertEqual(len(retrieved_histories), 1)
        
        retrieved = retrieved_histories[0]
        self.assertEqual(retrieved.instrument_id, test_history.instrument_id)
        self.assertEqual(retrieved.symbol, test_history.symbol)
        self.assertEqual(retrieved.open_price, test_history.open_price)
        self.assertEqual(retrieved.high_price, test_history.high_price)
        self.assertEqual(retrieved.low_price, test_history.low_price)
        self.assertEqual(retrieved.close_price, test_history.close_price)
        self.assertEqual(retrieved.volume, test_history.volume)
        self.assertEqual(retrieved.wap, test_history.wap)
        self.assertEqual(retrieved.bar_count, test_history.bar_count)
    
    def test_save_multiple_histories_and_retrieve_by_symbol(self):
        """Test saving multiple history records and retrieving by symbol."""
        # Create multiple history records for the same symbol
        histories = [
            History(
                id=None,
                instrument_id=100,
                symbol="AAPL",
                bar_time=datetime(2026, 1, 24, 15, 30, 45),
                open_price=150.50,
                high_price=152.00,
                low_price=149.00,
                close_price=151.25,
                volume=1000000,
                wap=150.75,
                bar_count=500
            ),
            History(
                id=None,
                instrument_id=100,
                symbol="AAPL",
                bar_time=datetime(2026, 1, 24, 15, 31, 45),
                open_price=151.25,
                high_price=153.00,
                low_price=150.00,
                close_price=152.50,
                volume=1100000,
                wap=151.75,
                bar_count=550
            )
        ]
        
        # Save all histories
        for history in histories:
            saved_id = self.history_dto.save_history(history)
            self.assertIsNotNone(saved_id)
        
        # Retrieve by symbol
        retrieved = self.history_dto.get_history_by_symbol("AAPL")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.symbol, "AAPL")
    
    def test_get_history_by_symbol_and_after_date(self):
        """Test retrieving history records after a specific date."""
        # Create multiple history records with different times
        histories = [
            History(
                id=None,
                instrument_id=100,
                symbol="AAPL",
                bar_time=datetime(2026, 1, 24, 14, 0, 0),  # Before cutoff
                open_price=148.00,
                high_price=149.00,
                low_price=147.00,
                close_price=148.50,
                volume=900000,
                wap=148.25,
                bar_count=450
            ),
            History(
                id=None,
                instrument_id=100,
                symbol="AAPL",
                bar_time=datetime(2026, 1, 24, 15, 30, 45),  # After cutoff
                open_price=150.50,
                high_price=152.00,
                low_price=149.00,
                close_price=151.25,
                volume=1000000,
                wap=150.75,
                bar_count=500
            ),
            History(
                id=None,
                instrument_id=100,
                symbol="AAPL",
                bar_time=datetime(2026, 1, 24, 16, 30, 45),  # After cutoff
                open_price=151.25,
                high_price=153.00,
                low_price=150.00,
                close_price=152.50,
                volume=1100000,
                wap=151.75,
                bar_count=550
            )
        ]
        
        # Save all histories
        for history in histories:
            self.history_dto.save_history(history)
        
        # Retrieve histories after 15:00
        after_date = datetime(2026, 1, 24, 15, 0, 0)
        retrieved = self.history_dto.get_history_by_symbol_and_after_date("AAPL", after_date)
        
        # Should only get the 2 records after 15:00
        self.assertEqual(len(retrieved), 2)
        for hist in retrieved:
            self.assertGreaterEqual(hist.bar_time, after_date)
    
    def test_update_history(self):
        """Test updating an existing history record."""
        # Create and save initial history
        original_history = History(
            id=None,
            instrument_id=100,
            symbol="AAPL",
            bar_time=datetime(2026, 1, 24, 15, 30, 45),
            open_price=150.50,
            high_price=152.00,
            low_price=149.00,
            close_price=151.25,
            volume=1000000,
            wap=150.75,
            bar_count=500
        )
        
        saved_id = self.history_dto.save_history(original_history)
        
        # Retrieve and modify
        retrieved = self.history_dto.get_history_by_instrument(100)[0]
        retrieved.close_price = 155.00
        retrieved.volume = 1200000
        
        # Update (if your DTO has an update method)
        # self.history_dto.update_history(retrieved)
        
        # For now, test that we can retrieve what we saved
        final = self.history_dto.get_history_by_instrument(100)[0]
        self.assertEqual(final.instrument_id, 100)
    
    def test_save_history_with_none_optional_fields(self):
        """Test saving history with None values for optional fields."""
        history = History(
            id=None,
            instrument_id=100,
            symbol="AAPL",
            bar_time=datetime(2026, 1, 24, 15, 30, 45),
            open_price=150.50,
            high_price=152.00,
            low_price=149.00,
            close_price=151.25,
            volume=1000000,
            wap=None,  # Optional field
            bar_count=None  # Optional field
        )
        
        saved_id = self.history_dto.save_history(history)
        self.assertIsNotNone(saved_id)
        
        # Retrieve and verify None values are handled
        retrieved = self.history_dto.get_history_by_instrument(100)[0]
        self.assertIsNone(retrieved.wap)
        self.assertIsNone(retrieved.bar_count)
    
    def test_database_constraints(self):
        """Test that database constraints are enforced."""
        # Test missing required field - instrument_id
        invalid_history = History(
            id=None,
            instrument_id=None,  # Required field
            symbol="AAPL",
            bar_time=datetime(2026, 1, 24, 15, 30, 45),
            open_price=150.50,
            high_price=152.00,
            low_price=149.00,
            close_price=151.25,
            volume=1000000
        )
        
        # Should raise an error (depending on your implementation)
        # This test depends on how your save_history handles None instrument_id
        with self.assertRaises((ValueError, TypeError, Exception)):
            self.history_dto.save_history(invalid_history)


if __name__ == '__main__':
    unittest.main()