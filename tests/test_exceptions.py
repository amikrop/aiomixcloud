from aiomixcloud.exceptions import MixcloudError, MixcloudOAuthError

from tests.verbose import VerboseTestCase


class TestMixcloudError(VerboseTestCase):
    """Test `MixcloudError`."""

    def test_str(self):
        """`MixcloudError` must be correctly represented as
        a string.
        """
        error = MixcloudError(
            {'error': {'type': 'FooException',
                       'message': 'A Foo exception occurred'}})
        self.assertEqual(str(error), 'FooException: A Foo exception occurred')

    def test_extra(self):
        """`MixcloudError` must be correctly represented as
        a string, when extra information exists.
        """
        error = MixcloudError(
            {'error': {'message': 'An exception occurred',
                       'foo': 'bar', 'test': 'hello there', 'empty': ''}})
        self.assertEqual(str(error),
                         'An exception occurred (foo: bar, test: hello there)')

    def test_no_message(self):
        """`MixcloudError` must be correctly represented as
        a string, when no "message" key exists.
        """
        error = MixcloudError({'error': {'foo': 'bar baz', 'test': 'yes'}})
        self.assertEqual(str(error), '(foo: bar baz, test: yes)')

    def test_type_no_message(self):
        """`MixcloudError` must be correctly represented as
        a string, when "type" is the only existing key.
        """
        error = MixcloudError({'error': {'type': 'AuthError'}})
        self.assertEqual(str(error), 'AuthError')


class TestMixcloudOAuthError(VerboseTestCase):
    """Test `MixcloudOAuthError`."""

    def test_str(self):
        """`MixcloudOAuthError` must be correctly represented as
        a string.
        """
        error = MixcloudOAuthError({'error': 'OAuth authorization failed'})
        self.assertEqual(str(error), 'OAuth authorization failed')
