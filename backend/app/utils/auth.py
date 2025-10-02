from __future__ import annotations

import base64
import os
from functools import wraps
from typing import Callable, TypeVar

import bcrypt
from flask import Response, current_app, request

F = TypeVar("F", bound=Callable)


def _get_password_hash() -> bytes | None:
    raw = os.getenv("APP_SHARED_PASSWORD_HASH")
    if not raw:
        return None
    return raw.encode("utf-8")


def _unauthorized_response() -> Response:
    realm = current_app.config.get("BASIC_AUTH_REALM", "Restricted")
    response = Response("Unauthorized", 401)
    response.headers["WWW-Authenticate"] = f'Basic realm="{realm}", charset="UTF-8"'
    return response


def require_basic_auth(func: F) -> F:
    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[override]
        expected_hash = _get_password_hash()
        if expected_hash is None:
            # If no hash is configured we allow access but log.
            current_app.logger.warning("APP_SHARED_PASSWORD_HASH not set; skipping auth gate")
            return func(*args, **kwargs)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return _unauthorized_response()
        try:
            encoded = auth_header.split(" ", 1)[1]
            decoded = base64.b64decode(encoded).decode("utf-8")
        except Exception:
            return _unauthorized_response()

        if ":" not in decoded:
            return _unauthorized_response()
        username, password = decoded.split(":", 1)
        # Username is unused for now but logged for future auditing
        if not password:
            return _unauthorized_response()
        password_ok = bcrypt.checkpw(password.encode("utf-8"), expected_hash)
        if not password_ok:
            return _unauthorized_response()
        request.environ["checklist.user"] = username or "anonymous"
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
