#!/usr/bin/env python3
"""Generate a branded follow-up questions PowerPoint for the next audit session.

Called by the GQ capability after generating and gate-checking follow-up questions.
Reads a questions-input.json prepared by Claude and renders a .pptx using python-pptx.

Usage:
  python3 generate_follow_up_pptx.py --client-slug <slug> --session <N> --questions-json <path>
  python3 generate_follow_up_pptx.py --client-slug <slug> --session <N> --questions-json <path> --output-dir <path>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent
REPO_ROOT = PLUGIN_ROOT.parent
LOGO_PATH = PLUGIN_ROOT / "assets" / "apg-logo-dark.png"

sys.path.insert(0, str(SCRIPT_DIR))
import _paths  # noqa: E402

# ---------------------------------------------------------------------------
# Brand constants
# ---------------------------------------------------------------------------
APG_GREEN = RGBColor(0x25, 0x63, 0xEB)
DARK      = RGBColor(0x1A, 0x1A, 0x1A)
MED_GREY  = RGBColor(0x66, 0x66, 0x66)
LIGHT_BG  = RGBColor(0xF0, 0xF0, 0xF0)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)

SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5
MAX_QUESTIONS_PER_SLIDE = 5


# ---------------------------------------------------------------------------
# Slide helpers
# ---------------------------------------------------------------------------

def _new_prs() -> Presentation:
    prs = Presentation()
    prs.slide_width  = Inches(SLIDE_W_IN)
    prs.slide_height = Inches(SLIDE_H_IN)
    return prs


def _blank_slide(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _set_bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_logo(slide, right: float = 0.5, top: float = 0.4, width: float = 1.0) -> None:
    if not LOGO_PATH.exists():
        return
    left = Inches(SLIDE_W_IN - right - width)
    slide.shapes.add_picture(str(LOGO_PATH), left, Inches(top), width=Inches(width))


def _add_textbox(slide, left, top, width, height, text,
                 size=18, bold=False, color=DARK,
                 align=PP_ALIGN.LEFT, font="Calibri") -> None:
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font
    p.alignment = align


def _add_accent_bar(slide, left: float, top: float, width: float = 2.0) -> None:
    bar = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = APG_GREEN
    bar.line.fill.background()


# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------

def _build_title_slide(prs: Presentation, company: str, session_number: int,
                        session_date: str, sessions_completed: int) -> None:
    slide = _blank_slide(prs)
    _set_bg(slide, DARK)
    _add_logo(slide, width=1.5, top=0.5)
    _add_textbox(slide, 0.8, 1.8, 11, 1.2, company, size=52, bold=True, color=WHITE)
    _add_textbox(slide, 0.8, 3.1, 11, 0.8,
                 f"Follow-Up Questions: Session {session_number}",
                 size=28, color=APG_GREEN)
    label = f"Audit Discovery  |  {session_date}  |  {sessions_completed} session{'s' if sessions_completed != 1 else ''} complete"
    _add_textbox(slide, 0.8, 4.0, 11, 0.5, label, size=15, color=MED_GREY)
    _add_accent_bar(slide, 0.8, 4.8, 3.0)
    _add_textbox(slide, 0.8, 5.1, 11, 0.5, "Bosar Agency", size=13, color=MED_GREY)


def _build_recap_slide(prs: Presentation, recap: list[dict]) -> None:
    if not recap:
        return
    slide = _blank_slide(prs)
    _set_bg(slide, WHITE)
    _add_logo(slide)
    _add_textbox(slide, 0.8, 0.4, 10, 0.6, "What We Covered Last Session",
                 size=28, bold=True, color=DARK)
    _add_accent_bar(slide, 0.8, 1.0)

    box = slide.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.5), Inches(5.5))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(recap):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(8)
        r1 = p.add_run()
        r1.text = f"{item.get('label', '')}: "
        r1.font.size = Pt(17)
        r1.font.bold = True
        r1.font.color.rgb = DARK
        r1.font.name = "Calibri"
        r2 = p.add_run()
        r2.text = item.get("detail", "")
        r2.font.size = Pt(17)
        r2.font.color.rgb = MED_GREY
        r2.font.name = "Calibri"


def _build_question_slide(prs: Presentation, title: str, subtitle: str | None,
                            questions: list[dict], gate_items: list[str]) -> None:
    slide = _blank_slide(prs)
    _set_bg(slide, WHITE)
    _add_logo(slide)
    _add_textbox(slide, 0.8, 0.4, 10, 0.6, title, size=26, bold=True, color=DARK)
    _add_accent_bar(slide, 0.8, 1.0)

    if subtitle:
        _add_textbox(slide, 0.8, 1.12, 11, 0.38, subtitle, size=13, color=MED_GREY)
        q_top = 1.55
    else:
        q_top = 1.28

    gate_height = 0.30 + len(gate_items) * 0.26
    q_height = SLIDE_H_IN - q_top - gate_height - 0.28

    box = slide.shapes.add_textbox(Inches(0.8), Inches(q_top), Inches(11.5), Inches(q_height))
    tf = box.text_frame
    tf.word_wrap = True

    for i, q in enumerate(questions):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(8)
        p.space_after = Pt(2)

        r_num = p.add_run()
        r_num.text = f"{q.get('number', i + 1)}.  "
        r_num.font.size = Pt(16)
        r_num.font.bold = True
        r_num.font.color.rgb = APG_GREEN
        r_num.font.name = "Calibri"

        r_q = p.add_run()
        r_q.text = q.get("text", "")
        r_q.font.size = Pt(16)
        r_q.font.color.rgb = DARK
        r_q.font.name = "Calibri"

        ctx = q.get("context", "")
        if ctx:
            pc = tf.add_paragraph()
            pc.space_before = Pt(0)
            pc.space_after = Pt(4)
            rc = pc.add_run()
            rc.text = f"      {ctx}"
            rc.font.size = Pt(12)
            rc.font.italic = True
            rc.font.color.rgb = MED_GREY
            rc.font.name = "Calibri"

    gate_top = SLIDE_H_IN - gate_height - 0.15
    bg = slide.shapes.add_shape(1, Inches(0.5), Inches(gate_top), Inches(12.333), Inches(gate_height))
    bg.fill.solid()
    bg.fill.fore_color.rgb = LIGHT_BG
    bg.line.fill.background()

    gtf_box = slide.shapes.add_textbox(Inches(0.8), Inches(gate_top + 0.07), Inches(11.5), Inches(gate_height))
    gtf = gtf_box.text_frame
    gtf.word_wrap = True

    p = gtf.paragraphs[0]
    r = p.add_run()
    r.text = "WHAT WE NEED  "
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = APG_GREEN
    r.font.name = "Calibri"

    for j, item in enumerate(gate_items):
        if j == 0:
            r2 = p.add_run()
            r2.text = f"  {item}"
            r2.font.size = Pt(10)
            r2.font.color.rgb = MED_GREY
            r2.font.name = "Calibri"
        else:
            p2 = gtf.add_paragraph()
            p2.space_before = Pt(1)
            r2 = p2.add_run()
            r2.text = f"                      {item}"
            r2.font.size = Pt(10)
            r2.font.color.rgb = MED_GREY
            r2.font.name = "Calibri"


def _build_researched_slide(prs: Presentation, items: list[dict]) -> None:
    if not items:
        return
    slide = _blank_slide(prs)
    _set_bg(slide, WHITE)
    _add_logo(slide)
    _add_textbox(slide, 0.8, 0.4, 10, 0.6, "Already Researched",
                 size=26, bold=True, color=DARK)
    _add_accent_bar(slide, 0.8, 1.0)
    _add_textbox(slide, 0.8, 1.08, 11, 0.38,
                 "We looked these up ourselves. Let us know if anything needs correcting.",
                 size=13, color=MED_GREY)

    box = slide.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.5), Inches(5.5))
    tf = box.text_frame
    tf.word_wrap = True

    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(10)

        r1 = p.add_run()
        r1.text = f"{i + 1}.  {item.get('question', '')}"
        r1.font.size = Pt(15)
        r1.font.bold = True
        r1.font.color.rgb = DARK
        r1.font.name = "Calibri"

        pa = tf.add_paragraph()
        pa.space_before = Pt(2)
        ra = pa.add_run()
        ra.text = f"      {item.get('answer', '')}"
        ra.font.size = Pt(13)
        ra.font.color.rgb = MED_GREY
        ra.font.name = "Calibri"

        src = item.get("source", "")
        if src:
            ps = tf.add_paragraph()
            ps.space_before = Pt(1)
            rs = ps.add_run()
            rs.text = f"      Source: {src}"
            rs.font.size = Pt(11)
            rs.font.italic = True
            rs.font.color.rgb = MED_GREY
            rs.font.name = "Calibri"


def _build_closing_slide(prs: Presentation, contact_name: str) -> None:
    slide = _blank_slide(prs)
    _set_bg(slide, DARK)
    _add_logo(slide, width=1.5, top=0.5)
    _add_textbox(slide, 0.8, 2.2, 11, 1.0, "Next Steps", size=44, bold=True, color=WHITE)

    body = f"Review these questions before our next session"
    if contact_name:
        body = f"Review these questions, {contact_name}, and we'll work through them together next session."
    _add_textbox(slide, 0.8, 3.4, 11, 0.6, body, size=18, color=MED_GREY)
    _add_accent_bar(slide, 0.8, 4.4, 3.0)
    _add_textbox(slide, 0.8, 4.7, 11, 0.5,
                 "bohdan@bosar.agency  |  bosar.agency", size=14, color=MED_GREY)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate(data: dict, output_path: Path) -> None:
    prs = _new_prs()

    company   = data.get("company_name", "Client")
    contact   = data.get("contact_name", "")
    sess_num  = data.get("session_number", 1)
    sess_date = data.get("session_date", "")
    sess_done = data.get("sessions_completed", sess_num)
    recap     = data.get("session_recap", [])
    groups    = data.get("question_groups", [])
    researched = data.get("researched_questions", [])

    _build_title_slide(prs, company, sess_num, sess_date, sess_done)
    _build_recap_slide(prs, recap)

    for group in groups:
        questions   = group.get("questions", [])
        gate_items  = group.get("gate_items", [])
        title       = group.get("title", "Questions")
        subtitle    = group.get("subtitle", "")

        chunks = [questions[i:i + MAX_QUESTIONS_PER_SLIDE]
                  for i in range(0, len(questions), MAX_QUESTIONS_PER_SLIDE)]
        for idx, chunk in enumerate(chunks):
            slide_title = title if idx == 0 else f"{title} (continued)"
            slide_subtitle = subtitle if idx == 0 else None
            _build_question_slide(prs, slide_title, slide_subtitle, chunk, gate_items)

    _build_researched_slide(prs, researched)
    _build_closing_slide(prs, contact)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    print(f"Saved: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate follow-up questions PPTX for an audit session.")
    parser.add_argument("--client-slug",    required=True,  help="Client slug (e.g. acme-trades)")
    parser.add_argument("--session",        required=True,  type=int, help="Session number")
    parser.add_argument("--questions-json", required=True,  help="Path to questions-input.json")
    parser.add_argument("--output-dir",     required=False, help="Override output directory")
    args = parser.parse_args()

    questions_path = Path(args.questions_json)
    if not questions_path.exists():
        print(f"Error: questions-json not found: {questions_path}", file=sys.stderr)
        sys.exit(1)

    with open(questions_path) as f:
        data = json.load(f)

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        sessions_dir = _paths.get_audit_sessions_dir(args.client_slug)
        session_date = data.get("session_date", "")
        label = data.get("session_label", "")
        if not label:
            groups = data.get("session_recap", [])
            label = groups[0].get("label", "").lower().replace(" ", "-") if groups else "session"
        label = "".join(c if c.isalnum() or c == "-" else "-" for c in label).strip("-")
        folder_name = f"{session_date}-{label}" if session_date else f"session-{args.session}"
        output_dir = sessions_dir / folder_name

    output_path = output_dir / "follow-up-questions.pptx"
    generate(data, output_path)


if __name__ == "__main__":
    main()
