"""
[Internal use only] Contains implementation of cache entry.
"""

import datetime

from typing import Any

CacheKey = str
CachedValue = Any


class CacheEntry:
    """Implementation of cache entry used internally"""

    def __init__(self, created: datetime.datetime, update_after: datetime.datetime, expires_after: datetime.datetime,
                 value: CachedValue) -> None:
        self.value = value
        self.created = created
        self.update_after = update_after
        self.expires_after = expires_after
        self.__hashable = (self.value, self.created, self.update_after, self.expires_after)

    def __repr__(self) -> str:
        return "CacheEntry[value={value},created={created},update_after={update_after},expires_after={expires_after}]" \
            .format(value=self.value, created=self.created,
                    update_after=self.update_after, expires_after=self.expires_after)

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, o) -> bool:
        return self.__hashable.__eq__(o.__hashable) if isinstance(o, CacheEntry) else False

    def __hash__(self) -> int:
        return hash(self.__hashable)
