"""
Function decorators
~~~~~~~~~~~~~~~~~~~

This module contains decorators for functions of the package.
Specifically:

    - :func:`displayed`, handling requests with varying response format
      and HTML display information by defining the proper arguments and
      passing a `dict` produced out of them to the decorated coroutine.

    - :func:`paginated`, handling pagination of resource lists by
      defining the proper arguments, checking their validity and
      passing a `dict` produced out of them to the decorated coroutine.

    - :func:`personal`, checking that `access_token` is set on the
      object which owns the decorated coroutine method, before awaiting
      it.

    - :func:`targeting`, marking the decorated coroutine as one that
      targets a specific resource identified by a key, making said
      coroutine available as a :class:`~aiomixcloud.models.Resource`
      method.

    - :func:`uploading`, handling requests that upload data to the
      server by defining the proper arguments and passing a `dict`
      produced out of them to the decorated coroutine.
"""

from functools import wraps
from os.path import getsize

from aiomixcloud.constants import DESCRIPTION_MAX_SIZE, \
                                  PICTURE_MAX_SIZE, TAG_MAX_COUNT
from aiomixcloud.datetime import format_datetime, to_timestamp


def displayed(coroutine):
    """Return a coroutine that takes arguments about desired response
    format and HTML display and makes a parameters dictionary out
    of them.  Then, it passes that dictionary to the original
    coroutine, while awaiting it.
    """
    @wraps(coroutine)
    async def wrapper(self, *args, format='json',
                      width=None, height=None, color=None):
        """Pass the non-None arguments to the wrapped coroutine,
        as a dictionary.
        """
        params = {'format': format}
        if width is not None:
            params['width'] = width
        if height is not None:
            params['height'] = height
        if color is not None:
            params['color'] = color

        return await coroutine(self, *args, params=params)

    return wrapper


def paginated(coroutine):
    """Return a coroutine that takes pagination arguments, runs checks
    on them and makes a parameters dictionary out of them.  Then, it
    passes that dictionary to the original coroutine, while
    awaiting it.
    """
    @wraps(coroutine)
    async def wrapper(self, *args, offset=None, limit=None, since=None,
                      until=None, page=None, per_page=20, **kwargs):
        """Check that `page` is not specified simultaneously with any
        of the API arguments (`offset`, `limit`, `since` and `until`).
        If `page` is set, calculate `offset` and `limit` out of it,
        using `per_page`.  Pass the non-None API arguments to the
        wrapped coroutine, as a dictionary.
        """
        message = 'page and offset/limit/since/until ' \
                  'cannot be specified simultaneously'

        assert (page is None
                or (offset is None and limit is None
                    and since is None and until is None)), message

        if page is not None:
            offset = page * per_page
            limit = per_page

        params = {}
        if offset is not None:
            params['offset'] = offset
        if limit is not None:
            params['limit'] = limit
        if since is not None:
            params['since'] = to_timestamp(since)
        if until is not None:
            params['until'] = to_timestamp(until)

        return await coroutine(self, *args, params=params, **kwargs)

    return wrapper


def personal(coroutine):
    """Return a coroutine method that checks if `access_token` is set
    on `self`.
    """
    @wraps(coroutine)
    async def wrapper(self, *args, **kwargs):
        """Check that `self.access_token` is set."""
        assert self.access_token is not None, 'access_token must be set'
        return await coroutine(self, *args, **kwargs)

    return wrapper


def targeting(coroutine):
    """Mark `coroutine` as one that targets a specific resource,
    so it can be used as a :class:`~aiomixcloud.models.Resource`
    method.
    """
    coroutine._targeting = True
    return coroutine


def uploading(coroutine):
    """Return a coroutine that takes arguments about uploading
    cloudcast-related data, runs checks on them and makes a parameters
    dictionary out of them.  Then, it passes that dictionary to the
    original coroutine, while awaiting it.
    """
    @wraps(coroutine)
    async def wrapper(self, *args, picture=None,
                      description=None, tags=None, publish_date=None,
                      disable_comments=False, hide_stats=False,
                      unlisted=False, sections=None, **kwargs):
        """Check that `picture` and `description` do not exceed the
        maximum allowed size and `tags` are no more than the maximum
        allowed count.  Pass the explicitly specified arguments to the
        wrapped coroutine, as a dictionary.  `sections` must be an
        iterable of dictionaries, whose keys names are the last part of
        the hyphen-separated string the API mentions (e.g. "artist").
        """
        params = {}

        if picture is not None:
            message = f'picture file size must be {PICTURE_MAX_SIZE} ' \
                       'bytes at most'
            assert getsize(picture) <= PICTURE_MAX_SIZE, message
            params['picture'] = picture

        if description is not None:
            message = f'description size must be {DESCRIPTION_MAX_SIZE} ' \
                       'characters at most'
            assert len(description) <= DESCRIPTION_MAX_SIZE, message
            params['description'] = description

        if tags is not None:
            message = f'an upload must have {TAG_MAX_COUNT} tags at most'
            assert len(tags) <= TAG_MAX_COUNT, message
            params['tags'] = tags

        if publish_date is not None:
            params['publish_date'] = format_datetime(publish_date)
        if disable_comments:
            params['disable_comments'] = True
        if hide_stats:
            params['hide_stats'] = True
        if unlisted:
            params['unlisted'] = True
        if sections is not None:
            params['sections'] = sections

        return await coroutine(self, *args, params=params, **kwargs)

    return wrapper
