from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header
from fastapi import HTTPException
from pydantic import BaseModel

from app.services.auth import get_bearer_token, optional_user
from app.services.db import authenticate, logout, register_student

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None


@router.post("/login")
def login(req: LoginRequest) -> dict[str, Any]:
    result = authenticate(req.username, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return result


@router.post("/register")
def register(req: RegisterRequest) -> dict[str, Any]:
    try:
        return register_student(req.username, req.password, req.display_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/logout")
def do_logout(authorization: str | None = Header(default=None)) -> dict[str, bool]:
    logout(get_bearer_token(authorization))
    return {"ok": True}


@router.get("/me")
def me(user: dict[str, Any] | None = Depends(optional_user)) -> dict[str, Any]:
    return {"user": user}
