import gradio as gr
import os
import tempfile
import datetime
from transcriber import transcribe_audio
from analyzer import analyze_transcript

# ── PDF Generation ──
# reportlab install : pip install reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ════════════════════════════════════════════
# PDF THEME 1: DARK (active)
# ════════════════════════════════════════════
def build_pdf_dark(data: dict, transcript: str, output_path: str):
    """Dark theme: black bg, white text, blue accents."""
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    BG       = colors.HexColor("#080b14")
    CARD     = colors.HexColor("#141b2d")
    ACCENT   = colors.HexColor("#3b82f6")
    ACCENT2  = colors.HexColor("#60a5fa")
    TXT      = colors.HexColor("#e2e8f0")
    TXT2     = colors.HexColor("#94a3b8")
    BORDER   = colors.HexColor("#1e2a42")
    WHITE    = colors.white

    def bg_canvas(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BG)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.restoreState()

    styles = getSampleStyleSheet()

    h1 = ParagraphStyle("h1", fontSize=22, textColor=WHITE,
                         fontName="Helvetica-Bold", spaceAfter=4,
                         leading=26, alignment=TA_LEFT)
    h2 = ParagraphStyle("h2", fontSize=11, textColor=ACCENT2,
                         fontName="Helvetica-Bold", spaceAfter=6,
                         spaceBefore=14, leading=14,
                         borderPad=0)
    body = ParagraphStyle("body", fontSize=10, textColor=TXT,
                           fontName="Helvetica", leading=15,
                           spaceAfter=4)
    muted = ParagraphStyle("muted", fontSize=9, textColor=TXT2,
                            fontName="Helvetica", leading=12)
    mono = ParagraphStyle("mono", fontSize=9, textColor=ACCENT2,
                           fontName="Courier", leading=13, spaceAfter=2)

    story = []
    now = datetime.datetime.now().strftime("%B %d, %Y  %H:%M")

    # Header block
    header_data = [[
        Paragraph("AI Meeting Assistant", h1),
        Paragraph(f"<font color='#94a3b8'>Generated: {now}</font>", muted)
    ]]
    header_tbl = Table(header_data, colWidths=["65%", "35%"])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), CARD),
        ("TOPPADDING",   (0,0), (-1,-1), 14),
        ("BOTTOMPADDING",(0,0), (-1,-1), 14),
        ("LEFTPADDING",  (0,0), (-1,-1), 16),
        ("RIGHTPADDING", (0,0), (-1,-1), 16),
        ("ROUNDEDCORNERS", (0,0), (-1,-1), [6,6,6,6]),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",        (1,0), (1,0), "RIGHT"),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 10))

    # Summary
    summary = data.get("summary", "N/A")
    story.append(Paragraph("SUMMARY", h2))
    summary_tbl = Table([[Paragraph(summary, body)]], colWidths=["100%"])
    summary_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD),
        ("LEFTPADDING",   (0,0),(-1,-1), 16),
        ("RIGHTPADDING",  (0,0),(-1,-1), 16),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LINEBEFORE",    (0,0),(0,-1), 3, ACCENT),
    ]))
    story.append(summary_tbl)
    story.append(Spacer(1, 8))

    # Metadata row
    mood     = data.get("meeting_mood", "N/A")
    duration = data.get("duration_estimate", "N/A")
    topics   = "  ·  ".join(data.get("topics_discussed", [])) or "N/A"
    meta_data = [
        [Paragraph("MOOD", muted),     Paragraph("DURATION", muted),  Paragraph("TOPICS", muted)],
        [Paragraph(mood, body),        Paragraph(duration, body),      Paragraph(topics, body)],
    ]
    meta_tbl = Table(meta_data, colWidths=["20%","25%","55%"])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD),
        ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#0d1220")),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LINEAFTER",     (0,0),(1,-1), 0.5, BORDER),
        ("TEXTCOLOR",     (0,0),(-1,0), TXT2),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 8))

    # Key Decisions
    decisions = data.get("key_decisions", [])
    story.append(Paragraph("KEY DECISIONS", h2))
    if decisions:
        for d in decisions:
            story.append(Paragraph(f"▸  {d}", body))
    else:
        story.append(Paragraph("None identified.", muted))
    story.append(Spacer(1, 8))

    # Action Items table
    action_items = data.get("action_items", [])
    story.append(Paragraph("ACTION ITEMS", h2))
    if action_items:
        tbl_data = [[
            Paragraph("TASK", muted),
            Paragraph("OWNER", muted),
            Paragraph("DEADLINE", muted),
        ]]
        for item in action_items:
            tbl_data.append([
                Paragraph(item.get("task", ""), body),
                Paragraph(item.get("owner", "Unassigned"), body),
                Paragraph(item.get("deadline", "Not specified"), body),
            ])
        actions_tbl = Table(tbl_data, colWidths=["55%","22%","23%"])
        actions_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#0d1220")),
            ("BACKGROUND",    (0,1),(-1,-1), CARD),
            ("TEXTCOLOR",     (0,0),(-1,0), TXT2),
            ("TEXTCOLOR",     (0,1),(-1,-1), TXT),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica"),
            ("FONTSIZE",      (0,0),(-1,0), 8),
            ("TOPPADDING",    (0,0),(-1,-1), 9),
            ("BOTTOMPADDING", (0,0),(-1,-1), 9),
            ("LEFTPADDING",   (0,0),(-1,-1), 12),
            ("RIGHTPADDING",  (0,0),(-1,-1), 12),
            ("LINEBELOW",     (0,0),(-1,-2), 0.5, BORDER),
            ("LINEAFTER",     (0,0),(1,-1), 0.5, BORDER),
        ]))
        story.append(actions_tbl)
    else:
        story.append(Paragraph("No action items identified.", muted))
    story.append(Spacer(1, 8))

    # Followup Questions
    followups = data.get("followup_questions", [])
    story.append(Paragraph("FOLLOWUP QUESTIONS", h2))
    if followups:
        for i, q in enumerate(followups, 1):
            story.append(Paragraph(f"{i}.  {q}", body))
    else:
        story.append(Paragraph("None.", muted))
    story.append(Spacer(1, 14))

    # Transcript (truncated)
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph("TRANSCRIPT", h2))
    # transcript_preview = transcript[:1500] + (" ..." if len(transcript) > 1500 else "")
    story.append(Paragraph(transcript, muted))

    doc.build(story, onFirstPage=bg_canvas, onLaterPages=bg_canvas)


