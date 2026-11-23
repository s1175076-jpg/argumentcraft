from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.auth import optional_user, require_teacher, require_user
from app.services.db import (
    create_assignment,
    list_assignments,
    list_sessions_for_teacher,
    list_sessions_for_user,
    save_session,
)

router = APIRouter(prefix="/api", tags=["classroom"])


class AssignmentRequest(BaseModel):
    title: str
    topic: str
    stance: str = ""
    description: str = ""
    active: bool = True


class SessionSaveRequest(BaseModel):
    assignment_id: int | None = None
    topic: str = ""
    stance: str = ""
    persona: str = "socratic"
    toulmin: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)


@router.get("/assignments/active")
def active_assignment(user: dict[str, Any] | None = Depends(optional_user)) -> dict[str, Any]:
    items = list_assignments(active_only=True)
    return {"assignment": items[0] if items else None}


@router.get("/assignments")
def all_assignments(teacher: dict[str, Any] = Depends(require_teacher)) -> dict[str, Any]:
    return {"assignments": list_assignments(active_only=False)}


@router.post("/assignments")
def publish_assignment(req: AssignmentRequest, teacher: dict[str, Any] = Depends(require_teacher)) -> dict[str, Any]:
    if not req.title.strip() or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Title and topic are required")
    return {"assignment": create_assignment(teacher["id"], req.title, req.topic, req.stance, req.description, req.active)}


@router.post("/sessions")
def store_session(req: SessionSaveRequest, user: dict[str, Any] = Depends(require_user)) -> dict[str, Any]:
    return {"session": save_session(user["id"], req.model_dump(), req.result)}


@router.get("/sessions/mine")
def my_sessions(user: dict[str, Any] = Depends(require_user)) -> dict[str, Any]:
    return {"sessions": list_sessions_for_user(user["id"])}


@router.get("/teacher/sessions")
def teacher_sessions(teacher: dict[str, Any] = Depends(require_teacher)) -> dict[str, Any]:
    return {"sessions": list_sessions_for_teacher()}
