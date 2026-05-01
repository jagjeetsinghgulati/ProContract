from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from config import get_settings


def create_session(st_module, username: str) -> None:
    timeout = get_settings().session_timeout_minutes
    st_module.session_state["auth_token"] = str(uuid4())
    st_module.session_state["auth_user"] = username
    st_module.session_state["auth_expires_at"] = datetime.utcnow() + timedelta(minutes=timeout)


def is_authenticated(st_module) -> bool:
    token = st_module.session_state.get("auth_token")
    expires_at = st_module.session_state.get("auth_expires_at")
    if not token or not expires_at:
        return False
    if datetime.utcnow() > expires_at:
        logout(st_module)
        return False
    return True


def require_authenticated_user(st_module) -> bool:
    if not is_authenticated(st_module):
        st_module.warning("Please log in from the main app page.")
        st_module.stop()
        return False
    return True


def logout(st_module) -> None:
    for key in ("auth_token", "auth_user", "auth_expires_at"):
        st_module.session_state.pop(key, None)
