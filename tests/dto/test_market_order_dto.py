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
        self.mock_cursor.fetchone.return_value = ("row",)
        out = self.dto.get_market_order_by_id(5)
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE order_id = ?", (5,)
        )
        self.assertEqual(out, ("row",))

    def test_get_all_market_orders(self):
        self.mock_cursor.fetchall.return_value = [("r1",), ("r2",)]
        out = self.dto.get_all_market_orders()
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM market_orders")
        self.assertEqual(out, [("r1",), ("r2",)])

    def test_get_market_orders_by_strategy(self):
        self.mock_cursor.fetchall.return_value = [("r1",)]
        out = self.dto.get_market_orders_by_strategy(7)
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE strategy_id = ?", (7,)
        )
        self.assertEqual(out, [("r1",)])

    def test_get_market_orders_by_status(self):
        self.mock_cursor.fetchall.return_value = [("r1",)]
        out = self.dto.get_market_orders_by_status("NEW")
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE order_status = ?", ("NEW",)
        )
        self.assertEqual(out, [("r1",)])

    def test_get_market_orders_by_create_date(self):
        self.mock_cursor.fetchall.return_value = [("r1",)]
        out = self.dto.get_market_orders_by_create_date("2025-01-01")
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM market_orders WHERE create_date >= ?", ("2025-01-01",)
        )
        self.assertEqual(out, [("r1",)])

    # ------------------------------------------------------------------ update

    def test_update_market_order_status(self):
        self.dto.update_market_order_status(9, "FILLED")
        self.mock_cursor.execute.assert_called_once_with(
            "UPDATE market_orders SET order_status = ?, update_date = CURRENT_TIMESTAMP WHERE order_id = ?",
            ("FILLED", 9),
        )
        self.mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()