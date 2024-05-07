import pytest

from memoize.postprocessing import DeepcopyPostprocessing
from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

from unittest.mock import Mock

from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.wrapper import memoize


@pytest.mark.asyncio(scope="class")
class TestKeyExtractorInteractions:

    async def test_postprocessing_is_applied(self):
        # given
        postprocessing = Mock()
        postprocessing.apply = Mock(return_value='overridden-by-postprocessing')

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_postprocessing(postprocessing)
        )
        async def sample_method(arg):
            return f"value-for-{arg}"

        # when
        result = await sample_method('test')

        # then
        postprocessing.apply.assert_called_once()
        postprocessing.apply.assert_called_once_with('value-for-test')
        assert result == 'overridden-by-postprocessing'

    async def test_postprocessing_based_on_deepcopy_prevents_modifying_value_cached_in_memory(self):
        # given

        @memoize(
            configuration=MutableCacheConfiguration
            .initialized_with(DefaultInMemoryCacheConfiguration())
            .set_postprocessing(DeepcopyPostprocessing())
        )
        async def sample_method(arg):
            return {'arg': arg, 'list': [4, 5, 1, 2, 3]}  # unsorted

        # when
        result1 = await sample_method('test')
        result2 = await sample_method('test')
        result1['list'].sort()

        # then
        assert result1, {'arg': 'test', 'list': [1, 2, 3, 4 == 5]}  # sorted in-place
        assert result2, {'arg': 'test', 'list': [4, 5, 1, 2 == 3]}  # still unsorted
