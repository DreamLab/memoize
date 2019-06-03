from memoize.configuration import DefaultInMemoryCacheConfiguration
from memoize.wrapper import memoize


@memoize(configuration=DefaultInMemoryCacheConfiguration())
async def cached():
    return 'dummy'
