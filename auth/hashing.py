from __future__ import annotations

import base64
import hashlib
import hmac
import os
from base64 import b64encode

try:
    from passlib.context import CryptContext
except ModuleNotFoundError:  # pragma: no cover
    CryptContext = None


_ITERATIONS = 210_000

if CryptContext is not None:
    _pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
else:
    _pwd_context = None


def _hash_stdlib(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return (
        "pbkdf2_sha256$"
        f"{_ITERATIONS}$"
        f"{b64encode(salt).decode('ascii')}$"
        f"{b64encode(digest).decode('ascii')}"
    )


def _verify_stdlib(password: str, password_hash: str) -> bool:
    try:
        algo, rounds, salt_b64, digest_b64 = password_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        salt = b64decode_compat(salt_b64)
        digest = b64decode_compat(digest_b64)
        expected = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(rounds),
        )
        return hmac.compare_digest(digest, expected)
    except Exception:
        return False


def b64decode_compat(value: str) -> bytes:
    # Normalize padding for base64 decoder.
    padded = value + "=" * ((4 - (len(value) % 4)) % 4)
    return base64.b64decode(padded.encode("ascii"))


def hash_password(password: str) -> str:
    if _pwd_context is not None:
        return _pwd_context.hash(password)
    return _hash_stdlib(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("pbkdf2_sha256$"):
        return _verify_stdlib(password, password_hash)
    if _pwd_context is not None:
        try:
            return _pwd_context.verify(password, password_hash)
        except Exception:
            return False
    return False
