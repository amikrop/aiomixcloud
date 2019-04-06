import unittest

from aiomixcloud.decorators import displayed, paginated, targeting, uploading


class DecoratorTest(unittest.TestCase):
    """Test function decorators."""

    def test_targeting(self):
        """`targeting` must set a `_targeting` attribute to the
        decorated coroutine, equal to ``True``.
        """
        @targeting
        async def coroutine():
            """Dummy coroutine function."""

        self.assertTrue(hasattr(coroutine, '_targeting'))
        self.assertTrue(coroutine._targeting)
