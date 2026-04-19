import unittest
from unittest.mock import patch, MagicMock, Mock

import sqlite3

from app.dto.scanner_dto import ScannerDTO


class TestScannerDTO(unittest.TestCase):
    def setUp(self):
        # Patch SQLiteManager in module
        self.sqlite_patcher = patch("app.dto.scanner_dto.SQLiteManager")
        self.mock_sqlite_cls = self.sqlite_patcher.start()
        self.addCleanup(self.sqlite_patcher.stop)

        # SQLiteManager instance + cursor
        self.mock_sqlite = self.mock_sqlite_cls.return_value
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_sqlite.conn = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        self.dto = ScannerDTO(strategy_id=123)

    # ------------------------------------------------------------------ rows_to_instruments

    @patch("app.dto.scanner_dto.Instrument")
    def test_rows_to_instruments_ok(self, mock_instr_cls):
        mock_instr_cls.from_row.side_effect = ["I1", "I2"]
        rows = [("row1",), ("row2",)]
        out = self.dto.rows_to_instruments(rows)
        self.assertEqual(out, ["I1", "I2"])
        self.assertEqual(mock_instr_cls.from_row.call_count, 2)

    @patch("app.dto.scanner_dto.Instrument")
    def test_rows_to_instruments_skips_bad_rows(self, mock_instr_cls):
        mock_instr_cls.from_row.side_effect = [Exception("bad"), "GOOD"]
        rows = [("bad",), ("good",)]
        out = self.dto.rows_to_instruments(rows)
        self.assertEqual(out, ["GOOD"])
        self.assertEqual(mock_instr_cls.from_row.call_count, 2)

    # ------------------------------------------------------------------ save_details

    def test_save_details_inserts_and_commits(self):
        # Build fake contractDetails
        contract = Mock(conId=1, symbol="AAPL", secType="STK",
                        currency="USD", tradingClass="NMS", exchange="NASDAQ")
        details = Mock(contract=contract)

        self.dto.save_details(reqId=10, rank=5, contractDetails=details, exec_key="KEY")

        self.mock_cursor.execute.assert_called_once()
        args = self.mock_cursor.execute.call_args[0]
        self.assertIn("INSERT INTO scanner_results", args[0])
        self.assertEqual(args[1], (10, 5, 123, 1, "AAPL", "STK", "USD", "NMS", "NASDAQ", "KEY"))
        self.mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------ set_order_candidate

    def test_set_order_candidate_updates_and_commits(self):
        self.dto.set_order_candidate(exec_key="KEY", contract_id=42, is_order_candidate=1)
        self.mock_cursor.execute.assert_called_once()
        sql, params = self.mock_cursor.execute.call_args[0]
        self.assertIn("UPDATE scanner_results SET is_order_candidate", sql)
        self.assertEqual(params, (1, "KEY", 42))
        self.mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------ get_details

    def test_get_details_fetches_all(self):
        self.mock_cursor.fetchall.return_value = [("r1",), ("r2",)]
        out = self.dto.get_details()
        self.assertEqual(out, [("r1",), ("r2",)])
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM scanner_results")

    # ------------------------------------------------------------------ get_instruments_by_exec_key

    def test_get_instruments_by_exec_key(self):
        rows = [("r1",)]
        self.mock_cursor.fetchall.return_value = rows
        with patch.object(self.dto, "rows_to_instruments", return_value=["I1"]) as mock_r2i:
            out = self.dto.get_instruments_by_exec_key("KEY")
        self.assertEqual(out, ["I1"])
        sql, params = self.mock_cursor.execute.call_args[0]
        self.assertIn("FROM scanner_results WHERE exec_key = ?", sql)
        self.assertEqual(params, ("KEY",))
        mock_r2i.assert_called_once_with(rows)

    # ------------------------------------------------------------------ get_instruments_candidates

    def test_get_instruments_candidates(self):
        rows = [("r1",)]
        self.mock_cursor.fetchall.return_value = rows
        with patch.object(self.dto, "rows_to_instruments", return_value=["I1"]) as mock_r2i:
            out = self.dto.get_instruments_candidates("KEY")
        self.assertEqual(out, ["I1"])
        sql, params = self.mock_cursor.execute.call_args[0]
        self.assertIn("is_order_candidate = 1 and exec_key = ?", sql)
        self.assertEqual(params, ("KEY",))
        mock_r2i.assert_called_once_with(rows)
        
    def test_get_contract_id_by_symbol_returns_id_and_none(self):
        # First call returns a row
        self.mock_cursor.fetchone.side_effect = [(12345,), None]

        contract_id = self.dto.get_contract_id_by_symbol("AAPL")
        self.assertEqual(contract_id, 12345)

        contract_id_none = self.dto.get_contract_id_by_symbol("MISSING")
        self.assertIsNone(contract_id_none)

