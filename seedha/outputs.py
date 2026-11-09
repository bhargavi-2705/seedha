"""Write the raw, unedited case files for every sample story."""

from __future__ import annotations

import json
from pathlib import Path

from seedha.bank import cases
from seedha.pipeline import advise

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for case in cases():
        result = advise(case["text"], case.get("language") or "en")
        path = OUT / f"{case['id']}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{case['id']}: track={result['track']} notice={'yes' if result['notice'] else 'no'}")


if __name__ == "__main__":
    main()
