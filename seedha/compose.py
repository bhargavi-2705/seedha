"""Plain-language case file and notice. Citations are passed in. This file does not choose the law."""

from __future__ import annotations

from seedha.extract import inr

_MONTHS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
}


def place(facts: dict) -> str:
    city, state = facts.get("city") or "", facts.get("state") or ""
    if city and state and city != state:
        return f"{city}, {state}"
    return state or city or ""


def money(amount: int | None) -> str:
    if amount is None:
        return "[amount]"
    return f"Rs {inr(amount)}"


def deposit_span(facts: dict) -> str | None:
    deposit, rent = facts.get("deposit"), facts.get("rent")
    if not deposit or not rent:
        return None
    ratio = deposit / rent
    rounded = round(ratio)
    if abs(ratio - rounded) > 0.08:
        return f"about {ratio:.1f} months"
    word = _MONTHS.get(rounded, str(rounded))
    unit = "month" if rounded == 1 else "months"
    return f"{word} {unit}"


def forum(amount: int | None) -> str | None:
    if amount is None:
        return None
    if amount <= 5_000_000:
        return "District Commission"
    if amount <= 20_000_000:
        return "State Commission"
    return "National Commission"


def missing_for(facts: dict, track: str) -> list[str]:
    gaps = []
    if track == "deposit":
        if not facts.get("state"):
            gaps.append("Which city was the house in? A deposit cap, if one exists, is state law. I will not guess it.")
        if not facts.get("deposit"):
            gaps.append("How much was the deposit?")
        if not facts.get("rent"):
            gaps.append("What was the monthly rent? I need it before I can say how many months of rent the deposit was.")
        if not facts.get("other_party"):
            gaps.append("What is the landlord's name, as it should appear on the notice?")
        if not facts.get("dates"):
            gaps.append("On what date did you return the keys?")
        if not facts.get("proofs"):
            gaps.append("What can you actually show: the agreement, a transfer, photos, or chats?")
    elif track == "refund":
        if not facts.get("consideration"):
            gaps.append("What did you pay? The commission depends on that figure, not on what you want as compensation.")
        if not facts.get("other_party") and "invoice" not in " ".join(facts.get("proofs") or []):
            gaps.append("Who took the money: the seller's name, or the hospital or site?")
        if not facts.get("proofs"):
            gaps.append("What can you show: an invoice, a bank transfer, or the chat where they refused?")
    elif track == "salary":
        if not facts.get("wages"):
            gaps.append("What is your in-hand monthly wage, not your CTC? The wage Act has a ceiling, and I will not guess which side of it you are on.")
        if not facts.get("unpaid_months"):
            gaps.append("Which months are unpaid? 'Since July' is not a number of months.")
        if not facts.get("other_party"):
            gaps.append("What is the employer's legal name?")
        if not facts.get("proofs"):
            gaps.append("What can you show: an appointment letter, pay slips, or bank credits?")
    return gaps


def _party(facts: dict, fallback: str) -> str:
    return facts.get("other_party") or fallback


def explain(track: str, facts: dict, language: str, refused: list[dict]) -> dict:
    if language == "hi":
        return _hindi(track, facts, refused)
    return _english(track, facts, refused)


