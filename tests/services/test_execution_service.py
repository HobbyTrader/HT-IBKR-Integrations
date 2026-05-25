import sqlite3
import unittest
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

        self.service.execDetails(1, Mock(), execution)

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

        self.service.execDetails(2, Mock(), execution)

        rows = self.dto.get_execution_orders_by_order_id(9002)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].shares, 7)
        self.assertEqual(rows[0].price, 99.5)
        self.assertEqual(rows[0].execution_time.strftime("%Y%m%d-%H:%M:%S"), "20260525-11:00:00")


if __name__ == "__main__":
    unittest.main()