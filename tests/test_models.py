import asyncio
import unittest
from collections import UserDict, UserList

from aiomixcloud import Mixcloud
from aiomixcloud.models import AccessDict, AccessList, Resource, _WrapMixin


class Wrap(_WrapMixin):
    """"""

    def __init__(self, mixcloud):
        """"""
        self.mixcloud = mixcloud


class WrapDict(_WrapMixin, UserDict):
    """"""


class WrapList(_WrapMixin, UserList):
    """"""


def async_classmethod(method):
    """Return blocking version of coroutine `method`,
    making it a `classmethod`.
    """
    def wrapper(cls):
        """Wait for coroutine `method` to complete."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(method(cls))
    return classmethod(wrapper)


class TestWrapMixin(unittest.TestCase):
    """Test _WrapMixin."""

    @async_classmethod
    async def setUpClass(cls):
        """Store Mixcloud instance."""
        cls.mixcloud = Mixcloud()

    @async_classmethod
    async def tearDownClass(cls):
        """Store Mixcloud instance."""
        await cls.mixcloud.close()

    def test_wrap(self):
        """_WrapMixin._wrap must return correct data types
        for each input.
        """
        wrap = Wrap(self.mixcloud)

        data = [
            (9, int),
            ('test', str),
            ([1, 3, 2], AccessList),
            ({'foo': 'bar', 'one': 'two'}, AccessDict),
            ({'name': 'Aristotelis', 'type': 'user'}, Resource),
        ]

        for value, expected_type in data:
            wrapped = wrap._wrap(value)
            self.assertIsInstance(wrapped, expected_type)
