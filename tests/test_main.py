import unittest
import sqlite3
from unittest.mock import Mock, patch

from app.main import (
    TERMINAL_RETRYABLE_BUY_STATUSES,
    count_buy_orders_today_for_strategy,
    has_buy_order_today,
)
from app.data.instrument import Instrument
from app.data.strategy import Strategy
from app.dto.market_order_dto import MarketOrderDTO


class TestMainOrderDuplicationGuard(unittest.TestCase):
    def setUp(self):
        self.instrument = Instrument(
            id=12345,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        self.strategy = Strategy(name="US", id=7)

    def _build_order(self, order_action: str, order_status: str, order_id: int = 1):
        order = Mock()
        order.order_action = order_action
        order.order_status = order_status
        order.order_id = order_id
        return order

    def test_has_buy_order_today_true_for_non_retryable_buy_status(self):
        dto = Mock()
        dto.get_market_orders_by_contract_id_today.return_value = [
            self._build_order("BUY", "Filled", 10)
        ]

        self.assertTrue(has_buy_order_today(self.instrument, dto))

    def test_has_buy_order_today_false_for_retryable_buy_statuses(self):
        for status in TERMINAL_RETRYABLE_BUY_STATUSES:
            with self.subTest(status=status):
                dto = Mock()
                dto.get_market_orders_by_contract_id_today.return_value = [
                    self._build_order("BUY", status, 20)
                ]
                self.assertFalse(has_buy_order_today(self.instrument, dto))

    def test_has_buy_order_today_false_for_sell_only_orders(self):
        dto = Mock()
        dto.get_market_orders_by_contract_id_today.return_value = [
            self._build_order("SELL", "Filled", 30),
            self._build_order("SELL", "Submitted", 31),
        ]

        self.assertFalse(has_buy_order_today(self.instrument, dto))

    def test_has_buy_order_today_false_for_no_orders(self):
        dto = Mock()
        dto.get_market_orders_by_contract_id_today.return_value = []

        self.assertFalse(has_buy_order_today(self.instrument, dto))

    def test_count_buy_orders_today_for_strategy_counts_non_retryable_buys_only(self):
        dto = Mock()
        dto.get_market_orders_by_strategy_today.return_value = [
            self._build_order("BUY", "Filled", 1),
            self._build_order("BUY", "Submitted", 2),
            self._build_order("BUY", "Rejected", 3),
            self._build_order("SELL", "Filled", 4),
        ]

        self.assertEqual(count_buy_orders_today_for_strategy(self.strategy, dto), 2)


if __name__ == "__main__":
    unittest.main()


class TestMainOrderDuplicationGuardIntegration(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self._create_tables()

        mock_db_manager = Mock()
        mock_db_manager.conn = self.conn
        self.db_patcher = patch(
            "app.dto.market_order_dto.SQLiteManager",
            return_value=mock_db_manager,
        )
        self.db_patcher.start()

        self.market_order_dto = MarketOrderDTO()
        self.instrument = Instrument(
            id=9001,
            symbol="AAPL",
            sectype="STK",
            currency="USD",
            exchange="SMART",
        )
        self.strategy = Strategy(name="US", id=1)

    def tearDown(self):
        if hasattr(self, "db_patcher"):
            self.db_patcher.stop()
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

    def _insert_market_order(
        self,
        order_id: int,
        order_contract_id: int,
        order_action: str,
        order_status: str,
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO market_orders (
                order_id,
                strategy_id,
                order_contract_id,
                order_symbol,
                order_status,
                order_quantity,
                order_currency,
                order_price,
                order_type,
                order_action,
                order_parent_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                1,
                order_contract_id,
                "AAPL",
                order_status,
                10,
                "USD",
                100.0,
                "MKT",
                order_action,
                0,
            ),
        )
        self.conn.commit()

    def test_has_buy_order_today_reads_market_orders_table(self):
        self._insert_market_order(
            order_id=50001,
            order_contract_id=self.instrument.id,
            order_action="BUY",
            order_status="Filled",
        )

        self.assertTrue(has_buy_order_today(self.instrument, self.market_order_dto))

    def test_has_buy_order_today_ignores_retryable_buy_status(self):
        self._insert_market_order(
            order_id=50002,
            order_contract_id=self.instrument.id,
            order_action="BUY",
            order_status="Rejected",
        )

        self.assertFalse(has_buy_order_today(self.instrument, self.market_order_dto))

    def test_has_buy_order_today_ignores_other_contract_orders(self):
        self._insert_market_order(
            order_id=50003,
            order_contract_id=99999,
            order_action="BUY",
            order_status="Filled",
        )

        self.assertFalse(has_buy_order_today(self.instrument, self.market_order_dto))

    def test_count_buy_orders_today_for_strategy_reads_market_orders_table(self):
        self._insert_market_order(
            order_id=60001,
            order_contract_id=self.instrument.id,
            order_action="BUY",
            order_status="Filled",
        )
        self._insert_market_order(
            order_id=60002,
            order_contract_id=self.instrument.id,
            order_action="BUY",
            order_status="Submitted",
        )
        self._insert_market_order(
            order_id=60003,
            order_contract_id=self.instrument.id,
            order_action="BUY",
            order_status="Rejected",
        )
        self._insert_market_order(
            order_id=60004,
            order_contract_id=self.instrument.id,
            order_action="SELL",
            order_status="Filled",
        )

        self.assertEqual(
            count_buy_orders_today_for_strategy(self.strategy, self.market_order_dto),
            2,
        )
