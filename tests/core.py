import json
import os
from os.path import basename
from pathlib import Path
from tempfile import NamedTemporaryFile, mkstemp
from unittest.mock import Mock, patch

import aiohttp
import yarl
from multidict import MultiDict

from aiomixcloud.models import AccessDict

from tests.mock import AsyncContextManagerMock


def urljoin(root, path):
    """Join `root` and `path` into a single URL.  `path` is expected
    not to start from a slash.
    """
    root = root.rstrip('/')
    return f'{root}/{path}'


class TestMixcloudMixin:
    """Mixin testcase for `Mixcloud`-like classes."""

    @classmethod
    def setUpClass(cls):
        """Store test data and create and store patcher."""
        cls.url_values = [
            ('', ''),
            ('foo', 'foo'),
            ('hello/', 'hello/'),
            ('/something', 'something'),
            ('/bar/', 'bar/'),
            ('this/that', 'this/that'),
            ('hello/world/', 'hello/world/'),
            ('/one/two', 'one/two'),
            ('/abcd/efgh/', 'abcd/efgh/'),
        ]
        cls.sample_dict = {'username': 'chris',
                           'key': '/chris/', 'type': 'user'}
        cls.error_dict = {'error': {'message': 'problem'}}
        cls.patcher = patch('aiohttp.ClientSession', autospec=True)

    def setUp(self):
        """Start patcher, store mocked session object, store result of
        GET asynchronous context management and set mocked session
        object's `close` method to a noop.
        """
        async def coroutine():
            """Return sample `AccessDict`."""
            return AccessDict(self.sample_dict, mixcloud=self.mixcloud)

        async def close():
            """Dummy coroutine function."""

        mock_session_class = self.patcher.start()

        self.mock_session = mock_session_class.return_value
        self.response_get = self.configure_session_method(
            self.mock_session.get)
        self.mock_session.close = close

        self.mixcloud = self.mixcloud_class()
        self.coroutine = coroutine

    def tearDown(self):
        """Stop patcher."""
        self.patcher.stop()

    def configure_session_method(self, method):
        """Configure `method` to return an asynchronous context
        manager and return its `__aenter__` value.
        """
        method.return_value = AsyncContextManagerMock()
        return method.return_value.aenter

    def test_url_join(self):
        """`_url_join` must return an absolute URL consisting of two
        given arguments.
        """
        values = [
            ('http://foo.com', 'testing', 'http://foo.com/testing'),
            ('https://abcd.org/', 'baz', 'https://abcd.org/baz'),
            ('http://test.com', '/hello', 'http://test.com/hello'),
            ('https://foobar.net/', '/hi', 'https://foobar.net/hi'),
            ('https://example.com/', '/foo/baz/',
             'https://example.com/foo/baz/'),
        ]
        for root, path, expected in values:
            result = self.mixcloud._url_join(root, path)
            self.assertEqual(result, yarl.URL(expected))

    def test_build_url(self):
        """`_build_url` must return an absolute URL consisting of
        `_api_root` and given argument.
        """
        for value, path in self.url_values:
            result = self.mixcloud._build_url(value)
            expected = urljoin(self.mixcloud._api_root, path)
            self.assertEqual(result, yarl.URL(expected))

    def configure_get_json(self, coroutine):
        """Set `coroutine`'s result as return value of asynchronously
        context-managed mock session's `json` method.
        """
        self.response_get.json.return_value = coroutine()

    def test_get(self):
        """`get` must, under normal circumstances, return a
        `Resource`-like object of received data.
        """
        self.check_get('rob', self.sample_dict, self.resource_class)

    def test_get_none(self):
        """`get` must return an empty `AccessDict` when
        `_process_response` returns None.
        """
        self.check_get('/marc', None, AccessDict, {})

    def test_get_error(self):
        """`get` must return an `AccessDict` of received data when that
        data has an 'error' key and `_raise_exceptions` is False.
        """
        self.check_get('john/', {'error': {'message': 'foo'}}, AccessDict)

    def test_get_data(self):
        """`get` must return a `ResourceList`-like object of received
        data when that data contains a 'data' key.
        """
        filename = Path('tests') / 'fixtures' / 'followers.json'
        with filename.open() as f:
            data = json.load(f)
        self.check_get('/luke/', data, self.resource_list_class)

    def test_me(self):
        """`me` must return `get` called with 'me'."""
        self.mixcloud.access_token = '51sq'
        self.check_shortcut('me', 'me')

    def test_discover(self):
        """`discover` must return `get` called with 'discover/'
        concatenated with given tag.
        """
        self.check_shortcut('discover', 'discover/jazz', 'jazz')

    def shortcut_prepare(self):
        """Prepare test data for a shortcut method."""
        filename = Path('tests') / 'fixtures' / 'comments.json'
        with filename.open() as f:
            self.shortcut_data = json.load(f)

        async def coroutine():
            """Return sample `ResourceList`-like object."""
            return self.resource_list_class(
                self.shortcut_data, mixcloud=self.mixcloud)

        self.mixcloud.get = Mock()
        self.mixcloud.get.return_value = coroutine()

    def assert_resource_list_equal(self, value):
        """Check that `value` is a `ResourceList`-like object with its
        `data` attribute equal to `self.shortcut_data`.
        """
        self.assertIsInstance(value, self.resource_list_class)
        self.assertEqual(value.data, self.shortcut_data)

    def prepare_process_response(self, value):
        """Configure and store mock `_process_response`."""
        async def coroutine():
            """Return result of mock `_process_response`."""
            return value

        self.mock_process_response = self.mixcloud._process_response = Mock()
        self.mock_process_response.return_value = coroutine()

    def assert_access_dict_equal(self, value, expected):
        """Assert that `value` is an `AccessDict` with its `data`
        attribute equal to `expected`.
        """
        self.assertIsInstance(value, AccessDict)
        self.assertEqual(value.data, expected)

    def test_post_action(self):
        """`_post_action` must make an HTTP POST request about
        some action.
        """
        self.check_make_action('post')

    def test_delete_action(self):
        """`_post_action` must make an HTTP DELETE request about
        some action.
        """
        self.check_make_action('delete')

    def check_post_action(self, action_name):
        """Check that POST method about action `action_name`
        works correctly.
        """
        self.check_specific_action('post', action_name)

    def check_delete_action(self, action_name):
        """Check that DELETE method about action `action_name`
        works correctly.
        """
        self.check_specific_action('delete', f'un{action_name}')

    def test_follow(self):
        """`follow` must return `_post_action` called with 'follow'."""
        self.check_post_action('follow')

    def test_favorite(self):
        """`favorite` must return `_post_action` called
        with 'favorite'.
        """
        self.check_post_action('favorite')

    def test_repost(self):
        """`repost` must return `._post_action` called
        with 'repost'.
        """
        self.check_post_action('repost')

    def test_listen_later(self):
        """`listen_later` must return `_post_action` called
        with 'listen-later'.
        """
        self.check_post_action('listen_later')

    def test_unfollow(self):
        """`unfollow` must return `_delete_action` called
        with 'follow'.
        """
        self.check_delete_action('follow')

    def test_unfavorite(self):
        """`unfavorite` must return `_delete_action` called
        with 'favorite'.
        """
        self.check_delete_action('favorite')

    def test_unrepost(self):
        """`unrepost` must return `_delete_action` called
        with 'repost'.
        """
        self.check_delete_action('repost')

    def test_unlisten_later(self):
        """`unlisten_later` must return `_delete_action` called
        with 'listen-later'.
        """
        self.check_delete_action('listen_later')

    def test_underscore_upload(self):
        """`_upload` must go through `_session.post` of the proper URL,
        form POST parameters in a proper way and call `_native_result`.
        """
        params = {'tags': ['house', 'tech'],
                  'sections': [{'artist': 'somebody', 'start_time': 20}],
                  'unlisted': True}
        data = aiohttp.FormData({'name': 'Sample Name'})
        expected_fields = [
            (MultiDict({'name': 'name'}), {}, 'Sample Name'),
            (MultiDict({'name': 'unlisted'}), {}, True),
            (MultiDict({'name': 'tags-0-tag'}), {}, 'house'),
            (MultiDict({'name': 'tags-1-tag'}), {}, 'tech'),
            (MultiDict({'name': 'sections-0-artist'}), {}, 'somebody'),
            (MultiDict({'name': 'sections-0-start_time'}), {}, '20')]

        self.check_underscore_upload(params, data, 'i36j', expected_fields)

    def test_underscore_upload_picture(self):
        """`_upload` must go through `_session.post` of the proper URL,
        form POST parameters in a proper way and call `_native_result`,
        when `picture` argument is passed.
        """
        with NamedTemporaryFile() as f:
            params = {'picture': f.name, 'tags': ['jazz', 'smooth'],
                      'sections': [{'artist': 'cool dj', 'start_time': 15}]}
            data = aiohttp.FormData({'name': 'My show'})
            expected_fields = [
                (MultiDict({'name': 'name'}), {}, 'My show'),
                (MultiDict({'name': 'tags-0-tag'}), {}, 'jazz'),
                (MultiDict({'name': 'tags-1-tag'}), {}, 'smooth'),
                (MultiDict({'name': 'sections-0-artist'}), {}, 'cool dj'),
                (MultiDict({'name': 'sections-0-start_time'}), {}, '15')]

            self.check_underscore_upload(
                params, data, '93gq', expected_fields,
                picture_filename=basename(f.name))

    def test_upload(self):
        """`upload` must work correctly, going through `_upload`."""
        _, path = mkstemp()
        try:
            url = urljoin(self.mixcloud._api_root, 'upload/')
            expected_fields = [(MultiDict({'name': 'name'}), {}, 'test')]
            self.check_upload('b69p', 'upload', {'description': 'testing'},
                              url, expected_fields, basename(path), path,
                              'test', description='testing')
        finally:
            os.remove(path)

    def test_edit(self):
        """`edit` must work correctly, going through `_upload`."""
        url = urljoin(self.mixcloud._api_root,
                      'upload/myself/mycloudcast/edit/')
        self.check_upload('mq1k', 'edit', {'tags': ['foo', 'bar']},
                          url, [], None, 'myself/mycloudcast',
                          tags=['foo', 'bar'])

    def test_edit_own_cloudcast(self):
        """`edit` must work correctly, going through `_upload`, forming
        the URL with help of data returned by `me`, when `key` does not
        include the user's key.
        """
        async def coroutine():
            """Return data containing a "key" key."""
            return {'key': 'myself'}

        mock_me = self.mixcloud.me = Mock()
        mock_me.return_value = coroutine()

        url = urljoin(self.mixcloud._api_root, 'upload/myself/mymix/edit/')
        self.check_upload('kf3p', 'edit', {'tags': ['baz']},
                          url, [], None, 'mymix', tags=['baz'])
        mock_me.assert_called_once_with()

    def test_edit_name(self):
        """`edit` must work correctly, going through `_upload`, when
        the `name` argument is passed.
        """
        url = urljoin(self.mixcloud._api_root,
                      'upload/myself/mycloudcast/edit/')
        expected_fields = [(MultiDict({'name': 'name'}), {}, 'newname')]
        self.check_upload('m9ub', 'edit', {'description': 'new description'},
                          url, expected_fields, None, 'myself/mycloudcast',
                          description='new description', name='newname')
