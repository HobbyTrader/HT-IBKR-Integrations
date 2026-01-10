import unittest
from unittest.mock import patch, MagicMock, Mock

from app.dto.market_order_dto import MarketOrderDTO


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
        mo.order_details = "details"
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
                1, 2, "details", "NEW", 10, "USD",
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
            "UPDATE market_orders SET order_status = ?, update_date = CURRENT_TIMESTAMP WHERE order_id = ?",
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
            "details",      # order_details
            "FILLED",       # order_status
            10,             # order_quantity
            "USD",          # order_currency
            150.50,         # order_price
            "MKT",          # order_type
            "BUY",          # order_action
            None,           # order_parent_id
            "2025-01-04",   # create_date
            "2025-01-04"    # update_date
        )
        
        mock_order = Mock()
        mock_market_order_cls.return_value = mock_order
        
        result = self.dto.row_to_market_order(row)
        
        mock_market_order_cls.assert_called_once_with(
            id=1,
            order_id=100,
            strategy_id=5,
            order_details="details",
            order_status="FILLED",
            order_quantity=10,
            order_currency="USD",
            order_price=150.50,
            order_type="MKT",
            order_action="BUY",
            order_parent_id=None,
            create_date="2025-01-04",
            update_date="2025-01-04"
        )
        self.assertEqual(result, mock_order)

if __name__ == "__main__":
    unittest.main()