def _english(track: str, facts: dict, refused: list[dict]) -> dict:
    if track == "unsafe":
        return {
            "explanation": (
                "If you are in danger, call 112 now. Women can also call 181. "
                "I will not draft a notice while the story includes a threat of violence. "
                "A letter does not make you safe, and sending one can make an angry person angrier. "
                "When you are safe, come back with the money facts and I will draft the civil letter. "
                "If he has already hurt you or threatened to, tell the police. That is not this tool's job."
            ),
            "options": [
                "Call 112 if you are unsafe right now.",
                "Women can call 181, the women's helpline.",
                "After you are safe, come back. I will then draft a civil notice and still will not add a criminal threat to it.",
            ],
            "lawyer": "See a lawyer, or the police, before you send anyone a letter about this.",
            "opponent": [],
        }
    if track == "out_of_scope":
        cheque = (
            "A bounced cheque has its own Act and a short deadline. I have not loaded the Negotiable Instruments Act, so I will not quote a section from it. "
            if facts.get("cheque") else ""
        )
        return {
            "explanation": (
                f"{cheque}I only handle three problems: a security deposit that was not returned, a refund that was not paid, "
                "and wages that stopped. I would rather say that than invent a section for a problem I have not loaded. "
                "A real lawyer should hear a cheque case, a property case, a criminal case, or anything where the deadline may already be close."
            ),
            "options": ["Take this to a lawyer this week if a cheque, a police case, or a court deadline is involved."],
            "lawyer": "This one needs a lawyer. I do not have the statute loaded.",
            "opponent": [],
        }
    if track == "unclear":
        return {
            "explanation": "This story looks like more than one kind of problem. Tell me which money you want back first: the deposit, the refund, or the unpaid wages. I will not cite a law until that is clear.",
            "options": ["Reply with one of the three, and the amount."],
            "lawyer": "If the matters are tied together, a lawyer should split them. I will not.",
            "opponent": [],
        }
    if track == "deposit":
        return _deposit_en(facts, refused)
    if track == "refund":
        return _refund_en(facts, refused)
    if track == "salary":
        return _salary_en(facts, refused)
    return _english("out_of_scope", facts, refused)


def _pressure_line(facts: dict) -> str:
    if not facts.get("pressure"):
        return ""
    return (
        "You asked me to add a criminal section so that he gets scared. I will not add one. "
        "A deposit, a refund, or unpaid wages is a money demand. Threatening a criminal case in the same letter can become its own problem. "
    )


def _deposit_en(facts: dict, refused: list[dict]) -> dict:
    where = place(facts) or "a city you have not named"
    span = deposit_span(facts)
    span_line = f" That deposit is {span} of rent." if span else ""
    uk = facts.get("state") == "Uttarakhand"
    if uk:
        law = (
            "Uttarakhand has a tenancy Act. Section 11 of that Act, which I have loaded, talks about two months of rent "
            "and about giving the deposit back when the landlord takes vacant possession. Section 1(3) of the same Act says it comes into force "
            "on a date the state notifies. I have not loaded that notification, and I cannot tell from a story whether your tenancy is even covered. "
            "So the notice does not rely on that cap. It relies on the agreement and on section 73 of the Indian Contract Act, 1872."
        )
    else:
        law = (
            f"I will not cite the Model Tenancy Act for {facts.get('state') or 'an unnamed state'}. "
            "It is a model for states to copy. It is not, by itself, the law in your city. "
            "I also have not loaded your state's rent Act, so I will not quote a deposit cap from memory. "
            "People repeat a two-month figure online. If I cannot point at the section that applies to you, it does not go in the letter. "
            "What I can stand behind is the agreement and section 73 of the Indian Contract Act, 1872: if a contract is broken, "
            "the person who suffers can claim compensation for the loss that naturally arose from the breach."
        )
    explanation = (
        f"{_pressure_line(facts)}"
        f"You are asking for a deposit back in {where}.{span_line} {law} "
        "A painting deduction, or any other deduction, has to come from the agreement and from bills. A flat refusal is not a bill. "
        "I cannot decide the deduction from a story."
    )
    return {
        "explanation": " ".join(explanation.split()),
        "options": [
            "Send a notice asking for the deposit within 15 days, or a written list of deductions with bills.",
            "Do not add a criminal allegation to that letter.",
            "If there is no reply, ask a local lawyer which court takes a money claim, and whether you are still in time. I have not loaded the Limitation Act.",
        ],
        "lawyer": "See a lawyer before you file. See one sooner if the amount is large, the agreement is oral, or you left more than a couple of years ago.",
        "opponent": [
            "Show the clause that says the deposit comes back. If it is not in the agreement, you will be asked why you believed it would.",
            "The flat needed painting. Where are your photos from the day you handed over the keys?",
            "You left without a handover note, so I never accepted vacant possession.",
        ],
    }


