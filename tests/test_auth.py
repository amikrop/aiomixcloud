from aiomixcloud.auth import MixcloudOAuth

from tests.synced import SyncedTestCase


class TestMixcloudOAuth(SyncedTestCase):
    """Test `MixcloudOAuth`."""

    def test_authorization_url_arguments(self):
        """`MixcloudOAuth`'s `authorization_url` property must return
        the correct result when `client_id` and `redirect_uri` are
        passed as arguments during instantiation.
        """
        client_id = 'dk3054ha'
        redirect_uri = 'http://foo.com/code/'
        auth = MixcloudOAuth(client_id=client_id, redirect_uri=redirect_uri)
        self.assertEqual(
            auth.authorization_url,
            f'https://www.mixcloud.com/oauth/authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_set_attributes(self):
        """`MixcloudOAuth`'s `authorization_url` property must return
        the correct result when `client_id` and `redirect_uri` are
        set after instantiation.
        """
        client_id = 'o40dk309c'
        redirect_uri = 'https://example.com/store'
        auth = MixcloudOAuth()
        auth.client_id = client_id
        auth.redirect_uri = redirect_uri
        self.assertEqual(
            auth.authorization_url,
            f'https://www.mixcloud.com/oauth/authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_custom_root(self):
        """`MixcloudOAuth`'s `authorization_url` property must return
        the correct result when passing a custom `oauth_root` during
        instantiation.
        """
        oauth_root = 'https://mixcloud.com/auth/'
        client_id = '0suf43kj'
        redirect_uri = 'http://baz.org/foo'
        auth = MixcloudOAuth(oauth_root, client_id=client_id)
        auth.redirect_uri = redirect_uri
        self.assertEqual(
            auth.authorization_url,
            f'{oauth_root}authorize?client_id={client_id}'
            f'&redirect_uri={redirect_uri}')

    def test_authorization_url_invalid(self):
        """`MixcloudOAuth`'s `authorization_url` property must raise
        AssertionError when `client_id` or `redirect_uri` is not set.
        """
        values = [
            {},
            {'client_id': 'ar0495jd1w'},
            {'redirect_uri': 'https://example.com/store'},
        ]
        for params in values:
            auth = MixcloudOAuth(**params)
            with self.assertRaises(AssertionError):
                auth.authorization_url
