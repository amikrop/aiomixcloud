from unittest.mock import patch

import yarl

from aiomixcloud import MixcloudOAuthError
from aiomixcloud.auth import MixcloudOAuth

from tests.auth import TestMixcloudOAuthMixin, \
                       configure_mock_session, make_mock_mixcloud
from tests.synced import SyncedTestCase


class TestMixcloudOAuth(TestMixcloudOAuthMixin, SyncedTestCase):
    """Test `MixcloudOAuth`."""

    mixcloud_oauth_class = MixcloudOAuth

    async def test_access_token(self):
        """`MixcloudOAuth.access_token` must return an access token
        after having sent a valid OAuth code.
        """
        auth = MixcloudOAuth(client_id='ah3',
                             redirect_uri='test.com', client_secret='uq8')
        with patch('aiohttp.ClientSession', autospec=True) as MockSession:
            async def coroutine():
                """Return an access token after supposedly successful
                OAuth transaction.
                """
                return {'access_token': 'k4jw'}

            mock_session = configure_mock_session(MockSession, coroutine)
            result = await auth.access_token('acb')

            mock_session.get.assert_called_once_with(
                yarl.URL('https://www.mixcloud.com/oauth/access_token'),
                params={'client_id': 'ah3', 'redirect_uri': 'test.com',
                        'client_secret': 'uq8', 'code': 'acb'})
            mock_session.close.assert_called_once_with()
        self.assertEqual(result, 'k4jw')

    async def test_access_token_mixcloud_instance(self):
        """`MixcloudOAuth.access_token` must return an access token
        using the stored Mixcloud instance when there is one available,
        after having sent a valid OAuth code.
        """
        async def coroutine():
            """Return an access token after supposedly successful
            OAuth transaction.
            """
            return {'access_token': 'j39m'}

        mock_mixcloud = make_mock_mixcloud(coroutine)

        auth = MixcloudOAuth(client_id='cj2', redirect_uri='foo.org',
                             client_secret='8k3', mixcloud=mock_mixcloud)
        result = await auth.access_token('nfe')

        mock_mixcloud._session.get.assert_called_once_with(
            yarl.URL('https://www.mixcloud.com/oauth/access_token'),
            params={'client_id': 'cj2', 'redirect_uri': 'foo.org',
                    'client_secret': '8k3', 'code': 'nfe'})
        self.assertEqual(result, 'j39m')

    async def test_access_token_invalid(self):
        """`MixcloudOAuth.access_token` must raise AssertionError when
        `client_id`, `redirect_uri` or `client_secret` is not set.
        """
        values = [
            {'client_id': 'mm39d6fr',
             'redirect_uri': 'https://baz.net/oauth'},
            {'client_id': 'jsoe2rs4',
             'client_secret': 'is4je'},
            {'redirect_uri': 'https://test.com/a',
             'client_secret': 'mm39d6fr'},
        ]
        with patch('aiohttp.ClientSession.get', autospec=True):
            for params in values:
                auth = MixcloudOAuth(**params)
                with self.assertRaises(AssertionError):
                    await auth.access_token('foo')

    async def test_access_token_failure(self):
        """`MixcloudOAuth.access_token` must return None when
        authorization fails and both `_raise_exceptions` and `mixcloud`
        are None.
        """
        auth = MixcloudOAuth(client_id='jvs',
                             redirect_uri='abc.com', client_secret='4k9')
        with patch('aiohttp.ClientSession', autospec=True) as MockSession:
            async def coroutine():
                """Do not include an access token in return value,
                after supposedly failed OAuth transaction.
                """
                return {}

            configure_mock_session(MockSession, coroutine)
            result = await auth.access_token('ikq')

        self.assertIsNone(result)

    async def test_access_token_failure_raise_exception(self):
        """`MixcloudOAuth.access_token` must raise MixcloudOAuthError
        when authorization fails and `_raise_exceptions` is True.
        """
        async def coroutine():
            """Do not include an access token in return value,
            after supposedly failed OAuth transaction.
            """
            return {}

        mock_mixcloud = make_mock_mixcloud(coroutine)
        mock_mixcloud._raise_exceptions = False
        auth = MixcloudOAuth(client_id='owd',
                             redirect_uri='n4o.com', client_secret='83g',
                             raise_exceptions=True, mixcloud=mock_mixcloud)

        with self.assertRaises(MixcloudOAuthError):
            await auth.access_token('hvr')

    async def test_access_token_failure_raise_exception_false(self):
        """`MixcloudOAuth.access_token` must return None when
        authorization fails and `_raise_exceptions` is False.
        """
        auth = MixcloudOAuth(client_id='e8f', redirect_uri='foo.net',
                             client_secret='cc7', raise_exceptions=False)
        with patch('aiohttp.ClientSession', autospec=True) as MockSession:
            async def coroutine():
                """Do not include an access token in return value,
                after supposedly failed OAuth transaction.
                """
                return {}

            configure_mock_session(MockSession, coroutine)
            result = await auth.access_token('5ut')

        self.assertIsNone(result)

    async def test_access_token_failure_mixcloud_raise_exception(self):
        """`MixcloudOAuth.access_token` must raise MixcloudOAuthError
        when authorization fails and `_raise_exceptions` is None and
        `mixcloud._raise_exceptions` is True.
        """
        async def coroutine():
            """Do not include an access token in return value,
            after supposedly failed OAuth transaction.
            """
            return {}

        mock_mixcloud = make_mock_mixcloud(coroutine)
        auth = MixcloudOAuth(client_id='pse', redirect_uri='baz.org',
                             client_secret='32p', mixcloud=mock_mixcloud)
        with self.assertRaises(MixcloudOAuthError):
            await auth.access_token('plv')
