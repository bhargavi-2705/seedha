"""Pull facts with rules. The model is not asked to decide the amount or the state."""

from __future__ import annotations

import re

# Earliest mention in the story wins. Cities are mapped to the state that decides the law.
STATE_ALIASES: list[tuple[str, str, str]] = [
    ("dehradun", "Uttarakhand", "Dehradun"),
    ("uttarakhand", "Uttarakhand", ""),
    ("bengaluru", "Karnataka", "Bengaluru"),
    ("bangalore", "Karnataka", "Bengaluru"),
    ("बेंगलुरु", "Karnataka", "Bengaluru"),
    ("koramangala", "Karnataka", "Bengaluru"),
    ("karnataka", "Karnataka", ""),
    ("hyderabad", "Telangana", "Hyderabad"),
    ("telangana", "Telangana", ""),
    ("lucknow", "Uttar Pradesh", "Lucknow"),
    ("noida", "Uttar Pradesh", "Noida"),
    ("uttar pradesh", "Uttar Pradesh", ""),
    ("jaipur", "Rajasthan", "Jaipur"),
    ("rajasthan", "Rajasthan", ""),
    ("ludhiana", "Punjab", "Ludhiana"),
    ("punjab", "Punjab", ""),
    ("coimbatore", "Tamil Nadu", "Coimbatore"),
    ("chennai", "Tamil Nadu", "Chennai"),
    ("tamil nadu", "Tamil Nadu", ""),
    ("pune", "Maharashtra", "Pune"),
    ("mumbai", "Maharashtra", "Mumbai"),
    ("maharashtra", "Maharashtra", ""),
    ("gurugram", "Haryana", "Gurugram"),
    ("gurgaon", "Haryana", "Gurugram"),
    ("haryana", "Haryana", ""),
    ("delhi", "Delhi", "Delhi"),
    ("kolkata", "West Bengal", "Kolkata"),
    ("ahmedabad", "Gujarat", "Ahmedabad"),
    ("kochi", "Kerala", "Kochi"),
    ("देहरादून", "Uttarakhand", "Dehradun"),
    ("बैंगलोर", "Karnataka", "Bengaluru"),
    ("बेंगलोर", "Karnataka", "Bengaluru"),
    ("हैदराबाद", "Telangana", "Hyderabad"),
    ("लखनऊ", "Uttar Pradesh", "Lucknow"),
    ("नोएडा", "Uttar Pradesh", "Noida"),
    ("जयपुर", "Rajasthan", "Jaipur"),
    ("लुधियाना", "Punjab", "Ludhiana"),
    ("कोयंबटूर", "Tamil Nadu", "Coimbatore"),
    ("चेन्नई", "Tamil Nadu", "Chennai"),
    ("पुणे", "Maharashtra", "Pune"),
    ("मुंबई", "Maharashtra", "Mumbai"),
    ("गुरुग्राम", "Haryana", "Gurugram"),
    ("गुड़गांव", "Haryana", "Gurugram"),
    ("दिल्ली", "Delhi", "Delhi"),
    ("कोलकाता", "West Bengal", "Kolkata"),
    ("अहमदाबाद", "Gujarat", "Ahmedabad"),
    ("कोच्चि", "Kerala", "Kochi"),
]

DEPOSIT_WORDS = (
    "deposit", "security", "landlord", "tenant", "flat", "keys", "rent",
    "जमानत", "मकान मालिक", "किराए", "किराया", "किराये", "समझौता",
)
REFUND_WORDS = (
    "refund", "refunded", "flipkart", "amazon", "myntra", "seller", "order",
    "torn", "hospital", "surgery", "invoice", "product", "delivered",
)
SALARY_WORDS = (
    "salary", "wage", "wages", "employer", "workshop", "factory", "in-hand",
    "in hand", "ctc", "pay slip", "payslip", "appointment letter", "offer letter",
    "payroll",
)

UNSAFE_RE = re.compile(
    r"threatened to (?:beat|kill|hit)|"
    r"(?:beat|hit|assault(?:ed)?)\s+me|"
    r"came with .{0,30}men|"
    r"kill me|rape|molest|suicide|kill myself|"
    r"जान से मार|मार देगा|पीट(?:ेगा|ा)",
    re.I,
)
PRESSURE_RE = re.compile(
    r"\bipc\b|\bbns\b|section\s*420|\b420\b|section\s*406|\b406\b|"
    r"scare him|gets scared|criminal case|file an fir",
    re.I,
)
CHEQUE_RE = re.compile(r"\bcheques?\b|\bbounced\b", re.I)
MEDICAL_RE = re.compile(r"hospital|surgery|doctor|negligen", re.I)

