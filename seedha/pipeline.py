"""Turn a messy story into a case file. Code picks the law. A model may only rephrase."""

from __future__ import annotations

from seedha.bank import get
from seedha.compose import explain, forum, missing_for, notice
from seedha.extract import classify, extract
from seedha.verify import verify_model_text

WAGE_CEILING = 24000

# The mistake this tool is built to stop. Kept here so a reviewer can see the rejection,
# not so it can ever be returned as the notice.
REJECTED_EXAMPLE = (
    "Under Section 11 of the Model Tenancy Act, 2021, the landlord cannot keep more than two months of rent, "
    "so she must return the rest at once. If she refuses, file a criminal case under Section 420 IPC for cheating "
    "and Section 406 for criminal breach of trust. Courts always order double the deposit as a penalty."
)


def _pack(statute_id: str, in_notice: bool) -> dict:
    row = dict(get(statute_id))
    row["in_notice"] = in_notice
    return row


def _online(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in ("flipkart", "amazon", "myntra", "ajio", "meesho", "website"))


def _rent_refusal(state: str) -> dict:
    if state == "Uttarakhand":
        return {}
    if state == "Tamil Nadu":
        reason = (
            "Tamil Nadu has its own tenancy Act. I have not loaded the official text. "
            "I will not quote the three-month figure that circulates online, because the part people skip is the part that lets the agreement say otherwise."
        )
    elif state == "Andhra Pradesh":
        reason = (
            "Andhra Pradesh has its own tenancy Act. I have not loaded it, so I will not quote a deposit cap."
        )
    elif state:
        reason = (
            f"The Model Tenancy Act is a model, not the law in {state}. "
            f"I have not loaded the {state} rent Act, so your notice has no deposit cap."
        )
    else:
        reason = (
            "You have not named a city. Deposit caps are state law. "
            "The Model Tenancy Act is not, by itself, the law anywhere, so I will not use it."
        )
    return {
        "label": "A statutory deposit cap",
        "reason": reason,
    }


def retrieve(text: str, facts: dict) -> tuple[list[dict], list[dict]]:
    track = facts["track"]
    cited: list[dict] = []
    refused: list[dict] = []
    if facts.get("pressure"):
        refused.append({
            "label": "A criminal section, added to frighten the other side",
            "reason": "Not cited. A money dispute does not become a criminal notice because the letter is angrier. I will not name a penal section.",
        })
    if track == "deposit":
        cited.append(_pack("contract-73", True))
        if facts.get("state") == "Uttarakhand":
            # Shown, and kept out of the notice until commencement is actually loaded.
            cited.append(_pack("uk-tenancy-1-3", False))
            cited.append(_pack("uk-tenancy-11", False))
        else:
            refusal = _rent_refusal(facts.get("state") or "")
            if refusal:
                refused.append(refusal)
    elif track == "refund":
        cited.append(_pack("cpa-2-7", True))
        cited.append(_pack("cpa-2-11", True))
        cited.append(_pack("cpa-jurisdiction-2021", True))
        if facts.get("online"):
            cited.append(_pack("ecommerce-4-5", True))
            cited.append(_pack("ecommerce-4-10", True))
            cited.append(_pack("ecommerce-6-3", True))
        else:
            refused.append({
                "label": "Consumer Protection (E-Commerce) Rules, 2020",
                "reason": "Not cited. This story does not read as an online marketplace order, so those rules stay out of the notice.",
            })
        if facts.get("consideration") is None:
            refused.append({
                "label": "A named consumer commission",
                "reason": "Not named. The 2021 rules look at what you paid. I do not have that number.",
            })
    elif track == "salary":
        wages = facts.get("wages")
        if wages is not None and wages <= WAGE_CEILING:
            cited.append(_pack("pow-1-6", True))
            cited.append(_pack("pow-5", True))
            cited.append(_pack("pow-15-2", True))
        elif wages is not None:
            ceiling = get("pow-1-6")
            refused.append({
                "label": "Payment of Wages Act, 1936",
                "reason": (
                    f"Not used. Section 1(6) in the copy I hold applies where wages for the wage period do not exceed Rs 24,000 a month. "
                    f"The in-hand figure here is higher, so sections 5 and 15 do not go in the notice either."
                ),
                "quote": ceiling["quote"],
                "source": ceiling["source"],
                "source_url": ceiling["source_url"],
            })
            cited.append(_pack("contract-73", True))
        else:
            refused.append({
                "label": "Payment of Wages Act, 1936",
                "reason": "Not used yet. I need the in-hand monthly wage before I know whether the ceiling even lets me open this Act.",
            })
            cited.append(_pack("contract-73", True))
    return cited, refused


def _rejected_example(facts: dict, notice_rows: list[dict]) -> dict | None:
    if facts.get("track") != "deposit" or facts.get("state") != "Karnataka":
        return None
    return {
        "text": REJECTED_EXAMPLE,
        "problems": verify_model_text(REJECTED_EXAMPLE, notice_rows),
        "note": (
            "This is not your notice. While building Seedha I treated the Model Tenancy Act as if a Bengaluru tenant could use it, "
            "and I reached for criminal sections to make the letter sound serious. That draft is fluent and wrong. "
            "The checker below is what stops it being shown as advice. A live model, if you add a key, is held to the same check."
        ),
    }


