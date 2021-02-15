"""
[API] Provides interface (and built-in implementations)
of SerDe that may be used to implement cache storage.
"""

import codecs
import pickle

try:
    import ujson as json
except:
    # ignoring type error as mypy falsely reports json is already imported
    import json  # type: ignore
from abc import ABCMeta, abstractmethod
from datetime import datetime

from typing import Callable, Any

from memoize.entry import CacheEntry, CachedValue


class SerDe(metaclass=ABCMeta):
    """Responsible for (de)serialization of values handled by CacheStorage (if SerDes are supported)."""

    @abstractmethod
    def serialize(self, entry: CacheEntry) -> bytes:
        raise NotImplementedError()

    @abstractmethod
    def deserialize(self, data: bytes) -> CacheEntry:
        raise NotImplementedError()


class PickleSerDe(SerDe):
    """Uses encoded pickles as binary representation."""

    def __init__(self, pickle_protocol=pickle.HIGHEST_PROTOCOL) -> None:
        self.__pickle_protocol = pickle_protocol

    def deserialize(self, data: bytes) -> CacheEntry:
        return pickle.loads(data, )

    def serialize(self, entry: CacheEntry) -> bytes:
        return pickle.dumps(entry, protocol=self.__pickle_protocol)


JsonReversibleObject = Any


class JsonSerDe(SerDe):
    """Uses encoded json string as binary representation. 
    Value of cached type should consist of types which are json-reversible (json.loads(json.dumps(v)) is equal to v)
    or one should provide (by constructor) functions converting values to/from such representation."""

    def __init__(self, string_encoding: str = "utf-8",
                 value_to_reversible_repr: Callable[[CachedValue], JsonReversibleObject] = lambda x: x,
                 reversible_repr_to_value: Callable[[JsonReversibleObject], CachedValue] = lambda x: x, ) -> None:
        self.__string_encoding = string_encoding
        self.__reversible_repr_to_value = reversible_repr_to_value
        self.__value_to_reversible_repr = value_to_reversible_repr

    def deserialize(self, data: bytes) -> CacheEntry:
        as_dict = json.loads(codecs.decode(data, self.__string_encoding))
        return CacheEntry(
            created=datetime.utcfromtimestamp(as_dict['created']),
            update_after=datetime.utcfromtimestamp(as_dict['update_after']),
            expires_after=datetime.utcfromtimestamp(as_dict['expires_after']),
            value=self.__reversible_repr_to_value(as_dict['value']),
        )

    def serialize(self, entry: CacheEntry) -> bytes:
        return codecs.encode(json.dumps({
            'created': entry.created.timestamp(),
            'update_after': entry.update_after.timestamp(),
            'expires_after': entry.expires_after.timestamp(),
            'value': self.__value_to_reversible_repr(entry.value),
        }), self.__string_encoding)


# types are ignored as everything works just fine with bytes instead of strings
class EncodingSerDe(SerDe):
    """Applies extra encoding to the data (for instance compression when 'zip' or 'bz2' codec used)."""

    def __init__(self, serde: SerDe, binary_encoding: str = "zip") -> None:
        super().__init__()
        self.__binary_encoding = binary_encoding
        self.__serde = serde

    def deserialize(self, value: bytes) -> CacheEntry:
        decoded = codecs.decode(value, self.__binary_encoding)
        return self.__serde.deserialize(decoded)  # type: ignore

    def serialize(self, value: CacheEntry) -> bytes:
        serialized = self.__serde.serialize(value)
        return codecs.encode(serialized, self.__binary_encoding)  # type: ignore
