import asyncio
import logging
from contextlib import asynccontextmanager
import os
from pathlib import Path

import uvicorn
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from otgpt_hft.auth import is_logged_in
from otgpt_hft.routes import (
    PAGE_DIR,
    PAGE_EDITOR_PATH,
    PAGE_EDITOR_ROUTE,
    PAGE_LOGIN,
    ROUTE_PREFIX,
)

from . import api, public
from .global_res import DATA_STORE_PATH, g_data_bridge, g_database

logger = logging.getLogger(__name__)
uvicorn.Config


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("lifespan startup")
    # connect to database
    await g_database.connect()
    await g_database.setup_db_if_not_already()
    logger.debug("connected to database")

    await g_data_bridge.load_data(DATA_STORE_PATH)
    logger.debug("loaded data to data_bridge")

    # TODO switch back to mux when there are multiple components [2/2]
    running_loop = asyncio.get_running_loop()
    # api.ws_connect_mux.set_loop(asyncio.get_running_loop())
    g_data_bridge.set_loop(running_loop)

    yield
    # close database connection
    await g_database.close()
    logger.debug("database connection closed")


app = FastAPI(lifespan=lifespan)

# Add SessionMiddleware to your application
app.add_middleware(SessionMiddleware, secret_key=os.environ["SESSION_KEY"])


app.include_router(
    public.api.router,
    prefix=ROUTE_PREFIX + "/public/api",
)

app.mount(
    ROUTE_PREFIX + "/public",
    StaticFiles(directory="public", html=True),
    name="public",
)

@app.get("/")
async def root(request: Request):
    return RedirectResponse(ROUTE_PREFIX)

@app.get(ROUTE_PREFIX + "/")
async def route_root(request: Request):
    if is_logged_in(request):
        return RedirectResponse(PAGE_EDITOR_ROUTE)
    return RedirectResponse(PAGE_LOGIN)


def logged_in(request: Request):
    if not is_logged_in(request):
        accept_header = request.headers.get("Accept", "")
        if "text/html" in accept_header:
            # The client expects HTML
            raise HTTPException(
                status_code=302,
                detail="Redirecting to login",
                headers={"Location": PAGE_LOGIN},
            )
        else:
            # Handle other types of responses (e.g., JSON)
            # return {"message": "This is a JSON response."}
            raise HTTPException(status_code=401, detail="not logged in")


core_router = APIRouter(dependencies=[Depends(logged_in)])

core_router.include_router(
    api.router,
    prefix="/api",
    tags=["api"],
)

@core_router.get("/page/{path_name:path}")
async def custom_static(path_name: str):
    file_path = Path(PAGE_DIR) / path_name
    if not file_path.exists() or not file_path.is_file():
        return FileResponse(PAGE_EDITOR_PATH)
        # raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


app.include_router(
    core_router,
    prefix=ROUTE_PREFIX,
)
