from __future__ import annotations

from typing import Any, Tuple, Type, Union, TypeVar


T = TypeVar("T")


def get_baseclass(type_: Type[Any], default: T) -> Union[Tuple[Type[Any], ...], T]:
    return getattr(type_, "__orig_bases__", default)


def get_generic_base(type_: Type[Any], default: T) -> Union[Type[Any], T]:
    return getattr(type_, "__origin__", default)


def get_generic_args(type_: Type[Any], default: T) -> Union[Tuple[Type[Any], ...], T]:
    return getattr(type_, "__args__", default)