# ════════════════════════════════════════════
# PDF THEME 2: LIGHT (commented out - uncomment to use)
# ════════════════════════════════════════════
# def build_pdf_light(data: dict, transcript: str, output_path: str):
#     """Professional light theme: white bg, dark text, blue accents."""
#     doc = SimpleDocTemplate(
#         output_path, pagesize=A4,
#         leftMargin=20*mm, rightMargin=20*mm,
#         topMargin=20*mm, bottomMargin=20*mm
#     )
#     NAVY   = colors.HexColor("#0f172a")
#     BLUE   = colors.HexColor("#3b82f6")
#     BLUE2  = colors.HexColor("#1d4ed8")
#     GRAY   = colors.HexColor("#64748b")
#     LGRAY  = colors.HexColor("#f1f5f9")
#     BORDER = colors.HexColor("#e2e8f0")
#     WHITE  = colors.white
#
#     styles = getSampleStyleSheet()
#     h1  = ParagraphStyle("h1",  fontSize=22, textColor=NAVY,  fontName="Helvetica-Bold", spaceAfter=3, leading=26)
#     h2  = ParagraphStyle("h2",  fontSize=10, textColor=BLUE2, fontName="Helvetica-Bold", spaceAfter=5, spaceBefore=12, leading=13)
#     body= ParagraphStyle("body",fontSize=10, textColor=NAVY,  fontName="Helvetica", leading=15, spaceAfter=3)
#     muted=ParagraphStyle("muted",fontSize=9, textColor=GRAY,  fontName="Helvetica", leading=12)
#
#     story = []
#     now = datetime.datetime.now().strftime("%B %d, %Y  %H:%M")
#
#     # Header
#     header_data = [[
#         Paragraph("AI Meeting Assistant", h1),
#         Paragraph(f"<font color='#64748b'>Generated: {now}</font>", muted)
#     ]]
#     header_tbl = Table(header_data, colWidths=["65%","35%"])
#     header_tbl.setStyle(TableStyle([
#         ("BACKGROUND",   (0,0),(-1,-1), LGRAY),
#         ("TOPPADDING",   (0,0),(-1,-1), 14),
#         ("BOTTOMPADDING",(0,0),(-1,-1), 14),
#         ("LEFTPADDING",  (0,0),(-1,-1), 16),
#         ("RIGHTPADDING", (0,0),(-1,-1), 16),
#         ("LINEBELOW",    (0,0),(-1,0), 2, BLUE),
#         ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
#         ("ALIGN",        (1,0),(1,0), "RIGHT"),
#     ]))
#     story.append(header_tbl)
#     story.append(Spacer(1, 10))
#
#     # Summary
#     story.append(Paragraph("SUMMARY", h2))
#     summary_tbl = Table([[Paragraph(data.get("summary","N/A"), body)]], colWidths=["100%"])
#     summary_tbl.setStyle(TableStyle([
#         ("BACKGROUND",   (0,0),(-1,-1), LGRAY),
#         ("LEFTPADDING",  (0,0),(-1,-1), 16),
#         ("RIGHTPADDING", (0,0),(-1,-1), 16),
#         ("TOPPADDING",   (0,0),(-1,-1), 12),
#         ("BOTTOMPADDING",(0,0),(-1,-1), 12),
#         ("LINEBEFORE",   (0,0),(0,-1), 3, BLUE),
#         ("BOX",          (0,0),(-1,-1), 0.5, BORDER),
#     ]))
#     story.append(summary_tbl)
#     story.append(Spacer(1, 8))
#
#     # Meta
#     mood    = data.get("meeting_mood","N/A")
#     duration= data.get("duration_estimate","N/A")
#     topics  = "  ·  ".join(data.get("topics_discussed",[])) or "N/A"
#     meta_tbl= Table([[
#         Paragraph(f"<font color='#64748b'>Mood</font><br/>{mood}", body),
#         Paragraph(f"<font color='#64748b'>Duration</font><br/>{duration}", body),
#         Paragraph(f"<font color='#64748b'>Topics</font><br/>{topics}", body),
#     ]], colWidths=["20%","25%","55%"])
#     meta_tbl.setStyle(TableStyle([
#         ("BOX",         (0,0),(-1,-1), 0.5, BORDER),
#         ("LINEAFTER",   (0,0),(1,-1), 0.5, BORDER),
#         ("LEFTPADDING", (0,0),(-1,-1), 12),
#         ("TOPPADDING",  (0,0),(-1,-1), 10),
#         ("BOTTOMPADDING",(0,0),(-1,-1), 10),
#     ]))
#     story.append(meta_tbl)
#     story.append(Spacer(1, 8))
#
#     # Decisions
#     story.append(Paragraph("KEY DECISIONS", h2))
#     decisions = data.get("key_decisions",[])
#     for d in decisions: story.append(Paragraph(f"▸  {d}", body))
#     if not decisions: story.append(Paragraph("None identified.", muted))
#     story.append(Spacer(1, 8))
#
#     # Action Items
#     story.append(Paragraph("ACTION ITEMS", h2))
#     action_items = data.get("action_items",[])
#     if action_items:
#         tbl_data = [[Paragraph("TASK",muted), Paragraph("OWNER",muted), Paragraph("DEADLINE",muted)]]
#         for item in action_items:
#             tbl_data.append([
#                 Paragraph(item.get("task",""), body),
#                 Paragraph(item.get("owner","Unassigned"), body),
#                 Paragraph(item.get("deadline","Not specified"), body),
#             ])
#         at = Table(tbl_data, colWidths=["55%","22%","23%"])
#         at.setStyle(TableStyle([
#             ("BACKGROUND",   (0,0),(-1,0), LGRAY),
#             ("BOX",          (0,0),(-1,-1), 0.5, BORDER),
#             ("LINEBELOW",    (0,0),(-1,-2), 0.5, BORDER),
#             ("LINEAFTER",    (0,0),(1,-1), 0.5, BORDER),
#             ("LEFTPADDING",  (0,0),(-1,-1), 12),
#             ("TOPPADDING",   (0,0),(-1,-1), 9),
#             ("BOTTOMPADDING",(0,0),(-1,-1), 9),
#         ]))
#         story.append(at)
#     else: story.append(Paragraph("No action items.", muted))
#     story.append(Spacer(1, 8))
#
#     # Followups
#     story.append(Paragraph("FOLLOWUP QUESTIONS", h2))
#     followups = data.get("followup_questions",[])
#     for i,q in enumerate(followups,1): story.append(Paragraph(f"{i}.  {q}", body))
#     if not followups: story.append(Paragraph("None.", muted))
#     story.append(Spacer(1, 14))
#
#     story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
#     story.append(Spacer(1, 6))
#     story.append(Paragraph("TRANSCRIPT", h2))
#    # transcript_preview = transcript[:1500] + (" ..." if len(transcript) > 1500 else "")
#     story.append(Paragraph(transcript, muted))
#     doc.build(story)


