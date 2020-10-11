"""
aiomixcloud
~~~~~~~~~~~

Mixcloud API wrapper for Python and Async IO
--------------------------------------------

*aiomixcloud* is a wrapper library for the `HTTP API
<https://www.mixcloud.com/developers/>`_ of `Mixcloud
<https://www.mixcloud.com/>`_.  It supports asynchronous operation via
`asyncio <https://docs.python.org/3/library/asyncio.html>`_ and specifically
the `aiohttp <https://aiohttp.readthedocs.io/en/stable/>`_ framework.
*aiomixcloud* tries to be abstract and independent of the API's transient
structure, meaning it is not tied to specific JSON fields and resource types.
That is, when the API changes or expands, the library should be ready to
handle it.
"""

from aiomixcloud.constants import API_ROOT, DESCRIPTION_MAX_SIZE, \
                                  MIXCLOUD_ROOT, MP3_MAX_SIZE, OAUTH_ROOT, \
                                  OEMBED_ROOT, PICTURE_MAX_SIZE, TAG_MAX_COUNT
from aiomixcloud.core import Mixcloud
from aiomixcloud.exceptions import MixcloudError, MixcloudOAuthError


__version__ = '1.0.5'
__author__ = 'Aristotelis Mikropoulos <amikrop@gmail.com>'
__license__ = 'MIT'
__url__ = 'https://github.com/amikrop/aiomixcloud'
