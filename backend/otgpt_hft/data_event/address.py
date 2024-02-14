from typing import Annotated, Tuple

from pydantic import (
    PlainSerializer,
    RootModel,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)

# Address = RootModel[Tuple[str, ...]]


def address_wvalidator(
    v: str | Tuple[str, ...],
    handler: ValidatorFunctionWrapHandler,
    info: ValidationInfo,
) -> Tuple[str, ...]:
    if info.mode == "json":
        assert isinstance(v, str), f"expecting JSON of type: string, got {type(v)}"
        address = tuple(v.split(":"))
        return handler(address)

    assert info.mode == "python"
    return handler(v)


# NOTE: we don't need WrapSerializer, PlainSerializer is enough
# def address_wserializer(
#     v: Tuple[str, ...] | Any,
#     handler: SerializerFunctionWrapHandler,
# ) -> str:
#     if not isinstance(v, tuple):
#         raise ValueError(f"expecting instance of type: Address, got {type(v)}")
#     return ":".join(v)


WAddress = RootModel[
    Annotated[
        Tuple[str, ...],
        WrapValidator(address_wvalidator),
        PlainSerializer(":".join, return_type=str, when_used="json"),
        # NOTE: we don't need WrapSerializer, PlainSerializer is enough
        # WrapSerializer(address_wserializer),
    ]
]
