from __future__ import annotations

import asyncio
import logging
from asyncio import Future
from typing import (
    Annotated,
    Any,
    Awaitable,
    Dict,
    List,
    Literal,
    Optional,
    TypeVar,
    Union,
)
from uuid import uuid4

from fastapi import WebSocketDisconnect
from pydantic import Field, TypeAdapter

from otgpt_hft.tooling.client_exc import ClientException
from otgpt_hft.tooling.ws.connection import AbsTypedWebSocket
from otgpt_hft.utils.min_bg_task import MinBGTasks

from .connection import (
    AQ,
    AS,
    FQ,
    FS,
    AbsTypedWebSocket,
    APayloadBM,
    FPayloadBM,
    PayloadBM,
    PSession,
    TypedWebSocketHandler,
    combine_fa_req,
)

logger = logging.getLogger(__name__)

P = TypeVar("P", bound=PayloadBM[Any, Any])


class ClientOpenConnection(FPayloadBM[Literal["open"]]):
    channel: str
    type: Literal["open"] = "open"


class ServerAcceptOpenConnection(FPayloadBM[Literal["open"]]):
    channel: str
    type: Literal["open"] = "open"
    session: str


class CloseConnection(APayloadBM[Literal["close"]]):
    session: str
    type: Literal["close"] = "close"
    code: int


class MultiplexedMsg(APayloadBM[Literal["msg"]]):
    session: str
    type: Literal["msg"] = "msg"
    msg: Any


# class MultiplexedMsg(APayloadBM[Literal["msg"]], Generic[P]):
#     session: str
#     type: Literal["msg"] = "msg"
#     msg: P


FetchRequest = ClientOpenConnection
FetchResponse = ServerAcceptOpenConnection
# FetchRequest = ClientOpenConnection | CloseConnection
# FetchResponse = ServerAcceptOpenConnection | CloseConnection
# FetchRequest = FPayloadBM[Any]
# FetchResponse = FPayloadBM[Any]

REQ = TypeVar("REQ", bound=PayloadBM[Any, Any])
RES = TypeVar("RES", bound=PayloadBM[Any, Any])

AsyncRequest = Annotated[
    Union[
        # ClientOpenConnection,
        CloseConnection,
        MultiplexedMsg,
        # MultiplexedMsg[Any],
    ],
    Field(discriminator="type"),
]
AsyncResponse = Annotated[
    Union[
        # ServerAcceptOpenConnection,
        CloseConnection,
        MultiplexedMsg,
        # MultiplexedMsg[Any],
    ],
    Field(discriminator="type"),
]


class VirtualTypedWebSocket(AbsTypedWebSocket[FQ, FS, AQ, AS]):
    def __init__(
        self,
        t_ws: AbsTypedWebSocket[
            FetchRequest,
            FetchResponse,
            AsyncRequest,
            AsyncResponse,
        ],
        ReqType: TypeAdapter[FQ | AQ],
        acceept_fetch_id: str,
        channel: str,
        logger: logging.LoggerAdapter[logging.Logger],
    ) -> None:
        self.t_ws = t_ws
        self.req_session = t_ws.req_session
        self.channel = channel
        self.session_id = str(uuid4())
        self.logger = logging.LoggerAdapter(
            logger, {"virtual_session": self.session_id}
        )
        self.closed = False
        self.ReqType = ReqType
        self.msg_queue: List[FQ | AQ] = []
        self.pending_receive: Optional[Future[FQ | AQ]] = None
        self.pending_acceept: Future[ServerAcceptOpenConnection] = Future()
        self.acceept_fetch_id = acceept_fetch_id

    def queue_msg(self, r_msg: Any):
        """Used by creator for supplying the messages"""
        msg = self.ReqType.validate_python(r_msg)
        if self.pending_receive is None:
            self.msg_queue.append(msg)
        else:
            future = self.pending_receive
            self.pending_receive = None
            future.set_result(msg)

    async def accept(self) -> None:
        assert self.acceept_fetch_id is not None
        self.pending_acceept.set_result(
            ServerAcceptOpenConnection(
                id=self.acceept_fetch_id,
                channel=self.channel,
                session=self.session_id,
            )
        )

    async def send(self, msg: FS | AS) -> None:
        await self.t_ws.send(MultiplexedMsg(session=self.session_id, msg=msg))

    def receive(self) -> Awaitable[FQ | AQ]:
        if len(self.msg_queue) > 0:
            msg = self.msg_queue[0]
            self.msg_queue = self.msg_queue[1:]
            future: Future[FQ | AQ] = Future()
            future.set_result(msg)
            return future
        else:
            assert (
                self.pending_receive is None
            ), "cannot call receive_msg while future is pending"
            self.pending_receive = Future()
            return self.pending_receive

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        self.closed = True
        self.logger.error(
            f"virutal socket closed, {self.session_id} {code} {reason}",
        )
        self.cleanup()
        # self.pending_receive.set_exception
        await self.t_ws.send(CloseConnection(session=self.session_id, code=code))

    def cleanup(self, code: int = 1000, reason: Optional[str] = None):
        if self.pending_receive is not None:
            self.pending_receive.set_exception(
                WebSocketDisconnect(
                    code=code,
                    reason=reason,
                )
            )


