"""
[Internal use only] Encapsulates update state management.
"""
import datetime
import logging
from asyncio import Future
from typing import Optional, Dict, Awaitable

from memoize import coerced
from memoize.entry import CacheKey, CacheEntry


class UpdateStatuses:
    def __init__(self, update_lock_timeout: datetime.timedelta = datetime.timedelta(minutes=5)) -> None:
        self.logger = logging.getLogger(__name__)
        self._update_lock_timeout = update_lock_timeout
        # type declaration should not be in comment once we drop py35 support
        self._updates_in_progress = {}  # type: Dict[CacheKey, Future]

    def is_being_updated(self, key: CacheKey) -> bool:
        """Checks if update for given key is in progress. Obtained info is valid until control gets back to IO-loop."""
        return key in self._updates_in_progress

    def mark_being_updated(self, key: CacheKey) -> None:
        """Informs that update has been started.
        Should be called only if 'is_being_updated' returned False (and since then IO-loop has not been lost)..
        Calls to 'is_being_updated' will return True until 'mark_updated' will be called."""
        if key in self._updates_in_progress:
            raise ValueError('Key {} is already being updated'.format(key))

        future = coerced._future()
        self._updates_in_progress[key] = future

        def complete_on_timeout_passed():
            if key not in self._updates_in_progress:
                return
            if self._updates_in_progress[key] == future and not self._updates_in_progress[key].done():
                self.logger.debug('Update task timed out - notifying clients awaiting for key %s', key)
                self._updates_in_progress[key].set_result(None)
                self._updates_in_progress.pop(key)

        coerced._call_later(self._update_lock_timeout, complete_on_timeout_passed)

    def mark_updated(self, key: CacheKey, entry: CacheEntry) -> None:
        """Informs that update has been finished.
        Calls to 'is_being_updated' will return False until 'mark_being_updated' will be called."""
        if key not in self._updates_in_progress:
            raise ValueError('Key {} is not being updated'.format(key))
        update = self._updates_in_progress.pop(key)
        update.set_result(entry)

    def mark_update_aborted(self, key: CacheKey) -> None:
        """Informs that update failed to complete.
        Calls to 'is_being_updated' will return False until 'mark_being_updated' will be called."""
        if key not in self._updates_in_progress:
            raise ValueError('Key {} is not being updated'.format(key))
        update = self._updates_in_progress.pop(key)
        update.set_result(None)

    def await_updated(self, key: CacheKey) -> Awaitable[Optional[CacheEntry]]:
        """Waits (asynchronously) until update in progress has benn finished.
        Returns updated entry or None if update failed/timed-out.
        Should be called only if 'is_being_updated' returned True (and since then IO-loop has not been lost)."""
        if not self.is_being_updated(key):
            raise ValueError('Key {} is not being updated'.format(key))
        return self._updates_in_progress[key]
