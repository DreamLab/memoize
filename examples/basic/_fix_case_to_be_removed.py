import asyncio

from memoize import memoize_configuration

# needed if one has tornado installed (could be removed otherwise)
memoize_configuration.force_asyncio = True

from datetime import timedelta
from memoize.wrapper import memoize
from memoize.configuration import MutableCacheConfiguration
from memoize.entrybuilder import ProvidedLifeSpanCacheEntryBuilder
from memoize.eviction import NoEvictionStrategy
from memoize.key import EncodedMethodReferenceAndArgsKeyExtractor
from memoize.storage import LocalInMemoryCacheStorage
from asyncio import sleep, gather


@memoize(configuration=MutableCacheConfiguration(
    configured=True,
    storage=LocalInMemoryCacheStorage(),
    key_extractor=EncodedMethodReferenceAndArgsKeyExtractor(),
    method_timeout=timedelta(hours=1),
    entry_builder=ProvidedLifeSpanCacheEntryBuilder(update_after=timedelta(hours=1), expire_after=timedelta(hours=1)),
    eviction_strategy=NoEvictionStrategy(),
))
async def test():
    await sleep(1)
    raise ValueError("something went wrong")


async def main():
    results = await gather(test(), test(), test(), test(), return_exceptions=True)
    for result in results:
        print(result)
        print(result.__cause__)

    # see nice traceback in the console
    await test()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
