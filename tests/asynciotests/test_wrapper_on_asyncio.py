import asyncio
import time
from datetime import timedelta
from unittest.mock import Mock

import tornado
from tornado.platform.asyncio import to_asyncio_future
from tornado.testing import AsyncTestCase, gen_test

from memoize import memoize_configuration
from memoize.configuration import MutableCacheConfiguration, NotConfiguredCacheCalledException, \
    DefaultInMemoryCacheConfiguration
from memoize.eviction import LeastRecentlyUpdatedEvictionStrategy
from memoize.exceptions import CachedMethodFailedException
from memoize.storage import LocalInMemoryCacheStorage
from memoize.wrapper import memoize
from tests import _ensure_asyncio_background_tasks_finished


class MemoizationTests(AsyncTestCase):

    def get_new_ioloop(self):
        return tornado.platform.asyncio.AsyncIOMainLoop()

    def setUp(self):
        self.maxDiff = None
        super().setUp()

    @gen_test
    async def test_should_return_cached_value_on_expiration_time_not_reached(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(minutes=1),
                                                                 expire_after=timedelta(minutes=2)))
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test', kwarg='args')
        time.sleep(.200)
        await _ensure_asyncio_background_tasks_finished()
        value = 1
        # calling thrice be more confident about behaviour of parallel execution
        res2 = await self._call_thrice(lambda: get_value('test', kwarg='args'))

        # then
        self.assertEqual(0, res1)
        self.assertEqual([0, 0, 0], res2)

    @gen_test
    async def test_should_return_updated_value_on_expiration_time_reached(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(milliseconds=50),
                                                                 expire_after=timedelta(milliseconds=100)))
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test', kwarg='args')
        time.sleep(.200)
        await _ensure_asyncio_background_tasks_finished()
        value = 1
        # calling thrice be more confident about behaviour of parallel execution
        res2 = await self._call_thrice(lambda: get_value('test', kwarg='args'))

        # then
        self.assertEqual(0, res1)
        self.assertEqual([1, 1, 1], res2)

    @gen_test
    async def test_should_return_current_value_on_first_call_after_update_time_reached_but_not_expiration_time(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(milliseconds=100),
                                                                 expire_after=timedelta(minutes=5)))
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test', kwarg='args')
        time.sleep(.200)
        await _ensure_asyncio_background_tasks_finished()
        value = 1
        # calling thrice be more confident about behaviour of parallel execution
        res2 = await self._call_thrice(lambda: get_value('test', kwarg='args'))

        # then
        self.assertEqual(0, res1)
        self.assertEqual([0, 0, 0], res2)

    @gen_test
    async def test_should_return_current_value_on_second_call_after_update_time_reached_but_not_expiration_time(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(milliseconds=100),
                                                                 expire_after=timedelta(minutes=5)))
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test', kwarg='args')
        time.sleep(.200)
        await _ensure_asyncio_background_tasks_finished()
        value = 1
        await get_value('test', kwarg='args')
        await _ensure_asyncio_background_tasks_finished()
        # calling thrice be more confident about behaviour of parallel execution
        res2 = await self._call_thrice(lambda: get_value('test', kwarg='args'))

        # then
        self.assertEqual(0, res1)
        self.assertEqual([1, 1, 1], res2)

    @gen_test
    async def test_should_return_different_values_on_different_args_with_default_key(self):
        # given
        value = 0

        @memoize()
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test1', kwarg='args')
        time.sleep(.200)
        await _ensure_asyncio_background_tasks_finished()
        value = 1
        res2 = await get_value('test2', kwarg='args')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(1, res2)

    @gen_test
    async def test_should_return_different_values_on_different_kwargs_with_default_key(self):
        # given
        value = 0

        @memoize()
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test', kwarg='args1')
        time.sleep(.200)
        await _ensure_asyncio_background_tasks_finished()
        value = 1
        res2 = await get_value('test', kwarg='args2')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(1, res2)

    @gen_test
    async def test_should_return_same_value_on_constant_key_function(self):
        # given
        value = 0
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='lol')

        @memoize(
            configuration=MutableCacheConfiguration
                .initialized_with(DefaultInMemoryCacheConfiguration())
                .set_key_extractor(key_extractor)
        )
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test1', kwarg='args1')
        time.sleep(.200)
        await _ensure_asyncio_background_tasks_finished()
        value = 1
        res2 = await get_value('test2', kwarg='args2')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(0, res2)

    @gen_test
    async def test_should_release_keys_on_caching_multiple_elements(self):
        # given
        value = 0
        storage = LocalInMemoryCacheStorage()
        key_extractor = Mock()
        key_extractor.format_key = Mock(side_effect=lambda method, args, kwargs: str((args[0], kwargs.get('kwarg'))))

        @memoize(
            configuration=MutableCacheConfiguration
                .initialized_with(DefaultInMemoryCacheConfiguration())
                .set_eviction_strategy(LeastRecentlyUpdatedEvictionStrategy(capacity=2))
                .set_key_extractor(key_extractor)
                .set_storage(storage)
        )
        async def get_value(arg, kwarg=None):
            return value

        # when
        await get_value('test1', kwarg='args1')
        await get_value('test2', kwarg='args2')
        await get_value('test3', kwarg='args3')
        await get_value('test4', kwarg='args4')
        await _ensure_asyncio_background_tasks_finished()

        # then
        s1 = await storage.get("('test1', 'args1')")
        s2 = await storage.get("('test2', 'args2')")
        s3 = await storage.get("('test3', 'args3')")
        s4 = await storage.get("('test4', 'args4')")

        self.assertIsNone(s1)
        self.assertIsNone(s2)
        self.assertIsNotNone(s3)
        self.assertIsNotNone(s4)

    @gen_test
    async def test_should_throw_exception_on_configuration_not_ready(self):
        # given
        @memoize(
            configuration=MutableCacheConfiguration
                .initialized_with(DefaultInMemoryCacheConfiguration())
                .set_configured(False)
        )
        async def get_value(arg, kwarg=None):
            raise ValueError("Get lost")

        # when
        with self.assertRaises(Exception) as context:
            await get_value('test1', kwarg='args1')

        # then
        expected = NotConfiguredCacheCalledException()
        self.assertEqual(str(expected), str(context.exception))

    @gen_test
    async def test_should_throw_exception_on_wrapped_method_failure(self):
        # given
        @memoize()
        async def get_value(arg, kwarg=None):
            raise ValueError("Get lost")

        # when
        with self.assertRaises(Exception) as context:
            await get_value('test1', kwarg='args1')

        # then
        expected = CachedMethodFailedException('Refresh failed to complete', ValueError('Get lost', ))
        self.assertEqual(str(expected), str(context.exception))  # ToDo: consider better comparision

    @gen_test
    async def test_should_throw_exception_on_refresh_timeout(self):
        # given

        @memoize(configuration=DefaultInMemoryCacheConfiguration(method_timeout=timedelta(milliseconds=100)))
        async def get_value(arg, kwarg=None):
            await _ensure_asyncio_background_tasks_finished()
            time.sleep(.200)
            await _ensure_asyncio_background_tasks_finished()
            return 0

        # when
        with self.assertRaises(Exception) as context:
            await get_value('test1', kwarg='args1')

        # then
        expected = CachedMethodFailedException('Refresh timed out')
        self.assertEqual(str(expected), str(context.exception))  # ToDo: consider better comparision

    @staticmethod
    async def _call_thrice(call):
        # gen_test setup somehow interferes with coroutines and futures
        # code tested manually works without such "decorations" but for testing this workaround was the bes I've found
        if memoize_configuration.force_asyncio:
            res2 = await asyncio.gather(call(), call(), call())
        else:
            res2 = await asyncio.gather(to_asyncio_future(call()), to_asyncio_future(call()), to_asyncio_future(call()))
        return res2
