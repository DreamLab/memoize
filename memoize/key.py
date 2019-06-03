"""
[API] Provides interface (and built-in implementations)
how cache keys are constructed.
This interface is used in cache configuration.
"""

from abc import abstractmethod, ABCMeta

from typing import Tuple, Any, Dict


class KeyExtractor(metaclass=ABCMeta):
    """ Provides logic of cache key construction. """

    @abstractmethod
    def format_key(self, method_reference, call_args: Tuple[Any, ...], call_kwargs: Dict[str, Any]) -> str:
        """Using wrapped method object, call args and call keyword args, prepare cache entry key."""
        raise NotImplementedError()


class EncodedMethodReferenceAndArgsKeyExtractor(KeyExtractor):
    """Encodes method reference, args & kwargs to string and uses that as cache entry key.
    This KeyExtractor is object-centric and creates different keys for different objects of the same type 
    (so when you create new objects - for instance after app restart - old entries in external store 
    like Redis will be unreachable)."""

    def format_key(self, method_reference, call_args: Tuple[Any, ...], call_kwargs: Dict[str, Any]) -> str:
        return str((method_reference, call_args, call_kwargs,))


class EncodedMethodNameAndArgsKeyExtractor(KeyExtractor):
    """Encodes method name, args & kwargs to string and uses that as cache entry key.
    This KeyExtractor is class-centric and creates same keys for all objects of the same type.
    
    Note: If wrapped function is a method (has 'self' as first positional arg) you may want to exclude 'self' from key
    by setting 'skip_first_arg_as_self' flag. 
    For static methods of ordinary functions flag should be set to 'False'.
        
    Warning: uses method name only, so be cautious and do not wrap methods of different classes with the same names 
    while using same store and 'skip_first_arg_as_self' set to False."""

    def __init__(self, skip_first_arg_as_self=False) -> None:
        self._skip_first_arg_as_self = skip_first_arg_as_self

    def format_key(self, method_reference, call_args: Tuple[Any, ...], call_kwargs: Dict[str, Any]) -> str:
        if self._skip_first_arg_as_self:
            call_args = call_args[1:]

        return str((method_reference.__name__, call_args, call_kwargs,))

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{name}[skip_first_arg_as_self={skip_first_arg_as_self}]".format(
            name=self.__class__, skip_first_arg_as_self=self._skip_first_arg_as_self)
