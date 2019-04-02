import asyncio
import unittest
from collections import UserDict, UserList

from aiomixcloud import Mixcloud
from aiomixcloud.models import AccessDict, AccessList, Resource, _WrapMixin


def async_classmethod(method):
    """Return blocking version of coroutine `method`,
    making it a `classmethod`.
    """
    def wrapper(cls):
        """Wait for coroutine `method` to complete."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(method(cls))
    return classmethod(wrapper)


class MixcloudTestCase(unittest.TestCase):
    """Testcase with a `Mixcloud` instance available."""

    @async_classmethod
    async def setUpClass(cls):
        """Store `Mixcloud` instance."""
        cls.mixcloud = Mixcloud()

    @async_classmethod
    async def tearDownClass(cls):
        """Close `Mixcloud` instance."""
        await cls.mixcloud.close()


class Wrap(_WrapMixin):
    """`_WrapMixin` trivial implementation."""

    def __init__(self, mixcloud):
        """Store `Mixcloud` instance."""
        self.mixcloud = mixcloud


class WrapDict(_WrapMixin, UserDict):
    """Wrapping dictionary."""


class WrapList(_WrapMixin, UserList):
    """Wrapping list."""


class TestWrapMixin(MixcloudTestCase):
    """Test `_WrapMixin`."""

    @classmethod
    def setUpClass(cls):
        """Store test data."""
        super().setUpClass()
        cls.expected = [int, str, AccessList, AccessDict, Resource]

    def test_wrap(self):
        """`_WrapMixin._wrap` must return correct data types
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
        """`_WrapMixin` must return correct data types when being
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

    def test_indexing_sequence(self):
        """`_WrapMixin` must return correct data types when being
        indexed as a sequence.
        """
        data = [
            8,
            'hello',
            [2, 2, -1, 14],
            {'foo1': True, '4bar': False},
            {'description': 'this is the description',
             'type': 'cloudcast', 'tags': ['jazz', 'funk']},
        ]
        wrap_list = WrapList(data, mixcloud=self.mixcloud)

        for i, expected_type in enumerate(self.expected):
            wrapped = wrap_list[i]
            self.assertIsInstance(wrapped, expected_type)

    def test_indexing_mapping(self):
        """`_WrapMixin` must return correct data types when being
        indexed as a mapping.
        """
        data = {
            'aa': 21,
            'b': 'hi',
            'check': [3, 41],
            'eee': {'foo': 'test', 'f': -5},
            'xyz': {'key': 'akey', 'type': 'tag'},
        }
        wrap_dict = WrapDict(data, mixcloud=self.mixcloud)

        sorted_keys = sorted(data.keys())
        for i, key in enumerate(sorted_keys):
            wrapped = wrap_dict[key]
            expected_type = self.expected[i]
            self.assertIsInstance(wrapped, expected_type)


class TestAccessDict(MixcloudTestCase):
    """Test `AccessDict`."""

    def setUp(self):
        """Store test data."""
        self.access_dict = AccessDict(
            {'foo': 3, 'bar': 8}, mixcloud=self.mixcloud)

    def test_get_item(self):
        """`AccessDict` must return respective item when accessed
        with given key.
        """
        value = self.access_dict['bar']
        self.assertEqual(value, 8)

    def test_get_item_failure(self):
        """`AccessDict` must raise `KeyError` when accessed with
        missing key.
        """
        with self.assertRaises(KeyError):
            self.access_dict['not there']

    def test_get_item_as_attribute(self):
        """`AccessDict` must return respective item when accessing
        missing attribute named as item's key.
        """
        value = self.access_dict.foo
        self.assertEqual(value, 3)

    def test_get_item_as_attribute_failure(self):
        """`AccessDict` must raise `AttributeError` when accessing
        attribute not corresponding to any key name.
        """
        with self.assertRaises(AttributeError):
            self.access_dict.missing

    def test_present_attribute(self):
        """`AccessDict` must return attribute's value when attribute
        is present, even when having item with the same key name.
        """
        self.access_dict.bar = 15
        value = self.access_dict.bar
        self.assertEqual(value, 15)


class TestAccessList(MixcloudTestCase):
    """Test `AccessList`."""

    @classmethod
    def setUpClass(cls):
        """Store test data."""
        super().setUpClass()
        cls.access_list = AccessList(
            [{'foo': 'bar', 'test': 'aa'},
             {'name': 'Some User', 'key': '/someuser/', 'type': 'user'}],
            mixcloud=cls.mixcloud)

    def test_integer_index(self):
        """`AccessList` must return item with given integer index."""
        value = self.access_list[0]
        self.assertEqual(value, {'foo': 'bar', 'test': 'aa'})

    def test_integer_index_failure(self):
        """`AccessList` must raise `IndexError` when accessed with
        invalid integer index.
        """
        with self.assertRaises(IndexError):
            self.access_list[4]

    def test_str_index(self):
        """`AccessList must return `Resource`-like item with given
        `str` key as a key.
        """
        value = self.access_list['someuser']
        self.assertEqual(
            value, {'name': 'Some User', 'key': '/someuser/', 'type': 'user'})

    def test_str_index_failure(self):
        """`AccessList must raise `KeyError` when accessed with `str`
        key not matching any of its `Resource`-like items' keys.
        """
        with self.assertRaises(KeyError):
            self.access_list['missing']
