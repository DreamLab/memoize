"""
[API] Provides interface (and built-in implementations)
of full cache configuration.
"""

from abc import ABCMeta, abstractmethod
from datetime import timedelta

from memoize.entrybuilder import CacheEntryBuilder, ProvidedLifeSpanCacheEntryBuilder
from memoize.eviction import EvictionStrategy, LeastRecentlyUpdatedEvictionStrategy
from memoize.key import KeyExtractor, EncodedMethodReferenceAndArgsKeyExtractor
from memoize.storage import CacheStorage
from memoize.storage import LocalInMemoryCacheStorage


class NotConfiguredCacheCalledException(Exception):
    pass


class CacheConfiguration(metaclass=ABCMeta):
    """ Provides configuration for cache. """

    @abstractmethod
    def configured(self) -> bool:
        """ Cache will raise NotConfiguredCacheCalledException if this returns false.
        May be useful if when cache is reconfigured in runtime. """
        raise NotImplementedError()

    @abstractmethod
    def method_timeout(self) -> timedelta:
        """ Defines how much time wrapped method can take to complete. """
        raise NotImplementedError()

    @abstractmethod
    def entry_builder(self) -> CacheEntryBuilder:
        """ Determines which CacheEntryBuilder is to be used by cache. """
        raise NotImplementedError()

    @abstractmethod
    def key_extractor(self) -> KeyExtractor:
        """ Determines which KeyExtractor is to be used by cache. """
        raise NotImplementedError()

    @abstractmethod
    def storage(self) -> CacheStorage:
        """ Determines which CacheStorage is to be used by cache. """
        raise NotImplementedError()

    @abstractmethod
    def eviction_strategy(self) -> EvictionStrategy:
        """ Determines which EvictionStrategy is to be used by cache. """
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{name}[configured={configured}, method_timeout={method_timeout}, entry_builder={entry_builder}," \
               " key_extractor={key_extractor}, storage={storage}, eviction_strategy={eviction_strategy}]" \
            .format(name=self.__class__, configured=self.configured(), method_timeout=self.method_timeout(),
                    entry_builder=self.entry_builder(), key_extractor=self.key_extractor(), storage=self.storage(),
                    eviction_strategy=self.eviction_strategy())


class MutableCacheConfiguration(CacheConfiguration):
    """ Mutable configuration which can be change at runtime.
    May be also used to customize existing configuration (for example a default one, which is immutable)."""

    def __init__(self, configured: bool, storage: CacheStorage, key_extractor: KeyExtractor,
                 eviction_strategy: EvictionStrategy, entry_builder: CacheEntryBuilder,
                 method_timeout: timedelta) -> None:
        self.__storage = storage
        self.__configured = configured
        self.__key_extractor = key_extractor
        self.__entry_builder = entry_builder
        self.__method_timeout = method_timeout
        self.__eviction_strategy = eviction_strategy

    @staticmethod
    def initialized_with(configuration: CacheConfiguration) -> 'MutableCacheConfiguration':
        return MutableCacheConfiguration(
            storage=configuration.storage(),
            configured=configuration.configured(),
            key_extractor=configuration.key_extractor(),
            entry_builder=configuration.entry_builder(),
            method_timeout=configuration.method_timeout(),
            eviction_strategy=configuration.eviction_strategy(),
        )

    def method_timeout(self) -> timedelta:
        return self.__method_timeout

    def key_extractor(self) -> KeyExtractor:
        return self.__key_extractor

    def configured(self) -> bool:
        return self.__configured

    def storage(self) -> CacheStorage:
        return self.__storage

    def entry_builder(self) -> CacheEntryBuilder:
        return self.__entry_builder

    def eviction_strategy(self) -> EvictionStrategy:
        return self.__eviction_strategy

    def set_method_timeout(self, value: timedelta) -> 'MutableCacheConfiguration':
        self.__method_timeout = value
        return self

    def set_key_extractor(self, value: KeyExtractor) -> 'MutableCacheConfiguration':
        self.__key_extractor = value
        return self

    def set_configured(self, value: bool) -> 'MutableCacheConfiguration':
        self.__configured = value
        return self

    def set_storage(self, value: CacheStorage) -> 'MutableCacheConfiguration':
        self.__storage = value
        return self

    def set_entry_builder(self, value: CacheEntryBuilder) -> 'MutableCacheConfiguration':
        self.__entry_builder = value
        return self

    def set_eviction_strategy(self, value: EvictionStrategy) -> 'MutableCacheConfiguration':
        self.__eviction_strategy = value
        return self


class DefaultInMemoryCacheConfiguration(CacheConfiguration):
    """ Default parameters that describe in-memory cache. Be ware that parameters used do not suit every case. """

    def __init__(self, capacity: int = 4096, method_timeout: timedelta = timedelta(minutes=2),
                 update_after: timedelta = timedelta(minutes=10),
                 expire_after: timedelta = timedelta(minutes=30)) -> None:
        self.__configured = True
        self.__method_timeout = method_timeout
        self.__storage = LocalInMemoryCacheStorage()
        self.__key_extractor = EncodedMethodReferenceAndArgsKeyExtractor()
        self.__eviction_strategy = LeastRecentlyUpdatedEvictionStrategy(capacity=capacity)
        self.__entry_builder = ProvidedLifeSpanCacheEntryBuilder(update_after=update_after, expire_after=expire_after)

    def configured(self) -> bool:
        return self.__configured

    def method_timeout(self) -> timedelta:
        return self.__method_timeout

    def storage(self) -> LocalInMemoryCacheStorage:
        return self.__storage

    def entry_builder(self) -> ProvidedLifeSpanCacheEntryBuilder:
        return self.__entry_builder

    def eviction_strategy(self) -> LeastRecentlyUpdatedEvictionStrategy:
        return self.__eviction_strategy

    def key_extractor(self) -> EncodedMethodReferenceAndArgsKeyExtractor:
        return self.__key_extractor
