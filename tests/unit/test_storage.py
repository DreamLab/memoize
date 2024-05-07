import pytest

from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

from datetime import datetime

from memoize.entry import CacheKey, CacheEntry
from memoize.storage import LocalInMemoryCacheStorage

CACHE_SAMPLE_ENTRY = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")

CACHE_KEY = CacheKey("key")


@pytest.mark.asyncio(scope="class")
class TestLocalInMemoryCacheStorage:
    def setup_method(self):
        self.storage = LocalInMemoryCacheStorage()

    async def test_offer_and_get_returns_same_object(self):
        # given
        await self.storage.offer(CACHE_KEY, CACHE_SAMPLE_ENTRY)

        # when
        returned_value = await self.storage.get(CACHE_KEY)

        # then
        assert returned_value.value == "value"

    async def test_get_without_offer_returns_none(self):
        # given/when
        returned_value = await self.storage.get(CACHE_KEY)

        # then
        assert returned_value == None

    async def test_released_object_is_not_returned(self):
        # given
        await self.storage.offer(CACHE_KEY, CACHE_SAMPLE_ENTRY)
        await self.storage.release(CACHE_KEY)

        # when
        returned_value = await self.storage.get(CACHE_KEY)

        # then
        assert returned_value == None
