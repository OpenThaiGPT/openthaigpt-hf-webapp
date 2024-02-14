from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    Literal,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    cast,
    final,
)

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, TypeAdapter

from otgpt_hft.utils.logger import Logger

if TYPE_CHECKING:
    _LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    _LoggerAdapter = logging.LoggerAdapter

logger = logging.getLogger(__name__)

P = TypeVar("P", bound=Literal["F", "A"])
T = TypeVar("T", bound=str)


class PayloadBM(BaseModel, Generic[P, T]):
    """equivalent to client's IFPayload"""

    p: P
    type: T


class FPayloadBM(PayloadBM[Literal["F"], T]):
    """equivalent to client's IFPayload"""

    p: Literal["F"] = "F"
    id: str
    type: T


class APayloadBM(PayloadBM[Literal["A"], T]):
    """equivalent to client's IAPayload"""

    p: Literal["A"] = "A"
    type: T


class FFakePayloadBM(FPayloadBM[Literal["fake"]]):
    """placeholder payload type"""

    type: Literal["fake"] = "fake"


class AFakePayloadBM(APayloadBM[Literal["fake"]]):
    """placeholder payload type"""

    type: Literal["fake"] = "fake"


FQ = TypeVar("FQ", bound=FPayloadBM[Any])
FS = TypeVar("FS", bound=FPayloadBM[Any])
AQ = TypeVar("AQ", bound=APayloadBM[Any])
AS = TypeVar("AS", bound=APayloadBM[Any])


class AbsTypedWebSocket(ABC, Generic[FQ, FS, AQ, AS]):
    req_session: Dict[str, Any]

    def accept(self) -> Awaitable[None]: ...

    def send(self, msg: FS | AS) -> Awaitable[None]: ...

    def receive(self) -> Awaitable[FQ | AQ]: ...

    def close(
        self, code: int = 1000, reason: Optional[str] = None
    ) -> Awaitable[None]: ...


class TypedWebSocket(AbsTypedWebSocket[FQ, FS, AQ, AS]):
    def __init__(self, ws: WebSocket, ReqType: TypeAdapter[FQ | AQ]):
        self.ws = ws
        self.req_session = ws.session
        self.ReqType = ReqType

    async def accept(self) -> None:
        await self.ws.accept()

    async def send(self, msg: FS | AS) -> None:
        logger.info(
            {
                "msg": "ws-snd",
                "payload": msg,
            }
        )
        await self.ws.send_text(msg.model_dump_json(by_alias=True))

    async def receive(self) -> FQ | AQ:
        obj = await self.ws.receive_json()
        bm_obj = self.ReqType.validate_python(obj)
        logger.info(
            {
                "msg": "ws-rcv",
                "payload": bm_obj,
            }
        )
        return bm_obj

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        await self.ws.close(code, reason)


class PSession(Protocol):
    logger: _LoggerAdapter

    def on_close(self): ...

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> Optional[bool]:
        self.on_close()
        return False


SSN = TypeVar("SSN", bound=PSession)

WsHandler = Callable[[WebSocket], Awaitable[None]]


class SessionError(Exception):
    def __init__(self, code: int, reason: str):
        self.code = code
        self.reason = reason


class TypedWebSocketHandler(Generic[SSN, FQ, FS, AQ, AS], ABC):
    """Helper class for which provides a WebSocket connection handler `handle_ws`
    and exposes a Python typehint interface."""

    ReqType: TypeAdapter[FQ | AQ]

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    @abstractmethod
    async def create_session(self, t_ws: AbsTypedWebSocket[FQ, FS, AQ, AS]) -> SSN: ...

    @abstractmethod
    def handle_fetch_request(
        self, t_ws: AbsTypedWebSocket[FQ, FS, AQ, AS], session: SSN, request: FQ
    ) -> Awaitable[FS]:
        """return if the request is handled"""
        ...

    @abstractmethod
    async def handle_async_request(
        self, t_ws: AbsTypedWebSocket[FQ, FS, AQ, AS], session: SSN, request: AQ
    ) -> bool:
        """return if the request is handled"""
        ...

    @final
    async def handle_t_ws(self, t_ws: AbsTypedWebSocket[FQ, FS, AQ, AS]):
        # acknowledge connection
        # self.logger.info({"handler": type(self), "msg": "connection initializing"})
        await t_ws.accept()
        self.logger.debug({"handler": type(self), "msg": "connection accepted"})

        t_ws_closed = False
        try:
            session = await self.create_session(t_ws)
        except SessionError as e:
            await t_ws.close(e.code, e.reason)
            return

        try:
            while True:
                try:
                    # wait for a request from client
                    req = await t_ws.receive()
                except WebSocketDisconnect as e:
                    t_ws_closed = True
                    # client disconnected
                    if e.code == 1000:
                        session.logger.info(
                            {
                                "handler": type(self),
                                "msg": f"client disconnected: websocket.receive_text WebSocketDisconnect: {e}",
                                "code": e.code,
                                "reason": e.reason,
                            }
                        )
                    elif e.code == 1001:
                        session.logger.error(
                            {
                                "handler": type(self),
                                "msg": f"client disconnected: WebSocketDisconnect[{e.code}]: lost connection between server and client",
                                "code": e.code,
                                "reason": e.reason,
                            }
                        )
                    else:
                        session.logger.error(
                            {
                                "handler": type(self),
                                "msg": f"websocket.receive_text WebSocketDisconnect: {e}",
                                "code": e.code,
                                "reason": e.reason,
                            }
                        )
                    return

                if req.p == "F":
                    # TODO handle fetch and connection accept response in background
                    res = await self.handle_fetch_request(t_ws, session, cast(FQ, req))
                    await t_ws.send(res)
                else:
                    assert req.p == "A"
                    handled = await self.handle_async_request(
                        t_ws, session, cast(AQ, req)
                    )

                    if not handled:
                        # invalid request close connection
                        await t_ws.close(4000, "bad request")
                        session.logger.error(
                            f"websocket.receive_text Cannot handle message"
                        )
                        return
        finally:
            session.on_close()
            if not t_ws_closed:
                await t_ws.close(code=1011)

    async def handle_ws(self, ws: WebSocket):
        await self.handle_t_ws(TypedWebSocket(ws, self.ReqType))


def combine_fa_req(
    FetchReqType: Type[FQ], AsyncReqType: Type[AQ]
) -> TypeAdapter[FQ | AQ]:
    return TypeAdapter(
        Annotated[Union[FetchReqType, AsyncReqType], Field(discriminator="p")]
    )
