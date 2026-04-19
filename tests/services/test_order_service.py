import sqlite3
import unittest
from unittest.mock import Mock, patch

from app.data.market_order import MarketOrder
from app.dto.market_order_dto import MarketOrderDTO
from app.services.order import OrderService


class _InstantThread:
    def __init__(self, target=None, args=(), kwargs=None):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}

    def start(self):
        if self._target:
            self._target(*self._args, **self._kwargs)


class TestOrderServiceCallbacksIntegration(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self._create_tables()

        mock_db_manager = Mock()
        mock_db_manager.conn = self.conn

        self.sqlite_patcher = patch(
            "app.dto.market_order_dto.SQLiteManager",
            return_value=mock_db_manager,
        )
        self.sqlite_patcher.start()

        self.thread_patcher = patch("app.services.order.threading.Thread", _InstantThread)
        self.thread_patcher.start()

        self.service = OrderService()
        self.dto = self.service.order_dto

    def tearDown(self):
        if hasattr(self, "thread_patcher"):
            self.thread_patcher.stop()
        if hasattr(self, "sqlite_patcher"):
            self.sqlite_patcher.stop()
        if hasattr(self, "conn"):
            self.conn.close()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                strategy_tags TEXT,
                strategy_details TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                create_date TEXT NOT NULL DEFAULT (datetime('now')),
                update_date TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                strategy_id INTEGER NOT NULL,
                order_contract_id INTEGER NOT NULL,
                order_symbol TEXT NOT NULL,
                order_status TEXT NOT NULL,
                order_quantity INTEGER NOT NULL DEFAULT 0,
                order_currency TEXT NOT NULL,
                order_price REAL,
                order_type TEXT NOT NULL,
                order_action TEXT NOT NULL,
                order_parent_id INTEGER DEFAULT 0,
                create_date TEXT NOT NULL DEFAULT (datetime('now')),
                update_date TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO strategies (strategy_id, strategy_name, strategy_details)
            VALUES (1, 'Test Strategy', 'Test strategy details')
            """
        )
        self.conn.commit()

    def _insert_order(self, order_id: int, status: str = "PendingSubmit"):
        order = MarketOrder(
            order_id=order_id,
            strategy_id=1,
            order_contract_id=101,
            order_symbol="AAPL",
            order_status=status,
            order_quantity=10,
            order_currency="USD",
            order_price=100.0,
            order_type="MKT",
            order_action="BUY",
            order_parent_id=0,
        )
        self.dto.save_market_order(order)

    def test_open_order_callback_updates_status_in_db(self):
        self._insert_order(order_id=1001, status="PendingSubmit")

        order_state = Mock()
        order_state.status = "Submitted"

        self.service.openOrder(1001, None, None, order_state)

        updated = self.dto.get_market_order_by_id(1001)
        self.assertEqual(updated.order_status, "Submitted")

    def test_order_status_callback_updates_status_in_db(self):
        self._insert_order(order_id=1002, status="Submitted")

        self.service.orderStatus(
            1002,
            "Filled",
            10,
            0,
            101.0,
            1,
            0,
            101.0,
            0,
            "",
            0.0,
        )

        updated = self.dto.get_market_order_by_id(1002)
        self.assertEqual(updated.order_status, "Filled")

    def test_completed_order_callback_updates_status_in_db(self):
        self._insert_order(order_id=1003, status="Submitted")

        order = Mock()
        order.orderId = 1003
        order_state = Mock()
        order_state.status = "Filled"

        self.service.completedOrder(None, order, order_state)

        updated = self.dto.get_market_order_by_id(1003)
        self.assertEqual(updated.order_status, "Filled")

    def test_rejected_status_is_not_overwritten_by_later_status(self):
        self._insert_order(order_id=1004, status="Rejected")

        self.service.orderStatus(
            1004,
            "Filled",
            10,
            0,
            101.0,
            1,
            0,
            101.0,
            0,
            "",
            0.0,
        )

        updated = self.dto.get_market_order_by_id(1004)
        self.assertEqual(updated.order_status, "Rejected")


if __name__ == "__main__":
    unittest.main()
