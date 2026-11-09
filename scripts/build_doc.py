"""Two-page solution doc. Helvetica only, so a missing glyph cannot become a black box."""

from pathlib import Path

from reportlab.lib.colors import Color, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

OUT = Path(__file__).resolve().parent.parent / "Seedha-solution-doc.pdf"
INK = Color(0.13, 0.11, 0.09)
MUTED = Color(0.38, 0.33, 0.29)
SEAL = Color(0.56, 0.18, 0.17)
RULE = Color(0.86, 0.80, 0.73)
PAPER = Color(0.98, 0.96, 0.93)

BODY = ParagraphStyle(
    "body", fontName="Times-Roman", fontSize=9, leading=11.4,
    textColor=INK, alignment=TA_LEFT, spaceAfter=4,
)
H = ParagraphStyle(
    "h", fontName="Times-Bold", fontSize=10.5, leading=13,
    textColor=SEAL, spaceBefore=6, spaceAfter=2,
)
SMALL = ParagraphStyle(
    "small", fontName="Times-Roman", fontSize=8, leading=10, textColor=INK,
)
CELL = ParagraphStyle(
    "cell", fontName="Times-Roman", fontSize=7.5, leading=9.2, textColor=INK,
)
HEADCELL = ParagraphStyle(
    "headcell", fontName="Times-Bold", fontSize=7.5, leading=9.2, textColor=white,
)


