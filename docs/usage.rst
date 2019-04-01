Usage
~~~~~

Basic usage
-----------

The library's main interface is the :class:`~aiomixcloud.core.Mixcloud` class.
Import it directly from :mod:`aiomixcloud` and use it as an asynchronous
context manager.  Pass a key (URL part corresponding to a unique API resource)
to its :meth:`~aiomixcloud.core.Mixcloud.get` method to fetch information
about that :class:`resource <aiomixcloud.models.Resource>`::

    from aiomixcloud import Mixcloud

    async with Mixcloud() as mixcloud:
        user = await mixcloud.get('bob')

Result data is available both as dictionary items and attributes::

    user.city  # 'London'
    user['favorite_count']  # 38
    user.pictures['medium']  # 'https://thumbnailer.mixcloud.com/unsafe/10...'

Datetime data gets automatically converted to
:class:`~datetime.datetime` objects::

    user.updated_time  # datetime.datetime(2018, 3, 10, 7, 32, tzinfo=tzutc())

The :meth:`~aiomixcloud.core.Mixcloud.discover` shortcut returns information
about a tag::

    tag = await mixcloud.discover('jazz')
    tag['name']  # 'Jazz shows'

The listing methods consist of:

    - :meth:`~aiomixcloud.core.Mixcloud.popular`
    - :meth:`~aiomixcloud.core.Mixcloud.hot`
    - :meth:`~aiomixcloud.core.Mixcloud.new`
    - :meth:`~aiomixcloud.core.Mixcloud.search`

and are responsible for downloading a list of resources::

    popular = await mixcloud.popular()
    popular  # <ResourceList 'Popular Cloudcasts'>

    # Index the list
    popular[0]  # <Resource: Cloudcast '/alice/pop-hits-episode-42/'>

    # Items are resources
    popular[3]['audio_length']  # 1676

    # Iterate
    for p in popular:
        p.url  # 'https://www.mixcloud.com/...'

Items of a resource list can also be accessed by their key::

    popular['chris-smith/funky-mix']  # <Resource: Cloudcast '/chris-smit...'>

The :meth:`~aiomixcloud.core.Mixcloud.search` method, which can accept a
`type` argument, among ``'cloudcast'`` (default), ``'user'`` and ``'tag'``,
returns resources matching the given term::

    rock_cloudcasts = await mixcloud.search('rock')
    johns = await mixcloud.search('john', type='user')

Listing methods can accept pagination arguments the API itself defines:
`offset`, `limit`, `since` and `until`.  The former two concern net numbers
(counts) and the latter two can be UNIX timestamps, human-readable strings or
:class:`~datetime.datetime` objects.  Alternatively, instead any of those,
a `page` argument can be specified (zero-indexed), giving 20 results per page
(unless the `per_page` argument indicates otherwise)::

    hot = await mixcloud.hot(offset=40, limit=80)
    new = await mixcloud.new(since='2018 Feb 12 13:00:00',
                             until='2019 March 28 21:15:04')
    some_jazz = await mixcloud.search('jazz', page=2)
    metal_music = await mixcloud.search('metal', page=4, per_page=30)

When responding with a :class:`resource list
<aiomixcloud.models.ResourceList>`, the API sends most of the information
for each resource, but not all of it.  That is an example of dealing with
*non-full* resources.  Again, in a resource list, some of the data included,
represent resources related to each list item, for example each item in a
cloudcast list contains information about the user who uploaded the cloudcast.
The information about that user is also incomplete, making it another case of
a non-full resource.  The :meth:`~aiomixcloud.models.Resource.load` method of
:class:`~aiomixcloud.models.Resource` objects can be used to load the full
information of a non-full resource::

    # Using `hot` from previous snippet
    some_hot_cloudcast = hot[5]
    some_hot_cloudcast.description  # raises AttributeError
    await some_hot_cloudcast.load()
    some_hot_cloudcast.description  # 'The greatest set of all time...'

:meth:`~aiomixcloud.models.Resource.load` also returns the freshly-loaded
object so it can be used in chained calls, something that can find elegant
application in `synchronous library usage <sync_>`_.

API resources can have sub-resources, or, *connections*, that is other API
resources associated with (or, "owned" by) them.  For example, a user can have
followers, i.e a user resource has `followers` as a connection, which are
other user resources themselves.  The connections of a resource become
available through methods of it, named after the respective connection names::

    peter = await mixcloud.get('peter')
    his_followers = await peter.followers()
    his_followers  # <ResourceList "Peter's followers">

    nice_cloudcast = await mixcloud.get('luke/a-nice-mix')
    comments = await nice_cloudcast.comments()
    for comment in comments:
        comment  # <Resource: Comment '/comments/cr/.../'>
        comment.comment  # 'Nice set, keep up the good work!'

Embed information and HTML code for a cloudcast can be retrieved through the
:meth:`~aiomixcloud.core.Mixcloud.embed_json` and
:meth:`~aiomixcloud.core.Mixcloud.embed_html` methods, being able to take
`width`, `height` and `color` as arguments::

    json_embed_info = await mixcloud.embed_json('someuser/the-best-mix')
    html_embed_code = await mixcloud.embed_html('someuser/the-best-mix',
                                                width=300, height=150)

`oEmbed <https://oembed.com/>`_ information for a resource (previous arguments
applicable here as well) is available through::

    oembed_info = await mixcloud.oembed(resource_key)

Authorization
-------------

Significant part of the API's functionality is available after OAuth
authorization.  The :class:`~aiomixcloud.auth.MixcloudOAuth` class assists the
process of acquiring an OAuth access token::

    from aiomixcloud.auth import MixcloudOAuth

    oauth = MixcloudOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                          redirect_uri='https://example.com/store-code')
    oauth.authorization_url  # Forward user here to prompt them to allow
                             # access to your application

