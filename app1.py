# app.py
# Gradio interface — Audio upload karo, transcript dekho, analysis dekho.

import gradio as gr
from transcriber import transcribe_audio
from analyzer import analyze_transcript


def format_analysis(data: dict) -> str:
    """Analysis dict ko clean markdown mein convert karo."""
    
    summary      = data.get("summary", "N/A")
    mood         = data.get("meeting_mood", "N/A")
    duration     = data.get("duration_estimate", "N/A")
    topics       = data.get("topics_discussed", [])
    decisions    = data.get("key_decisions", [])
    action_items = data.get("action_items", [])
    followups    = data.get("followup_questions", [])

    mood_map = {
        "Productive": "🟢 Productive",
        "Tense":      "🔴 Tense",
        "Casual":     "🟡 Casual",
        "Unclear":    "⚪ Unclear",
    }

    # Action items table
    if action_items:
        actions_md = "| Task | Owner | Deadline |\n|---|---|---|\n"
        for item in action_items:
            task     = item.get("task", "")
            owner    = item.get("owner", "Unassigned")
            deadline = item.get("deadline", "Not specified")
            actions_md += f"| {task} | {owner} | {deadline} |\n"
    else:
        actions_md = "No action items identified."

    # Decisions
    decisions_md = "\n".join(f"- {d}" for d in decisions) if decisions else "- None identified"
    
    # Topics
    topics_md = "  ·  ".join(topics) if topics else "None identified"
    
    # Followups
    followups_md = "\n".join(f"{i+1}. {q}" for i, q in enumerate(followups)) if followups else "None"

    return f"""---
### Meeting Summary

{summary}

---

| Field | Value |
|:--|:--|
| Meeting Mood | {mood_map.get(mood, mood)} |
| Duration Estimate | {duration} |
| Topics | {topics_md} |

---

**KEY DECISIONS**
{decisions_md}

---

**ACTION ITEMS**
{actions_md}

---

**FOLLOWUP QUESTIONS**
{followups_md}
"""


def process_audio(audio_path: str):
    """
    Main function — audio file process karo aur dono outputs return karo.
    Gradio mein yeh function tab call hota hai jab user 'Analyze' click kare.
    """
    if audio_path is None:
        return "Please upload an audio file first.", ""
    
    # Step 1: Transcribe
    transcript_result = transcribe_audio(audio_path)
    
    if not transcript_result["success"]:
        error_msg = f"**Transcription Error:** {transcript_result['error']}"
        return error_msg, ""
    
    transcript = transcript_result["text"]
    lang       = transcript_result.get("language", "unknown")
    
    transcript_display = f"**Detected Language:** {lang.upper()}\n\n---\n\n{transcript}"
    
    # Step 2: Analyze
    analysis_result = analyze_transcript(transcript)
    
    if not analysis_result["success"]:
        return transcript_display, f"**Analysis Error:** {analysis_result['error']}"
    
    analysis_display = format_analysis(analysis_result["data"])
    
    return transcript_display, analysis_display


# ── Sample demo text (for testing without audio) ──
def load_sample_transcript():
    """
    Ek sample transcript load karo taake user bina audio ke bhi
    analyzer test kar sake.
    """
    sample = """Sarah: Alright everyone, let's get started. We need to discuss the Q2 product roadmap.
    
John: Sure. I think our top priority should be the mobile app redesign. Users have been complaining about the navigation.

Sarah: Agreed. John, can you lead that? We need it done by end of April.

John: Yes, I can do that. I'll need the design team's support though.

Maria: I can assign two designers to work with John starting next Monday.

Sarah: Perfect. What about the API performance issues we discussed last week?

David: I've identified the bottleneck. It's in the authentication service. I can fix it by Friday.

Sarah: Great. So to summarize — John owns the mobile redesign by April 30th, David fixes the API by Friday, and Maria provides design resources. Any questions?

John: Should we do a mid-point check-in?

Sarah: Good idea. Let's schedule a follow-up for April 15th. Meeting adjourned."""
    
    return sample


def analyze_sample(sample_text: str):
    """Sample transcript ko directly analyze karo (bina audio ke)."""
    if not sample_text or len(sample_text.strip()) < 50:
        return "Please provide a transcript.", ""
    
    result = analyze_transcript(sample_text)
    
    if not result["success"]:
        return f"**Error:** {result['error']}", ""
    
    return f"**Manual Transcript**\n\n---\n\n{sample_text}", format_analysis(result["data"])


