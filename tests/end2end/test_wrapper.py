import asyncio
import time
from asyncio import CancelledError
from datetime import timedelta
from unittest.mock import Mock

import pytest

from memoize.configuration import MutableCacheConfiguration, NotConfiguredCacheCalledException, \
    DefaultInMemoryCacheConfiguration
from memoize.eviction import LeastRecentlyUpdatedEvictionStrategy
from memoize.exceptions import CachedMethodFailedException
from memoize.storage import LocalInMemoryCacheStorage
from memoize.wrapper import memoize
from tests import _ensure_background_tasks_finished


@pytest.mark.asyncio(scope="class")
class TestWrapper:

    def setUp(self):
        self.maxDiff = None
        super().setUp()

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
        await _ensure_background_tasks_finished()
        value = 1
        # calling thrice be more confident about behaviour of parallel execution
        res2 = await self._call_thrice(lambda: get_value('test', kwarg='args'))

        # then
        assert 0 == res1
        assert [0, 0, 0] == res2

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
        await _ensure_background_tasks_finished()
        value = 1
        # calling thrice be more confident about behaviour of parallel execution
        res2 = await self._call_thrice(lambda: get_value('test', kwarg='args'))

        # then
        assert 0 == res1
        assert [1, 1, 1] == res2

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
        await _ensure_background_tasks_finished()
        value = 1
        # calling thrice be more confident about behaviour of parallel execution
        res2 = await self._call_thrice(lambda: get_value('test', kwarg='args'))

        # then
        assert 0 == res1
        assert [0, 0, 0] == res2

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
        await _ensure_background_tasks_finished()
        value = 1
        await get_value('test', kwarg='args')
        await _ensure_background_tasks_finished()
        # calling thrice be more confident about behaviour of parallel execution
        res2 = await self._call_thrice(lambda: get_value('test', kwarg='args'))

        # then
        assert 0 == res1
        assert [1, 1, 1] == res2

    async def test_should_return_different_values_on_different_args_with_default_key(self):
        # given
        value = 0

        @memoize()
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test1', kwarg='args')
        time.sleep(.200)
        await _ensure_background_tasks_finished()
        value = 1
        res2 = await get_value('test2', kwarg='args')

        # then
        assert 0 == res1
        assert 1 == res2

    async def test_should_return_different_values_on_different_kwargs_with_default_key(self):
        # given
        value = 0

        @memoize()
        async def get_value(arg, kwarg=None):
            return value

        # when
        res1 = await get_value('test', kwarg='args1')
        time.sleep(.200)
        await _ensure_background_tasks_finished()
        value = 1
        res2 = await get_value('test', kwarg='args2')

        # then
        assert 0 == res1
        assert 1 == res2

    async def test_should_return_exception_for_all_concurrent_callers(self):
        # given
        value = 0

        @memoize()
        async def get_value(arg, kwarg=None):
            raise ValueError(f'stub{value}')

        # when
        res1 = get_value('test', kwarg='args1')
        res2 = get_value('test', kwarg='args1')
        res3 = get_value('test', kwarg='args1')

        # then
        with pytest.raises(Exception) as context:
            await res1
        assert context.value.__class__ == CachedMethodFailedException
        assert str(context.value.__cause__) == str(ValueError('stub0'))

        with pytest.raises(Exception) as context:
            await res2
        assert context.value.__class__ == CachedMethodFailedException
        assert str(context.value.__cause__) == str(ValueError('stub0'))

        with pytest.raises(Exception) as context:
            await res3
        assert context.value.__class__ == CachedMethodFailedException
        assert str(context.value.__cause__) == str(ValueError('stub0'))

    async def test_should_return_cancelled_exception_for_all_concurrent_callers(self):
        # given
        value = 0

        @memoize()
        async def get_value(arg, kwarg=None):
            new_task = asyncio.create_task(asyncio.sleep(1))
            new_task.cancel()  # this will raise CancelledError
            await new_task

        # when
        res1 = get_value('test', kwarg='args1')
        res2 = get_value('test', kwarg='args1')
        res3 = get_value('test', kwarg='args1')

        # then
        with pytest.raises(Exception) as context:
            await res1
        assert context.value.__class__ == CachedMethodFailedException
        assert str(context.value.__cause__) == str(CancelledError())

        with pytest.raises(Exception) as context:
            await res2
        assert context.value.__class__ == CachedMethodFailedException
        assert str(context.value.__cause__) == str(CancelledError())

        with pytest.raises(Exception) as context:
            await res3
        assert context.value.__class__ == CachedMethodFailedException
        assert str(context.value.__cause__) == str(CancelledError())

    async def test_should_return_timeout_for_all_concurrent_callers(self):
        # given
        value = 0

        @memoize(configuration=DefaultInMemoryCacheConfiguration(method_timeout=timedelta(milliseconds=1)))
        async def get_value(arg, kwarg=None):
            await _ensure_background_tasks_finished()
            time.sleep(.200)
            await _ensure_background_tasks_finished()
            return value

        # when
        res1 = get_value('test', kwarg='args1')
        res2 = get_value('test', kwarg='args1')
        res3 = get_value('test', kwarg='args1')

        # then
        with pytest.raises(Exception) as context:
            await res1
        assert context.value.__class__ == CachedMethodFailedException
        assert context.value.__cause__.__class__ == asyncio.TimeoutError

        with pytest.raises(Exception) as context:
            await res2
        assert context.value.__class__ == CachedMethodFailedException
        assert context.value.__cause__.__class__ == asyncio.TimeoutError

        with pytest.raises(Exception) as context:
            await res3
        assert context.value.__class__ == CachedMethodFailedException
        assert context.value.__cause__.__class__ == asyncio.TimeoutError

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
        await _ensure_background_tasks_finished()
        value = 1
        res2 = await get_value('test2', kwarg='args2')

        # then
        assert 0 == res1
        assert 0 == res2

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
        await _ensure_background_tasks_finished()

        # then
        s1 = await storage.get("('test1', 'args1')")
        s2 = await storage.get("('test2', 'args2')")
        s3 = await storage.get("('test3', 'args3')")
        s4 = await storage.get("('test4', 'args4')")

        assert s1 is None
        assert s2 is None
        assert s3 is not None
        assert s4 is not None

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
        with pytest.raises(Exception) as context:
            await get_value('test1', kwarg='args1')

        # then
        expected = NotConfiguredCacheCalledException()
        assert str(expected) == str(context.value)

    async def test_should_throw_exception_on_wrapped_method_failure(self):
        # given
        @memoize()
        async def get_value(arg, kwarg=None):
            raise ValueError("Get lost")

        # when
        with pytest.raises(Exception) as context:
            await get_value('test1', kwarg='args1')

        # then
        assert str(context.value) == str(CachedMethodFailedException('Refresh failed to complete'))
        assert str(context.value.__cause__) == str(ValueError("Get lost"))

    async def test_should_throw_exception_on_refresh_timeout(self):
        # given

        @memoize(configuration=DefaultInMemoryCacheConfiguration(method_timeout=timedelta(milliseconds=100)))
        async def get_value(arg, kwarg=None):
            await _ensure_background_tasks_finished()
            time.sleep(.200)
            await _ensure_background_tasks_finished()
            return 0

        # when
        with pytest.raises(Exception) as context:
            await get_value('test1', kwarg='args1')

        # then
        assert context.value.__class__ == CachedMethodFailedException
        assert context.value.__cause__.__class__ == asyncio.TimeoutError

    @staticmethod
    async def _call_thrice(call):
        return await asyncio.gather(call(), call(), call())
