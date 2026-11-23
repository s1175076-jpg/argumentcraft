from __future__ import annotations

from typing import Any

from fastapi import Header, HTTPException

from app.services.db import get_user_by_token


def get_bearer_token(authorization: str | None = Header(default=None)) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def require_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = get_user_by_token(get_bearer_token(authorization))
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return user


def optional_user(authorization: str | None = Header(default=None)) -> dict[str, Any] | None:
    return get_user_by_token(get_bearer_token(authorization))


def require_teacher(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_user(authorization)
    if user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Teacher role required")
    return user