def _refund_en(facts: dict, refused: list[dict]) -> dict:
    amount = facts.get("consideration")
    which = forum(amount)
    if which:
        forum_line = (
            f"What you paid is {money(amount)}. Under the 2021 jurisdiction rules I have loaded, "
            f"that sits with the {which}. The test is the consideration you paid, not a compensation number you add later."
        )
    else:
        forum_line = "I cannot name the commission until you tell me what you paid."
    medical = ""
    if facts.get("medical"):
        medical = (
            " You mentioned a hospital or a surgery. This letter is only about the money that was not returned. "
            "It is not an opinion on negligence, and it is not a medical-negligence case. That needs a lawyer and a medical opinion."
        )
    online = facts.get("online")
    rules = (
        " Because this was an online order, I am also using the E-Commerce Rules, 2020: a marketplace seller is not supposed to refuse a refund for goods that are defective or not as advertised, and the grievance officer has to acknowledge a complaint in forty-eight hours and redress it in one month. "
        "That one month is for the complaint, not a promise that the bank credit arrives in one month. A refund they have not even accepted is a different sentence in the same rules, and it says a reasonable period, not a fixed number of days."
        if online else
        " I am not using the E-Commerce Rules. This does not look like an online marketplace order."
    )
    explanation = (
        f"{_pressure_line(facts)}This is a refund of money you already paid, for a good or a service that was not delivered as agreed. "
        f"{forum_line}{rules}{medical} "
        "Section 2(11) of the Consumer Protection Act, 2019 is the definition of deficiency I have loaded: a fault in the performance of a service, including withholding information. "
        "The fact you can take forward is that the money was not returned. Whether a commission will agree is not something I can promise."
    )
    options = [
        f"Write to the other side and keep the complaint number. Ask for {money(amount)} back." if amount else "Write to the other side and keep the complaint number.",
        "For a packaged good, you can also register it on the National Consumer Helpline, 1915, or consumerhelpline.gov.in, before you file a case.",
    ]
    if which:
        options.append(f"If that fails, the forum I can point at is the {which}. Filing is on the e-Jagriti portal. I have not loaded the filing section, so the notice does not cite it.")
    return {
        "explanation": " ".join(explanation.split()),
        "options": options,
        "lawyer": "See a lawyer if the other side is a hospital, the amount is large, or you are close to a deadline. I have not loaded the Limitation Act.",
        "opponent": [
            "The return window in the policy had closed.",
            "The product was used, so this is not a defect.",
            "We offered a replacement, not money. Read your own invoice before you answer that.",
        ],
    }


