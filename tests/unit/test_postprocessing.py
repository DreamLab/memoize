from memoize.postprocessing import DeepcopyPostprocessing
from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

from unittest.mock import Mock

from tornado import gen
from tornado.testing import AsyncTestCase, gen_test

from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.wrapper import memoize


class KeyExtractorInteractionsTests(AsyncTestCase):

    @gen_test
    def test_postprocessing_is_applied(self):
        # given
        postprocessing = Mock()
        postprocessing.apply = Mock(return_value='overridden-by-postprocessing')

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_postprocessing(postprocessing)
        )
        @gen.coroutine
        def sample_method(arg):
            return f"value-for-{arg}"

        # when
        result = yield sample_method('test')

        # then
        postprocessing.apply.assert_called_once()
        postprocessing.apply.assert_called_once_with('value-for-test')
        self.assertEqual(result, 'overridden-by-postprocessing')

    @gen_test
    def test_postprocessing_based_on_deepcopy_prevents_modifying_value_cached_in_memory(self):
        # given

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_postprocessing(DeepcopyPostprocessing())
        )
        @gen.coroutine
        def sample_method(arg):
            return {'arg': arg, 'list': [4, 5, 1, 2, 3]}  # unsorted

        # when
        result1 = yield sample_method('test')
        result2 = yield sample_method('test')
        result1['list'].sort()

        # then
        self.assertEqual(result1, {'arg': 'test', 'list': [1, 2, 3, 4, 5]})  # sorted in-place
        self.assertEqual(result2, {'arg': 'test', 'list': [4, 5, 1, 2, 3]})  # still unsorted
