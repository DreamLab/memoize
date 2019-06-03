from memoize import memoize_configuration

# needed if one has tornado installed (could be removed otherwise)
memoize_configuration.force_asyncio = True

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


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
