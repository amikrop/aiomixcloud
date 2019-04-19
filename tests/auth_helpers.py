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
