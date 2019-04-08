import unittest
from datetime import datetime, timezone

from aiomixcloud.decorators import displayed, paginated, targeting, uploading

from tests.synced import SyncedTestCase


class TestDisplayed(SyncedTestCase):
    """Test `displayed`."""

    async def test_none(self):
        """`displayed` must call the decorated function with 'json' as
        a 'format' `params` item and no other `params` items, when
        called with no keyword arguments.
        """
        @displayed
        async def coroutine(*args, params):
            """Check that `params` contains the proper items
            according to the calls.
            """
            self.assertEqual(params['format'], 'json')
            params.pop('format')
            self.assertFalse(params)

        await coroutine()
        await coroutine('positional', 5)

    async def test_some(self):
        """`displayed` must call the decorated function with `params`
        containing items corresponding to used keyword arguments, when
        called with some of the available keyword arguments.
        """
        @displayed
        async def coroutine(*args, params):
            """Check that `params` contains the proper items
            according to the calls.
            """
            for key in ('format', 'height'):
                self.assertIn(key, params)
                params.pop(key)
            self.assertFalse(params)

        await coroutine(format='html', height=60)
        await coroutine('testing', False, 32, format='html', height=65)

    async def test_all(self):
        """`displayed` must call the decorated function with `params`
        containing items corresponding to used keyword arguments, when
        called with all available keyword arguments.
        """
        @displayed
        async def coroutine(*args, params):
            """Check that `params` contains the proper items
            according to the calls.
            """
            for key in ('format', 'width', 'height', 'color'):
                self.assertIn(key, params)
                params.pop(key)
            self.assertFalse(params)

        await coroutine(format='html', width=100, height=50, color='f4cb42')
        await coroutine('test', -4, [],
                        format='html', width=110, height=55, color='9bf441')

    async def test_extra(self):
        """Functions decorated by `displayed` must raise `TypeError`
        when called with non-existent keyword arguments.
        """
        @displayed
        async def coroutine(*args, params):
            """Dummy coroutine function."""

        with self.assertRaises(TypeError):
            await coroutine(nonexistent=9)
        with self.assertRaises(TypeError):
            await coroutine(5, True, missing='a')


class TestPaginated(SyncedTestCase):
    """Test `paginated`."""

    async def test_none(self):
        """`paginated` must call the decorated function with an empty
        `params`, when called with no keyword arguments.
        """
        @paginated
        async def coroutine(*args, params, **kwargs):
            """Check that `params` contains the proper items
            according to the calls.
            """
            self.assertFalse(params)

        await coroutine()
        await coroutine('foo', {3: 'bc'}, None)
        await coroutine(42, 'a', some_keyword=3, baz=False)

    async def test_some(self):
        """`paginated` must call the decorated function with `params`
        containing items corresponding to used keyword arguments, when
        called with some of the available keyword arguments.
        """
        @paginated
        async def coroutine(*args, params, **kwargs):
            """Check that `params` contains the proper items
            according to the calls.
            """
            for key in ('since', 'until'):
                self.assertIn(key, params)
                params.pop(key)
            self.assertFalse(params)

        await coroutine(since=39847202, until=39852219)
        await coroutine(since='03/09/2017', until='03/10/2017', extra=8)
        await coroutine(True, 'baz', -1, (2, False),
                        since=892402130, until=892450038)
        await coroutine(4, 'test', since='11/09/2018',
                        until='12/09/2018', foo='bar', keyword=12)

    async def test_invalid(self):
        """`paginated` must raise `AssertionError` when `params`'s
        'page' item is specified simultaneously with any of
        ['offset', 'limit', 'since', 'until'].
        """
        @paginated
        async def coroutine(params):
            """Dummy coroutine function."""

        with self.assertRaises(AssertionError):
            await coroutine(page=3, limit=90)

    async def test_threshold_calculation(self):
        """`paginated` must calculate `params`'s 'offset'
        and 'limit' items, out of 'page'.
        """
        @paginated
        async def coroutine(params):
            """Return the 'offset' and 'limit' items of `params`."""
            return params['offset'], params['limit']

        values = [
            (2, None, 40, 20),
            (8, None, 160, 20),
            (0, None, 0, 20),
            (7, 30, 210, 30),
            (12, 45, 540, 45),
            (2, 4, 8, 4),
            (0, 1, 0, 1),
        ]
        for page, per_page, offset, limit in values:
            params = {'page': page}
            if per_page is not None:
                params['per_page'] = per_page
            result_offset, result_limit = await coroutine(**params)

            self.assertEqual(result_offset, offset)
            self.assertEqual(result_limit, limit)

    async def test_timestamp_conversion(self):
        """`paginated` must convert `params`'s 'since'
        and 'until' items to UNIX timestamps.
        """
        @paginated
        async def coroutine(params):
            """Return the 'since' and 'until' items of `params`."""
            return params['since'], params['until']

        values = [
            ('Jan 12 2018 21:02:44 UTC', 1515931200,
             1515790964, 1515931200),
            (1550001910, datetime(2020, 2, 12, 20, 0, 0, tzinfo=timezone.utc),
             1550001910, 1581537600),
            (datetime(2015, 8, 9, 0, 10, 0, tzinfo=timezone.utc),
             'August 1, 2016 00:00:00GMT', 1439079000, 1470009600),
        ]
        for since, until, expected_since, expected_until in values:
            result_since, result_until = await coroutine(
                since=since, until=until)

            self.assertEqual(result_since, expected_since)
            self.assertEqual(result_until, expected_until)


class TestTargeting(unittest.TestCase):
    """Test `targeting`."""

    def test_targeting(self):
        """`targeting` must set a `_targeting` attribute to the
        decorated coroutine, equal to ``True``.
        """
        @targeting
        async def coroutine():
            """Dummy coroutine function."""

        self.assertTrue(hasattr(coroutine, '_targeting'))
        self.assertTrue(coroutine._targeting)


class TestUploading(SyncedTestCase):
    """Test `uploading`."""

    async def test_none(self):
        """`uploading` must call the decorated function with an empty
        `params`, when called with no keyword arguments.
        """
        @paginated
        async def coroutine(*args, params):
            """Check that `params` contains the proper items
            according to the calls.
            """
            self.assertFalse(params)

        await coroutine()
        await coroutine(-14, False, 'foo')
