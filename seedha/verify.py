"""Reject model prose that cites a section this case did not retrieve.

Code-written explanations may name a law in order to refuse it. Anything a model
writes, and every notice, has to pass this check.
"""

from __future__ import annotations

import re

BANNED_PHRASES = (
    "courts always",
    "definitely win",
    "you will win",
    "guaranteed",
    "bound to win",
    "double the deposit",
)

SECTION_RE = re.compile(r"(?:\b(?:section|sec\.?|article|rule)\s+|धारा\s+)(\d+)", re.I)
CODE_RE = re.compile(r"\b(IPC|BNS|CrPC|BNSS|FIR)\b")


def allowed_numbers(rows: list[dict]) -> set[str]:
    numbers: set[str] = set()
    for row in rows:
        numbers.update(str(n) for n in row.get("section_numbers", []))
    return numbers


def verify_model_text(text: str, rows: list[dict]) -> list[str]:
    """Return human-readable problems. An empty list means the text may be shown."""
    if not text:
        return []
    problems: list[str] = []
    lowered = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            problems.append(f'unsupported claim: "{phrase}"')
    allowed = allowed_numbers(rows)
    for match in SECTION_RE.finditer(text):
        number = match.group(1)
        if number not in allowed:
            problems.append(f"{match.group(0)} was not retrieved for this case")
    for match in CODE_RE.finditer(text):
        problems.append(f"{match.group(1)} is not in the statute bank")
    acts = " ".join(row.get("act", "") for row in rows).lower()
    if "model tenancy" in lowered and "model tenancy" not in acts:
        problems.append("Model Tenancy Act was not retrieved, and it is not in force as such")
    # A bare "section 420" style criminal number written as digits with IPC already caught.
    # Also catch "s.420" and "s.138".
    for match in re.finditer(r"\bs\.?\s*(\d{3})\b", text, re.I):
        if match.group(1) not in allowed:
            problems.append(f"s.{match.group(1)} was not retrieved")
    return problems


def assert_clean(text: str, rows: list[dict]) -> None:
    problems = verify_model_text(text, rows)
    if problems:
        joined = "; ".join(problems)
        raise ValueError(f"Citation check failed: {joined}")
