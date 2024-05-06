import copy
from abc import ABCMeta, abstractmethod
from typing import Any

ValueType = Any


class Postprocessing(metaclass=ABCMeta):
    @abstractmethod
    def apply(self, original: ValueType) -> ValueType:
        """Transforms value just before returning from the cache."""
        raise NotImplementedError()


class NoPostprocessing(Postprocessing):
    def apply(self, original: ValueType) -> ValueType:
        """Applies no postprocessing (returns original value)."""
        return original


class DeepcopyPostprocessing(Postprocessing):
    def apply(self, original: ValueType) -> ValueType:
        """
        Performs deep copy of the value. Useful when you want to prevent modifying the value cached in memory
        (so callers could modify their copies safely).

        Have in mind that this operation may be expensive,
        and may not be suitable for all types of values (see docs on copy.deepcopy).
        """
        return copy.deepcopy(original)
