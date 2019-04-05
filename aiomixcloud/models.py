"""
Basic data structures
~~~~~~~~~~~~~~~~~~~~~

This module contains the basic data structures used throughout
the package.  Specifically:

    - :class:`_WrapMixin`, a mixin providing type casting of
      accessed items.

    - :class:`AccessDict`, dict-like, supports accessing items
      by attribute.  Accessed items are properly wrapped.

    - :class:`AccessList`, list-like, supports accessing
      :class:`Resource` items by their "key" key.  Accessed items
      are properly wrapped.

    - :class:`Resource`, like an :class:`AccessDict` which has
      a "type" key.  Gets methods for downloading its "connections",
      that is the sub-entities "owned" by the resource.
      Mirrors methods of :class:`~aiomixcloud.core.Mixcloud` marked as
      "targeted" with their first argument as its key.  Also provides
      a :meth:`Resource.load` method to download full resource
      information in case it is partly loaded as an element of another
      API response.

    - :class:`ResourceList`, like an :class:`AccessDict` which
      delegates string indexing and iterating over, to its "data" item.
      Supports pagination through the :meth:`ResourceList.previous`
      and :meth:`ResourceList.next` methods, which return a new object
      with the respective data.
"""

from collections import UserDict, UserList
from functools import partial
from types import MethodType

from aiomixcloud.decorators import paginated


class _WrapMixin:
    """Enables returning the proper kind of object, when indexed and
    iterated over.  Produces aiomixcloud models out of dictionaries
    and lists, leaving the rest of the types intact.
    """

    def __init__(self, data, *, mixcloud):
        """Call super's `__init__` and store
        :class:`~aiomixcloud.core.Mixcloud` instance, if given one.
        """
        super().__init__(data)
        #: :class:`~aiomixcloud.models.Mixcloud` instance to pass
        #: along to contained items
        self.mixcloud = mixcloud

    def __getitem__(self, key):
        """Wrap and return item gotten by `key`."""
        item = super().__getitem__(key)
        return self._wrap(item)

    def __iter__(self):
        """Wrap yielded values."""
        for item in super().__iter__():
            yield self._wrap(item)

    def _wrap(self, item):
        """Wrap `item` with proper class.  `dict` becomes
        :class:`AccessDict`, or :class:`Resource`-like if it has
        ``"type"`` as a key.  `list` becomes :class:`AccessList`.
        The rest remain unchanged.
        """
        if isinstance(item, dict):
            if 'type' in item:
                # Item is considered an entity, make it a resource.
                return self.mixcloud._resource_class(
                    item, mixcloud=self.mixcloud)
            return AccessDict(item, mixcloud=self.mixcloud)

        if isinstance(item, list):
            return AccessList(item, mixcloud=self.mixcloud)

        return item


class AccessDict(_WrapMixin, UserDict):
    """Dict-like model which supports accessing items using keys
    as attributes.  Items are wrapped with a proper model, depending
    on their type.  Original `dict` is stored in `self.data`.
    """

    def __getattr__(self, name):
        """Try returning an item with given `name` as a key."""
        try:
            return self.__getitem__(name)
        except KeyError:
            raise AttributeError(f'{self.__class__.__name__!r} object '
                                 f'has no attribute {name!r}') from None


class AccessList(_WrapMixin, UserList):
    """List-like model which supports accessing :class:`Resource`-like
    items by matching their "key" item.  Items are wrapped with a
    proper model, depending on their type.  Original `list` is stored
    in `self.data`.
    """

    def __getitem__(self, key):
        """Try returning item by given `key`.  On failure, try to
        find and return a :class:`Resource`-like item whose their "key"
        item equals `key`.  Raise :exc:`KeyError` on failure of finding
        one.
        """
        try:
            return super().__getitem__(key)
        except TypeError:
            # `key` is probably a string, try to find a resource
            # whose key matches it.

            # Surround `key` by slashes in case it is not already
            # surrounded.
            if not key.startswith('/'):
                key = f'/{key}'
            if not key.endswith('/'):
                key = f'{key}/'

            for item in self:
                if (isinstance(item, self.mixcloud._resource_class)
                        and item['key'] == key):
                    return item
            raise KeyError(key) from None