def advise(text: str, language: str = "en") -> dict:
    cleaned = (text or "").strip()
    if not cleaned:
        return {
            "language": language,
            "track": "empty",
            "explanation": "Tell me what happened, in the language you actually speak. One story is enough.",
            "notice": None,
            "statutes": [],
            "refused": [],
            "missing": [],
            "options": [],
            "opponent": [],
            "checks": [],
            "facts": {},
            "model": "rules",
        }
    if len(cleaned) > 8000:
        cleaned = cleaned[:8000]
    lang = language if language in {"en", "hi"} else "en"
    facts = extract(cleaned)
    facts["online"] = _online(cleaned)
    facts["track"] = classify(cleaned)
    cited, refused = retrieve(cleaned, facts)
    prose = explain(facts["track"], facts, lang, refused)
    notice_rows = [row for row in cited if row.get("in_notice")]
    letter = notice(facts["track"], facts, lang, {row["id"] for row in notice_rows})
    problems = verify_model_text(letter or "", notice_rows)
    if problems:
        letter = None
        refused.append({
            "label": "The draft notice",
            "reason": "Withdrawn by the citation check: " + "; ".join(problems),
        })
    which = forum(facts.get("consideration")) if facts["track"] == "refund" else None
    checks = ["Citations in the notice were checked against the sections retrieved for this story."]
    if facts["track"] == "deposit" and facts.get("state") != "Uttarakhand":
        checks.append("No deposit cap was cited. The Model Tenancy Act was not treated as local law.")
    if facts["track"] == "deposit" and facts.get("state") == "Uttarakhand":
        checks.append("The Uttarakhand deposit section is shown, and kept out of the notice, because commencement is not loaded.")
    if facts["track"] == "salary" and facts.get("wages") is not None and facts["wages"] > WAGE_CEILING:
        checks.append("Payment of Wages Act was opened and then not used, because the in-hand figure is over Rs 24,000.")
    if facts.get("ctc_ignored"):
        checks.append("CTC was ignored. The in-hand figure is the one compared with the wage ceiling.")
    if which:
        checks.append(f"Consumer forum follows what was paid ({which}), not a compensation claim.")
    if facts.get("pressure"):
        checks.append("A request to add a criminal section was refused.")
    result = {
        "language": lang,
        "track": facts["track"],
        "title": {
            "deposit": "Security deposit",
            "refund": "Refund that did not come",
            "salary": "Wages that stopped",
            "unsafe": "Safety first",
            "unclear": "Which problem?",
            "out_of_scope": "Outside what I have loaded",
            "empty": "No story yet",
        }.get(facts["track"], facts["track"]),
        "facts": {
            "state": facts.get("state") or None,
            "city": facts.get("city") or None,
            "other_party": facts.get("other_party") or None,
            "deposit": facts.get("deposit"),
            "rent": facts.get("rent"),
            "wages": facts.get("wages"),
            "ctc_ignored": facts.get("ctc_ignored"),
            "consideration": facts.get("consideration"),
            "unpaid_months": facts.get("unpaid_months"),
            "headcount": facts.get("headcount"),
            "proofs": facts.get("proofs") or [],
            "dates": facts.get("dates") or [],
            "forum": which,
        },
        "missing": missing_for(facts, facts["track"]),
        "statutes": cited,
        "refused": refused,
        "explanation": prose["explanation"],
        "options": prose["options"],
        "lawyer": prose["lawyer"],
        "opponent": prose["opponent"],
        "notice": letter,
        "checks": checks,
        "rejected_draft": _rejected_example(facts, notice_rows),
        "model": "rules",
        "llm_rejected": False,
    }
    return _maybe_rephrase(cleaned, result, notice_rows)


def _maybe_rephrase(story: str, result: dict, notice_rows: list[dict]) -> dict:
    """Optional. Off unless SEEDHA_LLM=1, so a sample run stays reproducible."""
    import os

    if os.getenv("SEEDHA_LLM", "").strip() != "1":
        return result
    try:
        from seedha.llm import rephrase
    except Exception:
        return result
    rewritten = rephrase(story, result["explanation"])
    if not rewritten:
        return result
    problems = verify_model_text(rewritten, result["statutes"])
    result["model"] = "gemini+rules"
    if problems:
        result["llm_rejected"] = True
        result["checks"] = list(result["checks"]) + [
            "The model rewrote the explanation and the citation check rejected the rewrite. You are seeing the template."
        ]
        result["rejected_draft"] = {
            "text": rewritten,
            "problems": problems,
            "note": "A live model wrote this. It did not pass the citation check, so it was not shown as the answer.",
        }
        return result
    result["explanation"] = rewritten
    result["checks"] = list(result["checks"]) + ["A model rewrote the explanation. The citation check let it through."]
    return result