if __name__ == "__main__":
    unittest.main()


class TestScannerDTOIntegration(unittest.TestCase):
    """Integration tests with actual in-memory database."""

    def setUp(self):
        # Create in-memory DB
        self.conn = sqlite3.connect(":memory:")
        self._create_tables()

        # Patch SQLiteManager to use this connection
        mock_db_manager = Mock()
        mock_db_manager.conn = self.conn

        self.db_patcher = patch("app.dto.scanner_dto.SQLiteManager", return_value=mock_db_manager)
        self.db_patcher.start()

        self.dto = ScannerDTO(strategy_id=123)

    def tearDown(self):
        if hasattr(self, "conn"):
            self.conn.close()
        if hasattr(self, "db_patcher"):
            self.db_patcher.stop()

    def _create_tables(self):
        cursor = self.conn.cursor()

        # strategies table (for FK)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_date  TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # scanner_results table aligned with current schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanner_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exec_key TEXT NOT NULL,
                strategy_id INTEGER NOT NULL,
                req_id INTEGER NOT NULL, 
                rank INTEGER NOT NULL, 
                contract_id INTEGER NOT NULL,
                contract_symbol TEXT NOT NULL, 
                contract_sectype TEXT NOT NULL,
                contract_currency TEXT NOT NULL,
                contract_trading_class TEXT NOT NULL,
                contract_exchange TEXT,
                is_order_candidate BOOLEAN NOT NULL DEFAULT 0,
                create_date  TEXT NOT NULL DEFAULT (datetime('now')),
                update_date  TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
            );
        """)

        # Insert matching strategy
        cursor.execute("INSERT INTO strategies (strategy_id) VALUES (123)")
        self.conn.commit()

    # ------------------------------------------------------------------ integration tests

    def test_save_details_and_get_details(self):
        contract = Mock(conId=1, symbol="AAPL", secType="STK",
                        currency="USD", tradingClass="NMS", exchange="NASDAQ")
        details = Mock(contract=contract)

        self.dto.save_details(reqId=10, rank=5, contractDetails=details, exec_key="KEY")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT req_id, rank, strategy_id, contract_id, exec_key
            FROM scanner_results
            WHERE exec_key = ?
        """, ("KEY",))
        row = cursor.fetchone()
        self.assertIsNotNone(row)

        # Explicit column checks (avoid column-order assumptions)
        self.assertEqual(row[0], 10)    # req_id
        self.assertEqual(row[1], 5)     # rank
        self.assertEqual(row[2], 123)   # strategy_id
        self.assertEqual(row[3], 1)     # contract_id
        self.assertEqual(row[4], "KEY") # exec_key

    def test_set_order_candidate_updates(self):
        # Insert one row
        contract = Mock(conId=2, symbol="MSFT", secType="STK",
                        currency="USD", tradingClass="NMS", exchange="NASDAQ")
        details = Mock(contract=contract)
        self.dto.save_details(reqId=11, rank=1, contractDetails=details, exec_key="KEY2")

        # Update candidate flag
        self.dto.set_order_candidate(exec_key="KEY2", contract_id=2, is_order_candidate=1)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT is_order_candidate
            FROM scanner_results
            WHERE exec_key = ? AND contract_id = ?
        """, ("KEY2", 2))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 1)

    def test_get_details(self):
        # Insert two rows
        for idx, symbol in [(1, "AAPL"), (2, "MSFT")]:
            contract = Mock(conId=idx, symbol=symbol, secType="STK",
                            currency="USD", tradingClass="NMS", exchange="NASDAQ")
            details = Mock(contract=contract)
            self.dto.save_details(reqId=20 + idx, rank=idx, contractDetails=details, exec_key="K")

        out = self.dto.get_details()
        self.assertEqual(len(out), 2)
        
    def test_clean_non_candidates_deletes_and_commits(self):
        exec_key = "ABC"
        self.dto.save_details(reqId=1, rank=1, contractDetails=Mock(contract=Mock(conId=1, symbol="AAPL", secType="STK", currency="USD", tradingClass="NMS", exchange="NASDAQ")), exec_key=exec_key)
        self.dto.save_details(reqId=1, rank=2, contractDetails=Mock(contract=Mock(conId=2, symbol="TSLA", secType="STK", currency="USD", tradingClass="NMS", exchange="NASDAQ")), exec_key=exec_key)
        self.dto.set_order_candidate(exec_key=exec_key, contract_id=1, is_order_candidate=1)
        
        self.dto.clean_non_candidates(exec_key)

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scanner_results WHERE exec_key = ?", (exec_key,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
        

    