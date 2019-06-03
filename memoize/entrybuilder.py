"""
[API] Provides interface (and built-in implementations)
how cache entries should be constructed (responsibility of expiry & update after times lies here).
This interface is used in cache configuration.
"""

import datetime
from abc import ABCMeta, abstractmethod

from memoize.entry import CacheKey, CachedValue, CacheEntry


class CacheEntryBuilder(metaclass=ABCMeta):
    @abstractmethod
    def build(self, key: CacheKey, value: CachedValue) -> CacheEntry:
        """Constructs cache entry object (sets creation time, can transform value, governs update/expiration times)."""
        raise NotImplementedError()


class ProvidedLifeSpanCacheEntryBuilder(CacheEntryBuilder):
    """CacheEntryBuilder which uses constant delays independent form values that are cached"""
    def __init__(self, update_after: datetime.timedelta = datetime.timedelta(minutes=10),
                 expire_after: datetime.timedelta = datetime.timedelta(minutes=30)) -> None:
        """
        Builder that sets update/expire times using provided constants.
        :param datetime.timedelta update_after:         when background/async updates should start; default = 10 minutes
        :param datetime.timedelta expire_after:         when entry starts being out-of-date; default = 30 minutes
        """
        self._expires_after = expire_after
        self._update_after = update_after

    def update_timeouts(self, update_after: datetime.timedelta, expire_after: datetime.timedelta) -> None:
        self._expires_after = expire_after
        self._update_after = update_after

    def build(self, key: CacheKey, value: CachedValue) -> CacheEntry:
        now = datetime.datetime.utcnow()
        return CacheEntry(created=now,
                          update_after=now + self._update_after,
                          expires_after=now + self._expires_after,
                          value=value)

    def __str__(self) -> str:
        return "{}[update_after={},expire_after={}]".format(self.__class__, self._update_after, self._expires_after)
