from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUTES_PATH = ROOT / "data" / "statutes.json"
CASES_PATH = ROOT / "data" / "cases.json"


@lru_cache(maxsize=1)
def statutes() -> dict[str, dict]:
    rows = json.loads(STATUTES_PATH.read_text(encoding="utf-8"))
    return {row["id"]: row for row in rows}


@lru_cache(maxsize=1)
def cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def get(statute_id: str) -> dict:
    try:
        return statutes()[statute_id]
    except KeyError as exc:
        raise KeyError(f"Statute not in the bank: {statute_id}") from exc
