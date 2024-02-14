from typing import Any, Dict

from fastapi import Request, WebSocket


def is_session_logged_in(session: Dict[str, Any]):
    return "uname" in session


def is_logged_in(request: Request | WebSocket):
    return is_session_logged_in(request.session)