LAKH_RE = re.compile(
    r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs)\b",
    re.I,
)
RUPEE_RE = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)", re.I)
RUPEE_AFTER_RE = re.compile(r"([\d,]+(?:\.\d+)?)\s*(?:रुपये|रुपया)", re.I)
PEOPLE_RE = re.compile(r"(\d+)\s+people", re.I)
MONTHS_N_RE = re.compile(r"(\d+)\s+months?", re.I)
MONTH_NAMES = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)
_HI_MONTHS = (
    "जनवरी|फरवरी|फ़रवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|"
    "सितंबर|सितम्बर|अक्टूबर|नवंबर|नवम्बर|दिसंबर|दिसम्बर"
)
DATE_RE = re.compile(
    r"(?:\d{1,2}\s+)?(?:" + "|".join(MONTH_NAMES) + "|" + _HI_MONTHS + r")\s+\d{4}",
    re.I,
)


def inr(amount: int) -> str:
    sign = "-" if amount < 0 else ""
    raw = str(abs(int(amount)))
    if len(raw) <= 3:
        return sign + raw
    head, tail = raw[:-3], raw[-3:]
    parts: list[str] = []
    while len(head) > 2:
        parts.append(head[-2:])
        head = head[:-2]
    if head:
        parts.append(head)
    return sign + ",".join(reversed(parts)) + "," + tail


def _parse_int(token: str) -> int:
    return int(round(float(token.replace(",", ""))))


def _hits(text: str) -> list[dict]:
    occupied: list[tuple[int, int]] = []
    found: list[dict] = []

    def free(start: int, end: int) -> bool:
        return all(end <= a or start >= b for a, b in occupied)

    for match in LAKH_RE.finditer(text):
        if not free(match.start(), match.end()):
            continue
        occupied.append((match.start(), match.end()))
        found.append({
            "amount": int(round(float(match.group(1)) * 100000)),
            "start": match.start(),
            "end": match.end(),
        })
    for regex in (RUPEE_RE, RUPEE_AFTER_RE):
        for match in regex.finditer(text):
            if not free(match.start(), match.end()):
                continue
            # "Rs 60 lakh" is already consumed by LAKH_RE; a bare "60" must not survive.
            occupied.append((match.start(), match.end()))
            found.append({
                "amount": _parse_int(match.group(1)),
                "start": match.start(),
                "end": match.end(),
            })
    found.sort(key=lambda row: row["start"])
    return found


_KIND_WORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ctc", ("ctc",)),
    ("wages", ("in-hand", "in hand", "take-home", "take home", "wage", "wages", "salary", "वेतन", "सैलरी")),
    ("deposit", ("deposit", "security", "जमानत")),
    ("rent", ("rent", "किरा")),
    ("consideration", ("order", "invoice", "paid", "package", "hospital", "shoes", "cheque", "refund")),
)


def _closest_kind(text: str, start: int, end: int) -> str:
    """Prefer the label just before the amount. Look after it only when the label comes second, as in Hindi."""
    before = text[max(0, start - 50): start]

    def nearest(window: str, from_end: bool) -> str | None:
        best_kind = None
        best_distance = 10**6
        for kind, words in _KIND_WORDS:
            for word in words:
                haystack = window.lower()
                needle = word.lower()
                at = haystack.rfind(needle) if from_end else haystack.find(needle)
                if at < 0:
                    continue
                distance = (len(window) - (at + len(word))) if from_end else at
                if distance < best_distance:
                    best_distance = distance
                    best_kind = kind
        return best_kind

    # A label sitting just before the amount ("rent was Rs 15,000") beats a word that happens to follow it ("I paid").
    # A label that follows ("80,000 रुपये जमानत") is used when nothing close sits in front.
    before_kind = nearest(before, True)
    before_distance = _label_distance(before, before_kind) if before_kind else 10**6
    if before_kind and before_distance <= 22:
        return before_kind
    after = text[end: end + 28]
    return nearest(after, False) or before_kind or "other"


