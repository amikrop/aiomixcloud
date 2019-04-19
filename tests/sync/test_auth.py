from unittest.mock import patch

import yarl

from aiomixcloud import MixcloudOAuthError
from aiomixcloud.sync import MixcloudOAuthSync

from tests.auth_helpers import configure_mock_session, make_mock_mixcloud
from tests.verbose import VerboseTestCase


class TestMixcloudOAuth(VerboseTestCase):
    """Test `MixcloudOAuthSync`."""

    def test_authorization_url_arguments(self):
        """`MixcloudOAuthSync.authorization_url` must return the
        correct result when `client_id` and `redirect_uri` are passed
        as arguments during instantiation.
        """
        client_id = 'ks76vqq0'
        redirect_uri = 'http://test.com/code/'
        auth = MixcloudOAuthSync(client_id=client_id,
                                 redirect_uri=redirect_uri)
        self.assertEqual(
            auth.authorization_url,
            f'https://www.mixcloud.com/oauth/authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_set_attributes(self):
        """`MixcloudOAuthSync.authorization_url` must return the
        correct result when `client_id` and `redirect_uri` are set
        after instantiation.
        """
        client_id = 'js76bb2pi'
        redirect_uri = 'https://foo.com/store'
        auth = MixcloudOAuthSync()
        auth.client_id = client_id
        auth.redirect_uri = redirect_uri
        self.assertEqual(
            auth.authorization_url,
            f'https://www.mixcloud.com/oauth/authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_custom_root(self):
        """`MixcloudOAuthSync.authorization_url` must return the
        correct result when passing a custom `oauth_root` during
        instantiation.
        """
        oauth_root = 'https://mixcloud.com/auth/'
        client_id = 'ssku49n7'
        redirect_uri = 'http://test.org/foo'
        auth = MixcloudOAuthSync(oauth_root, client_id=client_id)
        auth.redirect_uri = redirect_uri
        self.assertEqual(
            auth.authorization_url,
            f'{oauth_root}authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_invalid(self):
        """`MixcloudOAuthSync.authorization_url` must raise
        AssertionError when `client_id` or `redirect_uri` is not set.
        """
        values = [
            {'client_id': 'di8ber5b'},
            {'redirect_uri': 'https://example.net/store'},
        ]
        for params in values:
            auth = MixcloudOAuthSync(**params)
            with self.assertRaises(AssertionError):
                auth.authorization_url

    def test_access_token(self):
        """`MixcloudOAuth.access_token` must return an access token
        after having sent a valid OAuth code.
        """
        auth = MixcloudOAuthSync(client_id='gb7',
                                 redirect_uri='test.com', client_secret='5rf')
        with patch('aiohttp.ClientSession', autospec=True) as MockSession:
            async def coroutine():
                """Return an access token after supposedly successful
                OAuth transaction.
                """
                return {'access_token': 'kc3h'}

            mock_session = configure_mock_session(MockSession, coroutine)
            result = auth.access_token('qtc')

            mock_session.get.assert_called_once_with(
                yarl.URL('https://www.mixcloud.com/oauth/access_token'),
                params={'client_id': 'gb7', 'redirect_uri': 'test.com',
                        'client_secret': '5rf', 'code': 'qtc'})
            mock_session.close.assert_called_once_with()
        self.assertEqual(result, 'kc3h')

    def test_access_token_mixcloud_instance(self):
        """`MixcloudOAuthSync.access_token` must return an access token
        using the stored Mixcloud instance when there is one available,
        after having sent a valid OAuth code.
        """
        async def coroutine():
            """Return an access token after supposedly successful
            OAuth transaction.
            """
            return {'access_token': 'jf8n'}

        mock_mixcloud = make_mock_mixcloud(coroutine)

        auth = MixcloudOAuthSync(client_id='v9a', redirect_uri='abc.org',
                                 client_secret='21p', mixcloud=mock_mixcloud)
        result = auth.access_token('k89r')

        mock_mixcloud._session.get.assert_called_once_with(
            yarl.URL('https://www.mixcloud.com/oauth/access_token'),
            params={'client_id': 'v9a', 'redirect_uri': 'abc.org',
                    'client_secret': '21p', 'code': 'k89r'})
        self.assertEqual(result, 'jf8n')

    def test_access_token_invalid(self):
        """`MixcloudOAuthSync.access_token` must raise AssertionError
        when `client_id`, `redirect_uri` or `client_secret` is not set.
        """
        values = [
            {'client_id': 'ks8b4yth',
             'redirect_uri': 'https://foo.com/oauth'},
            {'client_id': 'k47vw98i',
             'client_secret': 'e78cl'},
            {'redirect_uri': 'https://baz.com/a',
             'client_secret': 'd3dlk80h'},
        ]
        with patch('aiohttp.ClientSession.get', autospec=True):
            for params in values:
                auth = MixcloudOAuthSync(**params)
                with self.assertRaises(AssertionError):
                    auth.access_token('foo')

    def test_access_token_failure(self):
        """`MixcloudOAuthSync.access_token` must return None when
        authorization fails and both `_raise_exceptions` and `mixcloud`
        are None.
        """
        auth = MixcloudOAuthSync(client_id='jvs',
                                 redirect_uri='abc.com', client_secret='4k9')
        with patch('aiohttp.ClientSession', autospec=True) as MockSession:
            async def coroutine():
                """Do not include an access token in return value,
                after supposedly failed OAuth transaction.
                """
                return {}

            configure_mock_session(MockSession, coroutine)
            result = auth.access_token('uoz')

        self.assertIsNone(result)

    def test_access_token_failure_raise_exception(self):
        """`MixcloudOAuthSync.access_token` must raise
        MixcloudOAuthError when authorization fails and
        `_raise_exceptions` is True.
        """
        async def coroutine():
            """Do not include an access token in return value,
            after supposedly failed OAuth transaction.
            """
            return {}

        mock_mixcloud = make_mock_mixcloud(coroutine)
        mock_mixcloud._raise_exceptions = False
        auth = MixcloudOAuthSync(
            client_id='jte',
            redirect_uri='bar.com', client_secret='ln9',
            raise_exceptions=True, mixcloud=mock_mixcloud)

        with self.assertRaises(MixcloudOAuthError):
            auth.access_token('nlq')

    def test_access_token_failure_raise_exception_false(self):
        """`MixcloudOAuthSync.access_token` must return None when
        authorization fails and `_raise_exceptions` is False.
        """
        auth = MixcloudOAuthSync(client_id='8ne', redirect_uri='baz.org',
                                 client_secret='kw2', raise_exceptions=False)
        with patch('aiohttp.ClientSession', autospec=True) as MockSession:
            async def coroutine():
                """Do not include an access token in return value,
                after supposedly failed OAuth transaction.
                """
                return {}

            configure_mock_session(MockSession, coroutine)
            result = auth.access_token('ly4')

        self.assertIsNone(result)

    def test_access_token_failure_mixcloud_raise_exception(self):
        """`MixcloudOAuthSync.access_token` must raise
        MixcloudOAuthError when authorization fails and
        `_raise_exceptions` is None and `mixcloud._raise_exceptions`
        is True.
        """
        async def coroutine():
            """Do not include an access token in return value,
            after supposedly failed OAuth transaction.
            """
            return {}

        mock_mixcloud = make_mock_mixcloud(coroutine)
        auth = MixcloudOAuthSync(client_id='sc4', redirect_uri='abc.com',
                                 client_secret='1zn', mixcloud=mock_mixcloud)
        with self.assertRaises(MixcloudOAuthError):
            auth.access_token('f7f')