def _salary_en(facts: dict, refused: list[dict]) -> dict:
    wages = facts.get("wages")
    months = facts.get("unpaid_months")
    unpaid = wages * months if wages and months else None
    ctc = facts.get("ctc_ignored")
    ctc_line = (
        f" I ignored the CTC of {money(ctc)}. The in-hand figure is {money(wages)}, and that is the number I compared with the ceiling."
        if ctc else ""
    )
    if wages is not None and wages <= 24000:
        day = "seventh" if facts.get("headcount") is None or facts["headcount"] < 1000 else "tenth"
        people = ""
        if facts.get("headcount"):
            people = f" You said about {facts['headcount']} people work there. If that is the establishment the Act covers, wages were due before the {day} day after the wage period, not the other one."
        law = (
            f"Your in-hand figure of {money(wages)} does not exceed Rs 24,000 a month, which is the ceiling in section 1(6) of the Payment of Wages Act, 1936, as I have it (notified at that figure in 2017). "
            f"If the Act applies to this job, section 5 is the time of payment, and section 15(2) gives twelve months from the date the wages were due to apply to the authority, unless that authority accepts a late reason.{people} "
            "I cannot tell from a story whether a workshop or a factory is actually covered. The notice says 'if the Act applies', and a lawyer or the labour office should confirm it before you rely on it."
        )
    elif wages is not None:
        law = (
            f"Your figure of {money(wages)} is above Rs 24,000 a month. That is the ceiling in the copy of section 1(6) I hold, so I will not use the Payment of Wages Act for you. "
            "I have not loaded the Industrial Disputes Act. An engineer or a manager is often outside the labour-court route. "
            "The notice uses the appointment contract and section 73 of the Indian Contract Act, 1872. A lawyer should pick the forum."
        )
    else:
        law = "I do not yet have an in-hand monthly figure, so I will not pick a wage Act."
    unpaid_line = f" On the numbers I have, the unpaid total is {money(unpaid)}." if unpaid else ""
    explanation = f"{_pressure_line(facts)}{ctc_line} This is unpaid wages.{unpaid_line} {law}"
    return {
        "explanation": " ".join(explanation.split()),
        "options": [
            "Send a notice that names the months and the in-hand amount, and give them 15 days.",
            "Keep pay slips, the appointment letter, and the bank entries together. Do not hand over the only copies.",
            "If the wage Act might apply, do not wait a year. Section 15(2) is twelve months from when the wages were due, and the excuse for being late is not automatic.",
        ] if wages is not None and wages <= 24000 else [
            "Send a contract notice for the unpaid salary. Do not describe it as a Payment of Wages Act claim.",
            "Ask a lawyer whether you are a workman at all before you pick a labour court. I have not loaded that test.",
        ],
        "lawyer": "See a lawyer before you file, and immediately if you were dismissed, if the amount includes bonus or gratuity, or if the twelve-month window may already have closed.",
        "opponent": [
            "You stopped coming to work, so nothing is due.",
            "You signed a full and final settlement. Bring it, or say clearly that you never signed one.",
            "This workplace is not an establishment the wage law covers. That is a question for the labour office, not a sentence I will pretend to settle.",
        ],
    }


