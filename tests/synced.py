import asyncio
from functools import wraps

from tests.verbose import VerboseTestCase


def _synced(method):
    """Return a blocking version of coroutine `method`."""
    @wraps(method)
    def wrapper(*args, **kwargs):
        """Wait for coroutine `method` to complete."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(method(*args, **kwargs))
    return wrapper


class SyncedTestCase(VerboseTestCase):
    """Testcase with all of its coroutine methods turned into
    synchronous (i.e blocking) methods.
    """

    def __init__(self, *args):
        """Turn all of coroutine methods into synchronous ones."""
        super().__init__(*args)
        for name in dir(self):
            attribute = getattr(self, name)
            if (asyncio.iscoroutinefunction(attribute)
                    and not hasattr(attribute, '_async')):
                setattr(self, name, _synced(attribute))
