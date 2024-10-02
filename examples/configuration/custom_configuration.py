from datetime import timedelta

from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.entrybuilder import ProvidedLifeSpanCacheEntryBuilder
from memoize.eviction import LeastRecentlyUpdatedEvictionStrategy
from memoize.key import EncodedMethodNameAndArgsKeyExtractor
from memoize.postprocessing import DeepcopyPostprocessing
from memoize.statuses import InMemoryLocks
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
