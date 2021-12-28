from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

from datetime import datetime
from tornado.testing import AsyncTestCase, gen_test
from memoize.entry import CacheKey, CacheEntry
from memoize.storage import LocalInMemoryCacheStorage

CACHE_SAMPLE_ENTRY = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")

CACHE_KEY = CacheKey("key")


class LocalInMemoryCacheStorageTests(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.storage = LocalInMemoryCacheStorage()

    def tearDown(self):
        super().tearDown()

    @gen_test
    def test_offer_and_get_returns_same_object(self):
        # given
        yield self.storage.offer(CACHE_KEY, CACHE_SAMPLE_ENTRY)

        # when
        returned_value = yield self.storage.get(CACHE_KEY)

        # then
        self.assertEqual(returned_value.value, "value")

    @gen_test
    def test_get_without_offer_returns_none(self):
        # given/when
        returned_value = yield self.storage.get(CACHE_KEY)

        # then
        self.assertIsNone(returned_value)

    @gen_test
    def test_released_object_is_not_returned(self):
        # given
        yield self.storage.offer(CACHE_KEY, CACHE_SAMPLE_ENTRY)
        yield self.storage.release(CACHE_KEY)

        # when
        returned_value = yield self.storage.get(CACHE_KEY)

        # then
        self.assertIsNone(returned_value)