# ════════════════════════════════════════════
# PDF THEME 3: BRANDED (commented out - uncomment to use)
# ════════════════════════════════════════════
# def build_pdf_branded(data: dict, transcript: str, output_path: str):
#     """Branded: indigo/blue header band, white body, accent tables."""
#     doc = SimpleDocTemplate(
#         output_path, pagesize=A4,
#         leftMargin=20*mm, rightMargin=20*mm,
#         topMargin=20*mm, bottomMargin=20*mm
#     )
#     INDIGO = colors.HexColor("#4f46e5")
#     INDIGO2= colors.HexColor("#6366f1")
#     LIGHT  = colors.HexColor("#eef2ff")
#     NAVY   = colors.HexColor("#1e1b4b")
#     GRAY   = colors.HexColor("#6b7280")
#     BORDER = colors.HexColor("#e0e7ff")
#     WHITE  = colors.white
#
#     styles = getSampleStyleSheet()
#     h1  = ParagraphStyle("h1",  fontSize=22, textColor=WHITE,  fontName="Helvetica-Bold", spaceAfter=2, leading=26)
#     sub = ParagraphStyle("sub", fontSize=10, textColor=colors.HexColor("#c7d2fe"), fontName="Helvetica", leading=13)
#     h2  = ParagraphStyle("h2",  fontSize=10, textColor=INDIGO,  fontName="Helvetica-Bold", spaceAfter=5, spaceBefore=12, leading=13)
#     body= ParagraphStyle("body",fontSize=10, textColor=NAVY,  fontName="Helvetica", leading=15, spaceAfter=3)
#     muted=ParagraphStyle("muted",fontSize=9, textColor=GRAY,  fontName="Helvetica", leading=12)
#
#     story = []
#     now = datetime.datetime.now().strftime("%B %d, %Y  %H:%M")
#
#     # Branded header band
#     header_data = [[
#         Paragraph("AI Meeting Assistant", h1),
#         Paragraph(f"<font color='#c7d2fe'>{now}</font><br/><font color='#c7d2fe'>Muhammad Zeeshan · AI Engineer</font>", sub)
#     ]]
#     ht = Table(header_data, colWidths=["60%","40%"])
#     ht.setStyle(TableStyle([
#         ("BACKGROUND",   (0,0),(-1,-1), INDIGO),
#         ("TOPPADDING",   (0,0),(-1,-1), 18),
#         ("BOTTOMPADDING",(0,0),(-1,-1), 18),
#         ("LEFTPADDING",  (0,0),(-1,-1), 18),
#         ("RIGHTPADDING", (0,0),(-1,-1), 18),
#         ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
#         ("ALIGN",        (1,0),(1,0), "RIGHT"),
#     ]))
#     story.append(ht)
#     story.append(Spacer(1, 12))
#
#     # Summary with indigo left border
#     story.append(Paragraph("SUMMARY", h2))
#     st = Table([[Paragraph(data.get("summary","N/A"), body)]], colWidths=["100%"])
#     st.setStyle(TableStyle([
#         ("BACKGROUND",   (0,0),(-1,-1), LIGHT),
#         ("LEFTPADDING",  (0,0),(-1,-1), 16),
#         ("RIGHTPADDING", (0,0),(-1,-1), 16),
#         ("TOPPADDING",   (0,0),(-1,-1), 12),
#         ("BOTTOMPADDING",(0,0),(-1,-1), 12),
#         ("LINEBEFORE",   (0,0),(0,-1), 4, INDIGO2),
#     ]))
#     story.append(st)
#     story.append(Spacer(1, 8))
#
#     # Meta
#     mood    = data.get("meeting_mood","N/A")
#     duration= data.get("duration_estimate","N/A")
#     topics  = "  ·  ".join(data.get("topics_discussed",[])) or "N/A"
#     mt = Table([[
#         Paragraph(f"<font color='#6b7280'>Mood</font><br/><b>{mood}</b>", body),
#         Paragraph(f"<font color='#6b7280'>Duration</font><br/><b>{duration}</b>", body),
#         Paragraph(f"<font color='#6b7280'>Topics</font><br/>{topics}", body),
#     ]], colWidths=["20%","25%","55%"])
#     mt.setStyle(TableStyle([
#         ("BACKGROUND",   (0,0),(-1,-1), LIGHT),
#         ("LINEAFTER",    (0,0),(1,-1), 0.5, BORDER),
#         ("LEFTPADDING",  (0,0),(-1,-1), 12),
#         ("TOPPADDING",   (0,0),(-1,-1), 10),
#         ("BOTTOMPADDING",(0,0),(-1,-1), 10),
#     ]))
#     story.append(mt)
#     story.append(Spacer(1, 8))
#
#     # Decisions
#     story.append(Paragraph("KEY DECISIONS", h2))
#     decisions = data.get("key_decisions",[])
#     for d in decisions: story.append(Paragraph(f"▸  {d}", body))
#     if not decisions: story.append(Paragraph("None identified.", muted))
#     story.append(Spacer(1, 8))
#
#     # Action Items
#     story.append(Paragraph("ACTION ITEMS", h2))
#     action_items = data.get("action_items",[])
#     if action_items:
#         td = [[Paragraph("TASK",muted), Paragraph("OWNER",muted), Paragraph("DEADLINE",muted)]]
#         for item in action_items:
#             td.append([
#                 Paragraph(item.get("task",""), body),
#                 Paragraph(item.get("owner","Unassigned"), body),
#                 Paragraph(item.get("deadline","Not specified"), body),
#             ])
#         at = Table(td, colWidths=["55%","22%","23%"])
#         at.setStyle(TableStyle([
#             ("BACKGROUND",    (0,0),(-1,0), INDIGO),
#             ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
#             ("BACKGROUND",    (0,1),(-1,-1), LIGHT),
#             ("LINEBELOW",     (0,0),(-1,-2), 0.5, BORDER),
#             ("LINEAFTER",     (0,0),(1,-1), 0.5, BORDER),
#             ("LEFTPADDING",   (0,0),(-1,-1), 12),
#             ("TOPPADDING",    (0,0),(-1,-1), 9),
#             ("BOTTOMPADDING", (0,0),(-1,-1), 9),
#         ]))
#         story.append(at)
#     else: story.append(Paragraph("No action items.", muted))
#     story.append(Spacer(1, 8))
#
#     # Followups
#     story.append(Paragraph("FOLLOWUP QUESTIONS", h2))
#     followups = data.get("followup_questions",[])
#     for i,q in enumerate(followups,1): story.append(Paragraph(f"{i}.  {q}", body))
#     if not followups: story.append(Paragraph("None.", muted))
#     story.append(Spacer(1, 14))
#
#     story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
#     story.append(Spacer(1, 6))
#     story.append(Paragraph("TRANSCRIPT", h2))
#     # transcript_preview = transcript[:1500] + (" ..." if len(transcript) > 1500 else "")
#     story.append(Paragraph(transcript, muted))
#     doc.build(story)


