import pytest

from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

from datetime import timedelta

from memoize.statuses import InMemoryLocks, UpdateStatuses


@pytest.mark.asyncio(scope="class")
class TestStatuses:

    def setup_method(self):
        self.update_statuses: UpdateStatuses = InMemoryLocks()

    async def test_should_not_be_updating(self):
        # given/when/then
        assert not self.update_statuses.mark_being_updated('key')

    async def test_should_be_updating(self):
        # given/when
        self.update_statuses.mark_being_updated('key')

        # then
        assert self.update_statuses.is_being_updated('key')

    async def test_should_raise_exception_during_marked_as_being_updated(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when/then
        with pytest.raises(ValueError):
            self.update_statuses.mark_being_updated('key')

    async def test_should_be_marked_as_being_updated(self):
        # given/when
        self.update_statuses.mark_being_updated('key')

        # then
        assert self.update_statuses.is_being_updated('key')

    async def test_should_raise_exception_during_be_mark_as_updated(self):
        # given/when/then
        with pytest.raises(ValueError):
            self.update_statuses.mark_updated('key', None)

    async def test_should_be_mark_as_updated(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when
        self.update_statuses.mark_updated('key', 'entry')

        # then
        assert not self.update_statuses.is_being_updated('key')

    async def test_should_raise_exception_during_mark_update_as_aborted(self):
        # given/when/then
        with pytest.raises(ValueError):
            self.update_statuses.mark_update_aborted('key', Exception('stub'))

    async def test_should_mark_update_as_aborted(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when
        self.update_statuses.mark_update_aborted('key', Exception('stub'))

        # then
        assert not self.update_statuses.is_being_updated('key')

    async def test_should_raise_exception_during_await_updated(self):
        # given/when/then
        with pytest.raises(ValueError):
            await self.update_statuses.await_updated('key')

    async def test_should_raise_timeout_exception_during_await_updated(self):
        # given
        self.update_statuses._update_lock_timeout = timedelta(milliseconds=1)
        self.update_statuses.mark_being_updated('key')

        # when
        await self.update_statuses.await_updated('key')

        # then
        assert not self.update_statuses.is_being_updated('key')

    async def test_should_await_updated_return_entry(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when
        result = self.update_statuses.await_updated('key')
        self.update_statuses.mark_updated('key', None)
        result = await result

        # then
        assert result == None
        assert not self.update_statuses.is_being_updated('key')

    async def test_concurrent_callers_should_all_get_exception_on_aborted_update(self):
        # given
        self.update_statuses.mark_being_updated('key')

        # when
        result1 = self.update_statuses.await_updated('key')
        result2 = self.update_statuses.await_updated('key')
        result3 = self.update_statuses.await_updated('key')
        self.update_statuses.mark_update_aborted('key', ValueError('stub'))
        result1 = await result1
        result2 = await result2
        result3 = await result3

        # then
        assert not self.update_statuses.is_being_updated('key')
        assert str(result1) == str(ValueError('stub'))
        assert str(result2) == str(ValueError('stub'))
        assert str(result3) == str(ValueError('stub'))
