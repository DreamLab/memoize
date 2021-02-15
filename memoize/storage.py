"""
[API] Provides interface (and built-in implementations)
of storage for cache entries.
This interface is used in cache configuration.
"""

from abc import ABCMeta, abstractmethod

from typing import Optional, Dict

from memoize.entry import CacheKey, CacheEntry


class CacheStorage(metaclass=ABCMeta):
    @abstractmethod
    async def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """Request value for given key. If currently there is no such value, returns None. 
        Has to be async."""
        raise NotImplementedError()

    @abstractmethod
    async def offer(self, key: CacheKey, entry: CacheEntry) -> None:
        """Offer entry to be stored. If storage already has more relevant data, offer may be declined. 
        Has to be async."""
        raise NotImplementedError()

    @abstractmethod
    async def release(self, key: CacheKey) -> None:
        """Declare that current client does not need entry determined by given key. 
        Has to be async."""
        raise NotImplementedError()


class LocalInMemoryCacheStorage(CacheStorage):
    """Implementation that stores all entries as-is in a dictionary residing solely in memory."""
    def __init__(self) -> None:
        self._data = {}  # type: Dict[CacheKey, CacheEntry]

    async def offer(self, key: CacheKey, entry: CacheEntry) -> None:
        self._data[key] = entry

    async def release(self, key: CacheKey) -> None:
        self._data.pop(key, None)

    async def get(self, key: CacheKey) -> Optional[CacheEntry]:
        return self._data.get(key, None)
