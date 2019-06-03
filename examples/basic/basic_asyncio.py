from memoize import memoize_configuration

# needed if one has tornado installed (could be removed otherwise)
memoize_configuration.force_asyncio = True

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
