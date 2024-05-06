import asyncio
import time
from datetime import timedelta
from unittest.mock import Mock

import pytest

from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.entrybuilder import ProvidedLifeSpanCacheEntryBuilder
from memoize.wrapper import memoize
from tests import _assert_called_once_with, AnyObject, _as_future, _ensure_asyncio_background_tasks_finished, \
    _ensure_background_tasks_finished


@pytest.mark.asyncio
class TestEvictionStrategyInteractions:

    async def test_should_inform_eviction_strategy_on_entry_added(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='key')

        eviction_strategy = Mock()

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_key_extractor(key_extractor)
            .set_eviction_strategy(eviction_strategy)
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        await sample_method('test', kwarg='args')

        # then
        _assert_called_once_with(eviction_strategy.mark_written, ('key', AnyObject()), {})

    async def test_should_inform_eviction_strategy_on_entry_updated(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='key')

        eviction_strategy = Mock()

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_entry_builder(ProvidedLifeSpanCacheEntryBuilder(update_after=timedelta(milliseconds=100)))
            .set_key_extractor(key_extractor)
            .set_eviction_strategy(eviction_strategy)
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        await sample_method('test', kwarg='args')
        await asyncio.sleep(0.200)

        # when
        await sample_method('test', kwarg='args')

        # then
        _assert_called_once_with(eviction_strategy.mark_written, ('key', AnyObject()), {})

    async def test_should_inform_eviction_strategy_on_entry_mark_read(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='key')

        eviction_strategy = Mock()

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_key_extractor(key_extractor)
            .set_eviction_strategy(eviction_strategy)
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        await sample_method('test', kwarg='args')

        # when
        await sample_method('test', kwarg='args')

        # then
        eviction_strategy.mark_read.assert_called_once_with('key')

    async def test_should_inform_eviction_strategy_entry_mark_released(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(side_effect=lambda method, args, kwargs: str((args, kwargs)))

        eviction_strategy = Mock()
        eviction_strategy.next_to_release = Mock(return_value='release-test')

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_key_extractor(key_extractor)
            .set_eviction_strategy(eviction_strategy)
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        await sample_method('test', kwarg='args')
        await _ensure_background_tasks_finished()

        # then
        eviction_strategy.mark_released.assert_called_once_with('release-test')

    async def test_should_retrieve_entry_to_release_on_entry_added(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(side_effect=lambda method, args, kwargs: str((args, kwargs)))

        eviction_strategy = Mock()
        eviction_strategy.next_to_release = Mock(return_value='release-test')

        storage = Mock()
        storage.get = Mock(return_value=_as_future(None))
        storage.offer = Mock(return_value=_as_future(None))
        storage.release = Mock(return_value=_as_future(None))

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_storage(storage)
            .set_key_extractor(key_extractor)
            .set_eviction_strategy(eviction_strategy)
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        await sample_method('test', kwarg='args')
        await _ensure_background_tasks_finished()

        # then
        eviction_strategy.next_to_release.assert_called_once_with()
        storage.release.assert_called_once_with('release-test')

    async def test_should_retrieve_entry_to_release_on_entry_updated(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(side_effect=lambda method, args, kwargs: str((args, kwargs)))

        eviction_strategy = Mock()
        eviction_strategy.next_to_release = Mock(return_value='release-test')

        storage = Mock()
        storage.get = Mock(return_value=_as_future(None))
        storage.offer = Mock(return_value=_as_future(None))
        storage.release = Mock(return_value=_as_future(None))

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_key_extractor(key_extractor)
            .set_eviction_strategy(eviction_strategy)
            .set_storage(storage)
            .set_entry_builder(ProvidedLifeSpanCacheEntryBuilder(update_after=timedelta(milliseconds=50)))
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        await sample_method('test', kwarg='args')
        await _ensure_asyncio_background_tasks_finished()
        time.sleep(.200)
        eviction_strategy.next_to_release.reset_mock()
        storage.release.reset_mock()

        # when
        await sample_method('test', kwarg='args')
        await _ensure_asyncio_background_tasks_finished()

        # then
        eviction_strategy.next_to_release.assert_called_once_with()
        storage.release.assert_called_once_with('release-test')
