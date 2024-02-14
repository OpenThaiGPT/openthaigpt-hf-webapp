import asyncio
import functools
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


def async_to_sync(f: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    @functools.wraps(f)
    def sync_func(*args: Any, **kwargs: Any) -> T:
        return asyncio.run(f(*args, **kwargs))  # type: ignore

    return sync_func


if __name__ == "__main__":
    # Usage example
    @async_to_sync
    async def async_example() -> str:
        await asyncio.sleep(1)
        return "Hello from async function!"

    result = async_example()
    print(result)  # This will print "Hello from async function!"
