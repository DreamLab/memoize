from datetime import timedelta

from tornado.testing import AsyncTestCase, gen_test

from memoize.statuses import UpdateStatuses


class UpdateStatusesTests(AsyncTestCase):

    def setUp(self):
        super().setUp()
        self.update_statuses = UpdateStatuses()

    def tearDown(self):
        super().tearDown()

    def test_should_not_be_updating(self):
        # given/when/then
        self.assertFalse(self.update_statuses.mark_being_updated('key'))

    def test_should_be_updating(self):
        # given/when
        self.update_statuses.mark_being_updated('key')

        # then
        self.assertTrue(self.update_statuses.is_being_updated('key'))

    def test_should_raise_exception_during_marked_as_being_updated(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when/then
        with self.assertRaises(ValueError):
            self.update_statuses.mark_being_updated('key')

    def test_should_be_marked_as_being_updated(self):
        # given/when
        self.update_statuses.mark_being_updated('key')

        # then
        self.assertTrue(self.update_statuses.is_being_updated('key'))

    def test_should_raise_exception_during_be_mark_as_updated(self):
        # given/when/then
        with self.assertRaises(ValueError):
            self.update_statuses.mark_updated('key', None)

    def test_should_be_mark_as_updated(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when
        self.update_statuses.mark_updated('key', 'entry')

        # then
        self.assertFalse(self.update_statuses.is_being_updated('key'))

    def test_should_raise_exception_during_mark_update_as_aborted(self):
        # given/when/then
        with self.assertRaises(ValueError):
            self.update_statuses.mark_update_aborted('key')

    def test_should_mark_update_as_aborted(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when
        self.update_statuses.mark_update_aborted('key')

        # then
        self.assertFalse(self.update_statuses.is_being_updated('key'))

    @gen_test
    def test_should_raise_exception_during_await_updated(self):
        # given/when/then
        with self.assertRaises(ValueError):
            yield self.update_statuses.await_updated('key')

    @gen_test
    async def test_should_raise_timeout_exception_during_await_updated(self):
        # given
        self.update_statuses._update_lock_timeout = timedelta(milliseconds=1)
        self.update_statuses.mark_being_updated('key')

        # when
        await self.update_statuses.await_updated('key')

        # then
        self.assertFalse(self.update_statuses.is_being_updated('key'))

    @gen_test
    async def test_should_await_updated_return_entry(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when
        result = self.update_statuses.await_updated('key')
        self.update_statuses.mark_updated('key', None)
        result = await result

        # then
        self.assertIsNone(result)
        self.assertFalse(self.update_statuses.is_being_updated('key'))
