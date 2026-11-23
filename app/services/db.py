from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              salt TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('student','teacher')),
              display_name TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tokens (
              token TEXT PRIMARY KEY,
              user_id INTEGER NOT NULL REFERENCES users(id),
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS assignments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              teacher_id INTEGER NOT NULL REFERENCES users(id),
              title TEXT NOT NULL,
              topic TEXT NOT NULL,
              stance TEXT NOT NULL DEFAULT '',
              description TEXT NOT NULL DEFAULT '',
              active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id),
              assignment_id INTEGER REFERENCES assignments(id),
              topic TEXT NOT NULL DEFAULT '',
              stance TEXT NOT NULL DEFAULT '',
              persona TEXT NOT NULL DEFAULT 'socratic',
              toulmin_json TEXT NOT NULL DEFAULT '{}',
              history_json TEXT NOT NULL DEFAULT '[]',
              result_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """
        )
        _seed_users(conn)


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return dk.hex(), salt


DEMO_ACCOUNTS = [
    ("teacher", "ArgueTch_6065", "teacher", "Teacher"),
    ("student", "ArgueStu_6065", "student", "Student"),
]


def _seed_users(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if not existing:
        for username, password, role, display_name in DEMO_ACCOUNTS:
            ph, salt = _hash_password(password)
            conn.execute(
                "INSERT INTO users(username,password_hash,salt,role,display_name,created_at) VALUES (?,?,?,?,?,?)",
                (username, ph, salt, role, display_name, utcnow()),
            )
        return
    # Keep demo accounts usable for local prototype; refresh their passwords.
    for username, password, role, display_name in DEMO_ACCOUNTS:
        row = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        ph, salt = _hash_password(password)
        if row:
            conn.execute("UPDATE users SET password_hash=?, salt=?, role=?, display_name=? WHERE id=?", (ph, salt, role, display_name, row["id"]))
        else:
            conn.execute(
                "INSERT INTO users(username,password_hash,salt,role,display_name,created_at) VALUES (?,?,?,?,?,?)",
                (username, ph, salt, role, display_name, utcnow()),
            )


def create_user(username: str, password: str, role: str, display_name: str | None = None) -> dict[str, Any]:
    ph, salt = _hash_password(password)
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO users(username,password_hash,salt,role,display_name,created_at) VALUES (?,?,?,?,?,?)",
            (username.strip(), ph, salt, role, (display_name or username).strip(), utcnow()),
        )
        row = conn.execute("SELECT id,username,role,display_name,created_at FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def register_student(username: str, password: str, display_name: str | None = None) -> dict[str, Any]:
    username = (username or "").strip()
    if not username or not password:
        raise ValueError("Username and password are required")
    if len(username) < 2 or len(username) > 32:
        raise ValueError("Username must be 2–32 characters")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    ph, salt = _hash_password(password)
    with connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users(username,password_hash,salt,role,display_name,created_at) VALUES (?,?,?,?,?,?)",
                (username, ph, salt, "student", (display_name or username).strip(), utcnow()),
            )
        except sqlite3.IntegrityError as e:
            raise ValueError("Username already exists") from e
        row = conn.execute("SELECT id,username,role,display_name FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        token = secrets.token_urlsafe(32)
        conn.execute("INSERT INTO tokens(token,user_id,created_at) VALUES (?,?,?)", (token, row["id"], utcnow()))
        return {"token": token, "user": dict(row)}


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
        if not row:
            return None
        ph, _ = _hash_password(password, row["salt"])
        if not secrets.compare_digest(ph, row["password_hash"]):
            return None
        token = secrets.token_urlsafe(32)
        conn.execute("INSERT INTO tokens(token,user_id,created_at) VALUES (?,?,?)", (token, row["id"], utcnow()))
        return {
            "token": token,
            "user": {"id": row["id"], "username": row["username"], "role": row["role"], "display_name": row["display_name"]},
        }


def get_user_by_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT u.id,u.username,u.role,u.display_name FROM tokens t JOIN users u ON u.id=t.user_id WHERE t.token=?",
            (token,),
        ).fetchone()
        return dict(row) if row else None


def logout(token: str | None) -> None:
    if not token:
        return
    with connect() as conn:
        conn.execute("DELETE FROM tokens WHERE token=?", (token,))


def create_assignment(teacher_id: int, title: str, topic: str, stance: str = "", description: str = "", active: bool = True) -> dict[str, Any]:
    with connect() as conn:
        if active:
            conn.execute("UPDATE assignments SET active=0 WHERE active=1")
        cur = conn.execute(
            "INSERT INTO assignments(teacher_id,title,topic,stance,description,active,created_at) VALUES (?,?,?,?,?,?,?)",
            (teacher_id, title.strip(), topic.strip(), stance.strip(), description.strip(), 1 if active else 0, utcnow()),
        )
        row = conn.execute("SELECT * FROM assignments WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def list_assignments(active_only: bool = False) -> list[dict[str, Any]]:
    q = "SELECT a.*,u.display_name AS teacher_name FROM assignments a JOIN users u ON u.id=a.teacher_id"
    params: list[Any] = []
    if active_only:
        q += " WHERE a.active=1"
    q += " ORDER BY a.created_at DESC"
    with connect() as conn:
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]


def save_session(user_id: int, payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO sessions(user_id,assignment_id,topic,stance,persona,toulmin_json,history_json,result_json,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                payload.get("assignment_id"),
                (payload.get("topic") or "").strip(),
                (payload.get("stance") or "").strip(),
                (payload.get("persona") or "socratic").strip(),
                json.dumps(payload.get("toulmin") or {}, ensure_ascii=False),
                json.dumps(payload.get("history") or [], ensure_ascii=False),
                json.dumps(result or {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM sessions WHERE id=?", (cur.lastrowid,)).fetchone()
        return _session_to_dict(row)


def _session_to_dict(row: sqlite3.Row | None) -> dict[str, Any]:
    if not row:
        return {}
    d = dict(row)
    for k in ("toulmin_json", "history_json", "result_json"):
        try:
            d[k.replace("_json", "")] = json.loads(d.pop(k) or ("[]" if "history" in k else "{}"))
        except Exception:
            d[k.replace("_json", "")] = [] if "history" in k else {}
    return d


def list_sessions_for_user(user_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM sessions WHERE user_id=? ORDER BY updated_at DESC LIMIT 100", (user_id,)).fetchall()
        return [_session_to_dict(r) for r in rows]


def list_sessions_for_teacher() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT s.*,u.username,u.display_name,a.title AS assignment_title
               FROM sessions s JOIN users u ON u.id=s.user_id
               LEFT JOIN assignments a ON a.id=s.assignment_id
               ORDER BY s.updated_at DESC LIMIT 200"""
        ).fetchall()
        out = []
        for r in rows:
            d = _session_to_dict(r)
            d["username"] = r["username"]
            d["display_name"] = r["display_name"]
            d["assignment_title"] = r["assignment_title"]
            out.append(d)
        return out
