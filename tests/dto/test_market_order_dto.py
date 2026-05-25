import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
import sqlite3

from app.dto.market_order_dto import MarketOrderDTO
from app.data.market_order import MarketOrder
from app.utils.date_helper import _parse_datetime


class TestDateHelperParseDatetime(unittest.TestCase):
    def test_parse_datetime_supported_formats(self):
        cases = [
            ("2025-01-04", datetime(2025, 1, 4, 0, 0, 0)),
            ("2025-01-04 15:30:45", datetime(2025, 1, 4, 15, 30, 45)),
            ("2025-01-04 15:30:45.123456", datetime(2025, 1, 4, 15, 30, 45, 123456)),
            ("20250104", datetime(2025, 1, 4, 0, 0, 0)),
            ("20250104 15:30:45", datetime(2025, 1, 4, 15, 30, 45)),
            ("20250104-15:30:45", datetime(2025, 1, 4, 15, 30, 45)),
            ("20260521 09:56:30 US/Eastern", datetime(2026, 5, 21, 9, 56, 30)),
        ]

        for raw_value, expected in cases:
            with self.subTest(raw_value=raw_value):
                parsed = _parse_datetime(raw_value)
                self.assertEqual(parsed, expected)

    def test_parse_datetime_returns_datetime_instance_for_none(self):
        parsed = _parse_datetime(None)
        self.assertIsInstance(parsed, datetime)


