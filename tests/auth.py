from unittest.mock import Mock

from tests.mock import AsyncContextManagerMock


def configure_mock_session(mock_session_class, coroutine):
    """Return a mock session object out of the `mock_session_class`
    mock class, with proper asynchronous context management behavior,
    specified by `coroutine`.
    """
    async def close():
        """Dumy coroutine function."""

    mock_session = mock_session_class.return_value
    mock_session.get = AsyncContextManagerMock()
    mock_session.get.return_value.aenter.json.return_value = coroutine()
    mock_session.close.return_value = close()
    return mock_session


def make_mock_mixcloud(coroutine):
    """Return a mock mixcloud object with asynchronous context
    management behavior specified by `coroutine`.
    """
    mock = Mock()
    mock._session.get = AsyncContextManagerMock()
    mock._session.get.return_value.aenter.json.return_value = coroutine()
    return mock


class TestMixcloudOAuthMixin:
    """Mixin testcase for `MixcloudOAuth`-like classes."""

    def test_authorization_url_arguments(self):
        """`authorization_url` must return the correct result when
        `client_id` and `redirect_uri` are passed as arguments during
        instantiation.
        """
        client_id = 'ks76vqq0'
        redirect_uri = 'http://test.com/code/'
        auth = self.mixcloud_oauth_class(client_id=client_id,
                                         redirect_uri=redirect_uri)
        self.assertEqual(
            auth.authorization_url,
            f'https://www.mixcloud.com/oauth/authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_set_attributes(self):
        """`authorization_url` must return the correct result when
        `client_id` and `redirect_uri` are set after instantiation.
        """
        client_id = 'o40dk309c'
        redirect_uri = 'https://example.com/store'
        auth = self.mixcloud_oauth_class()
        auth.client_id = client_id
        auth.redirect_uri = redirect_uri
        self.assertEqual(
            auth.authorization_url,
            f'https://www.mixcloud.com/oauth/authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_custom_root(self):
        """`authorization_url` must return the correct result when
        passing a custom `oauth_root` during instantiation.
        """
        oauth_root = 'https://mixcloud.com/auth/'
        client_id = '0suf43kj'
        redirect_uri = 'http://baz.org/foo'
        auth = self.mixcloud_oauth_class(oauth_root, client_id=client_id)
        auth.redirect_uri = redirect_uri
        self.assertEqual(
            auth.authorization_url,
            f'{oauth_root}authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_invalid(self):
        """`authorization_url` must raise AssertionError when
        `client_id` or `redirect_uri` is not set.
        """
        values = [
            {'client_id': 'ar0495jd1w'},
            {'redirect_uri': 'https://example.com/store'},
        ]
        for params in values:
            auth = self.mixcloud_oauth_class(**params)
            with self.assertRaises(AssertionError):
                auth.authorization_url
