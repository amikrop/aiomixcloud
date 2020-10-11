from unittest.mock import Mock


class AsyncContextManagerMock(Mock):
    """Mock supporting asynchronous context management."""

    async def __aenter__(self):
        """Return value that can be set while mocking."""
        return self.aenter

    async def __aexit__(self, *args):
        """End asynchronous context management."""