class Session(PSession):
    def __init__(
        self,
        session_name: str,
    ):
        self.logger = logging.LoggerAdapter(logger, {"session": session_name})

        self.v_sockets: List[VirtualTypedWebSocket[Any, Any, Any, Any]] = []

    def on_close(self):
        for v_socket in self.v_sockets:
            v_socket.cleanup(
                1001, "VirtualTypedWebSocket closed due to parent Session being closed"
            )


class WebSocketMultiplexer(
    TypedWebSocketHandler[
        Session,
        FetchRequest,
        FetchResponse,
        AsyncRequest,
        AsyncResponse,
        # AsyncRequest[FQ | AQ],
        # AsyncResponse[FS | AS],
    ],
    # Generic[FQ, FS, AQ, AS],
):
    ReqType = combine_fa_req(FetchRequest, AsyncRequest)

    def __init__(
        self, routers: Dict[str, TypedWebSocketHandler[Any, Any, Any, Any, Any]]
    ):
        super().__init__(logging.LoggerAdapter(logger, {"handler": "mux"}))
        # mapping from request channels to routers
        self.routers = routers
        # mapping from session ids to virtual sockets
        self.sockets: Dict[str, VirtualTypedWebSocket[Any, Any, Any, Any]] = {}
        self.bg_tasks = MinBGTasks()

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.bg_tasks.set_loop(loop)

    async def create_session(
        self,
        t_ws: AbsTypedWebSocket[
            FetchRequest, FetchResponse, AsyncRequest, AsyncResponse
        ],
    ) -> Session:
        return Session(str(uuid4()))

    async def handle_fetch_request(
        self,
        t_ws: AbsTypedWebSocket[
            FetchRequest,
            FetchResponse,
            AsyncRequest,
            AsyncResponse,
        ],
        session: Session,
        request: FetchRequest,
    ) -> FetchResponse:
        assert isinstance(request, ClientOpenConnection)
        if request.channel not in self.routers:
            logger.error(f"invalid channel: {request.channel}")
            raise ClientException(
                "invalid channel", f"'{request.channel}' does not exist"
            )
            # return False

        # pass virtual socket to handler
        handler = self.routers[request.channel]

        # create virtual socket for open request
        v_socket = VirtualTypedWebSocket[Any, Any, Any, Any](
            t_ws=t_ws,
            ReqType=handler.ReqType,
            acceept_fetch_id=request.id,
            channel=request.channel,
            logger=session.logger,
        )
        session.v_sockets.append(v_socket)

        # keep track of virtual socket
        self.sockets[v_socket.session_id] = v_socket

        self.bg_tasks.run(handler.handle_t_ws(v_socket))

        return await v_socket.pending_acceept

    async def handle_async_request(
        self,
        t_ws: AbsTypedWebSocket[
            FetchRequest,
            FetchResponse,
            AsyncRequest,
            AsyncResponse,
        ],
        session: Session,
        request: AsyncRequest,
    ) -> bool:
        if request.session not in self.sockets:
            logger.error(f"invalid session: {request.session}")
            return False
        v_socket = self.sockets[request.session]

        if isinstance(request, MultiplexedMsg):
            v_socket.queue_msg(request.msg)

        else:
            assert isinstance(request, CloseConnection)
            if not v_socket.closed:
                # if virtual socket is not already closed, therefor the close is intiated by the client
                v_socket.closed = True
                # send confirmation of closing the socket
                await v_socket.send(
                    CloseConnection(session=request.session, code=request.code)
                )
            # delete socket from session
            del self.sockets[request.session]

        return True
