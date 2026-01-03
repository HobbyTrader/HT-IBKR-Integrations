import unittest
from unittest.mock import Mock, MagicMock, patch

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

        mock_strategy.assert_called_once_with(id=2, name="MeanRev", details="DETAILS", tags=["US", "STOCK", "TECH"])

    @patch("app.dto.strategy_dto.Strategy")
    @patch("app.dto.strategy_dto.StrategyDetail")
    def test_row_to_strategy_parses_list_value(self, mock_detail, mock_strategy):
        mock_detail.from_json.return_value = "DETAILS"
        row = [3, "FX", ["FX", "G10"], "{}"]

        self.dto.row_to_strategy(row)

        mock_strategy.assert_called_once_with(id=3, name="FX", details="DETAILS", tags=["FX", "G10"])

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