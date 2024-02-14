import logging
from abc import ABC, abstractmethod
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from otgpt_hft.tooling.ws.connection import APayloadBM

from ..client_exc import ClientException

logger = logging.getLogger(__name__)

ChannelName = Prefix = Union[
    Tuple[str | int, ...],
    Tuple[str, ...],
    Tuple[str],
]


CH = TypeVar("CH", bound=ChannelName)


class SubscriptionAReq(APayloadBM[Literal["sub", "unsub"]], Generic[CH]):
    type: Literal["sub", "unsub"]
    channel: CH


class SubscriptionARes(APayloadBM[Literal["sub"]], Generic[CH]):
    type: Literal["sub"] = "sub"
    channel: CH
    data: Any


HookChannel = Tuple[Tuple[str, ...], Tuple[str, ...]]
Message = Any
Subscriber = Callable[[SubscriptionARes[Any]], Awaitable[None]]


class UnregisteredChannel(ClientException):
    pass


class PubSub(ABC):
    # TODO remove unused method
    # def get_initial_msg(self, ch: ChannelName) -> Optional[Message]:
    #     """Return initial message that should be sent to a subscriber

    #     Args:
    #         ch (Channel): channel

    #     Returns:
    #         Optional[Message]: message (if any)
    #     """
    #     ...

    @abstractmethod
    async def subscribe(self, ch: ChannelName, sub: Subscriber) -> None:
        """Add subscriber to channel

        Once subscribe, future message to the channel will be pass to the Subscriber.

        Args:
            ch (Channel): channel
            sub (Subscriber): subscriber
        """
        ...

    @abstractmethod
    def unsubscribe(self, ch: ChannelName, sub: Subscriber) -> None:
        """Remove subscriber to channel

        Args:
            ch (Channel): channel
            sub (Subscriber): subscriber
        """
        ...