class Resource(AccessDict):
    """Mixcloud API resource

    A resource is like an :class:`AccessDict` object which has a "type"
    key.  When a "type" key is present in an API (sub)object,
    suggesting it has a unique URL, it is considered an API resource,
    that is an individual entity (a user, a cloudcast, a tag, etc).
    A :class:`Resource` object has appropriately named methods for
    downloading information about its sub-entities ("connections").
    It also mirrors "targeted" methods of its
    :class:`~aiomixcloud.core.Mixcloud` instance, passing them its key
    as a first argument.  Targeted methods include "actions"
    (e.g :meth:`~aiomixcloud.core.Mixcloud.follow` or
    :meth:`~aiomixcloud.core.Mixcloud.unfavorite`), embed-related
    methods and :meth:`~aiomixcloud.core.Mixcloud.edit`.
    """

    def __init__(self, data, *, full=False,
                 create_connections=True, mixcloud):
        """Pass `mixcloud` to super's `__init__` and store whether
        resource is full.  If it is full and `create_connections`
        is set, create resource connections.
        """
        super().__init__(data, mixcloud=mixcloud)
        #: Whether all of resource data has been downloaded (by having
        #: accessed the detail page).
        self._full = full
        if full and create_connections:
            self._create_connections()

    def __getattr__(self, name):
        """If super fails to find an attribute named `name`, try
        to find a method of :attr:`mixcloud` with the `_targeted`
        attribute set and return a version of it with the first
        argument frozen as current object's key.
        """
        try:
            return super().__getattr__(name)
        except AttributeError:
            mixcloud_attribute = getattr(self.mixcloud, name, None)
            if hasattr(mixcloud_attribute, '_targeting'):
                # Targeting method of Mixcloud instance found,
                # freeze its first argument as own key and return it.
                return partial(mixcloud_attribute, self['key'])
            # Targeting method not found, let AttributeError
            # pass through.
            raise

    def __repr__(self):
        """Return representation string consisting of class name,
        resource type and value of the "key" key.
        """
        # Make resource type friendlier to read
        resource_type = self['type'].replace('_', ' ').title()
        return f'<{self.__class__.__name__}: {resource_type} {self["key"]!r}>'

    def _create_connections(self):
        """In case there is an item with a
        ``['metadata']['connections']`` key, create a method for each
        of its items (resource "connections") that fetches information
        about sub-entities associated with the resource (eg `comments`,
        `followers` etc).  Each of these methods is named after the
        respective connection.
        """
        try:
            connections = self['metadata']['connections']
        except KeyError:
            pass
        else:
            # Make a method for each connection of the object.
            # Use a factory function to avoid late binding.
            def make_fetcher(url):
                """Return a function that fetches information
                from `url`.
                """
                @paginated
                async def fetcher(self, params):
                    """Download sub-entities information from `url`
                    and return the relevant :class:`ResourceList`.
                    """
                    return await self.mixcloud.get(
                        url, relative=False, **params)

                return fetcher

            for name, url in connections.items():
                fetcher_function = make_fetcher(url)
                # Make produced function a method and bind it to `self`.
                method = MethodType(fetcher_function, self)
                # Make sure it has a valid identifier.
                name = name.replace('-', '_')
                setattr(self, name, method)

    async def load(self, *, force=False):
        """Load full resource information from detail page.
        Do nothing in case :attr:`_full` is ``True``, unless `force`
        is set.  Return `self`, so this can be used in chained calls.
        """
        if not self._full or force:
            full_resource = await self.mixcloud.get(
                self['key'], create_connections=False)
            self.update(full_resource)
            self._create_connections()
            self._full = True
        return self


class ResourceList(AccessDict):
    """Contains a list of resources, with paging capabilities.
    Main data is stored in the ``'data'`` item, while a ``'paging'``
    item may be present indicating URLs of the previous and next pages
    of the resource list, as well as a `'name'` item describing the
    collection.  Indexing falls back to ``self['data']`` on failure,
    while iterating over and length concern "data" straight up.
    """

    def __getitem__(self, key):
        """If `key` is not found in `self`, delegate
        to ``self['data']`` (list of contained resources).
        """
        try:
            return super().__getitem__(key)
        except KeyError:
            return self['data'].__getitem__(key)

    def __iter__(self):
        """Iterate over contained resources."""
        return self['data'].__iter__()

    def __len__(self):
        """Return count of contained resources."""
        return self['data'].__len__()

    def __repr__(self):
        """Return representation string consisting of class name
        and value of the "name" key, if it exists.
        """
        display = self.__class__.__name__
        if 'name' in self:
            display = f'{display} {self["name"]!r}'
        return f'<{display}>'

    async def _navigate(self, where):
        """Return an adjacent page of current resource list (another
        :class:`ResourceList` object) specified by `where`, or ``None``
        if it is not found.
        """
        try:
            url = self['paging'][where]
        except KeyError:
            return None
        return await self.mixcloud.get(url, relative=False)

    async def previous(self):
        """Return previous page of current resource list,
        or ``None`` if it is not found.
        """
        return await self._navigate('previous')

    async def next(self):
        """Return next page of current resource list,
        or ``None`` if it is not found.
        """
        return await self._navigate('next')
