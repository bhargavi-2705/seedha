import json
from pathlib import Path

from seedha.bank import cases
from seedha.pipeline import REJECTED_EXAMPLE, advise
from seedha.verify import verify_model_text

ROOT = Path(__file__).resolve().parent.parent


def _ids(result: dict) -> set[str]:
    return {row["id"] for row in result["statutes"]}


def test_every_sample_matches_its_expectation():
    failures = []
    for case in cases():
        result = advise(case["text"], case.get("language") or "en")
        expect = case["expect"]
        notice = result["notice"] or ""
        problems = []
        if result["track"] != expect["track"]:
            problems.append(f"track {result['track']}")
        if "state" in expect and (result["facts"].get("state") or "") != expect["state"]:
            problems.append(f"state {result['facts'].get('state')}")
        if "notice" in expect and bool(notice) != expect["notice"]:
            problems.append(f"notice={bool(notice)}")
        cited = _ids(result)
        for statute_id in expect.get("must_cite", []):
            if statute_id not in cited:
                problems.append(f"missing {statute_id}")
        for statute_id in expect.get("must_not_cite", []):
            if statute_id in cited:
                problems.append(f"cited {statute_id}")
        blob = result["explanation"]
        for snippet in expect.get("explanation_must_contain", []):
            if snippet not in blob:
                problems.append(f"explanation lacks {snippet!r}")
        for snippet in expect.get("notice_must_not_contain", []):
            if snippet in notice:
                problems.append(f"notice contains {snippet!r}")
        notice_rows = [row for row in result["statutes"] if row.get("in_notice")]
        leaked = verify_model_text(notice, notice_rows)
        if leaked:
            problems.append("verifier: " + "; ".join(leaked))
        if problems:
            failures.append(f"{case['id']}: {', '.join(problems)}\n{result['explanation'][:400]}\n---\n{notice[:400]}")
    assert not failures, "\n\n".join(failures)


def test_bengaluru_draft_is_rejected_and_is_not_the_notice():
    result = advise(cases()[0]["text"], "en")
    draft = result["rejected_draft"]
    assert draft["problems"], draft
    assert "Model Tenancy" in " ".join(draft["problems"]) or any("11" in item for item in draft["problems"])
    assert result["notice"]
    assert "Model Tenancy" not in result["notice"]
    assert "420" not in result["notice"]
    assert REJECTED_EXAMPLE not in result["notice"]


def test_rejected_example_fails_on_its_own():
    problems = verify_model_text(REJECTED_EXAMPLE, [])
    assert any("420" in item or "Section 420" in item for item in problems)
    assert any("Model Tenancy" in item for item in problems)
    assert any("406" in item for item in problems)
    assert any("courts always" in item for item in problems)


def test_outputs_are_the_pipeline_and_not_hand_edited():
    """Raw outputs, if present, must match a fresh run. Regeneration is python -m seedha.outputs."""
    out = ROOT / "outputs"
    if not any(out.glob("*.json")):
        return
    for case in cases():
        path = out / f"{case['id']}.json"
        saved = json.loads(path.read_text(encoding="utf-8"))
        fresh = advise(case["text"], case.get("language") or "en")
        assert saved == fresh, case["id"]
