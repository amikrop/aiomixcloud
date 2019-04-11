import json
from pathlib import Path
from unittest.mock import Mock, patch

import yarl

from aiomixcloud import Mixcloud, MixcloudError
from aiomixcloud.models import AccessDict, Resource, ResourceList

from tests.mock import AsyncContextManagerMock
from tests.synced import SyncedTestCase


def urljoin(root, path):
    """Join `root` and `path` into a single URL.  `path` is expected
    not to start from a slash.
    """
    root = root.rstrip('/')
    return f'{root}/{path}'


def shortcut_list_check(method):
    """Return a wrapper that prepares before and tests after
    calling `method`.
    """
    async def wrapper(self):
        """Prepare test data, call `method` and assert about
        its result.
        """
        filename = Path('tests') / 'fixtures' / 'comments.json'
        with filename.open() as f:
            self.shortcut_data = json.load(f)

        async def coroutine():
            """Return sample `ResourceList`."""
            return ResourceList(self.shortcut_data, mixcloud=self.mixcloud)

        self.mixcloud.get = Mock()
        self.mixcloud.get.return_value = coroutine()

        result = await method(self)

        self.assertIsInstance(result, ResourceList)
        self.assertEqual(result.data, self.shortcut_data)

    return wrapper


class TestMixcloud(SyncedTestCase):
    """Test `Mixcloud`."""

    @classmethod
    def setUpClass(cls):
        """Store test data and create and store patcher."""
        cls.url_values = [
            ('test', 'test'),
            ('testing/', 'testing/'),
            ('/url', 'url'),
            ('/abc/', 'abc/'),
            ('one/two', 'one/two'),
            ('test/this/', 'test/this/'),
            ('/foo/bar', 'foo/bar'),
            ('/hello/there/', 'hello/there/'),
        ]
        cls.sample_dict = {'username': 'john',
                           'key': '/john/', 'type': 'user'}
        cls.patcher = patch('aiohttp.ClientSession', autospec=True)

    def setUp(self):
        """Start patcher, store mocked session object, store result of
        GET asynchronous context management and set mocked session
        object's `close` method to a noop.
        """
        async def coroutine():
            """Dummy coroutine function."""

        mock_session_class = self.patcher.start()

        self.mock_session = mock_session_class.return_value
        self.mock_session.get.return_value = AsyncContextManagerMock()
        self.response_get = self.mock_session.get.return_value.aenter
        self.mock_session.close = coroutine

        self.mixcloud = Mixcloud()

    def tearDown(self):
        """Stop patcher."""
        self.patcher.stop()

    def configure_get_json(self, coroutine):
        """Set `coroutine`'s result as return value of asynchronously
        context-managed mock session's `json` method.
        """
        self.response_get.json.return_value = coroutine()

    async def test_build_url(self):
        """`Mixcloud._build_url` must return an absolute URL consisting
        of `_api_root` and given argument.
        """
        for value, path in self.url_values:
            result = self.mixcloud._build_url(value)
            expected = urljoin(self.mixcloud._api_root, path)
            self.assertEqual(result, yarl.URL(expected))

    async def test_build_url_api_root(self):
        """`Mixcloud._build_url` must return an absolute URL consisting
        of `_api_root` and given argument, when using a custom
        `_api_root`.
        """
        async with Mixcloud('https://api.mc.com') as mixcloud:
            for value, path in self.url_values:
                result = mixcloud._build_url(value)
                expected = f'https://api.mc.com/{path}'
                self.assertEqual(result, yarl.URL(expected))

    async def test_process_response(self):
        """`Mixcloud._process_respose` must return a dict of
        received data.
        """
        @self.configure_get_json
        async def coroutine():
            """Return sample dict."""
            return self.sample_dict

        result = await self.mixcloud._process_response(self.response_get)
        self.response_get.json.assert_called_once_with(
            loads=self.mixcloud._json_decode, content_type=None)
        self.assertEqual(result, self.sample_dict)

    async def test_process_response_failure(self):
        """`Mixcloud._process_respose` must return None when JSON
        decoding fails and `_raise_exceptions` is False.
        """
        @self.configure_get_json
        async def coroutine():
            """Raise JSONDecodeError."""
            json.loads('')

        result = await self.mixcloud._process_response(self.response_get)
        self.assertIsNone(result)

    async def test_process_response_failure_raise_exception(self):
        """`Mixcloud._process_respose` must raise JSONDecodeError when
        JSON decoding fails and `_raise_exceptions` is True.
        """
        @self.configure_get_json
        async def coroutine():
            """Raise JSONDecodeError."""
            json.loads('')

        async with Mixcloud(raise_exceptions=True) as mixcloud:
            with self.assertRaises(json.JSONDecodeError):
                await mixcloud._process_response(self.response_get)

    async def check_get(self, key, result, result_type, expected=None):
        """Check that `Mixcloud.get` when called with `key` returns
        result of type `result_type` with `data` attribute equal to
        `expected`, given that `_process_response` returns `result`.
        If `expected` is not specified it is set equal to `result`.
        """
        if expected is None:
            expected = result

        @self.configure_get_json
        async def coroutine():
            """Return mock `_process_result`'s expected result."""
            return expected

        result = await self.mixcloud.get(key)

        self.mock_session.get.assert_called_once_with(
            self.mixcloud._build_url(key).with_query(metadata=1))
        self.assertIsInstance(result, result_type)
        self.assertEqual(result.data, expected)

    def test_get(self):
        """`Mixcloud.get` must, under normal circumstances,
        return a `Resource` of received data.
        """
        self.check_get('rob', self.sample_dict, Resource)

    def test_get_none(self):
        """`Mixcloud.get` must return an empty `AccessDict` when
        `_process_response` returns None.
        """
        self.check_get('/marc', None, AccessDict, {})

    def test_get_error(self):
        """`Mixcloud.get` must return an `AccessDict` of received
        data when that data has an 'error' key and `_raise_exceptions`
        is False.
        """
        self.check_get('john/', {'error': {'message': 'foo'}}, AccessDict)

    def test_get_data(self):
        """`Mixcloud.get` must return a `ResourceList` of received data
        when that data contains a 'data' key.
        """
        filename = Path('tests') / 'fixtures' / 'followers.json'
        with filename.open() as f:
            data = json.load(f)
        self.check_get('/luke/', data, ResourceList)

    async def test_get_error_raise_exception(self):
        """`Mixcloud.get` must raise a MixcloudError when received
        data has an 'error' key and `_raise_exceptions` is True.
        """
        @self.configure_get_json
        async def coroutine():
            """Return mock `_process_result`'s expected result."""
            return {'error': {'message': 'baz'}}

        async with Mixcloud(raise_exceptions=True) as mixcloud:
            with self.assertRaises(MixcloudError):
                await mixcloud.get('foo')

            self.mock_session.get.assert_called_once_with(
                mixcloud._build_url('foo').with_query(metadata=1))

    async def test_get_absolute(self):
        """`Mixcloud.get` must correctly handle absolute URLs."""
        values = [
            ('https://api.mixcloud.com/chris/followers/',
             'https://api.mixcloud.com/chris/followers/?metadata=1'),
            ('https://api.mixcloud.com/nick/cloudcasts?metadata=1',
             'https://api.mixcloud.com/nick/cloudcasts?metadata=1'),
        ]
        for value, url in values:
            @self.configure_get_json
            async def coroutine():
                """Dummy coroutine function."""

            await self.mixcloud.get(value, relative=False)

            self.mock_session.get.assert_called_with(
                yarl.URL(url))
        self.assertEqual(self.mock_session.get.call_count, len(values))

    async def test_get_params(self):
        """`Mixcloud.get` must correctly handle GET parameters."""
        @self.configure_get_json
        async def coroutine():
            """Dummy coroutine function."""

        await self.mixcloud.get('some/resource', foo='bar', height=3)
        expected = urljoin(
            self.mixcloud._api_root,
            'some/resource?foo=bar&height=3&metadata=1')

        self.mock_session.get.assert_called_once_with(
            yarl.URL(expected))

    async def check_shortcut(self, method_name, called_with, *args):
        """Check that shortcut method `method_name` works correctly."""
        async def coroutine():
            """Return sample `Resource`."""
            return Resource(self.sample_dict, mixcloud=self.mixcloud)

        self.mixcloud.get = Mock()
        self.mixcloud.get.return_value = coroutine()
        method = getattr(self.mixcloud, method_name)
        result = await method(*args)

        self.mixcloud.get.assert_called_once_with(called_with)
        self.assertIsInstance(result, Resource)
        self.assertEqual(result.data, self.sample_dict)

    def test_me(self):
        """`Mixcloud.me` must return `Mixcloud.get` called
        with 'me'.
        """
        self.check_shortcut('me', 'me')

    def test_discover(self):
        """`Mixcloud.discover` must return `Mixcloud.get` called with
        'discover/' concatenated with given tag.
        """
        self.check_shortcut('discover', 'discover/jazz', 'jazz')

    @shortcut_list_check
    async def test_popular(self):
        """`Mixcloud.popular` must return `Mixcloud.get` called with
        appropriate parameters.
        """
        result = await self.mixcloud.popular(offset=30, limit=30)
        self.mixcloud.get.assert_called_once_with(
            'popular', offset=30, limit=30)
        return result

    @shortcut_list_check
    async def test_hot(self):
        """`Mixcloud.hot` must return `Mixcloud.get` called with
        appropriate parameters.
        """
        result = await self.mixcloud.hot(page=3)
        self.mixcloud.get.assert_called_once_with(
            'popular/hot', offset=60, limit=20)
        return result

    @shortcut_list_check
    async def test_new(self):
        """`Mixcloud.new` must return `Mixcloud.get` called with
        appropriate parameters.
        """
        result = await self.mixcloud.new(since=1000, until=100000)
        self.mixcloud.get.assert_called_once_with(
            'new', since=1000, until=100000)
        return result

    @shortcut_list_check
    async def test_search(self):
        """`Mixcloud.search` must return `Mixcloud.get` called with
        appropriate parameters.
        """
        result = await self.mixcloud.search('foo', offset=90, limit=45)
        self.mixcloud.get.assert_called_once_with(
            'search', q='foo', type='cloudcast', offset=90, limit=45)
        return result
