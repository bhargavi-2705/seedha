"""Seedha. One process, no login, no database. The interview can paste a new story."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from seedha.bank import cases
from seedha.pipeline import advise

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(title="Seedha")


class CaseIn(BaseModel):
    text: str = Field(default="", max_length=8000)
    language: str = "en"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/samples")
def samples() -> list[dict]:
    return [
        {"id": case["id"], "title": case["title"], "language": case.get("language") or "en", "text": case["text"]}
        for case in cases()
    ]


@app.post("/api/case")
def case(body: CaseIn) -> dict:
    language = body.language if body.language in {"en", "hi"} else "en"
    return advise(body.text, language)


app.mount("/static", StaticFiles(directory=STATIC), name="static")
