import asyncio
import unittest
from collections import UserDict, UserList

from aiomixcloud import Mixcloud
from aiomixcloud.models import AccessDict, AccessList, Resource, _WrapMixin


class Wrap(_WrapMixin):
    """`_WrapMixin` trivial implementation."""

    def __init__(self, mixcloud):
        """Store Mixcloud instance."""
        self.mixcloud = mixcloud


class WrapDict(_WrapMixin, UserDict):
    """Wrapping dictionary."""


class WrapList(_WrapMixin, UserList):
    """Wrapping list."""


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
        """Store expected types and Mixcloud instance."""
        cls.expected = [int, str, AccessList, AccessDict, Resource]
        cls.mixcloud = Mixcloud()

    @async_classmethod
    async def tearDownClass(cls):
        """Close Mixcloud instance."""
        await cls.mixcloud.close()

    def test_wrap(self):
        """_WrapMixin._wrap must return correct data types
        for each input.
        """
        wrap = Wrap(self.mixcloud)
        data = [
            9,
            'test',
            [1, 3, 2],
            {'foo': 'bar', 'one': 'two'},
            {'name': 'Aristotelis', 'type': 'user'},
        ]

        for i, value in enumerate(data):
            wrapped = wrap._wrap(value)
            expected_type = self.expected[i]
            self.assertIsInstance(wrapped, expected_type)

    def test_iteration(self):
        """_WrapMixin must return correct data types when being
        iterated over.
        """
        data = [
            -3,
            'foo',
            [8, 0, 4, -2],
            {'test': 12, 'baz': 15},
            {'key': 'somekey', 'type': 'comment'},
        ]
        wrap_list = WrapList(data, mixcloud=self.mixcloud)

        for i, wrapped in enumerate(wrap_list):
            expected_type = self.expected[i]
            self.assertIsInstance(wrapped, expected_type)
