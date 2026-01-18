import json
import unittest
from datetime import time

from app.utils.timeencoder import TimeEncoder


class TestTimeEncoder(unittest.TestCase):
    """Test cases for TimeEncoder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = TimeEncoder()
    
    def test_encode_time_object(self):
        """Test encoding a time object to ISO format string."""
        test_time = time(14, 30, 45)
        result = json.dumps({"time": test_time}, cls=TimeEncoder)
        expected = '{"time": "14:30:45"}'
        self.assertEqual(result, expected)
    
    def test_encode_time_with_microseconds(self):
        """Test encoding time with microseconds."""
        test_time = time(14, 30, 45, 123456)
        result = json.dumps({"time": test_time}, cls=TimeEncoder)
        expected = '{"time": "14:30:45.123456"}'
        self.assertEqual(result, expected)
    
    def test_encode_midnight(self):
        """Test encoding midnight time."""
        test_time = time(0, 0, 0)
        result = json.dumps({"time": test_time}, cls=TimeEncoder)
        expected = '{"time": "00:00:00"}'
        self.assertEqual(result, expected)
    
    def test_encode_end_of_day(self):
        """Test encoding end of day time."""
        test_time = time(23, 59, 59)
        result = json.dumps({"time": test_time}, cls=TimeEncoder)
        expected = '{"time": "23:59:59"}'
        self.assertEqual(result, expected)
    
    def test_encode_multiple_time_objects(self):
        """Test encoding multiple time objects in a dictionary."""
        data = {
            "start": time(9, 30, 0),
            "end": time(16, 0, 0)
        }
        result = json.dumps(data, cls=TimeEncoder)
        self.assertIn('"start": "09:30:00"', result)
        self.assertIn('"end": "16:00:00"', result)
    
    def test_encode_list_of_times(self):
        """Test encoding a list of time objects."""
        times = [time(9, 30), time(12, 0), time(16, 0)]
        result = json.dumps(times, cls=TimeEncoder)
        expected = '["09:30:00", "12:00:00", "16:00:00"]'
        self.assertEqual(result, expected)
    
    def test_encode_nested_structure(self):
        """Test encoding nested structure with time objects."""
        data = {
            "schedule": {
                "morning": time(9, 0),
                "afternoon": time(14, 0)
            }
        }
        result = json.dumps(data, cls=TimeEncoder)
        self.assertIn('"morning": "09:00:00"', result)
        self.assertIn('"afternoon": "14:00:00"', result)
    
    def test_encode_non_time_objects(self):
        """Test that non-time objects are encoded normally."""
        data = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "null": None
        }
        result = json.dumps(data, cls=TimeEncoder)
        self.assertIn('"string": "test"', result)
        self.assertIn('"number": 42', result)
        self.assertIn('"boolean": true', result)
        self.assertIn('"null": null', result)
    
    def test_encode_mixed_types_with_time(self):
        """Test encoding mixed data types including time."""
        data = {
            "time": time(10, 30),
            "name": "Trading Session",
            "active": True,
            "count": 5
        }
        result = json.dumps(data, cls=TimeEncoder)
        self.assertIn('"time": "10:30:00"', result)
        self.assertIn('"name": "Trading Session"', result)
        self.assertIn('"active": true', result)
        self.assertIn('"count": 5', result)
    
    def test_default_method_directly(self):
        """Test calling the default method directly."""
        test_time = time(12, 0, 0)
        result = self.encoder.default(test_time)
        self.assertEqual(result, "12:00:00")
    
    def test_default_method_with_non_time(self):
        """Test default method raises TypeError for unsupported types."""
        with self.assertRaises(TypeError):
            self.encoder.default(object())


if __name__ == '__main__':
    unittest.main()