import json
import os
from os.path import basename
from pathlib import Path
from tempfile import NamedTemporaryFile, mkstemp
from unittest.mock import Mock, patch

import aiohttp
import yarl
from multidict import MultiDict

from aiomixcloud import Mixcloud, MixcloudError
from aiomixcloud.models import AccessDict, Resource, ResourceList

from tests.core import TestMixcloudMixin, urljoin
from tests.mock import AsyncContextManagerMock
from tests.synced import SyncedTestCase


def shortcut_list_check(method):
    """Return a wrapper that prepares before and tests after
    awaiting `method`.
    """
    async def wrapper(self):
        """Prepare test data, await `method` and assert about
        its result.
        """
        self.shortcut_prepare()
        result = await method(self)
        self.assert_resource_list_equal(result)
    return wrapper


class TestMixcloud(TestMixcloudMixin, SyncedTestCase):
    """Test `Mixcloud`."""

    mixcloud_class = Mixcloud
    resource_class = Resource
    resource_list_class = ResourceList

    async def test_pass_session(self):
        """`Mixcloud` must store a custom session, if one is passed
        during instantiation.
        """
        session = aiohttp.ClientSession()
        async with Mixcloud(session=session) as mixcloud:
            self.assertEqual(mixcloud._session, session)

    async def test_aexit(self):
        """`Mixcloud.__aexit__` must call `close`."""
        async def coroutine():
            """Dummy coroutine function."""

        with patch('aiomixcloud.Mixcloud.close', autospec=True) as mock_close:
            mock_close.return_value = coroutine()
            async with Mixcloud() as mixcloud:
                pass
            mock_close.assert_called_once_with(mixcloud)

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

    async def check_get(self, key, value, result_type, expected=None):
        """Check that `Mixcloud.get` when called with `key` returns
        result of type `result_type` with `data` attribute equal to
        `expected`, given that `_process_response` returns `value`.
        If `expected` is not specified it is set equal to `value`.
        """
        if expected is None:
            expected = value

        @self.configure_get_json
        async def coroutine():
            """Return mock `_process_result`'s result."""
            return value

        result = await self.mixcloud.get(key)

        self.mock_session.get.assert_called_once_with(
            self.mixcloud._build_url(key).with_query(metadata=1))
        self.assertIsInstance(result, result_type)
        self.assertEqual(result.data, expected)

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

    async def test_get_access_token(self):
        """`Mixcloud.get` must include access token as a GET parameter,
        if it is not None.
        """
        @self.configure_get_json
        async def coroutine():
            """Dummy coroutine function."""

        self.mixcloud.access_token = 'fwp9'
        await self.mixcloud.get('foo/bar')
        expected = urljoin(
            self.mixcloud._api_root,
            'foo/bar?metadata=1&access_token=fwp9')

        self.mock_session.get.assert_called_once_with(
            yarl.URL(expected))

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

    async def test_get_error_raise_exception(self):
        """`Mixcloud.get` must raise a MixcloudError when received
        data has an 'error' key and `_raise_exceptions` is True.
        """
        @self.configure_get_json
        async def coroutine():
            """Return mock `_process_result`'s expected result."""
            return self.error_dict

        async with Mixcloud(raise_exceptions=True) as mixcloud:
            with self.assertRaises(MixcloudError):
                await mixcloud.get('foo')

            self.mock_session.get.assert_called_once_with(
                mixcloud._build_url('foo').with_query(metadata=1))

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

    async def check_native_result(self, value, expected):
        """Check that `_native_result` goes through `_process_response`
        and returns an `AccessDict` of expected data.
        """
        self.prepare_process_response(value)
        result = await self.mixcloud._native_result('response')

        self.mock_process_response.assert_called_once_with('response')
        self.assert_access_dict_equal(result, expected)

    check_native_result._async = True

    async def test_native_result(self):
        """`Mixcloud._native_result` must, under normal circumstances,
        return an `AccessDict` of received data.
        """
        await self.check_native_result(self.sample_dict, self.sample_dict)

    async def test_native_result_none(self):
        """`Mixcloud._native_result` must return an empty `AccessDict`
        if received None.
        """
        await self.check_native_result(None, {})

    async def test_native_result_error(self):
        """`Mixcloud._native_result` must return an `AccessDict` of
        received data, if received a dict with an 'error' key and
        `_raise_exceptions` is False.
        """
        await self.check_native_result(self.error_dict, self.error_dict)

    async def test_native_result_error_raise_exception(self):
        """`Mixcloud._native_result` must raise MixcloudError if
        received a dict with an 'error' key and `_raise_exceptions`
        is True.
        """
        self.prepare_process_response(self.error_dict)
        self.mixcloud._raise_exceptions = True

        with self.assertRaises(MixcloudError):
            await self.mixcloud._native_result('response')
        self.mock_process_response.assert_called_once_with('response')

    async def test_do_action(self):
        """`Mixcloud._do_action` must, under normal circumstances,
        make the specified HTTP method request and return an
        `AccessDict` of received data.
        """
        methods = ['post', 'delete']
        for method_name in methods:
            async def coroutine():
                """Return sample `AccessDict`."""
                return AccessDict(self.sample_dict, mixcloud=self.mixcloud)

            method = getattr(self.mock_session, method_name)
            response = self.configure_session_method(method)
            self.mixcloud.access_token = '6he8'

            mock_native_result = self.mixcloud._native_result = Mock()
            mock_native_result.return_value = coroutine()
            result = await self.mixcloud._do_action(
                'nick/mymix', 'favorite', method_name)
            expected_url = urljoin(self.mixcloud._api_root,
                                   'nick/mymix/favorite/?access_token=6he8')

            method.assert_called_once_with(yarl.URL(expected_url))
            mock_native_result.assert_called_once_with(response)
            self.assert_access_dict_equal(result, self.sample_dict)

    async def test_do_action_failure(self):
        """`Mixcloud._do_action` must raise AssertionError when
        `access_token` is not set.
        """
        with self.assertRaises(AssertionError):
            await self.mixcloud._do_action('foo', 'follow', 'post')

    async def check_make_action(self, method_name):
        """Check that `Mixcloud`'s HTTP `method` request about some
        action works corectly.
        """
        mock_do_action = self.mixcloud._do_action = Mock()
        mock_do_action.return_value = self.coroutine()
        method = getattr(self.mixcloud, f'_{method_name}_action')
        result = await method('foo', 'follow')

        mock_do_action.assert_called_once_with('foo', 'follow', method_name)
        self.assert_access_dict_equal(result, self.sample_dict)

    async def check_specific_action(self, method_name, action_name):
        """Check that `Mixcloud`'s action method `method_name` about
        action `action_name` works correctly.
        """
        attribute = f'_{method_name}_action'
        setattr(self.mixcloud, attribute, Mock())
        mock_method = getattr(self.mixcloud, attribute)
        mock_method.return_value = self.coroutine()
        action = getattr(self.mixcloud, action_name)
        result = await action('test')

        if method_name == 'delete':
            action_name = action_name[2:]
        action_name = action_name.replace('_', '-')

        mock_method.assert_called_once_with('test', action_name)
        self.assert_access_dict_equal(result, self.sample_dict)

    async def test_proper_result(self):
        """`Mixcloud._proper_result` must call `_native_result` when
        dealing with JSON data.
        """
        mock_response = Mock()
        mock_response.headers = {'content-type': 'application/javascript'}
        mock_native_result = self.mixcloud._native_result = Mock()
        mock_native_result.return_value = self.coroutine()
        result = await self.mixcloud._proper_result(mock_response)

        mock_native_result.assert_called_once_with(mock_response)
        self.assert_access_dict_equal(result, self.sample_dict)

    async def test_proper_result_text(self):
        """`Mixcloud._proper_result` must call response's `text` method
        when dealing with text data.
        """
        async def coroutine():
            """Return sample text."""
            return 'sample'

        mock_response = Mock(headers={})
        mock_response.text.return_value = coroutine()
        result = await self.mixcloud._proper_result(mock_response)

        mock_response.text.assert_called_once_with()
        self.assertEqual(result, 'sample')

    async def test_embed(self):
        """`Mixcloud._embed` must go through `_session.get` of the
        proper URL and call `_proper_result`.
        """
        mock_proper_result = self.mixcloud._proper_result = Mock()
        mock_proper_result.return_value = self.coroutine()
        result = await self.mixcloud._embed('auser/amix', height=60)

        url = urljoin(self.mixcloud._api_root, 'auser/amix/embed-json')
        self.mock_session.get.assert_called_once_with(
            yarl.URL(url), params={'height': 60})
        self.assert_access_dict_equal(result, self.sample_dict)

    async def test_embed_json(self):
        """`Mixcloud.embed_json` must call `_embed` with format='json'
        and any other arguments forwarded.
        """
        mock_embed = self.mixcloud._embed = Mock()
        mock_embed.return_value = self.coroutine()
        result = await self.mixcloud.embed_json(width=250)

        mock_embed.assert_called_once_with(format='json', width=250)
        self.assert_access_dict_equal(result, self.sample_dict)

    async def test_embed_html(self):
        """`Mixcloud.embed_html` must call `_embed` with format='html'
        and any other arguments forwarded.
        """
        async def coroutine():
            """Return sample text."""
            return 'test'

        mock_embed = self.mixcloud._embed = Mock()
        mock_embed.return_value = coroutine()
        result = await self.mixcloud.embed_html(width=300)

        mock_embed.assert_called_once_with(format='html', width=300)
        self.assertEqual(result, 'test')

    async def test_oembed(self):
        """`Mixcloud._oembed` must go through `_session.get` of the
        proper URL and call `_proper_result`.
        """
        xml = '<?xml version="1.0" encoding="utf-8"?><oembed>foo</oembed>'

        async def coroutine():
            """Return sample XML."""
            return xml

        mock_proper_result = self.mixcloud._proper_result = Mock()
        mock_proper_result.return_value = coroutine()
        result = await self.mixcloud.oembed(
            'someuser/somemix', height=120, format='xml')

        url = urljoin(self.mixcloud._mixcloud_root, 'someuser/somemix')
        self.mock_session.get.assert_called_once_with(
            self.mixcloud._oembed_root,
            params={'url': url, 'height': 120, 'format': 'xml'})
        mock_proper_result.assert_called_once_with(self.response_get)
        self.assertEqual(result, xml)

    async def check_underscore_upload(self, params, data, access_token,
                                      expected_fields, picture_filename=None):
        """Check that `Mixcloud._upload` works correctly using given
        arguments.
        """
        self.mixcloud.access_token = access_token
        response = self.configure_session_method(self.mock_session.post)
        mock_native_result = self.mixcloud._native_result = Mock()
        mock_native_result.return_value = self.coroutine()

        url = urljoin(self.mixcloud._api_root,
                      f'upload/?access_token={access_token}')
        yarl_url = yarl.URL(url)
        result = await self.mixcloud._upload(params, data, yarl_url)

        self.assertEqual(self.mock_session.post.call_count, 1)
        (call_url,), kwargs = self.mock_session.post.call_args
        kwargs = kwargs.copy()
        call_data = kwargs.pop('data')
        self.assertFalse(kwargs)
        self.assertEqual(call_url, yarl_url)
        if picture_filename is not None:
            expected_fields.insert(
                1, (MultiDict(
                        {'name': 'picture',
                         'filename': picture_filename}),
                        {}, data._fields[1][-1]))
        self.assertIsInstance(call_data, aiohttp.FormData)
        self.assertEqual(call_data._fields, expected_fields)
        mock_native_result.assert_called_once_with(response)
        self.assert_access_dict_equal(result, self.sample_dict)

    async def check_upload(self, access_token, method_name,
                           expected_params, expected_url,
                           expected_fields, mp3_filename, *args, **kwargs):
        """Check that `Mixcloud`'s method indicated by `method_name`
        works correctly, using given arguments.
        """
        self.mixcloud.access_token = access_token
        mock_upload = self.mixcloud._upload = Mock()
        mock_upload.return_value = self.coroutine()
        method = getattr(self.mixcloud, method_name)
        result = await method(*args, **kwargs)

        self.assertEqual(mock_upload.call_count, 1)
        (params, data, url), kwargs = mock_upload.call_args
        self.assertFalse(kwargs)
        self.assertEqual(params, expected_params)
        self.assertEqual(url, yarl.URL(expected_url))
        self.assertIsInstance(data, aiohttp.FormData)
        if mp3_filename is not None:
            expected_fields.append(
                (MultiDict({'name': 'mp3', 'filename': mp3_filename}),
                 {}, data._fields[1][-1]))
        self.assertEqual(data._fields, expected_fields)
        self.assert_access_dict_equal(result, self.sample_dict)

    async def test_close(self):
        """`Mixcloud.close` must call `_session.close`."""
        async def coroutine():
            """Dummy coroutine function."""

        mock_close = self.mixcloud._session.close = Mock()
        mock_close.return_value = coroutine()
        await self.mixcloud.close()
        mock_close.assert_called_once_with()
