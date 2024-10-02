.. image:: https://img.shields.io/pypi/v/py-memoize.svg
    :target: https://pypi.org/project/py-memoize

.. image:: https://img.shields.io/pypi/pyversions/py-memoize.svg
    :target: https://pypi.org/project/py-memoize

.. image:: https://readthedocs.org/projects/memoize/badge/?version=latest
    :target: https://memoize.readthedocs.io/en/latest/?badge=latest

.. image:: https://github.com/DreamLab/memoize/actions/workflows/tox-tests.yml/badge.svg
    :target: https://github.com/DreamLab/memoize/actions/workflows/tox-tests.yml

.. image:: https://github.com/DreamLab/memoize/actions/workflows/non-test-tox.yml/badge.svg
    :target: https://github.com/DreamLab/memoize/actions/workflows/non-test-tox.yml

Extended docs (including API docs) available at `memoize.readthedocs.io <https://memoize.readthedocs.io>`_.

What & Why
==========

**What:** Caching library for asyncio Python applications.

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

To harness the power of `ujson <https://pypi.org/project/ujson/>`_ (if JSON SerDe is used) install extra:

.. code-block:: bash

   pip install py-memoize[ujson]

Usage
-----

Provided examples use default configuration to cache results in memory.
For configuration options see `Configurability`_.

asyncio
~~~~~~~

To apply default caching configuration use:

..
    _example_source: examples/basic/basic.py

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


Features
========

Async-first
-----------

Asynchronous programming is often seen as a huge performance boost in python programming.
But with all the benefits it brings there are also new concurrency-related caveats
like `dog-piling <https://en.wikipedia.org/wiki/Cache_stampede>`_.

This library is built async-oriented from the ground-up, what manifests in, for example,
in `Dog-piling proofness`_ or `Async cache storage`_.


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
* value post-processing (see :class:`memoize.postprocessing.Postprocessing`);
  noop is the default one;
  deep-copy post-processing is also provided (be wary of deep-copy cost & limitations,
  but deep-copying allows callers to safely modify values retrieved from an in-memory cache).

All of these elements are open for extension (you can implement and plug-in your own).
Please contribute!

Example how to customize default config (everything gets overridden):

..
    _example_source: examples/configuration/custom_configuration.py

.. code-block:: python

    from datetime import timedelta

    from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
    from memoize.entrybuilder import ProvidedLifeSpanCacheEntryBuilder
    from memoize.eviction import LeastRecentlyUpdatedEvictionStrategy
    from memoize.key import EncodedMethodNameAndArgsKeyExtractor
    from memoize.postprocessing import DeepcopyPostprocessing
    from memoize.storage import LocalInMemoryCacheStorage
    from memoize.wrapper import memoize

    @memoize(
        configuration=MutableCacheConfiguration
        .initialized_with(DefaultInMemoryCacheConfiguration())
        .set_method_timeout(value=timedelta(minutes=2))
        .set_entry_builder(ProvidedLifeSpanCacheEntryBuilder(update_after=timedelta(minutes=2),
                                                             expire_after=timedelta(minutes=5)))
        .set_eviction_strategy(LeastRecentlyUpdatedEvictionStrategy(capacity=2048))
        .set_key_extractor(EncodedMethodNameAndArgsKeyExtractor(skip_first_arg_as_self=False))
        .set_storage(LocalInMemoryCacheStorage())
        .set_postprocessing(DeepcopyPostprocessing()),
        update_statuses=InMemoryLocks(update_lock_timeout=timedelta(minutes=5))
    )
    async def cached():
        return 'dummy'


Still, you can use default configuration which:

* sets timeout for underlying method to 2 minutes;
* uses in-memory storage;
* uses method instance & arguments to infer cache key;
* stores up to 4096 elements in cache and evicts entries according to least recently updated policy;
* refreshes elements after 10 minutes & ignores unrefreshed elements after 30 minutes;
* does not post-process cached values.

If that satisfies you, just use default config:

..
    _example_source: examples/configuration/default_configuration.py

.. code-block:: python

    from memoize.configuration import DefaultInMemoryCacheConfiguration
    from memoize.wrapper import memoize


    @memoize(configuration=DefaultInMemoryCacheConfiguration())
    async def cached():
        return 'dummy'

Also, if you want to stick to the building blocks of the default configuration, but need to adjust some basic params:

..
    _example_source: examples/configuration/default_customized_configuration.py

.. code-block:: python

    from datetime import timedelta

    from memoize.configuration import DefaultInMemoryCacheConfiguration
    from memoize.wrapper import memoize


    @memoize(configuration=DefaultInMemoryCacheConfiguration(capacity=4096, method_timeout=timedelta(minutes=2),
                                                             update_after=timedelta(minutes=10),
                                                             expire_after=timedelta(minutes=30)))
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

..
    _example_source: examples/dogpiling/dogpiling.py

