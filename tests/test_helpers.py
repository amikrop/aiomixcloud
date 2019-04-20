import asyncio

from tests.mock import AsyncContextManagerMock
from tests.synced import SyncedTestCase
from tests.verbose import VerboseTestCase


class TestAsyncContextManagerMock(SyncedTestCase):
    """Test `AsyncContextManagerMock`."""

    async def test_mock(self):
        """`AsyncContextManagerMock` must return its `aenter` attribute
        when used in asynchronous context management.
        """
        target = object()
        mock = AsyncContextManagerMock()
        mock.aenter = target
        async with mock as result:
            self.assertEqual(result, target)


class TestSyncedTestCase(SyncedTestCase):
    """Test `SyncedTestCase`."""

    class TestClass(SyncedTestCase):
        """Test class inheriting from `SyncedTestCase`."""

        def synchronous(self):
            """Synchronous method."""
            return 1

        async def asynchronous(self):
            """Asynchronous method."""
            return 2

        async def kept_asynchronous(self):
            """Asynchronous method whose `_async` attribute is set
            to True.
            """
            return 3

        kept_asynchronous._async = True

    @classmethod
    def setUpClass(cls):
        """Store test class instance."""
        cls.test = cls.TestClass()

    def test_synchronous(self):
        """`SyncedTestCase`'s synchronous methods must be left
        unchanged.
        """
        self.assertFalse(asyncio.iscoroutinefunction(self.test.synchronous))
        result = self.test.synchronous()
        self.assertEqual(result, 1)

    def test_asynchronous(self):
        """`SyncedTestCase`'s coroutine methods must be turned into
        synchronous ones.
        """
        self.assertFalse(asyncio.iscoroutinefunction(self.test.asynchronous))
        result = self.test.asynchronous()
        self.assertEqual(result, 2)

    async def test_kept_asynchronous(self):
        """`SyncedTestCase`'s coroutine methods with their `_async`
        attribute set to True, must be left unchanged.
        """
        self.assertTrue(
            asyncio.iscoroutinefunction(self.test.kept_asynchronous))
        result = await self.test.kept_asynchronous()
        self.assertEqual(result, 3)


class TestVerboseTestCase(VerboseTestCase):
    """Test `VerboseTestCase`."""

    def test_short_description(self):
        """`VerboseTestCase.shortDescription` must return the full
        currently tested method's docstring, without leading space
        in any line and without the last, blank, line.
        """
        class TestClass(VerboseTestCase):
            """Test class inheriting from `VerboseTestCase`."""

            def test_method(self):
                """This is a multiline docstring of a test method.
                Here comes the second line of the docstring.
                """

        test = TestClass('test_method')
        result = test.shortDescription()
        self.assertEqual(result, 'This is a multiline docstring '
                                 'of a test method.\nHere comes the '
                                 'second line of the docstring.')
