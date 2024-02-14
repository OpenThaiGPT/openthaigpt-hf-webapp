from typing import Annotated, Any, Tuple

from pydantic import (
    PlainSerializer,
    RootModel,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)


def str_int_wvalidator(
    v: str | int,
    handler: ValidatorFunctionWrapHandler,
    info: ValidationInfo,
) -> Tuple[str, ...]:
    if info.mode == "json":
        assert isinstance(v, str), f"expecting JSON of type: string, got {type(v)}"
        return handler(str_to_si(v))

    assert info.mode == "python"
    if isinstance(v, str) and v.startswith("i:"):
        raise ValueError("cannot have string begin with the reserved word 'i:'")
    return handler(v)


def str_to_si(v: str | Any) -> str | int:
    if v.startswith("i:"):
        return int(v[2:])
    else:
        return v


def si_to_str(si: str | int | Any) -> str:
    if isinstance(si, str):
        return si
    elif isinstance(si, int):
        return "i:" + str(si)
    else:
        raise TypeError("must be either `str` or `int`")


str_int_pserializer = si_to_str


StrInt = str | int

WStrInt = RootModel[
    Annotated[
        StrInt,
        WrapValidator(str_int_wvalidator),
        PlainSerializer(str_int_pserializer, return_type=str, when_used="json"),
    ]
]
