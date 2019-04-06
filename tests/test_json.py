import unittest
from datetime import datetime, timezone
from pathlib import Path

from aiomixcloud.json import MixcloudJSONDecoder


class JSONTestCase(unittest.TestCase):
    """Test `MixcloudJSONDecoder`."""

    @classmethod
    def setUpClass(cls):
        """Store `MixcloudJSONDecoder instance."""
        cls.decoder = MixcloudJSONDecoder()

    def test_default(self):
        """`MixcloudJSONDecoder` must decode non-datetime-like values
        as `json.JSONDecoder` does.
        """
        result = self.decoder.decode('{"foo": "bar", "test": 9}')
        self.assertEqual(result['foo'], 'bar')
        self.assertEqual(result['test'], 9)

    def test_datetime(self):
        """`MixcloudJSONDecoder` must decode datetime-like strings
        as `datetime` objects.
        """
        result = self.decoder.decode('{"foo": "2019-02-03T04:22:18Z"}')
        expected = datetime(2019, 2, 3, 4, 22, 18, tzinfo=timezone.utc)
        self.assertEqual(result['foo'], expected)

    def test_combined(self):
        """`MixcloudJSONDecoder` must decode all values (datetime-like
        or not) correctly when both kinds are present in the encoded
        data.
        """
        filename = Path('tests') / 'fixtures' / 'favorites.json'
        with filename.open() as f:
            data = f.read()
        result = self.decoder.decode(data)

        self.assertEqual(result['name'], "Chris's favorites")
        self.assertEqual(result['data'][0]['play_count'], 6365)
        expected_datetime = datetime(
            2017, 1, 4, 9, 56, 10, tzinfo=timezone.utc)
        self.assertEqual(result['data'][1]['created_time'], expected_datetime)
