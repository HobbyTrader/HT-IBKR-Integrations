import sqlite3
import unittest
from decimal import Decimal
from unittest.mock import Mock, patch

from app.data.execution_order import ExecutionOrder
from app.dto.execution_order_dto import ExecutionOrderDTO
from app.services.execution import ExecutionService


class TestExecutionServiceCallbacksIntegration(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self._create_tables()

        mock_db_manager = Mock()
        mock_db_manager.conn = self.conn

        self.sqlite_patcher = patch(
            "app.dto.execution_order_dto.SQLiteManager",
            return_value=mock_db_manager,
        )
        self.sqlite_patcher.start()

        self.service = ExecutionService()
        self.dto = self.service.execution_order_dto

    def tearDown(self):
        if hasattr(self, "sqlite_patcher"):
            self.sqlite_patcher.stop()
        if hasattr(self, "conn"):
            self.conn.close()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exec_id TEXT NOT NULL,
                order_id INTEGER NOT NULL,
                contract_symbol TEXT NOT NULL DEFAULT '',
                side TEXT NOT NULL,
                shares REAL NOT NULL,
                price REAL NOT NULL,
                execution_time TEXT NOT NULL,
                create_date TEXT NOT NULL DEFAULT (datetime('now')),
                update_date TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self.conn.commit()

    def test_exec_details_updates_existing_row_by_order_id(self):
        existing = ExecutionOrder(
            exec_id="INIT-1",
            order_id=9001,
            contract_symbol="AAPL",
            side="BUY",
            shares=1,
            price=10,
            execution_time="20260101-00:00:00",
        )
        self.dto.save_execution_order(existing)

        execution = Mock()
        execution.execId = "IB-9001"
        execution.orderId = 9001
        execution.side = "BUY"
        execution.cumQty = 15
        execution.avgPrice = 123.45
        execution.time = "20260525-10:12:30"
        contract = Mock()
        contract.symbol = "AAPL"

        self.service.execDetails(1, contract, execution)

        rows = self.dto.get_execution_orders_by_order_id(9001)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].shares, 15)
        self.assertEqual(rows[0].price, 123.45)
        self.assertEqual(rows[0].execution_time.strftime("%Y%m%d-%H:%M:%S"), "20260525-10:12:30")

    def test_exec_details_inserts_when_order_id_not_found(self):
        execution = Mock()
        execution.execId = "IB-9002"
        execution.orderId = 9002
        execution.side = "SELL"
        execution.cumQty = 7
        execution.avgPrice = 99.5
        execution.time = "20260525-11:00:00"
        contract = Mock()
        contract.symbol = "MSFT"

        self.service.execDetails(2, contract, execution)

        rows = self.dto.get_execution_orders_by_order_id(9002)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].shares, 7)
        self.assertEqual(rows[0].price, 99.5)
        self.assertEqual(rows[0].execution_time.strftime("%Y%m%d-%H:%M:%S"), "20260525-11:00:00")

    def test_exec_details_accepts_decimal_values(self):
        execution = Mock()
        execution.execId = "IB-9003"
        execution.orderId = 9003
        execution.side = "BUY"
        execution.cumQty = Decimal("12")
        execution.avgPrice = Decimal("45.67")
        execution.time = "20260526-09:30:00"
        contract = Mock()
        contract.symbol = "NVDA"

        self.service.execDetails(3, contract, execution)

        rows = self.dto.get_execution_orders_by_order_id(9003)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].shares, 12)
        self.assertEqual(rows[0].price, 45.67)
        self.assertEqual(rows[0].execution_time.strftime("%Y%m%d-%H:%M:%S"), "20260526-09:30:00")

    def test_exec_details_uses_symbol_with_order_id_as_update_key(self):
        self.dto.save_execution_order(
            ExecutionOrder(
                exec_id="INIT-AAPL",
                order_id=777,
                contract_symbol="AAPL",
                side="BUY",
                shares=1,
                price=10,
                execution_time="20260101-00:00:00",
            )
        )
        self.dto.save_execution_order(
            ExecutionOrder(
                exec_id="INIT-MSFT",
                order_id=777,
                contract_symbol="MSFT",
                side="BUY",
                shares=2,
                price=20,
                execution_time="20260101-00:00:00",
            )
        )

        execution = Mock()
        execution.execId = "IB-777"
        execution.orderId = 777
        execution.side = "BUY"
        execution.cumQty = 50
        execution.avgPrice = 123.4
        execution.time = "20260526-12:00:00"

        contract = Mock()
        contract.symbol = "AAPL"

        self.service.execDetails(10, contract, execution)

        rows = self.dto.get_execution_orders_by_order_id(777)
        by_symbol = {row.contract_symbol: row for row in rows}

        self.assertEqual(by_symbol["AAPL"].shares, 50)
        self.assertEqual(by_symbol["AAPL"].price, 123.4)
        self.assertEqual(by_symbol["MSFT"].shares, 2)
        self.assertEqual(by_symbol["MSFT"].price, 20)


if __name__ == "__main__":
    unittest.main()