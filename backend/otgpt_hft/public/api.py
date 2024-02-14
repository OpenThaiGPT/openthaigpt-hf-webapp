import starlette.status
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, SecretStr

from otgpt_hft.routes import PAGE_EDITOR_ROUTE, PAGE_LOGIN

from ..global_res import g_database

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/status", tags=["debug"])
async def status(request: Request):
    return {"uname": request.session.get("uname")}


@router.post("/login", tags=["auth"])
async def login(request: Request, username: str = Form(), password: SecretStr = Form()):
    uname = await g_database.check_user(username, password)
    if uname is None:
        return "fail"
    else:
        request.session["uname"] = uname
        return RedirectResponse(
            PAGE_EDITOR_ROUTE, status_code=starlette.status.HTTP_302_FOUND
        )


@router.api_route("/logout", methods=["GET", "POST"], tags=["auth"])
async def logout(request: Request):
    if "uname" not in request.session:
        return "already logged out"
    del request.session["uname"]
    return "logged out"


@router.post("/register", tags=["auth"])
async def register(
    request: Request,
    username: str = Form(),
    password: SecretStr = Form(),
    confirm_password: SecretStr = Form(),
):
    if password.get_secret_value() != confirm_password.get_secret_value():
        return "password and confirm password mismatch"
    uname = username.lower()
    found = await g_database.find_user_name(username)
    if found:
        return f"user already exist with username '{uname}'."

    await g_database.register_user(username, password)
    return RedirectResponse(PAGE_LOGIN, status_code=starlette.status.HTTP_302_FOUND)