def P(text: str) -> Paragraph:
    return Paragraph(text, BODY)


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(SEAL)
    canvas.rect(0, 0, 5 * mm, A4[1], fill=1, stroke=0)
    canvas.setFillColor(MUTED)
    canvas.setFont("Times-Italic", 8)
    canvas.drawString(14 * mm, 8 * mm, "Seedha  ·  not a lawyer  ·  it will not file this")
    canvas.drawRightString(A4[0] - 12 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def main() -> None:
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=14 * mm, rightMargin=12 * mm,
        topMargin=10 * mm, bottomMargin=14 * mm,
        title="Seedha — Kuku AI Generalist, Problem 2",
        author="",
    )
    story = []
    story.append(Paragraph("SEEDHA", ParagraphStyle(
        "title", fontName="Times-Bold", fontSize=20, leading=22, textColor=INK, spaceAfter=0,
    )))
    story.append(Paragraph(
        "Kuku AI Generalist  ·  Problem 2  ·  solution doc",
        ParagraphStyle("sub", fontName="Times-Italic", fontSize=9, leading=11, textColor=MUTED, spaceAfter=2),
    ))
    story.append(Paragraph(
        "Name _______________________ &nbsp;&nbsp; Roll _______________________ &nbsp;&nbsp; Branch _______________________",
        SMALL,
    ))
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width="100%", thickness=0.6, color=SEAL, spaceAfter=4))

    story.append(Paragraph("Why this problem", H))
    story.append(P(
        "The brief names the failure: models invent sections, and they do it confidently. "
        "Seedha is built against that failure. It is a conversation for one person, about one of three problems "
        "people in India actually give up on: a deposit the landlord kept, a refund that never came, and wages that stopped. "
        "English or simple Hindi, typed or spoken into the browser. "
        "I did not pick the promo problem. Without the show pack I would have been grading myself on a screenplay I had written, "
        "and the raw-output requirement is the full pack. This one I can run, break, and show the break."
    ))

    story.append(Paragraph("What I assumed", H))
    story.append(P(
        "One dispute, enough to decide the next letter, not to file a case. "
        "Three tracks are enough. Cheque bounce, criminal law, rent acts I have not loaded, and the whole of the Limitation Act are out, and the tool says so. "
        "A statutory quote is used only from <font face='Times-Italic'>data/statutes.json</font>, with the source written next to it. "
        "If a state has a rent Act I have not opened, there is no deposit cap in the notice. Silence is the honest output. "
        "The person still has to read the draft. Seedha does not send it and does not represent anyone."
    ))

    story.append(Paragraph("How it works, and what the model is not allowed to do", H))
    story.append(P(
        "Rules read the city, the amounts, and the kind of problem, and they also catch two things a template would miss: "
        "a threat of violence, and a request to add a criminal section so the other side gets scared. "
        "Violence stops the notice and says call 112. The criminal request is refused, and the civil demand is still drafted without it. "
        "Code then retrieves quotes. A template writes the case file and the notice. Section numbers in the notice come from that list, not from a model. "
        "<font face='Times-Italic'>seedha/verify.py</font> rejects a section, a rule, the Indian Penal Code, or a line like \"courts always\" if it was not retrieved. "
        "The model is one function in <font face='Times-Italic'>seedha/llm.py</font>, off unless <font face='Times-Italic'>SEEDHA_LLM=1</font> and a Gemini key are set. "
        "It may only rephrase. If the rephrase cites anything new, it is discarded and the template stays. "
        "Change <font face='Times-Italic'>GEMINI_MODEL</font> to swap the model. A rerun on a new story needs no key: paste it in the page, or run <font face='Times-Italic'>python -m seedha.cli</font>."
    ))

    story.append(Paragraph("The decisions that should be visible in an interview", H))
    rows = [
        [Paragraph(h, HEADCELL) for h in ("Story", "What the notice may cite", "What it refuses")],
        [Paragraph(c, CELL) for c in (
            "Bengaluru deposit, four months of rent",
            "Indian Contract Act, section 73",
            "No deposit cap. The Model Tenancy Act is a model, not Karnataka law. A fluent criminal draft is rejected, not shown as the notice.",
        )],
        [Paragraph(c, CELL) for c in (
            "Dehradun deposit, ten months of rent",
            "Section 73 only",
            "Uttarakhand section 11 is shown, then kept out of the letter. Section 1(3) says the Act starts when the state notifies it. That notification is not loaded.",
        )],
        [Paragraph(c, CELL) for c in (
            "Workshop, Rs 18,000 in hand, 40 people",
            "Payment of Wages Act, sections 1(6), 5 and 15(2), and only with the words \"if it applies\"",
            "Twelve months to apply, from section 15(2). Seventh day, because they said under 1,000 people. I cannot tell if the workshop is covered.",
        )],
        [Paragraph(c, CELL) for c in (
            "Engineer, Rs 80,000. Also a CTC of Rs 80,000 with in-hand Rs 18,000",
            "Section 73 once the figure is over the ceiling. The in-hand figure when both are present.",
            "The wage Act is opened and not used above Rs 24,000, the ceiling in the copy of section 1(6) I hold (2017 notification). CTC is not wages. Industrial Disputes Act is not loaded.",
        )],
        [Paragraph(c, CELL) for c in (
            "Flipkart, Rs 2,499. Hospital package, Rs 60 lakh",
            "Consumer Protection Act, section 2(11). E-commerce rules only for the online order. Forum from the 2021 jurisdiction rules.",
            "District Commission at Rs 2,499. State Commission at Rs 60 lakh. The test is what was paid, not a compensation claim. The hospital letter is not a negligence opinion.",
        )],
        [Paragraph(c, CELL) for c in (
            "\"Add a criminal section so he pays.\" A beating threat. A bounced cheque.",
            "Section 73 for the Hyderabad deposit. Nothing for the other two.",
            "No penal section in the notice. No notice at all after a threat: call 112. No section for the cheque. The Negotiable Instruments Act is not loaded.",
        )],
    ]
    table = Table(rows, colWidths=[48 * mm, 58 * mm, 78 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SEAL),
        ("BACKGROUND", (0, 1), (-1, 1), PAPER),
        ("BACKGROUND", (0, 3), (-1, 3), PAPER),
        ("BACKGROUND", (0, 5), (-1, 5), PAPER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
    ]))
    story.append(table)

    story.append(Paragraph("Scale, cost, and the human", H))
    story.append(P(
        "The costly step is not the model. A new state, or a new problem, is one official quote plus one test, added by a person. "
        "The model does not grow the bank. At a helpline's volume the optional rephrase is a short call on a free-tier model, and the default path costs nothing because it does not call out. "
        "A human stays in the loop twice: the person checks the facts the tool heard, and someone who practises in that city reads the notice before it is sent. "
        "Nothing is filed. That is the shape that holds up if the volume is every consumer call in a week, not one demo."
    ))

    story.append(Paragraph("How I know, and where it fails", H))
    story.append(P(
        "Eleven stories are in <font face='Times-Italic'>outputs/</font>, regenerated by <font face='Times-Italic'>python -m seedha.outputs</font>, and <font face='Times-Italic'>pytest</font> fails if a saved file drifts or a notice cites a section the retriever did not return. "
        "The Bengaluru result includes <font face='Times-Italic'>rejected_draft</font>: while building this I wrote a notice that cited section 11 of the Model Tenancy Act for a Karnataka tenant, which is a real section and the wrong law, and then reached for criminal sections to make it sound serious. "
        "That draft is fluent. The checker will not let it be the notice. Cursor is the tool I used, and that was the place it went wrong."
    ))
    story.append(P(
        "It misses a city if you only name a neighbourhood I have not listed, and then it refuses the cap rather than guessing. "
        "It believes the wage number you type, which is why CTC is split out only when you say both. "
        "It cannot decide if a tenancy or a workshop is actually covered. "
        "It has no Shops Act and no time-limit statute, so it tells you to ask before you rely on a deadline other than the twelve months in section 15(2). "
        "Hindi is simple, not legal Hindi, and the statute quotes stay in English on purpose: a translation is not the law. "
        "The microphone is the browser's, and it is weak on names. The case file repeats what it heard so you can correct it before you copy the notice."
    ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(OUT)


if __name__ == "__main__":
    main()