# ════════════════════════════════════════════
# ACTIVE PDF BUILDER: switch theme here
# ════════════════════════════════════════════
def generate_pdf(data: dict, transcript: str) -> str:
    """
    PDF generate karo aur file path return karo.
    Theme change karne ke liye:
      - Dark:    build_pdf_dark(...)       ← currently active
      - Light:   build_pdf_light(...)      ← uncomment theme 2 above
      - Branded: build_pdf_branded(...)    ← uncomment theme 3 above
    """
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".pdf",
        prefix="meeting_analysis_"
    )
    tmp.close()
    build_pdf_dark(data, transcript, tmp.name)  # ← change theme here
    return tmp.name


# ════════════════════════════════════════════
# CORE LOGIC
# ════════════════════════════════════════════
def format_analysis(data: dict) -> str:
    summary      = data.get("summary", "N/A")
    mood         = data.get("meeting_mood", "N/A")
    duration     = data.get("duration_estimate", "N/A")
    topics       = data.get("topics_discussed", [])
    decisions    = data.get("key_decisions", [])
    action_items = data.get("action_items", [])
    followups    = data.get("followup_questions", [])

    mood_map = {
        "Productive": "🟢 Productive", "Tense": "🔴 Tense",
        "Casual": "🟡 Casual",         "Unclear": "⚪ Unclear",
    }
    if action_items:
        actions_md = "| Task | Owner | Deadline |\n|---|---|---|\n"
        for item in action_items:
            actions_md += f"| {item.get('task','')} | {item.get('owner','Unassigned')} | {item.get('deadline','Not specified')} |\n"
    else:
        actions_md = "No action items identified."

    decisions_md = "\n".join(f"- {d}" for d in decisions) if decisions else "- None identified"
    topics_str   = "  ·  ".join(topics) if topics else "None identified"
    followups_md = "\n".join(f"{i+1}. {q}" for i,q in enumerate(followups)) if followups else "1. None"

    return f"""**SUMMARY**
{summary}

---

| Field | Value |
|:--|:--|
| Mood | {mood_map.get(mood, mood)} |
| Duration | {duration} |
| Topics | {topics_str} |

**KEY DECISIONS**
{decisions_md}

---

**ACTION ITEMS**
{actions_md}

---

**FOLLOWUP QUESTIONS**
{followups_md}"""