.. code-block:: python

    import asyncio
    from datetime import timedelta

    from aiocache import cached, SimpleMemoryCache  # version 0.11.1 (latest) used as example of other cache implementation

    from memoize.configuration import DefaultInMemoryCacheConfiguration
    from memoize.wrapper import memoize

    # scenario configuration
    concurrent_requests = 5
    request_batches_execution_count = 50
    cached_value_ttl_ms = 200
    delay_between_request_batches_ms = 70

    # results/statistics
    unique_calls_under_memoize = 0
    unique_calls_under_different_cache = 0


    @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(milliseconds=cached_value_ttl_ms)))
    async def cached_with_memoize():
        global unique_calls_under_memoize
        unique_calls_under_memoize += 1
        await asyncio.sleep(0.01)
        return unique_calls_under_memoize


    @cached(ttl=cached_value_ttl_ms / 1000, cache=SimpleMemoryCache)
    async def cached_with_different_cache():
        global unique_calls_under_different_cache
        unique_calls_under_different_cache += 1
        await asyncio.sleep(0.01)
        return unique_calls_under_different_cache


    async def main():
        for i in range(request_batches_execution_count):
            await asyncio.gather(*[x() for x in [cached_with_memoize] * concurrent_requests])
            await asyncio.gather(*[x() for x in [cached_with_different_cache] * concurrent_requests])
            await asyncio.sleep(delay_between_request_batches_ms / 1000)

        print("Memoize generated {} unique backend calls".format(unique_calls_under_memoize))
        print("Other cache generated {} unique backend calls".format(unique_calls_under_different_cache))
        predicted = (delay_between_request_batches_ms * request_batches_execution_count) // cached_value_ttl_ms
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

Manual Invalidation
-------------------

You could also invalidate entries manually.
To do so you need to create instance of :class:`memoize.invalidation.InvalidationSupport`)
and pass it alongside cache configuration.
Then you could just pass args and kwargs for which you want to invalidate entry.

..
    _example_source: memoize/invalidation.py

.. code-block:: python

    from memoize.configuration import DefaultInMemoryCacheConfiguration
    from memoize.invalidation import InvalidationSupport


    import asyncio
    import random
    from memoize.wrapper import memoize

    invalidation = InvalidationSupport()


    @memoize(configuration=DefaultInMemoryCacheConfiguration(), invalidation=invalidation)
    async def expensive_computation(*args, **kwargs):
        return 'expensive-computation-' + str(random.randint(1, 100))


    async def main():
        print(await expensive_computation('arg1', kwarg='kwarg1'))
        print(await expensive_computation('arg1', kwarg='kwarg1'))

        print("Invalidation #1")
        await invalidation.invalidate_for_arguments(('arg1',), {'kwarg': 'kwarg1'})

        print(await expensive_computation('arg1', kwarg='kwarg1'))
        print(await expensive_computation('arg1', kwarg='kwarg1'))

        print("Invalidation #2")
        await invalidation.invalidate_for_arguments(('arg1',), {'kwarg': 'kwarg1'})

        print(await expensive_computation('arg1', kwarg='kwarg1'))

        # Sample output:
        #
        # expensive - computation - 98
        # expensive - computation - 98
        # Invalidation  # 1
        # expensive - computation - 73
        # expensive - computation - 73
        # Invalidation  # 2
        # expensive - computation - 59

    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())


Openness to granular TTL
------------------------

Default configuration sets update and expiry based on fixed values, which are the same for all entries.
If you need to set different TTLs for different entries, you can do so by providing
a custom :class:`memoize.entrybuilder.CacheEntryBuilder`.

.. code-block:: python

    import datetime
    import asyncio
    import random
    from dataclasses import dataclass

    from memoize.wrapper import memoize
    from memoize.configuration import DefaultInMemoryCacheConfiguration, MutableCacheConfiguration
    from memoize.entry import CacheKey, CacheEntry
    from memoize.entrybuilder import CacheEntryBuilder
    from memoize.storage import LocalInMemoryCacheStorage


    @dataclass
    class ValueWithTTL:
        value: str
        ttl_seconds: int  # for instance, it could be derived from Cache-Control response header


    class TtlRespectingCacheEntryBuilder(CacheEntryBuilder):
        def build(self, key: CacheKey, value: ValueWithTTL):
            now = datetime.datetime.now(datetime.timezone.utc)
            ttl_ends_at = now + datetime.timedelta(seconds=value.ttl_seconds)
            return CacheEntry(
                created=now,
                update_after=ttl_ends_at,
                # allowing stale data for 10% of TTL
                expires_after=ttl_ends_at + datetime.timedelta(seconds=value.ttl_seconds // 10),
                value=value
            )


    storage = LocalInMemoryCacheStorage()  # overridden & extracted for demonstration purposes only


    @memoize(configuration=MutableCacheConfiguration
             .initialized_with(DefaultInMemoryCacheConfiguration())
             .set_entry_builder(TtlRespectingCacheEntryBuilder())
             .set_storage(storage))
    async def external_call(key: str):
        return ValueWithTTL(
            value=f'{key}-result-{random.randint(1, 100)}',
            ttl_seconds=random.randint(60, 300)
        )


    async def main():
        await external_call('a')
        await external_call('b')
        await external_call('b')

        print("Entries persisted in the cache:")
        for entry in storage._data.values():
            print('Entry: ', entry.value)
            print('Effective TTL: ', (entry.update_after - entry.created).total_seconds())

        # Entries persisted in the cache:
        # Entry: ValueWithTTL(value='a-result-79', ttl_seconds=148)
        # Effective TTL: 148.0
        # Entry: ValueWithTTL(value='b-result-27', ttl_seconds=192)
        # Effective TTL: 192.0


    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())