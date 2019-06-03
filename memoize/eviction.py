"""
[API] Provides interface (and built-in implementations)
how cache entries should be constructed (responsibility of expiry & update after times lies here).
This interface is used in cache configuration.
"""

import collections
from abc import ABCMeta, abstractmethod

from typing import Optional

from memoize.entry import CacheKey, CacheEntry


class EvictionStrategy(metaclass=ABCMeta):
    @abstractmethod
    def mark_read(self, key: CacheKey) -> None:
        """Informs strategy that entry related to given key was read by current client."""
        raise NotImplementedError()

    @abstractmethod
    def mark_written(self, key: CacheKey, entry: CacheEntry) -> None:
        """Informs strategy that entry related to given key was updated by current client."""
        raise NotImplementedError()

    @abstractmethod
    def mark_released(self, key: CacheKey) -> None:
        """Informs strategy that entry related to given key was deemed non-essential by current client."""
        raise NotImplementedError()

    @abstractmethod
    def next_to_release(self) -> Optional[CacheKey]:
        """Returns element that should be released by the current client according to this strategy (or None)."""
        raise NotImplementedError()


class LeastRecentlyUpdatedEvictionStrategy(EvictionStrategy):
    def __init__(self, capacity=4096):
        self._capacity = capacity
        self._data = collections.OrderedDict()

    def mark_read(self, key: CacheKey) -> None:
        pass

    def mark_released(self, key: CacheKey) -> None:
        self._data.pop(key, None)

    def mark_written(self, key: CacheKey, entry: CacheEntry) -> None:
        self._data.pop(key, None)
        self._data[key] = None

    def next_to_release(self) -> Optional[CacheKey]:
        entries = len(self._data)
        if entries > 0 and entries > self._capacity:
            key, _ = self._data.popitem(last=False)
            return key
        return None

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{name}[capacity={capacity}]".format(name=self.__class__, capacity=self._capacity)


class NoEvictionStrategy(EvictionStrategy):
    """
    Strategy to be used when delegating eviction to cache itself.
    This strategy performs no actions.
    """

    def mark_released(self, key: CacheKey) -> None:
        return None

    def mark_read(self, key: CacheKey) -> None:
        return None

    def next_to_release(self) -> Optional[CacheKey]:
        return None

    def mark_written(self, key: CacheKey, entry: CacheEntry) -> None:
        return None
