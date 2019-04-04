import asyncio
import json
import unittest
from collections import UserDict, UserList
from pathlib import Path
from unittest.mock import Mock, patch

from aiomixcloud import Mixcloud
from aiomixcloud.models import AccessDict, AccessList, \
                               Resource, ResourceList, _WrapMixin


def synced(method):
    """Return a blocking version of coroutine `method`."""
    def wrapper(argument):
        """Wait for coroutine `method` to complete."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(method(argument))
    return wrapper


class MixcloudTestCase(unittest.TestCase):
    """Testcase with a `Mixcloud` instance available."""

    @classmethod
    @synced
    async def setUpClass(cls):
        """Store a new `Mixcloud` instance."""
        cls.mixcloud = Mixcloud()

    @classmethod
    @synced
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


class TestResource(MixcloudTestCase):
    """Test `Resource`."""

    @classmethod
    def setUpClass(cls):
        """Store test data for `Resource.load` tests."""
        super().setUpClass()
        cls.data = {'username': 'john', 'name': 'John Fooer',
                    'key': '/john/', 'type': 'user', 'cloudcast_count': 6}

    def setUp(self):
        """Store test data."""
        self.user_root = 'https://api.mixcloud.com/bob/'
        data = {'username': 'bob', 'city': 'London', 'key': '/bob/',
                'metadata': {
                    'connections': {
                        'comments': f'{self.user_root}comments/',
                        'followers': f'{self.user_root}followers/',
                        'favorites': f'{self.user_root}favorites/'}},
                'type': 'user'}
        self.resource = Resource(data, full=True, mixcloud=self.mixcloud)
        self.connections = data['metadata']['connections'].keys()

    def test_repr(self):
        """`Resource` must have a proper representation."""
        value = repr(self.resource)
        self.assertEqual(value, "<Resource: User '/bob/'>")

    def test_targeting(self):
        """The "targeting" methods must be available as
        `Resource` methods.
        """
        actions = ['follow', 'favorite', 'repost', 'listen_later']
        undo_actions = [f'un{action}' for action in actions]
        targeting = (actions + undo_actions
                     + ['embed_json', 'embed_html', 'oembed', 'edit'])

        for t in targeting:
            method = getattr(self.resource, t)
            self.assertTrue(callable(method))

    def test_targeting_failure(self):
        """`Resource` must raise `AttributeError` when accessed with
        a missing attribute which is not included in the "targeting"
        methods.
        """
        with self.assertRaises(AttributeError):
            self.resource.not_there

    def test_connections_existence(self):
        """`Resource` must have methods corresponding to
        its "connections".
        """
        for connection in self.connections:
            method = getattr(self.resource, connection)
            self.assertTrue(callable(method))

    @synced
    @patch('aiomixcloud.core.Mixcloud')
    async def test_connections(self, mock_mixcloud):
        """`Resource`'s "connections" must return a `ResourceList`
        of respective `Resource`s.
        """
        for connection in self.connections:
            method = getattr(self.resource, connection)

            filename = Path('tests') / 'fixtures' / f'{connection}.json'
            with filename.open() as f:
                fixture = json.load(f)
            expected_resource_list = ResourceList(
                fixture, mixcloud=self.mixcloud)

            async def mock_get():
                """Return a `ResourceList` appropriate
                for `connection`.
                """
                return expected_resource_list

            mock_mixcloud.get = Mock()
            mock_mixcloud.get.return_value = mock_get()
            self.resource.mixcloud = mock_mixcloud

            resource_list = await method()
            mock_mixcloud.get.assert_called_once_with(
                f'{self.user_root}{connection}/', relative=False)
            self.assertIsInstance(resource_list, ResourceList)
            self.assertEqual(resource_list.data, expected_resource_list.data)

    @synced
    @patch('aiomixcloud.core.Mixcloud')
    async def test_load(self, mock_mixcloud):
        """`Resource`'s `load` method must load all the available data,
        mark self as "full" and return it.
        """
        async def mock_get():
            """Return a `Resource` with more data, marked as "full"."""
            return Resource(self.data, full=True, mixcloud=self.mixcloud)

        mock_mixcloud.get.return_value = mock_get()

        incomplete_data = self.data.copy()
        del incomplete_data['cloudcast_count']

        resource = Resource(incomplete_data, mixcloud=mock_mixcloud)
        result = await resource.load()

        mock_mixcloud.get.assert_called_once_with('/john/')
        self.assertTrue(result._full)
        self.assertEqual(result.data, self.data)
        self.assertIs(result, resource)

    @synced
    @patch('aiomixcloud.core.Mixcloud')
    async def test_load_full(self, mock_mixcloud):
        """`Resource`'s `load` method must not load any data anew
        if `Resource` is already "full", unless `force` is set.
        """
        resource = Resource(self.data, full=True, mixcloud=self.mixcloud)

        async def mock_get():
            """Return the same `Resource`."""
            return resource

        mock_mixcloud.get.return_value = mock_get()
        resource.mixcloud = mock_mixcloud

        await resource.load()
        mock_mixcloud.get.assert_not_called()
        self.assertEqual(resource.data, self.data)

        await resource.load(force=True)
        mock_mixcloud.get.assert_called_once_with('/john/')
        self.assertEqual(resource.data, self.data)
