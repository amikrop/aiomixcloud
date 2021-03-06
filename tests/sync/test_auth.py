from unittest.mock import patch

import yarl

from aiomixcloud import MixcloudOAuthError
from aiomixcloud.sync import MixcloudOAuthSync

from tests.auth import TestMixcloudOAuthMixin, \
                       configure_mock_session, make_mock_mixcloud
from tests.verbose import VerboseTestCase


class TestMixcloudOAuthSync(TestMixcloudOAuthMixin, VerboseTestCase):
    """Test `MixcloudOAuthSync`."""

    mixcloud_oauth_class = MixcloudOAuthSync

    def test_access_token(self):
        """`MixcloudOAuthSync.access_token` must return an access token
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
