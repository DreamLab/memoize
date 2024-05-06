import pytest

from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

from memoize.invalidation import InvalidationSupport
from memoize.wrapper import memoize


@pytest.mark.asyncio(scope="class")
class TestInvalidationSupport:

    async def test_invalidation(self):
        # given
        invalidation = invalidation = InvalidationSupport()
        global counter
        counter = 0

        @memoize(invalidation=invalidation)
        async def sample_method(arg, kwarg=None):
            global counter
            counter += 1
            return counter

        # when
        res1 = await sample_method('test', kwarg='args')
        res2 = await sample_method('test', kwarg='args')
        await invalidation.invalidate_for_arguments(('test',), {'kwarg': 'args'})
        res3 = await sample_method('test', kwarg='args')
        res4 = await sample_method('test', kwarg='args')
        await invalidation.invalidate_for_arguments(('test',), {'kwarg': 'args'})
        res5 = await sample_method('test', kwarg='args')
        # await _ensure_background_tasks_finished()

        # then
        assert res1 == 1
        assert res2 == 1
        assert res3 == 2  # post-invalidation
        assert res4 == 2  # post-invalidation
        assert res5 == 3  # post-second-invalidation

    async def test_invalidation_throws_when_not_configured(self):
        # given
        invalidation = InvalidationSupport()
        global counter
        counter = 0

        @memoize(
            # would be properly configured if invalidation would be set via `invalidation=invalidation`
        )
        async def sample_method(arg, kwarg=None):
            global counter
            counter += 1
            return counter

        # when
        with pytest.raises(Exception) as context:
            await invalidation.invalidate_for_arguments(('test',), {'kwarg': 'args'})

        # then
        expected = RuntimeError(
            "Uninitialized: InvalidationSupport should be passed to @memoize to have it initialized")
        assert str(context.value) == str(expected)
