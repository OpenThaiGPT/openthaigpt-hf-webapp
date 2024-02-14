from .address import WAddress

TEST_STRING = '"eiei:gum"'
TEST_PY_OBJ = ("eiei", "gum")


def test_waddress_serialization():
    add = WAddress(TEST_PY_OBJ)

    assert add.model_dump_json() == TEST_STRING


def test_waddress_deserialization():
    add = WAddress.model_validate_json(TEST_STRING)

    assert add.root == TEST_PY_OBJ
