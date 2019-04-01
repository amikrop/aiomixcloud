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
        some_resource = await mixcloud.get(some_key)

For more details see the `usage page <https://aiomixcloud.readthedocs.io>`_
of the `documentation <https://aiomixcloud.readthedocs.io>`_.

License
-------

Distributed under the `MIT License
<https://github.com/amikrop/aiomixcloud/blob/master/LICENSE>`_.