def _label_distance(window: str, kind: str) -> int:
    best = 10**6
    words = dict(_KIND_WORDS)[kind]
    haystack = window.lower()
    for word in words:
        at = haystack.rfind(word.lower())
        if at >= 0:
            best = min(best, len(window) - (at + len(word)))
    return best


def _first_state(text: str) -> tuple[str, str]:
    lowered = text.lower()
    found: list[tuple[int, str, str]] = []
    for alias, state, city in STATE_ALIASES:
        at = lowered.find(alias.lower())
        if at >= 0:
            found.append((at, state, city))
    if not found:
        return "", ""
    found.sort()
    return found[0][1], found[0][2]


def _party(text: str) -> str:
    patterns = (
        r"landlord is ([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})",
        r"landlord,?\s+Mr\.?\s+([A-Z][a-z]+)",
        r"landlord ([A-Z][a-z]+)",
        r"\bMr\.?\s+([A-Z][a-z]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def _proofs(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    pairs = (
        ("rental agreement or lease", ("agreement", "समझौता", "lease")),
        ("payment proof", ("upi", "यूपीआई", "receipt", "bank", "transfer", "pay slip", "payslip")),
        ("photos of the premises", ("photo",)),
        ("chat or email screenshots", ("screenshot", "chat", "email")),
        ("invoice", ("invoice",)),
        ("appointment or offer letter", ("appointment", "offer letter")),
        ("attendance record", ("attendance",)),
    )
    for label, keys in pairs:
        if any(key in lowered for key in keys):
            found.append(label)
    return found


def _dates(text: str) -> list[str]:
    return [match.group(0).strip() for match in DATE_RE.finditer(text)]


def _month_count(text: str) -> int | None:
    count_match = MONTHS_N_RE.search(text)
    if count_match:
        window = text[max(0, count_match.start() - 24): count_match.end() + 12].lower()
        if "rent" not in window and "deposit" not in window:
            return int(count_match.group(1))
    lowered = text.lower()
    names = re.findall(
        r"\b(" + "|".join(MONTH_NAMES) + r")\b(?=\s+\d{4}|\s*,|\s+and\b)",
        lowered,
    )
    if len(names) >= 2:
        return len(names)
    if len(names) == 1 and re.search(rf"\bfor {names[0]}\b", lowered):
        return 1
    return None


def _score(text: str, words: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(1 for word in words if word in lowered)


def classify(text: str) -> str:
    if UNSAFE_RE.search(text):
        return "unsafe"
    deposit = _score(text, DEPOSIT_WORDS)
    refund = _score(text, REFUND_WORDS)
    salary = _score(text, SALARY_WORDS)
    best = max(deposit, refund, salary)
    if best == 0:
        return "out_of_scope"
    # A cheque-bounce question with no consumer, wage, or deposit story is its own statute.
    if CHEQUE_RE.search(text) and deposit == 0 and salary == 0 and refund == 0:
        return "out_of_scope"
    scores = {"deposit": deposit, "refund": refund, "salary": salary}
    winners = [name for name, score in scores.items() if score == best]
    if len(winners) > 1:
        return "unclear"
    return winners[0]


def extract(text: str) -> dict:
    hits = _hits(text)
    by_kind: dict[str, list[int]] = {}
    for hit in hits:
        by_kind.setdefault(_closest_kind(text, hit["start"], hit["end"]), []).append(hit["amount"])
    state, city = _first_state(text)
    wages = by_kind.get("wages", [])
    ctc = by_kind.get("ctc", [])
    monthly = wages[0] if wages else None
    track = classify(text)
    headcount_match = PEOPLE_RE.search(text)
    return {
        "track": track,
        "state": state,
        "city": city,
        "amounts": [hit["amount"] for hit in hits],
        "deposit": (by_kind.get("deposit") or [None])[0],
        "rent": (by_kind.get("rent") or [None])[0],
        "wages": monthly,
        "ctc_ignored": ctc[0] if ctc and monthly else None,
        "consideration": (by_kind.get("consideration") or [None])[0],
        "unpaid_months": _month_count(text) if track == "salary" else None,
        "headcount": int(headcount_match.group(1)) if headcount_match else None,
        "other_party": _party(text),
        "proofs": _proofs(text),
        "dates": _dates(text),
        "pressure": bool(PRESSURE_RE.search(text)),
        "medical": bool(MEDICAL_RE.search(text)),
        "cheque": bool(CHEQUE_RE.search(text)),
    }
