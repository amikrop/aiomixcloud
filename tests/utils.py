from unittest.mock import MagicMock


class AsyncContextManagerMock(MagicMock):
    """MagicMock supporting asynchronous context management."""

    async def __aenter__(self):
        """Return value that can be set while mocking."""
        return self.aenter

    async def __aexit__(self, *args):
        """End asynchronous context management."""


def configure_mock_session(mock_session_class, coroutine):
    """Return a mock session object out of the `mock_session_class`
    mock class, with proper asynchronous context management behavior.
    """
    async def close():
        """Dumy coroutine function."""

    mock_session = mock_session_class.return_value
    mock_session.get = AsyncContextManagerMock()
    mock_session.get.return_value.aenter.json.return_value = coroutine()
    mock_session.close.return_value = close()
    return mock_session