class TestMarketOrderDTO(unittest.TestCase):
    def setUp(self):
        # Patch SQLiteManager inside the module
        self.sqlite_patcher = patch("app.dto.market_order_dto.SQLiteManager")
        self.mock_sqlite_cls = self.sqlite_patcher.start()
        self.addCleanup(self.sqlite_patcher.stop)

        # Mock SQLiteManager instance and its connection/cursor
        self.mock_sqlite = self.mock_sqlite_cls.return_value
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_sqlite.conn = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        self.dto = MarketOrderDTO()

    # ------------------------------------------------------------------ save_market_order

    def test_save_market_order_inserts_and_commits(self):
        mo = Mock()
        mo.order_id = 1
        mo.strategy_id = 2
        mo.order_contract_id = 3
        mo.order_symbol = "AAPL"
        mo.order_status = "NEW"
        mo.order_quantity = 10
        mo.order_currency = "USD"
        mo.order_price = 123.45
        mo.order_type = "MKT"
        mo.order_action = "BUY"
        mo.order_parent_id = None

        self.dto.save_market_order(mo)

        self.mock_cursor.execute.assert_called_once()
        sql, params = self.mock_cursor.execute.call_args[0]
        self.assertIn("INSERT INTO market_orders", sql)
        # Expect 10 values matching the 10 columns
        self.assertEqual(
            params,
            (
                1, 2, 3, "AAPL", "NEW", 10, "USD",
                123.45, "MKT", "BUY", None
            ),
        )
        self.mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------ getters

    def test_get_market_order_by_id(self):
        """Test get_market_order_by_id returns single transformed order."""
        row = ("r1",)
        self.mock_cursor.fetchone.return_value = row  # fetchone, not fetchall
        
        mock_order = Mock()
        with patch.object(self.dto, 'row_to_market_order', return_value=mock_order) as mock_transform:
            out = self.dto.get_market_order_by_id(5)
        
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE order_id = ?", (5,)
        )
        mock_transform.assert_called_once_with(row)
        self.assertEqual(out, mock_order)  # Returns single object, not list

    def test_get_all_market_orders(self):
        """Test with mocked row_to_market_order transformation."""
        rows = [("r1",), ("r2",)]
        self.mock_cursor.fetchall.return_value = rows
        
        mock_order1 = Mock()
        mock_order2 = Mock()
        with patch.object(self.dto, 'row_to_market_order', side_effect=[mock_order1, mock_order2]) as mock_transform:
            out = self.dto.get_all_market_orders()
        
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders"
        )
        self.assertEqual(mock_transform.call_count, 2)
        mock_transform.assert_any_call(("r1",))
        mock_transform.assert_any_call(("r2",))
        self.assertEqual(out, [mock_order1, mock_order2])

    def test_get_market_orders_by_strategy(self):
        """Test with mocked row_to_market_order transformation."""
        rows = [("r1",), ("r2",)]
        self.mock_cursor.fetchall.return_value = rows
        
        mock_order1 = Mock()
        mock_order2 = Mock()
        with patch.object(self.dto, 'row_to_market_order', side_effect=[mock_order1, mock_order2]) as mock_transform:
            out = self.dto.get_market_orders_by_strategy(7)
        
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE strategy_id = ?", (7,)
        )
        self.assertEqual(mock_transform.call_count, 2)
        mock_transform.assert_any_call(("r1",))
        mock_transform.assert_any_call(("r2",))
        self.assertEqual(out, [mock_order1, mock_order2])
        
    def test_get_market_orders_by_strategy_today(self):
        """Test with mocked row_to_market_order transformation."""
        rows = [("r1",), ("r2",)]
        self.mock_cursor.fetchall.return_value = rows
        
        # Mock the row_to_market_order method on the instance
        mock_order1 = Mock()
        mock_order2 = Mock()
        with patch.object(self.dto, 'row_to_market_order', side_effect=[mock_order1, mock_order2]) as mock_transform:
            out = self.dto.get_market_orders_by_strategy_today(7)
        
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE strategy_id = ? AND DATE(create_date) = DATE('now')", (7,)
        )
        # Verify transformation was called for each row
        self.assertEqual(mock_transform.call_count, 2)
        mock_transform.assert_any_call(("r1",))
        mock_transform.assert_any_call(("r2",))
        # Verify result
        self.assertEqual(out, [mock_order1, mock_order2])

    def test_get_market_orders_by_status(self):
        """Test with mocked row_to_market_order transformation."""
        rows = [("r1",)]
        self.mock_cursor.fetchall.return_value = rows
        
        mock_order1 = Mock()
        with patch.object(self.dto, 'row_to_market_order', side_effect=[mock_order1]) as mock_transform:
            out = self.dto.get_market_orders_by_status("NEW")
        
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE order_status = ?", ("NEW",)
        )
        self.assertEqual(mock_transform.call_count, 1)
        mock_transform.assert_any_call(("r1",))
        self.assertEqual(out, [mock_order1])

    def test_get_market_orders_by_create_date(self):
        """Test with mocked row_to_market_order transformation."""
        rows = [("r1",)]
        self.mock_cursor.fetchall.return_value = rows
        
        mock_order1 = Mock()
        with patch.object(self.dto, 'row_to_market_order', side_effect=[mock_order1]) as mock_transform:
            out = self.dto.get_market_orders_by_create_date("2025-01-01")
        
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE create_date >= ?", ("2025-01-01",)
        )
        self.assertEqual(mock_transform.call_count, 1)
        mock_transform.assert_any_call(("r1",))
        self.assertEqual(out, [mock_order1])

    # ------------------------------------------------------------------ update

    def test_update_market_order_status(self):
        self.dto.update_market_order_status(9, "FILLED")
        self.mock_cursor.execute.assert_called_once_with(
            "UPDATE market_orders SET order_status = ?, update_date = CURRENT_TIMESTAMP WHERE order_id = ? AND LOWER(order_status) != 'rejected'",
            ("FILLED", 9),
        )
        self.mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------ row_to_market_order

    @patch("app.dto.market_order_dto.MarketOrder")
    def test_row_to_market_order(self, mock_market_order_cls):
        # Complete row with all 13 columns (based on table schema)
        row = (
            1,              # id
            100,            # order_id
            5,              # strategy_id
            3,              # order_contract_id
            "AAPL",         # order_symbol
            "FILLED",       # order_status
            10,             # order_quantity
            "USD",          # order_currency
            150.50,         # order_price
            "MKT",          # order_type
            "BUY",          # order_action
            None,           # order_parent_id
            _parse_datetime("2025-01-04"),   # create_date
            _parse_datetime("2025-01-04")    # update_date
        )
        
        mock_order = Mock()
        mock_market_order_cls.return_value = mock_order
        
        result = self.dto.row_to_market_order(row)
        
        mock_market_order_cls.assert_called_once_with(
            id=1,
            order_id=100,
            strategy_id=5,
            order_contract_id=3,
            order_symbol="AAPL",
            order_status="FILLED",
            order_quantity=10,
            order_currency="USD",
            order_price=150.50,
            order_type="MKT",
            order_action="BUY",
            order_parent_id=None,
            create_date=_parse_datetime("2025-01-04"),
            update_date=_parse_datetime("2025-01-04")
        )
        self.assertEqual(result, mock_order)


