import unittest
from datetime import datetime, timezone

from aiomixcloud.datetime import _to_datetime, format_datetime, to_timestamp


class TestDatetime(unittest.TestCase):
    """Test datetime functions."""

    def test_to_datetime_datetime_utc(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a UTC `datetime`.
        """
        value = datetime(2019, 4, 5, 16, 44, 41, 589590, tzinfo=timezone.utc)
        result = _to_datetime(value)
        self.assertEqual(result, value)
