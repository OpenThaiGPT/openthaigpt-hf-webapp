import logging
from typing import Any, Callable, Dict, Literal, Optional, Protocol, Tuple

from .base import (
    ChannelName,
    Prefix,
    PubSub,
    Subscriber,
    SubscriptionARes,
    UnregisteredChannel,
)

logger = logging.getLogger(__name__)

ChannelType = Literal["base", "cached", "diff"]


class PChannel(Protocol):
    ch: ChannelName

    def get_initial_msg(self) -> Optional[SubscriptionARes[Any]]:
        ...

    async def sub(self, sub: Subscriber) -> None:
        ...

    def unsub(self, sub: Subscriber) -> bool:
        ...


Hook = Callable[[ChannelName], PChannel]


class ExtensiblePubSub(PubSub):
    def __init__(self):
        self.ch_s: Dict[ChannelName, PChannel] = {}
        self.ch_hook_s: Dict[Prefix, Hook] = {}

    def register_channel(self, ch_name: ChannelName, channel: PChannel) -> None:
        if ch_name in self.ch_s:
            raise ValueError(
                f"cannot register channel: channel '{ch_name}' already exist"
            )

        self.ch_s[ch_name] = channel

    def register_hook(
        self,
        prefix: Tuple[str, ...],
        hook: Hook,
        # call_back: Callable[[Tuple[str | int, ...]], Message],
    ) -> None:
        if prefix in self.ch_hook_s:
            raise ValueError(
                f"cannot register hook: hook with '{prefix}' as prefix already exist"
            )
        self.ch_hook_s[prefix] = hook

    # def get_initial_msg(self, ch: ChannelName) -> Optional[Message]:
    #     return self.ch_s[ch].get_initial_msg()

    async def subscribe(self, ch: ChannelName, sub: Subscriber) -> None:
        if ch in self.ch_s:
            # subscribe to existing channels
            await self.ch_s[ch].sub(sub)
        else:
            # find hooks that can provide data to the requested channel
            hook = self._find_hook(ch)
            if hook is not None:
                # create channel with hook
                channel = hook(ch)
                self.register_channel(ch, channel)
                # subscribe to new channel
                await channel.sub(sub)
                return

            raise UnregisteredChannel(
                "invalid channel",
                f"cannot subscribe to an unregistered channel",
            )

    def unsubscribe(self, ch: ChannelName, sub: Subscriber) -> None:
        if ch not in self.ch_s:
            raise UnregisteredChannel(
                "invalid channel",
                f"cannot unsubscribe to an unregistered channel",
            )

        keep_ch = self.ch_s[ch].unsub(sub)
        if not keep_ch:
            del self.ch_s[ch]

    def _find_hook(self, ch: ChannelName) -> Hook | None:
        for i in range(len(ch), -1, -1):
            prefix = ch[:i]
            if prefix in self.ch_hook_s:
                return self.ch_hook_s[prefix]

        return None
