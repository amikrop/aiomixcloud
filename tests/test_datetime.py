import unittest
from datetime import datetime, timezone

from aiomixcloud.datetime import _to_datetime, format_datetime, to_timestamp


class TestDatetime(unittest.TestCase):
    """Test datetime functions."""

    def test_to_datetime_datetime(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a timezone-naive `datetime`.
        """
        value = datetime(2019, 4, 5, 19, 43, 10, 461812)
        result = _to_datetime(value)
        self.assertEqual(result, value.astimezone(timezone.utc))

    def test_to_datetime_datetime_utc(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a UTC `datetime`.
        """
        value = datetime(2019, 4, 5, 16, 44, 41, 589590, tzinfo=timezone.utc)
        result = _to_datetime(value)
        self.assertEqual(result, value)

    def test_to_datetime_str(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a datetime-like `str`.
        """
        values = [
            ('2019-04-10T07:32:56Z',
             datetime(2019, 4, 10, 7, 32, 56, tzinfo=timezone.utc)),
            ('2019-04-10T09:33:04',
             datetime(2019, 4, 10, 6, 33, 4, tzinfo=timezone.utc)),
            ('11-12-2018 09:41:05',
             datetime(2018, 11, 12, 7, 41, 5, tzinfo=timezone.utc)),
            ('10-03-2019',
             datetime(2019, 10, 2, 21, 0, tzinfo=timezone.utc)),
            ('17/06/2019',
             datetime(2019, 6, 16, 21, 0, tzinfo=timezone.utc)),
            ('Jan 1, 2020 12:33:11',
             datetime(2020, 1, 1, 10, 33, 11, tzinfo=timezone.utc)),
            ('February 18, 2020 13:21:59',
             datetime(2020, 2, 18, 11, 21, 59, tzinfo=timezone.utc)),
        ]

        for value, expected in values:
            self.assertEqual(_to_datetime(value), expected)