def process_audio(audio_path):
    if audio_path is None:
        return "Please upload an audio file first.", "", None

    tr = transcribe_audio(audio_path)
    if not tr["success"]:
        return f"**Error:** {tr['error']}", "", None

    transcript = tr["text"]
    lang       = tr.get("language", "unknown")

    an = analyze_transcript(transcript)
    if not an["success"]:
        return f"**Language:** {lang.upper()}\n\n{transcript}", f"**Error:** {an['error']}", None

    analysis_md = format_analysis(an["data"])
    pdf_path    = generate_pdf(an["data"], transcript)

    return (
        f"**Detected Language:** {lang.upper()}\n\n---\n\n{transcript}",
        analysis_md,
        pdf_path
    )


def analyze_sample(text):
    if not text or len(text.strip()) < 50:
        return "Please provide a transcript.", "", None

    an = analyze_transcript(text)
    if not an["success"]:
        return f"**Error:** {an['error']}", "", None

    analysis_md = format_analysis(an["data"])
    pdf_path    = generate_pdf(an["data"], text)

    return f"**Manual Transcript**\n\n---\n\n{text}", analysis_md, pdf_path


SAMPLE = """Sarah: Alright everyone, let's get started. We need to discuss the Q2 product roadmap.

John: Sure. I think our top priority should be the mobile app redesign. Users have been complaining about the navigation.

Sarah: Agreed. John, can you lead that? We need it done by end of April.

John: Yes, I can do that. I'll need the design team's support though.

Maria: I can assign two designers to work with John starting next Monday.

Sarah: Perfect. What about the API performance issues we discussed last week?

David: I've identified the bottleneck. It's in the authentication service. I can fix it by Friday.

Sarah: Great. So to summarize John owns the mobile redesign by April 30th, David fixes the API by Friday, and Maria provides design resources. Any questions?

John: Should we do a mid-point check-in?

Sarah: Good idea. Let's schedule a follow-up for April 15th. Meeting adjourned."""


