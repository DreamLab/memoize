import pytest

from tests.py310workaround import fix_python_3_10_compatibility

fix_python_3_10_compatibility()

import codecs
import json
import pickle
from datetime import datetime, timezone
from pickle import HIGHEST_PROTOCOL, DEFAULT_PROTOCOL
from unittest.mock import Mock

from memoize.entry import CacheEntry
from memoize.serde import PickleSerDe, EncodingSerDe, JsonSerDe


@pytest.mark.asyncio(scope="class")
class TestEncodingSerDe:

    async def test_should_apply_encoding_on_wrapped_serde_results(self):
        # given
        cache_entry = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")
        serde = Mock()
        serde.serialize.return_value = b"in"
        wrapper = EncodingSerDe(serde, binary_encoding="base64")

        # when
        bytes = wrapper.serialize(cache_entry)

        # then
        expected = codecs.encode(b"in", 'base64')
        assert bytes == expected
        serde.serialize.assert_called_once_with(cache_entry)

    async def test_should_apply_decoding_on_wrapped_serde_results(self):
        # given
        cache_entry = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")
        encoded_cache_entry = codecs.encode(b'y', 'base64')
        serde = Mock()
        serde.deserialize.return_value = cache_entry
        wrapper = EncodingSerDe(serde, binary_encoding="base64")

        # when
        data = wrapper.deserialize(encoded_cache_entry)

        # then
        assert data == cache_entry
        serde.deserialize.assert_called_once_with(b'y')

    async def test_e2e_integration_with_sample_serde(self):
        # given
        cache_entry = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")
        serde = PickleSerDe(pickle_protocol=HIGHEST_PROTOCOL)  # sample serde
        wrapper = EncodingSerDe(serde, binary_encoding="base64")

        # when
        encoded_cache_entry = wrapper.serialize(cache_entry)
        data = wrapper.deserialize(encoded_cache_entry)

        # then
        assert data == cache_entry


class JsonSerDeTests:

    async def test_should_encode_as_readable_json(self):
        # given
        cache_entry = CacheEntry(datetime.fromtimestamp(1, timezone.utc), datetime.fromtimestamp(2, timezone.utc),
                                 datetime.fromtimestamp(3, timezone.utc), "in")
        serde = JsonSerDe(string_encoding='utf-8')

        # when
        bytes = serde.serialize(cache_entry)

        # then
        parsed = json.loads(codecs.decode(bytes))  # verified this way due to json/ujson slight separator differences
        assert parsed == {"created": cache_entry.created.timestamp(),
                          "update_after": cache_entry.update_after.timestamp(),
                          "expires_after": cache_entry.expires_after.timestamp(),
                          "value": "in"}

    async def test_should_decode_readable_json(self):
        # given
        serde = JsonSerDe(string_encoding='utf-8')

        # when
        bytes = serde.deserialize(b'{"created":1,"update_after":2,"expires_after":3,"value":"value"}')

        # then
        cache_entry = CacheEntry(datetime.fromtimestamp(1, timezone.utc), datetime.fromtimestamp(2, timezone.utc),
                                 datetime.fromtimestamp(3, timezone.utc), "value")
        assert bytes == cache_entry

    async def test_should_apply_value_transformations_on_serialization(self):
        # given
        cache_entry = CacheEntry(datetime.fromtimestamp(1, timezone.utc), datetime.fromtimestamp(2, timezone.utc),
                                 datetime.fromtimestamp(3, timezone.utc), "in")
        encode = Mock(return_value="out")
        decode = Mock(return_value="in")
        serde = JsonSerDe(string_encoding='utf-8', value_to_reversible_repr=encode, reversible_repr_to_value=decode)

        # when
        bytes = serde.serialize(cache_entry)

        # then
        parsed = json.loads(codecs.decode(bytes))  # verified this way due to json/ujson slight separator differences
        assert parsed == {"created": cache_entry.created.timestamp(),
                          "update_after": cache_entry.update_after.timestamp(),
                          "expires_after": cache_entry.expires_after.timestamp(),
                          "value": "out"}
        encode.assert_called_once_with("in")

    async def test_should_apply_value_transformations_on_deserialization(self):
        # given
        encode = Mock(return_value="in")
        decode = Mock(return_value="out")
        serde = JsonSerDe(string_encoding='utf-8', value_to_reversible_repr=encode, reversible_repr_to_value=decode)

        # when
        data = serde.deserialize(b'{"created":1,"update_after":2,"expires_after":3,"value":"in"}')

        # then
        cache_entry = CacheEntry(datetime.fromtimestamp(1, timezone.utc), datetime.fromtimestamp(2, timezone.utc),
                                 datetime.fromtimestamp(3, timezone.utc), "out")
        assert data == cache_entry
        decode.assert_called_once_with("in")


class PickleSerDeTests:

    async def test_should_pickle_using_highest_protocol(self):
        # given
        cache_entry = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")
        serde = PickleSerDe(pickle_protocol=HIGHEST_PROTOCOL)

        # when
        bytes = serde.serialize(cache_entry)

        # then
        expected = pickle.dumps(cache_entry, protocol=HIGHEST_PROTOCOL)
        assert bytes == expected

    async def test_should_unpickle_using_highest_protocol(self):
        # given
        cache_entry = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")
        serde = PickleSerDe(pickle_protocol=HIGHEST_PROTOCOL)
        bytes = pickle.dumps(cache_entry, protocol=HIGHEST_PROTOCOL)

        # when
        data = serde.deserialize(bytes)

        # then
        assert data == cache_entry

    async def test_should_pickle_using_default_protocol(self):
        # given
        cache_entry = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")
        serde = PickleSerDe(pickle_protocol=DEFAULT_PROTOCOL)

        # when
        bytes = serde.serialize(cache_entry)

        # then
        expected = pickle.dumps(cache_entry, protocol=DEFAULT_PROTOCOL)
        assert bytes == expected

    async def test_should_unpickle_using_default_protocol(self):
        # given
        cache_entry = CacheEntry(datetime.now(), datetime.now(), datetime.now(), "value")
        serde = PickleSerDe(pickle_protocol=DEFAULT_PROTOCOL)
        bytes = pickle.dumps(cache_entry, protocol=DEFAULT_PROTOCOL)

        # when
        data = serde.deserialize(bytes)

        # then
        assert data == cache_entry