def _hindi(track: str, facts: dict, refused: list[dict]) -> dict:
    """Simple Hindi. Statute quotes stay in English, and the notice does not pretend a translation is the law."""
    if track == "unsafe":
        return {
            "explanation": "अगर आप खतरे में हैं तो अभी 112 पर कॉल करें. महिलाएँ 181 पर भी कॉल कर सकती हैं. कहानी में मारने की धमकी है, इसलिए मैं नोटिस नहीं लिखूँगा. पत्र आपको सुरक्षित नहीं करता. जब आप सुरक्षित हों, तब पैसे वाले तथ्य लेकर वापस आएँ.",
            "options": ["अभी 112 पर कॉल करें.", "सुरक्षित होने के बाद सिविल नोटिस के लिए वापस आएँ."],
            "lawyer": "पत्र भेजने से पहले वकील या पुलिस से बात करें.",
            "opponent": [],
        }
    if track in {"out_of_scope", "unclear"}:
        cheque = "बाउंस चेक का अपना कानून और छोटी समय-सीमा होती है. मैंने Negotiable Instruments Act लोड नहीं किया, इसलिए उसकी कोई धारा नहीं लिखूँगा. " if facts.get("cheque") else ""
        return {
            "explanation": cheque + "मैं सिर्फ तीन बातें देखता हूँ: जमा न लौटना, रिफंड न मिलना, और रुक गया वेतन. इसके बाहर मैं धारा नहीं गढ़ता.",
            "options": ["यह काम वकील का है."],
            "lawyer": "इसके लिए वकील चाहिए.",
            "opponent": [],
        }
    base = _english(track, facts, refused)
    where = place(facts) or "जो शहर आपने नहीं बताया"
    if track == "deposit":
        span = deposit_span(facts)
        span_bit = f" यह जमानत करीब {span} के किराए के बराबर है." if span else ""
        cap = (
            "उत्तराखंड का किराया कानून मेरे पास है, पर वह तभी लागू होता है जब राज्य अधिसूचना निकाल दे. वह अधिसूचना मेरे पास नहीं है, इसलिए नोटिस में दो महीने की सीमा नहीं लिखी."
            if facts.get("state") == "Uttarakhand"
            else "मैं Model Tenancy Act को आपके राज्य का कानून नहीं मानता. वह एक मॉडल है. आपके राज्य का किराया कानून मेरे पास लोड नहीं है, इसलिए मैं जमानत की कोई सीमा याद से नहीं लिखूँगा."
        )
        explanation = (
            f"{'आपने डराने के लिए आपराधिक धारा जोड़ने को कहा. मैं नहीं जोड़ूँगा. ' if facts.get('pressure') else ''}"
            f"आप {where} में जमानत वापस माँग रहे हैं.{span_bit} {cap} "
            "नोटिस समझौते और Indian Contract Act, 1872 की धारा 73 पर टिका है: अनुबंध टूटे तो हुए नुकसान का मुआवजा माँगा जा सकता है. पेंटिंग का कटना तभी जब समझौता और बिल दोनों हों."
        )
    elif track == "refund":
        which = forum(facts.get("consideration"))
        which_bit = f" आपने {money(facts.get('consideration'))} दिए. मेरे पास जो नियम हैं, उनके हिसाब से यह {which} का मामला है." if which else "जब तक भुगतान की रकम नहीं पता, मैं कमीशन का नाम नहीं लूँगा."
        explanation = f"यह दिए हुए पैसे की वापसी है.{which_bit} कानून का मूल अंग्रेज़ी पाठ नीचे है. मैं उसका अनुवाद हवाला बनाकर नहीं लिखता."
    elif track == "salary":
        explanation = "यह रुका हुआ वेतन है. " + (
            f"हाथ में आने वाली रकम {money(facts.get('wages'))} है. "
            if facts.get("wages") is not None else ""
        )
        if facts.get("ctc_ignored"):
            explanation += f"CTC {money(facts['ctc_ignored'])} को मैंने वेतन नहीं माना. "
        if facts.get("wages") is not None and facts["wages"] <= 24000:
            explanation += "यह Rs 24,000 की सीमा के अंदर है, इसलिए Payment of Wages Act की धाराएँ नीचे हैं, और नोटिस कहता है कि कानून लागू हो तभी. धारा 15(2) में आवेदन की अवधि twelve months है."
        elif facts.get("wages") is not None:
            explanation += "यह Rs 24,000 से ऊपर है, इसलिए मैं Payment of Wages Act इस्तेमाल नहीं कर रहा. Industrial Disputes Act मैंने लोड नहीं किया. नोटिस सिर्फ अनुबंध और धारा 73 पर है."
    else:
        explanation = base["explanation"]
    base["explanation"] = " ".join(explanation.split())
    return base


def notice(track: str, facts: dict, language: str, notice_ids: set[str]) -> str | None:
    if track not in {"deposit", "refund", "salary"}:
        return None
    if language == "hi":
        body = _notice_hi(track, facts, notice_ids)
    else:
        body = _notice_en(track, facts, notice_ids)
    footer = (
        "\n\nThis is a draft for you to read. Seedha is not a lawyer, does not represent you, and will not file this. "
        "Have a person who practises in your city read it before you send it, especially on time limits and the right court or authority."
    )
    if language == "hi":
        footer += "\n\nयह मसौदा है. Seedha वकील नहीं है और यह पत्र दाखिल नहीं करता. भेजने से पहले अपने शहर के वकील को दिखाएँ. कानून का हवाला अंग्रेज़ी मूल से है."
    return body + footer


def _line(label: str, value: str) -> str:
    return f"{label}: {value}"


