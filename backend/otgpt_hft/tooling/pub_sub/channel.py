import logging
from typing import Any, Callable, Generic, List, Optional, Type, TypeVar

from .base import ChannelName, Message, Subscriber, SubscriptionARes
from .pub_sub_ex import PChannel

logger = logging.getLogger(__name__)

SAR = TypeVar("SAR", bound=SubscriptionARes[Any])


class Channel(PChannel, Generic[SAR]):
    def __init__(
        self,
        ch: ChannelName,
        SARType: Type[SAR],
        on_empty: Optional[Callable[[PChannel], None]] = None,
    ) -> None:
        self._subs: List[Subscriber] = []
        self.ch = ch
        self._SARType = SARType
        self._cache = None
        self._on_empty = on_empty

    def _set_cache(self, msg: Message):
        self._cache = self._wrap_msg(msg)

    def get_initial_msg(self) -> Optional[SAR]:
        return self._cache

    async def sub(self, sub: Subscriber) -> None:
        self._subs.append(sub)
        if self._cache is not None:
            await sub(self._cache)

    def unsub(self, sub: Subscriber) -> bool:
        """Unsubscribe

        Args:
            sub (Subscriber): subscriber to remove

        Returns:
            bool: channel should be kept by PubSub
        """
        try:
            self._subs.remove(sub)
        except ValueError:
            logger.error("sub cannot be remove: sub does not exist")

        if self._on_empty is not None and len(self._subs) == 0:
            self._on_empty(self)
            return False

        return True

    def _wrap_msg(self, msg: Message) -> SAR:
        return self._SARType(channel=self.ch, data=msg)

    async def publish(self, msg: Message) -> None:
        self._cache = wmsg = self._wrap_msg(msg)
        for i in range(len(self._subs) - 1, -1, -1):
            sub = self._subs[i]
            try:
                await sub(wmsg)
            except RuntimeError as e:
                self._subs.pop(i)
                logger.error(
                    f"sub must not raise a RuntimeError, got {e}: there probably dangling with a close WebsocketConnection"
                )
            except Exception as e:
                self._subs.pop(i)
                logger.error(f"sub must not raise an exception: got exception: {e}")


# class BaseChannel(AbsChannel):
#     def __init__(self, channel: ChannelName) -> None:
#         self._subs: List[Subscriber] = []
#         self.channel = channel

#     def get_initial_msg(self) -> Optional[SubscriptionARes[Any]]:
#         return None

#     async def sub(self, sub: Subscriber) -> None:
#         self._subs.append(sub)

#     def unsub(self, sub: Subscriber) -> bool:
#         """Unsubscribe

#         Args:
#             sub (Subscriber): subscriber to remove

#         Returns:
#             bool: channel should be kept by PubSub
#         """
#         try:
#             self._subs.remove(sub)
#         except ValueError:
#             logger.error("sub cannot be remove: sub does not exist")
#         return True

#     def wrap_msg(self, msg: Message) -> SubscriptionARes[Any]:
#         return SubscriptionARes(channel=self.channel, data=msg)

#     async def publish(self, msg: Message) -> None:
#         wmsg = self.wrap_msg(msg)
#         for i in range(len(self._subs) - 1, -1, -1):
#             sub = self._subs[i]
#             try:
#                 await sub(wmsg)
#             except RuntimeError as e:
#                 self._subs.pop(i)
#                 logger.error(
#                     f"sub must not raise a RuntimeError, got {e}: there probably dangling with a close WebsocketConnection"
#                 )
#             except Exception as e:
#                 self._subs.pop(i)
#                 logger.error(f"sub must not raise an exception: got exception: {e}")


# class CachedChannel(BaseChannel):
#     def __init__(self, channel: ChannelName) -> None:
#         super().__init__(channel)
#         self.cache: Optional[SubscriptionARes[Any]] = None

#     def get_initial_msg(self) -> Optional[SubscriptionARes[Any]]:
#         return self.cache

#     async def sub(self, sub: Subscriber) -> None:
#         await super().sub(sub)
#         if self.cache is not None:
#             await sub(self.cache)

#     async def publish(self, msg: Message) -> None:
#         wmsg = self.cache = self.wrap_msg(msg)
#         for i in range(len(self._subs) - 1, -1, -1):
#             sub = self._subs[i]
#             try:
#                 await sub(wmsg)
#             except RuntimeError as e:
#                 self._subs.pop(i)
#                 logger.error(
#                     f"sub must not raise a RuntimeError, got {e}: there probably dangling with a close WebsocketConnection"
#                 )
#             except Exception as e:
#                 self._subs.pop(i)
#                 logger.error(f"sub must not raise an exception: got exception: {e}")


# HookCallback = Callable[[ChannelName], Message]


# class DiffChannel(BaseChannel):
#     def __init__(self, channel: ChannelName, init_msg_hook: HookCallback) -> None:
#         super().__init__(channel)
#         self.init_msg_hook = init_msg_hook

#     def get_initial_msg(self) -> Message:
#         init_msg = self.init_msg_hook(self.channel)
#         init_wmsg = self.wrap_msg(init_msg)
#         return init_wmsg

#     async def sub(self, sub: Subscriber) -> None:
#         await super().sub(sub)
#         await self.publish(self.get_initial_msg())


# Channel = Union[BaseChannel, CachedChannel, DiffChannel]
