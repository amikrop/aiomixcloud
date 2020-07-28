"""
Main functionality coordination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the class responsible for aggregating and
organizing the main functionality and usage of the package.
Specifically:

    - :class:`Mixcloud`, providing the interface of the package.
      Stores the basic configuration and preferences, holds the session
      which API calls are made from and has all the methods necessary
      to reach every endpoint of the API, as well as take advantage of
      its capabilities.
"""

from json import JSONDecodeError
from os.path import getsize

import aiohttp
import yarl

from aiomixcloud.constants import API_ROOT, MP3_MAX_SIZE, \
                                  MIXCLOUD_ROOT, OEMBED_ROOT
from aiomixcloud.decorators import displayed, paginated, \
                                   personal, targeting, uploading
from aiomixcloud.exceptions import MixcloudError
from aiomixcloud.json import MixcloudJSONDecoder
from aiomixcloud.models import AccessDict, Resource, ResourceList


class Mixcloud:
    """Asynchronous Mixcloud API handler

    This class orchestrates the interaction of the package's user with
    the Mixcloud API.  Being ready for use with no explicit
    configuration at all, as well as being capable of customized
    operation, it provides the methods to hit the API.  A common to use
    method and base for many of the rest, is the :meth:`get` method,
    which takes a "key", a URL segment corresponding to a unique API
    resource and returns a native, yet familiar and handy data
    structure representing that resource.  There, also, exist a family
    of methods, like :meth:`popular`, which receive pagination
    arguments and return a list of resources.  The class provides some
    personalized methods, that is methods which require authorization
    to run, through an access token.  These are methods like
    :meth:`follow` and :meth:`unfollow`.  In this category belong the
    methods about uploading data to the server, :meth:`upload` and
    :meth:`edit`.  Finally, there are methods about getting embedding
    information for some resource, like :meth:`embed_html`.  The class
    can be used as an asynchronous context manager to avoid having to
    call :meth:`close` explicitly, which closes the session.
    """

    #: Default Mixcloud root URL
    mixcloud_root = MIXCLOUD_ROOT

    #: Default Mixcloud API root URL
    api_root = API_ROOT

    #: Default Mixcloud oEmbed root URL
    oembed_root = OEMBED_ROOT

    #: Default JSON decoder class
    json_decoder_class = MixcloudJSONDecoder

    #: Resource model class
    resource_class = Resource

    #: Resource model list class
    resource_list_class = ResourceList

    def __init__(self, api_root=api_root, *, access_token=None,
                 mixcloud_root=mixcloud_root, oembed_root=oembed_root,
                 json_decoder_class=json_decoder_class,
                 resource_class=resource_class,
                 resource_list_class=resource_list_class,
                 raise_exceptions=False, session=None):
        """Store instance attributes.  If no `session` is given,
        start a new one.
        """
        if session is None:
            session = aiohttp.ClientSession()

        #: Base URL for all API requests
        self._api_root = api_root
        #: OAuth Access token
        self.access_token = access_token
        #: Base Mixcloud URL
        self._mixcloud_root = mixcloud_root
        #: Base URL for all oEmbed requests
        self._oembed_root = oembed_root
        #: JSON decode function
        self._json_decode = json_decoder_class().decode
        #: Class for resource model
        self._resource_class = resource_class
        #: Class for resource model list
        self._resource_list_class = resource_list_class
        #: Whether to raise an exception when API responds
        #: with error message
        self._raise_exceptions = raise_exceptions
        #: The :class:`~aiohttp.ClientSession` object to
        #: make requests from
        self._session = session

    async def __aenter__(self):
        """Enable asynchronous context management."""
        return self

    async def __aexit__(self, *args):
        """Clean up."""
        await self.close()

    @staticmethod
    def _url_join(url, segment):
        """Return a :class:`~yarl.URL` consisting of `url`, followed
        by `segment`.  Strip possibly existing leading slash of
        `segment`, for joining to work.
        """
        return yarl.URL(url) / segment.lstrip('/')

    def _build_url(self, segment):
        """Return a :class:`~yarl.URL` consisting of API root,
        followed by `segment`.
        """
        return self._url_join(self._api_root, segment)

    async def _process_response(self, response):
        """Return JSON-decoded data out of `response`.  If fail to
        decode, let :exc:`~json.JSONDecodeError` pass through in
        case :attr:`_raise_exceptions` is set, otherwise return
        ``None``.
        """
        try:
            # Pass None as content type to avoid strict
            # content type checking.
            data = await response.json(
                loads=self._json_decode, content_type=None)
        except JSONDecodeError:
            if self._raise_exceptions:
                # Let JSONDecodeError pass through.
                raise
            # Inform caller that decoding failed.
            return None
        return data

    async def get(self, url, *, relative=True,
                  create_connections=True, **params):
        """Send a GET request to API and return JSON-decoded data.
        If `relative` is ``True``, `url` is considered relative to the
        API root, otherwise it is considered as an absolute URL.
        """
        # Relative or not, either way end up with a yarl URL.
        if relative:
            yarl_url = self._build_url(url)
        else:
            yarl_url = yarl.URL(url)
        # Ask for detailed information by setting "metadata" to 1
        # in the query.
        params['metadata'] = 1
        # If an access token is available, use it.
        if self.access_token is not None:
            params['access_token'] = self.access_token

        # Use yarl's `update_query` rather than pass `params` to
        # `session.get` to avoid adding possibly duplicate query
        # parameters to the URL.
        final_url = yarl_url.update_query(params)

        async with self._session.get(final_url) as response:
            data = await self._process_response(response)

        if data is None:
            # Could not decode JSON response, return empty data.
            return AccessDict({}, mixcloud=self)
        if 'error' in data:
            if self._raise_exceptions:
                raise MixcloudError(data)
            # Error response, no resource
            return AccessDict(data, mixcloud=self)
        if 'data' in data:
            # List of resources
            return self._resource_list_class(data, mixcloud=self)
        # Single resource
        return self._resource_class(
            data, full=True,
            create_connections=create_connections, mixcloud=self)

    @personal
    async def me(self):
        """Get information about user authorized by
        used access token.
        """
        return await self.get('me')

    async def discover(self, tag):
        """Get information about `tag`."""
        return await self.get(f'discover/{tag}')

    @paginated
    async def popular(self, params):
        """Get information about popular cloudcasts."""
        return await self.get('popular', **params)

    @paginated
    async def hot(self, params):
        """Get information about hot cloudcasts."""
        return await self.get('popular/hot', **params)

    @paginated
    async def new(self, params):
        """Get information about new cloudcasts."""
        return await self.get('new', **params)

    @paginated
    async def search(self, query, params, *, type='cloudcast'):
        """Search resources of `type` by `query` and return
        found information.
        """
        return await self.get('search', q=query, type=type, **params)

    async def _native_result(self, response):
        """Wrap :meth:`_process_response` and return appropriate
        :class:`~aiomixcloud.models.AccessDict` object.
        """
        data = await self._process_response(response)

        if data is None:
            # Could not decode JSON response, return empty data.
            return AccessDict({}, mixcloud=self)
        if 'error' in data and self._raise_exceptions:
            raise MixcloudError(data)

        return AccessDict(data, mixcloud=self)

    @personal
    async def _do_action(self, url, action, method):
        """Make HTTP `method` request about `action`, to resource
        specified by `url` and return results.
        """
        # API requires URLs to end in a slash, when dealing
        # with non-GET requests.
        action = f'{action}/'
        # Form path, build absolute URL and add
        # access token GET parameter.
        absolute_url = self._build_url(url) / action
        final_url = absolute_url.with_query(access_token=self.access_token)

        # Choose appropriate HTTP method.
        make_request = getattr(self._session, method)

        async with make_request(final_url) as response:
            return await self._native_result(response)

    async def _post_action(self, url, action):
        """Make HTTP POST request about `action`, to resource
        specified by `url` and return results.
        """
        return await self._do_action(url, action, 'post')

    async def _delete_action(self, url, action):
        """Make HTTP DELETE request about `action`, to resource
        specified by `url` and return results.
        """
        return await self._do_action(url, action, 'delete')

    @targeting
    async def follow(self, user):
        """Follow `user` and return results of the request."""
        return await self._post_action(user, 'follow')

    @targeting
    async def favorite(self, cloudcast):
        """Favorite `cloudcast` and return results of the request."""
        return await self._post_action(cloudcast, 'favorite')

    @targeting
    async def repost(self, cloudcast):
        """Repost `cloudcast` and return results of the request."""
        return await self._post_action(cloudcast, 'repost')

    @targeting
    async def listen_later(self, cloudcast):
        """Add `cloudcast` to "listen later" list and
        return results of the request.
        """
        return await self._post_action(cloudcast, 'listen-later')

    @targeting
    async def unfollow(self, user):
        """Unfollow `user` and return results of the request."""
        return await self._delete_action(user, 'follow')

    @targeting
    async def unfavorite(self, cloudcast):
        """Unfavorite `cloudcast` and return results of the request."""
        return await self._delete_action(cloudcast, 'favorite')

    @targeting
    async def unrepost(self, cloudcast):
        """Unrepost `cloudcast` and return results of the request."""
        return await self._delete_action(cloudcast, 'repost')

    @targeting
    async def unlisten_later(self, cloudcast):
        """Remove `cloudcast` from "listen later" list and
        return results of the request.
        """
        return await self._delete_action(cloudcast, 'listen-later')

    async def _proper_result(self, response):
        """Return the proper kind of result, based on Content-Type
        of `response`.
        """
        content_type = response.headers.get('content-type', '')
        if 'javascript' in content_type or 'json' in content_type:
            # Handle JSON response
            return await self._native_result(response)
        # Handle non-JSON response
        return await response.text()

    @displayed
    async def _embed(self, cloudcast, params):
        """Get embed data for `cloudcast`, in desirable format
        using specified display options.
        """
        format = params.pop('format')
        url = self._build_url(cloudcast) / f'embed-{format}'

        async with self._session.get(url, params=params) as response:
            return await self._proper_result(response)

    @targeting
    async def embed_json(self, *args, **kwargs):
        """Get embed data for given cloudcast, in JSON format
        using specified display options.
        """
        return await self._embed(*args, format='json', **kwargs)

    @targeting
    async def embed_html(self, *args, **kwargs):
        """Get embed data for given cloudcast, in HTML format
        using specified display options.
        """
        return await self._embed(*args, format='html', **kwargs)

    @targeting
    @displayed
    async def oembed(self, key, params):
        """Get oEmbed data for resource identified by `key`,
        in desirable format using specified display options.
        """
        url = self._url_join(self._mixcloud_root, key)
        params['url'] = str(url)
        async with self._session.get(
                self._oembed_root, params=params) as response:
            return await self._proper_result(response)

    async def _upload(self, params, data, url):
        """Add multipart fields from `params` to possibly half-filled
        `data`, POST it to `url` and return results.
        """
        # Add possibly existing picture.
        picture = params.pop('picture', None)
        if picture is not None:
            picture_file = open(picture, 'rb')
            data.add_field('picture', picture_file)

        # Remove tags and sections from `params` to handle
        # them separately.
        tags = params.pop('tags', [])
        sections = params.pop('sections', [])

        # Add rest of the parameters.
        for k, v in params.items():
            data.add_field(k, v)

        # Add possibly existing tags.
        for i, tag in enumerate(tags):
            data.add_field(f'tags-{i}-tag', tag)

        # Add possibly existing sections.
        for i, section in enumerate(sections):
            for k, v in section.items():
                data.add_field(f'sections-{i}-{k}', str(v))

        final_url = url.with_query(access_token=self.access_token)
        async with self._session.post(final_url, data=data) as response:
            result = await self._native_result(response)

        if picture is not None:
            picture_file.close()

        return result

    @uploading
    @personal
    async def upload(self, mp3, name, params):
        """Upload file with filename indicated by `mp3`, named `name`
        and described by specified parameters.
        """
        message = f'mp3 file size must be {MP3_MAX_SIZE} bytes at most'
        assert getsize(mp3) <= MP3_MAX_SIZE, message

        url = self._build_url('upload/')

        data = aiohttp.FormData()
        data.add_field('name', name)
        with open(mp3, 'rb') as mp3_file:
            data.add_field('mp3', mp3_file)

            return await self._upload(params, data, url)

    @targeting
    @uploading
    @personal
    async def edit(self, key, params, *, name=None):
        """Edit upload identified by `key`, as described by
        specified parameters.
        """
        if '/' not in key:
            # `key` is just the cloudcast's key, without the username
            # part, build full key by fetching current user's key.
            user = await self.me()
            segment = yarl.URL(user['key'])
            key = str(segment / key)
            # Strip leading slash for joining to work.
            key = key.lstrip('/')

        url = self._build_url('upload') / key / 'edit/'

        data = aiohttp.FormData()
        if name is not None:
            data.add_field('name', name)

        return await self._upload(params, data, url)

    async def close(self):
        """Close :attr:`_session`."""
        await self._session.close()
