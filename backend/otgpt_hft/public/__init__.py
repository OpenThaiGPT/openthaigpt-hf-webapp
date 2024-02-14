from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from . import api

subapp = FastAPI()

subapp.mount("/page", StaticFiles(directory="public", html=True), name="public")


subapp.include_router(
    api.router,
    prefix="/api",
    tags=["api"],
)
