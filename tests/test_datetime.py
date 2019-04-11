from datetime import datetime, timezone

from dateutil.tz import tzlocal

from aiomixcloud.datetime import _to_datetime, format_datetime, to_timestamp

from tests.verbose import VerboseTestCase


def naive_to_utc(dt):
    """Convert and return given timezone-naive `dt` in UTC.
    Consider it being in the local timezone.
    """
    aware_local = dt.replace(tzinfo=tzlocal())
    return aware_local.astimezone(timezone.utc)


class TestDatetime(VerboseTestCase):
    """Test datetime functions."""

    def test_to_datetime_datetime(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a timezone-naive `datetime`.
        """
        value = datetime(2019, 2, 7, 19, 43, 10, 461812)
        result = _to_datetime(value)
        expected = naive_to_utc(value)
        self.assertEqual(result, expected)

    def test_to_datetime_datetime_utc(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a UTC `datetime`.
        """
        value = datetime(2019, 4, 5, 16, 44, 41, 589590, tzinfo=timezone.utc)
        result = _to_datetime(value)
        self.assertEqual(result, value)

    def test_to_datetime_str_naive(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a timezone-naive datetime-like str.
        """
        values = [
            ('2019-11-10T09:33:04', datetime(2019, 11, 10, 9, 33, 4)),
            ('11-12-2018 09:41:05', datetime(2018, 11, 12, 9, 41, 5)),
            ('10-03-2019', datetime(2019, 10, 3, 0, 0)),
            ('17/06/2019', datetime(2019, 6, 17, 0, 0)),
            ('Jan 1, 2020 12:33:11', datetime(2020, 1, 1, 12, 33, 11)),
            ('February 18, 2020 13:21:59', datetime(2020, 2, 18, 13, 21, 59)),
        ]

        for value, naive in values:
            expected = naive_to_utc(naive)
            self.assertEqual(_to_datetime(value), expected)

    def check_aware_values(self, values):
        """Check that `_to_datetime` returns a UTC `datetime` when
        called with timezone-aware values.
        """
        for value, naive in values:
            expected = naive.replace(tzinfo=timezone.utc)
            self.assertEqual(_to_datetime(value), expected)

    def test_to_datetime_str_aware(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a timezone-aware datetime-like str.
        """
        values = [
            ('2019-04-10T07:32:56Z', datetime(2019, 4, 10, 7, 32, 56)),
            ('2018-02-12T13:00:28 GMT-2', datetime(2018, 2, 12, 11, 0, 28)),
            ('2020 April 17, 02:58:04 +03', datetime(2020, 4, 16, 23, 58, 4)),
        ]
        self.check_aware_values(values)

    def test_to_datetime_timestamp(self):
        """`_to_datetime` must return a UTC `datetime` when called
        with a UNIX timestamp.
        """
        values = [
            (-2345542, datetime(1969, 12, 4, 20, 27, 38)),
            (0, datetime(1970, 1, 1, 0, 0)),
            (1383429086, datetime(2013, 11, 2, 21, 51, 26)),
        ]
        self.check_aware_values(values)

    def test_to_datetime_failure(self):
        """`to_datetime` must raise TypeError when called
        with invalid input."""
        invalid_values = ['random text', [True, 3], {}]
        for value in invalid_values:
            with self.assertRaises(TypeError):
                _to_datetime(value)

    def test_format_datetime(self):
        """`format_datetime` must return a string in
        the "YYYY-MM-DDTHH:MM:SSZ" format.
        """
        value = datetime(2019, 3, 4, 20, 23, 17, tzinfo=timezone.utc)
        result = format_datetime(value)
        self.assertEqual(result, '2019-03-04T20:23:17Z')

    def test_to_timestamp(self):
        """`to_timestamp` must return a UNIX timestamp."""
        value = datetime(2020, 6, 1, 18, 21, 1, tzinfo=timezone.utc)
        result = to_timestamp(value)
        self.assertEqual(result, 1591035661)
