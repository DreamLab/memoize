.. image:: https://readthedocs.org/projects/memoize/badge/?version=latest
    :target: https://memoize.readthedocs.io/en/latest/?badge=latest

.. image:: https://travis-ci.com/DreamLab/memoize.svg?token=PCPPzZaRDc9FFFUfKaj9&branch=master
    :target: https://travis-ci.com/DreamLab/memoize

What & Why
==========

**What:** Caching library for asynchronous Python applications.

**Why:** Python deserves library that works in async world
(for instance handles `dog-piling <https://en.wikipedia.org/wiki/Cache_stampede>`_ )
and has a proper, extensible API.

Etymology
=========

*In computing, memoization or memoisation is an optimization technique
used primarily to speed up computer programs by storing the results of
expensive function calls and returning the cached result when the same
inputs occur again. (…) The term “memoization” was coined by Donald
Michie in 1968 and is derived from the Latin word “memorandum” (“to be
remembered”), usually truncated as “memo” in the English language, and
thus carries the meaning of “turning [the results of] a function into
something to be remembered.”*
~ `Wikipedia <https://en.wikipedia.org/wiki/Memoization>`_

Getting Started
===============

Installation
------------

Basic Installation
~~~~~~~~~~~~~~~~~~

To get you up & running all you need is to install:

.. code-block:: bash

   pip install py-memoize

Installation of Extras
~~~~~~~~~~~~~~~~~~~~~~

If you are going to use ``memoize`` with tornado add a dependency on extra:

.. code-block:: bash

   pip install py-memoize[tornado]

To harness the power of `ujson <https://pypi.org/project/ujson/>`_ (if JSON SerDe is used) install extra:

.. code-block:: bash

   pip install py-memoize[ujson]

Usage
-----

Provided examples use default configuration to cache results in memory.
For configuration options see `Configurability`_.

You can use ``memoize`` with both `asyncio <https://docs.python.org/3/library/asyncio.html>`_
and `Tornado <https://github.com/tornadoweb/tornado>`_ -  please see the appropriate example:

asyncio
~~~~~~~

To apply default caching configuration use:


.. code-block:: python

    import asyncio
    import random
    from memoize.wrapper import memoize


    @memoize()
    async def expensive_computation():
        return 'expensive-computation-' + str(random.randint(1, 100))


    async def main():
        print(await expensive_computation())
        print(await expensive_computation())
        print(await expensive_computation())


    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())


Tornado
~~~~~~~

If your project is based on Tornado use:

.. code-block:: python

    import random

    from tornado import gen
    from tornado.ioloop import IOLoop

    from memoize.wrapper import memoize


    @memoize()
    @gen.coroutine
    def expensive_computation():
        return 'expensive-computation-' + str(random.randint(1, 100))


    @gen.coroutine
    def main():
        result1 = yield expensive_computation()
        print(result1)
        result2 = yield expensive_computation()
        print(result2)
        result3 = yield expensive_computation()
        print(result3)


    if __name__ == "__main__":
        IOLoop.current().run_sync(main)



Features
========

Async-first
-----------

Asynchronous programming is often seen as a huge performance boost in python programming.
But with all the benefits it brings there are also new concurrency-related caveats
like `dog-piling <https://en.wikipedia.org/wiki/Cache_stampede>`_.

This library is built async-oriented from the ground-up, what manifests in, for example,
in `Dog-piling proofness`_ or `Async cache storage`_.


Tornado & asyncio support
-------------------------

No matter what are you using, build-in `asyncio <https://docs.python.org/3/library/asyncio.html>`_
or its predecessor `Tornado <https://github.com/tornadoweb/tornado>`_
*memoize* has you covered as you can use it with both.
**This may come handy if you are planning a migration from Tornado to asyncio.**

Under the hood *memoize* detects if you are using *Tornado* or *asyncio*
(by checking if *Tornado* is installed and available to import).

If have *Tornado* installed but your application uses *asyncio* IO-loop,
set ``MEMOIZE_FORCE_ASYNCIO=1`` environment variable to force using *asyncio* and ignore *Tornado* instalation.


Configurability
---------------

With *memoize* you have under control:

* timeout applied to the cached method;
* key generation strategy (see :class:`memoize.key.KeyExtractor`);
  already provided strategies use arguments (both positional & keyword) and method name (or reference);
* storage for cached entries/items (see :class:`memoize.storage.CacheStorage`);
  in-memory storage is already provided;
  for convenience of implementing new storage adapters some SerDe (:class:`memoize.serde.SerDe`) are provided;
* eviction strategy (see :class:`memoize.eviction.EvictionStrategy`);
  least-recently-updated strategy is already provided;
* entry builder (see :class:`memoize.entrybuilder.CacheEntryBuilder`)
  which has control over ``update_after``  & ``expires_after`` described in `Tunable eviction & async refreshing`_

All of these elements are open for extension (you can implement and plug-in your own).
Please contribute!

Example how to customize default config (everything gets overridden):

