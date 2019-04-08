"""
API access authorization
~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the class for Mixcloud API OAuth authorization.
Specifically:

    - :class:`MixcloudOAuth`, producing authorization URLs and
      trading OAuth codes for access tokens.
"""

import aiohttp
import yarl

from aiomixcloud.constants import OAUTH_ROOT
from aiomixcloud.exceptions import MixcloudOAuthError


class MixcloudOAuth:
    """Mixcloud OAuth authorization

    By having :attr:`client_id` and :attr:`redirect_uri` set,
    a :class:`MixcloudOAuth` object provides :attr:`authorization_url`,
    a URL to forward the end user to, where they will be able to
    "allow the application access to their data".
    It also provides the :meth:`access_token` method, which trades
    an OAuth code for an access token (requiring :attr:`client_secret`
    as well as the previously mentionted attributes).
    """

    #: Default Mixcloud OAuth root URL
    oauth_root = OAUTH_ROOT

    def __init__(self, oauth_root=oauth_root, *,
                 client_id=None, client_secret=None,
                 redirect_uri=None, raise_exceptions=None, mixcloud=None):
        """Store instance attributes."""
        #: Base URL for OAuth-related requests
        self._oauth_root = oauth_root
        #: Client ID, provided by Mixcloud
        self.client_id = client_id
        #: Client secret, provided by Mixcloud
        self.client_secret = client_secret
        #: Redirect URI, chosen by the developer
        self.redirect_uri = redirect_uri
        #: Whether to raise an exception when API responds
        #: with an error message.  If not specified, use the respective
        #: setting of the :attr:`mixcloud` attribute.  If that
        #: attribute is not specified, default to ``False``.
        self._raise_exceptions = raise_exceptions
        #: The :class:`~aiomixcloud.core.Mixcloud` object whose session
        #: will be used to make the request from.  If ``None``, a new
        #: session will be created for the access token request.
        self.mixcloud = mixcloud

    def _check(self):
        """Check that :attr:`client ID <client_id>` and
        :attr:`redirect URI <redirect_uri>` have been set.
        """
        assert self.client_id is not None, 'client_id must be set'
        assert self.redirect_uri is not None, 'redirect_uri must be set'

    def _build_url(self, segment):
        """Return a :class:`~yarl.URL` consisting of
        :attr:`OAuth root <_oauth_root>`, followed by `segment`.
        """
        return yarl.URL(self._oauth_root) / segment

    @property
    def authorization_url(self):
        """Return authorization URL."""
        self._check()

        params = {'client_id': self.client_id,
                  'redirect_uri': self.redirect_uri}

        url = self._build_url('authorize')
        final_url = url.with_query(params)
        return str(final_url)

    async def access_token(self, code):
        """Send OAuth `code` to server and get an access token.  If
        fail raise :class:`~aiomixcloud.exceptions.MixcloudOAuthError`
        in case this is the setting
        (:attr:`self._raise_exceptions <_raise_exceptions>` or
        :attr:`self.mixcloud._raise_exceptions`), otherwise return
        ``None``.
        """
        self._check()
        assert self.client_secret is not None, 'client_secret must be set'

        params = {'client_id': self.client_id,
                  'redirect_uri': self.redirect_uri,
                  'client_secret': self.client_secret,
                  'code': code}

        url = self._build_url('access_token')
        if self.mixcloud is None:
            # No Mixcloud instance stored, start a new session.
            session = aiohttp.ClientSession()
        else:
            session = self.mixcloud._session
        async with session.get(url, params=params) as response:
            data = await response.json()

        # If started a new session, close it.
        if self.mixcloud is None:
            await session.close()

        try:
            return data['access_token']
        except KeyError:
            if self._raise_exceptions is None:
                # Own setting not specified.  If a Mixcloud instance
                # is stored, act according to its setting.
                if (self.mixcloud is not None
                        and self.mixcloud._raise_exceptions):
                    raise MixcloudOAuthError(data) from None
            elif self._raise_exceptions:
                # Own setting specified and dictates to
                # raise exception.
                raise MixcloudOAuthError(data) from None
        # No setting to raise exception.
        return None