def _notice_en(track: str, facts: dict, notice_ids: set[str]) -> str:
    who = _party(facts, "[name]")
    where = place(facts) or "[city]"
    lines = [
        "LEGAL NOTICE",
        "(Without prejudice. Civil demand only. No criminal allegation.)",
        "",
        _line("To", who),
        _line("Address", "[address]"),
        _line("From", "[your name]"),
        _line("Address", "[your address]"),
        "",
    ]
    if track == "deposit":
        lines += [
            f"Subject: Return of the security deposit of {money(facts.get('deposit'))} for the premises at {where}",
            "",
            f"1. I was the tenant at {where}. The monthly rent was {money(facts.get('rent'))}. I paid a security deposit of {money(facts.get('deposit'))}.",
            f"2. I left the premises on {facts['dates'][-1] if facts.get('dates') else '[date you returned the keys]'}. The deposit has not been returned.",
            "3. Any deduction has to be one the agreement allows, with bills. An open refusal is not a deduction.",
            "4. Section 73 of the Indian Contract Act, 1872 says that when a contract has been broken, the party who suffers is entitled to compensation for the loss which naturally arose from that breach.",
            f"5. Pay {money(facts.get('deposit'))} within 15 days of receiving this notice, or send a written list of deductions with bills in those same 15 days. If you do neither, I will take advice on a civil claim for the money.",
        ]
    elif track == "refund":
        which = forum(facts.get("consideration")) or "[the commission that matches what I paid]"
        lines += [
            f"Subject: Refund of {money(facts.get('consideration'))} paid for goods or services that were not delivered as agreed",
            "",
            f"1. I paid {money(facts.get('consideration'))}. The good or service was cancelled, defective, or not what was agreed. The money has not come back.",
            "2. Section 2(11) of the Consumer Protection Act, 2019 treats a fault in the performance of a service, and the withholding of relevant information, as a deficiency.",
        ]
        if "ecommerce-6-3" in notice_ids:
            lines.append(
                "3. Rule 6(3) of the Consumer Protection (E-Commerce) Rules, 2020 says a marketplace seller shall not refuse to refund consideration paid where the goods or services are defective, deficient, or not of the characteristics advertised or agreed. Rule 4(5) gives the grievance officer forty-eight hours to acknowledge a complaint and one month to redress it."
            )
            demand = "4."
        else:
            demand = "3."
        lines.append(
            f"{demand} Refund {money(facts.get('consideration'))} within 15 days. If you do not, I will take advice on a complaint before the {which}. I am not adding a compensation figure, because the forum depends on what I paid."
        )
    else:
        months = facts.get("unpaid_months")
        wages = facts.get("wages")
        unpaid = wages * months if wages and months else None
        if not months:
            period = "[the unpaid months]"
        elif months == 1:
            period = "1 month"
        else:
            period = f"{months} months"
        lines += [
            f"Subject: Unpaid wages of {money(unpaid) if unpaid else money(wages)}",
            "",
            f"1. My in-hand wage is {money(wages)} a month. The unpaid period is {period}.",
            "2. The wages have not been paid. I have not signed a full and final settlement. If you say I have, send a copy.",
        ]
        if "pow-5" in notice_ids:
            day = "seventh" if not facts.get("headcount") or facts["headcount"] < 1000 else "tenth"
            lines.append(
                f"3. If the Payment of Wages Act, 1936 applies to this employment, section 5 required payment before the {day} day after the wage period "
                "(or before the second working day after termination), and section 15(2) gives twelve months from the due date to apply, unless the authority accepts a sufficient cause for delay. "
                "Section 1(6) is why I am willing to name that Act: the in-hand wages I was given do not exceed twenty four thousand rupees a month. "
                "If the Act does not cover this establishment, ignore this paragraph and treat the demand as a contract claim, to be checked by a lawyer."
            )
            demand_no = "4"
        else:
            if facts.get("wages") is None:
                lines.append("3. I am not using the Payment of Wages Act yet, because I do not have an in-hand monthly figure.")
            else:
                lines.append(
                    "3. I am not using the Payment of Wages Act. The in-hand figure I was given is above the ceiling in the copy of that Act I hold."
                )
            if "contract-73" in notice_ids:
                lines.append(
                    "4. Unpaid salary is a breach of the appointment contract. Section 73 of the Indian Contract Act, 1872 says the party who suffers by a breach is entitled to compensation for the loss which naturally arose from it."
                )
                demand_no = "5"
            else:
                demand_no = "4"
        lines.append(
            f"{demand_no}. Pay {money(unpaid) if unpaid else '[the unpaid total]'} within 15 days of receiving this notice. If you do not, I will take advice on the right authority. This is not a criminal complaint."
        )
    lines += ["", "[signature]", "[your name]", "Date: [the day you send this]"]
    return "\n".join(lines)


