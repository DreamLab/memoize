import datetime
import asyncio
import random
from dataclasses import dataclass

from memoize.wrapper import memoize
from memoize.configuration import DefaultInMemoryCacheConfiguration, MutableCacheConfiguration
from memoize.entry import CacheKey, CacheEntry
from memoize.entrybuilder import CacheEntryBuilder
from memoize.storage import LocalInMemoryCacheStorage

# needed if one has tornado installed (could be removed otherwise)
from memoize import memoize_configuration
memoize_configuration.force_asyncio = True


@dataclass
class ValueWithTTL:
    value: str
    ttl_seconds: int  # for instance, it could be derived from Cache-Control response header


class TtlRespectingCacheEntryBuilder(CacheEntryBuilder):
    def build(self, key: CacheKey, value: ValueWithTTL):
        now = datetime.datetime.utcnow()
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
