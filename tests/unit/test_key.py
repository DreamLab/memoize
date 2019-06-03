from unittest.mock import Mock

import tornado
from tornado import gen
from tornado.testing import AsyncTestCase, gen_test

from tests import _ensure_background_tasks_finished, _assert_called_once_with, AnyObject, _as_future
from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.key import EncodedMethodNameAndArgsKeyExtractor, EncodedMethodReferenceAndArgsKeyExtractor
from memoize.wrapper import memoize


class KeyExtractorInteractionsTests(AsyncTestCase):

    @gen_test
    def test_should_call_key_extractor_on_method_used(self):
        # given
        key_extractor = Mock()
        key_extractor.format_key = Mock(return_value='key')

        @memoize(
            configuration=MutableCacheConfiguration
                .initialized_with(DefaultInMemoryCacheConfiguration())
                .set_key_extractor(key_extractor)
        )
        @gen.coroutine
        def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        yield sample_method('test', kwarg='args')
        yield _ensure_background_tasks_finished()

        # then
        # ToDo: assert wrapped methods match somehow

        _assert_called_once_with(self, key_extractor.format_key, (AnyObject(), ('test',), {'kwarg': 'args'},), {})

    @gen_test
    def test_should_pass_extracted_key_to_storage_on_entry_added_to_cache(self):
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
        @gen.coroutine
        def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        yield sample_method('test', kwarg='args')
        yield _ensure_background_tasks_finished()

        # then
        storage.get.assert_called_once_with('key')
        _assert_called_once_with(self, storage.offer, ('key', AnyObject()), {})

    @gen_test
    def test_should_pass_extracted_key_to_eviction_strategy_on_entry_added_to_cache(self):
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
        @gen.coroutine
        def sample_method(arg, kwarg=None):
            return arg, kwarg

        # when
        yield sample_method('test', kwarg='args')
        yield _ensure_background_tasks_finished()
        yield sample_method('test', kwarg='args')
        yield _ensure_background_tasks_finished()

        # then
        eviction_strategy.mark_read.assert_called_once_with('key')
        _assert_called_once_with(self, eviction_strategy.mark_written, ('key', AnyObject()), {})


class EncodedMethodReferenceAndArgsKeyExtractorTests(AsyncTestCase):

    def helper_method(self, x, y, z='val'):
        pass

    @gen_test
    def test_should_format_key(self):
        # given
        key_extractor = EncodedMethodReferenceAndArgsKeyExtractor()

        # when
        key = key_extractor.format_key(self.helper_method, ('a', 'b',), {'z': 'c'})

        # then
        self.assertEqual(key, "(" + str(self.helper_method) + ", ('a', 'b'), {'z': 'c'})")


class EncodedMethodNameAndArgsKeyExtractorTests(AsyncTestCase):
    def get_new_ioloop(self):
        return tornado.platform.asyncio.AsyncIOMainLoop()

    def helper_method(self, x, y, z='val'):
        pass

    @gen_test
    def test_should_format_key_with_all_args_on_skip_flag_not_set(self):
        # given
        key_extractor = EncodedMethodNameAndArgsKeyExtractor(skip_first_arg_as_self=False)

        # when
        key = key_extractor.format_key(self.helper_method, ('a', 'b',), {'z': 'c'})

        # then
        self.assertEqual(key, "('helper_method', ('a', 'b'), {'z': 'c'})")

    @gen_test
    def test_should_format_key_with_all_args_on_skip_flag_set(self):
        # given
        key_extractor = EncodedMethodNameAndArgsKeyExtractor(skip_first_arg_as_self=True)

        # when
        key = key_extractor.format_key(self.helper_method, (self, 'a', 'b',), {'z': 'c'})

        # then
        self.assertEqual(key, "('helper_method', ('a', 'b'), {'z': 'c'})")
