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
