from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.debate import build_messages, normalize_result
from app.services.llm import build_client, chat_jsonable

router = APIRouter(prefix="/api", tags=["debate"])


class DebateRequest(BaseModel):
    topic: str = ""
    stance: str = ""
    toulmin: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    learner_message: str = ""
    persona: str = "socratic"
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


@router.post("/debate")
def debate(req: DebateRequest) -> dict[str, Any]:
    model = (req.model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    try:
        client = build_client(api_key=req.api_key, base_url=req.base_url)
        messages = build_messages(req.model_dump())
        raw = chat_jsonable(client=client, model=model, messages=messages)
        result = normalize_result(raw)
        result["model"] = model
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - return useful error to local UI
        raise HTTPException(status_code=500, detail=f"Debate request failed: {exc}") from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
