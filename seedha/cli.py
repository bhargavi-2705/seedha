"""Run one story from the command line. Used in the interview on a new input."""

from __future__ import annotations

import json
import sys

from seedha.pipeline import advise


def main() -> None:
    language = "en"
    args = sys.argv[1:]
    if args and args[0] in {"--hi", "--en"}:
        language = "hi" if args[0] == "--hi" else "en"
        args = args[1:]
    text = " ".join(args).strip() or sys.stdin.read()
    json.dump(advise(text, language), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
