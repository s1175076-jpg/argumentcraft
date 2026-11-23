from __future__ import annotations

import json
import re
from typing import Any

TOULMIN_FIELDS = [
    "claim",
    "grounds",
    "warrant",
    "backing",
    "qualifier",
    "rebuttal",
]


def _extract_json(text: string) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


PERSONA_PROMPTS = {
    "socratic": "Persona: Friendly questioner. Ask simple questions that help the learner spot gaps in their idea.",
    "gentle": "Persona: Kind coach. Cheer the learner on and gently show the next small step.",
    "rigorous": "Persona: Careful checker. Ask for proof and clear reasons. Be polite and exact.",
    "challenger": "Persona: Friendly challenger. Ask about the other side and weak spots. Never be rude.",
    "debate": "Persona: Debate buddy. Take the other side and ask the learner to defend their idea.",
}


def system_prompt(persona: str = "socratic") -> str:
    persona_text = PERSONA_PROMPTS.get((persona or "socratic").strip().lower(), PERSONA_PROMPTS["socratic"])
    return (
        "You are ArgumentCraft, a friendly AI debate buddy for young learners "
        "(about 9-12 years old). Your goal is NOT to win or to lecture. You help "
        "the learner make their argument stronger using the Toulmin model "
        "(Claim, Grounds, Warrant, Backing, Qualifier, Rebuttal).\n\n"
        f"{persona_text}\n\n"
        "How to talk:\n"
        "- Use simple, everyday words a child knows.\n"
        "- Use short sentences (about 5-10 words each).\n"
        "- Give a tiny example when it helps.\n"
        "- Be warm and encouraging. Never be rude.\n\n"
        "Rules:\n"
        "1. Ask 1-2 short questions per turn. Each question must be under 15 words.\n"
        "2. Ask about ONE weak spot: the proof, the reason, when it is true, or the other side.\n"
        "3. Pick the Toulmin element that is weakest right now.\n"
        "4. Do not repeat a question you already asked.\n"
        "5. Return ONLY valid JSON with this schema:\n"
        "{\n"
        '  "socratic_questions": ["..."],\n'
        '  "challenge_summary": "very short summary of the problem",\n'
        '  "target_element": "claim|grounds|warrant|backing|qualifier|rebuttal|overall",\n'
        '  "conflict_level": 1,\n'
        '  "suggested_revision": "one short tip to fix it",\n'
        '  "toulmin_feedback": {\n'
        '    "claim": "...", "grounds": "...", "warrant": "...", "backing": "...",\n'
        '    "qualifier": "...", "rebuttal": "..."\n'
        "  }\n"
        "}\n"
        "Keep every text field short. challenge_summary and suggested_revision: under 12 words. "
        "toulmin_feedback values: under 8 words each. conflict_level is a number 1-5."
    )


def build_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    topic = (payload.get("topic") or "").strip()
    stance = (payload.get("stance") or "").strip()
    toulmin = payload.get("toulmin") or {}
    history = payload.get("history") or []
    learner_message = (payload.get("learner_message") or "").strip()
    persona = (payload.get("persona") or "socratic").strip()
    toulmin_lines = []
    for key in TOULMIN_FIELDS:
        value = str(toulmin.get(key) or "").strip() or "(not provided)"
        toulmin_lines.append(f"- {key.title()}: {value}")

    context = (
        f"Debate topic: {topic or '(not provided)'}\n"
        f"Learner stance: {stance or '(not provided)'}\n"
        "Current Toulmin argument map:\n" + "\n".join(toulmin_lines)
    )

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt(persona)}]
    messages.append({"role": "user", "content": context})

    for item in history:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    if learner_message:
        messages.append({"role": "user", "content": learner_message})
    else:
        messages.append(
            {
                "role": "user",
                "content": (
                    "Start the first round. Look at my argument map and ask 1-2 short, "
                    "easy questions."
                ),
            }
        )

    return messages


def normalize_result(raw: str) -> dict[str, Any]:
    parsed = _extract_json(raw)
    if not parsed:
        return {
            "socratic_questions": [raw[:1200] or "What is your main idea?"],
            "challenge_summary": "Here is the AI's reply.",
            "target_element": "overall",
            "conflict_level": 2,
            "suggested_revision": "Add proof or explain why it fits.",
            "toulmin_feedback": {k: "" for k in TOULMIN_FIELDS},
            "raw": raw,
        }

    questions = parsed.get("socratic_questions")
    if isinstance(questions, str):
        questions = [questions]
    if not isinstance(questions, list):
        questions = [str(parsed.get("question") or "What is your proof?")]

    feedback = parsed.get("toulmin_feedback") or {}
    if not isinstance(feedback, dict):
        feedback = {}

    level = parsed.get("conflict_level", 2)
    try:
        level = max(1, min(5, int(level)))
    except (TypeError, ValueError):
        level = 2

    target = str(parsed.get("target_element") or "overall").lower()
    if target not in TOULMIN_FIELDS + ["overall"]:
        target = "overall"

    return {
        "socratic_questions": [str(q).strip() for q in questions if str(q).strip()][:3]
        or ["What links your proof to your idea?"],
        "challenge_summary": str(parsed.get("challenge_summary") or "").strip()
        or "A question was asked.",
        "target_element": target,
        "conflict_level": level,
        "suggested_revision": str(parsed.get("suggested_revision") or "").strip(),
        "toulmin_feedback": {k: str(feedback.get(k) or "").strip() for k in TOULMIN_FIELDS},
    }
