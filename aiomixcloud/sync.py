"""
Synchronous operation mode
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains synchronous (i.e blocking) versions of the package
classes.  Specifically:

    - :class:`MixcloudOAuthSync`, synchronous version of
      :class:`~aiomixcloud.auth.MixcloudOAuth`, handling OAuth
      authorization.

    - :class:`MixcloudSync`, synchronous version of
      :class:`~aiomixcloud.core.Mixcloud`, handling main functionality
      coordination.
"""

import asyncio
from functools import wraps

from aiomixcloud.auth import MixcloudOAuth
from aiomixcloud.core import Mixcloud
from aiomixcloud.models import Resource, ResourceList


def _make_sync(cls, **options):
    """Return a synchronous version of `cls`, freezing `options`
    as keyword arguments to its constructor.
    """
    class Sync:
        """A synchronous version of `cls`, storing the original object,
        delegating attribute lookup to it, returning blocking versions
        of its coroutine attributes.
        """

        def __init__(self, *args, **kwargs):
            """Merge `options` with keyword arguments and store
            original object.
            """
            kwargs.update(options)
            self.__dict__['_object'] = cls(*args, **kwargs)

        def __getattr__(self, name):
            """If attribute with given `name` is a coroutine function,
            return a synchronous version of it, else return the
            original attribute.
            """
            attribute = getattr(self._object, name)
            if asyncio.iscoroutinefunction(attribute):
                @wraps(attribute)
                def sync_method(*args, **kwargs):
                    """Wait for coroutine `attribute` to complete and
                    return its result.
                    """
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(attribute(*args, **kwargs))
                return sync_method
            return attribute

        def __setattr__(self, name, value):
            """Set attribute with given `name` equal to `value`,
            on original object.
            """
            setattr(self._object, name, value)

        # Delegate special methods used by potential original objects.
        for name in ('getitem', 'iter', 'len', 'repr'):
            method_name = f'__{name}__'

            def method(self, *args, method_name=method_name):
                """Mirror original object's method with
                given `method_name`.
                """
                return getattr(self._object, method_name)(*args)

            locals()[method_name] = method

    # Update wrapped class' name-related attributes.
    for name in ('name', 'qualname'):
        attribute_name = f'__{name}__'
        value = getattr(cls, attribute_name)
        setattr(Sync, attribute_name, f'{value}Sync')

    return Sync


#: Synchronous version of :class:`~aiomixcloud.auth.MixcloudOAuth`.
MixcloudOAuthSync = _make_sync(MixcloudOAuth)

#: Synchronous version of :class:`~aiomixcloud.models.Resource`.
ResourceSync = _make_sync(Resource)

#: Synchronous version of :class:`~aiomixcloud.models.ResourceList`.
ResourceListSync = _make_sync(ResourceList)

#: Synchronous version of :class:`~aiomixcloud.core.Mixcloud`
#: without synchronous context management capabilities.
_MixcloudSync = _make_sync(Mixcloud,
                           resource_class=ResourceSync,
                           resource_list_class=ResourceListSync)


class MixcloudSync(_MixcloudSync):
    """Synchronous version of :class:`~aiomixcloud.core.Mixcloud`
    with synchronous context management capabilities.
    """

    def __enter__(self):
        """Enable context management."""
        return self

    def __exit__(self, *args):
        """Clean up."""
        self.close()
