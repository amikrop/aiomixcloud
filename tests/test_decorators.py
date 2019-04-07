import unittest

from aiomixcloud.decorators import displayed, paginated, targeting, uploading

from tests.synced import synced


class TestDisplayed(unittest.TestCase):
    """Test `displayed`."""

    @synced
    async def test_none(self):
        """`displayed` must call the decorated function with 'json' as
        a 'format' `param` item and no other `param` items, when called
        with no keyword arguments.
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
            """Dummy coroutine."""

        with self.assertRaises(TypeError):
            await coroutine(nonexistent=9)
        with self.assertRaises(TypeError):
            await coroutine(5, True, missing='a')


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
