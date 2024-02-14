from typing import Annotated, Tuple, Type, TypeVar

from pydantic import (
    PlainSerializer,
    RootModel,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)

from .str_int import str_to_si


def channel_wvalidator(
    v: str | Tuple[str | int, ...],
    handler: ValidatorFunctionWrapHandler,
    info: ValidationInfo,
) -> Tuple[str, ...]:
    if isinstance(v, str):
        address = tuple(str_to_si(seg) for seg in v.split("/"))
        return handler(address)
    else:
        assert isinstance(v, tuple)
        return handler(v)


def seg_to_str(seg: str | int) -> str:
    if isinstance(seg, int):
        return f"i:{seg}"
    return seg


def join_channel(channel: Tuple[str | int, ...]) -> str:
    return "/".join(seg_to_str(seg) for seg in channel)


CH = TypeVar("CH", bound=Tuple[str | int, ...])


def wrap_channel_type(tuple_type: Type[CH]) -> Type[CH]:
    return Annotated[
        tuple_type,
        WrapValidator(channel_wvalidator),
        PlainSerializer(join_channel, return_type=str, when_used="json"),
    ]
