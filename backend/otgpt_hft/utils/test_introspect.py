from typing import Any, Dict, List, Tuple, Type

import pytest

from .introspect import get_generic_args, get_generic_base


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (List[int], list),
        (List[float], list),
        (List[str], list),
        (Dict[str, str], dict),
        (Dict[int, str], dict),
        (Dict[int, int], dict),
    ],  # type: ignore
)
def test_get_generic_base(test_input: Type[Any], expected: Type[Any]):
    assert get_generic_base(test_input, None) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (List[int], (int,)),
        (List[float], (float,)),
        (List[str], (str,)),
        (Dict[str, str], (str, str)),
        (Dict[int, str], (int, str)),
        (Dict[int, int], (int, int)),
    ],
)
def test_get_generic_args(test_input: Type[Any], expected: Tuple[Type[Any], ...]):
    assert get_generic_args(test_input, None) == expected
