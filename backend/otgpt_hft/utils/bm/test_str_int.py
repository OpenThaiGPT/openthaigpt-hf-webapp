import pytest

from .str_int import WStrInt


def test_waddress_serialization():
    si = WStrInt(1)
    assert si.model_dump_json() == '"i:1"'

    si = WStrInt("A")
    assert si.model_dump_json() == '"A"'

    with pytest.raises(ValueError):
        si = WStrInt("i:e")

    with pytest.raises(ValueError):
        si = WStrInt("i:1")


def test_waddress_deserialization():
    si = WStrInt.model_validate_json('"i:1"')
    assert si.root == 1

    si = WStrInt.model_validate_json('"A"')
    assert si.root == "A"
