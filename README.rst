aiomixcloud
~~~~~~~~~~~

Mixcloud API wrapper for Python and Async IO
--------------------------------------------

.. image:: https://img.shields.io/pypi/v/aiomixcloud.svg
    :target: https://pypi.org/project/aiomixcloud/
    :alt: PyPI

.. image:: https://img.shields.io/pypi/l/aiomixcloud.svg
    :target: https://pypi.org/project/aiomixcloud/
    :alt: PyPI - License

.. image:: https://img.shields.io/pypi/pyversions/aiomixcloud.svg
    :target: https://pypi.org/project/aiomixcloud/
    :alt: PyPI - Python Version

.. image:: https://codecov.io/gh/amikrop/aiomixcloud/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/amikrop/aiomixcloud
    :alt: Coverage

.. image:: https://travis-ci.org/amikrop/aiomixcloud.svg?branch=master
    :target: https://travis-ci.org/amikrop/aiomixcloud/
    :alt: Build Status

.. image:: https://readthedocs.org/projects/aiomixcloud/badge/?version=latest
    :target: https://aiomixcloud.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

*aiomixcloud* is a wrapper library for the `HTTP API
<https://www.mixcloud.com/developers/>`_ of `Mixcloud
<https://www.mixcloud.com/>`_.  It supports asynchronous operation via
`asyncio <https://docs.python.org/3/library/asyncio.html>`_ and specifically
the `aiohttp <https://aiohttp.readthedocs.io/en/stable/>`_ framework.
*aiomixcloud* tries to be abstract and independent of the API's transient
structure, meaning it is not tied to specific JSON fields and resource types.
That is, when the API changes or expands, the library should be ready to
handle it.

Installation
------------

The following Python versions are supported:

- CPython: 3.6, 3.7, 3.8
- PyPy: 3.5

Install via `pip
<https://packaging.python.org/tutorials/installing-packages/>`_:

.. code-block:: bash

    pip install aiomixcloud

Usage
-----

You can start using *aiomixcloud* as simply as:

.. code-block:: python

    from aiomixcloud import Mixcloud

    # Inside your coroutine:
    async with Mixcloud() as mixcloud:
        cloudcast = await mixcloud.get('bob/cool-mix')

        # Data is available both as attributes and items
        cloudcast.user.name
        cloudcast['pictures']['large']

        # Iterate over associated resources
        for comment in await cloudcast.comments():
            comment.url

A variety of possibilities is enabled during `authorized usage
<https://aiomixcloud.readthedocs.io/en/latest/usage.html#authorization>`_:

.. code-block:: python

    # Inside your coroutine:
    async with Mixcloud(access_token=access_token) as mixcloud:
        # Follow a user
        user = await mixcloud.get('alice')
        await user.follow()

        # Upload a cloudcast
        await mixcloud.upload('myshow.mp3', 'My Show', picture='myshow.jpg')

For more details see the `usage page
<https://aiomixcloud.readthedocs.io/en/latest/usage.html>`_
of the `documentation <https://aiomixcloud.readthedocs.io/en/latest/>`_.

License
-------

Distributed under the `MIT License
<https://github.com/amikrop/aiomixcloud/blob/master/LICENSE>`_.