# ════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════
CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@600;700;800&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:#080b14; --bg1:#0d1220; --bg2:#111828; --card:#141b2d;
    --b1:#1e2a42; --b2:#263350;
    --accent:#3b82f6; --accent2:#60a5fa; --purple:#8b5cf6;
    --green:#10b981; --amber:#f59e0b;
    --txt:#e2e8f0; --txt2:#94a3b8; --txt3:#475569;
}
*,*::before,*::after { font-family:'DM Sans',system-ui,sans-serif !important; box-sizing:border-box !important; }
body,.gradio-container,#root { background:var(--bg) !important; }
.gradio-container { max-width:100% !important; padding:0 !important; margin:0 !important; }

/* Header */
.app-header { background:linear-gradient(135deg,#080b14 0%,#0d1627 50%,#080b14 100%); border-bottom:1px solid var(--b1); padding:40px 24px 32px; text-align:center; position:relative; overflow:hidden; }
.app-header::before { content:''; position:absolute; top:-80px; left:50%; transform:translateX(-50%); width:500px; height:200px; background:radial-gradient(ellipse,rgba(59,130,246,0.12),transparent 70%); pointer-events:none; }
.app-header::after { content:''; position:absolute; inset:0; background-image:linear-gradient(rgba(59,130,246,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(59,130,246,0.04) 1px,transparent 1px); background-size:40px 40px; pointer-events:none; }
.header-badge { display:inline-flex; align-items:center; gap:6px; background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.25); border-radius:100px; padding:5px 14px; font-family:'DM Mono',monospace !important; font-size:11px; color:var(--accent2); letter-spacing:0.1em; margin-bottom:18px; }
.header-dot { width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 8px var(--green); animation:pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100%{box-shadow:0 0 6px var(--green)} 50%{box-shadow:0 0 14px var(--green),0 0 28px rgba(16,185,129,0.3)} }
.header-title { font-family:'Syne',sans-serif !important; font-size:clamp(28px,5vw,44px); font-weight:800; color:var(--txt); letter-spacing:-0.03em; line-height:1.1; margin-bottom:10px; position:relative; z-index:1; }
.header-title span { background:linear-gradient(135deg,var(--accent),var(--purple)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.header-sub { font-size:14px; color:var(--txt2); margin-bottom:20px; line-height:1.6; position:relative; z-index:1; }
.header-links { display:flex; justify-content:center; gap:12px; flex-wrap:wrap; position:relative; z-index:1; }
.header-link { font-family:'DM Mono',monospace !important; font-size:11px; color:var(--txt2); text-decoration:none; padding:6px 14px; border:1px solid var(--b1); border-radius:6px; background:rgba(255,255,255,0.03); transition:all 0.2s; letter-spacing:0.05em; }
.header-link:hover { border-color:var(--accent); color:var(--accent2); background:rgba(59,130,246,0.08); }

/* Stats bar */
.stats-bar { display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--b1); border:1px solid var(--b1); border-radius:12px; overflow:hidden; margin:24px auto; max-width:900px; }
.stat-item { background:var(--card); padding:16px 20px; text-align:center; }
.stat-num { font-family:'Syne',sans-serif !important; font-size:22px; font-weight:700; color:var(--accent2); line-height:1; margin-bottom:4px; }
.stat-lbl { font-family:'DM Mono',monospace !important; font-size:10px; color:var(--txt3); letter-spacing:0.1em; text-transform:uppercase; }

/* Tabs */
.tab-nav { border-bottom:1px solid var(--b1) !important; margin:0 !important; padding:0 !important; background:var(--bg1) !important; }
.tab-nav button { font-family:'DM Mono',monospace !important; font-size:12px !important; font-weight:500 !important; color:var(--txt3) !important; background:transparent !important; border:none !important; border-bottom:2px solid transparent !important; padding:14px 22px !important; border-radius:0 !important; letter-spacing:0.06em !important; text-transform:uppercase !important; transition:all 0.2s !important; margin-bottom:-1px !important; }
.tab-nav button:hover { color:var(--txt) !important; }
.tab-nav button.selected { color:var(--accent2) !important; border-bottom-color:var(--accent) !important; background:rgba(59,130,246,0.04) !important; }
.tabitem { background:var(--bg1) !important; padding:28px 24px !important; border:none !important; }

/* Textarea */
textarea { font-size:13.5px !important; line-height:1.7 !important; background:var(--card) !important; border:1px solid var(--b1) !important; border-radius:10px !important; color:var(--txt) !important; padding:14px !important; transition:border-color 0.2s,box-shadow 0.2s !important; }
textarea::placeholder { color:var(--txt3) !important; }
textarea:focus { border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(59,130,246,0.12) !important; outline:none !important; }
label span { font-family:'DM Mono',monospace !important; font-size:10px !important; font-weight:500 !important; letter-spacing:0.1em !important; text-transform:uppercase !important; color:var(--txt3) !important; }

/* Buttons */
button.primary { background:linear-gradient(135deg,#3b82f6,#2563eb) !important; color:#fff !important; border:none !important; border-radius:9px !important; font-size:13px !important; font-weight:600 !important; padding:11px 24px !important; transition:all 0.2s !important; cursor:pointer !important; box-shadow:0 2px 12px rgba(59,130,246,0.3) !important; }
button.primary:hover { background:linear-gradient(135deg,#2563eb,#1d4ed8) !important; transform:translateY(-1px) !important; box-shadow:0 6px 22px rgba(59,130,246,0.4) !important; }
button.secondary { background:rgba(255,255,255,0.05) !important; color:var(--txt2) !important; border:1px solid var(--b1) !important; border-radius:9px !important; font-size:13px !important; font-weight:500 !important; padding:11px 24px !important; transition:all 0.2s !important; }
button.secondary:hover { border-color:var(--accent) !important; color:var(--accent2) !important; background:rgba(59,130,246,0.06) !important; }

/* Markdown */
.md-out p { font-size:13.5px !important; line-height:1.85 !important; color:var(--txt) !important; margin:5px 0 !important; }
.md-out strong { font-family:'DM Mono',monospace !important; font-size:10px !important; font-weight:600 !important; letter-spacing:0.1em !important; text-transform:uppercase !important; color:var(--accent2) !important; }
.md-out hr { border:none !important; border-top:1px solid var(--b1) !important; margin:16px 0 !important; }
.md-out table { width:100% !important; border-collapse:collapse !important; margin:14px 0 !important; border:1px solid var(--b1) !important; border-radius:10px !important; overflow:hidden !important; }
.md-out thead tr { background:rgba(59,130,246,0.08) !important; }
.md-out th { padding:10px 16px !important; font-family:'DM Mono',monospace !important; font-size:10px !important; font-weight:600 !important; text-transform:uppercase !important; letter-spacing:0.1em !important; color:var(--accent2) !important; text-align:left !important; border-bottom:1px solid var(--b1) !important; }
.md-out td { padding:10px 16px !important; font-size:13px !important; color:var(--txt) !important; border-bottom:1px solid rgba(30,42,66,0.6) !important; }
.md-out tr:last-child td { border-bottom:none !important; }
.md-out li { font-size:13.5px !important; color:var(--txt) !important; line-height:1.75 !important; margin:4px 0 !important; }
.md-out ul,.md-out ol { padding-left:20px !important; margin:6px 0 !important; }
.info-strip { font-family:'DM Mono',monospace !important; font-size:11px; color:var(--txt3); margin:10px 0 16px; letter-spacing:0.04em; }

/* Footer */
footer { display:none !important; }
.app-footer { text-align:center; padding:24px; border-top:1px solid var(--b1); margin-top:8px; }
.app-footer p { font-family:'DM Mono',monospace !important; font-size:11px; color:var(--txt3); letter-spacing:0.05em; }
.app-footer a { color:var(--accent2); text-decoration:none; }
"""

HEADER_HTML = """
<div class="app-header">
    <div class="header-badge"><div class="header-dot"></div>AI-POWERED · WHISPER + LLAMA 3.3</div>
    <div class="header-title">AI Meeting Assistant</div>
    <div class="header-sub">Automatic transcription, action items &amp; structured summaries<br>from any meeting recording powered by OpenAI Whisper &amp; Groq</div>
    <div class="header-links">
        <a class="header-link" href="https://zeeshan-portfolio-amber.vercel.app" target="_blank">◈ Portfolio</a>
        <a class="header-link" href="https://linkedin.com/in/zeeshanofficial" target="_blank">◈ LinkedIn</a>
        <a class="header-link" href="https://github.com/dev-mzeeshan" target="_blank">◈ GitHub</a>
    </div>
</div>
<div class="stats-bar">
    <div class="stat-item"><div class="stat-num">95%</div><div class="stat-lbl">Accuracy (EN)</div></div>
    <div class="stat-item"><div class="stat-num">&lt;60s</div><div class="stat-lbl">Processing Time</div></div>
    <div class="stat-item"><div class="stat-num">Free</div><div class="stat-lbl">No API Cost</div></div>
</div>
"""

FOOTER_HTML = """
<div class="app-footer">
    <p>Powered by OpenAI Whisper &nbsp;·&nbsp; Groq API (Llama 3.3 70B) &nbsp;·&nbsp; Gradio 5 &nbsp;·&nbsp;
    Built by <a href="https://zeeshan-portfolio-amber.vercel.app" target="_blank">Muhammad Zeeshan</a> &nbsp;·&nbsp;
    <a href="https://github.com/dev-mzeeshan/ai-meeting-assistant" target="_blank">View Source</a></p>
</div>
"""

# ════════════════════════════════════════════
# FAVICON path: Must be the same folder
# ════════════════════════════════════════════
FAVICON = os.path.join(os.path.dirname(__file__), "favicon.ico")

# ════════════════════════════════════════════
# UI
# ════════════════════════════════════════════
with gr.Blocks(
    theme=gr.themes.Base(primary_hue="blue", neutral_hue="slate"),
    css=CSS,
    title="AI Meeting Assistant",
    # favicon_path=FAVICON if os.path.exists(FAVICON) else None,
) as demo:

    gr.HTML(HEADER_HTML)

    with gr.Tabs():

        # Tab 1: Audio Upload
        with gr.TabItem("  Upload Audio  "):
            gr.HTML("<p class='info-strip'>Upload a meeting recording (MP3, WAV, M4A: MAX 25MB). Whisper transcribes locally, Groq extracts insights, PDF is generated automatically.</p>")
            audio_input = gr.Audio(label="Meeting Recording", type="filepath", sources=["upload"])
            with gr.Row():
                analyze_btn = gr.Button("Transcribe & Analyze", variant="primary", scale=3)
                clear_btn   = gr.Button("Clear", variant="secondary", scale=1)
            gr.HTML("<p class='info-strip' style='margin-top:8px'>Processing: 30–90 seconds depending on audio length.</p>")
            with gr.Row():
                with gr.Column():
                    gr.HTML("<p class='info-strip'>TRANSCRIPT</p>")
                    transcript_out = gr.Markdown(value="*Transcript will appear here...*", elem_classes=["md-out"])
                with gr.Column():
                    gr.HTML("<p class='info-strip'>ANALYSIS</p>")
                    analysis_out = gr.Markdown(value="*Action items and summary will appear here...*", elem_classes=["md-out"])
            gr.HTML("<p class='info-strip' style='margin-top:16px'>DOWNLOAD REPORT</p>")
            pdf_out1 = gr.File(label="Meeting Analysis PDF", visible=True)

            analyze_btn.click(process_audio, inputs=audio_input, outputs=[transcript_out, analysis_out, pdf_out1])
            clear_btn.click(
                lambda: (None, "*Transcript will appear here...*", "*Action items and summary will appear here...*", None),
                outputs=[audio_input, transcript_out, analysis_out, pdf_out1]
            )

        # Tab 2: Paste Transcript
        with gr.TabItem("  Paste Transcript  "):
            gr.HTML("<p class='info-strip'>Already have a transcript? Paste it here no audio needed. PDF will be generated automatically.</p>")
            text_input = gr.Textbox(
                label="Meeting Transcript",
                placeholder="Speaker: What they said...\nSpeaker 2: Their response...",
                lines=10, max_lines=30,
            )
            with gr.Row():
                analyze_text_btn = gr.Button("Analyze Transcript", variant="primary", scale=3)
                load_sample_btn  = gr.Button("Load Sample Meeting", variant="secondary", scale=1)
            with gr.Row():
                with gr.Column():
                    gr.HTML("<p class='info-strip'>TRANSCRIPT</p>")
                    transcript_out2 = gr.Markdown(value="*Transcript will appear here...*", elem_classes=["md-out"])
                with gr.Column():
                    gr.HTML("<p class='info-strip'>ANALYSIS</p>")
                    analysis_out2 = gr.Markdown(value="*Analysis will appear here...*", elem_classes=["md-out"])
            gr.HTML("<p class='info-strip' style='margin-top:16px'>DOWNLOAD REPORT</p>")
            pdf_out2 = gr.File(label="Meeting Analysis PDF", visible=True)

            analyze_text_btn.click(analyze_sample, inputs=text_input, outputs=[transcript_out2, analysis_out2, pdf_out2])
            load_sample_btn.click(lambda: SAMPLE, outputs=text_input)

    gr.HTML(FOOTER_HTML)


if __name__ == "__main__":
    demo.launch(ssr_mode=False, favicon_path=FAVICON)