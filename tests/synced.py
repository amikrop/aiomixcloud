import asyncio


def synced(method):
    """Return a blocking version of coroutine `method`."""
    def wrapper(*args):
        """Wait for coroutine `method` to complete."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(method(*args))
    return wrapper