# ── CSS ──
CSS = """
* {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
}
.gradio-container {
    max-width: 820px !important;
    margin: 0 auto !important;
    padding-bottom: 40px !important;
}
.tab-nav button {
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 9px 20px !important;
}
.tab-nav button.selected {
    color: #6366f1 !important;
    border-bottom: 2px solid #6366f1 !important;
}
button.primary {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
button.primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}
button.secondary {
    border-radius: 9px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.md-out p { font-size: 14px !important; line-height: 1.8 !important; }
.md-out strong { font-size: 11px !important; font-weight: 700 !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }
.md-out table { width: 100% !important; border-collapse: collapse !important; margin: 12px 0 !important; }
.md-out th { font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; padding: 9px 14px !important; }
.md-out td { font-size: 13.5px !important; padding: 10px 14px !important; }
.md-out hr { margin: 14px 0 !important; }
footer { display: none !important; }
"""


# ── UI ──
with gr.Blocks(
    theme=gr.themes.Base(
        primary_hue="indigo",
        neutral_hue="slate",
    ),
    css=CSS,
    title="AI Meeting Assistant",
) as demo:

    gr.Markdown("""
# AI Meeting Assistant
Automatic transcription, action items, and structured summaries from meeting recordings &nbsp;·&nbsp; Built by [**Muhammad Zeeshan**](https://zeeshan-portfolio-amber.vercel.app) &nbsp;·&nbsp; [GitHub](https://github.com/dev-mzeeshan)

---
""")

    with gr.Tabs():

        # ── Tab 1: Audio Upload ──
        with gr.TabItem("Upload Audio"):
            gr.Markdown(
                "<p style='font-size:13px;color:#64748b;margin:0 0 16px'>"
                "Upload a meeting recording (MP3, WAV, M4A — max 25MB). "
                "Whisper will transcribe it, then AI will extract action items and insights."
                "</p>"
            )

            audio_input = gr.Audio(
                label="Meeting Recording",
                type="filepath",
                sources=["upload"],
            )

            with gr.Row():
                analyze_btn = gr.Button("Transcribe & Analyze", variant="primary", scale=3)
                clear_btn   = gr.Button("Clear", variant="secondary", scale=1)

            gr.Markdown("<p style='font-size:12px;color:#94a3b8;margin:10px 0 4px'>Processing time: ~30-60 seconds depending on audio length.</p>")

            with gr.Row():
                transcript_out = gr.Markdown(
                    value="*Transcript will appear here...*",
                    label="Transcript",
                    elem_classes=["md-out"],
                )
                analysis_out = gr.Markdown(
                    value="*Analysis will appear here...*",
                    label="Analysis",
                    elem_classes=["md-out"],
                )

            analyze_btn.click(
                process_audio,
                inputs=audio_input,
                outputs=[transcript_out, analysis_out],
            )
            clear_btn.click(
                lambda: (None, "*Transcript will appear here...*", "*Analysis will appear here...*"),
                outputs=[audio_input, transcript_out, analysis_out],
            )

        # ── Tab 2: Paste Transcript ──
        with gr.TabItem("Paste Transcript"):
            gr.Markdown(
                "<p style='font-size:13px;color:#64748b;margin:0 0 16px'>"
                "Already have a transcript? Paste it here to get instant AI analysis "
                "without uploading audio."
                "</p>"
            )

            text_input = gr.Textbox(
                label="Meeting Transcript",
                placeholder="Paste your meeting transcript here...\n\nFormat: 'Speaker: What they said'",
                lines=10,
                max_lines=30,
            )

            with gr.Row():
                analyze_text_btn = gr.Button("Analyze Transcript", variant="primary", scale=3)
                load_sample_btn  = gr.Button("Load Sample",        variant="secondary", scale=1)

            with gr.Row():
                transcript_out2 = gr.Markdown(
                    value="*Transcript will appear here...*",
                    elem_classes=["md-out"],
                )
                analysis_out2 = gr.Markdown(
                    value="*Analysis will appear here...*",
                    elem_classes=["md-out"],
                )

            analyze_text_btn.click(
                analyze_sample,
                inputs=text_input,
                outputs=[transcript_out2, analysis_out2],
            )
            load_sample_btn.click(
                load_sample_transcript,
                outputs=text_input,
            )

    gr.Markdown(
        "<p style='font-size:12px;color:#94a3b8;text-align:center;margin-top:20px'>"
        "Powered by OpenAI Whisper &nbsp;·&nbsp; Groq API (Llama 3.3 70B) &nbsp;·&nbsp; Gradio 5 &nbsp;·&nbsp; "
        "<a href='https://github.com/dev-mzeeshan/ai-meeting-assistant' target='_blank'>GitHub</a>"
        "</p>"
    )


if __name__ == "__main__":
    demo.launch(ssr_mode=False)