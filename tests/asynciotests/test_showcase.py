import time
from datetime import timedelta

import tornado
from tornado.testing import AsyncTestCase, gen_test

from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.entrybuilder import ProvidedLifeSpanCacheEntryBuilder
from memoize.exceptions import CachedMethodFailedException
from memoize.wrapper import memoize
from tests import _ensure_asyncio_background_tasks_finished


class MemoizationTests(AsyncTestCase):

    def get_new_ioloop(self):
        return tornado.platform.asyncio.AsyncIOMainLoop()

    def setUp(self):
        self.maxDiff = None
        super().setUp()

    # overriding this as background refreshes that failed
    # with default _handle_exception implementation cause test-case failure despite assertions passing
    def _handle_exception(self, typ, value, tb):
        import logging
        logging.warning("Loose exception - see it is related to background refreshes that failed %s", value)

    @gen_test
    async def test_complex_showcase(self):
        # given
        UPDATE_MS = 400.0
        UPDATE_S = UPDATE_MS / 1000
        EXPIRE_MS = 800.0
        EXPIRE_S = EXPIRE_MS / 1000

        @memoize(
            configuration=MutableCacheConfiguration
                .initialized_with(DefaultInMemoryCacheConfiguration())
                .set_entry_builder(ProvidedLifeSpanCacheEntryBuilder(update_after=timedelta(milliseconds=UPDATE_MS),
                                                                     expire_after=timedelta(milliseconds=EXPIRE_MS))))
        async def get_value_or_throw(arg, kwarg=None):
            if should_throw:
                raise ValueError(value)
            else:
                return value

        # when #1: initial call
        value, should_throw = 'ok #1', False
        res1 = await get_value_or_throw('test', kwarg='args')

        # when #2: background refresh - returns stale
        time.sleep(UPDATE_S)
        await _ensure_asyncio_background_tasks_finished()
        value, should_throw = 'ok #2', False
        res2 = await get_value_or_throw('test', kwarg='args')

        # when #3: no refresh (cache up-to-date)
        time.sleep(.10)
        await _ensure_asyncio_background_tasks_finished()
        value, should_throw = 'ok #3', False
        res3 = await get_value_or_throw('test', kwarg='args')

        # when #4: no refresh (cache up-to-date) but starts throwing
        time.sleep(.10)
        await _ensure_asyncio_background_tasks_finished()
        value, should_throw = 'throws #1', True
        res4 = await get_value_or_throw('test', kwarg='args')

        # when #5: background refresh while throwing - returns stale
        time.sleep(UPDATE_S)
        await _ensure_asyncio_background_tasks_finished()
        value, should_throw = 'throws #2', True
        res5 = await get_value_or_throw('test', kwarg='args')

        # when #6: stale value from cache as method raised during background refresh at #5
        time.sleep(.10)
        await _ensure_asyncio_background_tasks_finished()
        value, should_throw = 'throws #3', True
        res6 = await get_value_or_throw('test', kwarg='args')

        # when #7: stale expired - cache throws synchronously
        time.sleep(EXPIRE_S)
        await _ensure_asyncio_background_tasks_finished()
        value, should_throw = 'throws #4', True
        with self.assertRaises(Exception) as context:
            await get_value_or_throw('test', kwarg='args')

        # then
        self.assertEqual('ok #1', res1)
        self.assertEqual('ok #1', res2)  # previous value - refresh in background
        self.assertEqual('ok #2', res3)  # value from cache - still relevant
        self.assertEqual('ok #2', res4)  # value from cache - still relevant
        self.assertEqual('ok #2', res5)  # stale from cache - refresh in background
        self.assertEqual('ok #2', res6)  # stale from cache - should be updated but method throws
        expected = CachedMethodFailedException('Refresh failed to complete', ValueError('throws #4', ))
        self.assertEqual(str(expected), str(context.exception))  # ToDo: consider better comparision
