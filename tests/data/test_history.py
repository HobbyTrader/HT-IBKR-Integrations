import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from app.data.history import History

class TestHistory(unittest.TestCase):
    def test_from_row_happy_path(self):
        fixed_dt = datetime(2024, 1, 1, 9, 30)
        row = (
            101,                # instrument_id
            "AAPL",             # symbol
            "2024-01-01 09:30", # bar_time
            100.0,              # open_price
            110.0,              # high_price
            95.0,               # low_price
            105.0,              # close_price
            1000,               # volume
            102.5,              # wap
            12,                 # bar_count
            "2024-01-01 09:31", # create_date
            "2024-01-01 09:32", # update_date
        )

        with patch("app.data.history._parse_datetime", return_value=fixed_dt):
            hist = History.from_row(row)

        self.assertEqual(hist.instrument_id, 101)
        self.assertEqual(hist.symbol, "AAPL")
        self.assertEqual(hist.bar_time, fixed_dt)
        self.assertEqual(hist.open_price, 100.0)
        self.assertEqual(hist.high_price, 110.0)
        self.assertEqual(hist.low_price, 95.0)
        self.assertEqual(hist.close_price, 105.0)
        self.assertEqual(hist.volume, 1000)
        self.assertEqual(hist.wap, 102.5)
        self.assertEqual(hist.bar_count, 12)
        self.assertEqual(hist.create_date, fixed_dt)
        self.assertEqual(hist.update_date, fixed_dt)

    def test_from_row_invalid_length_raises(self):
        with self.assertRaises(ValueError):
            History.from_row((1, 2, 3))

    def test_from_bar(self):
        fixed_dt = datetime(2024, 1, 1, 9, 30)
        bar = SimpleNamespace(
            date="2024-01-01 09:30",
            open=10.0,
            high=12.0,
            low=9.5,
            close=11.0,
            volume=500,
            wap=10.8,
            barCount=7,
        )

        with patch("app.data.history._parse_datetime", return_value=fixed_dt):
            hist = History.from_bar(200, "MSFT", bar)

        self.assertEqual(hist.instrument_id, 200)
        self.assertEqual(hist.symbol, "MSFT")
        self.assertEqual(hist.bar_time, fixed_dt)
        self.assertEqual(hist.open_price, 10.0)
        self.assertEqual(hist.high_price, 12.0)
        self.assertEqual(hist.low_price, 9.5)
        self.assertEqual(hist.close_price, 11.0)
        self.assertEqual(hist.volume, 500)
        self.assertEqual(hist.wap, 10.8)
        self.assertEqual(hist.bar_count, 7)

    
if __name__ == "__main__":
    unittest.main()