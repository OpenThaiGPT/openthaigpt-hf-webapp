from typing import Iterable, Optional, TypeVar

T = TypeVar("T")


def take_one(iterable: Iterable[T]) -> Optional[T]:
    """
    Takes one item from an iterable and returns it.

    Args:
        iterable: The iterable from which to take one item.

    Returns:
        item: The first item from the iterable.
    """
    for item in iterable:
        return item
