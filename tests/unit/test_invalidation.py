from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

from tornado import gen
from tornado.testing import AsyncTestCase, gen_test

from memoize.invalidation import InvalidationSupport
from memoize.wrapper import memoize


class TestInvalidationSupport(AsyncTestCase):
    @gen_test
    def test_invalidation(self):
        # given
        invalidation = invalidation = InvalidationSupport()
        global counter
        counter = 0

        @memoize(invalidation=invalidation)
        @gen.coroutine
        def sample_method(arg, kwarg=None):
            global counter
            counter += 1
            return counter

        # when
        res1 = yield sample_method('test', kwarg='args')
        res2 = yield sample_method('test', kwarg='args')
        yield invalidation.invalidate_for_arguments(('test',), {'kwarg': 'args'})
        res3 = yield sample_method('test', kwarg='args')
        res4 = yield sample_method('test', kwarg='args')
        yield invalidation.invalidate_for_arguments(('test',), {'kwarg': 'args'})
        res5 = yield sample_method('test', kwarg='args')
        # yield _ensure_background_tasks_finished()

        # then
        self.assertEqual(res1, 1)
        self.assertEqual(res2, 1)
        self.assertEqual(res3, 2)  # post-invalidation
        self.assertEqual(res4, 2)  # post-invalidation
        self.assertEqual(res5, 3)  # post-second-invalidation

    @gen_test
    def test_invalidation_throws_when_not_configured(self):
        # given
        invalidation = InvalidationSupport()
        global counter
        counter = 0

        @memoize(
            # would be properly configured if invalidation would be set via `invalidation=invalidation`
        )
        @gen.coroutine
        def sample_method(arg, kwarg=None):
            global counter
            counter += 1
            return counter

        # when
        with self.assertRaises(Exception) as context:
            yield invalidation.invalidate_for_arguments(('test',), {'kwarg': 'args'})

        # then
        expected = RuntimeError("Uninitialized: InvalidationSupport should be passed to @memoize to have it initialized")
        self.assertEqual(str(context.exception), str(expected))
