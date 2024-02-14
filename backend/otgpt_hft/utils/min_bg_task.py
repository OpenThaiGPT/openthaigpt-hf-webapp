import asyncio
from typing import Any, Callable, Coroutine, List, Optional, TypeVar

T = TypeVar("T")


class MinBGTasks:
    """
    A class for managing background tasks in an asyncio event loop.

    This class allows for the running and tracking of asynchronous tasks in the background.
    It provides mechanisms to handle exceptions in these tasks and to query the number of
    tasks currently running.

    Attributes:
        _tasks (List[asyncio.Task[Any]]): A list of asyncio tasks that are currently running.
        _loop (asyncio.AbstractEventLoop): The asyncio event loop in which tasks are running.
        _on_task_exception (Optional[Callable[[Exception], None]]): An optional callable that is invoked
            when an exception occurs in a background task.

    Args:
        loop (asyncio.AbstractEventLoop): The asyncio event loop to run tasks in.
        on_task_exception (Optional[Callable[[Exception], None]], optional): An optional callable that
            is called when an exception occurs in a background task. Defaults to None.

    Methods:
        __len__() -> int:
            Returns the number of pending tasks.
        run(coroutine: Coroutine[Any, Any, T]) -> asyncio.Task[Optional[T]]:
            Runs a coroutine in the background and returns a task object.
        _on_task_complete(task: asyncio.Task[Any]):
            A callback method to remove a task from the list of running tasks once it is complete.
    """

    def __init__(
        self,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        on_task_exception: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        self._tasks: List[asyncio.Task[Any]] = []
        self._loop = loop
        self._on_task_exception = on_task_exception

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        assert self._loop is None, "event loop is already set"
        self._loop = loop

    def __len__(self) -> int:
        """
        Returns the number of currently running background tasks.

        Returns:
            int: The number of pending tasks.
        """
        return len(self._tasks)

    def run(self, coroutine: Coroutine[Any, Any, T]) -> asyncio.Task[Optional[T]]:
        """
        Runs a coroutine in the background.

        This method wraps the given coroutine in an error handling wrapper which invokes the
        `on_task_exception` callback in case of an exception, or re-raises the exception if
        no callback is provided. The task is added to the list of running tasks.

        Args:
            coroutine (Coroutine[Any, Any, T]): The coroutine to be run in the background.

        Returns:
            asyncio.Task[Optional[T]]: The asyncio task created for the coroutine.
        """
        assert self._loop is not None, "event loop not set"

        async def error_wrapper(coroutine: Coroutine[Any, Any, T]) -> Optional[T]:
            try:
                return await coroutine
            except Exception as e:
                if self._on_task_exception is not None:
                    self._on_task_exception(e)
                else:
                    raise e

        task = self._loop.create_task(error_wrapper(coroutine))
        self._tasks.append(task)
        task.add_done_callback(self._on_task_complete)
        return task

    def _on_task_complete(self, task: asyncio.Task[Any]):
        """
        Callback method to remove a completed task from the list of running tasks.

        This method is invoked when a task completes (either by finishing its execution or by being cancelled).

        Args:
            task (asyncio.Task[Any]): The task that has completed.
        """
        self._tasks.remove(task)