Once the user allows access to your application they will be redirected to
`https://example.com/store_code?code=OAUTH_CODE` and you can use the passed
`code` GET parameter to get their access token::

    access_token = oauth.access_token(code)
    async with Mixcloud(access_token=access_token) as mixcloud:
        # Authorized use of the API here
        pass

This process can, alternatively, take place after the instantiation of
the :class:`~aiomixcloud.core.Mixcloud` class, to make use of its
session::

    async with Mixcloud() as mixcloud:
        oauth = MixcloudOAuth(client_id=CLIENT_ID,
                              client_secret=CLIENT_SECRET,
                              redirect_uri='https://example.com/store-code',
                              mixcloud=mixcloud)
        # ... After getting user's permission and storing `code` ...
        mixcloud.access_token = await oauth.access_token(code)

Apart from getting richer results from some of the API calls,
authorized usage enables access to personalized methods, concerning the
user who the access token corresponds to.  The simplest of them is
:meth:`~aiomixcloud.core.Mixcloud.me`, which gives the resource of the
access token owner `(current user)`::

    current_user = await mixcloud.me()
    current_user.username  # 'amikrop'

Authorized usage also enables *actions*, a group of methods about doing
and undoing certain actions on specific resources:

    ===============================================  =================================================
    :meth:`~aiomixcloud.core.Mixcloud.follow`        :meth:`~aiomixcloud.core.Mixcloud.unfollow`
    :meth:`~aiomixcloud.core.Mixcloud.favorite`      :meth:`~aiomixcloud.core.Mixcloud.unfavorite`
    :meth:`~aiomixcloud.core.Mixcloud.repost`        :meth:`~aiomixcloud.core.Mixcloud.unrepost`
    :meth:`~aiomixcloud.core.Mixcloud.listen_later`  :meth:`~aiomixcloud.core.Mixcloud.unlisten_later`
    ===============================================  =================================================

Each of them takes a resource key as an argument (the two methods on
the first row target a user, the rest of them target a cloudcast)::

    data = await mixcloud.follow('bob')
    data['result']['message']  # 'Now following bob'
    data = await mixcloud.unrepost('alice/fun-times-ep-25')
    data.result.success  # True

Making authorized use of the API allows uploading cloudcasts and
editing existing uploads.  Both :meth:`~aiomixcloud.core.Mixcloud.upload` and
:meth:`~aiomixcloud.core.Mixcloud.edit` share the following optional
arguments: `picture` (filename), `description` (text), `tags` (sequence of
strings), sections (sequence of mappings) and some fields available only to
pro accounts: `publish_date` (UNIX timestamp, human-readable string or
:class:`~datetime.datetime` object), `disable_comments` (boolean),
`hide_stats` (boolean) and `unlisted` (boolean).

The :meth:`~aiomixcloud.core.Mixcloud.upload` method takes two positional
arguments, `mp3` (filename) and `name` (string)::

    data = await mixcloud.upload('perfectmix.mp3', 'Perfect Mix',
                                 picture='perfectpic.jpg',
                                 description='The perfect house mix',
                                 tags=['house', 'deep'],
                                 sections=[{'chapter': 'Intro',
                                            'start_time': 0},
                                           {'artist': 'Somebody',
                                            'song': 'Some song',
                                            'start_time': 60},
                                           {'artist': 'Cool DJ',
                                            'song': 'Cool track',
                                            'start_time': 240}])
    data.result['success']  # True

:meth:`~aiomixcloud.core.Mixcloud.edit` takes a `key` positional argument and
a `name` optional argument::

    data = await mixcloud.edit('amikrop/perfect-mix', name='The Perfect Mix',
                               description='The best house mix, right for summer',
                               tags=['house', 'deep', 'summer'])
    data['result'].success  # True

Methods of :class:`~aiomixcloud.core.Mixcloud` that target a specific resource
(and thus, take a key as first argument) are also available as methods of
:class:`~aiomixcloud.models.Resource` objects::

    someone = await mixcloud.get('certainuser')
    await someone.unfollow()  # {'result': ...

    mix = await mixcloud.get('auser/acloudcast')
    await mix.favorite()  # {'result': ...

    await mix.embed_html()  # '<iframe width="100%" height=...'

    my_mix = await mixcloud.get('amikrop/perfect-mix')
    await my_mix.edit(description='The best house mix, perfect for summer!',
                      tags=['house', 'deep',
                            'summer', 'smooth'])  # {'result': ...

Those methods include the *actions*, the embedding methods and
:meth:`~aiomixcloud.core.Mixcloud.edit`.

.. _sync:

Synchronous mode
----------------

All the functionality of the package is also available for synchronous
(i.e blocking) usage.  :class:`~aiomixcloud.sync.MixcloudSync` and
:class:`~aiomixcloud.sync.MixcloudOAuthSync` provide the same interface as
their asynchronous versions, with all the coroutine methods being now classic
methods.  Context management becomes synchronous and methods of returned
objects are synchronous as well::

    from aiomixcloud.sync import MixcloudOAuthSync, MixcloudSync

    with MixcloudSync() as mixcloud:
        oauth = MixcloudOAuthSync(client_id=CLIENT_ID,
                                  client_secret=CLIENT_SECRET,
                                  redirect_uri=REDIRECT_URI,
                                  mixcloud=mixcloud)
        # ... After getting user's permission and storing `code` ...
        mixcloud.access_token = oauth.access_token(code)

        some_cloudcast = mixcloud.get('someuser/somemix')
        some_cloudcast.repost()  # {'result': ...

        # Chained calls
        some_cloudcast.similar()[0].load().picture_primary_color  # '02f102'
