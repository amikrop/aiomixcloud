from unittest.mock import patch

from aiomixcloud import Mixcloud

from tests.synced import SyncedTestCase
from tests.utils import AsyncContextManagerMock


class TestMixcloud(SyncedTestCase):
    """Test `Mixcloud`."""

    @classmethod
    def setUpClass(cls):
        """Create and store patcher."""
        cls.patcher = patch('aiohttp.ClientSession', autospec=True)

    def setUp(self):
        """Start patcher, store created mock class and set a noop as
        its `close` method."""
        async def coroutine():
            """Dummy coroutine function."""

        self.mock_session_class = self.patcher.start()
        self.mock_session_class.return_value.close.return_value = coroutine()

    def tearDown(self):
        """Stop patcher."""
        self.patcher.stop()

    async def test_process_response(self):
        """"""
        result_dict = {'username': 'john', 'key': '/john/', 'type': 'user'}

        async def coroutine():
            """"""
            return result_dict

        mock_session = self.mock_session_class.return_value
        mock_session.get = AsyncContextManagerMock()
        response = mock_session.get.return_value.aenter
        response.json.return_value = coroutine()

        async with Mixcloud() as mixcloud:
            result = await mixcloud._process_response(response)
            response.json.assert_called_once_with(
                loads=mixcloud._json_decode, content_type=None)
        self.assertEqual(result, result_dict)
