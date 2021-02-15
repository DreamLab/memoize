import time
from datetime import timedelta
from unittest.mock import Mock

from tornado import gen
from tornado.testing import AsyncTestCase, gen_test

from memoize.configuration import MutableCacheConfiguration, NotConfiguredCacheCalledException, \
    DefaultInMemoryCacheConfiguration
from memoize.eviction import LeastRecentlyUpdatedEvictionStrategy
from memoize.exceptions import CachedMethodFailedException
from memoize.storage import LocalInMemoryCacheStorage
from memoize.wrapper import memoize
from tests import _ensure_background_tasks_finished


class MemoizationTests(AsyncTestCase):

    def setUp(self):
        self.maxDiff = None
        super().setUp()

    @gen_test
    def test_should_return_cached_value_on_expiration_time_not_reached(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(minutes=1),
                                                                 expire_after=timedelta(minutes=2)))
        @gen.coroutine
        def get_value(arg, kwarg=None):
            return value

        # when
        res1 = yield get_value('test', kwarg='args')
        time.sleep(.200)
        yield _ensure_background_tasks_finished()
        value = 1
        res2 = yield get_value('test', kwarg='args')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(0, res2)

    @gen_test
    def test_should_return_updated_value_on_expiration_time_reached(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(milliseconds=50),
                                                                 expire_after=timedelta(milliseconds=100)))
        @gen.coroutine
        def get_value(arg, kwarg=None):
            return value

        # when
        res1 = yield get_value('test', kwarg='args')
        time.sleep(.200)
        yield _ensure_background_tasks_finished()
        value = 1
        res2 = yield get_value('test', kwarg='args')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(1, res2)

    @gen_test
    def test_should_return_current_value_on_first_call_after_update_time_reached_but_not_expiration_time(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(milliseconds=100),
                                                                 expire_after=timedelta(minutes=5)))
        @gen.coroutine
        def get_value(arg, kwarg=None):
            return value

        # when
        res1 = yield get_value('test', kwarg='args')
        time.sleep(.200)
        yield _ensure_background_tasks_finished()
        value = 1
        res2 = yield get_value('test', kwarg='args')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(0, res2)

    @gen_test
    def test_should_return_current_value_on_second_call_after_update_time_reached_but_not_expiration_time(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(update_after=timedelta(milliseconds=100),
                                                                 expire_after=timedelta(minutes=5)))
        @gen.coroutine
        def get_value(arg, kwarg=None):
            return value

        # when
        res1 = yield get_value('test', kwarg='args')
        time.sleep(.200)
        yield _ensure_background_tasks_finished()
        value = 1
        yield get_value('test', kwarg='args')
        yield _ensure_background_tasks_finished()
        res2 = yield get_value('test', kwarg='args')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(1, res2)

    @gen_test
    def test_should_return_different_values_on_different_args_with_default_key(self):
        # given
        value = 0

        @memoize()
        @gen.coroutine
        def get_value(arg, kwarg=None):
            return value

        # when
        res1 = yield get_value('test1', kwarg='args')
        time.sleep(.200)
        yield _ensure_background_tasks_finished()
        value = 1
        res2 = yield get_value('test2', kwarg='args')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(1, res2)

    @gen_test
    def test_should_return_different_values_on_different_kwargs_with_default_key(self):
        # given
        value = 0

        @memoize()
        @gen.coroutine
        def get_value(arg, kwarg=None):
            return value

        # when
        res1 = yield get_value('test', kwarg='args1')
        time.sleep(.200)
        yield _ensure_background_tasks_finished()
        value = 1
        res2 = yield get_value('test', kwarg='args2')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(1, res2)

    @gen_test
    def test_should_return_same_value_on_constant_key_function(self):
        # given
        value = 0
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='lol')

        @memoize(
            configuration=MutableCacheConfiguration
                .initialized_with(DefaultInMemoryCacheConfiguration())
                .set_key_extractor(key_extractor)
        )
        @gen.coroutine
        def get_value(arg, kwarg=None):
            return value

        # when
        res1 = yield get_value('test1', kwarg='args1')
        time.sleep(.200)
        yield _ensure_background_tasks_finished()
        value = 1
        res2 = yield get_value('test2', kwarg='args2')

        # then
        self.assertEqual(0, res1)
        self.assertEqual(0, res2)

    @gen_test
    def test_should_release_keys_on_caching_multiple_elements(self):
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
        @gen.coroutine
        def get_value(arg, kwarg=None):
            return value

        # when
        yield get_value('test1', kwarg='args1')
        yield get_value('test2', kwarg='args2')
        yield get_value('test3', kwarg='args3')
        yield get_value('test4', kwarg='args4')
        yield _ensure_background_tasks_finished()

        # then
        s1 = yield storage.get("('test1', 'args1')")
        s2 = yield storage.get("('test2', 'args2')")
        s3 = yield storage.get("('test3', 'args3')")
        s4 = yield storage.get("('test4', 'args4')")

        self.assertIsNone(s1)
        self.assertIsNone(s2)
        self.assertIsNotNone(s3)
        self.assertIsNotNone(s4)

    @gen_test
    def test_should_throw_exception_on_configuration_not_ready(self):
        # given
        @memoize(
            configuration=MutableCacheConfiguration
                .initialized_with(DefaultInMemoryCacheConfiguration())
                .set_configured(False)
        )
        @gen.coroutine
        def get_value(arg, kwarg=None):
            raise ValueError("Get lost")

        # when
        with self.assertRaises(Exception) as context:
            yield get_value('test1', kwarg='args1')

        # then
        expected = NotConfiguredCacheCalledException()
        self.assertEqual(str(expected), str(context.exception))

    @gen_test
    def test_should_throw_exception_on_wrapped_method_failure(self):
        # given
        @memoize()
        @gen.coroutine
        def get_value(arg, kwarg=None):
            raise ValueError("Get lost")

        # when
        with self.assertRaises(Exception) as context:
            yield get_value('test1', kwarg='args1')

        # then
        expected = CachedMethodFailedException('Refresh failed to complete', ValueError('Get lost', ))
        self.assertEqual(str(expected), str(context.exception))  # ToDo: consider better comparision

    @gen_test
    def test_should_throw_exception_on_refresh_timeout(self):
        # given

        @memoize(configuration=DefaultInMemoryCacheConfiguration(method_timeout=timedelta(milliseconds=100)))
        @gen.coroutine
        def get_value(arg, kwarg=None):
            yield _ensure_background_tasks_finished()
            time.sleep(.200)
            yield _ensure_background_tasks_finished()
            return 0

        # when
        with self.assertRaises(Exception) as context:
            yield get_value('test1', kwarg='args1')

        # then
        expected = CachedMethodFailedException('Refresh timed out')
        self.assertEqual(str(expected), str(context.exception))  # ToDo: consider better comparision
