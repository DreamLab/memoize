from typing import Callable, TypeVar, overload, Optional

from memoize.configuration import CacheConfiguration
from memoize.invalidation import InvalidationSupport
from memoize.statuses import UpdateStatuses

FN = TypeVar('FN', bound=Callable)


@overload
def memoize(*, configuration: Optional[CacheConfiguration] = None,
            invalidation: Optional[InvalidationSupport] = None, update_statuses: Optional[UpdateStatuses] = None) -> Callable[[FN], FN]: ...


@overload
def memoize(method: FN, configuration: Optional[CacheConfiguration] = None,
            invalidation: Optional[InvalidationSupport] = None, update_statuses: Optional[UpdateStatuses] = None) -> FN: ...
