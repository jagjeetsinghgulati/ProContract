from __future__ import annotations

import sqlite3

from auth.hashing import verify_password
from config import get_settings
from data_model.persistence import authenticate_user, create_user, get_user_by_username
from data_model.schema import UserModel


def seed_admin_if_missing() -> UserModel | None:
    settings = get_settings()
    existing = get_user_by_username(settings.seed_admin_username)
    try:
        if existing and verify_password(settings.seed_admin_password, existing.password_hash):
            return existing
        # Create if missing, or rotate hash to configured seed password if verification fails.
        return create_user(settings.seed_admin_username, settings.seed_admin_password)
    except sqlite3.IntegrityError:
        return get_user_by_username(settings.seed_admin_username)


def register_user(username: str, password: str) -> UserModel:
    return create_user(username, password)


def login_user(username: str, password: str) -> UserModel | None:
    return authenticate_user(username, password)
