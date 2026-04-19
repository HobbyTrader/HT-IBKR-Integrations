import unittest
from unittest.mock import Mock, MagicMock, patch

import sqlite3

from app.dto.strategy_dto import StrategyDTO


class TestStrategyDTO(unittest.TestCase):
    def setUp(self):
        # Patch SQLiteManager for all tests
        self.sqlite_patcher = patch("app.dto.strategy_dto.SQLiteManager")
        self.mock_sqlite_cls = self.sqlite_patcher.start()
        self.addCleanup(self.sqlite_patcher.stop)

        # Instance and its cursor/connection mocks
        self.mock_sqlite = self.mock_sqlite_cls.return_value
        self.mock_cursor = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_sqlite.get_cursor.return_value = self.mock_cursor
        self.mock_sqlite.get_connection.return_value = self.mock_conn

        self.dto = StrategyDTO()

    # ------------------------------------------------------------------ row_to_strategy

    @patch("app.dto.strategy_dto.Strategy")
    @patch("app.dto.strategy_dto.StrategyDetail")
    def test_row_to_strategy_parses_list_like_string(self, mock_detail, mock_strategy):
        mock_detail.from_json.return_value = "DETAILS"
        row = [1, "GapOpen", "['US', 'STOCK']", '{"foo": "bar"}']

        result = self.dto.row_to_strategy(row)

        mock_detail.from_json.assert_called_once_with('{"foo": "bar"}')
        mock_strategy.assert_called_once_with(id=1, name="GapOpen", details="DETAILS", tags=["US", "STOCK"])
        self.assertEqual(result, mock_strategy.return_value)

    @patch("app.dto.strategy_dto.Strategy")
    @patch("app.dto.strategy_dto.StrategyDetail")
    def test_row_to_strategy_parses_comma_string(self, mock_detail, mock_strategy):
        mock_detail.from_json.return_value = "DETAILS"
        row = [2, "MeanRev", "US,STOCK,TECH", "{}"]

        self.dto.row_to_strategy(row)

        mock_strategy.assert_called_once_with(id=2, name="MeanRev", details=None, tags=["US", "STOCK", "TECH"])

    @patch("app.dto.strategy_dto.Strategy")
    @patch("app.dto.strategy_dto.StrategyDetail")
    def test_row_to_strategy_parses_list_value(self, mock_detail, mock_strategy):
        mock_detail.from_json.return_value = "DETAILS"
        row = [3, "FX", ["FX", "G10"], "{}"]

        self.dto.row_to_strategy(row)

        mock_strategy.assert_called_once_with(id=3, name="FX", details=None, tags=["FX", "G10"])

    # ------------------------------------------------------------------ save_strategy

    def test_save_strategy_inserts_and_commits(self):
        strategy = Mock()
        strategy.name = "Gap"
        strategy.tags = ["US", "STOCK"]
        strategy.details.to_json.return_value = '{"d":1}'

        self.dto.save_strategy(strategy)

        self.mock_cursor.execute.assert_called_once_with(
            "INSERT INTO strategies (strategy_name, strategy_tags, strategy_details) VALUES (?, ?, ?)",
            ("Gap", "['US', 'STOCK']", '{"d":1}'),
        )
        self.mock_conn.commit.assert_called_once()

    # ------------------------------------------------------------------ get_active_strategies

    def test_get_active_strategies_builds_list(self):
        rows = [
            (1, "S1", "US,STOCK", "{}"),
            (2, "S2", "EU,FOREX", "{}"),
        ]
        self.mock_cursor.fetchall.return_value = rows

        with patch.object(self.dto, "row_to_strategy", side_effect=["A", "B"]) as mock_r2s:
            result = self.dto.get_active_strategies()

        self.assertEqual(result, ["A", "B"])
        mock_r2s.assert_called()
        self.mock_cursor.execute.assert_called_once()

    # ------------------------------------------------------------------ get_strategy_by_name / id

    def test_get_strategy_by_name_none(self):
        self.mock_cursor.fetchone.return_value = None
        self.assertIsNone(self.dto.get_strategy_by_name("X"))

    def test_get_strategy_by_name_found(self):
        row = (1, "S1", "US", "{}")
        self.mock_cursor.fetchone.return_value = row
        with patch.object(self.dto, "row_to_strategy", return_value="OBJ") as mock_r2s:
            out = self.dto.get_strategy_by_name("S1")
        self.assertEqual(out, "OBJ")
        mock_r2s.assert_called_once_with(row)

    def test_get_strategy_by_id_none(self):
        self.mock_cursor.fetchone.return_value = None
        self.assertIsNone(self.dto.get_strategy_by_id(99))

    def test_get_strategy_by_id_found(self):
        row = (2, "S2", "US", "{}")
        self.mock_cursor.fetchone.return_value = row
        with patch.object(self.dto, "row_to_strategy", return_value="OBJ") as mock_r2s:
            out = self.dto.get_strategy_by_id(2)
        self.assertEqual(out, "OBJ")
        mock_r2s.assert_called_once_with(row)

    # ------------------------------------------------------------------ get_strategies_by_tags

    def test_get_strategies_by_tags_or(self):
        rows = [(1, "S1", "US,STOCK", "{}")]
        self.mock_cursor.fetchall.return_value = rows
        with patch.object(self.dto, "row_to_strategy", return_value="OBJ") as mock_r2s:
            out = self.dto.get_strategies_by_tags(["US", "STOCK"], all_must_match=False)
        self.assertEqual(out, ["OBJ"])
        sql, params = self.mock_cursor.execute.call_args[0][0], self.mock_cursor.execute.call_args[0][1]
        self.assertIn(" OR ", sql)
        self.assertEqual(params, ["%US%", "%STOCK%"])
        mock_r2s.assert_called_once_with(rows[0])

    def test_get_strategies_by_tags_and(self):
        rows = [(1, "S1", "US,STOCK", "{}")]
        self.mock_cursor.fetchall.return_value = rows
        with patch.object(self.dto, "row_to_strategy", return_value="OBJ"):
            self.dto.get_strategies_by_tags(["US", "STOCK"], all_must_match=True)
        sql = self.mock_cursor.execute.call_args[0][0]
        self.assertIn(" AND ", sql)

    # ------------------------------------------------------------------ deactivate_strategy / update_strategy

    def test_deactivate_strategy_updates(self):
        self.dto.deactivate_strategy(5)
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()

    def test_update_strategy_updates(self):
        strategy = Mock()
        strategy.name = "New"
        strategy.tags = ["US"]
        strategy.details.to_json.return_value = '{"a":1}'
        self.dto.update_strategy(7, strategy)
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()


