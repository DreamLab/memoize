from typing import Tuple, Any, Dict, Callable

from memoize.key import KeyExtractor
from memoize.storage import CacheStorage


class InvalidationSupport(object):
    """ Allows to manually invalidate cache entries. """

    def __init__(self) -> None:
        self.__initialized = False

    def _initialized(self) -> bool:
        """ Executed internally by the library. """
        return self.__initialized

    def _initialize(self, cache_storage: CacheStorage, key_extractor: KeyExtractor,
                    method_reference: Callable) -> None:
        """ Executed internally by the library. """
        self.__cache_storage = cache_storage
        self.__key_extractor = key_extractor
        self.__method_reference = method_reference
        self.__initialized = True

    async def invalidate_for_arguments(self, call_args: Tuple[Any, ...], call_kwargs: Dict[str, Any]) -> None:
        """ Provide agrs and kwargs for which you want to invalidate cache. """
        if not self._initialized():
            raise RuntimeError("Uninitialized: InvalidationSupport should be passed to @memoize to have it initialized")
        key = self.__key_extractor.format_key(self.__method_reference, call_args, call_kwargs)
        await self.__cache_storage.release(key)

