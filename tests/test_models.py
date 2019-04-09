import json
import unittest
from collections import UserDict, UserList
from pathlib import Path
from unittest.mock import Mock

from aiomixcloud.core import Mixcloud
from aiomixcloud.models import AccessDict, AccessList, \
                               Resource, ResourceList, _WrapMixin

from tests.synced import SyncedTestCase


class MixcloudTestCaseMixin:
    """Testcase mixin with a mock Mixcloud instance available."""

    def setUp(self):
        """Store a mock Mixcloud instance."""
        self.mixcloud = Mock(_resource_class=Resource)


class MixcloudTestCase(MixcloudTestCaseMixin, unittest.TestCase):
    """Testcase with a mock Mixcloud instance available."""


class MixcloudSyncedTestCase(MixcloudTestCaseMixin, SyncedTestCase):
    """Testcase with a mock Mixcloud instance available and all of its
    coroutine methods turned into synchronous ones.
    """


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
        """`_WrapMixin` must yield data of correct types when being
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
        super().setUp()
        self.access_dict = AccessDict(
            {'foo': 3, 'bar': 8}, mixcloud=self.mixcloud)

    def test_get_item(self):
        """`AccessDict` must return respective item when accessed
        with given key.
        """
        value = self.access_dict['bar']
        self.assertEqual(value, 8)

    def test_get_item_failure(self):
        """`AccessDict` must raise KeyError when accessed with
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
        """`AccessDict` must raise AttributeError when accessing
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

    def setUp(self):
        """Store test data."""
        super().setUp()
        self.access_list = AccessList(
            [{'foo': 'bar', 'test': 'aa'},
             {'name': 'Some User', 'key': '/someuser/', 'type': 'user'}],
            mixcloud=self.mixcloud)

    def test_integer_index(self):
        """`AccessList` must return item with given integer index."""
        value = self.access_list[0]
        self.assertEqual(value, {'foo': 'bar', 'test': 'aa'})

    def test_integer_index_failure(self):
        """`AccessList` must raise IndexError when accessed with
        invalid integer index.
        """
        with self.assertRaises(IndexError):
            self.access_list[4]

    def test_str_index(self):
        """`AccessList must return `Resource`-like item with given
        `str` key as a key.
        """
        for key in ('someuser', 'someuser/', '/someuser'):
            value = self.access_list[key]
            self.assertEqual(
                value, {'name': 'Some User',
                        'key': '/someuser/', 'type': 'user'})

    def test_str_index_failure(self):
        """`AccessList must raise KeyError when accessed with str
        key not matching any of its `Resource`-like items' keys.
        """
        with self.assertRaises(KeyError):
            self.access_list['missing']


class TestResource(MixcloudSyncedTestCase):
    """Test `Resource`."""

    @classmethod
    def setUpClass(cls):
        """Store test data for `Resource.load` tests."""
        cls.data = {'username': 'john', 'name': 'John Fooer',
                    'key': '/john/', 'type': 'user', 'cloudcast_count': 6}

    def setUp(self):
        """Store test data."""
        super().setUp()
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

    async def test_targeting_failure(self):
        """`Resource` must raise AttributeError when accessed with
        a missing attribute which is not included in the "targeting"
        methods.
        """
        async with Mixcloud() as mixcloud:
            self.resource.mixcloud = mixcloud
            with self.assertRaises(AttributeError):
                self.resource.not_there

    def test_connections_existence(self):
        """`Resource` must have methods corresponding to
        its "connections".
        """
        for connection in self.connections:
            method = getattr(self.resource, connection)
            self.assertTrue(callable(method))

    async def test_connections(self):
        """`Resource`'s "connections" must return a `ResourceList`
        of respective `Resource`s.
        """
        for connection in self.connections:
            method = getattr(self.resource, connection)

            filename = Path('tests') / 'fixtures' / f'{connection}.json'
            with filename.open() as f:
                data = json.load(f)
            expected_resource_list = ResourceList(
                data, mixcloud=self.mixcloud)

            async def mock_get():
                """Return a `ResourceList` appropriate
                for `connection`.
                """
                return expected_resource_list

            self.mixcloud.get = Mock()
            self.mixcloud.get.return_value = mock_get()

            resource_list = await method()
            self.mixcloud.get.assert_called_once_with(
                f'{self.user_root}{connection}/', relative=False)
            self.assertIsInstance(resource_list, ResourceList)
            self.assertEqual(resource_list.data, expected_resource_list.data)

    async def test_load(self):
        """`Resource`'s `load` method must load all the available data,
        mark self as "full" and return it.
        """
        async def mock_get():
            """Return a `Resource` with more data, marked as "full"."""
            return Resource(self.data, full=True, mixcloud=self.mixcloud)

        self.mixcloud.get.return_value = mock_get()

        incomplete_data = self.data.copy()
        del incomplete_data['cloudcast_count']

        resource = Resource(incomplete_data, mixcloud=self.mixcloud)
        result = await resource.load()

        self.mixcloud.get.assert_called_once_with(
            '/john/', create_connections=False)
        self.assertTrue(result._full)
        self.assertEqual(result.data, self.data)
        self.assertIs(result, resource)

    async def test_load_full(self):
        """`Resource`'s `load` method must not load any data anew
        if `Resource` is already "full", unless `force` is set.
        """
        resource = Resource(self.data, full=True, mixcloud=self.mixcloud)

        async def mock_get():
            """Return the same `Resource`."""
            return resource

        self.mixcloud.get.return_value = mock_get()

        await resource.load()
        self.mixcloud.get.assert_not_called()
        self.assertEqual(resource.data, self.data)

        await resource.load(force=True)
        self.mixcloud.get.assert_called_once_with(
            '/john/', create_connections=False)
        self.assertEqual(resource.data, self.data)


class TestResourceList(MixcloudSyncedTestCase):
    """Test `ResourceList`."""

    def setUp(self):
        """Store test data."""
        super().setUp()
        filename = Path('tests') / 'fixtures' / 'comments.json'
        with filename.open() as f:
            self.data = json.load(f)
        self.resource_list = ResourceList(self.data, mixcloud=self.mixcloud)

    def test_getitem_found(self):
        """`ResourceList` must return item when indexed with
        a present key name.
        """
        value = self.resource_list['name']
        self.assertEqual(value, self.data['name'])

    def test_getitem_missing(self):
        """`ResourceList` must raise KeyError when indexed with
        a missing `str` key.
        """
        with self.assertRaises(KeyError):
            self.resource_list['not here']

    def test_getitem_delegated(self):
        """`ResourceList` must delegate indexing to its 'data' item
        when not found in self.
        """
        value = self.resource_list[1]
        self.assertIsInstance(value, Resource)
        self.assertEqual(value.data, self.data['data'][1])

    def test_getitem_delegated_missing(self):
        """`ResourceList` must raise IndexError when indexed with
        an out-of-range index.
        """
        with self.assertRaises(IndexError):
            self.resource_list[17]

    def test_iteration(self):
        """`ResourceList` must yield items of its 'data' item when
        being iterated over.
        """
        for i, item in enumerate(self.resource_list):
            self.assertIsInstance(item, Resource)
            expected_dict = self.data['data'][i]
            self.assertEqual(item.data, expected_dict)

    def test_len(self):
        """`ResourceList` must have the same length
        as its 'data' item.
        """
        value = len(self.resource_list)
        expected_length = len(self.data['data'])
        self.assertEqual(value, expected_length)

    def test_repr(self):
        """`ResourceList` must have a proper representation."""
        value = repr(self.resource_list)
        self.assertEqual(value, '<ResourceList "Comments on Bob\'s profile">')

        del self.data['name']
        resource_list = ResourceList(self.data, mixcloud=self.mixcloud)

        value = repr(resource_list)
        self.assertEqual(value, '<ResourceList>')

    async def check_navigation(self, where):
        """Check that `ResourceList`'s navigation method indicated
        by `where` returns a `ResourceList` containing data from
        the corresponding page.
        """
        url = self.data['paging'][where]

        async def mock_get():
            """Return a `ResourceList` of adjacent page."""
            return self.resource_list

        self.mixcloud.get.return_value = mock_get()

        method = getattr(self.resource_list, where)
        result = await method()
        self.mixcloud.get.assert_called_once_with(url, relative=False)
        self.assertIsInstance(result, ResourceList)
        self.assertEqual(result.data, self.resource_list.data)

    def test_previous(self):
        """`ResourceList`'s `previous` method must return a
        `ResourceList` containing data from the previous page.
        """
        self.check_navigation('previous')

    def test_next(self):
        """`ResourceList`'s `next` method must return a
        `ResourceList` containing data from the next page.
        """
        self.check_navigation('next')

    async def check_navigation_missing(self, where):
        """Check that `ResourceList`'s navigation method indicated
        by `where` returns None when the corresponding navigation
        URL is missing.
        """
        del self.data['paging'][where]
        resource_list = ResourceList(self.data, mixcloud=self.mixcloud)
        method = getattr(resource_list, where)
        result = await method()
        self.assertIsNone(result)

    def test_previous_missing(self):
        """Check that `ResourceList`'s `previous` method returns
        None when the "previous" navigation URL is missing.
        """
        self.check_navigation_missing('previous')

    def test_next_missing(self):
        """Check that `ResourceList`'s `next` method returns
        None when the "next" navigation URL is missing.
        """
        self.check_navigation_missing('next')