class TestStrategyDTOIntegration(unittest.TestCase):
    """Integration tests with actual in-memory database."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self._create_tables()

        mock_db = Mock()
        mock_db.get_connection.return_value = self.conn
        mock_db.get_cursor.return_value = self.conn.cursor()

        self.db_patcher = patch("app.dto.strategy_dto.SQLiteManager", return_value=mock_db)
        self.db_patcher.start()

        self.dto = StrategyDTO()

    def tearDown(self):
        if hasattr(self, "conn"):
            self.conn.close()
        if hasattr(self, "db_patcher"):
            self.db_patcher.stop()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                strategy_tags TEXT NOT NULL,
                strategy_details TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                create_date TEXT NOT NULL DEFAULT (datetime('now')),
                update_date TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self.conn.commit()

    def test_save_and_get_by_name(self):
        strategy = Mock()
        strategy.name = "GapOpen"
        strategy.tags = ["US", "STOCK"]
        strategy.details.to_json.return_value = '''{"instrument": "STK",
                "locationCode": "STK.US.MAJOR",
                "scanCode": "HIGH_OPEN_GAP",
                "scan_options": [],
                "filter_options": [],
                "maxResults": 50,
                "minutes_to_order": 3,
                "max_shares_to_invest_per_trade": 1000,
                "min_shares_to_invest_per_trade": 100,
                "max_price_per_trade": 5000,
                "min_price_per_trade": 1000,
                "max_trades_per_day": 5,
                "opening_hours": ["15:30:00","22:00:00"],
                "min_open_trade_gap_percentage": 2.0,
                "max_open_trade_gap_percentage": 10.0,
                "max_volume_percent": 1.0,
                "stop_loss_percent": 95.0,
                "take_profit_percent": 110.0,
                "increase_position_candidate_percentage": 0.5}'''

        self.dto.save_strategy(strategy)

        out = self.dto.get_strategy_by_name("GapOpen")
        self.assertIsNotNone(out)
        self.assertEqual(out.name, "GapOpen")
        self.assertEqual(out.tags, ["US", "STOCK"])

    def test_get_active_strategies_only(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO strategies (strategy_name, strategy_tags, strategy_details, is_active)
            VALUES
            ('S1', 'US', '{}', 1),
            ('S2', 'EU', '{}', 0)
        """)
        self.conn.commit()

        results = self.dto.get_active_strategies()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "S1")

    def test_update_strategy_updates_fields(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO strategies (strategy_name, strategy_tags, strategy_details, is_active)
            VALUES ('Old', 'US', '{}', 1)
        """)
        self.conn.commit()

        strategy_id = cur.lastrowid

        new_strategy = Mock()
        new_strategy.name = "New"
        new_strategy.tags = ["EU"]
        new_strategy.details.to_json.return_value = '{"v":1}'

        self.dto.update_strategy(strategy_id, new_strategy)

        cur.execute("""
            SELECT strategy_name, strategy_tags, strategy_details
            FROM strategies WHERE strategy_id = ?
        """, (strategy_id,))
        row = cur.fetchone()

        self.assertEqual(row[0], "New")
        self.assertEqual(row[1], "['EU']")
        self.assertEqual(row[2], '{"v":1}')

    def test_deactivate_strategy_sets_inactive(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO strategies (strategy_name, strategy_tags, strategy_details, is_active)
            VALUES ('S1', 'US', '{}', 1)
        """)
        self.conn.commit()

        strategy_id = cur.lastrowid
        self.dto.deactivate_strategy(strategy_id)

        cur.execute("SELECT is_active FROM strategies WHERE strategy_id = ?", (strategy_id,))
        row = cur.fetchone()
        self.assertEqual(row[0], 0)