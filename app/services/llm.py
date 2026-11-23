from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


def build_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAI:
    key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise ValueError(
            "Missing API key. Set OPENAI_API_KEY or provide it in the app settings."
        )
    url = (base_url or os.getenv("OPENAI_BASE_URL") or "").strip() or None
    return OpenAI(api_key=key, base_url=url)


def chat_jsonable(
    *,
    client: OpenAI,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.7,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    content = response.choices[0].message.content or ""
    return content.strip()