def _notice_hi(track: str, facts: dict, notice_ids: set[str]) -> str:
    who = _party(facts, "[नाम]")
    where = place(facts) or "[शहर]"
    head = [
        "कानूनी नोटिस",
        "(बिना पक्षपात. केवल सिविल माँग. कोई आपराधिक आरोप नहीं.)",
        "",
        f"प्रति: {who}",
        "पता: [पता]",
        "प्रेषक: [आपका नाम]",
        "",
    ]
    if track == "deposit":
        body = [
            f"विषय: {where} के मकान की जमानत {money(facts.get('deposit'))} लौटाना",
            "",
            f"1. मैं {where} में किरायेदार था/थी. मासिक किराया {money(facts.get('rent'))} था. जमानत {money(facts.get('deposit'))} दी थी.",
            f"2. मैंने {facts['dates'][-1] if facts.get('dates') else '[चाबी लौटाने की तारीख]'} को घर छोड़ा. जमानत नहीं लौटी. कटौती तभी मानी जाएगी जब समझौते में हो और बिल हों.",
            "3. Indian Contract Act, 1872 की धारा 73 के अनुसार टूटे अनुबंध पर हुए स्वाभाविक नुकसान का मुआवजा माँगा जा सकता है.",
            f"4. यह नोटिस मिलने के 15 दिनों में {money(facts.get('deposit'))} लौटाएँ, या बिलों के साथ कटौती की सूची भेजें.",
        ]
    elif track == "refund":
        which = forum(facts.get("consideration")) or "[सही आयोग]"
        body = [
            f"विषय: {money(facts.get('consideration'))} का रिफंड",
            "",
            f"1. मैंने {money(facts.get('consideration'))} दिए. सामान या सेवा तयशुदा नहीं मिली, और पैसे नहीं लौटे.",
            "2. Consumer Protection Act, 2019 की धारा 2(11) कमी को परिभाषित करती है.",
            f"3. 15 दिनों में पूरी रकम लौटाएँ, नहीं तो मैं {which} में शिकायत की सलाह लूँगा/लूँगी.",
        ]
    else:
        body = [
            f"विषय: बकाया वेतन {money(facts.get('wages'))} प्रति माह",
            "",
            f"1. हाथ में वेतन {money(facts.get('wages'))} प्रति माह है. बकाया अवधि: {facts.get('unpaid_months') or '[महीने]'}.",
            "2. भुगतान नहीं हुआ है.",
        ]
        if "pow-5" in notice_ids:
            body.append("3. यदि Payment of Wages Act, 1936 इस नौकरी पर लागू होता है, तो धारा 5 भुगतान का समय है और धारा 15(2) में आवेदन की अवधि twelve months है.")
        if "contract-73" in notice_ids:
            body.append("3. यह नियुक्ति अनुबंध का उल्लंघन है. Indian Contract Act की धारा 73 लागू होती है. Payment of Wages Act मैं इस रकम पर इस्तेमाल नहीं कर रहा.")
        body.append("4. 15 दिनों में बकाया वेतन चुकाएँ. यह आपराधिक शिकायत नहीं है.")
    return "\n".join(head + body + ["", "[हस्ताक्षर]", "[आपका नाम]", "तारीख: [जिस दिन भेजें]"])