class TestMarketOrderDTOIntegration(unittest.TestCase):
    """Integration tests with actual in-memory database."""
    
    def setUp(self):
        """Set up each test with a fresh in-memory database."""
        # Create in-memory database directly
        self.conn = sqlite3.connect(':memory:')
        
        # Create tables directly
        self._create_tables()
        
        # Mock SQLiteManager to use our connection
        mock_db_manager = Mock()
        mock_db_manager.conn = self.conn
        
        # Patch SQLiteManager
        self.db_patcher = patch(
            'app.dto.market_order_dto.SQLiteManager',
            return_value=mock_db_manager
        )
        self.db_patcher.start()
        
        # Create MarketOrderDTO instance
        self.market_order_dto = MarketOrderDTO()
    
    def _create_tables(self):
        """Create necessary database tables."""
        cursor = self.conn.cursor()
        
        # Create strategies table (required for foreign key)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                strategy_tags TEXT,
                strategy_details TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                create_date TEXT NOT NULL DEFAULT (datetime('now')),
                update_date TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        
        # Create market_orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL UNIQUE,
                strategy_id INTEGER NOT NULL,
                order_contract_id INTEGER NOT NULL,
                order_symbol TEXT NOT NULL,
                order_status TEXT NOT NULL,
                order_quantity INTEGER NOT NULL,
                order_currency TEXT NOT NULL,
                order_price REAL NOT NULL,
                order_type TEXT NOT NULL,
                order_action TEXT NOT NULL,
                order_parent_id INTEGER,
                create_date TEXT NOT NULL DEFAULT (datetime('now')),
                update_date TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
            )
        """)
        
        # Insert a test strategy for foreign key constraint
        cursor.execute("""
            INSERT INTO strategies (strategy_id, strategy_name, strategy_details)
            VALUES (1, 'Test Strategy', 'Test strategy details')
        """)
        
        self.conn.commit()
    
    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'conn'):
            self.conn.close()
        
        if hasattr(self, 'db_patcher'):
            self.db_patcher.stop()
    
    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================
    
    def test_save_and_retrieve_market_order(self):
        """Test full cycle of saving and retrieving a market order."""
        # Create a market order
        test_order = MarketOrder(
            id=None,
            order_id=1001,
            strategy_id=1,
            order_contract_id=3,
            order_symbol="AAPL",
            order_status="PreSubmitted",
            order_quantity=100,
            order_currency="USD",
            order_price=150.50,
            order_type="MKT",
            order_action="BUY",
            order_parent_id=None
        )
        
        # Save the order
        saved_id = self.market_order_dto.save_market_order(test_order)
        self.assertIsNotNone(saved_id)
        self.assertGreater(saved_id, 0)
        
        # Retrieve by order_id
        retrieved = self.market_order_dto.get_market_order_by_id(1001)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.order_id, test_order.order_id)
        self.assertEqual(retrieved.strategy_id, test_order.strategy_id)
        self.assertEqual(retrieved.order_contract_id, test_order.order_contract_id)
        self.assertEqual(retrieved.order_symbol, test_order.order_symbol)
        self.assertEqual(retrieved.order_status, test_order.order_status)
        self.assertEqual(retrieved.order_quantity, test_order.order_quantity)
        self.assertEqual(retrieved.order_currency, test_order.order_currency)
        self.assertEqual(retrieved.order_price, test_order.order_price)
        self.assertEqual(retrieved.order_type, test_order.order_type)
        self.assertEqual(retrieved.order_action, test_order.order_action)
    
    def test_save_multiple_orders_and_retrieve_all(self):
        """Test saving multiple orders and retrieving all."""
        orders = [
            MarketOrder(
                id=None,
                order_id=2001,
                strategy_id=1,
                order_contract_id=3,
                order_symbol="AAPL",
                order_status="PreSubmitted",
                order_quantity=100,
                order_currency="USD",
                order_price=150.50,
                order_type="MKT",
                order_action="BUY",
                order_parent_id=None
            ),
            MarketOrder(
                id=None,
                order_id=2002,
                strategy_id=1,
                order_contract_id=4,
                order_symbol="MSFT",
                order_status="Submitted",
                order_quantity=50,
                order_currency="USD",
                order_price=380.25,
                order_type="LMT",
                order_action="SELL",
                order_parent_id=None
            )
        ]
        
        # Save all orders
        for order in orders:
            saved_id = self.market_order_dto.save_market_order(order)
            self.assertIsNotNone(saved_id)
        
        # Retrieve all orders
        all_orders = self.market_order_dto.get_all_market_orders()
        self.assertEqual(len(all_orders), 2)
        self.assertEqual(all_orders[0].order_id, 2001)
        self.assertEqual(all_orders[1].order_id, 2002)
    
    def test_get_orders_by_strategy(self):
        """Test retrieving orders for a specific strategy."""
        # Create orders for different strategies
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO strategies (strategy_id, strategy_name, strategy_details)
            VALUES (2, 'Strategy 2', 'Second test strategy')
        """)
        self.conn.commit()
        
        orders = [
            MarketOrder(
                id=None, order_id=3001, strategy_id=1,
                order_contract_id=3, order_symbol="AAPL", order_status="NEW",
                order_quantity=100, order_currency="USD",
                order_price=150.00, order_type="MKT",
                order_action="BUY", order_parent_id=None
            ),
            MarketOrder(
                id=None, order_id=3002, strategy_id=1,
                order_contract_id=3, order_symbol="AAPL", order_status="NEW",
                order_quantity=200, order_currency="USD",
                order_price=151.00, order_type="MKT",
                order_action="BUY", order_parent_id=None
            ),
            MarketOrder(
                id=None, order_id=3003, strategy_id=2,
                order_contract_id=3, order_symbol="AAPL", order_status="NEW",
                order_quantity=300, order_currency="USD",
                order_price=152.00, order_type="MKT",
                order_action="BUY", order_parent_id=None
            )
        ]
        
        for order in orders:
            self.market_order_dto.save_market_order(order)
        
        # Get orders for strategy 1
        strategy_1_orders = self.market_order_dto.get_market_orders_by_strategy(1)
        self.assertEqual(len(strategy_1_orders), 2)
        for order in strategy_1_orders:
            self.assertEqual(order.strategy_id, 1)
        
        # Get orders for strategy 2
        strategy_2_orders = self.market_order_dto.get_market_orders_by_strategy(2)
        self.assertEqual(len(strategy_2_orders), 1)
        self.assertEqual(strategy_2_orders[0].strategy_id, 2)
    
    def test_get_orders_by_status(self):
        """Test retrieving orders by status."""
        orders = [
            MarketOrder(
                id=None, order_id=4001, strategy_id=1,
                order_contract_id=3, order_symbol="AAPL", order_status="PreSubmitted",
                order_quantity=100, order_currency="USD",
                order_price=150.00, order_type="MKT",
                order_action="BUY", order_parent_id=None
            ),
            MarketOrder(
                id=None, order_id=4002, strategy_id=1,
                order_contract_id=3, order_symbol="AAPL", order_status="Filled",
                order_quantity=200, order_currency="USD",
                order_price=151.00, order_type="MKT",
                order_action="BUY", order_parent_id=None
            ),
            MarketOrder(
                id=None, order_id=4003, strategy_id=1,
                order_contract_id=3, order_symbol="AAPL", order_status="Filled",
                order_quantity=300, order_currency="USD",
                order_price=152.00, order_type="MKT",
                order_action="BUY", order_parent_id=None
            )
        ]
        
        for order in orders:
            self.market_order_dto.save_market_order(order)
        
        # Get filled orders
        filled_orders = self.market_order_dto.get_market_orders_by_status("Filled")
        self.assertEqual(len(filled_orders), 2)
        for order in filled_orders:
            self.assertEqual(order.order_status, "Filled")
        
        # Get presubmitted orders
        presubmitted_orders = self.market_order_dto.get_market_orders_by_status("PreSubmitted")
        self.assertEqual(len(presubmitted_orders), 1)
        self.assertEqual(presubmitted_orders[0].order_status, "PreSubmitted")
    
    def test_update_order_status(self):
        """Test updating order status."""
        # Create and save an order
        order = MarketOrder(
            id=None, order_id=5001, strategy_id=1,
            order_contract_id=3, order_symbol="AAPL", order_status="PreSubmitted",
            order_quantity=100, order_currency="USD",
            order_price=150.00, order_type="MKT",
            order_action="BUY", order_parent_id=None
        )
        
        self.market_order_dto.save_market_order(order)
        
        # Verify initial status
        retrieved = self.market_order_dto.get_market_order_by_id(5001)
        self.assertEqual(retrieved.order_status, "PreSubmitted")
        
        # Update status
        self.market_order_dto.update_market_order_status(5001, "Filled")
        
        # Verify updated status
        updated = self.market_order_dto.get_market_order_by_id(5001)
        self.assertEqual(updated.order_status, "Filled")
    
    def test_get_orders_by_create_date(self):
        """Test retrieving orders created after a specific date."""
        # Create orders
        orders = [
            MarketOrder(
                id=None, order_id=6001, strategy_id=1,
                order_contract_id=3, order_symbol="AAPL", order_status="NEW",
                order_quantity=100, order_currency="USD",
                order_price=150.00, order_type="MKT",
                order_action="BUY", order_parent_id=None
            )
        ]
        
        for order in orders:
            self.market_order_dto.save_market_order(order)
        
        # Get orders created today (should find the order)
        today = datetime.now().strftime('%Y-%m-%d')
        retrieved = self.market_order_dto.get_market_orders_by_create_date(today)
        self.assertGreater(len(retrieved), 0)
        
        # Get orders created in the future (should find none)
        future = "2030-01-01"
        retrieved = self.market_order_dto.get_market_orders_by_create_date(future)
        self.assertEqual(len(retrieved), 0)
    
    def test_order_with_parent_id(self):
        """Test saving and retrieving orders with parent-child relationship."""
        # Create parent order
        parent_order = MarketOrder(
            id=None, order_id=7001, strategy_id=1,
            order_contract_id=3, order_symbol="AAPL", order_status="Filled",
            order_quantity=100, order_currency="USD",
            order_price=150.00, order_type="MKT",
            order_action="BUY", order_parent_id=None
        )
        
        self.market_order_dto.save_market_order(parent_order)
        
        # Create child order
        child_order = MarketOrder(
            id=None, order_id=7002, strategy_id=1,
            order_contract_id=3, order_symbol="AAPL", order_status="PreSubmitted",
            order_quantity=100, order_currency="USD",
            order_price=155.00, order_type="LMT",
            order_action="SELL", order_parent_id=7001
        )
        
        self.market_order_dto.save_market_order(child_order)
        
        # Retrieve and verify relationship
        retrieved_child = self.market_order_dto.get_market_order_by_id(7002)
        self.assertEqual(retrieved_child.order_parent_id, 7001)


if __name__ == "__main__":
    unittest.main()