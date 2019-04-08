import unittest

from aiomixcloud.decorators import displayed, paginated, targeting, uploading

from tests.synced import synced


class TestDisplayed(unittest.TestCase):
    """Test `displayed`."""

    @synced
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

    @synced
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

    @synced
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

    @synced
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


class TestPaginated(unittest.TestCase):
    """Test `paginated`."""

    @synced
    async def test_none(self):
        """`paginated` must call the decorated function with an empty
        `params`, when called with no keyword arguments.
        """
        @paginated
        async def coroutine(*args, params):
            """Check that `params` contains the proper items
            according to the calls.
            """
            self.assertFalse(params)

        await coroutine()
        await coroutine('foo', {3: 'bc'}, None)

    @synced
    async def test_some(self):
        """`paginated` must call the decorated function with `params`
        containing items corresponding to used keyword arguments, when
        called with some of the available keyword arguments.
        """
        @paginated
        async def coroutine(*args, params):
            """Check that `params` contains the proper items
            according to the calls.
            """
            for key in ('since', 'until'):
                self.assertIn(key, params)
                params.pop(key)
            self.assertFalse(params)

        await coroutine(since=39847202, until=39852219)
        await coroutine(True, 'baz', -1, (2, False),
                        since=892402130, until=892450038)

    @synced
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

    @synced
    async def test_threshold_calculation(self):
        """`paginated` must calculate `params`'s items 'offset'
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
