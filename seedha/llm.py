"""Optional phraser. Swap the model by changing GEMINI_MODEL. No key means the template stands."""

from __future__ import annotations

import json
import os

import httpx

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def rephrase(story: str, explanation: str) -> str | None:
    key = api_key()
    if not key:
        return None
    prompt = (
        "Rewrite the explanation in the same language, in shorter sentences, for a person who is not a lawyer. "
        "Do not add a section, rule, Act, or case that is not already named in the explanation. "
        "Do not say the person will win. Do not add a criminal allegation. Return JSON {\"explanation\": \"...\"} only.\n\n"
        f"STORY:\n{story}\n\nEXPLANATION:\n{explanation}"
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {"explanation": {"type": "STRING"}},
                "required": ["explanation"],
            },
        },
    }
    url = GEMINI_URL.format(model=model_name())
    try:
        response = httpx.post(url, params={"key": key}, json=body, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
    except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, TypeError):
        return None
    explanation_out = str(parsed.get("explanation") or "").strip()
    return explanation_out or None
