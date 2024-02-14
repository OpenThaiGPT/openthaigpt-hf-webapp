from typing import Literal, Tuple, Union

import pytest
from pydantic import RootModel, ValidationError

from .channel import wrap_channel_type

WChannel = RootModel[wrap_channel_type(Tuple[Literal["test"], int])]


def test_wchannel_serialization():
    si = WChannel.model_validate(("test", 1))
    assert si.model_dump_json() == '"test/i:1"'

    si = WChannel.model_validate(("test", 10))
    assert si.model_dump_json() == '"test/i:10"'

    with pytest.raises(ValidationError):
        si = WChannel.model_validate(("test", "eiei"))

    with pytest.raises(ValidationError):
        si = WChannel.model_validate(("eiei", 1))


def test_wchannel_deserialization():
    si = WChannel.model_validate_json('"test/i:1"')
    assert si.root == ("test", 1)

    si = WChannel.model_validate_json('"test/i:10"')
    assert si.root == ("test", 10)

    with pytest.raises(ValidationError):
        si = WChannel.model_validate_json('"test/eiei"')

    with pytest.raises(ValidationError):
        si = WChannel.model_validate_json('"eiei/i:1"')


WDBChannelName = Union[
    # list of data entry in the dataset
    Tuple[Literal["index"], str, str],
    # list of data splits in the dataset
    Tuple[Literal["index"], str],
    # list of all datasets
    Tuple[Literal["index"]],
]

WDBChannelName = RootModel[wrap_channel_type(WDBChannelName)]


def test_wdbchannel_serialization():
    si = WDBChannelName.model_validate(("index",))
    assert si.model_dump_json() == '"index"'

    si = WDBChannelName.model_validate(("index", "test"))
    assert si.model_dump_json() == '"index/test"'

    si = WDBChannelName.model_validate(("index", "test", "test"))
    assert si.model_dump_json() == '"index/test/test"'


def test_wdbchannel_deserialization():
    si = WDBChannelName.model_validate_json('"index"')
    assert si.root == ("index",)

    si = WDBChannelName.model_validate_json('"index/test"')
    assert si.root == ("index", "test")

    si = WDBChannelName.model_validate_json('"index/test/test"')
    assert si.root == ("index", "test", "test")

    with pytest.raises(ValidationError):
        si = WDBChannelName.model_validate_json('"inde/eiei"')

    with pytest.raises(ValidationError):
        si = WDBChannelName.model_validate_json('"index/i:1"')
