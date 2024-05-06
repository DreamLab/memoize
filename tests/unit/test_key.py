import pytest

from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

from unittest.mock import Mock

from tests import _ensure_background_tasks_finished, _assert_called_once_with, AnyObject, _as_future
from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.key import EncodedMethodNameAndArgsKeyExtractor, EncodedMethodReferenceAndArgsKeyExtractor
from memoize.wrapper import memoize


@pytest.mark.asyncio(scope="class")
class TestKeyExtractorInteractions:

    async def test_should_call_key_extractor_on_method_used(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='key')

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_key_extractor(key_extractor)
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        await sample_method('test', kwarg='args')
        await _ensure_background_tasks_finished()

        # then
        # ToDo: assert wrapped methods match somehow

        _assert_called_once_with(key_extractor.format_key, (AnyObject(), ('test',), {'kwarg': 'args'},), {})

    async def test_should_pass_extracted_key_to_storage_on_entry_added_to_cache(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='key')

        storage = Mock()
        storage.get = Mock(return_value=_as_future(None))
        storage.offer = Mock(return_value=_as_future(None))

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_key_extractor(key_extractor)
            .set_storage(storage)
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        await sample_method('test', kwarg='args')
        await _ensure_background_tasks_finished()

        # then
        storage.get.assert_called_once_with('key')
        _assert_called_once_with(storage.offer, ('key', AnyObject()), {})

    async def test_should_pass_extracted_key_to_eviction_strategy_on_entry_added_to_cache(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='key')

        eviction_strategy = Mock()

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_eviction_strategy(eviction_strategy)
            .set_key_extractor(key_extractor)
        )
        async def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        await sample_method('test', kwarg='args')
        await _ensure_background_tasks_finished()
        await sample_method('test', kwarg='args')
        await _ensure_background_tasks_finished()

        # then
        eviction_strategy.mark_read.assert_called_once_with('key')
        _assert_called_once_with(eviction_strategy.mark_written, ('key', AnyObject()), {})


class EncodedMethodReferenceAndArgsKeyExtractorTests:

    def helper_method(self, x, y, z='val'):
        pass

    async def test_should_format_key(self):
        # given
        key_extractor = EncodedMethodReferenceAndArgsKeyExtractor()

        # when
        key = key_extractor.format_key(self.helper_method, ('a', 'b',), {'z': 'c'})

        # then
        assert key, "(" + str(self.helper_method) + ", ('a', 'b') ==  {'z': 'c'})"


class EncodedMethodNameAndArgsKeyExtractorTests:

    def helper_method(self, x, y, z='val'):
        pass

    async def test_should_format_key_with_all_args_on_skip_flag_not_set(self):
        # given
        key_extractor = EncodedMethodNameAndArgsKeyExtractor(skip_first_arg_as_self=False)

        # when
        key = key_extractor.format_key(self.helper_method, ('a', 'b',), {'z': 'c'})

        # then
        assert key, "('helper_method', ('a', 'b') ==  {'z': 'c'})"

    async def test_should_format_key_with_all_args_on_skip_flag_set(self):
        # given
        key_extractor = EncodedMethodNameAndArgsKeyExtractor(skip_first_arg_as_self=True)

        # when
        key = key_extractor.format_key(self.helper_method, (self, 'a', 'b',), {'z': 'c'})

        # then
        assert key, "('helper_method', ('a', 'b') ==  {'z': 'c'})"
