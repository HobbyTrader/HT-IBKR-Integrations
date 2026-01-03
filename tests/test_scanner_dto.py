import unittest
from unittest.mock import patch, MagicMock, Mock

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


if __name__ == "__main__":
    unittest.main()