.. code-block:: python

    from datetime import timedelta

    from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
    from memoize.entrybuilder import ProvidedLifeSpanCacheEntryBuilder
    from memoize.eviction import LeastRecentlyUpdatedEvictionStrategy
    from memoize.key import EncodedMethodNameAndArgsKeyExtractor
    from memoize.storage import LocalInMemoryCacheStorage
    from memoize.wrapper import memoize


    @memoize(configuration=MutableCacheConfiguration
             .initialized_with(DefaultInMemoryCacheConfiguration())
             .set_method_timeout(value=timedelta(minutes=2))
             .set_entry_builder(ProvidedLifeSpanCacheEntryBuilder(update_after=timedelta(minutes=2),
                                                                  expire_after=timedelta(minutes=5)))
             .set_eviction_strategy(LeastRecentlyUpdatedEvictionStrategy(capacity=2048))
             .set_key_extractor(EncodedMethodNameAndArgsKeyExtractor(skip_first_arg_as_self=False))
             .set_storage(LocalInMemoryCacheStorage())
             )
    async def cached():
        return 'dummy'


Still, you can use default configuration which:

* sets timeout for underlying method to 2 minutes;
* uses in-memory storage;
* uses method instance & arguments to infer cache key;
* stores up to 4096 elements in cache and evicts entries according to least recently updated policy;
* refreshes elements after 10 minutes & ignores unrefreshed elements after 30 minutes.

If that satisfies you, just use default config:

.. code-block:: python

    from memoize.configuration import DefaultInMemoryCacheConfiguration
    from memoize.wrapper import memoize


    @memoize(configuration=DefaultInMemoryCacheConfiguration())
    async def cached():
        return 'dummy'


Tunable eviction & async refreshing
-----------------------------------

Sometimes caching libraries allow providing TTL only. This may result in a scenario where when the cache entry expires
latency is increased as the new value needs to be recomputed.
To mitigate this periodic extra latency multiple delays are often used. In the case of *memoize* there are two
(see :class:`memoize.entrybuilder.ProvidedLifeSpanCacheEntryBuilder`):

* ``update_after`` defines delay after which background/async update is executed;
* ``expire_after`` defines delay after which entry is considered outdated and invalid.

This allows refreshing cached value in the background without any observable latency.
Moreover, if some of those background refreshes fail they will be retried still in the background.
Due to this beneficial feature, it is recommended to ``update_after`` be significantly shorter than ``expire_after``.

Dog-piling proofness
--------------------

If some resource is accessed asynchronously `dog-piling <https://en.wikipedia.org/wiki/Cache_stampede>`_ may occur.
Caches designed for synchronous python code
(like built-in `LRU <https://docs.python.org/3.3/library/functools.html#lru_cache>`_)
will allow multiple concurrent tasks to observe a miss for the same resource and will proceed to flood underlying/cached
backend with requests for the same resource.


As it breaks the purpose of caching (as backend effectively sometimes is not protected with cache)
*memoize* has built-in dog-piling protection.

Under the hood, concurrent requests for the same resource (cache key) get collapsed to a single request to the backend.
When the resource is fetched all requesters obtain the result.
On failure, all requesters get an exception (same happens on timeout).

An example of what it all is about:

.. code-block:: python

    import asyncio
    from datetime import timedelta

    from aiocache import cached, SimpleMemoryCache  # version 0.10.1 used as example of other cache implementation

    from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
    from memoize.entrybuilder import ProvidedLifeSpanCacheEntryBuilder
    from memoize.wrapper import memoize

    # scenario configuration
    concurrent_requests = 5
    request_batches_execution_count = 50
    cached_value_ttl_millis = 200
    delay_between_request_batches_millis = 70

    # results/statistics
    unique_calls_under_memoize = 0
    unique_calls_under_different_cache = 0


    @memoize(configuration=MutableCacheConfiguration
        .initialized_with(DefaultInMemoryCacheConfiguration())
        .set_entry_builder(
            ProvidedLifeSpanCacheEntryBuilder(update_after=timedelta(milliseconds=cached_value_ttl_millis))
        ))
    async def cached_with_memoize():
        global unique_calls_under_memoize
        unique_calls_under_memoize += 1
        await asyncio.sleep(0.01)
        return unique_calls_under_memoize


    @cached(ttl=cached_value_ttl_millis / 1000, cache=SimpleMemoryCache)
    async def cached_with_different_cache():
        global unique_calls_under_different_cache
        unique_calls_under_different_cache += 1
        await asyncio.sleep(0.01)
        return unique_calls_under_different_cache


    async def main():
        for i in range(request_batches_execution_count):
            await asyncio.gather(*[x() for x in [cached_with_memoize] * concurrent_requests])
            await asyncio.gather(*[x() for x in [cached_with_different_cache] * concurrent_requests])
            await asyncio.sleep(delay_between_request_batches_millis / 1000)

        print("Memoize generated {} unique backend calls".format(unique_calls_under_memoize))
        print("Other cache generated {} unique backend calls".format(unique_calls_under_different_cache))
        predicted = (delay_between_request_batches_millis * request_batches_execution_count) // cached_value_ttl_millis
        print("Predicted (according to TTL) {} unique backend calls".format(predicted))

        # Printed:
        # Memoize generated 17 unique backend calls
        # Other cache generated 85 unique backend calls
        # Predicted (according to TTL) 17 unique backend calls

    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())


Async cache storage
-------------------

Interface for cache storage allows you to fully harness benefits of asynchronous programming
(see interface of :class:`memoize.storage.CacheStorage`).


Currently *memoize* provides only in-memory storage for cache values (internally at *RASP* we have others).
If you want (for instance) Redis integration, you need to implement one (please contribute!)
but *memoize* will optimally use your async implementation from the start.