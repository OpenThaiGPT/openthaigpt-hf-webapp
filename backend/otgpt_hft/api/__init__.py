from fastapi import APIRouter, Request

from ..global_res import g_data_bridge

router = APIRouter()


@router.get("/status", tags=["debug"])
async def status(request: Request):
    return {"uname": request.session.get("uname")}


# TODO switch back to mux when there are multiple components [1/2]
# ws_connect_mux = WebSocketMultiplexer(
#     {
#         "data-bridge": g_data_bridge,
#     }
# )
# router.add_websocket_route("/ws-connect", ws_connect_mux.handle_ws)

router.add_websocket_route("/ws-connect/data-bridge", g_data_bridge.handle_ws)
