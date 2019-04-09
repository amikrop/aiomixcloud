import asyncio
import unittest
from functools import wraps


def _synced(method):
    """Return a blocking version of coroutine `method`."""
    @wraps(method)
    def wrapper(*args):
        """Wait for coroutine `method` to complete."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(method(*args))
    return wrapper


class SyncedTestCase(unittest.TestCase):
    """Testcase with all of its coroutine methods turned into
    synchronous (i.e blocking) methods.
    """

    def __init__(self, *args):
        """Turn all of coroutine methods into synchronous ones."""
        super().__init__(*args)
        for name in dir(self):
            attribute = getattr(self, name)
            if asyncio.iscoroutinefunction(attribute):
                setattr(self, name, _synced(attribute))
