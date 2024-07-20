from typing import Callable, TypeVar, overload

from memoize.configuration import CacheConfiguration
from memoize.invalidation import InvalidationSupport

FN = TypeVar('FN', bound=Callable)


@overload
def memoize(configuration: CacheConfiguration = None,
            invalidation: InvalidationSupport = None) -> Callable[[FN], FN]: ...


@overload
def memoize(method: FN,
            configuration: CacheConfiguration = None,
            invalidation: InvalidationSupport = None) -> FN: ...
