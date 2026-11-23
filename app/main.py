from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Load server-side defaults from .env (project root). Keep the API key out of the browser.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.routers.auth import router as auth_router
from app.routers.classroom import router as classroom_router
from app.routers.debate import router as debate_router
from app.services.db import init_db

app = FastAPI(title="ArgumentCraft", version="0.1.0")

@app.on_event("startup")
def _startup() -> None:
    init_db()

app.include_router(auth_router)
app.include_router(classroom_router)
app.include_router(debate_router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "home.html")


@app.get("/app")
def app_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
