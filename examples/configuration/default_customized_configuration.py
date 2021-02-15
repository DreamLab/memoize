from datetime import timedelta

from memoize.configuration import DefaultInMemoryCacheConfiguration
from memoize.wrapper import memoize


@memoize(configuration=DefaultInMemoryCacheConfiguration(capacity=4096, method_timeout=timedelta(minutes=2),
                                                         update_after=timedelta(minutes=10),
                                                         expire_after=timedelta(minutes=30)))
async def cached():
    return 'dummy'
