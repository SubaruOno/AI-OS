#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""
generate.py, APG HTML deliverable generator.

Reads clients/{slug}/03-audit/data/ domain files and generates:
  - 1-client-website.html, Client-facing site with progressive session unlock
  - 2-process-map.html, HTML/CSS zone-based current-state process map
  - 3-findings.html, "What We Discussed" session summary with pain points and optimisations
  - 4-waste.html, "Hidden Costs", time and cost opportunity breakdown
  - 5-blueprint.html, AI Implementation Blueprint: initiative cards, priority matrix, phased roadmap

Usage:
  python3 generate.py --client-slug {slug} --output process-map|findings|waste|client-website|blueprint|handoff-zip|all

  --output all generates: process-map, findings, waste, blueprint, client-website

Output files written to: clients/{slug}/03-audit/deliverables/
"""

import argparse
import json
import math
import posixpath
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from html import escape


# ─── Design tokens ────────────────────────────────────────────────────────────

APG_LOGO_URL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGcAAABmCAYAAADWHY9cAAAIoklEQVR4nNWd+3HbRhDGV5z8H3QQpgLTFYSpIEoFoCuQXAHgCqRUIKYCJRVIqYBMBaArIFPBZY46cCCKJPbx7QHcGYzHNgku7od77H73uAkh0ABWENEtEX0iomn6e2sbIvqXiNZE9JrBj1m6PqW/x2uX/PiefIi+5LcIJ+O1CCG8BL41IYSnEMIU7Mc8hPAcQtgO7MfFK9cPzdMDWuwBUDgz4ctxyrJB8v6BIj0MyppUwBpf7sB+zK8ZTny7VsHHSqEvyBeka9U1wpkCmjEUIC8wrd17wbnZE8LbKo2AvG1BRH9e+P+n9Blv+9VjZDlB35CIqkxgoi2JqKRhwUR7PgoHIIauOTFmaSi/LY5qUE4w3Rfly5jhSAvlLyL6OwV5RSc4/SWB1gDSgHlNfrweBad3Qj+wzRt4EMC1F0asUCs65xeHIfG9IFh9HOtoLTrGsaXgnvfBz1YpDuP4MWMC2grumRXOivmmalI+Q4Jpr1vmvWHBKWq01rbRffZtBB3tOvUNMblJwv6R05/EPhNiKDgcMJtU0DQgoLUSTGuXYqrWpAOZs4asOX0WZQCLLY2ArGCIWXOi9HB1cBCayJKIvg4Epq392eyHjL9VgO5RKr4Xm5rfmM0SwscYa1ES69YJ6nooOLsM1b0gohdlaqjo9HcWQDPmb50KgjdpUPEHtwaimrU188GKAcBwc3HkPBKLtfc+pbeeWAMHYJzDCdJqxX0LB11Iqgd5yCBNiuGyBKGc1MlWqGQWIxLsokyeVbA794ZUjpF8w9TgC0cwUkCxPDztZHmfcqQtkCdF87MFASoUYFbKXFw5MJizimqfI1JAkkzyOUBaMIWwBnMA5QLT2rsm/7g5O2USQIWw0zwGZAVDQEC5wYTUb5+Ec6lDlwCKWVmJtYMEFBgCANKA2SbZZNG5looR3mEE1z5ILJw+kwCqFQ+GBEMGQHEmqNTqHl8kgt2h9kinD906AvLSYxaOfmwF+s1UAGh/z/aLDfONkgwOvACtFEKZByBpzCZp8vfBOrdJC4b5wfXAYMgBkAaMJFjfN21c+fXdKGIgQCuAPr8YGAy39sTf2Cc+OcrdP2SzWilRo/UYq2C3S36sjYJd33Psp4lNmJlihMhUp3T5UGAQgKxgWuM8yx5OLivSZEHN9wqwLz8pvxcFu2w2YdYKq45i0WOm6btT4FzuWIs1VqfvW8uC8yybCbOKWd4YhFA2BQGygEEBmjM+88YkjYC8Jsuh0/6NYUhfjWThlGgozQ1CG+FQ1kuPaRSAvJKYldPSx718II1DuLGGt1DWCAANIpSduGJSlWv7Z+sWZgAB0oBpBBPhJYAqZWYZDUgC5kPik1J62wpIC2aqzCQ0FwBVhsi/BgKSgHnXt2uzpqcAWcFIm9hL96gAS+gRgKRg3skyx5SlGnwX0LPiu+fe+toASAMG5UcXUGn145RDkuatLWTpcnLOwKJWPNyDQ79VZxLsPmhl5xyybkGCyi7XIxnxefoRzk0uzD0U1qT965HESl6Azs76vOQMGpBFj6lHkmVAAzJNx0UBQghl9cBg0IAuguHAQQBCgKF0aQJEJBgUoF4wXDjSPQa8wJByNIkGYwXEAhOvCTPlH/d2GYsFGoc17v47N2no2lMZ/EDWHmmAqVrd4A0GCagC+IEAZAXDBpQDDAJQBfTDAggFhgUoFxgLoMrBDw0gNJheQLlTN1JAlaMfEkBeYC7OQbcWxiql2hsHQJXwnltFwpEDSAPmGTGL1DJVtVvAUzCgyvBwSyCg0hDHaLLq78qj60hjLFgUIAsYAgKygCEloIdTcBagN94KCAGGDG/uFAhG68fhJZHWGk5foQWkEcpmPb5oAN05pGQkfhy2opSsz5HMW/Pe9LsZu1Bm8OOwFaVk3oA0LvAC1FyDUHbmWkqG1sQc9kn3I/AC1FyLUGbcSONRsnhKuw3WJq1pQazv2RjvZV3A1bUvyi0xd8w1Sm/bnzFJat5UZA1qrk0oMy473O8iTNwPDgiouUahrKcc2GtCOesTEdbu1Ce1HXDJoUUo22U4Q+5dmXPhIFaVVWmnPqnN0sIp1EtSKvuLdhGYtSzYa3AnzAWoi4FXlM1AgLRgkCvsOCvb3gY9zDjHskd/NRLBrgT6YekHG+5Qmjt60G6v4qHHrBSAyitbYXcIQkmgfEqCUU+hbCUA5CmUSQBJdnI8pG+kQ0sOoBxC2YoBSAOmcQTEOerlUL5dqg0IUE6hbHUBkDbtr5lDIdkbqA/QB8lAcj7MJUBWPQa1W2EZbAGmxo97AKCLK9ukc5G7N0MJZVZAZcBE/lI/pCPaY0C9K9s0BfMEVjAtgO4CNiUj9UO643wX0IdNOFAF47FfWZFh0+8F2I99TkwBaBQr28a0Xf7CyQ/3M9sQm74h7rlz8EOjx0Q/fmd+Fna68CRTwVjutQMD0gpl3Kx6tmPBEAUzlntYwLQWT+EdRc0Z21u/M97LCoaYeg5sV8WJc8G8OvRby4xC36Am2eNTA+i2c7gcwkoiejToMNa3mqPjwFRb6QasGkALEKDS2CwhBLvZmOEMBagE9BcIQHcZDqs9mHbr4pyAShAYK6AFs1nDTQIxRrHaXByNQChbCRKVHB1Gm745eyFuotU/+s5se8hwBg9HKLsTKJjaacsnr5s9Ibtp945epsBuk5rKWYqw74XNTtvMbpR+vKYpx5t0tX7MmbNlWvsZeX41Cg7yFFxr/1cM5If1EAtXOEMUzO7MwCS3H8gJ+wdDHzThlUWW/lZOPyjVGCiYaB6ngOQomB3jN3IB+uY1h9rriBbPgtkJ7h0/+9mwvqjPvgIOrjhrnufntAWDWrBECchnBfQF2I+2j9Hk+fiGHJc7Lp7aKiZPnPPjBeAHeoM/tyBUcs2FEwdf0nywYmA/skJpL/RQWmLzNNSN+aofO//+vaO/7DL5Ea94VFibO4u//1/6E61Jse1/kIBalALadb8AAAAASUVORK5CYII="
APG_FAVICON = f'<link rel="icon" type="image/png" href="{APG_LOGO_URL}">'
APG_COMPANY = "Bosar Agency"
APG_ADDRESS = "Cracow, Poland"
APG_EMAIL = "bohdan@bosar.agency"
APG_WEBSITE = "bosar.agency"

APG_LIME = "#2563eb"
APG_LIME_TEXT = "#1d4ed8"   # dark green for text, 7.1:1 contrast on white
APG_DARK = "#1a1a1a"
APG_GREY = "#64748b"
APG_LIGHT = "#f7f9fc"
APG_WHITE = "#ffffff"
APG_BORDER = "#e2e8f0"
STEP_COLORS = {
    "step": "#f7f9fc",
    "decision": "#fffbeb",
    "pain": "#fef2f2",
    "optimisation": "#166534",
    "automation": "#eff6ff",
}
STEP_BORDERS = {
    "step": "#e2e8f0",
    "decision": "#fcd34d",
    "pain": "#fca5a5",
    "optimisation": "#14532d",
    "automation": "#93c5fd",
}
STAGE_ACCENT_DEFAULT = "#7DFF00"
SPRINT_PRICE_AUD: int = 15_000
"""Flat price per 2-week sprint. Used across stage cards, investment table, and future-sprints block."""

# ── Portal Design System v2 ────────────────────────────────────────────────
# Shared constants for the unified portal chrome (topbar, footer, typography).
# Used by all five deliverable generators so the nav/footer stay in sync.

_PORTAL_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900'
    '&family=Playfair+Display:wght@700;800;900'
    '&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
)

_PORTAL_TOPBAR_CSS = """/* ── Unified topbar ── */
.apg-topbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(247,249,252,0.94); backdrop-filter: blur(14px);
  border-bottom: 1px solid #e2e8f0; padding: 0 24px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
.apg-topbar__inner {
  max-width: 1200px; margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; height: 62px;
}
.apg-topbar__left { display: flex; align-items: center; gap: 14px; min-width: 0; }
.apg-topbar__logo { display: block; height: 30px; width: 30px; border-radius: 6px; flex-shrink: 0; }
.apg-topbar__brand { display: none; }
.apg-topbar__brand-sub { font-weight: 500; font-size: 12px; color: #64748b; }
.apg-topbar__crumbs {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #64748b; min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.apg-topbar__crumbs a { color: #64748b; text-decoration: none; transition: color 120ms; }
.apg-topbar__crumbs a:hover { color: #059669; }
.apg-topbar__crumbs .sep { color: #d1d5db; }
.apg-topbar__crumbs .current { color: #0f1825; font-weight: 600; }
.apg-topbar__right { display: flex; align-items: center; gap: 10px; }
.apg-topbar__pill {
  display: inline-flex; align-items: center; gap: 5px;
  background: #f0fdf4; border: 1px solid #bbf7d0; color: #064E3B;
  font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
  padding: 4px 10px; border-radius: 999px; white-space: nowrap;
}
.apg-topbar__pill .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #059669; box-shadow: 0 0 0 2px rgba(5,150,105,0.18);
}
.apg-topbar__client { font-size: 12px; font-weight: 500; color: #64748b; white-space: nowrap; letter-spacing: -0.01em; }"""

_PORTAL_FOOTER_CSS = """/* ── Unified footer ── */
.apg-footer {
  background: #0f1825; color: rgba(255,255,255,0.6);
  padding: 28px 24px 32px; margin-top: 80px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
.apg-footer__inner {
  max-width: 1200px; margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between;
  gap: 24px; flex-wrap: wrap;
}
.apg-footer__brand { display: flex; align-items: center; gap: 10px; color: rgba(255,255,255,0.85); font-weight: 700; font-size: 13px; letter-spacing: -0.01em; }
.apg-footer__brand img { width: 22px; height: 22px; border-radius: 5px; }
.apg-footer__meta { font-size: 11px; letter-spacing: 0.05em; color: rgba(255,255,255,0.45); text-align: right; }
.apg-footer__meta strong { color: rgba(255,255,255,0.85); font-weight: 600; }
.apg-footer a { color: #34d399; text-decoration: none; }
.apg-footer a:hover { text-decoration: underline; }"""

_PORTAL_TYPOGRAPHY_CSS = """/* ── Typography overrides ── */
.hero h1, .findings-title, .bp-hero h1 {
  font-family: 'Playfair Display', Georgia, serif !important;
  font-weight: 800 !important; letter-spacing: -0.035em !important; line-height: 1.02 !important;
}
.section-heading, h2.section-heading {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  font-weight: 800 !important; letter-spacing: -0.025em !important; color: #0f1825 !important;
}
.section-label, .hero-apg-label, .findings-eyebrow, .bp-eyebrow {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important;
  letter-spacing: 0.16em !important; color: #064E3B !important;
  background: transparent !important; padding: 0 !important;
}
.stat-figure, .apg-big-stat {
  font-family: 'Playfair Display', Georgia, serif !important;
  font-weight: 800 !important; letter-spacing: -0.035em !important;
}
::selection { background: rgba(16,185,129,0.22); color: #0f1825; }"""


def _portal_status_pill(sections: dict) -> str:
    """Derive short status pill text from sections dict."""
    if not sections:
        return "In progress"
    if sections.get("prototype") or sections.get("priority_matrix"):
        return "Audit complete"
    if sections.get("blueprint") or sections.get("transformation"):
        return "Blueprint ready"
    if sections.get("waste") or sections.get("findings"):
        return "In progress"
    return "In progress"


def _portal_topbar_html(page_name: str, company: str, status_text: str, is_home: bool = False, is_demo: bool = False) -> str:
    """Return the unified <nav class='apg-topbar'> HTML block."""
    from html import escape as _esc
    logo = APG_LOGO_URL
    pill = f'<span class="apg-topbar__pill"><span class="dot"></span>{_esc(status_text)}</span>'
    client = f'<span class="apg-topbar__client">{_esc(company)}</span>'
    if is_home:
        crumbs = f'<span class="apg-topbar__crumbs"><span class="current">{_esc(page_name)}</span></span>'
    else:
        crumbs = (
            f'<span class="apg-topbar__crumbs">'
            f'<a href="1-client-website.html">Audit overview</a>'
            f'<span class="sep">/</span>'
            f'<span class="current">{_esc(page_name)}</span>'
            f'</span>'
        )
    demo_notice = (
        '<span class="apg-topbar__demo">Example data only, for demonstration purposes</span>'
        if is_demo else ''
    )
    demo_css = (
        '<style>.apg-topbar__demo{font-size:11px;font-weight:600;color:#92400e;'
        'background:#fef3c7;border:1px solid #fde68a;border-radius:999px;'
        'padding:3px 10px;letter-spacing:0.02em;white-space:nowrap;}</style>'
        if is_demo else ''
    )
    return f"""{demo_css}<nav class="apg-topbar">
  <div class="apg-topbar__inner">
    <div class="apg-topbar__left">
      <a href="1-client-website.html" style="display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit">
        <img class="apg-topbar__logo" src="{logo}" alt="Bosar">
        <span class="apg-topbar__brand">Bosar Agency <span class="apg-topbar__brand-sub">&middot; Audit portal</span></span>
      </a>
      <span style="color:#d1d5db">/</span>
      {crumbs}
    </div>
    {demo_notice}
    <div class="apg-topbar__right">
      {pill}
      {client}
    </div>
  </div>
</nav>"""


def _portal_footer_html() -> str:
    """Return the unified <footer class='apg-footer'> HTML block."""
    return f"""<footer class="apg-footer">
  <div class="apg-footer__inner">
    <div class="apg-footer__brand">
      <img src="{APG_LOGO_URL}" alt="">
      Bosar Agency
    </div>
    <div class="apg-footer__meta">
      AI strategy audit &middot; prepared by <strong>Bosar Agency</strong><br>
      <a href="https://bosar.agency">bosar.agency</a>
    </div>
  </div>
</footer>"""

# ── End portal design system constants ────────────────────────────────────


def _sprint_payback_months(milestone_value_aud: float) -> float:
    """Months to pay back one sprint at SPRINT_PRICE_AUD given the stage's annual milestone value."""
    if not milestone_value_aud:
        return 0.0
    return round(SPRINT_PRICE_AUD * 12 / milestone_value_aud, 1)


def _classify_stage(stage: dict) -> str:
    """Return 'core' if this stage pays back within 12 months at SPRINT_PRICE_AUD, else 'future'."""
    mv = stage.get("milestone_value_aud") or 0
    if not mv:
        return "future"
    return "core" if _sprint_payback_months(mv) <= 12 else "future"


def _waste_counts_in_total(w: dict) -> bool:
    """Whether a waste item contributes to headline / breakdown totals.

    Opt-in overlap guard: an item is excluded only when it carries an explicit
    `overlap_parent_waste_id`, meaning it is a contributing sub-strategy already
    captured inside an aggregate parent item, counting both double-counts.
    Items without the field always count, so clients with no overlap
    annotations are unaffected.
    """
    return not w.get("overlap_parent_waste_id")


def _build_stage_lookups(ssad: dict) -> tuple:
    """Build stage label and subtitle dicts from audit data processes[].name/description."""
    labels = {}
    subtitles = {}
    for proc in ssad.get("processes", []):
        stage = proc["stage"]
        labels[stage] = proc.get("name") or stage.replace("_", " ").title()
        if proc.get("description"):
            subtitles[stage] = proc["description"]
    return labels, subtitles


def _stage_label(stage: str, labels: dict) -> str:
    """Look up a stage display name, falling back to title-cased key."""
    return labels.get(stage, stage.replace("_", " ").title())

# ─── Shared constants for change overlays ────────────────────────────────────

CHANGE_BADGE = {
    "automate":    ("AUTOMATED",   "#10B981", "#166534"),
    "replace":     ("REPLACED",    "#3B82F6", "#DBEAFE"),
    "eliminate":   ("ELIMINATED",  "#EF4444", "#FEE2E2"),
    "consolidate": ("CONSOLIDATED","#8B5CF6", "#EDE9FE"),
}

VALUE_TYPE_COLOR = {
    "time_saving": "#10B981",
    "productivity_enhancement": "#3B82F6",
    "both": "#8B5CF6",
}




def _stat_box(value: str, label: str) -> str:
    """Render a single stat box."""
    return f"""<div class="stat-box">
               <div class="stat-val">{value}</div>
               <div class="stat-label">{label}</div>
               </div>"""


def _render_current_step_simple(step: dict, changes: list) -> str:
    """Render a step card for the current-state process map."""
    stype = step.get("type", "step")
    desc = escape(step.get("description", ""))
    is_changed = bool(changes)
    opacity_style = "opacity:0.5;" if is_changed else ""
    bg = STEP_COLORS.get(stype, "#fff")
    border = STEP_BORDERS.get(stype, "#E5E7EB")
    return f"""<div style="background:{bg};border:1.5px solid {border};border-radius:8px;
               padding:10px 12px;margin-bottom:6px;font-size:12px;{opacity_style}">
               {desc}</div>"""


def _render_proposed_step_simple(step: dict, changes: list) -> str:
    """Render a step card for the proposed-state process map with change overlays."""
    desc = escape(step.get("description", ""))
    if not changes:
        return f"""<div style="background:#F9FAFB;border:1.5px solid #E5E7EB;border-radius:8px;
                   padding:10px 12px;margin-bottom:6px;font-size:12px;opacity:0.55;">
                   {desc}</div>"""
    ch = changes[0]
    ctype = ch.get("change_type", "automate")
    badge_label, border_color, bg_color = CHANGE_BADGE.get(ctype, ("CHANGED", "#6B7280", "#F3F4F6"))
    tools = ch.get("proposed_tools", [])
    tool_html = ""
    if tools:
        pills = "".join(f'<span style="background:#E0F2FE;color:#0369A1;border-radius:4px;padding:1px 6px;font-size:10px;margin-right:3px">{escape(t)}</span>' for t in tools)
        tool_html = f'<div style="margin-top:5px">{pills}</div>'
    merged_desc = ch.get("proposed_step_description", "")
    display_desc = escape(merged_desc) if merged_desc else desc
    eliminate_style = "opacity:0.35;text-decoration:line-through;" if ctype == "eliminate" else ""
    return f"""<div style="background:{bg_color};border:2px solid {border_color};border-radius:8px;
               padding:10px 12px;margin-bottom:6px;font-size:12px;{eliminate_style}position:relative">
               <span style="position:absolute;top:6px;right:8px;background:{border_color};color:#fff;
                 font-size:9px;font-weight:700;padding:1px 5px;border-radius:3px">{badge_label}</span>
               <div style="padding-right:90px">{display_desc}</div>
               {tool_html}
               </div>"""


def _build_change_lookup(proposed_changes: list) -> dict:
    """Build step_id → list of change dicts lookup."""
    change_by_step: dict = {}
    for ch in proposed_changes:
        for sid in ch.get("affected_step_ids", []):
            change_by_step.setdefault(sid, []).append(ch)
    return change_by_step


def _render_side_by_side_maps(processes: list, change_by_step: dict) -> str:
    """Render side-by-side current vs proposed process map zones."""
    zones_html = ""
    for proc in processes:
        stage = proc.get("stage", "")
        stage_label = proc.get("name") or stage.replace("_", " ").title()
        accent = STAGE_ACCENT_DEFAULT
        steps = [s for s in proc.get("steps", []) if not s.get("branch_only", False)]
        if not steps:
            continue
        current_col = ""
        proposed_col = ""
        for step in steps:
            sid = step.get("step_id", "")
            changes = change_by_step.get(sid, [])
            current_col += _render_current_step_simple(step, changes)
            proposed_col += _render_proposed_step_simple(step, changes)
        zones_html += f"""
        <div style="margin-bottom:32px">
          <div style="border-left:4px solid {accent};padding-left:12px;margin-bottom:12px">
            <span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:{accent}">{escape(stage_label)}</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
            <div>
              <div style="font-size:11px;font-weight:600;text-transform:uppercase;color:{APG_GREY};margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #E5E7EB">Current State</div>
              {current_col}
            </div>
            <div>
              <div style="font-size:11px;font-weight:600;text-transform:uppercase;color:{APG_GREY};margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #E5E7EB">Proposed State</div>
              {proposed_col}
            </div>
          </div>
        </div>"""
    return zones_html or f'<p style="color:{APG_GREY};font-style:italic">No process data available.</p>'


def _value_color(value: float, sorted_values: list) -> str:
    """Return a color based on where value falls in the distribution."""
    n = len(sorted_values)
    if n == 0:
        return "#94A3B8"
    rank = sum(1 for v in sorted_values if v <= value)
    pct = rank / n
    if pct >= 0.8:
        return "#059669"   # top tier, deep green
    elif pct >= 0.5:
        return "#10B981"   # mid-high, green
    elif pct >= 0.2:
        return "#F59E0B"   # mid-low, amber
    else:
        return "#94A3B8"   # low, slate

# ─── Utilities ────────────────────────────────────────────────────────────────

def _get_clients_dir():
    """Return the configured clients directory (lazy import to keep startup fast)."""
    import sys as _sys
    _reader_path = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts")
    if _reader_path not in _sys.path:
        _sys.path.insert(0, _reader_path)
    from _paths import get_clients_dir
    return get_clients_dir()


def _has_bpmn_processes(ssad: dict) -> bool:
    """True if any process in audit data has BPMN lanes + sequence_flows.

    Triggers the BPMN-based process map renderer instead of the legacy zone renderer.
    """
    processes = ssad.get("processes") or ssad.get("extraction", {}).get("processes") or []
    return any(p.get("lanes") and p.get("sequence_flows") for p in processes)


def _get_client_dir(slug: str) -> Path:
    """Return the resolved client folder, respecting client_paths overrides in config.yaml."""
    import sys as _sys
    _reader_path = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts")
    if _reader_path not in _sys.path:
        _sys.path.insert(0, _reader_path)
    from _paths import get_client_path
    return get_client_path(slug)


def _get_client_subdir(slug: str, name: str) -> Path:
    """Return a client subdirectory by canonical name, with legacy-name fallback."""
    import sys as _sys
    _reader_path = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts")
    if _reader_path not in _sys.path:
        _sys.path.insert(0, _reader_path)
    from _paths import get_client_subdir
    return get_client_subdir(slug, name)


def load_audit_data(client_slug: str) -> dict:
    """Load audit data for a client. Supports v2, v3, and v4 formats."""
    import sys as _sys
    _reader_path = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts")
    if _reader_path not in _sys.path:
        _sys.path.insert(0, _reader_path)
    from audit_reader import load_all
    try:
        return load_all(client_slug)
    except FileNotFoundError:
        print(f"Error: audit data not found for client '{client_slug}'", file=sys.stderr)
        sys.exit(2)


def load_client_sections(client_slug: str) -> dict:
    """Load section unlock flags from clients.json for the given client slug."""
    clients_path = _get_clients_dir() / "clients.json"
    default_sections = {
        "process_map": False, "findings": False, "waste": False,
        "priority_matrix": False, "transformation": False, "prototype": False,
    }
    if not clients_path.exists():
        return default_sections
    with open(clients_path) as f:
        clients = json.load(f)
    for key, entry in clients.items():
        if entry.get("slug") == client_slug or key == client_slug:
            merged = {**default_sections, **entry.get("sections", {})}
            # Pass prototype_url through sections so JS can read it
            if entry.get("prototype_url"):
                merged["prototype_url"] = entry["prototype_url"]
            # Pass demo flag through so generators can show the demo notice
            if entry.get("is_demo"):
                merged["is_demo"] = True
            return merged
    return default_sections


def ensure_deliverables_dir(client_slug: str) -> Path:
    client_dir = _get_client_dir(client_slug)
    # Prefer 03-audit/deliverables/ if the 03-audit/ folder exists
    if (client_dir / "03-audit").exists():
        d = client_dir / "03-audit" / "deliverables"
    else:
        d = client_dir / "deliverables"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fmt_aud(amount) -> str:
    if amount is None:
        return "N/A"
    if amount < 0:
        return f"-${abs(amount):,.0f}"
    return f"${amount:,.0f}"


# R&D Tax Incentive, refundable offset on eligible custom-build (R&D) expenditure.
# Conservative 43.5% offset (25% company tax rate + 18.5% premium); verbal headline is
# "up to 48.5%". Effective cost retained by the client after the offset = price * (1 - 0.435).
# Source of truth: apg-sales-plugin/context/pricing/apg-pricing.md
RND_OFFSET = 0.435
RND_RETAINED = 1.0 - RND_OFFSET


def rnd_effective(amount) -> str:
    """Single-figure effective cost after the ~43.5% R&D offset."""
    try:
        return fmt_aud(float(amount) * RND_RETAINED)
    except (TypeError, ValueError):
        return ""


def rnd_effective_range(low, high) -> str:
    """Effective build-cost range after the ~43.5% R&D offset, e.g. '$3,673-$4,520'."""
    try:
        return f"{fmt_aud(float(low) * RND_RETAINED)}-{fmt_aud(float(high) * RND_RETAINED)}"
    except (TypeError, ValueError):
        return ""


def _safe_numeric(value, fallback=0):
    """
    Return a numeric value safely.

    Some fields (e.g. plugin_assessment.annual_saving_aud) are stored as a nested
    calculation dict with a same-named numeric sub-key, a known data quality issue
    in older audit-data.json files. This helper unwraps that pattern and returns the
    numeric value, or fallback if not resolvable.
    """
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        # Try same-name sub-key first (e.g. {"annual_saving_aud": 2880, ...})
        for k, v in value.items():
            if isinstance(v, (int, float)):
                return v
    return fallback


def _vb_formula_lines(entry) -> list:
    """Return human-readable formula strings for a single proposed_change value object."""
    lines = []
    v = entry.get("value") or {}
    ts = v.get("time_saving") or {}
    pe = v.get("productivity_enhancement") or {}
    rr = v.get("risk_reduction") or {}
    ce = v.get("customer_experience") or {}
    cs = v.get("cost_saving") or {}
    if ts.get("formula"):
        lines.append(ts["formula"])
    elif ts.get("annual_saving_aud"):
        hrs = ts.get("hours_saved_per_week", 0) or 0
        rate = ts.get("hourly_rate_aud", 0) or 0
        ann = ts.get("annual_saving_aud", 0) or 0
        lines.append(f"{hrs} hrs/wk \u00d7 ${rate}/hr \u00d7 52 wks = {fmt_aud(ann)}/yr")
    if pe.get("formula"):
        lines.append(pe["formula"])
    elif pe.get("estimated_annual_value_aud"):
        ann = pe.get("estimated_annual_value_aud", 0) or 0
        lines.append(f"Productivity gain: {fmt_aud(ann)}/yr")
    if rr.get("formula"):
        lines.append(rr["formula"])
    elif rr.get("annual_value_aud"):
        lines.append(f"Risk reduction: {fmt_aud(rr['annual_value_aud'])}/yr")
    if ce.get("formula"):
        lines.append(ce["formula"])
    elif ce.get("annual_value_aud") or ce.get("revenue_impact_aud"):
        ann = ce.get("annual_value_aud") or ce.get("revenue_impact_aud") or 0
        lines.append(f"Customer experience: {fmt_aud(ann)}/yr")
    if cs.get("formula"):
        lines.append(cs["formula"])
    elif cs.get("annual_value_aud"):
        lines.append(f"Cost saving: {fmt_aud(cs['annual_value_aud'])}/yr")
    return lines


def _vb_evidence(entry) -> list:
    """Return [{excerpt, url, session}] from proposed_change.modal_content.meeting_references."""
    results = []
    for ref in (entry.get("modal_content") or {}).get("meeting_references") or []:
        excerpt = (ref.get("transcript_excerpt") or "").strip()
        if excerpt:
            results.append({
                "excerpt": excerpt,
                "url": ref.get("fathom_url", ""),
                "session": ref.get("session", ""),
            })
    return results


def confidence_badge(conf: str) -> str:
    colors = {"HIGH": "#10B981", "MEDIUM": "#F59E0B", "LOW": "#EF4444"}
    c = colors.get(conf, APG_GREY)
    return f'<span style="background:{c};color:#fff;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600">{conf}</span>'


def pricing_source_badge(source_type: str) -> str:
    """Render a badge indicating where pricing data was sourced from."""
    badges = {
        "official": ("#ffffff", "#166534", "OFFICIAL"),
        "aggregator": ("#3B82F6", "#DBEAFE", "AGGREGATOR"),
        "blog": ("#F59E0B", "#FEF3C7", "BLOG"),
        "estimated": ("#EF4444", "#FEE2E2", "ESTIMATED"),
        "training_knowledge": ("#EF4444", "#FEE2E2", "ESTIMATED"),
    }
    if not source_type or source_type not in badges:
        return ""
    color, bg, label = badges[source_type]
    return f'<span style="background:{bg};color:{color};padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600;margin-left:6px">{label}</span>'


def hidden_costs_html(hidden_costs: list) -> str:
    """Render a collapsible hidden costs section if any exist."""
    if not hidden_costs:
        return ""
    likelihood_colors = {
        "likely": ("#EF4444", "#FEE2E2"),
        "possible": ("#F59E0B", "#FEF3C7"),
        "unlikely": ("#64748B", "#F1F5F9"),
    }
    items = ""
    for hc in hidden_costs:
        hc_type = escape(str(hc.get("type", "")).replace("_", " ").title())
        desc = escape(str(hc.get("description", "")))
        annual = hc.get("estimated_annual_aud")
        annual_str = f"${annual:,.0f}/yr" if annual else "-"
        trigger = escape(str(hc.get("trigger", "")))
        lh = hc.get("likelihood", "possible")
        lh_color, lh_bg = likelihood_colors.get(lh, ("#64748B", "#F1F5F9"))
        lh_badge = f'<span style="background:{lh_bg};color:{lh_color};padding:1px 5px;border-radius:3px;font-size:9px;font-weight:600;text-transform:uppercase">{lh}</span>'
        items += f"""<div class="so-hc-item">
            <div class="so-hc-row"><span class="so-hc-type">{hc_type}</span> {lh_badge} <span class="so-hc-cost">{annual_str}</span></div>
            <div class="so-hc-desc">{desc}</div>
            {"<div class='so-hc-trigger'>Trigger: " + trigger + "</div>" if trigger else ""}
        </div>"""
    return f"""<details class="so-hidden-costs">
        <summary>Hidden Costs ({len(hidden_costs)} identified)</summary>
        <div class="so-hc-body">{items}</div>
    </details>"""


def base_css() -> str:
    return f"""
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: {APG_DARK}; background: {APG_LIGHT}; font-size: 15px; line-height: 1.5; }}
    .apg-header {{ background: {APG_DARK}; color: #fff; padding: 20px 32px;
                   display: flex; align-items: center; gap: 16px;
                   border-bottom: 3px solid #7DFF00; }}
    .apg-header .logo {{ font-size: 20px; font-weight: 800; color: #ffffff; }}
    .apg-header .subtitle {{ font-size: 13px; color: #9CA3AF; margin-top: 2px; }}
    .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 24px; }}
    h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 6px; }}
    h2 {{ font-size: 20px; font-weight: 700; margin: 24px 0 12px; color: {APG_DARK}; }}
    h3 {{ font-size: 16px; font-weight: 600; margin: 16px 0 8px; }}
    .meta {{ font-size: 13px; color: {APG_GREY}; margin-bottom: 20px; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
               font-size: 12px; font-weight: 600; }}
    .card {{ background: #fff; border: 1px solid {APG_BORDER}; border-radius: 10px;
              padding: 20px; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ background: {APG_DARK}; color: #fff; padding: 10px 12px; text-align: left;
          font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
    td {{ padding: 9px 12px; border-bottom: 1px solid #F3F4F6; vertical-align: top; }}
    tr:hover td {{ background: {APG_LIGHT}; }}
    .highlight {{ color: #166534; font-weight: 700; }}
    .warning {{ background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 6px;
                padding: 10px 14px; font-size: 13px; margin: 12px 0; }}
    blockquote {{ border-left: 3px solid #7DFF00; padding: 8px 16px;
                  background: #166534; font-style: italic; font-size: 13px;
                  color: #ffffff; margin: 10px 0; border-radius: 0 6px 6px 0; }}
    @media (max-width: 768px) {{
        .container {{ padding: 16px; }}
        table {{ font-size: 12px; }}
        th, td {{ padding: 8px; }}
    }}
    """


# ─── Transcript Helpers ───────────────────────────────────────────────────────

def _load_client_transcripts(client_dir: str, sessions: list) -> dict:
    """Returns {recording_id_str: [(seconds, speaker, text), ...]} for all sessions with transcripts."""
    result = {}
    meetings_dir = Path(client_dir) / "01-materials" / "meetings"
    if not meetings_dir.is_dir():
        meetings_dir = Path(client_dir) / "01-meetings"
    if not meetings_dir.is_dir():
        meetings_dir = Path(client_dir) / "meetings"
    if not meetings_dir.is_dir():
        return result
    for folder in meetings_dir.iterdir():
        if not folder.is_dir():
            continue
        meta_file = folder / "metadata.json"
        tx_file = folder / "transcript.txt"
        if not (meta_file.exists() and tx_file.exists()):
            continue
        try:
            meta = json.loads(meta_file.read_text())
            mid = str(meta.get("recording_id", ""))
        except Exception:
            continue
        if not mid:
            continue
        lines = []
        for line in tx_file.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\[(\d+):(\d+)\]\s+(.+?):\s+(.+)$", line.strip())
            if m:
                mins, secs, speaker, text = m.groups()
                lines.append((int(mins) * 60 + int(secs), speaker.strip(), text.strip()))
        result[mid] = lines
    return result


def _extract_transcript_window(transcripts: dict, meeting_id: str, ts: int,
                                before: int = 2, after: int = 6,
                                hint_text: str = "") -> str:
    """Extract a dialogue window anchored on the best keyword match for hint_text.
    Falls back to timestamp-based lookup if no keywords match."""
    lines = transcripts.get(str(meeting_id), [])
    if not lines:
        return ""

    anchor_idx = None

    # Primary: pure keyword search on source_quote (no proximity bias)
    if hint_text:
        keywords = [w.lower() for w in re.split(r'\W+', hint_text) if len(w) > 4]
        if keywords:
            best_score = 0
            for i, (s, speaker, text) in enumerate(lines):
                text_lower = text.lower()
                kw_matches = sum(1 for kw in keywords if kw in text_lower)
                if kw_matches > best_score:
                    best_score = kw_matches
                    anchor_idx = i

    # Fallback: timestamp-based lookup
    if anchor_idx is None:
        anchor_idx = 0
        for i, (s, _, _) in enumerate(lines):
            if s <= ts:
                anchor_idx = i

    start = max(0, anchor_idx - before)
    end = min(len(lines), anchor_idx + after + 1)

    # Group consecutive same-speaker utterances into single blocks
    grouped = []
    for s, speaker, text in lines[start:end]:
        if grouped and grouped[-1][0] == speaker:
            grouped[-1] = (speaker, grouped[-1][1] + " " + text)
        else:
            grouped.append((speaker, text))
    parts = [f"{speaker}: {text}" for speaker, text in grouped]
    return "\n".join(parts)


def _find_best_transcript_match(transcripts: dict, meeting_id: str, ts: int,
                                  hint_text: str = "") -> int:
    """Return the timestamp (seconds) of the best keyword match for hint_text.
    Falls back to ts if no keywords match."""
    lines = transcripts.get(str(meeting_id), [])
    if not lines or not hint_text:
        return ts

    keywords = [w.lower() for w in re.split(r'\W+', hint_text) if len(w) > 4]
    if not keywords:
        return ts

    best_score = 0
    best_ts = ts
    for s, speaker, text in lines:
        text_lower = text.lower()
        kw_matches = sum(1 for kw in keywords if kw in text_lower)
        if kw_matches > best_score:
            best_score = kw_matches
            best_ts = s

    return best_ts if best_score > 0 else ts


# ─── Process Map Generator ─────────────────────────────────────────────────────

# Stage → zone number (1-based)




def _norm_quote(value) -> str:
    """Normalise source_quote, accepts str or list[str], returns a single str."""
    if isinstance(value, list):
        return " ".join(str(v) for v in value if v)
    return str(value) if value else ""


# ARCHIVED 2026-05-25: Replaced by BPMN 3-level hierarchy (generate_bpmn.py).
def _generate_process_map_legacy(ssad: dict) -> str:
    company = escape(ssad.get("company_name", "Client"))
    generated = datetime.now().strftime("%d %b %Y")
    sessions = ssad.get("sessions_completed", 0)
    # Stages come only from the audit data, no hardcoded fallback list
    stages = [p["stage"] for p in ssad.get("processes", [])]
    stage_labels, stage_subtitles = _build_stage_lookups(ssad)
    # Build zone numbers dynamically (1-based, sequential)
    stage_zone = {s: i + 1 for i, s in enumerate(stages)}

    # Build processes dict keyed by stage (full proc entry including flows)
    processes_by_stage_meta = {}
    for proc in ssad.get("processes", []):
        processes_by_stage_meta[proc["stage"]] = proc
    # Convenience alias, steps only (used in owner palette build etc.)
    processes_by_stage = {stage: meta.get("steps", []) for stage, meta in processes_by_stage_meta.items()}

    def render_email_refs(email_references: list) -> str:
        """Render email evidence links for a process step (green pill, hover-reveal)."""
        if not email_references:
            return ""
        links = []
        for ref in email_references:
            filename = ref.get("filename", "").strip()
            subject = ref.get("subject", "").strip()
            excerpt = ref.get("excerpt", "").strip()
            if not filename:
                continue
            label = subject or filename
            # Deliverable is in clients/{slug}/deliverables/ → emails are at ../emails/
            href = f"../emails/{escape(filename)}"
            title_attr = f' title="{escape(excerpt)}"' if excerpt else ""
            links.append(
                f'<a class="email-link" href="{href}" target="_blank" rel="noopener"{title_attr}>'
                f'&#128231; {escape(label)}'
                f'</a>'
            )
        if not links:
            return ""
        return f'<div class="email-refs">{"".join(links)}</div>'

    # Build lookup: fathom_meeting_id (recording_id) → fathom_url (calls/{call_id})
    _fathom_base_url: dict = {}
    for _s in ssad.get("sessions", []):
        _mid = _s.get("fathom_meeting_id", "")
        _furl = _s.get("fathom_url", "")
        if _mid and _furl:
            _fathom_base_url[str(_mid)] = _furl.rstrip("/")

    # Build lookup: session_number → session data (for synthesising refs when meeting_references is empty)
    _session_by_num: dict = {}
    for _s in ssad.get("sessions", []):
        _snum = _s.get("session_number")
        if _snum:
            _session_by_num[int(_snum)] = _s

    def _synthesise_meeting_ref(item: dict) -> list:
        """Return a meeting_references list synthesised from source_session + source_timestamp_seconds.
        Used when the explicit meeting_references array is empty but session data is available."""
        sess_num = item.get("source_session")
        ts = item.get("source_timestamp_seconds")
        if not sess_num or ts is None:
            return []
        sess = _session_by_num.get(int(sess_num))
        if not sess:
            return []
        mid = sess.get("fathom_meeting_id", "")
        if not mid:
            return []
        participants = sess.get("participants", [])
        def _participant_name(p):
            return p.get("name", "") if isinstance(p, dict) else str(p)
        guest = next((_participant_name(p) for p in participants if "Bosar" not in _participant_name(p)), "")
        label = f"Session {sess_num}" + (f" · {guest.split('(')[0].strip()}" if guest else "")
        return [{"meeting_id": str(mid), "timestamp_seconds": int(ts), "label": label}]

    # Load local transcript files for excerpt extraction
    _client_dir = _get_client_dir(ssad.get("client_slug", ""))
    _transcripts = _load_client_transcripts(str(_client_dir), ssad.get("sessions", []))

    def render_meeting_refs(meeting_references: list, source_quote: str = "") -> str:
        """Render expandable Fathom transcript dropdowns for a process step."""
        if not meeting_references:
            return ""
        items_html = []
        for ref in meeting_references:
            # Accept session_id ("S1", "S2", or plain int) as alias for meeting_id, 
            # older SU sub-agents emit session_id; resolve to fathom_meeting_id via sessions[].
            if not ref.get("meeting_id"):
                sid_raw = str(ref.get("session_id", "")).strip().lstrip("Ss")
                if sid_raw.isdigit():
                    sess = _session_by_num.get(int(sid_raw))
                    if sess and sess.get("fathom_meeting_id"):
                        mid = str(sess["fathom_meeting_id"])
                        participants = sess.get("participants", []) or []
                        def _pname(p):
                            return p.get("name", "") if isinstance(p, dict) else str(p)
                        guest = next((_pname(p) for p in participants if "Bosar" not in _pname(p)), "")
                        synthesised_label = f"Session {int(sid_raw)}" + (
                            f" · {guest.split('(')[0].strip()}" if guest else ""
                        )
                        ref = {**ref, "meeting_id": mid, "label": ref.get("label") or synthesised_label}
            meeting_id = ref.get("meeting_id", "")
            ts = ref.get("timestamp_seconds")
            label = ref.get("label", "")
            if not meeting_id or ts is None:
                continue
            minutes = int(ts) // 60
            seconds = int(ts) % 60
            time_str = f"{minutes}:{seconds:02d}"
            short_label = label or "Meeting ref"
            _base = _fathom_base_url.get(str(meeting_id), f"https://fathom.video/calls/{meeting_id}")
            resolved_ts = _find_best_transcript_match(_transcripts, meeting_id, int(ts), hint_text=source_quote)
            href = f"{_base}?t={resolved_ts}"

            # Excerpt priority: analyst-provided > transcript file window > step source_quote
            excerpt_text = (
                ref.get("transcript_excerpt", "").strip()
                or _extract_transcript_window(_transcripts, meeting_id, int(ts), hint_text=source_quote)
                or source_quote
            )
            if excerpt_text:
                lines_html = "".join(
                    f'<div class="tx-line">{escape(line)}</div>'
                    for line in excerpt_text.splitlines()
                    if line.strip()
                )
                excerpt_html = f'<div class="fathom-excerpt">{lines_html}</div>'
            else:
                excerpt_html = ""

            items_html.append(
                f'<details class="fathom-dropdown">'
                f'<summary><span class="ref-label">{escape(short_label)}</span>'
                f'<span class="ref-time">{time_str}</span></summary>'
                f'<div class="fathom-panel">'
                f'{excerpt_html}'
                f'<a class="fathom-open-btn" href="{href}" target="_blank" rel="noopener">'
                f'&#9654; Open Recording</a>'
                f'</div>'
                f'</details>'
            )
        if not items_html:
            return ""
        return f'<div class="fathom-refs">{"".join(items_html)}</div>'

    _materials_dir = _get_client_subdir(ssad.get("client_slug", ""), "01-materials/documents")

    def _build_materials_index() -> dict:
        """Build a basename -> relative_path index of all files under 01-materials/documents/."""
        import os
        materials_dir = _materials_dir
        index = {}
        if materials_dir.is_dir():
            for root, _dirs, files in os.walk(materials_dir):
                for fname in files:
                    full = Path(root) / fname
                    rel = str(full.relative_to(materials_dir)).replace("\\", "/")
                    index[fname.lower()] = rel
                    index[Path(fname).stem.lower()] = rel
        return index

    _materials_index = _build_materials_index()

    def resolve_material_href(doc_path: str):
        """
        Normalize a source_document path to a relative URL under materials/.

        Handles three formats found in audit-data.json:
          1. "loom-transcripts/foo.md"                   (correct relative path)
          2. "client-provided-materials/loom-transcripts/foo.md"  (prefixed)
          3. "batch-1-operations-workflows.md"            (bare filename, needs lookup)

        Returns a URL relative to the deliverables/ directory, e.g.:
          "../materials/loom-transcripts/foo.html"
        Returns None if the path cannot be resolved (e.g. points to meetings/ or missing file).
        """
        import os, re as _re
        if not doc_path:
            return None

        normalized = doc_path.replace("\\", "/")

        # Strip leading "client-provided-materials/" prefix
        normalized = _re.sub(r"^client-provided-materials/", "", normalized)

        # Paths that point into meetings/ are handled by Fathom links, skip
        if normalized.startswith("meetings/"):
            return None

        # Directory paths (e.g. "emails/2026-05-12-from-jeanne/"), resolve to email.txt inside
        if normalized.endswith("/"):
            candidate = normalized + "email.txt"
            if (_materials_dir / candidate).exists():
                return f"materials/{str(Path(candidate).with_suffix('.html'))}"
            else:
                return None

        suffix = Path(normalized).suffix.lower()
        name = Path(normalized).name

        # Bare filename (no directory component), resolve via index
        if "/" not in normalized:
            key = name.lower()
            if key in _materials_index:
                normalized = _materials_index[key]
            else:
                stem_key = Path(name).stem.lower()
                if stem_key in _materials_index:
                    normalized = _materials_index[stem_key]
                else:
                    return None
        else:
            # Path has a directory component, check disk first to avoid basename collisions
            # (multiple email folders each contain email.txt, colliding in the index).
            _mdir = _materials_dir
            if (_mdir / normalized).exists():
                pass  # direct path is valid, use as-is
            elif normalized.lower() in {v.lower() for v in _materials_index.values()}:
                pass  # matches an indexed value, use as-is
            else:
                key = name.lower()
                if key in _materials_index:
                    normalized = _materials_index[key]
                else:
                    stem_key = Path(name).stem.lower()
                    if stem_key in _materials_index:
                        normalized = _materials_index[stem_key]
                    else:
                        return None

        # .docx/.xlsx → prefer text-extracted equivalent, fall back to linking the file directly
        suffix = Path(normalized).suffix.lower()
        if suffix in {".docx", ".doc", ".xlsx", ".xls", ".xlsm"}:
            txt_name = Path(normalized).stem + ".txt"
            txt_key = txt_name.lower()
            if txt_key in _materials_index:
                normalized = _materials_index[txt_key]
                suffix = ".txt"
            # else: link to Office file directly (deploy copies it as-is)

        # Map convertible extensions to .html
        if suffix in {".md", ".txt"}:
            normalized = str(Path(normalized).with_suffix(".html"))

        # Deliverables and materials/ are siblings in the deploy staging dir
        return f"materials/{normalized}"

    def render_document_ref(doc_path: str, source_quote: str = "") -> str:
        """Render a linked pill for a source_document (loom transcript, email, admin doc, etc.)"""
        if not doc_path:
            return ""
        import os
        name = os.path.basename(doc_path)
        # Determine type icon + label from path structure
        dp_lower = doc_path.lower()
        if dp_lower.startswith("loom-transcripts/") or "loom" in dp_lower:
            icon = "&#127909;"  # 🎬
            prefix = "Loom"
            stem = os.path.splitext(name)[0]
            import re as _re
            stem = _re.sub(r'^[a-z]+-\d+-', '', stem)
            label = stem.replace("-", " ").replace("_", " ").title()
        elif dp_lower.startswith("emails/") or "email" in dp_lower:
            icon = "&#128231;"  # 📧
            prefix = "Email"
            parts = doc_path.replace("\\", "/").split("/")
            folder = parts[-2] if len(parts) >= 2 else name
            import re as _re
            folder = _re.sub(r'^\d{4}-\d{2}-\d{2}-', '', folder)
            label = folder.replace("-", " ").replace("_", " ").title()
        elif "batch-" in dp_lower or "admin-folder" in dp_lower or "analysis" in dp_lower:
            icon = "&#128196;"  # 📄
            prefix = "Document"
            stem = os.path.splitext(name)[0]
            import re as _re
            stem = _re.sub(r'^batch-\d+-', '', stem)
            label = stem.replace("-", " ").replace("_", " ").title()
        else:
            icon = "&#128196;"  # 📄
            prefix = "Source"
            label = os.path.splitext(name)[0].replace("-", " ").replace("_", " ").title()

        href = resolve_material_href(doc_path)

        quote_html = ""
        if source_quote:
            q = escape(source_quote[:200] + ("..." if len(source_quote) > 200 else ""))
            quote_html = f'<div class="fathom-excerpt"><div class="tx-line">{q}</div></div>'

        if href:
            action_html = (
                f'<a class="fathom-open-btn" href="{href}" target="_blank" rel="noopener">'
                f'&#128196; Open Document</a>'
            )
        else:
            action_html = '<span class="fathom-open-btn" style="opacity:.4;cursor:default;">&#128196; Available on request</span>'

        return (
            f'<div class="fathom-refs">'
            f'<details class="fathom-dropdown">'
            f'<summary>'
            f'<span class="ref-label">{icon} {escape(prefix)}: {escape(label)}</span>'
            f'</summary>'
            f'<div class="fathom-panel">'
            f'{quote_html}'
            f'{action_html}'
            f'</div>'
            f'</details>'
            f'</div>'
        )

    def _sources_to_render_inputs(item: dict) -> tuple:
        """Split canonical sources[] into (meeting_refs[], doc_entries[]).
        Each doc_entries entry is (document_path, quote).
        Fathom entries become meeting_refs dicts with meeting_id/timestamp/label/excerpt.
        Returns ([], []) if item has no sources[] array.
        """
        sources = item.get("sources") or []
        if not isinstance(sources, list) or not sources:
            return [], []
        m_refs = []
        d_entries = []
        seen_doc = set()
        for s in sources:
            if not isinstance(s, dict):
                continue
            kind = s.get("kind")
            quote = (s.get("quote") or "").strip()
            if kind == "fathom":
                sid = s.get("session_id")
                ts = s.get("timestamp_seconds")
                if sid is None or ts is None:
                    continue
                sess = _session_by_num.get(int(sid)) if isinstance(sid, (int, float)) else None
                mid = str(sess.get("fathom_meeting_id")) if sess and sess.get("fathom_meeting_id") else ""
                if not mid:
                    continue
                participants = (sess.get("participants") or []) if sess else []
                def _pn(p):
                    return p.get("name", "") if isinstance(p, dict) else str(p)
                guest = next((_pn(p) for p in participants if "Bosar" not in _pn(p)), "")
                lbl = f"Session {int(sid)}" + (f" · {guest.split('(')[0].strip()}" if guest else "")
                m_refs.append({
                    "meeting_id": mid,
                    "timestamp_seconds": int(ts),
                    "label": lbl,
                    "transcript_excerpt": quote,
                })
            elif kind == "document":
                doc = (s.get("document_path") or "").strip()
                if not doc or doc in seen_doc:
                    continue
                seen_doc.add(doc)
                d_entries.append((doc, quote))
        return m_refs, d_entries

    def render_step(step: dict, zn: int = 1, owner_color_map: dict = None) -> str:
        if owner_color_map is None:
            owner_color_map = {}
        stype = step.get("type", "step")
        desc = escape(step.get("description", ""))
        owner_raw = (step.get("owner") or "").strip()
        owner = escape(owner_raw)
        conf = step.get("confidence", "LOW")
        quote = escape(_norm_quote(step.get("source_quote", "")))
        session = step.get("source_session", "")
        speaker = escape(step.get("source_speaker") or "")
        hours = step.get("waste_hours_per_week") or 0
        meeting_refs = step.get("meeting_references") or []
        email_refs = step.get("email_references") or []

        # Map type to CSS class; standard steps get zone-tinted class
        if stype == "step":
            box_class = f"step step-z{zn}"
        else:
            box_class_map = {
                "decision": "decision-box",
                "pain": "pain-box",
                "optimisation": "opp-box",
                "automation": "auto-box",
            }
            box_class = box_class_map.get(stype, "step")

        # LOW confidence adds dashed border override
        low_conf_style = "border-style:dashed!important;" if conf == "LOW" else ""

        # Tooltip from source quote
        tooltip = ""
        if quote:
            source_info = f"Session {session}" if session else ""
            if speaker:
                source_info += f" · {speaker}"
            q_text = quote[:120] + ("..." if len(quote) > 120 else "")
            tooltip_text = f"{source_info}: {q_text}" if source_info else q_text
            tooltip = f'title="{tooltip_text}"'

        # Owner tag: use assigned color class from owner_color_map
        if owner_raw:
            tag_cls, _ = owner_color_map.get(owner_raw, ("person-tag", None))
            owner_html = f'<div class="box-body"><span class="person-tag {tag_cls}">{owner}</span></div>'
        else:
            owner_html = ""

        # Tool tags from tool_ids
        tool_ids = step.get("tool_ids") or []
        if tool_ids:
            tool_pills = "".join(f'<span class="step-tool-tag">{escape(t)}</span>' for t in tool_ids)
            tools_html = f'<div class="step-tools">{tool_pills}</div>'
        else:
            tools_html = ""

        sq = step.get("source_quote", "") or step.get("source_quotes", "")
        if isinstance(sq, list):
            sq = " ".join(sq)
        # Source traceability, prefer canonical sources[] when present, fall back to legacy fields.
        canon_meeting_refs, canon_doc_entries = _sources_to_render_inputs(step)
        if canon_meeting_refs or canon_doc_entries:
            meeting_refs_html = render_meeting_refs(canon_meeting_refs, sq)
            doc_ref_html = "".join(render_document_ref(dp, q or sq) for dp, q in canon_doc_entries)
        else:
            effective_meeting_refs = meeting_refs or _synthesise_meeting_ref(step)
            meeting_refs_html = render_meeting_refs(effective_meeting_refs, sq)
            doc_ref_html = render_document_ref(step.get("source_document") or "", sq)
        email_refs_html = render_email_refs(email_refs)

        # Metadata chips
        meta_parts = []
        if step.get("duration_minutes"):
            meta_parts.append(f"{step['duration_minutes']} min")
        if step.get("frequency"):
            meta_parts.append(escape(str(step["frequency"])))
        meta_html = (
            '<div class="step-meta">' +
            "".join(f'<span class="meta-chip">{p}</span>' for p in meta_parts) +
            '</div>'
        ) if meta_parts else ""

        # Inline source quote (full text) + session badge
        quote_html = ""
        if quote:
            session_badge = f'<span class="step-session">Session {session}</span>' if session else ""
            quote_html = f'<div class="step-quote">&ldquo;{quote}&rdquo;{session_badge}</div>'

        return f"""
        <div class="box {box_class} process-step" {tooltip}
             style="{low_conf_style}">
          <div class="box-title">{desc}</div>
          {owner_html}
          {tools_html}
          {meta_html}
          {quote_html}
          {meeting_refs_html}
          {doc_ref_html}
          {email_refs_html}
        </div>"""

    def render_parallel_group(step: dict, zn: int = 1) -> str:
        items = step.get("items") or []
        label = escape(step.get("description", ""))
        conf = step.get("confidence", "LOW")
        low_conf = "border-style:dashed!important;" if conf == "LOW" else ""

        chip_parts = []
        for item in items:
            # Guard: item may be a plain string if audit data was written incorrectly
            if isinstance(item, str):
                item = {"label": item}
            lbl = escape(item.get("label", ""))
            tool = item.get("tool", "") or ""
            owner = item.get("owner", "") or ""
            q = escape(_norm_quote(item.get("source_quote") or "").strip())
            title_attr = f' title="{q}"' if q else ""

            refs = item.get("meeting_references") or []
            link_html = ""
            if refs and refs[0].get("meeting_id") and refs[0].get("timestamp_seconds") is not None:
                _mid0 = str(refs[0]['meeting_id'])
                _base0 = _fathom_base_url.get(_mid0, f"https://fathom.video/calls/{_mid0}")
                _url = f"{_base0}?t={int(refs[0]['timestamp_seconds'])}"
                _item_quote = _norm_quote(item.get("source_quote") or "").strip()
                _chip_excerpt = f'<p class="chip-excerpt">{escape(_item_quote)}</p>' if _item_quote else ""
                link_html = (
                    f'<details class="chip-dropdown">'
                    f'<summary>▶ Recording</summary>'
                    f'<div class="chip-panel">'
                    f'{_chip_excerpt}'
                    f'<a class="chip-open-btn" href="{_url}" target="_blank" rel="noopener">Open Recording &#8599;</a>'
                    f'</div>'
                    f'</details>'
                )

            tool_html = f'<span class="chip-tool">{escape(tool)}</span>' if tool else ""
            owner_html = f'<span class="chip-owner person-tag">{escape(owner)}</span>' if owner else ""

            chip_parts.append(
                f'<div class="pg-chip"{title_attr}>'
                f'{lbl}{tool_html}{owner_html}{link_html}'
                f'</div>'
            )

        n = max(len(items), 1)
        crossbar_pct = round((n - 1) / n * 100, 1) if n > 1 else 0
        legs = "".join(
            f'<div class="pg-leg"><div class="v-line"></div></div>' for _ in range(n)
        )

        return f"""
        <div class="process-step" style="{low_conf}">
          <div class="pg-label">{label}</div>
          <div class="pg-row">{"".join(chip_parts)}</div>
          <div class="pg-merge">
            <div class="pg-legs">{legs}</div>
            <div class="pg-crossbar" style="width:{crossbar_pct}%"></div>
            <div class="pg-drop">
              <div class="v-line"></div>
              <div class="v-tip"></div>
            </div>
          </div>
        </div>"""

    # Build decision_nodes dict keyed by stage (list, consumed sequentially)
    # Build step_id → stage lookup so nodes are placed in the zone their anchor lives in
    _step_id_to_stage: dict = {}
    for proc in ssad.get("processes", []):
        for st in proc.get("steps", []):
            sid = st.get("step_id", "")
            if sid:
                _step_id_to_stage[sid] = proc["stage"]

    _decision_nodes_by_stage: dict = {}
    for dn in ssad.get("decision_nodes", []):
        anchor = (dn.get("after_step_id") or "").strip()
        # Use the anchor step's stage when available; fall back to node's own stage field
        s = _step_id_to_stage.get(anchor) or dn.get("stage", "")
        _decision_nodes_by_stage.setdefault(s, []).append(dn)

    def render_decision_gate(node: dict, steps_by_id: dict = None, zn: int = 1) -> str:
        condition = escape(node.get("condition", ""))
        yes = escape(node.get("yes_path", ""))
        no  = escape(node.get("no_path", ""))
        v_tip = '<div class="v-arrow"><div class="v-line" style="height:8px;"></div><div class="v-tip"></div></div>'

        _steps_by_id = steps_by_id or {}
        no_branch_ids  = node.get("no_branch_step_ids")  or []
        yes_branch_ids = node.get("yes_branch_step_ids") or []

        yes_col_html = (_render_branch_sequence(yes_branch_ids, _steps_by_id, zn)
                        if yes_branch_ids
                        else f'<div class="box branch-yes-box"><div class="box-title">{yes}</div></div>')
        no_col_html  = (_render_branch_sequence(no_branch_ids, _steps_by_id, zn)
                        if no_branch_ids
                        else f'<div class="box branch-no-box"><div class="box-title">{no}</div></div>')

        # Source traceability for the decision node, prefer canonical sources[].
        gate_sq = node.get("source_quote", "")
        canon_m, canon_d = _sources_to_render_inputs(node)
        if canon_m or canon_d:
            gate_refs_html = render_meeting_refs(canon_m, gate_sq)
            gate_doc_html = "".join(render_document_ref(dp, q or gate_sq) for dp, q in canon_d)
        else:
            gate_refs = node.get("meeting_references") or _synthesise_meeting_ref(node)
            gate_refs_html = render_meeting_refs(gate_refs, gate_sq)
            gate_doc_html = render_document_ref(node.get("source_document") or "", gate_sq)

        return f"""
        <div class="decision-gate">
          <div class="gate-condition">&#11042; {condition}</div>
          <div class="two-col" style="margin-top:10px;align-items:start;">
            <div class="col">
              <span class="fork-label yes">&#10003; Yes</span>
              {v_tip}
              {yes_col_html}
            </div>
            <div class="col">
              <span class="fork-label no">&#10007; No</span>
              {v_tip}
              {no_col_html}
            </div>
          </div>
          {gate_refs_html}
          {gate_doc_html}
          <div class="gate-merge-spacer"></div>
        </div>"""

    def _render_branch_sequence(step_ids: list, steps_by_id: dict, zn: int) -> str:
        v_tip = '<div class="v-arrow"><div class="v-line" style="height:10px;"></div><div class="v-tip"></div></div>'
        parts = []
        for j, sid in enumerate(step_ids):
            s = steps_by_id.get(sid)
            if not s:
                continue
            if s.get("type") == "optimisation":
                continue
            if s.get("type") == "parallel_group":
                parts.append(render_parallel_group(s, zn=zn))
            else:
                parts.append(render_step(s, zn=zn, owner_color_map=owner_color_map))
            if j < len(step_ids) - 1:
                parts.append(v_tip)
        return "\n".join(parts)

    # Data flow mechanism → (color, short label)
    _FLOW_STYLES = {
        "automated_sync":     ("#10B981", "Auto-sync"),
        "api_integration":    ("#10B981", "API"),
        "manual_entry":       ("#EF4444", "Manual"),
        "manual_check":       ("#EF4444", "Manual check"),
        "email_notification": ("#F59E0B", "Email"),
        "csv_export":         ("#F59E0B", "CSV"),
        "verbal":             ("#9CA3AF", "Verbal"),
        "unknown":            ("#9CA3AF", "?"),
    }

    def render_labeled_arrow(data_flow: dict) -> str:
        """Render a v-arrow with a colored mechanism label."""
        mechanism = data_flow.get("mechanism", "unknown")
        color, label = _FLOW_STYLES.get(mechanism, ("#9CA3AF", mechanism.replace("_", " ").title()))
        return (
            f'<div class="v-arrow labeled-arrow">'
            f'<div class="v-line" style="height:6px;background:{color}"></div>'
            f'<span class="flow-label" style="color:{color};border-color:{color}">{escape(label)}</span>'
            f'<div class="v-line" style="height:6px;background:{color}"></div>'
            f'<div class="v-tip" style="border-top-color:{color}"></div>'
            f'</div>'
        )

    def render_step_sequence(step_list: list, nodes_by_step: dict, nodes_unanchored: list,
                              steps_by_id: dict, zn: int) -> str:
        """Render a vertical sequence of steps with anchored decision gates.
        Modifies nodes_unanchored in-place (pops legacy decision steps)."""
        v_arrow = '<div class="v-arrow"><div class="v-line" style="height:14px;"></div><div class="v-tip"></div></div>'
        step_parts = []
        prev_pg = False
        for i, s in enumerate(step_list):
            if s.get("branch_only"):
                continue
            if s.get("type") == "optimisation":
                continue
            if s.get("type") == "parallel_group":
                step_parts.append(render_parallel_group(s, zn=zn))
                prev_pg = True
            else:
                step_parts.append(render_step(s, zn=zn, owner_color_map=owner_color_map))
                prev_pg = False
            sid = s.get("step_id", "")
            # Inject anchored decision gates after their step
            anchored = nodes_by_step.get(sid, [])
            if len(anchored) == 1:
                step_parts.append(v_arrow)
                step_parts.append(render_decision_gate(anchored[0], steps_by_id=steps_by_id, zn=zn))
            elif len(anchored) > 1:
                step_parts.append(v_arrow)
                cells = "".join(
                    f'<div class="gate-row-cell">{render_decision_gate(dn, steps_by_id=steps_by_id, zn=zn)}</div>'
                    for dn in anchored
                )
                step_parts.append(f'<div class="gate-row">{cells}</div>')
            # Legacy fallback: type=="decision" steps consume unanchored nodes
            if s.get("type") == "decision" and nodes_unanchored:
                step_parts.append(render_decision_gate(nodes_unanchored.pop(0), steps_by_id=steps_by_id, zn=zn))
            if i < len(step_list) - 1 and not prev_pg:
                next_flow = None
                for ns in step_list[i + 1:]:
                    if not ns.get("branch_only"):
                        next_flow = ns.get("data_flow")
                        break
                if next_flow and next_flow.get("mechanism"):
                    step_parts.append(render_labeled_arrow(next_flow))
                else:
                    step_parts.append(v_arrow)
        return "\n".join(step_parts)

    def render_flow_column(flow_meta: dict, flow_steps: list, nodes_by_step: dict,
                           exception_nodes: list, steps_by_id: dict, zn: int) -> str:
        """Render a single named flow track (header + vertical step sequence)."""
        label = escape(flow_meta.get("label", ""))
        cadence = escape(flow_meta.get("cadence", ""))
        cadence_html = f'<span class="flow-track-cadence">{cadence}</span>' if cadence else ""
        header_html = f'<div class="flow-track-header"><span class="flow-track-label">{label}</span>{cadence_html}</div>'
        # Unanchored nodes scoped per column, pass a fresh list (don't mutate zone-level)
        col_unanchored: list = []
        body_html = render_step_sequence(flow_steps, nodes_by_step, col_unanchored, steps_by_id, zn)
        return f"{header_html}{body_html}"

    def render_zone(stage: str) -> str:
        steps = processes_by_stage.get(stage, [])
        label = stage_labels.get(stage, stage.replace("_", " ").title())
        subtitle = stage_subtitles.get(stage, "")
        zn = stage_zone.get(stage, 1)
        # Clamp z-number to CSS vars we define (z1-z9)
        zn = max(1, min(zn, 9))
        zone_class = f"zone z{zn}"

        # Build decision gate lookup: split exception vs main nodes first
        # then index main nodes by anchor step; unanchored main nodes go at zone end
        nodes_by_step: dict = {}
        nodes_unanchored: list = []
        exception_nodes: list = []
        for dn in _decision_nodes_by_stage.get(stage, []):
            if dn.get("is_exception"):
                exception_nodes.append(dn)
                continue
            anchor = (dn.get("after_step_id") or "").strip()
            if anchor:
                nodes_by_step.setdefault(anchor, []).append(dn)
            else:
                nodes_unanchored.append(dn)

        steps_by_id: dict = {s.get("step_id", ""): s for s in steps}

        v_arrow = '<div class="v-arrow"><div class="v-line" style="height:14px;"></div><div class="v-tip"></div></div>'

        if steps:
            # Check for parallel flow tracks defined on this process
            flows = (processes_by_stage_meta.get(stage) or {}).get("flows") or []

            if flows:
                # Assign steps to flow columns
                assigned_ids: set = set()
                flow_columns = []
                for flow in flows:
                    flow_step_ids = flow.get("step_ids", [])
                    flow_steps = [steps_by_id[sid] for sid in flow_step_ids if sid in steps_by_id]
                    assigned_ids.update(flow_step_ids)
                    flow_columns.append((flow, flow_steps))
                # Unassigned non-branch steps go in an implicit "Other" column
                unassigned = [
                    s for s in steps
                    if s.get("step_id") not in assigned_ids
                    and not s.get("branch_only")
                    and s.get("type") not in ("optimisation",)
                ]
                if unassigned:
                    flow_columns.append(({"label": "Other", "cadence": ""}, unassigned))

                col_htmls = []
                for flow_meta, flow_steps in flow_columns:
                    col_body = render_flow_column(
                        flow_meta, flow_steps, nodes_by_step, exception_nodes, steps_by_id, zn
                    )
                    col_htmls.append(f'<div class="flow-track">{col_body}</div>')
                n_cols = len(col_htmls)
                scroll_cls = " flows-row-overflow" if n_cols > 3 else ""
                steps_html = f'<div class="flows-scroll-wrap{scroll_cls}"><div class="flows-row">{"".join(col_htmls)}</div></div>'
            else:
                # Single-column rendering (original behaviour)
                step_parts_list_ref: list = []
                body = render_step_sequence(steps, nodes_by_step, nodes_unanchored, steps_by_id, zn)
                step_parts_list_ref.append(body)
                # Any remaining unanchored main nodes go at end of zone
                for dn in nodes_unanchored:
                    step_parts_list_ref.append(v_arrow)
                    step_parts_list_ref.append(render_decision_gate(dn, steps_by_id=steps_by_id, zn=zn))
                steps_html = "\n".join(step_parts_list_ref)

            # Exception paths render in a separate muted section below main flow (all layouts)
            if exception_nodes:
                ex_cells = "".join(
                    f'<div class="gate-row-cell">{render_decision_gate(dn, steps_by_id=steps_by_id, zn=zn)}</div>'
                    for dn in exception_nodes
                )
                ex_row = f'<div class="gate-row">{ex_cells}</div>' if len(exception_nodes) > 1 else render_decision_gate(exception_nodes[0], steps_by_id=steps_by_id, zn=zn)
                steps_html += f'''
                <div class="exception-paths-section">
                  <div class="exception-paths-header">&#9889; Exception Paths</div>
                  {ex_row}
                </div>'''

            badge_text = f"{len(steps)} step{'s' if len(steps) != 1 else ''}"
        else:
            steps_html = """
            <div style="text-align:center;padding:28px 12px;color:#9CA3AF;font-size:12px;
                        border:2px dashed #E5E7EB;border-radius:10px;margin:8px 0">
              <div style="font-size:24px;margin-bottom:8px">&#x23F3;</div>
              Data collection in progress
            </div>"""
            badge_text = "pending"

        return f"""
        <div class="{zone_class}" id="zone-{stage}">
          <span class="zone-badge">{badge_text}</span>
          <div class="zone-title">{label}</div>
          <div class="zone-subtitle">{subtitle}</div>
          {steps_html}
        </div>"""

    # ── Build owner → (css_class, hex_color) palette mapping ──────────────────
    OWNER_TAG_PALETTE = [
        ("tag-pink",    "#d63384"),
        ("tag-orange",  "#c75000"),
        ("tag-teal",    "#0d9488"),
        ("tag-purple",  "#7b2fbe"),
        ("tag-amber",   "#d97706"),
        ("tag-blue",    "#2563EB"),
        ("tag-green",   "#198754"),
        ("tag-health",  "#0891b2"),
        ("tag-rose",    "#be185d"),
    ]
    _tool_kw = {"automated", "hubspot", "monday", "twilio", "xero", "foundu", "system", "planned",
                "google", "sheets", "zapier", "slack", "notion", "airtable", "asana", "jira",
                "salesforce", "stripe", "quickbooks", "myob", "deputy", "employment hero"}
    owner_color_map: dict = {}  # owner_str → (css_class, hex)
    _palette_idx = 0
    for _proc in ssad.get("processes", []):
        for _step in _proc.get("steps", []):
            _o = (_step.get("owner") or "").strip()
            if _o and _o not in owner_color_map:
                if any(k in _o.lower() for k in _tool_kw):
                    owner_color_map[_o] = ("tool-tag", None)
                else:
                    _cls, _hex = OWNER_TAG_PALETTE[_palette_idx % len(OWNER_TAG_PALETTE)]
                    owner_color_map[_o] = (_cls, _hex)
                    _palette_idx += 1

    # ── Parse owner strings into canonical people + tools ─────────────────────
    _KNOWN_TOOLS = {
        "hubspot", "twilio", "monday", "foundu", "xero",
        "system", "automated", "automation", "planned automation",
        "google sheets", "sheets", "google", "zapier", "slack",
        "notion", "airtable", "asana", "jira", "salesforce",
        "stripe", "quickbooks", "myob", "deputy", "employment hero",
        "ucollect", "easydebit",
    }
    _STRIP_ALL_PARENS = re.compile(r'\s*\([^)]*\)')   # strip ALL parens first
    _SEPARATORS = re.compile(r'\s*\u2192\s*|\s*/\s*|\s*,\s*|\s+&\s+|\s*\+\s*')
    _SKIP = {"none", "planned", "payroll", "accountant", "nannies", "family",
             "va", "recruitment team", "bdm", "marketing", "",
             "videographer", "organic specialist", "specialist", "external", "admin"}
    _DEPARTMENTS = {"contractors", "management", "operations", "sales", "finance",
                    "hr", "support", "leadership", "founders"}
    # Normalise plural/variant role labels to their canonical singular form.
    # Keys are lowercase; values are the display string to use instead.
    _ROLE_ALIASES: dict = {
        "dealers": "Dealer",
        "customers": "Customer", "customer": "Customer",
        "prospects": "Prospect", "prospect": "Prospect",
        "clients": "Client", "client": "Client",
        "leads": "Lead", "lead": "Lead",
        "users": "User", "user": "User",
        "partners": "Partner",
        "referral partners": "Referral Partner",
        "brokers": "Finance Broker",
        "technicians": "Technician",
        "drivers": "Driver",
        "workers": "Support Worker",
        "support workers": "Support Worker",
        "participants": "Participant", "participant": "Participant",
        "candidates": "Candidate", "candidate": "Candidate",
        "applicants": "Applicant", "applicant": "Applicant",
        "suppliers": "Supplier", "supplier": "Supplier",
        "vendors": "Vendor", "vendor": "Vendor",
        "patients": "Patient", "patient": "Patient",
        "guests": "Guest", "guest": "Guest",
        "passengers": "Passenger", "passenger": "Passenger",
        "managers": "Manager",
        "coordinators": "Coordinator",
        "administrators": "Administrator",
        "admins": "Admin",
        "operators": "Operator",
        "owners": "Owner",
    }
    # Roles that represent external actors flowing through the process, not internal staff.
    # Classified into the People Bar's "Customer / External" section instead of "Team".
    _EXTERNAL_ACTOR_ROLES = {
        "lead", "client", "customer", "prospect", "user",
        "participant", "candidate", "applicant",
        "supplier", "vendor", "patient", "guest", "passenger",
        "dealer", "partner", "referral partner",
    }

    # Build canonical name map from staff_roster
    _roster = ssad.get("staff_roster", [])
    _canonical_name: dict = {}  # lowercase token → display first name
    for _person in _roster:
        _full = (_person.get("name") or "").strip()
        if _full:
            _first = _full.split()[0]
            _canonical_name[_full.lower()] = _first
            _canonical_name[_first.lower()] = _first

    canonical_people: dict = {}            # display_name → css_class (first-seen wins)
    canonical_departments: dict = {}       # dept_name → css_class
    canonical_tools: set = set()
    canonical_external_actors: dict = {}   # display_name → css_class (Lead, Client, etc.)

    for _owner_str, (_cls, _hex_) in owner_color_map.items():
        # Strip all parentheticals BEFORE splitting on / so "Alice (15hrs/wk)" works
        _clean_full = _STRIP_ALL_PARENS.sub('', _owner_str).strip()
        for _part in _SEPARATORS.split(_clean_full):
            _clean = _part.strip()
            _low = _clean.lower()
            if not _clean or _low in _SKIP or _low.startswith("none") or _low.startswith("planned"):
                continue
            # Resolve plural/variant role aliases before any further classification
            if _low in _ROLE_ALIASES:
                _clean = _ROLE_ALIASES[_low]
                _low = _clean.lower()
            if any(_t in _low for _t in _KNOWN_TOOLS):
                canonical_tools.add(_clean)
            elif _low in _DEPARTMENTS:
                if _clean not in canonical_departments:
                    canonical_departments[_clean] = "dept-tag"
            elif _low in _EXTERNAL_ACTOR_ROLES:
                if _clean not in canonical_external_actors:
                    canonical_external_actors[_clean] = "external-tag"
            else:
                # Normalize to staff roster name
                _display = _canonical_name.get(_low, _clean)
                if _display not in canonical_people:
                    canonical_people[_display] = _cls

    # Also pull tool names directly from tools[] in the audit data
    for _tool_entry in ssad.get("tools", []):
        _tn = _tool_entry.get("tool_name", "").strip()
        if _tn:
            canonical_tools.add(_tn)

    def _render_tool_badge(name: str) -> str:
        return f'<span class="tool-tag">{escape(name)}</span>'

    # ── People Bar HTML ────────────────────────────────────────────────────────
    _external_tags = [
        f'<span class="external-tag">{escape(name)}</span>'
        for name in canonical_external_actors
    ]
    _team_tags = [
        f'<span class="person-tag {cls}">{escape(name)}</span>'
        for name, cls in canonical_people.items()
    ]
    _dept_tags = [
        f'<span class="dept-tag">{escape(name)}</span>'
        for name in canonical_departments
    ]
    _tool_tags = [
        _render_tool_badge(t)
        for t in sorted(canonical_tools)
    ]
    _pb_sections = []
    if _external_tags:
        _pb_sections.append(
            f'<div class="pb-section"><span class="pb-label">External</span>{"".join(_external_tags)}</div>'
        )
    if _team_tags:
        _pb_sections.append(
            f'<div class="pb-section"><span class="pb-label">Team</span>{"".join(_team_tags)}</div>'
        )
    if _dept_tags:
        _pb_sections.append(
            f'<div class="pb-section"><span class="pb-label">Depts</span>{"".join(_dept_tags)}</div>'
        )
    if _tool_tags:
        _pb_sections.append(
            f'<div class="pb-section"><span class="pb-label">Tools</span>{"".join(_tool_tags)}</div>'
        )
    people_bar_html = (
        f'<div class="people-bar"><div class="people-bar-inner">{"".join(_pb_sections)}</div></div>'
        if _pb_sections else ""
    )

    zones_html = "\n".join(render_zone(stage) for stage in stages)

    pain_points = ssad.get("pain_points") or []
    pain_summary_html = ""
    opportunities_html = ""
    all_optimisations = ssad.get("optimisations") or []

    # Legend items
    legend_items = [
        ("#FFFFFF", "#E5E7EB", "Standard Step"),
        ("#FEE2E2", "#EF4444", "Pain Point"),
        ("#FEF3C7", "#F59E0B", "Decision"),
        ("#DBEAFE", "#3B82F6", "Automation"),
    ]
    legend_html = "".join(
        f'<div class="legend-item">'
        f'<div class="legend-swatch" style="background:{bg};border:1.5px solid {border}"></div>'
        f'{label}</div>'
        for bg, border, label in legend_items
    )
    legend_html += (
        '<div class="legend-item" style="color:#6B7280;font-style:italic">Dashed border = LOW confidence</div>'
    )

    # ── Sidebar Navigation ────────────────────────────────────────────────────
    nav_links = []
    for stage in stages:
        label = stage_labels.get(stage, stage.replace("_", " ").title())
        nav_links.append(f'<a href="#zone-{stage}" data-target="zone-{stage}">{label}</a>')

    sidebar_html = (
        '<nav class="sidebar-nav" id="sidebarNav">'
        '<div class="nav-header">Sections</div>'
        + "".join(nav_links)
        + '</nav>'
        '<button class="sidebar-toggle" id="sidebarToggle" '
        'onclick="document.getElementById(\'sidebarNav\').classList.toggle(\'open\')">'
        '&#9776;</button>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company}: Process Map</title>
{APG_FAVICON}
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  html {{ scroll-behavior: smooth; }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --pain-bg: #fef2f2; --pain-border: #fca5a5; --pain-text: #dc2626;
    --opp-bg: #166534; --opp-border: #14532d; --opp-text: #ffffff;
    --decision-bg: #fffbeb; --decision-border: #fcd34d; --decision-text: #92400e;
    --auto-bg: #eff6ff; --auto-border: #93c5fd; --auto-text: #1d4ed8;
  }}
  body {{ background: #f7f9fc; font-family: 'Inter', -apple-system, sans-serif;
          color: #0f1825; min-height: 100vh; }}

  /* ── APG HEADER ── */
  .apg-header {{ background: #0f1825; color: #fff; padding: 20px 32px;
                 display: flex; align-items: center; gap: 16px;
                 border-bottom: 3px solid #7DFF00; }}
  .apg-header .logo {{ font-size: 20px; font-weight: 800; color: #ffffff; }}
  .apg-header .subtitle {{ font-size: 13px; color: #9CA3AF; margin-top: 2px; }}

  /* ── SUBHEADER ── */
  .subheader {{ background: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                padding: 24px 32px 20px; text-align: center; }}
  .subheader h1 {{ font-family: 'Inter', sans-serif;
                   font-size: 28px; font-weight: 700; color: #0f1825; margin-bottom: 4px; }}
  .subheader .meta {{ font-size: 12px; color: #6B7280; }}

  /* ── LEGEND ── */
  .legend {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 14px;
             padding: 12px 20px; background: #f7f9fc; border-bottom: 1px solid #e2e8f0; }}
  .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 11px;
                  color: #475569; font-weight: 500; }}
  .legend-swatch {{ width: 13px; height: 13px; border-radius: 3px; flex-shrink: 0; }}

  /* ── CANVAS ── */
  .canvas {{ padding: 30px 24px 60px; max-width: 100%; margin-right: auto; }}

  /* ── ZONES ── */
  .zone {{ border-radius: 14px; padding: 20px 22px 24px;
           margin-bottom: 28px; position: relative;
           background: #ffffff; border: 1px solid #e2e8f0;
           box-shadow: 0 1px 8px rgba(15,24,37,0.06); }}
  .zone-title {{ font-family: 'Inter', sans-serif;
                 font-size: 18px; font-weight: 800; margin-bottom: 4px;
                 color: #0f1825; letter-spacing: -0.02em; }}
  .zone-subtitle {{ font-size: 11px; font-weight: 400; color: #64748b; margin-bottom: 14px; }}
  .zone-badge {{ position: absolute; top: 16px; right: 18px; font-size: 10px; font-weight: 600;
                 padding: 3px 10px; border-radius: 20px; letter-spacing: 0.5px; text-transform: uppercase;
                 color: #64748b; background: #f1f5f9; border: 1px solid #e2e8f0; }}
  .z1,.z2,.z3,.z4,.z5,.z6,.z7,.z8,.z9 {{ background: #ffffff; border: 1px solid #e2e8f0;
    box-shadow: 0 1px 8px rgba(15,24,37,0.06); }}
  .z1 .zone-title,.z2 .zone-title,.z3 .zone-title,.z4 .zone-title,
  .z5 .zone-title,.z6 .zone-title,.z7 .zone-title,.z8 .zone-title,
  .z9 .zone-title {{ color: #0f1825; }}
  .z1 .zone-badge,.z2 .zone-badge,.z3 .zone-badge,.z4 .zone-badge,
  .z5 .zone-badge,.z6 .zone-badge,.z7 .zone-badge,.z8 .zone-badge,
  .z9 .zone-badge {{ color: #64748b; background: #f1f5f9; border: 1px solid #e2e8f0; }}

  /* ── BOXES ── */
  .box {{ border-radius: 10px; padding: 12px 14px; font-size: 12px; line-height: 1.55;
          position: relative; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
          transition: box-shadow 0.15s; }}
  .box:hover {{ box-shadow: 0 4px 14px rgba(0,0,0,0.10); }}
  .box-title {{ font-weight: 600; font-size: 13px; margin-bottom: 4px; color: #0f1825; }}
  .box-body {{ font-size: 12px; color: #374151; line-height: 1.6; }}
  .step {{ background: #f7f9fc; border: 1px solid #e2e8f0; }}
  .step-z1 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z1 .box-title {{ color:#0f1825; }}
  .step-z2 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z2 .box-title {{ color:#0f1825; }}
  .step-z3 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z3 .box-title {{ color:#0f1825; }}
  .step-z4 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z4 .box-title {{ color:#0f1825; }}
  .step-z5 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z5 .box-title {{ color:#0f1825; }}
  .step-z6 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z6 .box-title {{ color:#0f1825; }}
  .step-z7 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z7 .box-title {{ color:#0f1825; }}
  .step-z8 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z8 .box-title {{ color:#0f1825; }}
  .step-z9 {{ background:#f7f9fc; border:1px solid #e2e8f0; }} .step-z9 .box-title {{ color:#0f1825; }}
  .decision-box {{ background: var(--decision-bg); border: 2px dashed var(--decision-border); border-radius: 50px; text-align: center; }}
  .decision-box .box-title {{ color: var(--decision-text); }}
  .auto-box {{ background: var(--auto-bg); border: 1.5px solid var(--auto-border); }}
  .auto-box .box-title {{ color: var(--auto-text); }}
  .pain-box {{ background: var(--pain-bg); border: 1.5px solid var(--pain-border); }}
  .pain-box .box-title {{ color: var(--pain-text); }}
  .opp-box {{ background: var(--opp-bg); border: 1.5px solid var(--opp-border); }}
  .opp-box .box-title {{ color: var(--opp-text); }}

  /* ── V-ARROW ── */
  .v-arrow {{ display:flex; flex-direction:column; align-items:center; margin: 3px 0; }}
  .v-line {{ width:2px; background:#94a3b8; }}
  .v-tip {{ width:0; height:0; border-left:5px solid transparent; border-right:5px solid transparent; border-top:7px solid #94a3b8; }}

  /* ── GRID LAYOUTS ── */
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
  .three-col {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }}
  .col {{ display:flex; flex-direction:column; align-items:center; }}
  .col .box {{ width:100%; }}

  /* ── FORK LABELS ── */
  .fork-label {{ font-size:10px; font-weight:700; color:white; border-radius:10px;
                 padding:3px 10px; display:inline-block; margin-bottom:4px; }}
  .fork-label.yes {{ background:#16a34a; }}
  .fork-label.no  {{ background:#dc2626; }}
  .branch-yes-box {{ background:#166534; border:1.5px solid #14532d; }}
  .branch-no-box  {{ background:#fef2f2; border:1.5px solid #fca5a5; }}
  .branch-yes-box .box-title {{ color:#ffffff; }}
  .branch-no-box  .box-title {{ color:#dc2626; }}
  .decision-gate {{ position: relative; margin: 4px 0; }}
  .gate-merge-spacer {{ height: 16px; }}
  .gate-condition {{ background: #fffbeb; border: 2px dashed #fcd34d;
                     border-radius: 8px; padding: 10px 14px; font-size: 12px; font-weight: 600;
                     color: #92400e; text-align: center; }}

  /* ── PARALLEL GATE ROW (co-anchored nodes side-by-side) ── */
  .gate-row {{ display: flex; gap: 14px; align-items: flex-start; }}
  .gate-row-cell {{ flex: 1 1 0; min-width: 280px; }}

  /* ── EXCEPTION PATHS SECTION ── */
  .exception-paths-section {{ margin-top: 20px; border-top: 1px dashed #e2e8f0; padding-top: 14px; }}
  .exception-paths-header {{ font-size: 10px; font-weight: 700; color: #94a3b8;
                              text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px; }}
  .exception-paths-section .decision-gate {{ opacity: 0.85; }}
  .exception-paths-section .gate-condition {{ background: #f8fafc; border-color: #cbd5e1;
                                              color: #64748b; }}

  /* ── FLOW TRACKS (parallel swimlane columns) ── */
  .flows-scroll-wrap {{ position: relative; }}
  .flows-scroll-wrap.flows-row-overflow::after {{
    content: ''; pointer-events: none;
    position: absolute; top: 0; right: 0; bottom: 8px; width: 80px;
    background: linear-gradient(to right, transparent, rgba(248,250,252,0.95));
    z-index: 2;
  }}
  .flows-scroll-wrap.flows-row-overflow::before {{
    content: '→ scroll'; pointer-events: none;
    position: absolute; top: 12px; right: 12px;
    background: #6366f1; color: #fff;
    font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
    padding: 4px 10px; border-radius: 20px; z-index: 3;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3);
  }}
  .flows-row {{ display: flex; gap: 20px; align-items: flex-start; overflow-x: auto; padding-bottom: 8px; }}
  .flow-track {{ flex: 0 0 320px; min-width: 320px; display: flex; flex-direction: column; }}
  .flow-track-header {{ display: flex; align-items: center; gap: 8px;
                        margin-bottom: 12px; padding-bottom: 8px;
                        border-bottom: 2px solid #e2e8f0; }}
  .flow-track-label {{ font-size: 11px; font-weight: 700; color: #374151; }}
  .flow-track-cadence {{ font-size: 9px; font-weight: 600; text-transform: uppercase;
                         letter-spacing: 0.07em; color: #6b7280;
                         background: #f3f4f6; border-radius: 4px; padding: 2px 6px; }}

  /* ── PEOPLE BAR ── */
  .people-bar {{ background:#ffffff; border-bottom:1px solid #e2e8f0; padding:12px 24px; }}
  .people-bar-inner {{ max-width:1300px; margin:0 auto; display:flex; flex-direction:column; gap:10px; }}
  .pb-section {{ display:flex; flex-wrap:wrap; align-items:center; gap:6px; }}
  .pb-label {{ font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.07em;
               color:#9CA3AF; white-space:nowrap; min-width:38px; }}

  /* ── PERSON / TOOL TAGS ── */
  .person-tag,
  .person-tag.tag-pink, .person-tag.tag-orange, .person-tag.tag-teal,
  .person-tag.tag-purple, .person-tag.tag-amber, .person-tag.tag-blue,
  .person-tag.tag-green, .person-tag.tag-health, .person-tag.tag-rose
    {{ background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1;
       border-radius: 6px; font-size: 11px; padding: 3px 10px; display: inline-block; margin-top: 2px; }}
  .tool-tag {{ display: inline-block; font-size: 10px; font-weight: 600;
               background: #166534; color: #ffffff; border: 1px solid #14532d;
               padding: 2px 9px; border-radius: 20px; margin-top: 2px; }}
  .dept-tag {{ display: inline-block; font-size: 10px; font-weight: 600;
               background: #f8fafc; color: #64748b; border: 1px dashed #94a3b8;
               padding: 2px 9px; border-radius: 20px; margin-top: 2px; }}
  .external-tag {{ display: inline-block; font-size: 10px; font-weight: 700;
               background: #fff7ed; color: #9a3412; border: 1px solid #fdba74;
               padding: 2px 9px; border-radius: 20px; margin-top: 2px;
               text-transform: uppercase; letter-spacing: 0.04em; }}

  /* ── STEP TOOL TAGS ── */
  .step-tools {{ margin-top:4px; display:flex; flex-wrap:wrap; gap:3px; }}
  .step-tool-tag {{ display:inline-block; font-size:11px; font-weight:600;
    background:#166534; color:#ffffff; border:1px solid #14532d;
    padding:1px 7px; border-radius:10px; }}

  /* ── LABELED FLOW ARROWS ── */
  .labeled-arrow {{ gap: 0; }}
  .flow-label {{ font-size:10px; font-weight:700; padding:1px 8px;
    border:1.5px solid #94a3b8; border-radius:10px; background:#ffffff;
    color:#475569; }}

  /* ── PAIN POINTS SUMMARY ── */
  .pain-summary-section {{ background:#fef2f2; border-left:4px solid #ef4444; border-radius:12px;
    padding:20px 22px 24px; margin-top:28px; }}
  .pain-summary-header {{ font-family:'Inter',sans-serif; font-size:18px;
    font-weight:800; color:#991b1b; margin-bottom:14px; }}
  .pain-themes-row {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:16px; }}
  .pain-theme-card {{ background:#fff; border:1px solid #FECACA; border-radius:8px;
    padding:10px 14px; flex:1 1 220px; min-width:200px; }}
  .pain-theme-name {{ font-weight:700; font-size:12px; color:#991B1B; margin-bottom:3px; }}
  .pain-theme-meta {{ font-size:10px; color:#6B7280; }}
  .pain-summary-quote {{ font-size:10px; font-style:italic; color:#9A8A80;
    border-left:2px solid #FECACA; padding:2px 6px; margin-top:5px; }}
  .pain-details {{ display:flex; flex-direction:column; gap:10px; }}
  .pp-stage-group {{ }}
  .pp-stage-label {{ font-size:10px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.06em; color:#991B1B; margin-bottom:4px; }}
  .pp-item {{ background:#fff; border:1px solid #FECACA; border-radius:6px;
    padding:8px 12px; margin-bottom:4px; }}
  .pp-item-desc {{ font-size:11px; font-weight:600; color:#1A1A2E; }}
  .pp-item-quote {{ font-size:10px; font-style:italic; color:#9A8A80; margin-top:3px; }}

  /* ── OPPORTUNITIES SUMMARY ── */
  .opp-summary-section {{ background:#166534; border-left:4px solid #22c55e; border-radius:12px;
    padding:20px 24px; margin-top:28px; }}
  .opp-summary-header {{ font-family:'Inter',sans-serif; font-size:18px;
    font-weight:800; color:#166534; margin-bottom:14px; }}
  .opp-details {{ display:flex; flex-direction:column; gap:12px; }}
  .opp-stage-group {{ }}
  .opp-stage-label {{ font-size:11px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.06em; color:#059669; margin-bottom:6px; }}
  .opp-item {{ background:#fff; border:1px solid #A7F3D0; border-radius:6px;
    padding:8px 12px; margin-bottom:4px; }}
  .opp-item-desc {{ font-size:11px; font-weight:600; color:#1A1A2E; }}
  .opp-item-quote {{ font-size:10px; font-style:italic; color:#6B7280; margin-top:3px; }}

  /* ── STEP METADATA + QUOTE ── */
  .step-meta {{ margin-top:5px; display:flex; flex-wrap:wrap; gap:4px; }}
  .meta-chip {{ font-size:10px; font-weight:600; color:#64748b; background:#f1f5f9;
                border-radius:4px; padding:1px 5px; }}
  .step-quote {{ font-size:10px; font-style:italic; color:#64748b;
                 border-left:2px solid #cbd5e1; padding:3px 7px; margin-top:5px; }}

  /* ── FATHOM TIMESTAMP DROPDOWNS ── */
  .fathom-refs {{ margin-top: 5px; display: flex; flex-direction: column; gap: 3px; }}
  .fathom-dropdown {{ border: 1px solid rgba(91,79,207,0.2); border-radius: 6px;
                      background: rgba(91,79,207,0.04); overflow: visible; }}
  .fathom-dropdown > summary {{ display: flex; align-items: center; gap: 8px; font-size: 10px;
    font-weight: 600; color: #5B4FCF; padding: 4px 8px; cursor: pointer;
    list-style: none; user-select: none; }}
  .fathom-dropdown > summary::-webkit-details-marker {{ display: none; }}
  .fathom-dropdown > summary::before {{ display: none; }}
  .fathom-dropdown > summary::after {{ content: "›"; margin-left: auto; font-size: 14px;
    line-height: 1; transition: transform 0.15s; display: inline-block; }}
  .fathom-dropdown[open] > summary::after {{ transform: rotate(90deg); }}
  .fathom-dropdown:hover {{ background: rgba(91,79,207,0.08); border-color: rgba(91,79,207,0.35); }}
  .ref-label {{ flex: 1; }}
  .ref-time {{ font-size: 9px; color: #8B7FCF; font-weight: 500; font-variant-numeric: tabular-nums; }}
  .fathom-panel {{ padding: 6px 10px 8px; border-top: 1px solid rgba(91,79,207,0.15);
                   display: flex; flex-direction: column; gap: 6px; }}
  .fathom-excerpt {{ font-size: 10px; color: #3D3560; background: rgba(91,79,207,0.05);
    border-left: 2px solid rgba(91,79,207,0.25); margin: 0; padding: 6px 10px;
    border-radius: 0 4px 4px 0; line-height: 1.5; }}
  .tx-line {{ margin-bottom: 3px; }}
  .tx-line:last-child {{ margin-bottom: 0; }}
  .fathom-open-btn {{ align-self: flex-start; font-size: 9px; font-weight: 700; color: #5B4FCF;
    text-decoration: none; background: rgba(91,79,207,0.1); border: 1px solid rgba(91,79,207,0.25);
    border-radius: 4px; padding: 3px 10px; letter-spacing: 0.02em; }}
  .fathom-open-btn:hover {{ background: rgba(91,79,207,0.2); }}

  /* ── EMAIL CITATION LINKS ── */
  .email-refs {{ margin-top: 3px; display: flex; flex-direction: column; gap: 2px; opacity: 0; transition: opacity 0.15s; }}
  .box:hover .email-refs {{ opacity: 1; }}
  .email-link {{ display: inline-block; font-size: 10px; font-weight: 600; color: #1a7f5a;
                 text-decoration: none; background: rgba(26,127,90,0.08);
                 border: 1px solid rgba(26,127,90,0.2); border-radius: 4px;
                 padding: 2px 6px; white-space: nowrap; }}
  .email-link:hover {{ background: rgba(26,127,90,0.15); text-decoration: underline; }}

  /* ── TOOL TAG RECORDING DROPDOWNS ── */
  .tool-dropdown {{ display: inline-block; vertical-align: middle; position: relative; }}
  .tool-dropdown > summary {{ display: inline-flex; align-items: center; gap: 3px; font-size: 10px;
    font-weight: 600; background: #166534; color: #ffffff; border: 1px solid #14532d;
    padding: 2px 9px; border-radius: 20px; margin-top: 2px; cursor: pointer;
    list-style: none; user-select: none; }}
  .tool-dropdown > summary::-webkit-details-marker {{ display: none; }}
  .tool-dropdown[open] > summary {{ background: #166534; border-color: #14532d;
    border-radius: 10px 10px 0 0; }}
  .tool-dropdown-panel {{ position: absolute; z-index: 20; left: 0; top: 100%;
    background: #166534; border: 1px solid #14532d; border-radius: 0 8px 8px 8px;
    padding: 6px 10px 8px; display: flex; flex-direction: column; gap: 5px;
    min-width: 200px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
  .tool-excerpt {{ font-size: 10px; font-style: italic; color: #ffffff;
    background: rgba(22,101,52,0.06); border-left: 2px solid rgba(22,101,52,0.3);
    margin: 0; padding: 3px 7px; border-radius: 0 3px 3px 0; line-height: 1.4; }}
  .tool-open-btn {{ align-self: flex-start; font-size: 9px; font-weight: 700; color: #ffffff;
    text-decoration: none; background: rgba(22,101,52,0.08); border: 1px solid rgba(22,101,52,0.25);
    border-radius: 4px; padding: 2px 8px; }}
  .tool-open-btn:hover {{ background: rgba(22,101,52,0.15); }}

  /* ── PARALLEL GROUP ── */
  .pg-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: #9CA3AF; text-align: center; margin-bottom: 6px; }}
  .pg-row {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-start; margin: 4px 0; }}
  .pg-chip {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 8px 12px; font-size: 11px; font-weight: 600; color: #0f1825;
    text-align: center; min-width: 80px; flex: 1 1 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .pg-chip .chip-tool {{ display: block; font-size: 9px; font-weight: 600; color: #166634;
    background: #166534; border: 1px solid #14532d; border-radius: 10px;
    padding: 1px 6px; margin-top: 3px; }}
  .pg-chip .chip-owner {{ display: block; font-size: 9px; margin-top: 3px; }}
  .pg-chip .chip-dropdown {{ display: block; margin-top: 4px; }}
  .pg-chip .chip-dropdown > summary {{ display: inline-flex; align-items: center; gap: 3px;
    font-size: 9px; color: #5B4FCF; cursor: pointer; list-style: none; opacity: 0.7; }}
  .pg-chip .chip-dropdown > summary::-webkit-details-marker {{ display: none; }}
  .pg-chip:hover .chip-dropdown > summary {{ opacity: 1; }}
  .pg-chip .chip-panel {{ margin-top: 4px; background: rgba(91,79,207,0.06);
    border: 1px solid rgba(91,79,207,0.2); border-radius: 6px; padding: 5px 8px;
    display: flex; flex-direction: column; gap: 5px; text-align: left; }}
  .pg-chip .chip-excerpt {{ font-size: 9px; font-style: italic; color: #5B4FCF;
    border-left: 2px solid rgba(91,79,207,0.3); padding-left: 5px; margin: 0; line-height: 1.4; }}
  .pg-chip .chip-open-btn {{ align-self: flex-start; font-size: 9px; font-weight: 700;
    color: #5B4FCF; text-decoration: none; background: rgba(91,79,207,0.1);
    border: 1px solid rgba(91,79,207,0.25); border-radius: 4px; padding: 1px 6px; }}
  .pg-merge {{ display: flex; flex-direction: column; align-items: center; }}
  .pg-legs {{ display: flex; justify-content: center; width: 100%; }}
  .pg-leg {{ flex: 1; display: flex; justify-content: center; }}
  .pg-leg .v-line {{ height: 10px; width: 2px; background: #94a3b8; }}
  .pg-crossbar {{ height: 2px; background: #94a3b8; }}
  .pg-drop {{ display: flex; flex-direction: column; align-items: center; }}
  .pg-drop .v-line {{ height: 10px; width: 2px; background: #94a3b8; }}
  .pg-drop .v-tip {{ width: 0; height: 0; border-left: 5px solid transparent;
    border-right: 5px solid transparent; border-top: 7px solid #94a3b8; }}

  /* ── FOOTER NOTE ── */
  .footer-note {{ font-size: 11px; color: #94a3b8; margin-top: 8px; padding-top: 12px;
                  border-top: 1px dashed #e2e8f0; }}

  @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  .box {{ animation: fadeUp 0.3s ease both; }}

  .step-session {{ font-size: 10px; color: #9CA3AF; font-weight: 500; margin-top: 4px; }}

  /* ── SIDEBAR NAV ── */
  .sidebar-nav {{ position: fixed; top: 0; left: 0; width: 210px; height: 100vh;
    background: rgba(15,24,37,0.97); padding: 20px 0; z-index: 100;
    overflow-y: auto; border-right: 1px solid #1e293b; }}
  .sidebar-nav .nav-header {{ padding: 12px 16px; font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; }}
  .sidebar-nav a {{ display: block; padding: 8px 16px; font-size: 12px; font-weight: 500;
    color: #94a3b8; text-decoration: none; border-left: 3px solid transparent;
    transition: all 0.15s; }}
  .sidebar-nav a:hover {{ color: #e2e8f0; background: rgba(255,255,255,0.04); }}
  .sidebar-nav a.active {{ color: #7DFF00; border-left-color: #7DFF00;
    background: rgba(125,255,0,0.06); font-weight: 600; }}
  .sidebar-toggle {{ display: none; position: fixed; top: 12px; left: 12px; z-index: 200;
    background: #0f1825; color: #7DFF00; border: 1px solid #1e293b;
    border-radius: 6px; padding: 8px 10px; cursor: pointer; font-size: 16px; }}
  .apg-header, .subheader, .legend, .people-bar {{ margin-left: 210px; }}
  .canvas {{ margin-left: 210px; }}
  @media (max-width: 768px) {{
    .sidebar-nav {{ transform: translateX(-100%); transition: transform 0.2s; }}
    .sidebar-nav.open {{ transform: translateX(0); }}
    .sidebar-toggle {{ display: block; }}
    .apg-header, .subheader, .legend, .people-bar {{ margin-left: 0; }}
    .canvas {{ margin-left: 0; }}
  }}
</style>
</head>
<body>

{sidebar_html}

<div class="apg-header">
  <div style="display:flex;align-items:center;gap:12px;">
    <img src="{APG_LOGO_URL}"
         alt="Bosar" style="height:38px;width:auto;display:block;">
    <div>
      <div class="logo">Bosar Agency</div>
      <div class="subtitle">Business Operations Audit</div>
    </div>
  </div>
  <div style="margin-left:auto;display:flex;align-items:center;gap:20px;">
    <div style="text-align:right">
      <div style="font-weight:700;font-size:16px">{company}</div>
      <div style="font-size:12px;color:#9CA3AF">Current-State Process Map &middot; {generated}</div>
    </div>
  </div>
</div>

<div class="subheader">
  <h1>Current-State Process Map</h1>
  <div class="meta">{company} &nbsp;&middot;&nbsp; {sessions} session{'s' if sessions != 1 else ''} completed &nbsp;&middot;&nbsp; Generated {generated}</div>
</div>

<div class="legend">
  {legend_html}
</div>

{people_bar_html}

<div class="canvas">
  {zones_html}
  {pain_summary_html}
  {opportunities_html}
  <div class="footer-note">
    Hover over any step to see the source quote from the audit session transcript.
    Dashed borders indicate LOW confidence, data to be confirmed in a future session.
    Steps with recording references show an expandable dropdown with transcript dialogue, expand to read context and open the recording at that exact moment.
    Tool tags with &#9654; in the People Bar link to the recording where that tool was discussed.
  </div>
</div>

<script>
/* ── Decision-gate branch connectors (SVG, drawn after layout) ── */
window.addEventListener('load', function() {{
  var C = '#94a3b8', W = 2;
  function svgEl(tag, attrs) {{
    var el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.keys(attrs).forEach(function(k) {{ el.setAttribute(k, attrs[k]); }});
    return el;
  }}
  document.querySelectorAll('.decision-gate').forEach(function(gate) {{
    var twocol = gate.querySelector('.two-col');
    var spacer = gate.querySelector('.gate-merge-spacer');
    if (!twocol || !spacer) return;
    var cols = twocol.querySelectorAll(':scope > .col');
    if (cols.length !== 2) return;

    var gR = gate.getBoundingClientRect();
    var centerX = gR.width / 2;

    /* Actual bottom-center of each col's last child */
    var colPts = Array.from(cols).map(function(col) {{
      var colR = col.getBoundingClientRect();
      var kids = Array.from(col.children);
      var last = kids.length ? kids[kids.length - 1] : col;
      var lR   = last.getBoundingClientRect();
      return {{ x: colR.left + colR.width / 2 - gR.left, y: lR.bottom - gR.top }};
    }});

    /* Merge Y = bottom of the taller column */
    var mergeY = Math.max(colPts[0].y, colPts[1].y);

    /* Connect Y = bottom of the v-arrow below the gate (SVG overflow:visible handles the gap) */
    var connectY = spacer.getBoundingClientRect().bottom - gR.top;
    var nextEl = gate.nextElementSibling;
    if (nextEl && nextEl.classList.contains('v-arrow')) {{
      connectY = nextEl.getBoundingClientRect().bottom - gR.top;
    }}

    var svg = svgEl('svg', {{
      style: 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;overflow:visible;z-index:1'
    }});

    colPts.forEach(function(pt) {{
      svg.appendChild(svgEl('line', {{ x1:pt.x, y1:pt.y, x2:pt.x,      y2:mergeY, stroke:C, 'stroke-width':W }}));
      svg.appendChild(svgEl('line', {{ x1:pt.x, y1:mergeY, x2:centerX, y2:mergeY, stroke:C, 'stroke-width':W }}));
    }});

    /* Vertical from merge point down to next v-arrow */
    svg.appendChild(svgEl('line', {{ x1:centerX, y1:mergeY, x2:centerX, y2:connectY, stroke:C, 'stroke-width':W }}));

    gate.appendChild(svg);
  }});
}});

/* ── Sidebar scroll-spy ── */
(function() {{
  var sections = document.querySelectorAll('[id^="zone-"], #pain-points, #opportunities');
  var navLinks = document.querySelectorAll('.sidebar-nav a');
  if (!sections.length || !navLinks.length) return;
  var observer = new IntersectionObserver(function(entries) {{
    entries.forEach(function(entry) {{
      if (entry.isIntersecting) {{
        navLinks.forEach(function(l) {{ l.classList.remove('active'); }});
        var active = document.querySelector('.sidebar-nav a[data-target="' + entry.target.id + '"]');
        if (active) active.classList.add('active');
      }}
    }});
  }}, {{ rootMargin: '-20% 0px -70% 0px' }});
  sections.forEach(function(s) {{ observer.observe(s); }});
  navLinks.forEach(function(link) {{
    link.addEventListener('click', function(e) {{
      e.preventDefault();
      var target = document.getElementById(this.getAttribute('data-target'));
      if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      document.getElementById('sidebarNav').classList.remove('open');
    }});
  }});
}})();
</script>
</body>
</html>"""


def _render_quadrant_matrix(ssad: dict, enriched_changes: list = None) -> tuple:
    """Build the quadrant priority matrix HTML grouped by process area.

    Returns (pm_quadrant_html, pm_modals_html).
    If *enriched_changes* is None, builds the list from ssad['proposed_changes']
    filtering for changes that have both value and implementation estimates.
    """
    import math as _math

    if enriched_changes is None:
        enriched_changes = [
            c for c in ssad.get("proposed_changes", [])
            if c.get("value", {}).get("combined_annual_value_aud") is not None
            and c.get("implementation", {}).get("weeks_estimate") is not None
        ]

    pm_quadrant_html = ""
    pm_modals_html = ""
    if enriched_changes:
        _roi_tier_lookup = {r.get("linked_change_id", ""): r.get("suggested_tier", "standard") for r in ssad.get("roi_items", [])}
        _pm_processes = ssad.get("processes", [])
        _pm_stage_labels = {p["stage"]: p["name"] for p in _pm_processes}
        _PM_TIER_COLOR = {"quick_win": "#ea580c", "micro": "#ea580c", "standard": "#2563eb", "complex": "#2563eb", "sprint": "#16a34a"}

        def _pm_effective_tier(c, _roi_tier_lookup):
            qwp = c.get("quick_win_plan", {})
            if qwp.get("qualified") is True:
                return "quick_win"
            return _roi_tier_lookup.get(c.get("change_id", ""), "standard")
        _PM_TIER_LABELS = {"micro": "Quick Win", "standard": "Cowork Plugin", "complex": "Cowork Plugin", "sprint": "Custom Platform"}

        # ── Attempt plugin-based grouping (new model) ──────────────────────────
        # Prefer plugin_cards from SA if present; fall back to plugin_bundles from RI.
        # Fall back to stage grouping if neither is populated.
        _sa_plugin_cards = (
            ssad.get("strategic_approaches", {})
                .get("service_tier_recommendation", {})
                .get("mid_ticket", {})
                .get("plugin_cards", [])
        )
        if not _sa_plugin_cards:
            _sa_plugin_cards = ssad.get("plugin_bundles", [])
        # Build map: change_id -> (plugin_idx, plugin_title, complexity_tier)
        _pm_plugin_by_cid = {}
        for _pi, _pc in enumerate(_sa_plugin_cards):
            _cids = _pc.get("covered_change_ids") or _pc.get("change_ids") or (
                [_pc["change_id"]] if _pc.get("change_id") else [])
            for _cid in _cids:
                if _cid:
                    _pm_plugin_by_cid[str(_cid)] = {
                        "idx": _pi,
                        "title": _pc.get("title", f"Plugin {_pi + 1}"),
                        "complexity": _pc.get("complexity_tier", "standard"),
                    }

        _use_plugin_grouping = bool(_pm_plugin_by_cid)

        if _use_plugin_grouping:
            # Group enriched_changes by plugin; uncovered → "custom-platform" bucket
            _pm_plugin_groups = {}   # idx -> list of changes
            _pm_custom_items = []
            for c in enriched_changes:
                cid = str(c.get("change_id", ""))
                _plugin_info = _pm_plugin_by_cid.get(cid)
                if _plugin_info:
                    _pm_plugin_groups.setdefault(_plugin_info["idx"], []).append(c)
                else:
                    _pm_custom_items.append(c)

            grouped = []
            for _pi, _pc in enumerate(_sa_plugin_cards):
                items = _pm_plugin_groups.get(_pi, [])
                if not items:
                    continue
                group_val = sum(c["value"]["combined_annual_value_aud"] for c in items)
                group_weeks = max(c["implementation"]["weeks_estimate"] for c in items)
                complexity = _pc.get("complexity_tier", "standard")
                dominant_tier = "complex" if complexity == "complex" else "standard"
                color = _PM_TIER_COLOR.get(dominant_tier, "#2563eb")
                grouped.append({
                    "stage": f"plg_{_pi}", "label": _pc.get("title", f"Plugin {_pi + 1}"),
                    "annual_val": group_val, "weeks": group_weeks, "color": color,
                    "dominant_tier": dominant_tier, "items": items,
                    "group_id": f"GRP-PLG-{_pi}",
                })

            if _pm_custom_items:
                group_val = sum(c["value"]["combined_annual_value_aud"] for c in _pm_custom_items)
                group_weeks = max(c["implementation"]["weeks_estimate"] for c in _pm_custom_items)
                grouped.append({
                    "stage": "custom_platform", "label": "Custom Platform scope",
                    "annual_val": group_val, "weeks": group_weeks,
                    "color": _PM_TIER_COLOR["sprint"], "dominant_tier": "sprint",
                    "items": _pm_custom_items, "group_id": "GRP-CUSTOM",
                })
        else:
            # Legacy fallback: group by stage
            _pm_stage_groups = {}
            for c in enriched_changes:
                stage = c.get("stage", "other")
                _pm_stage_groups.setdefault(stage, []).append(c)

            grouped = []
            for stage, items in _pm_stage_groups.items():
                group_val = sum(c["value"]["combined_annual_value_aud"] for c in items)
                group_weeks = max(c["implementation"]["weeks_estimate"] for c in items)
                tiers = [_pm_effective_tier(c, _roi_tier_lookup) for c in items]
                tier_counts = {}
                for t in tiers:
                    tier_counts[t] = tier_counts.get(t, 0) + 1
                dominant_tier = "sprint" if "sprint" in tier_counts else max(tier_counts, key=tier_counts.get)
                color = _PM_TIER_COLOR.get(dominant_tier, "#2563eb")
                grouped.append({
                    "stage": stage, "label": _pm_stage_labels.get(stage, stage.replace("_", " ").title()),
                    "annual_val": group_val, "weeks": group_weeks, "color": color,
                    "dominant_tier": dominant_tier, "items": items,
                    "group_id": f"GRP-{stage}",
                })

        values = [g["annual_val"] for g in grouped]
        weeks_list = [g["weeks"] for g in grouped]
        min_val, max_val = min(values), max(values)
        val_range = max(max_val - min_val, 1)

        def _impact(v):
            norm = _math.sqrt((v - min_val) / val_range) if val_range > 0 else 0.5
            return max(1, min(10, round(1 + norm * 9)))

        max_weeks = max(weeks_list)
        min_weeks = min(weeks_list)
        weeks_range = max(max_weeks - min_weeks, 0.5)

        def _ease(w):
            norm = 1 - ((w - min_weeks) / weeks_range)
            return max(1, min(10, round(1 + norm * 9)))

        bubble_data = []
        for g in grouped:
            impact = _impact(g["annual_val"])
            ease = _ease(g["weeks"])
            size = max(45, min(90, 45 + _math.sqrt(g["annual_val"] / max_val) * 45))
            savings_label = f"${g['annual_val']/1000:.0f}k/yr" if g["annual_val"] >= 1000 else f"${g['annual_val']:,.0f}/yr"
            bubble_data.append({
                "group_id": g["group_id"], "label": g["label"], "impact": impact, "ease": ease,
                "size": size, "color": g["color"], "savings_label": savings_label,
                "annual_val": g["annual_val"], "dominant_tier": g["dominant_tier"], "items": g["items"],
            })

        # Anti-overlap jitter pass
        for i in range(len(bubble_data)):
            for j in range(i):
                bi, bj = bubble_data[i], bubble_data[j]
                if bi["impact"] == bj["impact"] and bi["ease"] == bj["ease"]:
                    bi["impact"] = min(10, bi["impact"] + (1 if i % 2 == 0 else 0))
                    bi["ease"] = max(1, bi["ease"] - (1 if i % 2 == 1 else 0))
                elif abs(bi["impact"] - bj["impact"]) <= 1 and abs(bi["ease"] - bj["ease"]) <= 1:
                    bi["impact"] = min(10, max(1, bi["impact"] + (1 if i % 2 == 0 else -1)))

        # Build bubbles HTML
        bubbles_html = ""
        for i, b in enumerate(bubble_data):
            left = 12 + ((b["impact"] - 1) / 9) * 76
            bottom = 12 + ((b["ease"] - 1) / 9) * 76
            bubbles_html += f"""<div class="qm-bubble" data-idx="{i}" data-cid="{b['group_id']}"
              style="left:{left:.1f}%;bottom:{bottom:.1f}%;width:{b['size']:.0f}px;height:{b['size']:.0f}px;
                     border-color:{b['color']};background:{b['color']}20"
              onclick="qmClick({i})" onmouseenter="qmHover({i})" onmouseleave="qmHover(null)">
              <div class="qm-tip" id="qm-tip-{i}">
                <div style="font-size:13px;font-weight:700">{b['label']}</div>
                <div style="font-size:11px;color:{APG_GREY};margin-top:2px">{len(b['items'])} improvements &middot; {_PM_TIER_LABELS.get(b['dominant_tier'], 'SaaS')}</div>
                <div style="font-size:12px;font-weight:700;color:#166534;margin-top:2px">{b['savings_label']}</div>
              </div>
            </div>\n"""

        # Build legend buttons
        legend_html = ""
        for i, b in enumerate(bubble_data):
            legend_html += f"""<button class="qm-legend-btn" data-idx="{i}"
              onclick="qmSelect(qmSelected==={i}?null:{i})" onmouseenter="qmHover({i})" onmouseleave="qmHover(null)"
              style="border-color:var(--border)">
              <span style="width:12px;height:12px;border-radius:50%;border:2px solid {b['color']};background:{b['color']}30;flex-shrink:0;display:inline-block"></span>
              <span style="font-size:12px;font-weight:500">{b['label']}</span>
            </button>\n"""

        pm_quadrant_html = f"""<div class="qm-container">
          <div class="qm-axis-x"></div>
          <div class="qm-axis-y"></div>
          <div class="qm-mid-x"></div>
          <div class="qm-mid-y"></div>
          <div class="qm-label qm-label-tl">Nice-to-Haves</div>
          <div class="qm-label qm-label-tr" style="color:var(--lime-text)">Quick Wins</div>
          <div class="qm-label qm-label-br" style="color:#3b82f6">Big Swings</div>
          <div class="qm-label qm-label-bl">Future Plans</div>
          <div class="qm-axis-label-x">Business Impact &rarr;</div>
          <div class="qm-axis-label-y">Ease of Implementation &rarr;</div>
          {bubbles_html}
        </div>
        <div class="qm-legend">{legend_html}</div>"""

        # Build grouped modals
        for b in bubble_data:
            group_id = b["group_id"]
            label = b["label"]
            annual_val = b["annual_val"]
            dominant_tier = b["dominant_tier"]
            tier_label = _PM_TIER_LABELS.get(dominant_tier, "SaaS Toolkit")
            tier_color = _PM_TIER_COLOR.get(dominant_tier, "#2563eb")
            items = b["items"]

            sub_items_html = ""
            for c in items:
                c_title = escape(c.get("title", ""))
                c_val = (c.get("value") or {}).get("combined_annual_value_aud", 0) or 0
                c_wlabel = escape(c.get("implementation", {}).get("weeks_label", ""))
                c_tier = _roi_tier_lookup.get(c.get("change_id", ""), "standard")
                c_tier_label = _PM_TIER_LABELS.get(c_tier, "SaaS Toolkit")
                c_tier_color = _PM_TIER_COLOR.get(c_tier, "#2563eb")
                c_type = escape(c.get("change_type", ""))
                mc = c.get("modal_content", {})
                c_desc = escape(mc.get("what_we_will_build", mc.get("what_is_the_task", "")))
                sub_items_html += f"""<div style="padding:12px 0;border-bottom:1px solid #F1F5F9">
                  <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:4px">
                    <div style="font-size:14px;font-weight:600;color:{APG_DARK}">{c_title}</div>
                    <div style="font-size:14px;font-weight:700;color:#059669;white-space:nowrap;margin-left:12px">{fmt_aud(c_val)}/yr</div>
                  </div>
                  <div style="display:flex;gap:6px;margin-bottom:6px">
                    <span style="background:{c_tier_color};color:#fff;border-radius:4px;padding:1px 8px;font-size:10px;font-weight:600">{c_tier_label}</span>
                    <span style="background:#1E293B;color:#E5E7EB;border-radius:4px;padding:1px 8px;font-size:10px;text-transform:uppercase">{c_type}</span>
                    <span style="background:#1E293B;color:#E5E7EB;border-radius:4px;padding:1px 8px;font-size:10px">{c_wlabel}</span>
                  </div>
                  <div style="font-size:13px;color:#64748b;line-height:1.4">{c_desc}</div>
                </div>\n"""

            pm_modals_html += f"""<div class="pm-modal-backdrop" id="modal-{group_id}" style="display:none" onclick="if(event.target===this)closeModal()">
  <div class="pm-modal">
    <button class="pm-modal-close" onclick="closeModal()">&times;</button>
    <div style="margin-bottom:16px">
      <h3 style="font-size:18px;font-weight:700;margin-bottom:8px">{label}</h3>
      <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
        <span style="background:{tier_color};color:#fff;border-radius:4px;padding:1px 8px;font-size:10px;font-weight:600">{tier_label}</span>
        <span style="background:#1E293B;color:#E5E7EB;border-radius:4px;padding:1px 8px;font-size:10px">{len(items)} improvements</span>
      </div>
    </div>
    <div style="margin-bottom:16px">{sub_items_html}</div>
    <div class="pm-modal-stats">
      <div><span class="pm-modal-stat-val">{fmt_aud(annual_val)}</span><span class="pm-modal-stat-lbl">Combined annual value</span></div>
      <div><span class="pm-modal-stat-val">{len(items)}</span><span class="pm-modal-stat-lbl">Improvements</span></div>
    </div>
  </div>
</div>\n"""

    return (pm_quadrant_html, pm_modals_html)


def _build_bpmn_svg(ts: dict, change_id: str) -> str:
    """Build a BPMN 2.0 swim-lane SVG from a technical_spec object.

    Renders: horizontal swim lanes (one per tool), task nodes (rounded rects),
    start/end events (circles), sequence flows (solid arrows), and message
    flows (dashed arrows) for cross-lane data transfers.
    """
    swim  = ts.get("swim_lanes", {})
    tools = swim.get("tools", [])
    flows = swim.get("flows", [])
    steps = ts.get("implementation_steps", [])

    if not tools or not steps:
        return ""

    # ── Layout constants ─────────────────────────────────────────────────
    LABEL_W = 130   # Lane label column width
    LANE_H  = 100   # Height of each swim lane
    NODE_W  = 150   # Task node width
    NODE_H  = 58    # Task node height
    H_GAP   = 36    # Horizontal gap between node edges
    EVT_R   = 13    # Start / end event radius
    PAD_L   = 46    # Space left of first node (for start event)
    PAD_R   = 46    # Space right of last node (for end event)

    # ── Sort steps by step_id numeric suffix ─────────────────────────────
    def sid_key(s):
        tail = (s.get("step_id") or "").rsplit("-", 1)[-1]
        try: return int(tail)
        except: return 0

    ordered = sorted(steps, key=sid_key)
    n = len(ordered)
    n_lanes = len(tools)

    # ── Tool → lane index (fuzzy match) ──────────────────────────────────
    def _norm(name):
        return name.split("(")[0].strip().lower()

    tool_idx = {t: i for i, t in enumerate(tools)}

    def find_lane(tool_name):
        tn = _norm(tool_name)
        for t in tools:
            nt = _norm(t)
            if nt == tn or tn in nt or nt in tn:
                return tool_idx[t], t
        return 0, tools[0]

    # ── Geometry ─────────────────────────────────────────────────────────
    LEGEND_H = 34   # dedicated strip below the lanes for the legend

    lane_cy = [i * LANE_H + LANE_H // 2 for i in range(n_lanes)]

    # Per-step geometry
    node_data = []
    for j, st in enumerate(ordered):
        li, _ = find_lane(st.get("tool", ""))
        cx = LABEL_W + PAD_L + j * (NODE_W + H_GAP) + NODE_W // 2
        cy = lane_cy[li]
        node_data.append({"cx": cx, "cy": cy, "li": li, "st": st, "j": j})

    start_cx = LABEL_W + PAD_L // 2
    start_cy = node_data[0]["cy"]
    end_cx   = LABEL_W + PAD_L + n * (NODE_W + H_GAP) - H_GAP + 24 + PAD_R // 2
    end_cy   = node_data[-1]["cy"]

    nodes_right = end_cx + EVT_R + 14   # right extent the node/event row needs

    # ── Message-flow pre-pass: give every cross-lane flow a distinct x ────
    def _flow_short(s):
        s = s or ""
        return (s[:24] + "…") if len(s) > 24 else s

    def _chip_w(s):
        return int(len(_flow_short(s)) * 6.0) + 18

    flow_layout = []
    lane_use: dict = {}
    for fl in flows:
        if not isinstance(fl, dict):
            continue
        f_li, _ = find_lane(fl.get("from_tool", ""))
        t_li, _ = find_lane(fl.get("to_tool", ""))
        if f_li == t_li:
            continue
        in_lane = [nd for nd in node_data if nd["li"] == f_li]
        k = lane_use.get(f_li, 0)
        if in_lane:
            anchor = in_lane[min(k, len(in_lane) - 1)]
            x0 = anchor["cx"] + NODE_W // 2 + 16
        else:
            x0 = LABEL_W + PAD_L + NODE_W
        lane_use[f_li] = k + 1
        flow_layout.append({"fl": fl, "f_li": f_li, "t_li": t_li, "x": x0})

    # Resolve horizontal collisions so chips never overlap each other.
    flow_layout.sort(key=lambda v: v["x"])
    max_chip_w = max((_chip_w(v["fl"].get("data", "")) for v in flow_layout), default=0)
    min_gap = max(NODE_W // 2, max_chip_w + 18)
    prev_x = None
    for v in flow_layout:
        if prev_x is not None and v["x"] < prev_x + min_gap:
            v["x"] = prev_x + min_gap
        prev_x = v["x"]

    flows_right = max((v["x"] for v in flow_layout), default=0) + max_chip_w // 2 + 20

    total_w = max(nodes_right, flows_right, LABEL_W + 360) + PAD_R
    total_h = n_lanes * LANE_H + LEGEND_H

    cid = change_id  # safe, already escaped by caller
    parts = []

    # ── Pool outline ──────────────────────────────────────────────────────
    parts.append(
        f'<rect x="0" y="0" width="{total_w}" height="{total_h}" '
        f'rx="6" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>'
    )

    # ── Swim lanes ────────────────────────────────────────────────────────
    for i, tool in enumerate(tools):
        ly = i * LANE_H
        if i > 0:
            parts.append(f'<line x1="0" y1="{ly}" x2="{total_w}" y2="{ly}" stroke="#e2e8f0" stroke-width="1"/>')
        # Label column
        parts.append(f'<rect x="0" y="{ly}" width="{LABEL_W}" height="{LANE_H}" fill="#f8fafc"/>')
        parts.append(f'<line x1="{LABEL_W}" y1="{ly}" x2="{LABEL_W}" y2="{ly + LANE_H}" stroke="#cbd5e1" stroke-width="1"/>')
        # Tool name, strip URL suffix, wrap into 2 lines
        display = tool.split("(")[0].strip()
        words = display.split()
        l1, l2 = "", ""
        for w in words:
            if len((l1 + " " + w).strip()) <= 16:
                l1 = (l1 + " " + w).strip()
            else:
                l2 = (l2 + " " + w).strip()
        cy_t = ly + LANE_H // 2
        if l2:
            parts.append(
                f'<text x="{LABEL_W // 2}" y="{cy_t - 5}" text-anchor="middle" '
                f'font-size="11" font-weight="600" fill="#0f1825" font-family="Inter,sans-serif">{escape(l1)}</text>'
                f'<text x="{LABEL_W // 2}" y="{cy_t + 9}" text-anchor="middle" '
                f'font-size="11" font-weight="600" fill="#0f1825" font-family="Inter,sans-serif">{escape(l2)}</text>'
            )
        else:
            parts.append(
                f'<text x="{LABEL_W // 2}" y="{cy_t + 4}" text-anchor="middle" '
                f'font-size="11" font-weight="600" fill="#0f1825" font-family="Inter,sans-serif">{escape(l1)}</text>'
            )

    # ── Sequence flow arrows ──────────────────────────────────────────────
    # Anchor chain: start_event → node[0] → node[1] → ... → node[n-1] → end_event
    chain = (
        [(start_cx + EVT_R, start_cy)]
        + [(nd["cx"] - NODE_W // 2, nd["cy"]) for nd in node_data[:1]]  # right of start to left of first node
    )
    # Rebuild properly
    src_pts = [(start_cx + EVT_R, start_cy)] + [(nd["cx"] + NODE_W // 2, nd["cy"]) for nd in node_data]
    dst_pts = [(nd["cx"] - NODE_W // 2, nd["cy"]) for nd in node_data] + [(end_cx - EVT_R, end_cy)]

    for (x1, y1), (x2, y2) in zip(src_pts, dst_pts):
        if abs(y1 - y2) < 3:
            parts.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="#94a3b8" stroke-width="1.5" marker-end="url(#sa-{cid})"/>'
            )
        else:
            mx = (x1 + x2) // 2
            parts.append(
                f'<polyline points="{x1},{y1} {mx},{y1} {mx},{y2} {x2},{y2}" '
                f'fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#sa-{cid})"/>'
            )

    # ── Task nodes (rendered after edges so they sit on top) ─────────────
    for nd in node_data:
        cx, cy = nd["cx"], nd["cy"]
        st = nd["st"]
        nx, ny = cx - NODE_W // 2, cy - NODE_H // 2
        action = st.get("action", "")
        num = nd["j"] + 1

        # Soft shadow
        parts.append(
            f'<rect x="{nx + 2}" y="{ny + 2}" width="{NODE_W}" height="{NODE_H}" '
            f'rx="6" fill="#e8edf2" stroke="none"/>'
        )
        # Card
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="{NODE_W}" height="{NODE_H}" '
            f'rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5"/>'
        )
        # Dark green left accent bar
        parts.append(
            f'<rect x="{nx}" y="{ny + 8}" width="4" height="{NODE_H - 16}" rx="2" fill="#166534"/>'
        )
        # Step number badge, floated at the card's top-right corner.
        # Clamp it inside the card when the float would cross the lane above.
        badge_cx = nx + NODE_W + 6
        badge_cy = ny - 6
        lane_top = nd["cy"] - LANE_H // 2
        if badge_cy - 10 < lane_top + 4:
            badge_cx = nx + NODE_W - 13
            badge_cy = ny + 13
        parts.append(f'<circle cx="{badge_cx}" cy="{badge_cy}" r="10" fill="#0f1825"/>')
        parts.append(
            f'<text x="{badge_cx}" y="{badge_cy + 4}" text-anchor="middle" '
            f'font-size="9" font-weight="700" fill="#ffffff" font-family="Inter,monospace">{num}</text>'
        )
        # Action text, 2 lines max, full card width now badge is outside
        words = action.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if len(test) <= 22:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = w
            if len(lines) == 2: break
        if cur and len(lines) < 2: lines.append(cur)
        if not lines: lines = [action[:22]]
        t0 = cy - (len(lines) * 15) // 2 + 7
        for li2, ln in enumerate(lines[:2]):
            parts.append(
                f'<text x="{cx}" y="{t0 + li2 * 15}" text-anchor="middle" '
                f'font-size="11" font-weight="500" fill="#1e293b" font-family="Inter,sans-serif">{escape(ln)}</text>'
            )
        # Transparent click target, encodes full step data for modal
        inputs_enc  = escape(" | ".join(st.get("inputs",  [])[:4]))
        outputs_enc = escape(" | ".join(st.get("outputs", [])[:4]))
        notes_enc   = escape((st.get("notes") or "")[:300])
        action_enc  = escape(action)
        sid_enc     = escape(st.get("step_id", f"TS-{num:02d}"))
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="{NODE_W}" height="{NODE_H}" rx="6" '
            f'fill="transparent" style="cursor:pointer" '
            f'data-sid="{sid_enc}" data-action="{action_enc}" '
            f'data-inputs="{inputs_enc}" data-outputs="{outputs_enc}" data-notes="{notes_enc}" '
            f'onclick="apgBpmnStep(this)"/>'
        )

    # ── Start event ───────────────────────────────────────────────────────
    parts.append(
        f'<circle cx="{start_cx}" cy="{start_cy}" r="{EVT_R}" '
        f'fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>'
        f'<text x="{start_cx}" y="{start_cy + EVT_R + 12}" text-anchor="middle" '
        f'font-size="8" font-weight="600" fill="#94a3b8" '
        f'font-family="Inter,sans-serif">Start</text>'
    )

    # ── End event ─────────────────────────────────────────────────────────
    parts.append(
        f'<circle cx="{end_cx}" cy="{end_cy}" r="{EVT_R}" '
        f'fill="#fee2e2" stroke="#dc2626" stroke-width="3"/>'
    )
    parts.append(
        f'<circle cx="{end_cx}" cy="{end_cy}" r="{EVT_R - 4}" '
        f'fill="none" stroke="#dc2626" stroke-width="1.5"/>'
        f'<text x="{end_cx}" y="{end_cy + EVT_R + 12}" text-anchor="middle" '
        f'font-size="8" font-weight="600" fill="#94a3b8" '
        f'font-family="Inter,sans-serif">End</text>'
    )

    # ── Message flows (dashed, cross-lane data transfers) ─────────────────
    # Every cross-lane flow gets its own distinct anchor (see pre-pass). The
    # chip is a short, clickable label; full data + method open in a modal.
    for v in flow_layout:
        fl    = v["fl"]
        msg_x = v["x"]
        fy = lane_cy[v["f_li"]]
        ty = lane_cy[v["t_li"]]
        going_down = ty > fy
        y1 = fy + (EVT_R if going_down else -EVT_R)
        y2 = ty + (-EVT_R if going_down else EVT_R)

        parts.append(
            f'<line x1="{msg_x}" y1="{y1}" x2="{msg_x}" y2="{y2}" '
            f'stroke="#166534" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#ma-{cid})"/>'
        )
        parts.append(
            f'<circle cx="{msg_x}" cy="{y1}" r="4" fill="white" stroke="#166534" stroke-width="1.5"/>'
        )

        raw_lbl = fl.get("data", "") or ""
        method  = fl.get("method", "") or ""
        short   = _flow_short(raw_lbl)
        lw      = _chip_w(raw_lbl)
        lx      = msg_x - lw // 2          # centred on the dashed connector
        lyc     = (y1 + y2) // 2

        d_from   = escape((fl.get("from_tool", "") or "").split("(")[0].strip())
        d_to     = escape((fl.get("to_tool", "") or "").split("(")[0].strip())
        d_data   = escape(raw_lbl)
        d_method = escape(method)

        parts.append(
            f'<g class="apg-flow" style="cursor:pointer" '
            f'data-from="{d_from}" data-to="{d_to}" '
            f'data-data="{d_data}" data-method="{d_method}" '
            f'onclick="apgBpmnFlow(this)">'
            f'<rect class="apg-flow-box" x="{lx}" y="{lyc - 9}" width="{lw}" height="18" '
            f'rx="4" fill="#f0fdf4" stroke="#166534" stroke-width="1"/>'
            f'<text x="{lx + lw // 2}" y="{lyc + 4}" text-anchor="middle" font-size="9" '
            f'font-weight="500" fill="#166534" font-family="Inter,sans-serif" '
            f'style="pointer-events:none">{escape(short)}</text>'
            f'</g>'
        )

    # ── Legend (dedicated strip below the lanes) ──────────────────────────
    strip_y = n_lanes * LANE_H
    parts.append(
        f'<line x1="0" y1="{strip_y}" x2="{total_w}" y2="{strip_y}" stroke="#cbd5e1" stroke-width="1"/>'
        f'<rect x="0" y="{strip_y}" width="{total_w}" height="{LEGEND_H}" fill="#f8fafc"/>'
    )
    lgy = strip_y + LEGEND_H // 2
    lgx = max(LABEL_W + 14, total_w - 320)
    parts.append(
        f'<circle cx="{lgx}" cy="{lgy}" r="6" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>'
        f'<text x="{lgx + 11}" y="{lgy + 4}" font-size="9" fill="#64748b" font-family="Inter,sans-serif">Start</text>'
        f'<circle cx="{lgx + 56}" cy="{lgy}" r="6" fill="#fee2e2" stroke="#dc2626" stroke-width="2.5"/>'
        f'<text x="{lgx + 67}" y="{lgy + 4}" font-size="9" fill="#64748b" font-family="Inter,sans-serif">End</text>'
        f'<rect x="{lgx + 104}" y="{lgy - 7}" width="20" height="14" rx="3" fill="white" stroke="#e2e8f0" stroke-width="1.5"/>'
        f'<rect x="{lgx + 104}" y="{lgy - 3}" width="4" height="6" rx="1" fill="#166534"/>'
        f'<text x="{lgx + 129}" y="{lgy + 4}" font-size="9" fill="#64748b" font-family="Inter,sans-serif">Task (click)</text>'
        f'<rect x="{lgx + 196}" y="{lgy - 8}" width="34" height="16" rx="4" fill="#f0fdf4" stroke="#166534" stroke-width="1"/>'
        f'<text x="{lgx + 238}" y="{lgy + 4}" font-size="9" fill="#64748b" font-family="Inter,sans-serif">Data flow (click)</text>'
    )

    defs = (
        f'<defs>'
        f'<marker id="sa-{cid}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto">'
        f'<polygon points="0 0, 9 3.5, 0 7" fill="#94a3b8"/></marker>'
        f'<marker id="ma-{cid}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto">'
        f'<polygon points="0 0, 9 3.5, 0 7" fill="#166534"/></marker>'
        f'</defs>'
    )

    return (
        f'<div style="overflow-x:auto;border:1px solid #e2e8f0;border-radius:8px;'
        f'margin-bottom:16px;background:#fafafa;padding:0">'
        f'<svg viewBox="0 0 {total_w} {total_h}" width="{total_w}" height="{total_h}" '
        f'style="display:block;min-width:400px" xmlns="http://www.w3.org/2000/svg">'
        + defs + "".join(parts) +
        f'</svg></div>'
    )


def _render_tech_appendix_html(changes: list) -> str:
    """Render the Technical Appendix expandable section for the client website.

    For each proposed_change that has a technical_spec object, renders:
    - A BPMN swim-lane diagram showing tool lanes and data flows
    - Implementation phases table
    - Integration points with clickable API doc links
    - Acceptance criteria checklist
    """
    tech_changes = [c for c in changes if c.get("technical_spec")]
    if not tech_changes:
        return ""

    entries = []
    for c in tech_changes:
        cid = escape(c.get("change_id", ""))
        title = escape(c.get("title", cid))
        ts = c.get("technical_spec", {})
        swim = ts.get("swim_lanes", {})
        tools = swim.get("tools", [])
        flows = swim.get("flows", [])
        steps = ts.get("implementation_steps", [])
        phases = ts.get("phases", [])
        integrations = ts.get("integration_points", [])
        criteria = ts.get("acceptance_criteria", [])

        swim_svg = _build_bpmn_svg(ts, cid)

        # ── Phases table ──────────────────────────────────────────────────────
        phases_html = ""
        if phases:
            rows = []
            for ph in phases:
                ph_num = escape(str(ph.get("phase", "")))
                ph_label = escape(ph.get("label", ""))
                ph_dur = escape(ph.get("duration", ""))
                ph_tasks = ph.get("tasks", [])
                task_list = "".join(f'<li style="margin:2px 0;font-size:12px;color:#374151">{escape(t)}</li>' for t in ph_tasks)
                rows.append(
                    f'<tr>'
                    f'<td style="padding:10px 12px;font-weight:700;color:{APG_DARK};white-space:nowrap">Phase {ph_num}</td>'
                    f'<td style="padding:10px 12px;font-weight:600;color:#374151">{ph_label}</td>'
                    f'<td style="padding:10px 12px;color:{APG_GREY};white-space:nowrap">{ph_dur}</td>'
                    f'<td style="padding:10px 12px"><ul style="margin:0;padding-left:16px">{task_list}</ul></td>'
                    f'</tr>'
                )
            phases_html = (
                f'<h5 style="font-size:13px;font-weight:700;color:{APG_DARK};margin:20px 0 8px">Implementation Phases</h5>'
                '<table style="width:100%;border-collapse:collapse;font-size:13px">'
                f'<thead><tr style="background:#f8fafc">'
                f'<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:{APG_GREY};border-bottom:2px solid #e2e8f0">Phase</th>'
                f'<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:{APG_GREY};border-bottom:2px solid #e2e8f0">Name</th>'
                f'<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:{APG_GREY};border-bottom:2px solid #e2e8f0">Duration</th>'
                f'<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:{APG_GREY};border-bottom:2px solid #e2e8f0">Tasks</th>'
                '</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody>'
                '</table>'
            )

        # ── Integration points ─────────────────────────────────────────────────
        integ_html = ""
        if integrations:
            cards = []
            for ip in integrations:
                tool_name = escape(ip.get("tool", ""))
                method = escape(ip.get("method", ""))
                notes = escape(ip.get("notes", ""))
                docs_url = ip.get("docs_url", "")
                docs_btn = (
                    f'<a href="{escape(docs_url)}" target="_blank" rel="noopener" '
                    f'style="display:inline-block;margin-top:8px;font-size:11px;font-weight:600;color:{APG_LIME_TEXT};text-decoration:none;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:4px;padding:3px 8px">'
                    f'&#128196; API Docs</a>'
                ) if docs_url else ""
                cards.append(
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px">'
                    f'<div style="font-size:13px;font-weight:700;color:{APG_DARK}">{tool_name}</div>'
                    f'<div style="font-size:12px;color:{APG_GREY};margin-top:2px">{method}</div>'
                    + (f'<div style="font-size:12px;color:#374151;margin-top:4px">{notes}</div>' if notes else '')
                    + docs_btn
                    + '</div>'
                )
            integ_html = (
                f'<h5 style="font-size:13px;font-weight:700;color:{APG_DARK};margin:20px 0 8px">Integration Points</h5>'
                f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px">{"".join(cards)}</div>'
            )

        # ── Acceptance criteria ────────────────────────────────────────────────
        crit_html = ""
        if criteria:
            items = "".join(
                f'<li style="padding:6px 0;font-size:13px;color:#374151;border-bottom:1px solid #f1f5f9">'
                f'<span style="color:{APG_LIME_TEXT};font-weight:600;margin-right:6px">&#10003;</span>{escape(cr)}</li>'
                for cr in criteria
            )
            crit_html = (
                f'<h5 style="font-size:13px;font-weight:700;color:{APG_DARK};margin:20px 0 8px">Acceptance Criteria</h5>'
                f'<ul style="list-style:none;margin:0;padding:0;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden">{items}</ul>'
            )

        entries.append(
            f'<div id="tech-{cid}" style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:24px;margin-bottom:20px">'
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">'
            f'<span style="background:{APG_DARK};color:{APG_LIME};font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px;font-family:monospace">{cid}</span>'
            f'<h4 style="margin:0;font-size:16px;font-weight:700;color:{APG_DARK}">{title}</h4>'
            f'</div>'
            + (f'<div style="margin-bottom:16px">{swim_svg}</div>' if swim_svg else '')
            + phases_html
            + integ_html
            + crit_html
            + '</div>'
        )

    modal_html = (
        '<div id="bpmn-step-modal" style="display:none;position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.55);'
        'align-items:center;justify-content:center" onclick="if(event.target===this)apgBpmnClose()">'
        '<div style="background:#fff;border-radius:14px;width:min(520px,92vw);max-height:82vh;overflow-y:auto;'
        'box-shadow:0 20px 60px rgba(0,0,0,0.3);padding:28px 28px 24px;position:relative">'
        '<button onclick="apgBpmnClose()" style="position:absolute;top:14px;right:16px;background:none;border:none;'
        'font-size:20px;color:#94a3b8;cursor:pointer;line-height:1" title="Close">&times;</button>'
        '<div id="bpmn-modal-sid" style="display:inline-block;background:#0f1825;color:#fff;'
        'font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px;font-family:monospace;margin-bottom:12px"></div>'
        '<h3 id="bpmn-modal-action" style="margin:0 0 16px;font-size:16px;font-weight:700;color:#0f1825;'
        'padding-right:24px;line-height:1.4"></h3>'
        '<div id="bpmn-modal-inputs" style="margin-bottom:12px"></div>'
        '<div id="bpmn-modal-outputs" style="margin-bottom:12px"></div>'
        '<div id="bpmn-modal-notes"></div>'
        '</div></div>'
        '<style>.apg-flow .apg-flow-box{transition:fill .12s ease,stroke-width .12s ease}'
        '.apg-flow:hover .apg-flow-box{fill:#dcfce7;stroke-width:1.7}</style>'
        '<div id="bpmn-flow-modal" style="display:none;position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.55);'
        'align-items:center;justify-content:center" onclick="if(event.target===this)apgBpmnClose()">'
        '<div style="background:#fff;border-radius:14px;width:min(520px,92vw);max-height:82vh;overflow-y:auto;'
        'box-shadow:0 20px 60px rgba(0,0,0,0.3);padding:28px 28px 24px;position:relative">'
        '<button onclick="apgBpmnClose()" style="position:absolute;top:14px;right:16px;background:none;border:none;'
        'font-size:20px;color:#94a3b8;cursor:pointer;line-height:1" title="Close">&times;</button>'
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;flex-wrap:wrap;padding-right:24px">'
        '<span id="bpmn-flow-from" style="background:#0f1825;color:#fff;font-size:11px;font-weight:700;'
        'padding:5px 11px;border-radius:5px"></span>'
        '<span style="color:#166534;font-size:16px;font-weight:700;line-height:1">&#8594;</span>'
        '<span id="bpmn-flow-to" style="background:#166534;color:#fff;font-size:11px;font-weight:700;'
        'padding:5px 11px;border-radius:5px"></span>'
        '</div>'
        '<div id="bpmn-flow-data" style="margin-bottom:12px"></div>'
        '<div id="bpmn-flow-method"></div>'
        '</div></div>'
        '<script>'
        'function apgBpmnStep(el){'
        '  var sid=el.getAttribute("data-sid")||"",'
        '      action=el.getAttribute("data-action")||"",'
        '      inp=(el.getAttribute("data-inputs")||"").split(" | ").filter(Boolean),'
        '      out=(el.getAttribute("data-outputs")||"").split(" | ").filter(Boolean),'
        '      notes=el.getAttribute("data-notes")||"",'
        '      m=document.getElementById("bpmn-step-modal");'
        '  document.getElementById("bpmn-modal-sid").textContent=sid;'
        '  document.getElementById("bpmn-modal-action").textContent=action;'
        '  var inEl=document.getElementById("bpmn-modal-inputs");'
        '  inEl.innerHTML=inp.length?'
        '    "<div style=\'font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;letter-spacing:.05em;margin-bottom:4px\'>Inputs</div>"'
        '    +"<ul style=\'margin:0;padding-left:18px\'>"+inp.map(function(x){'
        '      return "<li style=\'font-size:13px;color:#374151;margin:2px 0\'>"+(x)+"</li>";}).join("")+"</ul>":"";'
        '  var outEl=document.getElementById("bpmn-modal-outputs");'
        '  outEl.innerHTML=out.length?'
        '    "<div style=\'font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;letter-spacing:.05em;margin-bottom:4px;margin-top:10px\'>Outputs</div>"'
        '    +"<ul style=\'margin:0;padding-left:18px\'>"+out.map(function(x){'
        '      return "<li style=\'font-size:13px;color:#374151;margin:2px 0\'>"+(x)+"</li>";}).join("")+"</ul>":"";'
        '  var notEl=document.getElementById("bpmn-modal-notes");'
        '  notEl.innerHTML=notes'
        '    ?"<div style=\'font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;letter-spacing:.05em;margin-bottom:4px;margin-top:10px\'>Notes</div>"'
        '     +"<p style=\'margin:0;font-size:13px;color:#374151;line-height:1.5\'>"+notes+"</p>":"";'
        '  m.style.display="flex";'
        '}'
        'function apgBpmnFlow(el){'
        '  var f=el.getAttribute("data-from")||"",t=el.getAttribute("data-to")||"",'
        '      d=el.getAttribute("data-data")||"",mth=el.getAttribute("data-method")||"";'
        '  document.getElementById("bpmn-flow-from").textContent=f||"Source";'
        '  document.getElementById("bpmn-flow-to").textContent=t||"Target";'
        '  var dEl=document.getElementById("bpmn-flow-data");'
        '  dEl.innerHTML="<div style=\'font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;letter-spacing:.05em;margin-bottom:4px\'>Data transferred</div>";'
        '  var dp=document.createElement("p");'
        '  dp.setAttribute("style","margin:0;font-size:13px;color:#374151;line-height:1.5");'
        '  dp.textContent=d||"Not specified";dEl.appendChild(dp);'
        '  var mEl=document.getElementById("bpmn-flow-method");'
        '  if(mth){'
        '    mEl.innerHTML="<div style=\'font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;letter-spacing:.05em;margin-bottom:4px;margin-top:10px\'>Method</div>";'
        '    var mp=document.createElement("p");'
        '    mp.setAttribute("style","margin:0;font-size:13px;color:#374151;line-height:1.5");'
        '    mp.textContent=mth;mEl.appendChild(mp);'
        '  }else{mEl.innerHTML="";}'
        '  document.getElementById("bpmn-flow-modal").style.display="flex";'
        '}'
        'function apgBpmnClose(){'
        '  document.getElementById("bpmn-step-modal").style.display="none";'
        '  document.getElementById("bpmn-flow-modal").style.display="none";'
        '}'
        'document.addEventListener("keydown",function(e){if(e.key==="Escape")apgBpmnClose();});'
        '</script>'
    )

    return (
        f'<section id="tech-appendix" style="padding:48px 24px;max-width:900px;margin:0 auto">'
        f'<details>'
        f'<summary style="cursor:pointer;list-style:none;display:flex;align-items:center;gap:12px;padding:16px 20px;'
        f'background:{APG_DARK};border-radius:12px;color:#fff;font-size:15px;font-weight:700;user-select:none">'
        f'<span style="color:{APG_LIME};font-size:18px">&#43;</span>'
        f'Technical Appendix'
        f'<span style="margin-left:auto;font-size:11px;font-weight:400;color:#94a3b8">'
        f'{len(tech_changes)} solution{"s" if len(tech_changes) != 1 else ""} with implementation detail</span>'
        f'</summary>'
        f'<div style="margin-top:20px">{"".join(entries)}</div>'
        f'</details>'
        + modal_html
        + f'</section>'
    )


# ─── Client Website Generator ──────────────────────────────────────────────────

def generate_client_website(ssad: dict, sections: dict = None) -> str:
    company = escape(ssad.get("company_name", "Client"))
    industry = escape(ssad.get("industry_tag", ""))
    generated = datetime.now().strftime("%d %b %Y")

    # Section unlock flags from clients.json (or fallback to all-locked)
    if sections is None:
        sections = {
            "process_map": False, "findings": False, "waste": False,
            "priority_matrix": False, "review": False, "transformation": False, "prototype": False,
        }
    sections_json = json.dumps(sections)

    # Pre-render transformation blueprint summary
    proposed_changes = ssad.get("proposed_changes", [])
    processes = ssad.get("processes", [])
    blueprint_data = ssad.get("transformation_blueprint", {})
    # Stats for blueprint summary
    _bp_actionable_types = {"step", "pain", "decision", "parallel_group"}
    total_steps = sum(len([s for s in p.get("steps", []) if not s.get("branch_only") and s.get("type", "step") in _bp_actionable_types]) for p in processes)
    _bp_eliminated = sum(1 for c in proposed_changes if c.get("change_type") == "eliminate")
    _bp_automated = sum(1 for c in proposed_changes if c.get("change_type") == "automate")
    _bp_consolidated_saved = sum(max(len(c.get("affected_step_ids", [])) - 1, 0) for c in proposed_changes if c.get("change_type") == "consolidate")
    steps_after = max(total_steps - _bp_eliminated - _bp_automated - _bp_consolidated_saved, 0)
    total_hrs_saved = sum((w.get("hours_per_week") or 0) * max(w.get("headcount_affected") or 1, 1) for w in ssad.get("waste_items", []))
    total_annual_value = sum(((c.get("value") or {}).get("combined_annual_value_aud", 0) or 0) for c in proposed_changes)
    bp_phases = blueprint_data.get("phases", [])
    blueprint_stats_html = f"""<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-bottom:20px">
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:22px;font-weight:800;color:{APG_DARK}">{total_steps} &rarr; {steps_after}</div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:{APG_GREY}">Steps</div>
      </div>
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:22px;font-weight:800;color:{APG_DARK}">{total_hrs_saved:.0f} hrs/wk</div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:{APG_GREY}">Time saved</div>
      </div>
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:22px;font-weight:800;color:{APG_DARK}">${total_annual_value:,.0f}</div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:{APG_GREY}">Annual run rate</div>
      </div>
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:22px;font-weight:800;color:{APG_DARK}">{len(bp_phases) or len(proposed_changes)}</div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:{APG_GREY}">{"Phases" if bp_phases else "Changes"}</div>
      </div>
    </div>"""
    # Phase timeline (if blueprint has been built)
    bp_phase_html = ""
    if bp_phases:
        phase_items = []
        for ph in bp_phases:
            ph_label = escape(ph.get("label", f"Phase {ph.get('phase_number', '?')}"))
            ph_time = escape(ph.get("timeframe", ""))
            ph_count = len(ph.get("change_ids", []))
            phase_items.append(f'<div style="flex:1;background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:12px;text-align:center;min-width:120px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;color:{APG_LIME_TEXT};letter-spacing:0.06em">Phase {ph.get("phase_number","")}</div><div style="font-size:14px;font-weight:800;color:{APG_DARK}">{ph_label}</div><div style="font-size:10px;color:{APG_GREY}">{ph_time} &middot; {ph_count} changes</div></div>')
        bp_phase_html = f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px">{"".join(phase_items)}</div>'
    # ── Pre-render cumulative savings chart + Gantt for transformation section ──
    import math as _math
    savings_gantt_html = ""
    chart_tip_json = "[]"
    enriched_changes = [c for c in proposed_changes if c.get("value", {}).get("combined_annual_value_aud") is not None
                        and c.get("implementation", {}).get("weeks_estimate") is not None]
    if enriched_changes:
        # ── 5-month compressed schedule: front-load quick wins into M1-M2 ──
        NUM_MONTHS = 5
        sorted_changes = sorted(enriched_changes, key=lambda c: c["implementation"]["weeks_estimate"])

        # Split into quick wins (<=1 week) and core (>1 week)
        quick_items = [c for c in sorted_changes if c["implementation"]["weeks_estimate"] <= 1]
        core_items = [c for c in sorted_changes if c["implementation"]["weeks_estimate"] > 1]

        change_schedule = []
        # Quick wins: pack into M1 and M2, each takes 1 month
        for i, c in enumerate(quick_items):
            start = 0 if i < len(quick_items) // 2 else 1
            change_schedule.append({
                "cid": escape(c.get("change_id", "")),
                "title": escape(c.get("title", "")),
                "start": start,
                "end": start + 1,
                "monthly_value": c["value"]["combined_annual_value_aud"] / 12,
                "annual_value": c["value"]["combined_annual_value_aud"],
                "weeks": c["implementation"]["weeks_estimate"],
                "horizon": 1,
            })

        # Core items: spread across M2-M5 with duration based on weeks
        core_start = 1  # Start from M2
        for i, c in enumerate(core_items):
            weeks = c["implementation"]["weeks_estimate"]
            duration_months = max(1, min(3, _math.ceil(weeks / 2)))
            start = min(core_start, NUM_MONTHS - 1)
            end = min(start + duration_months, NUM_MONTHS)
            change_schedule.append({
                "cid": escape(c.get("change_id", "")),
                "title": escape(c.get("title", "")),
                "start": start,
                "end": end,
                "monthly_value": c["value"]["combined_annual_value_aud"] / 12,
                "annual_value": c["value"]["combined_annual_value_aud"],
                "weeks": weeks,
                "horizon": 2 if weeks <= 4 else 3,
            })
            core_start = start + max(1, duration_months // 2)
            if core_start >= NUM_MONTHS:
                core_start = NUM_MONTHS - 1

        # Compute cumulative savings: M1-M5 rollout, M6-M12 at full run rate
        CHART_MONTHS = 12
        monthly_cumulative = []
        cumulative = 0.0
        # M1-M5: staggered rollout
        for m in range(NUM_MONTHS):
            active_monthly = sum(cs["monthly_value"] for cs in change_schedule if cs["end"] <= m + 1)
            cumulative += active_monthly
            monthly_cumulative.append(round(cumulative / 1000, 1))
        # M6-M12: full monthly run rate (all items live)
        full_monthly_rate = total_annual_value / 12
        for m in range(NUM_MONTHS, CHART_MONTHS):
            cumulative += full_monthly_rate
            monthly_cumulative.append(round(cumulative / 1000, 1))

        max_cum = max(monthly_cumulative) if monthly_cumulative else 1
        final_cum = monthly_cumulative[-1] if monthly_cumulative else 0
        rollout_cum = monthly_cumulative[NUM_MONTHS - 1] if len(monthly_cumulative) >= NUM_MONTHS else 0

        # ── SVG Area Chart (12 months) ──
        SVG_W, SVG_H = 600, 220
        PAD_L, PAD_R, PAD_T, PAD_B = 50, 20, 10, 30
        chart_w = SVG_W - PAD_L - PAD_R
        chart_h = SVG_H - PAD_T - PAD_B

        def cx(month_idx):
            return PAD_L + (month_idx / (CHART_MONTHS - 1)) * chart_w

        def cy(val):
            if max_cum == 0:
                return PAD_T + chart_h
            return PAD_T + chart_h - (val / max_cum) * chart_h

        # Grid lines
        grid_svg = ""
        y_ticks = [v for v in [5, 10, 25, 50, 100, 200, 500] if v <= max_cum * 1.1]
        if not y_ticks:
            y_ticks = [max(1, round(max_cum / 2))]
        for yv in y_ticks:
            gy = cy(yv)
            grid_svg += f'<line x1="{PAD_L}" y1="{gy:.0f}" x2="{SVG_W - PAD_R}" y2="{gy:.0f}" stroke="{APG_BORDER}" stroke-width="1"/>'
            grid_svg += f'<text x="{PAD_L - 6}" y="{gy:.0f}" text-anchor="end" dominant-baseline="middle" font-size="10" fill="{APG_GREY}">${int(yv)}K</text>'

        # X-axis month labels
        x_labels = ""
        for i in range(CHART_MONTHS):
            x_labels += f'<text x="{cx(i):.0f}" y="{SVG_H - 8}" text-anchor="middle" font-size="10" fill="{APG_GREY}">M{i+1}</text>'

        # Solid area path (M1-M5 rollout)
        rollout_points = " ".join(f"{cx(i):.1f},{cy(monthly_cumulative[i]):.1f}" for i in range(NUM_MONTHS))
        rollout_bottom = f"{cx(NUM_MONTHS - 1):.1f},{PAD_T + chart_h} {cx(0):.1f},{PAD_T + chart_h}"

        # Projected area path (M5-M12 dashed)
        proj_points = " ".join(f"{cx(i):.1f},{cy(monthly_cumulative[i]):.1f}" for i in range(NUM_MONTHS - 1, CHART_MONTHS))
        proj_bottom = f"{cx(CHART_MONTHS - 1):.1f},{PAD_T + chart_h} {cx(NUM_MONTHS - 1):.1f},{PAD_T + chart_h}"

        # Vertical separator at M5
        sep_x = cx(NUM_MONTHS - 1)
        separator_svg = f'<line x1="{sep_x:.1f}" y1="{PAD_T}" x2="{sep_x:.1f}" y2="{PAD_T + chart_h}" stroke="{APG_GREY}" stroke-width="1" stroke-dasharray="4 3" opacity="0.5"/>'
        separator_svg += f'<text x="{(cx(0) + sep_x) / 2:.0f}" y="{PAD_T + 14}" text-anchor="middle" font-size="9" fill="{APG_GREY}" font-weight="600">ROLLOUT</text>'
        separator_svg += f'<text x="{(sep_x + cx(CHART_MONTHS - 1)) / 2:.0f}" y="{PAD_T + 14}" text-anchor="middle" font-size="9" fill="{APG_GREY}" font-weight="600">FULL RUN RATE</text>'

        # Pre-compute per-month breakdown for tooltip
        month_breakdown = []
        for m in range(CHART_MONTHS):
            if m < NUM_MONTHS:
                live_this_month = [cs for cs in change_schedule if cs["end"] == m + 1]
                lines = []
                for cs in live_this_month:
                    v = f"${cs['annual_value']/1000:.0f}k/yr" if cs["annual_value"] >= 1000 else f"${cs['annual_value']:,.0f}/yr"
                    lines.append(f"{cs['title']}: {v}")
                month_breakdown.append(lines)
            else:
                month_breakdown.append(["All items live \u2014 full run rate"])

        # Build SVG dots for all 12 months
        dots_svg = ""
        import json as _json
        chart_tip_data = []
        for i in range(CHART_MONTHS):
            dot_cx = cx(i)
            dot_cy = cy(monthly_cumulative[i])
            chart_tip_data.append({
                "month": f"M{i+1}",
                "cumulative": f"${monthly_cumulative[i]:.0f}K cumulative",
                "items": month_breakdown[i],
            })
            is_projected = i >= NUM_MONTHS
            dot_fill = "#7DFF00" if not is_projected else f"{APG_GREY}"
            dot_stroke = "#ffffff"
            dots_svg += f"""<circle cx="{dot_cx:.1f}" cy="{dot_cy:.1f}" r="{'4' if is_projected else '5'}" fill="{dot_fill}" stroke="{dot_stroke}" stroke-width="2"
              style="cursor:pointer;transition:r 0.15s"
              onmouseenter="this.setAttribute('r','8');showChartDot(this,{i})"
              onmouseleave="this.setAttribute('r','{'4' if is_projected else '5'}');hideChartTip()"/>
            """
        chart_tip_json = _json.dumps(chart_tip_data)

        area_chart_svg = f"""<div style="position:relative">
          <svg viewBox="0 0 {SVG_W} {SVG_H}" style="width:100%;height:auto;display:block">
          <defs>
            <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#7DFF00" stop-opacity="0.25"/>
              <stop offset="100%" stop-color="#7DFF00" stop-opacity="0.03"/>
            </linearGradient>
            <linearGradient id="sg-proj" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#7DFF00" stop-opacity="0.10"/>
              <stop offset="100%" stop-color="#7DFF00" stop-opacity="0.01"/>
            </linearGradient>
          </defs>
          {grid_svg}
          <line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{PAD_T + chart_h}" stroke="{APG_BORDER}" stroke-width="1"/>
          <line x1="{PAD_L}" y1="{PAD_T + chart_h}" x2="{SVG_W - PAD_R}" y2="{PAD_T + chart_h}" stroke="{APG_BORDER}" stroke-width="1"/>
          <polygon points="{rollout_points} {rollout_bottom}" fill="url(#sg)"/>
          <polygon points="{proj_points} {proj_bottom}" fill="url(#sg-proj)"/>
          <polyline points="{rollout_points}" fill="none" stroke="#7DFF00" stroke-width="2.5" stroke-linejoin="round"/>
          <polyline points="{proj_points}" fill="none" stroke="#7DFF00" stroke-width="2" stroke-linejoin="round" stroke-dasharray="6 4"/>
          {separator_svg}
          {dots_svg}
          {x_labels}
        </svg>
        <div id="chart-tip" style="display:none;position:absolute;pointer-events:none;background:{APG_DARK};color:#fff;
             border-radius:8px;padding:10px 14px;font-size:12px;z-index:100;max-width:300px;box-shadow:0 4px 12px rgba(0,0,0,0.3)"></div>
        </div>"""

        # ── Gantt Timeline (5 months) ──
        h1 = [cs for cs in change_schedule if cs["horizon"] == 1]
        h2 = [cs for cs in change_schedule if cs["horizon"] == 2]
        h3 = [cs for cs in change_schedule if cs["horizon"] == 3]
        gantt_horizons = [
            ("Horizon 1, Quick Wins", h1, "1"),
            ("Horizon 2, Core Platform", h2, "0.7"),
            ("Horizon 3, Growth Engine", h3, "0.4"),
        ]

        month_headers = "".join(f'<div style="text-align:center;font-size:10px;color:{APG_GREY};font-family:monospace">M{i+1}</div>' for i in range(NUM_MONTHS))
        gantt_rows = ""
        for label, items, opacity in gantt_horizons:
            if not items:
                continue
            gantt_rows += f'<div style="font-size:11px;font-weight:700;color:{APG_LIME_TEXT};text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 8px 0">{label}</div>'
            for item in items:
                cid = item["cid"]
                title = item["title"]
                val_label = f"${item['annual_value']/1000:.0f}k/yr" if item["annual_value"] >= 1000 else f"${item['annual_value']:,.0f}/yr"
                cells = ""
                for mi in range(NUM_MONTHS):
                    if mi >= item["start"] and mi < item["end"]:
                        cells += f'<div style="height:24px;padding:0 1px"><div onclick="openModal(&quot;{cid}&quot;)" style="height:100%;background:{APG_LIME};opacity:{opacity};border-radius:2px;cursor:pointer" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity={opacity}"></div></div>'
                    else:
                        cells += '<div style="height:24px"></div>'
                name_html = (
                    f'<span onclick="openModal(&quot;{cid}&quot;)" '
                    f'style="cursor:pointer;border-bottom:1px dashed {APG_BORDER};padding-bottom:1px" '
                    f'onmouseover="this.style.color=&quot;{APG_LIME_TEXT}&quot;" '
                    f'onmouseout="this.style.color=&quot;{APG_GREY}&quot;">'
                    f'{title}</span> <span style="font-size:10px;font-weight:700;color:{APG_LIME_TEXT}">{val_label}</span>'
                )
                gantt_rows += f'<div style="display:grid;grid-template-columns:240px repeat({NUM_MONTHS},1fr);gap:0;margin-bottom:4px;align-items:center"><div style="font-size:12px;color:{APG_GREY};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:8px">{name_html}</div>{cells}</div>'

        savings_gantt_html = f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:24px 28px;margin-top:24px">
          <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:{APG_GREY};margin-bottom:16px">Cumulative Savings ($K)</div>
          {area_chart_svg}
          <div style="display:flex;justify-content:flex-end;margin-top:8px;align-items:baseline">
            <span style="font-size:18px;font-weight:800;color:var(--lime-text)">${final_cum:.0f}K</span>
            <span style="font-size:13px;color:{APG_GREY};margin-left:4px">projected Year 1 total</span>
          </div>
        </div>
        <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:24px 28px;margin-top:16px;overflow-x:auto">
          <div style="display:grid;grid-template-columns:240px repeat({NUM_MONTHS},1fr);gap:0;margin-bottom:12px">
            <div></div>{month_headers}
          </div>
          {gantt_rows}
        </div>"""

    savings_gantt_js = savings_gantt_html.replace("'", "\\'").replace("\n", " ")

    # Escape for JS embedding (single quotes, newlines)
    blueprint_content_js = (blueprint_stats_html + bp_phase_html + savings_gantt_html).replace("'", "\\'").replace("\n", " ")

    # ── Pre-render quadrant priority matrix for embedding (grouped by process area) ──
    pm_quadrant_html, pm_modals_html = _render_quadrant_matrix(ssad, enriched_changes)

    pm_quadrant_js = pm_quadrant_html.replace("'", "\\'").replace("\n", " ")

    # Format audit start date from "2026-03-12" to "12 Mar 2026"
    raw_start = ssad.get("audit_start_date", "")
    if raw_start:
        try:
            audit_start_display = datetime.strptime(raw_start, "%Y-%m-%d").strftime("%d %b %Y")
        except ValueError:
            audit_start_display = escape(raw_start)
    else:
        audit_start_display = generated

    sessions = ssad.get("sessions", [])
    # Deduplicate waste_items by waste_id (must match waste.html logic)
    _raw_waste = ssad.get("waste_items", [])
    _seen_wids: set = set()
    waste_items = []
    for _w in _raw_waste:
        _wid = _w.get("waste_id", "")
        if _wid and _wid in _seen_wids:
            continue
        _seen_wids.add(_wid)
        waste_items.append(_w)

    roi_items = ssad.get("roi_items", [])

    all_pain_points = ssad.get("pain_points", [])
    all_optimisations = ssad.get("optimisations", [])
    # Fallback: count optimisation steps from processes if optimisations[] is empty
    opp_count = len(all_optimisations) if all_optimisations else sum(
        1 for p in ssad.get("processes", []) for s in p.get("steps", []) if s.get("type") == "optimisation"
    )
    findings_count = len(all_pain_points) + opp_count

    qualified_waste = [w for w in waste_items if w.get("confidence") in ("HIGH", "MEDIUM")]
    total_annual = sum(w.get("annual_waste_aud") or 0 for w in qualified_waste if _waste_counts_in_total(w))
    total_monthly = sum(w.get("monthly_waste_aud") or 0 for w in qualified_waste)

    # Pre-compute available downloads for the downloads section
    _downloads = [
        {"file": "2-process-map.html", "label": "How You Work", "desc": "Full map of your current operations across every business stage.", "icon": "&#128506;"},
        {"file": "3-findings.html", "label": "What We Found", "desc": "Pain points and optimisation opportunities from our sessions.", "icon": "&#128269;"},
        {"file": "4-waste.html", "label": "Hidden Costs", "desc": "Opportunity analysis with hidden costs and untapped revenue breakdown.", "icon": "&#128200;"},
    ]
    if proposed_changes and any(c.get("research", {}).get("status") for c in proposed_changes):
        _downloads.append({"file": "5-blueprint.html", "label": "AI Blueprint", "desc": "Your AI roadmap, three implementation strategies with full cost comparison, timeline, and priority matrix.", "icon": "&#127919;"})
    if sections and sections.get("prototype") and sections.get("prototype_url"):
        _downloads.append({"file": sections["prototype_url"], "label": "Clickable Prototype", "desc": "Interactive walkthrough of your future platform, click through real screens and flows.", "icon": "&#128241;"})
    is_demo = ssad.get("client_slug", "").startswith("demo-")
    downloads_json = json.dumps(_downloads)

    demo_pdf_modal_html = ""
    if is_demo:
        demo_pdf_modal_html = f"""<div class="pm-modal-backdrop" id="modal-demo-pdf" style="display:none" onclick="if(event.target===this)closeModal()">
  <div class="pm-modal" style="text-align:center;padding:40px 32px">
    <button class="pm-modal-close" onclick="closeModal()">&times;</button>
    <div style="font-size:48px;margin-bottom:16px">&#128218;</div>
    <h3 style="font-size:20px;font-weight:700;margin:0 0 12px">Full Audit Report</h3>
    <p style="font-size:15px;line-height:1.6;color:var(--muted);margin:0 0 20px">This is a public demo portal. In a real engagement, this downloads a comprehensive 40+ page PDF report covering all findings, solutions, strategic recommendations, and your transformation roadmap.</p>
    <button onclick="closeModal()" class="btn-download" style="cursor:pointer;margin:0 auto">Got it</button>
  </div>
</div>"""

    # Stage labels from audit data
    stage_label_map, _ = _build_stage_lookups(ssad)

    def _fmt_date(raw: str) -> str:
        """Format 2026-03-12 to 12 Mar 2026."""
        try:
            return datetime.strptime(raw, "%Y-%m-%d").strftime("%d %b %Y")
        except (ValueError, TypeError):
            return escape(str(raw)) if raw else ""

    # Derive hero status text from unlocked sections
    _section_status_order = [
        ("prototype", "Audit complete: your prototype is ready to explore."),
        ("priority_matrix", "Audit complete: priority matrix mapped."),
        ("transformation", "Audit in progress: transformation blueprint ready."),
        ("waste", "Audit in progress: waste analysis complete."),
        ("findings", "Audit in progress: findings analysis complete."),
        ("process_map", "Audit in progress: process map under review."),
    ]
    hero_status_text = "Audit in progress: discovery sessions underway."
    for sec_key, status_text in _section_status_order:
        if sections.get(sec_key):
            hero_status_text = status_text
            break

    # ── Derive stages_covered per session from processes if not in session data ──
    _session_stages: dict = {}  # session_number → set of stage keys
    for proc in ssad.get("processes", []):
        stage_key = proc.get("stage", "")
        for step in proc.get("steps", []):
            src = step.get("source_session")
            if src and stage_key:
                _session_stages.setdefault(src, set()).add(stage_key)

    # Canonical stage order for sorting
    _stage_order = ["acquisition", "onboarding_family", "recruitment", "fulfilment",
                    "onboarding_nanny", "payroll_invoicing", "health_safety", "retention"]

    # ── Meeting cards HTML (exclude document-type sessions) ──
    meeting_cards_html = ""
    meeting_count = 0
    for s in sessions:
        # Skip non-meeting sessions (documents, emails), only show actual meetings
        if s.get("session_type") in ("document", "email"):
            continue
        meeting_count += 1
        s_num = meeting_count
        s_date = _fmt_date(s.get("date", ""))
        s_title = escape(s.get("title", f"Session {s_num}"))
        # Fallback: build summary from key_findings if summary field is missing
        s_summary_raw = s.get("summary", "")
        if not s_summary_raw and s.get("key_findings"):
            kf = s["key_findings"]
            if isinstance(kf, list):
                kf = "; ".join(kf)
            s_summary_raw = kf[:120] + ("..." if len(kf) > 120 else "")
        s_summary = escape(s_summary_raw)
        stages_covered = s.get("stages_covered", [])
        orig_num = s.get("session_number", "")
        if not stages_covered and orig_num in _session_stages:
            stages_covered = sorted(_session_stages[orig_num],
                                    key=lambda x: _stage_order.index(x) if x in _stage_order else 99)
        stage_tags = ""
        for sc in stages_covered:
            label = stage_label_map.get(sc, escape(sc).replace("_", " ").title())
            stage_tags += f'<span class="stage-tag">{label}</span>\n          '
        meeting_cards_html += f"""
      <div class="meeting-card">
        <div class="meeting-card-head">
          <span class="session-badge">Session {s_num}</span>
          <span class="complete-badge">&#10003; Complete</span>
        </div>
        <div class="meeting-date">{s_date}</div>
        <div class="meeting-title">{s_title}</div>
        <div class="meeting-summary">{s_summary}</div>
        <div class="stage-tags">
          {stage_tags.strip()}
        </div>
      </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company}: Business Operations Audit</title>
<link rel="icon" type="image/png" href="{APG_LOGO_URL}">
{_PORTAL_FONTS}
<style>
:root {{
  --bg: #f7f9fc;
  --card: #ffffff;
  --border: #e2e8f0;
  --lime: #10B981;
  --lime-text: #064E3B;
  --muted: #64748b;
  --fg: #0f1825;
  --lime-dim: rgba(16,185,129,0.10);
  --lime-glow: 0 4px 20px rgba(0,0,0,0.08);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--fg);
  font-size: 15px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}
a {{ color: inherit; text-decoration: none; }}
{_PORTAL_TOPBAR_CSS}

/* ── Layout ── */
.site-container {{ max-width: 960px; margin: 0 auto; padding: 0 24px; }}

/* ── Hero ── */
.hero {{
  padding: 80px 24px 72px;
  text-align: center;
  position: relative;
  overflow: hidden;
  background-image:
    linear-gradient(rgba(0,0,0,0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.035) 1px, transparent 1px);
  background-size: 60px 60px;
}}
.hero::before {{
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(125,255,0,0.12) 0%, transparent 70%);
  pointer-events: none;
}}
.hero-apg-label {{
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--lime-text);
  margin-bottom: 20px;
}}
.hero h1 {{
  font-size: clamp(36px, 6vw, 72px);
  font-weight: 900;
  letter-spacing: -0.04em;
  color: var(--fg);
  line-height: 1.05;
  margin-bottom: 16px;
}}
.hero-meta {{
  font-size: 14px;
  color: var(--muted);
  margin-bottom: 16px;
}}
.hero-status {{
  display: inline-block;
  font-size: 13px;
  color: var(--fg);
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--lime);
  border-radius: 8px;
  padding: 10px 20px;
  margin-top: 8px;
}}

/* ── Sections ── */
.page-section {{
  padding: 80px 0;
  border-bottom: 1px solid var(--border);
}}
.section-label {{
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--lime-text);
  margin-bottom: 12px;
}}
.section-heading {{
  font-size: clamp(24px, 4vw, 40px);
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--fg);
  margin-bottom: 8px;
}}
.section-sub {{
  font-size: 15px;
  color: var(--muted);
  margin-bottom: 40px;
}}

/* ── Progress Bar ── */
.progress-bar-wrap {{
  margin: 36px 0 40px;
  overflow-x: auto;
  padding-bottom: 4px;
}}
.progress-steps {{
  display: flex;
  align-items: center;
  gap: 0;
  min-width: 560px;
}}
.progress-step {{
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}}
.progress-step:not(:last-child)::after {{
  content: '';
  position: absolute;
  top: 14px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--border);
  z-index: 0;
}}
.progress-step.done:not(:last-child)::after,
.progress-step.active:not(:last-child)::after {{
  background: var(--lime);
}}
.step-dot {{
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--card);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  position: relative;
  z-index: 1;
  margin-bottom: 8px;
}}
.progress-step.done .step-dot {{
  background: var(--lime);
  border-color: var(--lime);
  color: #0f1825;
}}
.progress-step.active .step-dot {{
  background: var(--card);
  border-color: var(--lime);
  color: var(--lime-text);
  box-shadow: 0 0 0 4px rgba(125,255,0,0.18);
}}
.step-name {{
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  text-align: center;
  white-space: nowrap;
}}
.progress-step.done .step-name,
.progress-step.active .step-name {{
  color: var(--fg);
}}

/* ── Meeting Cards ── */
.meetings-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 32px;
}}
.meeting-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  transition: box-shadow 0.2s;
}}
.meeting-card:hover {{ box-shadow: var(--lime-glow); }}
.meeting-card-head {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}}
.session-badge {{
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #0f1825;
  background: var(--lime);
  border-radius: 6px;
  padding: 3px 10px;
  white-space: nowrap;
  flex-shrink: 0;
}}
.complete-badge {{
  font-size: 10px;
  font-weight: 700;
  color: #ffffff;
  background: #166534;
  border: 1px solid #14532d;
  border-radius: 6px;
  padding: 3px 10px;
  white-space: nowrap;
  flex-shrink: 0;
}}
.meeting-date {{
  font-size: 11px;
  color: var(--muted);
  margin-bottom: 6px;
}}
.meeting-title {{
  font-size: 14px;
  font-weight: 700;
  color: var(--fg);
  margin-bottom: 10px;
  line-height: 1.4;
}}
.meeting-summary {{
  font-size: 13px;
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: 14px;
}}
.stage-tags {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}}
.stage-tag {{
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  background: #f1f5f9;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 8px;
}}

/* ── Process Map Feature Card ── */
.pm-feature-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  margin-top: 0;
  position: relative;
}}
.pm-feature-card::before {{
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 60% 80% at 80% 50%, rgba(125,255,0,0.10) 0%, transparent 70%);
  pointer-events: none;
}}
.pm-feature-top {{
  border-top: 3px solid var(--lime);
}}
.pm-feature-inner {{
  padding: 40px 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 40px;
  flex-wrap: wrap;
}}
.pm-feature-text {{ flex: 1; min-width: 260px; }}
.pm-ready-badge {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: #ffffff;
  background: #166534;
  border: 1px solid #14532d;
  border-radius: 20px;
  padding: 4px 14px;
  margin-bottom: 16px;
}}
.pm-ready-dot {{
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--lime);
  animation: pulse-dot 1.8s ease-in-out infinite;
}}
@keyframes pulse-dot {{
  0%, 100% {{ opacity: 1; transform: scale(1); }}
  50% {{ opacity: 0.5; transform: scale(0.7); }}
}}
.pm-feature-heading {{
  font-size: clamp(22px, 3vw, 32px);
  font-weight: 900;
  letter-spacing: -0.04em;
  color: var(--fg);
  line-height: 1.1;
  margin-bottom: 10px;
}}
.pm-feature-sub {{
  font-size: 14px;
  color: var(--muted);
  line-height: 1.6;
  max-width: 440px;
}}
.pm-feature-action {{ flex-shrink: 0; }}
.btn-pm {{
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: var(--lime);
  color: #0f1825;
  font-weight: 900;
  font-size: 15px;
  padding: 16px 36px;
  border-radius: 10px;
  letter-spacing: -0.02em;
  transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s;
  box-shadow: 0 0 0 0 rgba(125,255,0,0.3);
  white-space: nowrap;
}}
.btn-pm:hover {{
  opacity: 0.95;
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(125,255,0,0.2);
}}
.btn-pm-arrow {{
  font-size: 18px;
  transition: transform 0.2s;
}}
.btn-pm:hover .btn-pm-arrow {{ transform: translateX(3px); }}

/* ── Process Map Button (old / generic) ── */
.btn-primary {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--lime);
  color: #0f1825;
  font-weight: 800;
  font-size: 14px;
  padding: 12px 28px;
  border-radius: 8px;
  letter-spacing: -0.01em;
  transition: opacity 0.2s, transform 0.1s;
}}
.btn-primary:hover {{ opacity: 0.9; transform: translateY(-1px); }}
.btn-disabled {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #f1f5f9;
  color: var(--muted);
  font-weight: 700;
  font-size: 14px;
  padding: 12px 28px;
  border-radius: 8px;
  letter-spacing: -0.01em;
  cursor: not-allowed;
  border: 1px solid var(--border);
  position: relative;
}}
.btn-tooltip {{
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: #334155;
  color: #ffffff;
  font-size: 11px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s;
}}
.btn-disabled:hover .btn-tooltip {{ opacity: 1; }}

/* ── Lock Card ── */
.lock-card {{
  background: var(--card);
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 48px 40px;
  text-align: center;
  margin-top: 32px;
  position: relative;
  overflow: hidden;
}}
.lock-icon {{
  font-size: 28px;
  margin-bottom: 12px;
}}
.lock-title {{
  font-size: 16px;
  font-weight: 700;
  color: var(--fg);
  margin-bottom: 8px;
}}
.lock-label {{
  font-size: 14px;
  color: var(--muted);
  max-width: 360px;
  margin: 0 auto;
}}
.lock-ghost {{
  margin-top: 28px;
  filter: blur(3px);
  opacity: 0.45;
  pointer-events: none;
  user-select: none;
}}

/* ── Pain Point Cards ── */
.pain-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 32px;
}}
.pain-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--lime);
  border-radius: 12px;
  padding: 24px;
  transition: box-shadow 0.2s;
}}
.pain-card:hover {{ box-shadow: var(--lime-glow); }}
.pain-desc {{
  font-weight: 600;
  font-size: 15px;
  color: var(--fg);
  margin-bottom: 12px;
}}
.pain-divider {{
  border: none;
  border-top: 1px solid var(--border);
  margin: 12px 0;
}}
.pain-quote {{
  font-size: 13px;
  font-style: italic;
  color: var(--muted);
  line-height: 1.5;
}}

/* ── Bottom Line ── */
.bottomline-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  margin-top: 32px;
  position: relative;
  overflow: hidden;
}}
.bottomline-card::before {{
  content: '';
  position: absolute;
  top: -60px; left: 50%; transform: translateX(-50%);
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(125,255,0,0.14) 0%, transparent 70%);
  pointer-events: none;
}}
.opportunity-label {{
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--lime-text);
  margin-bottom: 16px;
}}
.opportunity-number {{
  font-size: clamp(56px, 10vw, 96px);
  font-weight: 900;
  letter-spacing: -0.04em;
  color: var(--lime-text);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}}
.opportunity-sub {{
  font-size: 20px;
  color: var(--muted);
  margin-top: 8px;
  margin-bottom: 24px;
}}
.opportunity-explain {{
  font-size: 14px;
  color: var(--muted);
  max-width: 500px;
  margin: 0 auto;
  line-height: 1.6;
}}

/* ── Dark Table ── */
.dark-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}}
.dark-table thead tr {{
  border-bottom: 2px solid var(--border);
}}
.dark-table th {{
  padding: 10px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}}
.dark-table td {{
  padding: 12px 14px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}}
.dark-table tbody tr:hover td {{ background: var(--lime-dim); color: var(--fg); }}
.conf-badge {{
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}}
.source-cell {{
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-style: italic;
}}

/* ── Horizons ── */
.horizons-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 32px;
}}
.horizon-col {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
}}
.horizon-title {{
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 4px;
}}
.horizon-subtitle {{
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}}
.horizon-row {{
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}}
.horizon-row:last-child {{ border-bottom: none; }}
.horizon-name {{
  font-size: 13px;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 4px;
}}
.horizon-build {{
  font-size: 12px;
  color: var(--muted);
}}
.horizon-saving {{
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}}
.horizon-empty {{
  font-size: 13px;
  color: var(--muted);
  text-align: center;
  padding: 20px 0;
}}

/* ── Quadrant Priority Matrix ── */
.qm-container {{
  position: relative;
  aspect-ratio: 16/10;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 48px;
  overflow: visible;
  margin-top: 40px;
}}
.qm-axis-x {{
  position: absolute;
  left: 48px; right: 48px; bottom: 48px;
  height: 2px;
  background: var(--fg);
  opacity: 0.5;
}}
.qm-axis-y {{
  position: absolute;
  left: 48px; top: 48px; bottom: 48px;
  width: 2px;
  background: var(--fg);
  opacity: 0.5;
}}
.qm-mid-x {{
  position: absolute;
  left: 48px; right: 48px; top: 50%;
  height: 1px;
  background: var(--fg);
  opacity: 0.2;
}}
.qm-mid-y {{
  position: absolute;
  top: 48px; bottom: 48px; left: 50%;
  width: 1px;
  background: var(--fg);
  opacity: 0.2;
}}
.qm-label {{
  position: absolute;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  opacity: 0.4;
}}
.qm-label-tl {{ top: 56px; left: 56px; }}
.qm-label-tr {{ top: 56px; right: 56px; opacity: 1 !important; }}
.qm-label-br {{ bottom: 56px; right: 56px; opacity: 1 !important; }}
.qm-label-bl {{ bottom: 56px; left: 56px; }}
.qm-axis-label-x {{
  position: absolute;
  bottom: 8px; left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}}
.qm-axis-label-y {{
  position: absolute;
  left: 4px; top: 50%;
  transform: translateY(-50%) rotate(-90deg);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  white-space: nowrap;
}}
.qm-bubble {{
  position: absolute;
  border-radius: 50%;
  border: 2px solid;
  transform: translate(-50%, 50%);
  cursor: pointer;
  transition: all 0.3s ease;
}}
.qm-bubble.qm-dimmed {{
  opacity: 0.3 !important;
}}
.qm-bubble.qm-active {{
  transform: translate(-50%, 50%) scale(1.25) !important;
}}
.qm-tip {{
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 14px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  z-index: 20;
  white-space: nowrap;
  pointer-events: none;
}}
.qm-bubble.qm-active .qm-tip {{ display: block; }}
.qm-legend {{
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}}
.qm-legend-btn {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  color: var(--fg);
}}
.qm-legend-btn:hover, .qm-legend-btn.qm-legend-active {{
  border-color: var(--lime);
  background: rgba(125,255,0,0.08);
}}

/* ── Transformation Blueprint ── */
.blueprint-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px;
  margin-top: 32px;
}}
.blueprint-cols {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-bottom: 32px;
}}
.blueprint-col-label {{
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 12px;
}}
.blueprint-col-label.current {{ color: #ef4444; }}
.blueprint-col-label.proposed {{ color: var(--lime-text); }}
.blueprint-col-body {{
  font-size: 14px;
  color: var(--muted);
  line-height: 1.7;
}}
.blueprint-cta {{
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}}
.coming-soon-badge {{
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  background: #f1f5f9;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 12px;
}}

/* ── Interactive Priority Matrix (embedded chart) ── */
.pm-bubble {{ position:absolute; border-radius:50%; border:2px solid; opacity:0.85;
              cursor:pointer; display:flex; align-items:center; justify-content:center;
              transform:translate(-50%,-50%); transition:transform 0.15s ease, opacity 0.15s ease, box-shadow 0.15s ease; }}
.pm-bubble:hover {{ transform:translate(-50%,-50%) scale(1.18); opacity:1; box-shadow:0 4px 16px rgba(0,0,0,0.25); z-index:10; }}
.pm-bubble-label {{ font-weight:700; color:#fff; pointer-events:none; text-shadow:0 1px 2px rgba(0,0,0,0.5); line-height:1.1; }}
@keyframes pm-pulse {{ 0%,100% {{ box-shadow:0 0 0 0 rgba(5,150,105,0.3); }} 50% {{ box-shadow:0 0 0 8px rgba(5,150,105,0); }} }}
.pm-bubble-top {{ animation:pm-pulse 2s ease-in-out 3; }}
.pm-modal-backdrop {{ position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.6);
                      z-index:2000; display:flex; align-items:center; justify-content:center; padding:24px; }}
.pm-modal {{ background:var(--card); border-radius:14px; max-width:560px; width:100%; max-height:85vh; overflow-y:auto;
             padding:28px 32px; position:relative; box-shadow:0 20px 60px rgba(0,0,0,0.3); }}
.pm-modal-close {{ position:absolute; top:12px; right:16px; background:none; border:none; font-size:24px;
                   color:var(--muted); cursor:pointer; padding:4px 8px; line-height:1; }}
.pm-modal-close:hover {{ color:var(--fg); }}
.pm-modal-section {{ margin-bottom:16px; }}
.pm-modal-section h4 {{ font-size:13px; font-weight:700; color:var(--muted); text-transform:uppercase;
                        letter-spacing:0.05em; margin-bottom:4px; }}
.pm-modal-section p {{ font-size:14px; line-height:1.55; color:var(--fg); }}
.pm-modal-formula {{ background:#166534; border:1px solid #14532d; border-radius:6px; padding:8px 12px;
                     font-size:13px; font-weight:600; color:#ffffff; margin:8px 0 16px 0; font-family:monospace; }}
.pm-modal-stats {{ display:flex; gap:24px; margin-top:20px; padding-top:16px; border-top:1px solid var(--border); }}
.pm-modal-stat-val {{ font-size:20px; font-weight:800; color:var(--fg); display:block; }}
.pm-modal-stat-lbl {{ font-size:10px; text-transform:uppercase; letter-spacing:0.06em; color:var(--muted); }}

/* ── Downloads ── */
.downloads-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 8px;
}}
.download-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}
.download-card:hover {{
  border-color: var(--lime);
  box-shadow: 0 4px 16px rgba(125, 255, 0, 0.08);
}}
.download-icon {{
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(125, 255, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}}
.download-card h3 {{
  font-size: 15px;
  font-weight: 700;
  color: var(--fg);
  margin: 0;
}}
.download-card p {{
  font-size: 13px;
  color: var(--muted);
  line-height: 1.5;
  margin: 0;
  flex: 1;
}}
.btn-download {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  background: var(--lime);
  color: #166534;
  transition: opacity 0.15s ease;
  align-self: flex-start;
}}
.btn-download:hover {{ opacity: 0.85; }}
.btn-download-pdf {{
  background: transparent;
  border: 1px solid var(--lime);
  color: var(--lime-text);
}}
.btn-download-pdf:hover {{ background: rgba(125, 255, 0, 0.08); opacity: 1; }}

/* ── Prototype CTA (in deliverables section) ── */
.prototype-cta {{
  margin-top: 28px;
  background: linear-gradient(135deg, #0f1825 0%, #1a2e12 100%);
  border: 1px solid rgba(125, 255, 0, 0.2);
  border-radius: 16px;
  padding: 36px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}
.prototype-cta:hover {{
  border-color: var(--lime);
  box-shadow: 0 8px 32px rgba(125, 255, 0, 0.12);
}}
.prototype-cta-text {{
  flex: 1;
}}
.prototype-cta-badge {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--lime);
  margin-bottom: 10px;
}}
.prototype-cta-badge .dot {{
  width: 6px; height: 6px; border-radius: 50%; background: var(--lime);
}}
.prototype-cta h3 {{
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  margin: 0 0 8px 0;
  letter-spacing: -0.02em;
}}
.prototype-cta p {{
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  line-height: 1.5;
  max-width: 520px;
}}
.btn-prototype {{
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 32px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  background: var(--lime);
  color: #0f1825;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  white-space: nowrap;
}}
.btn-prototype:hover {{
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(125, 255, 0, 0.25);
}}
.btn-prototype .arrow {{
  font-size: 18px;
  transition: transform 0.15s ease;
}}
.btn-prototype:hover .arrow {{
  transform: translateX(3px);
}}
@media (max-width: 768px) {{
  .prototype-cta {{ flex-direction: column; text-align: center; padding: 28px 24px; }}
  .prototype-cta p {{ max-width: none; }}
  .btn-prototype {{ width: 100%; justify-content: center; }}
}}

/* ── Responsive ── */
@media (max-width: 768px) {{
  .pm-feature-inner {{ flex-direction: column; gap: 28px; padding: 32px 24px; }}
  .btn-pm {{ width: 100%; justify-content: center; }}
  .meetings-grid {{ grid-template-columns: 1fr; }}
  .horizons-grid {{ grid-template-columns: 1fr; }}
  .qm-container {{ padding: 24px; }}
  .qm-label {{ font-size: 8px; }}
  .qm-axis-x {{ left: 24px; right: 24px; bottom: 24px; }}
  .qm-axis-y {{ left: 24px; top: 24px; bottom: 24px; }}
  .qm-mid-x {{ left: 24px; right: 24px; }}
  .qm-mid-y {{ top: 24px; bottom: 24px; }}
  .qm-label-tl, .qm-label-tr {{ top: 28px; }}
  .qm-label-bl, .qm-label-br {{ bottom: 28px; }}
  .qm-label-tl, .qm-label-bl {{ left: 28px; }}
  .qm-label-tr, .qm-label-br {{ right: 28px; }}
  .blueprint-cols {{ grid-template-columns: 1fr; gap: 20px; }}
  .bottomline-card {{ padding: 32px 24px; }}
  .blueprint-card {{ padding: 28px 24px; }}
  .lock-card {{ padding: 40px 24px; }}
}}
{_PORTAL_FOOTER_CSS}
{_PORTAL_TYPOGRAPHY_CSS}
</style>
</head>
<body>

<script>
var SECTIONS = {sections_json};
var STAGE_ORDER = ['process_map','findings','waste','blueprint'];
function stageReached(s) {{ return !!SECTIONS[s]; }}
</script>

<!-- ── Nav ── -->
{_portal_topbar_html("Audit overview", company, _portal_status_pill(sections), is_home=True, is_demo=sections.get("is_demo", False))}

<!-- ── Hero ── -->
<section class="hero">
  <div class="hero-apg-label">Bosar Agency &middot; Business Operations Audit</div>
  <h1>{company}</h1>
  <div class="hero-meta">{industry}{" &middot; " if industry else ""}Audit started {audit_start_display}</div>
  <div class="hero-status" id="hero-status">{hero_status_text}</div>
</section>

<!-- ── AI Moment ── -->
<section id="section-ai-moment" style="padding:72px 0;background:#fff;border-bottom:1px solid var(--border)">
  <div style="max-width:960px;margin:0 auto;padding:0 24px">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#166534;margin-bottom:12px">THE AI MOMENT</div>
    <h2 style="font-size:clamp(26px,4vw,40px);font-weight:800;color:#0f1825;margin:0 0 16px;line-height:1.15">Any process done on a computer will be<br>40-80% quicker in the next two years.</h2>
    <p style="font-size:17px;color:#475569;margin:0 0 48px;max-width:640px;line-height:1.7">This is your blueprint for not getting left behind.</p>

    <!-- Excel analogy callout -->
    <div style="background:linear-gradient(135deg,#166534,#1e4d2b);border:1px solid #14532d;border-radius:12px;padding:24px 28px;margin-bottom:52px;display:flex;gap:20px;align-items:flex-start">
      <div style="flex-shrink:0;width:44px;height:44px;background:rgba(255,255,255,0.15);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px">&#128200;</div>
      <div>
        <div style="font-size:13px;font-weight:700;color:#86efac;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px">The Excel Analogy</div>
        <p style="font-size:15px;color:#e2e8f0;margin:0;line-height:1.7">AI is what Excel was in the early 2000s, a skill every competitive business had to learn. The ones that adopted it early outcompeted those that didn&rsquo;t. The same shift is happening now with AI, and it&rsquo;s moving significantly faster.</p>
      </div>
    </div>

    <!-- Three diagram cards -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px">

      <!-- Card 1: Human amplification diagram -->
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:16px;padding:28px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#166534;margin-bottom:6px">Amplification, not replacement</div>
        <p style="font-size:13px;color:#6b7280;margin:0 0 20px;line-height:1.5">Same team. Same knowledge. Dramatically more output.</p>
        <svg viewBox="0 0 280 130" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;margin-bottom:0">
          <defs>
            <linearGradient id="cwAmpG" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#4ade80"/>
              <stop offset="100%" stop-color="#16a34a"/>
            </linearGradient>
          </defs>
          <line x1="46" y1="100" x2="268" y2="100" stroke="#e5e7eb" stroke-width="1.5"/>
          <line x1="46" y1="100" x2="46" y2="14" stroke="#e5e7eb" stroke-width="1"/>
          <line x1="46" y1="58" x2="268" y2="58" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="3,3"/>
          <line x1="46" y1="16" x2="268" y2="16" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="3,3"/>
          <text x="42" y="103" text-anchor="end" font-size="8" fill="#9ca3af">0</text>
          <text x="42" y="61" text-anchor="end" font-size="8" fill="#9ca3af">100%</text>
          <text x="42" y="20" text-anchor="end" font-size="8" fill="#9ca3af">170%</text>
          <rect x="80" y="58" width="52" height="42" rx="5" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
          <text x="106" y="52" text-anchor="middle" font-size="10" fill="#64748b" font-weight="700">100%</text>
          <text x="106" y="114" text-anchor="middle" font-size="9" fill="#94a3b8">Today</text>
          <rect x="170" y="16" width="52" height="84" rx="5" fill="url(#cwAmpG)"/>
          <text x="196" y="11" text-anchor="middle" font-size="10" fill="#166534" font-weight="800">+70%</text>
          <text x="196" y="114" text-anchor="middle" font-size="9" fill="#166534" font-weight="700">With AI</text>
          <path d="M 140 58 Q 148 40 162 22" stroke="#22c55e" stroke-width="1.5" fill="none" stroke-dasharray="4,2"/>
          <polygon points="159,17 166,25 155,24" fill="#22c55e"/>
          <text x="157" y="127" text-anchor="middle" font-size="10" fill="#9ca3af">Output per team member. Same headcount.</text>
        </svg>
      </div>

      <!-- Card 2: Plugin architecture diagram -->
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:16px;padding:28px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#166534;margin-bottom:6px">What a plugin actually is</div>
        <p style="font-size:13px;color:#6b7280;margin:0 0 20px;line-height:1.5">Your data, connected to AI, placed directly into your team&rsquo;s workflow.</p>
        <svg viewBox="0 0 280 130" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">
          <defs>
            <marker id="cwFlArr" markerWidth="8" markerHeight="8" refX="6" refY="3.5" orient="auto">
              <polygon points="0,0.5 7,3.5 0,6.5" fill="#22c55e"/>
            </marker>
            <marker id="cwFlArrD" markerWidth="8" markerHeight="8" refX="6" refY="3.5" orient="auto">
              <polygon points="0,0.5 7,3.5 0,6.5" fill="#166534"/>
            </marker>
          </defs>
          <rect x="4" y="18" width="72" height="68" rx="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5"/>
          <ellipse cx="40" cy="35" rx="15" ry="5" fill="#dde3ea" stroke="#b8c4cf" stroke-width="1"/>
          <rect x="25" y="35" width="30" height="16" fill="#e8edf2"/>
          <line x1="25" y1="35" x2="25" y2="51" stroke="#b8c4cf" stroke-width="1"/>
          <line x1="55" y1="35" x2="55" y2="51" stroke="#b8c4cf" stroke-width="1"/>
          <ellipse cx="40" cy="51" rx="15" ry="5" fill="#f1f5f9" stroke="#b8c4cf" stroke-width="1"/>
          <text x="40" y="67" text-anchor="middle" font-size="8" fill="#64748b" font-weight="600">YOUR</text>
          <text x="40" y="78" text-anchor="middle" font-size="8" fill="#64748b" font-weight="600">TOOL</text>
          <line x1="78" y1="50" x2="98" y2="50" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" marker-end="url(#cwFlArr)"/>
          <text x="88" y="43" text-anchor="middle" font-size="8" fill="#16a34a" font-weight="700">data</text>
          <rect x="106" y="12" width="68" height="78" rx="10" fill="#22c55e" stroke="#16a34a" stroke-width="2"/>
          <circle cx="140" cy="40" r="20" fill="rgba(0,0,0,0.12)" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
          <circle cx="131" cy="36" r="3" fill="rgba(255,255,255,0.7)"/>
          <circle cx="149" cy="36" r="3" fill="rgba(255,255,255,0.7)"/>
          <circle cx="140" cy="51" r="3" fill="rgba(255,255,255,0.7)"/>
          <line x1="131" y1="36" x2="149" y2="36" stroke="rgba(255,255,255,0.45)" stroke-width="1"/>
          <line x1="131" y1="36" x2="140" y2="51" stroke="rgba(255,255,255,0.45)" stroke-width="1"/>
          <line x1="149" y1="36" x2="140" y2="51" stroke="rgba(255,255,255,0.45)" stroke-width="1"/>
          <text x="140" y="72" text-anchor="middle" font-size="9" fill="#fff" font-weight="800">Claude AI</text>
          <text x="140" y="84" text-anchor="middle" font-size="8" fill="#166534">reads &amp; reasons</text>
          <line x1="176" y1="50" x2="196" y2="50" stroke="#166834" stroke-width="2.5" stroke-linecap="round" marker-end="url(#cwFlArrD)"/>
          <text x="186" y="43" text-anchor="middle" font-size="8" fill="#166834" font-weight="700">output</text>
          <rect x="204" y="18" width="72" height="68" rx="10" fill="#166534" stroke="#14532d" stroke-width="1.5"/>
          <rect x="224" y="26" width="26" height="32" rx="3" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
          <line x1="228" y1="35" x2="246" y2="35" stroke="rgba(255,255,255,0.6)" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="228" y1="42" x2="246" y2="42" stroke="rgba(255,255,255,0.6)" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="228" y1="49" x2="240" y2="49" stroke="rgba(255,255,255,0.6)" stroke-width="1.5" stroke-linecap="round"/>
          <text x="240" y="68" text-anchor="middle" font-size="8" fill="#4ade80" font-weight="700">STAFF</text>
          <text x="240" y="79" text-anchor="middle" font-size="8" fill="#4ade80" font-weight="700">WORKFLOW</text>
          <text x="140" y="110" text-anchor="middle" font-size="10" fill="#9ca3af">Data in. Actionable output out.</text>
        </svg>
        <div style="margin-top:14px;font-size:12px;color:#6b7280;line-height:1.7">
          <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:6px">
            <span style="color:#22c55e;font-weight:700;flex-shrink:0">1.</span>
            <span>Your data is read from the tools you already use, no manual entry needed</span>
          </div>
          <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:6px">
            <span style="color:#22c55e;font-weight:700;flex-shrink:0">2.</span>
            <span>AI reasons about your data, applying your business rules and context</span>
          </div>
          <div style="display:flex;gap:8px;align-items:flex-start">
            <span style="color:#22c55e;font-weight:700;flex-shrink:0">3.</span>
            <span>Actionable output lands in your staff&rsquo;s workflow, ready to use</span>
          </div>
        </div>
      </div>

      <!-- Card 3: Data unlock diagram -->
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:16px;padding:28px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#166534;margin-bottom:6px">Data as the unlock</div>
        <p style="font-size:13px;color:#6b7280;margin:0 0 20px;line-height:1.5">Every recommendation in this report traces back to making your data accessible.</p>
        <svg viewBox="0 0 280 130" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">
          <rect x="4" y="8" width="128" height="102" rx="10" fill="#166534" stroke="#14532d" stroke-width="1.5"/>
          <text x="68" y="26" text-anchor="middle" font-size="10" fill="#166534" font-weight="700">Accessible</text>
          <ellipse cx="42" cy="48" rx="13" ry="4" fill="#166534" stroke="#14532d" stroke-width="1"/>
          <rect x="29" y="48" width="26" height="14" fill="#166534"/>
          <line x1="29" y1="48" x2="29" y2="62" stroke="#14532d" stroke-width="1"/>
          <line x1="55" y1="48" x2="55" y2="62" stroke="#14532d" stroke-width="1"/>
          <ellipse cx="42" cy="62" rx="13" ry="4" fill="#14532d" stroke="#14532d" stroke-width="1"/>
          <line x1="57" y1="55" x2="72" y2="55" stroke="#22c55e" stroke-width="2" stroke-linecap="round"/>
          <polygon points="72,51 80,55 72,59" fill="#22c55e"/>
          <circle cx="92" cy="55" r="14" fill="#22c55e" stroke="#16a34a" stroke-width="1.5"/>
          <text x="92" y="59" text-anchor="middle" font-size="10" fill="#fff" font-weight="800">AI</text>
          <circle cx="68" cy="88" r="11" fill="#166534"/>
          <path d="M 62,88 L 66,93 L 76,81" stroke="#4ade80" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <text x="68" y="109" text-anchor="middle" font-size="9" fill="#166534" font-weight="600">AI can help</text>
          <line x1="140" y1="8" x2="140" y2="110" stroke="#e2e8f0" stroke-width="1.5" stroke-dasharray="4,3"/>
          <text x="140" y="62" text-anchor="middle" font-size="9" fill="#9ca3af" transform="rotate(90,140,62)">vs</text>
          <rect x="148" y="8" width="128" height="102" rx="10" fill="#fff7f7" stroke="#fecaca" stroke-width="1.5"/>
          <text x="212" y="26" text-anchor="middle" font-size="10" fill="#991b1b" font-weight="700">Siloed</text>
          <ellipse cx="186" cy="48" rx="13" ry="4" fill="#fee2e2" stroke="#fca5a5" stroke-width="1"/>
          <rect x="173" y="48" width="26" height="14" fill="#fee2e2"/>
          <line x1="173" y1="48" x2="173" y2="62" stroke="#fca5a5" stroke-width="1"/>
          <line x1="199" y1="48" x2="199" y2="62" stroke="#fca5a5" stroke-width="1"/>
          <ellipse cx="186" cy="62" rx="13" ry="4" fill="#fecaca" stroke="#fca5a5" stroke-width="1"/>
          <rect x="181" y="37" width="10" height="8" rx="2" fill="#ef4444"/>
          <path d="M 183,37 Q 183,33 186,33 Q 189,33 189,37" stroke="#ef4444" stroke-width="1.5" fill="none"/>
          <line x1="201" y1="55" x2="215" y2="55" stroke="#fca5a5" stroke-width="2" stroke-dasharray="3,2" stroke-linecap="round"/>
          <circle cx="230" cy="55" r="14" fill="#f3f4f6" stroke="#e5e7eb" stroke-width="1.5"/>
          <text x="230" y="59" text-anchor="middle" font-size="10" fill="#9ca3af" font-weight="700">AI</text>
          <circle cx="212" cy="88" r="11" fill="#fee2e2" stroke="#fca5a5" stroke-width="1.5"/>
          <line x1="205" y1="81" x2="219" y2="95" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round"/>
          <line x1="219" y1="81" x2="205" y2="95" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round"/>
          <text x="212" y="109" text-anchor="middle" font-size="9" fill="#991b1b" font-weight="600">AI can&rsquo;t reach</text>
        </svg>
      </div>

    </div>

    <!-- Data centralisation visual -->
    <div style="margin-top:48px;background:#f8fafc;border:1px solid #E5E7EB;border-radius:16px;padding:32px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#166534;margin-bottom:6px">WHY DATA CENTRALISATION MATTERS</div>
      <p style="font-size:14px;color:#475569;margin:0 0 24px;line-height:1.6">AI can&rsquo;t work across information locked in separate silos. When your data is connected, AI becomes exponentially more powerful.</p>
      <svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:700px;height:auto;display:block;margin:0 auto">
        <defs>
          <marker id="cwNetArr" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto">
            <polygon points="0,0.5 7,3.5 0,6.5" fill="#4ade80"/>
          </marker>
          <linearGradient id="cwHubG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#22c55e"/>
            <stop offset="100%" stop-color="#15803d"/>
          </linearGradient>
        </defs>
        <text x="168" y="18" text-anchor="middle" fill="#991b1b" font-size="12" font-weight="700">TODAY: DATA IN SILOS</text>
        <rect x="18" y="32" width="60" height="26" rx="6" fill="#fee2e2" stroke="#fca5a5" stroke-width="1.5"/>
        <text x="48" y="49" text-anchor="middle" font-size="10" fill="#991b1b" font-weight="600">CRM</text>
        <rect x="248" y="27" width="58" height="26" rx="6" fill="#fee2e2" stroke="#fca5a5" stroke-width="1.5"/>
        <text x="277" y="44" text-anchor="middle" font-size="10" fill="#991b1b" font-weight="600">Email</text>
        <rect x="112" y="24" width="84" height="26" rx="6" fill="#fee2e2" stroke="#fca5a5" stroke-width="1.5"/>
        <text x="154" y="41" text-anchor="middle" font-size="10" fill="#991b1b" font-weight="600">Spreadsheets</text>
        <rect x="36" y="108" width="66" height="26" rx="6" fill="#fee2e2" stroke="#fca5a5" stroke-width="1.5"/>
        <text x="69" y="125" text-anchor="middle" font-size="10" fill="#991b1b" font-weight="600">Invoicing</text>
        <rect x="228" y="104" width="82" height="26" rx="6" fill="#fee2e2" stroke="#fca5a5" stroke-width="1.5"/>
        <text x="269" y="121" text-anchor="middle" font-size="10" fill="#991b1b" font-weight="600">Scheduling</text>
        <text x="96" y="44" text-anchor="middle" fill="#ef4444" font-size="18" font-weight="700">&#215;</text>
        <text x="216" y="38" text-anchor="middle" fill="#ef4444" font-size="18" font-weight="700">&#215;</text>
        <circle cx="168" cy="86" r="28" fill="#f9fafb" stroke="#e5e7eb" stroke-width="2"/>
        <text x="168" y="82" text-anchor="middle" fill="#94a3b8" font-size="11" font-weight="700">AI</text>
        <text x="168" y="96" text-anchor="middle" fill="#94a3b8" font-size="8">blocked</text>
        <line x1="151" y1="69" x2="185" y2="103" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" opacity="0.65"/>
        <line x1="185" y1="69" x2="151" y2="103" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" opacity="0.65"/>
        <text x="168" y="157" text-anchor="middle" fill="#991b1b" font-size="10" font-style="italic">Data locked in separate tools</text>
        <text x="168" y="172" text-anchor="middle" fill="#991b1b" font-size="10" font-style="italic">AI has no way to connect the dots</text>
        <line x1="350" y1="10" x2="350" y2="188" stroke="#e2e8f0" stroke-width="1.5" stroke-dasharray="6,4"/>
        <text x="530" y="18" text-anchor="middle" fill="#166534" font-size="12" font-weight="700">AFTER: DATA CONNECTED</text>
        <line x1="438" y1="62" x2="504" y2="87" stroke="#14532d" stroke-width="2" marker-end="url(#cwNetArr)"/>
        <line x1="530" y1="57" x2="530" y2="72" stroke="#14532d" stroke-width="2" marker-end="url(#cwNetArr)"/>
        <line x1="622" y1="62" x2="556" y2="87" stroke="#14532d" stroke-width="2" marker-end="url(#cwNetArr)"/>
        <line x1="446" y1="143" x2="505" y2="118" stroke="#14532d" stroke-width="2" marker-end="url(#cwNetArr)"/>
        <line x1="614" y1="143" x2="555" y2="118" stroke="#14532d" stroke-width="2" marker-end="url(#cwNetArr)"/>
        <rect x="400" y="48" width="60" height="26" rx="6" fill="#166534" stroke="#14532d" stroke-width="1.5"/>
        <text x="430" y="65" text-anchor="middle" font-size="10" fill="#ffffff" font-weight="600">CRM</text>
        <rect x="500" y="31" width="60" height="26" rx="6" fill="#166534" stroke="#14532d" stroke-width="1.5"/>
        <text x="530" y="48" text-anchor="middle" font-size="10" fill="#ffffff" font-weight="600">Sheets</text>
        <rect x="592" y="48" width="60" height="26" rx="6" fill="#166534" stroke="#14532d" stroke-width="1.5"/>
        <text x="622" y="65" text-anchor="middle" font-size="10" fill="#ffffff" font-weight="600">Email</text>
        <rect x="408" y="130" width="70" height="26" rx="6" fill="#166534" stroke="#14532d" stroke-width="1.5"/>
        <text x="443" y="147" text-anchor="middle" font-size="10" fill="#ffffff" font-weight="600">Invoicing</text>
        <rect x="574" y="130" width="78" height="26" rx="6" fill="#166534" stroke="#14532d" stroke-width="1.5"/>
        <text x="613" y="147" text-anchor="middle" font-size="10" fill="#ffffff" font-weight="600">Scheduling</text>
        <circle cx="530" cy="100" r="30" fill="url(#cwHubG)" stroke="#14532d" stroke-width="2.5"/>
        <circle cx="522" cy="96" r="2.5" fill="rgba(255,255,255,0.65)"/>
        <circle cx="538" cy="96" r="2.5" fill="rgba(255,255,255,0.65)"/>
        <circle cx="530" cy="110" r="2.5" fill="rgba(255,255,255,0.65)"/>
        <line x1="522" y1="96" x2="538" y2="96" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>
        <line x1="522" y1="96" x2="530" y2="110" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>
        <line x1="538" y1="96" x2="530" y2="110" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>
        <text x="530" y="88" text-anchor="middle" font-size="12" fill="#fff" font-weight="800">AI</text>
        <text x="530" y="178" text-anchor="middle" fill="#166534" font-size="10" font-style="italic">All data flows through one AI brain</text>
        <text x="530" y="193" text-anchor="middle" fill="#166534" font-size="10" font-style="italic">Insights span your entire operation</text>
      </svg>
    </div>
  </div>
</section>

<!-- ── Audit Journey ── -->
<section class="page-section">
  <div class="site-container">
    <div class="section-label">AUDIT PROGRESS</div>
    <h2 class="section-heading">Your Audit Journey</h2>
    <p class="section-sub">Track every stage of the audit as we move through your business together.</p>

    <!-- Progress Bar -->
    <div class="progress-bar-wrap">
      <div class="progress-steps" id="progress-steps">
        <!-- Injected by JS -->
      </div>
    </div>

    <!-- Meeting Cards -->
    <div class="meetings-grid">{meeting_cards_html}
    </div>

  </div>
</section>

<!-- ── Process Map ── -->
<section class="page-section" id="section-process-map">
  <div class="site-container">
    <div class="section-label">HOW YOU WORK</div>
    <h2 class="section-heading">How You Work Today</h2>
    <p class="section-sub">A full map of how your business operates today, every step, every handoff, every tool.</p>
    <div id="process-map-cta">
      <!-- Injected by JS -->
    </div>
  </div>
</section>

<!-- ── What We Found ── -->
<section class="page-section" id="section-findings">
  <div class="site-container">
    <div class="section-label">SESSION SUMMARY</div>
    <h2 class="section-heading">What We Discussed</h2>
    <div id="findings-content">
      <!-- Injected by JS -->
    </div>
  </div>
</section>

<!-- ── Total Waste ── -->
<section class="page-section" id="section-waste">
  <div class="site-container">
    <div class="section-label">HIDDEN COSTS</div>
    <h2 class="section-heading">Hidden Costs Uncovered</h2>
    <div id="waste-content">
      <!-- Injected by JS -->
    </div>
  </div>
</section>

<!-- ── AI Blueprint ── -->
<section class="page-section" id="section-strategies">
  <div class="site-container">
    <div class="section-label">AI BLUEPRINT</div>
    <h2 class="section-heading">Your AI Roadmap</h2>
    <div id="strategies-content">
      <!-- Injected by JS -->
    </div>
  </div>
</section>

<!-- Transformation and Priority Matrix sections removed, now embedded in Options & Pricing page -->
<!-- Prototype now rendered inside deliverables section via JS -->

<!-- ── Downloads ── -->
<section class="page-section" id="section-downloads">
  <div class="site-container">
    <div class="section-label">YOUR DELIVERABLES</div>
    <h2 class="section-heading">Downloads</h2>
    <div id="downloads-content">
      <!-- Injected by JS -->
    </div>
  </div>
</section>

<!-- ── Footer ── -->
{_portal_footer_html()}

<script>
// ── Progress Bar ──
(function() {{
  var steps = [
    {{ key: 'process_map', label: 'How You Work' }},
    {{ key: 'findings', label: 'What We Found' }},
    {{ key: 'waste', label: 'Hidden Costs' }},
    {{ key: 'blueprint', label: 'AI Blueprint' }},
  ];
  var container = document.getElementById('progress-steps');
  // Find the furthest unlocked section index for progress display
  var currentIdx = -1;
  for (var i = steps.length - 1; i >= 0; i--) {{
    if (SECTIONS[steps[i].key]) {{ currentIdx = i; break; }}
  }}
  steps.forEach(function(step, i) {{
    var div = document.createElement('div');
    var cls = 'progress-step';
    if (i < currentIdx) cls += ' done';
    else if (i === currentIdx) cls += ' active';
    div.className = cls;
    div.innerHTML =
      '<div class="step-dot">' + (i < currentIdx ? '&#10003;' : (i + 1)) + '</div>' +
      '<div class="step-name">' + step.label + '</div>';
    container.appendChild(div);
  }});
}})();

// ── Process Map CTA ──
(function() {{
  var wrap = document.getElementById('process-map-cta');
  if (stageReached('process_map')) {{
    wrap.innerHTML =
      '<div class="pm-feature-card pm-feature-top">' +
        '<div class="pm-feature-inner">' +
          '<div class="pm-feature-text">' +
            '<div class="pm-ready-badge"><span class="pm-ready-dot"></span>Now available</div>' +
            '<div class="pm-feature-heading">Your Process Map<br>is ready to explore.</div>' +
            '<p class="pm-feature-sub">We\\'re mapping every step of your current operation across 8 business stages \\u2014 every handoff, every tool, every pain point. This is being built directly from what you told us.</p>' +
          '</div>' +
          '<div class="pm-feature-action">' +
            '<a href="2-process-map.html" class="btn-pm">Open Process Map <span class="btn-pm-arrow">&rarr;</span></a>' +
          '</div>' +
        '</div>' +
      '</div>';
  }} else {{
    wrap.innerHTML =
      '<div class="lock-card">' +
        '<div class="lock-icon">&#128274;</div>' +
        '<div class="lock-title">How You Work</div>' +
        '<div class="lock-label">Your process map is being prepared \\u2014 it will appear here once ready.</div>' +
      '</div>';
  }}
}})();

// ── Findings ──
(function() {{
  var el = document.getElementById('findings-content');
  if (!stageReached('findings')) {{
    el.innerHTML =
      '<div class="lock-card">' +
        '<div class="lock-icon">&#128274;</div>' +
        '<div class="lock-title">What We Discussed</div>' +
        '<div class="lock-label">This section will unlock once the process map review is complete.</div>' +
        '<div class="lock-ghost">' +
          '<div style="height:12px;background:rgba(255,255,255,0.15);border-radius:6px;margin-bottom:10px;width:80%"></div>' +
          '<div style="height:12px;background:rgba(255,255,255,0.10);border-radius:6px;margin-bottom:10px;width:60%"></div>' +
          '<div style="height:12px;background:rgba(255,255,255,0.08);border-radius:6px;width:70%"></div>' +
        '</div>' +
      '</div>';
  }} else {{
    el.innerHTML =
      '<div class="pm-feature-card pm-feature-top">' +
        '<div class="pm-feature-inner">' +
          '<div class="pm-feature-text">' +
            '<div class="pm-ready-badge"><span class="pm-ready-dot"></span>Now available</div>' +
            '<div class="pm-feature-heading">What We Discussed</div>' +
            '<p class="pm-feature-sub">{findings_count} talking points from our conversations \\u2014 pain points you raised and optimisation ideas we explored together, each traced back to what you told us. This is not our proposed solution; that comes next.</p>' +
          '</div>' +
          '<div class="pm-feature-action">' +
            '<a href="3-findings.html" target="_blank" class="btn-pm">View What We Found <span class="btn-pm-arrow">&rarr;</span></a>' +
          '</div>' +
        '</div>' +
      '</div>';
  }}
}})();

// ── Waste ──
(function() {{
  var el = document.getElementById('waste-content');
  if (!stageReached('waste')) {{
    el.innerHTML =
      '<div class="lock-card">' +
        '<div class="lock-icon">&#128274;</div>' +
        '<div class="lock-title">Hidden Costs</div>' +
        '<div class="lock-label">This section will unlock once findings have been reviewed with you.</div>' +
        '<div class="lock-ghost">' +
          '<div style="height:60px;background:rgba(125,255,0,0.12);border-radius:8px;margin-bottom:12px;width:40%;margin-left:auto;margin-right:auto"></div>' +
          '<div style="height:12px;background:rgba(255,255,255,0.08);border-radius:6px;margin-bottom:8px"></div>' +
          '<div style="height:12px;background:rgba(255,255,255,0.06);border-radius:6px;width:80%"></div>' +
        '</div>' +
      '</div>';
  }} else {{
    el.innerHTML =
      '<div class="pm-feature-card pm-feature-top">' +
        '<div class="pm-feature-inner">' +
          '<div class="pm-feature-text">' +
            '<div class="pm-ready-badge"><span class="pm-ready-dot"></span>Now available</div>' +
            '<div class="pm-feature-heading">Hidden Costs Uncovered</div>' +
            '<p class="pm-feature-sub">Operational waste identified across every stage of your business \\u2014 every figure traces to something you or your team said directly during our sessions.</p>' +
          '</div>' +
          '<div class="pm-feature-action">' +
            '<a href="4-waste.html" target="_blank" class="btn-pm">View Hidden Costs <span class="btn-pm-arrow">&rarr;</span></a>' +
          '</div>' +
        '</div>' +
      '</div>';
  }}
}})();

// ── AI Blueprint ──
(function() {{
  var el = document.getElementById('strategies-content');
  if (!stageReached('blueprint')) {{
    el.innerHTML =
      '<div class="lock-card">' +
        '<div class="lock-icon">&#128161;</div>' +
        '<div class="lock-title">AI Blueprint</div>' +
        '<div class="lock-label">This section will unlock once we\\'ve outlined your AI roadmap and implementation strategy.</div>' +
        '<div class="lock-ghost">' +
          '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px">' +
            '<div style="height:80px;background:rgba(34,197,94,0.08);border-radius:8px"></div>' +
            '<div style="height:80px;background:rgba(59,130,246,0.08);border-radius:8px"></div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }} else {{
    el.innerHTML =
      '<div class="pm-feature-card pm-feature-top">' +
        '<div class="pm-feature-inner">' +
          '<div class="pm-feature-text">' +
            '<div class="pm-ready-badge"><span class="pm-ready-dot"></span>Now available</div>' +
            '<div class="pm-feature-heading">Your AI Roadmap</div>' +
            '<p class="pm-feature-sub">Three ways to implement your improvements \\u2014 from quick automation wins to a fully unified AI-powered platform.</p>' +
          '</div>' +
          '<div class="pm-feature-action">' +
            '<a href="5-blueprint.html" target="_blank" class="btn-pm">View Your AI Blueprint <span class="btn-pm-arrow">&rarr;</span></a>' +
          '</div>' +
        '</div>' +
      '</div>';
  }}
}})();

// ── Transformation Blueprint ──
(function() {{
  var el = document.getElementById('transformation-content');
  if (!el) return;
  if (!stageReached('transformation')) {{
    el.innerHTML =
      '<div class="lock-card">' +
        '<div class="lock-icon">&#128274;</div>' +
        '<div class="lock-title">The Roadmap</div>' +
        '<div class="lock-label">Coming next \\u2014 your step-by-step plan is being prepared.</div>' +
        '<div class="lock-ghost">' +
          '<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:16px">' +
            '<div style="height:100px;background:rgba(239,68,68,0.1);border-radius:8px"></div>' +
            '<div style="height:100px;background:rgba(125,255,0,0.08);border-radius:8px"></div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }} else {{
    el.innerHTML =
      '<p class="section-sub">Side-by-side view of how you work today vs how things could look after implementing the recommended changes.</p>' +
      '{blueprint_content_js}';
  }}
}})();

// ── Priority Matrix ──
(function() {{
  var el = document.getElementById('priority-content');
  if (!el) return;
  if (!stageReached('priority_matrix')) {{
    el.innerHTML =
      '<div class="lock-card">' +
        '<div class="lock-icon">&#128274;</div>' +
        '<div class="lock-title">What to Do First</div>' +
        '<div class="lock-label">This section will unlock once we\\'ve mapped out all your opportunities.</div>' +
        '<div class="lock-ghost">' +
          '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:16px">' +
            '<div style="height:80px;background:rgba(255,255,255,0.08);border-radius:8px"></div>' +
            '<div style="height:80px;background:rgba(255,255,255,0.06);border-radius:8px"></div>' +
            '<div style="height:80px;background:rgba(255,255,255,0.04);border-radius:8px"></div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }} else {{
    el.innerHTML =
      '<p class="section-sub">Each initiative plotted by business impact and ease of implementation. Click a bubble to see details.</p>' +
      '{pm_quadrant_js}';
  }}
}})();

// ── Prototype now rendered inside Downloads section ──

// ── Downloads ──
(function() {{
  var el = document.getElementById('downloads-content');
  if (!stageReached('transformation')) {{
    el.innerHTML =
      '<div class="lock-card">' +
        '<div class="lock-icon">&#128274;</div>' +
        '<div class="lock-title">Downloads</div>' +
        '<div class="lock-label">Your deliverables will be available here once the audit is complete.</div>' +
        '<div class="lock-ghost">' +
          '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:16px">' +
            '<div style="height:80px;background:rgba(255,255,255,0.08);border-radius:8px"></div>' +
            '<div style="height:80px;background:rgba(255,255,255,0.06);border-radius:8px"></div>' +
            '<div style="height:80px;background:rgba(255,255,255,0.04);border-radius:8px"></div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }} else {{
    var items = {downloads_json};
    var cards = '';
    items.forEach(function(d) {{
      var btnClass = d.pdf ? 'btn-download btn-download-pdf' : 'btn-download';
      var btnLabel = d.pdf ? 'Save as PDF \\u2192' : 'Open \\u2192';
      var btnHtml = d.demo
        ? '<button onclick="openModal(\\x27demo-pdf\\x27)" class="' + btnClass + '" style="cursor:pointer">' + btnLabel + '</button>'
        : '<a href="' + d.file + '" target="_blank" class="' + btnClass + '">' + btnLabel + '</a>';
      cards +=
        '<div class="download-card">' +
          '<div class="download-icon">' + d.icon + '</div>' +
          '<h3>' + d.label + '</h3>' +
          '<p>' + d.desc + '</p>' +
          btnHtml +
        '</div>';
    }});
    var protoCta = '';
    if (stageReached('prototype')) {{
      var pUrl = SECTIONS.prototype_url || '';
      if (pUrl) {{
        protoCta =
          '<div class="prototype-cta">' +
            '<div class="prototype-cta-text">' +
              '<div class="prototype-cta-badge"><span class="dot"></span>Interactive Prototype</div>' +
              '<h3>See your future platform in action</h3>' +
              '<p>A clickable prototype built from everything we discussed \\u2014 real screens, real workflows, real data. Explore it before a single line of production code is written.</p>' +
            '</div>' +
            '<a href="' + pUrl + '" target="_blank" class="btn-prototype">Open Prototype <span class="arrow">&rarr;</span></a>' +
          '</div>';
      }}
    }}
    el.innerHTML =
      '<p class="section-sub">All audit materials are available below. Open any deliverable or save the full report as a PDF.</p>' +
      '<div class="downloads-grid">' + cards + '</div>' +
      protoCta;
  }}
}})();

// ── Modal functions ──
function openModal(id) {{
  var el = document.getElementById('modal-' + id);
  if (el) {{ el.style.display = 'flex'; document.body.style.overflow = 'hidden'; }}
}}
function closeModal() {{
  document.querySelectorAll('.pm-modal-backdrop').forEach(function(m) {{ m.style.display = 'none'; }});
  document.body.style.overflow = '';
}}
document.addEventListener('keydown', function(e) {{ if (e.key === 'Escape') closeModal(); }});

// ── Chart tooltip ──
var chartTipData = null;
function _loadChartData() {{
  if (chartTipData) return;
  try {{ chartTipData = JSON.parse(document.getElementById('chart-tip-data')?.textContent || '[]'); }} catch(e) {{ chartTipData = []; }}
}}
function showChartDot(el, idx) {{
  _loadChartData();
  var tip = document.getElementById('chart-tip');
  if (!tip || !chartTipData[idx]) return;
  var d = chartTipData[idx];
  var lines = d.items.map(function(l) {{ return '<div style="font-size:11px;margin-top:3px">&#8226; ' + l + '</div>'; }}).join('');
  if (!d.items.length) lines = '<div style="font-size:11px;margin-top:3px;color:#9CA3AF">No new items this month</div>';
  tip.innerHTML = '<div style="font-weight:700;margin-bottom:4px">' + d.month + '-' + d.cumulative + '</div>' + lines;
  tip.style.display = 'block';
  var r = el.getBoundingClientRect();
  var container = tip.parentElement;
  var cr = container.getBoundingClientRect();
  tip.style.left = (r.left - cr.left + r.width/2) + 'px';
  tip.style.top = (r.top - cr.top - 8) + 'px';
  tip.style.transform = 'translate(-50%, -100%)';
}}
function hideChartTip() {{
  var tip = document.getElementById('chart-tip');
  if (tip) tip.style.display = 'none';
}}

// ── Quadrant matrix interaction ──
var qmHovered = null, qmSelected = null;
function qmUpdate() {{
  var active = qmHovered !== null ? qmHovered : qmSelected;
  document.querySelectorAll('.qm-bubble').forEach(function(b) {{
    var idx = parseInt(b.dataset.idx);
    b.classList.toggle('qm-active', idx === active);
    b.classList.toggle('qm-dimmed', active !== null && idx !== active);
    if (idx === active) {{
      b.style.boxShadow = '0 0 20px ' + b.style.borderColor + '80';
      b.style.background = b.style.borderColor + '40';
    }} else {{
      b.style.boxShadow = 'none';
      b.style.background = b.style.borderColor.replace(')', ',0.12)').replace('rgb', 'rgba');
    }}
  }});
  document.querySelectorAll('.qm-legend-btn').forEach(function(b) {{
    var idx = parseInt(b.dataset.idx);
    b.classList.toggle('qm-legend-active', idx === active);
  }});
}}
function qmHover(idx) {{ qmHovered = idx; qmUpdate(); }}
function qmSelect(idx) {{ qmSelected = (qmSelected === idx) ? null : idx; qmUpdate(); }}
function qmClick(idx) {{
  qmSelected = idx; qmUpdate();
  var b = document.querySelector('.qm-bubble[data-idx="' + idx + '"]');
  if (b && b.dataset.cid) openModal(b.dataset.cid);
}}
</script>

<!-- Chart tooltip data -->
<script type="application/json" id="chart-tip-data">{chart_tip_json}</script>

<!-- Priority matrix modals -->
{pm_modals_html}

{demo_pdf_modal_html}

</body>
</html>"""



# ─── Findings & Waste Partial Generators ──────────────────────────────────────



_WASTE_TYPE_LABELS = {
    "manual_data_entry":  "Manual Data Entry",
    "duplicate_work":     "Duplicate Work",
    "no_followup":        "No Follow-up",
    "communication_gap":  "Communication Gap",
    "missing_automation": "Missing Automation",
}


def _findings_stage_label(stage: str, labels: dict = None) -> str:
    if stage is None:
        return "Unknown"
    if labels:
        return labels.get(stage, stage.replace("_", " ").title())
    return stage.replace("_", " ").title()


def _waste_type_label(wt: str) -> str:
    return _WASTE_TYPE_LABELS.get(wt, wt.replace("_", " ").title())


def _waste_basis_note(blended_rate, confidence: str) -> str:
    """Build the calculation basis explanation shown in the waste hero."""
    rate_str = f"${blended_rate}/hr"
    if confidence == "HIGH":
        qualifier = "This rate was derived from salary data discussed during our sessions."
    elif confidence == "MEDIUM":
        qualifier = "This rate is an estimate based on information shared during our sessions and will be validated during your review call."
    else:
        qualifier = "This rate is a conservative estimate and will be validated during your review call."
    return (
        f"Calculated using a blended average hourly rate of <strong>{rate_str}</strong> "
        f"across affected roles &times; wasted hours &times; 52 weeks. {qualifier}"
    )


_PARTIAL_FONT = _PORTAL_FONTS  # alias kept for backward compat


def generate_findings_partial(ssad: dict, sections: dict = None) -> str:
    sections = sections or {}
    pain_items = [
        {**pp, "item_type": "pain", "item_id": pp.get("pain_point_id", "")}
        for pp in ssad.get("pain_points", [])
    ]
    opp_items = [
        {**op, "item_type": "optimisation", "item_id": op.get("optimisation_id", "")}
        for op in ssad.get("optimisations", [])
    ]
    # Fallback: extract optimisation steps from processes if optimisations[] is empty
    # (backwards compat for SDADs built before optimisations[] was populated)
    if not opp_items:
        for proc in ssad.get("processes", []):
            stage = proc.get("stage", "")
            for step in proc.get("steps", []):
                if step.get("type") == "optimisation":
                    opp_items.append({
                        "item_type": "optimisation",
                        "item_id": step.get("step_id", ""),
                        "stage": stage,
                        "description": step.get("description", ""),
                        "quote": step.get("source_quote", ""),
                        "speaker": step.get("source_speaker", ""),
                        "source_session": step.get("source_session"),
                        "source_timestamp_seconds": step.get("source_timestamp_seconds"),
                        "confidence": step.get("confidence", "MEDIUM"),
                    })
    all_items = pain_items + opp_items
    if not all_items:
        return "<html><body><p>No pain_points or optimisations found in audit data.</p></body></html>"

    company = escape(ssad.get("company_name", "Client"))
    generated = datetime.now().strftime("%d %b %Y")

    _findings_labels, _ = _build_stage_lookups(ssad)
    _findings_order = [p["stage"] for p in ssad.get("processes", [])]
    session_map = {s.get("session_number"): s for s in ssad.get("sessions", [])}

    # Materials index for non-Fathom source documents (Loom transcripts, admin docs, emails).
    # Same closure pattern as generate_waste / generate_blueprint, single source of truth for
    # how source_document paths resolve to deployable URLs.
    import os as _os_f
    _client_dir_f = _get_client_dir(ssad.get("client_slug", ""))
    _materials_dir_f = _get_client_subdir(ssad.get("client_slug", ""), "01-materials/documents")
    _mat_index_f: dict = {}
    if _materials_dir_f.is_dir():
        for _root_f, _dirs_f, _fnames_f in _os_f.walk(_materials_dir_f):
            for _fname_f in _fnames_f:
                _full_f = Path(_root_f) / _fname_f
                _rel_f = str(_full_f.relative_to(_materials_dir_f)).replace("\\", "/")
                _mat_index_f[_fname_f.lower()] = _rel_f
                _mat_index_f[Path(_fname_f).stem.lower()] = _rel_f

    def _findings_resolve_doc_href(doc_path: str):
        if not doc_path:
            return None
        norm = doc_path.replace("\\", "/")
        norm = re.sub(r"^client-provided-materials/", "", norm)
        if norm.startswith("meetings/"):
            return None
        if norm.endswith("/"):
            candidate = norm + "email.txt"
            if (_materials_dir_f / candidate).exists():
                return f"materials/{str(Path(candidate).with_suffix('.html'))}"
            else:
                return None
        sfx = Path(norm).suffix.lower()
        nm = Path(norm).name
        if "/" not in norm:
            norm = _mat_index_f.get(nm.lower()) or _mat_index_f.get(Path(nm).stem.lower())
            if not norm:
                return None
        else:
            if (_materials_dir_f / norm).exists():
                pass  # direct path is valid, use as-is
            elif norm.lower() in {v.lower() for v in _mat_index_f.values()}:
                pass  # matches an indexed value, use as-is
            else:
                norm = _mat_index_f.get(nm.lower()) or _mat_index_f.get(Path(nm).stem.lower())
                if not norm:
                    return None
        sfx = Path(norm).suffix.lower()
        if sfx in {".docx", ".doc", ".xlsx", ".xls", ".xlsm"}:
            txt_k = (Path(norm).stem + ".txt").lower()
            txt_resolved = _mat_index_f.get(txt_k)
            if txt_resolved:
                norm = txt_resolved
                sfx = ".txt"
        if sfx in {".md", ".txt"}:
            norm = str(Path(norm).with_suffix(".html"))
        return f"materials/{norm}"

    groups: dict = {}
    for item in all_items:
        s = item.get("stage") or "unknown"
        groups.setdefault(s, []).append(item)
    ordered_stages = [s for s in _findings_order if s in groups]
    for s in groups:
        if s not in ordered_stages:
            ordered_stages.append(s)

    modal_data = []
    for item in all_items:
        sess = session_map.get(item.get("source_session"))
        rec_href = None
        if sess and sess.get("fathom_url") and item.get("source_timestamp_seconds") is not None:
            rec_href = f"{sess['fathom_url']}?t={item['source_timestamp_seconds']}"
        raw_doc = item.get("source_document") or item.get("source_material") or ""
        modal_data.append({
            "id":          item.get("item_id", ""),
            "itemType":    item.get("item_type", "pain"),
            "stage":       item.get("stage") or "",
            "stageLabel":  _findings_stage_label(item.get("stage") or None, _findings_labels),
            "description": item.get("description", ""),
            "quote":       item.get("quote", "") or item.get("source_quote", ""),
            "speaker":     item.get("speaker", ""),
            "session":     item.get("source_session"),
            "confidence":  item.get("confidence", "LOW"),
            "recHref":     rec_href,
            "sourceDoc":   raw_doc,
            "sourceDocLabel": item.get("source_display_name") or (raw_doc.split("/")[-1] if raw_doc else ""),
            "sourceDocHref": _findings_resolve_doc_href(raw_doc),
            "sourceType":  item.get("source_type", ""),
            "sourceNote":  item.get("source_note", ""),
        })

    pills = [f'<button class="pill active" data-stage="all">All ({len(all_items)})</button>']
    for stage in ordered_stages:
        lbl = _findings_stage_label(stage, _findings_labels)
        n = len(groups[stage])
        pills.append(f'<button class="pill" data-stage="{escape(stage)}">{escape(lbl)} ({n})</button>')
    pills_html = "".join(pills)

    conf_colors = {"HIGH": ("#166534", "#ffffff", "#14532d"), "MEDIUM": ("#fef3c7", "#92400e", "#fcd34d"), "LOW": ("#f1f5f9", "#475569", "#cbd5e1")}
    type_eyebrow = {
        "pain":        ("PAIN POINT",  "#fef2f2", "#b91c1c"),
        "optimisation": ("OPTIMISATION", "#166534", "#ffffff"),
    }
    groups_html = ""
    for stage in ordered_stages:
        lbl = _findings_stage_label(stage, _findings_labels)
        items_in = groups[stage]
        cards_html = ""
        for item in items_in:
            pid = escape(item.get("item_id", ""))
            desc = item.get("description", "")
            desc_short = escape(desc[:115] + ("…" if len(desc) > 115 else ""))
            conf = item.get("confidence", "LOW")
            bg, fg, bd = conf_colors.get(conf, ("#f1f5f9", "#475569", "#cbd5e1"))
            session_num = item.get("source_session", "")
            session_tag = f'<span class="session-tag">Session {session_num}</span>' if session_num else ""
            etype = item.get("item_type", "pain")
            eyebrow_label, eyebrow_bg, eyebrow_fg = type_eyebrow.get(etype, type_eyebrow["pain"])
            cards_html += f"""
            <div class="finding-card" data-id="{pid}" role="button" tabindex="0" aria-haspopup="dialog">
              <div class="card-eyebrow" style="background:{eyebrow_bg};color:{eyebrow_fg}">{eyebrow_label}</div>
              <div class="card-top">
                <span class="card-id">{pid}</span>
                <span class="conf-pill" style="background:{bg};color:{fg};border:1px solid {bd}">{conf}</span>
              </div>
              <div class="card-desc">{desc_short}</div>
              <div class="card-foot">
                <span class="stage-tag">{escape(lbl)}</span>
                {session_tag}
              </div>
            </div>"""
        groups_html += f"""
        <div class="stage-group" data-stage="{escape(stage)}">
          <h3 class="stage-heading">{escape(lbl)}<span class="stage-count">{len(items_in)}</span></h3>
          <div class="card-grid">{cards_html}
          </div>
        </div>"""

    items_json = json.dumps(modal_data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company}: What We Discussed</title>
{APG_FAVICON}
{_PARTIAL_FONT}
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg: #f7f9fc; --fg: #0f1825; --card: #ffffff;
  --border: #e2e8f0; --lime: #10B981; --lime-fg: #064E3B;
  --muted: #64748b; --radius: 10px;
}}
body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--fg); font-size: 15px; line-height: 1.5; -webkit-font-smoothing: antialiased; }}
.findings-root {{ max-width: 1200px; margin: 0 auto; padding: 40px 24px 80px; }}
.findings-header {{ margin-bottom: 32px; }}
.findings-eyebrow {{ font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--lime-fg); margin-bottom: 10px; }}
.findings-title {{ font-size: 32px; font-weight: 800; line-height: 1.2; margin-bottom: 8px; }}
.findings-sub {{ font-size: 15px; color: var(--muted); }}
.stage-filters {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 36px; }}
.pill {{ background: var(--card); border: 1px solid var(--border); border-radius: 999px; padding: 6px 16px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all .15s; color: var(--muted); font-family: inherit; }}
.pill:hover {{ border-color: var(--lime); color: var(--fg); }}
.pill.active {{ background: var(--lime); border-color: var(--lime); color: var(--lime-fg); font-weight: 700; }}
.stage-group {{ margin-bottom: 48px; }}
.stage-group[hidden] {{ display: none; }}
.stage-heading {{ font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
.stage-count {{ background: var(--border); color: var(--fg); font-size: 11px; padding: 1px 7px; border-radius: 999px; font-weight: 700; }}
.card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }}
.finding-card {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; cursor: pointer; transition: transform .15s, box-shadow .15s, border-color .15s; display: flex; flex-direction: column; gap: 10px; }}
.finding-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,.08); border-color: #bfdbfe; }}
.finding-card:focus-visible {{ outline: 2px solid var(--lime); outline-offset: 2px; }}
.card-eyebrow {{ font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; align-self: flex-start; }}
.card-top {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
.card-id {{ font-size: 11px; font-weight: 700; color: var(--muted); font-family: monospace; }}
.conf-pill {{ font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: .05em; }}
.card-desc {{ font-size: 13px; line-height: 1.55; color: var(--fg); flex: 1; }}
.card-foot {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
.stage-tag {{ font-size: 11px; font-weight: 600; color: var(--muted); background: var(--bg); border: 1px solid var(--border); padding: 2px 8px; border-radius: 4px; }}
.session-tag {{ font-size: 11px; color: var(--muted); }}
.modal-overlay {{ display: none; position: fixed; inset: 0; background: rgba(15,24,37,.55); backdrop-filter: blur(4px); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }}
.modal-overlay.open {{ display: flex; }}
.modal-body {{ background: var(--card); border-radius: 16px; max-width: 640px; width: 100%; max-height: 90vh; overflow-y: auto; padding: 36px; position: relative; box-shadow: 0 24px 60px rgba(0,0,0,.2); }}
.modal-top {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
.modal-id {{ font-size: 12px; font-weight: 700; color: var(--muted); font-family: monospace; background: var(--bg); padding: 3px 8px; border-radius: 4px; }}
.modal-stage {{ font-size: 12px; font-weight: 600; color: var(--muted); background: var(--bg); padding: 3px 10px; border-radius: 4px; border: 1px solid var(--border); }}
.modal-conf {{ font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 4px; }}
.modal-type {{ font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; }}
.modal-desc {{ font-size: 16px; line-height: 1.6; color: var(--fg); margin-bottom: 20px; }}
.modal-quote {{ border-left: 3px solid #cbd5e1; padding: 12px 18px; background: #f8fafc; border-radius: 0 8px 8px 0; font-style: italic; font-size: 14px; color: #374151; margin-bottom: 16px; line-height: 1.6; }}
.modal-quote cite {{ display: block; margin-top: 8px; font-style: normal; font-size: 12px; color: #94a3b8; font-weight: 600; }}
.modal-meta {{ font-size: 13px; color: var(--muted); margin-bottom: 24px; }}
.btn-recording {{ display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #ffffff; font-weight: 700; font-size: 13px; padding: 10px 20px; border-radius: 8px; text-decoration: none; margin-bottom: 12px; transition: opacity .15s; }}
.btn-recording:hover {{ opacity: .85; }}
.btn-close {{ display: block; width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--muted); font-size: 13px; font-family: inherit; cursor: pointer; transition: background .15s; }}
.btn-close:hover {{ background: var(--bg); }}
.modal-close-x {{ position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 20px; color: var(--muted); cursor: pointer; padding: 4px 8px; border-radius: 4px; }}
.modal-close-x:hover {{ background: var(--bg); }}
.type-toggle {{ display: flex; align-items: stretch; gap: 0; margin-bottom: 28px; border-radius: 12px; overflow: hidden; border: 2px solid var(--border); width: fit-content; }}
.type-btn {{ background: var(--card); border: none; padding: 14px 28px; font-size: 15px; font-weight: 700; cursor: pointer; transition: all .2s; color: var(--muted); font-family: inherit; white-space: nowrap; position: relative; letter-spacing: -0.01em; }}
.type-btn:not(:last-child) {{ border-right: 2px solid var(--border); }}
.type-btn:hover {{ color: var(--fg); background: #f1f5f9; }}
.type-btn .type-count {{ display: inline-block; font-size: 12px; font-weight: 800; padding: 1px 7px; border-radius: 999px; margin-left: 6px; background: var(--border); color: var(--muted); }}
.type-btn.active-all {{ background: var(--fg); color: #fff; }}
.type-btn.active-all .type-count {{ background: rgba(255,255,255,0.2); color: #fff; }}
.type-btn.active-pain {{ background: #dc2626; color: #fff; }}
.type-btn.active-pain .type-count {{ background: rgba(255,255,255,0.25); color: #fff; }}
.type-btn.active-opt {{ background: #16a34a; color: #fff; }}
.type-btn.active-opt .type-count {{ background: rgba(255,255,255,0.25); color: #fff; }}
.finding-card.type-hidden {{ display: none; }}
@media (max-width: 600px) {{
  .findings-root {{ padding: 24px 16px 60px; }}
  .card-grid {{ grid-template-columns: 1fr; }}
  .modal-body {{ padding: 24px; }}
}}
{_PORTAL_TOPBAR_CSS}
{_PORTAL_FOOTER_CSS}
{_PORTAL_TYPOGRAPHY_CSS}
</style>
</head>
<body>
{_portal_topbar_html("What we discussed", company, _portal_status_pill(sections), is_demo=sections.get("is_demo", False))}
<div class="findings-root">
  <div class="findings-header">
    <div class="findings-eyebrow">Session Summary</div>
    <h1 class="findings-title">What We Discussed</h1>
    <p class="findings-sub">Everything below comes directly from our conversations, these are the pain points you raised and the optimisation ideas we explored together. This is not our proposed solution; that comes next.</p>
  </div>

  <div class="type-toggle" role="group" aria-label="Filter by type">
    <button class="type-btn active-all" data-type="all">All<span class="type-count" id="count-all">{len(all_items)}</span></button>
    <button class="type-btn" data-type="pain">Pain Points<span class="type-count" id="count-pain">{sum(1 for i in all_items if i.get('item_type') == 'pain')}</span></button>
    <button class="type-btn" data-type="optimisation">Optimisations<span class="type-count" id="count-opt">{sum(1 for i in all_items if i.get('item_type') == 'optimisation')}</span></button>
  </div>

  <div class="stage-filters" role="group" aria-label="Filter by stage">
    {pills_html}
  </div>

  {groups_html}

  <p style="font-size:12px;color:var(--muted);text-align:right">Generated {generated}</p>

  <div class="modal-overlay" id="finding-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-body">
      <button class="modal-close-x" id="modal-close-x" aria-label="Close">&times;</button>
      <div class="modal-top">
        <span class="modal-id" id="modal-id"></span>
        <span class="modal-type" id="modal-type"></span>
        <span class="modal-stage" id="modal-stage"></span>
        <span class="modal-conf" id="modal-conf"></span>
      </div>
      <p class="modal-desc" id="modal-desc"></p>
      <blockquote class="modal-quote" id="modal-quote-wrap">
        <span id="modal-quote"></span>
        <cite id="modal-speaker"></cite>
      </blockquote>
      <div class="modal-meta" id="modal-meta"></div>
      <div id="modal-source-wrap" style="display:none;margin-bottom:16px">
        <div style="font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#94a3b8;margin-bottom:8px">Source</div>
        <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:8px">
          <span id="modal-source-type-badge" style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:2px 8px;border-radius:4px"></span>
          <span id="modal-source-doc" style="font-size:12px;color:#475569;font-family:monospace;background:#f1f5f9;border:1px solid #e2e8f0;padding:2px 8px;border-radius:4px;word-break:break-all"></span>
        </div>
        <div id="modal-source-note" style="font-size:12px;color:#64748b;line-height:1.6;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px"></div>
      </div>
      <div id="modal-calc-note" style="display:none;margin-bottom:16px"><div style="font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#94a3b8;margin-bottom:8px">How we calculated this</div><div id="modal-calc-body" style="font-size:12px;color:#475569;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;line-height:1.7"></div></div>
      <div id="modal-rec-wrap"></div>
      <button class="btn-close" id="modal-close-btn">Close</button>
    </div>
  </div>
</div>

<script>
const ITEMS = {items_json};
const itemMap = Object.fromEntries(ITEMS.map(i => [i.id, i]));
const modal = document.getElementById('finding-modal');
const confColors = {{
  HIGH:   ['#166534', '#ffffff','#14532d'],
  MEDIUM: ['#fef3c7','#92400e','#fcd34d'],
  LOW:    ['#f1f5f9','#475569','#cbd5e1'],
}};
const typeStyles = {{
  pain:        ['PAIN POINT',  '#fef2f2','#b91c1c'],
  optimisation: ['OPTIMISATION', '#166534', '#ffffff'],
}};

function openModal(id) {{
  const d = itemMap[id]; if (!d) return;
  document.getElementById('modal-id').textContent = d.id;
  const typeEl = document.getElementById('modal-type');
  const [tlabel, tbg, tfg] = typeStyles[d.itemType] || typeStyles.pain;
  typeEl.textContent = tlabel;
  typeEl.style.cssText = `background:${{tbg}};color:${{tfg}}`;
  document.getElementById('modal-stage').textContent = d.stageLabel;
  const conf = document.getElementById('modal-conf');
  conf.textContent = d.confidence;
  const [bg,fg,bd] = confColors[d.confidence] || ['#f1f5f9','#475569','#cbd5e1'];
  conf.style.cssText = `background:${{bg}};color:${{fg}};border:1px solid ${{bd}}`;
  document.getElementById('modal-desc').textContent = d.description;
  const qwrap = document.getElementById('modal-quote-wrap');
  if (d.quote) {{
    document.getElementById('modal-quote').textContent = '\u201c' + d.quote + '\u201d';
    document.getElementById('modal-speaker').textContent = d.speaker || '';
    qwrap.style.display = '';
  }} else {{
    qwrap.style.display = 'none';
  }}
  document.getElementById('modal-meta').textContent = d.session ? 'Session ' + d.session : '';
  const recWrap = document.getElementById('modal-rec-wrap');
  if (d.recHref) {{
    recWrap.innerHTML = '<a class="btn-recording" href="' + d.recHref + '" target="_blank" rel="noopener">&#9654; Watch in recording &rarr;</a><br>';
  }} else {{
    recWrap.innerHTML = '';
  }}
  // Source attribution section
  const srcWrap = document.getElementById('modal-source-wrap');
  const sourceTypeLabels = {{
    'meeting_transcript': ['Meeting Transcript', '#dbeafe', '#1e40af'],
    'loom_transcript':    ['Loom Video', '#ede9fe', '#6d28d9'],
    'admin_document':     ['Admin Document', '#fef3c7', '#92400e'],
    'client_email':       ['Client Email', '#166534', '#ffffff'],
    'analyst_observation':['Analyst Note', '#f1f5f9', '#475569'],
  }};
  if (d.sourceDoc || d.sourceNote) {{
    srcWrap.style.display = '';
    const badge = document.getElementById('modal-source-type-badge');
    const [stLabel, stBg, stFg] = sourceTypeLabels[d.sourceType] || ['Document', '#f1f5f9', '#475569'];
    badge.textContent = stLabel;
    badge.style.cssText = 'font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:2px 8px;border-radius:4px;background:' + stBg + ';color:' + stFg;
    const sourceDocEl = document.getElementById('modal-source-doc');
    const docLabel = d.sourceDocLabel || d.sourceDoc || '';
    if (d.sourceDocHref && docLabel) {{
      sourceDocEl.innerHTML = '<a class="btn-recording" href="' + d.sourceDocHref + '" target="_blank" rel="noopener">&#128196; ' + docLabel + '</a>';
    }} else {{
      sourceDocEl.textContent = docLabel;
    }}
    const noteEl = document.getElementById('modal-source-note');
    if (d.sourceNote) {{ noteEl.textContent = d.sourceNote; noteEl.style.display = ''; }}
    else {{ noteEl.style.display = 'none'; }}
  }} else {{
    srcWrap.style.display = 'none';
  }}
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function closeModal() {{
  modal.classList.remove('open');
  document.body.style.overflow = '';
}}

document.querySelectorAll('.finding-card').forEach(card => {{
  card.addEventListener('click', () => openModal(card.dataset.id));
  card.addEventListener('keydown', e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModal(card.dataset.id); }} }});
}});
document.getElementById('modal-close-x').addEventListener('click', closeModal);
document.getElementById('modal-close-btn').addEventListener('click', closeModal);
modal.addEventListener('click', e => {{ if (e.target === modal) closeModal(); }});
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

// ── Type + Stage filtering ──
let activeType = 'all';
let activeStage = 'all';

function applyFilters() {{
  document.querySelectorAll('.finding-card').forEach(card => {{
    const item = itemMap[card.dataset.id];
    if (!item) return;
    const typeMatch = activeType === 'all' || item.itemType === activeType;
    card.classList.toggle('type-hidden', !typeMatch);
  }});
  document.querySelectorAll('.stage-group').forEach(g => {{
    const stageMatch = activeStage === 'all' || g.dataset.stage === activeStage;
    const hasVisible = g.querySelectorAll('.finding-card:not(.type-hidden)').length > 0;
    g.hidden = !stageMatch || !hasVisible;
    const countEl = g.querySelector('.stage-count');
    if (countEl) countEl.textContent = g.querySelectorAll('.finding-card:not(.type-hidden)').length;
  }});
  document.querySelectorAll('.pill').forEach(pill => {{
    const stage = pill.dataset.stage;
    let count;
    if (stage === 'all') {{
      count = ITEMS.filter(i => activeType === 'all' || i.itemType === activeType).length;
    }} else {{
      count = ITEMS.filter(i => i.stage === stage && (activeType === 'all' || i.itemType === activeType)).length;
    }}
    const label = pill.textContent.replace(/\\s*\\(\\d+\\)/, '');
    pill.textContent = label + ' (' + count + ')';
  }});
  const totalVisible = ITEMS.filter(i => activeType === 'all' || i.itemType === activeType).length;
  const sub = document.querySelector('.findings-sub');
  if (sub) sub.innerHTML = totalVisible + ' talking points from our conversations, these are the pain points you raised and the optimisation ideas we explored together. This is not our proposed solution; that comes next.';
}}

document.querySelectorAll('.type-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.type-btn').forEach(b => b.className = 'type-btn');
    const type = btn.dataset.type;
    btn.classList.add(type === 'all' ? 'active-all' : type === 'pain' ? 'active-pain' : 'active-opt');
    activeType = type;
    applyFilters();
  }});
}});

document.querySelectorAll('.pill').forEach(pill => {{
  pill.addEventListener('click', () => {{
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeStage = pill.dataset.stage;
    applyFilters();
  }});
}});
</script>
{_portal_footer_html()}
</body>
</html>"""


def generate_waste_partial(ssad: dict, sections: dict = None) -> str:
    sections = sections or {}
    waste_items = ssad.get("waste_items", [])
    # Deduplicate by waste_id
    seen_ids: set = set()
    deduped = []
    for w in waste_items:
        wid = w.get("waste_id", "")
        if wid and wid in seen_ids:
            continue
        seen_ids.add(wid)
        deduped.append(w)
    waste_items = deduped
    waste_items.sort(key=lambda w: w.get("annual_waste_aud") or 0, reverse=True)

    if not waste_items:
        return "<html><body><p>No waste_items found in audit data.</p></body></html>"

    company = escape(ssad.get("company_name", "Client"))
    generated = datetime.now().strftime("%d %b %Y")
    blended_rate = ssad.get("blended_hourly_rate_aud") or 0

    session_map = {s.get("session_number"): s for s in ssad.get("sessions", [])}
    _pp_lookup = {pp.get("pain_point_id"): pp for pp in ssad.get("pain_points", [])}

    qualified = [w for w in waste_items if w.get("confidence") in ("HIGH", "MEDIUM")]
    # Headline + breakdown exclude explicit overlap sub-strategies so the
    # hero never double-counts a parent and its contributing children.
    total_annual = sum(w.get("annual_waste_aud") or 0 for w in waste_items if _waste_counts_in_total(w))
    total_hrs_pw = sum(w.get("hours_per_week") or 0 for w in waste_items if _waste_counts_in_total(w))

    type_totals: dict = {}
    for w in waste_items:
        if not _waste_counts_in_total(w):
            continue
        wt = w.get("waste_type", "other")
        type_totals[wt] = type_totals.get(wt, 0) + (w.get("annual_waste_aud") or 0)

    quantified_types = [(t, v) for t, v in type_totals.items() if v > 0]
    quantified_types.sort(key=lambda x: x[1], reverse=True)

    bars_html = ""
    for wt, amt in quantified_types:
        pct = round(amt / max(total_annual, 1) * 100)
        lbl = _waste_type_label(wt)
        bars_html += f"""
        <div class="bar-row">
          <div class="bar-label">{escape(lbl)}</div>
          <div class="bar-track"><div class="bar-fill" style="width:{pct}%" title="{fmt_aud(amt)}/yr"></div></div>
          <div class="bar-amt">{fmt_aud(amt)}</div>
        </div>"""
    if not bars_html:
        bars_html = '<p style="color:#64748b;font-size:13px">Waste quantities not yet calculated.</p>'

    _waste_labels, _ = _build_stage_lookups(ssad)
    modal_data = []
    items_html = ""
    conf_colors = {"HIGH": ("#166534", "#ffffff", "#14532d"), "MEDIUM": ("#fef3c7", "#92400e", "#fcd34d"), "LOW": ("#f1f5f9", "#475569", "#cbd5e1")}

    # Build materials index for source doc links (same pattern as process map)
    import os as _os
    _client_dir_w = _get_client_dir(ssad.get("client_slug", ""))
    _materials_dir_w = _get_client_subdir(ssad.get("client_slug", ""), "01-materials/documents")
    _mat_index: dict = {}
    if _materials_dir_w.is_dir():
        for _root, _dirs, _fnames in _os.walk(_materials_dir_w):
            for _fname in _fnames:
                _full = Path(_root) / _fname
                _rel = str(_full.relative_to(_materials_dir_w)).replace("\\", "/")
                _mat_index[_fname.lower()] = _rel
                _mat_index[Path(_fname).stem.lower()] = _rel

    def _resolve_waste_href(doc_path: str):
        import re as _re2
        if not doc_path:
            return None
        norm = doc_path.replace("\\", "/")
        norm = _re2.sub(r"^client-provided-materials/", "", norm)
        if norm.startswith("meetings/"):
            return None
        if norm.endswith("/"):
            candidate = norm + "email.txt"
            if (_materials_dir_w / candidate).exists():
                return f"materials/{str(Path(candidate).with_suffix('.html'))}"
            else:
                return None
        sfx = Path(norm).suffix.lower()
        nm = Path(norm).name
        if "/" not in norm:
            norm = _mat_index.get(nm.lower()) or _mat_index.get(Path(nm).stem.lower())
            if not norm:
                return None
        else:
            if (_materials_dir_w / norm).exists():
                pass  # direct path is valid, use as-is
            elif norm.lower() in {v.lower() for v in _mat_index.values()}:
                pass  # matches an indexed value, use as-is
            else:
                norm = _mat_index.get(nm.lower()) or _mat_index.get(Path(nm).stem.lower())
                if not norm:
                    return None
        sfx = Path(norm).suffix.lower()
        if sfx in {".docx", ".doc", ".xlsx", ".xls", ".xlsm"}:
            txt_k = (Path(norm).stem + ".txt").lower()
            txt_resolved = _mat_index.get(txt_k)
            if txt_resolved:
                norm = txt_resolved
                sfx = ".txt"
        if sfx in {".md", ".txt"}:
            norm = str(Path(norm).with_suffix(".html"))
        return f"materials/{norm}"

    for i, w in enumerate(waste_items):
        wid = w.get("waste_id") or f"W-{i+1:03d}"
        stage = w.get("stage", "")
        stage_lbl = _findings_stage_label(stage, _waste_labels) if stage else "-"
        wt = w.get("waste_type", "")
        wt_lbl = _waste_type_label(wt) if wt else "-"
        desc = w.get("description") or w.get("activity", "")
        annual = w.get("annual_waste_aud")
        monthly = w.get("monthly_waste_aud")
        hrs = w.get("hours_per_week")
        headcount = w.get("headcount_affected")
        conf = w.get("confidence", "LOW")
        quote = w.get("source_quote") or w.get("quote", "")
        speaker = w.get("speaker", "")
        correction_note = w.get("correction_note", "")
        ts_secs = w.get("source_timestamp_seconds")
        source_type = w.get("source_type", "")
        source_document = w.get("source_document") or w.get("source_material", "")
        # Descriptive cross-reference (e.g. "pain_point PP-044 ..."), resolve to the referenced item's source
        if source_document and source_document.startswith("pain_point "):
            import re as _re_pp
            _pp_match = _re_pp.search(r'PP-\d+', source_document)
            if _pp_match:
                _ref_pp = _pp_lookup.get(_pp_match.group(0), {})
                source_document = _ref_pp.get("source_document") or _ref_pp.get("source_material") or source_document
        calculation_note = w.get("calculation_note", "")
        session_num = w.get("source_session")
        item_rate = w.get("hourly_rate_aud") or blended_rate
        rate_estimated = w.get("rate_is_estimated", True) if w.get("hourly_rate_aud") else True
        rec_href = None
        if session_num:
            sess = session_map.get(session_num)
            ts = w.get("source_timestamp_seconds")
            if sess and sess.get("fathom_url"):
                # Deep-link with timestamp if available; otherwise link to session start
                rec_href = f"{sess['fathom_url']}?t={ts}" if ts is not None else sess["fathom_url"]
        # Also check meeting_references for deep-links
        if not rec_href:
            for mref in (w.get("meeting_references") or []):
                ms = mref.get("session")
                mts = mref.get("timestamp_seconds")
                murl = mref.get("fathom_url")
                if murl:
                    rec_href = f"{murl}?t={mts}" if mts is not None else murl
                    break
                elif ms and session_map.get(ms) and session_map[ms].get("fathom_url"):
                    furl = session_map[ms]["fathom_url"]
                    rec_href = f"{furl}?t={mts}" if mts is not None else furl
                    break

        derived_annual = annual
        if not derived_annual and hrs and item_rate:
            derived_annual = round(hrs * headcount * item_rate * 52) if headcount else round(hrs * item_rate * 52)

        def _fmt_ts(secs):
            if secs is None: return ""
            m, s = divmod(int(secs), 60)
            return f"{m}:{s:02d}"

        ts_fmt = _fmt_ts(ts_secs)
        session_label = f"Session {session_num}" if session_num else ""
        source_line = " · ".join(filter(None, [session_label, ts_fmt]))

        modal_data.append({
            "id": wid, "stage": stage, "stageLabel": stage_lbl,
            "wasteType": wt_lbl, "description": desc,
            "quote": quote, "speaker": speaker,
            "session": session_num, "sessionLabel": session_label,
            "timestampFmt": ts_fmt, "correctionNote": correction_note,
            "sourceType": source_type, "sourceDocument": source_document,
            "calculationNote": calculation_note or w.get("annual_value_note", ""),
            "hoursPerWeek": hrs, "headcount": headcount,
            "hourlyRate": item_rate, "rateIsEstimated": rate_estimated,
            "annual": annual, "monthly": monthly,
            "derivedAnnual": derived_annual,
            "confidence": conf, "recHref": rec_href,
            "sourceDocHref": _resolve_waste_href(source_document),
        })

        bg, fg, bd = conf_colors.get(conf, ("#f1f5f9", "#475569", "#cbd5e1"))
        desc_short = escape(desc[:120] + ("…" if len(desc) > 120 else ""))
        annual_display = fmt_aud(annual) if annual else (fmt_aud(derived_annual) + "*" if derived_annual else "")
        rate_tag = " (est)" if rate_estimated and item_rate else ""
        rec_badge = f'<a class="wi-rec-link" href="{rec_href}" target="_blank" rel="noopener" onclick="event.stopPropagation()">&#9654;</a>' if rec_href else ""
        # Per-card document badge for items whose source is a non-Fathom file. Mirrors the
        # green ▶ Fathom badge so users can see at a glance that the source is openable.
        _doc_href_for_card = _resolve_waste_href(source_document)
        doc_badge = (
            f'<a class="wi-doc-link" href="{_doc_href_for_card}" target="_blank" rel="noopener" '
            f'onclick="event.stopPropagation()" title="Open source document">&#128196;</a>'
        ) if (_doc_href_for_card and not rec_href) else ""

        # Build formula string for visual breakdown
        is_revenue_type = (wt == "unrealized_revenue")
        if is_revenue_type:
            # For revenue items, show a compact excerpt of the calculation note instead of
            # the time-based formula (which would be misleading since hours_per_week is null)
            calc_text = calculation_note or w.get("annual_value_note", "")
            if calc_text:
                formula_str = escape(calc_text[:90] + ("…" if len(calc_text) > 90 else ""))
            else:
                formula_str = "estimated annual revenue"
        else:
            formula_parts = []
            if hrs:
                formula_parts.append(f"{hrs} hrs/wk")
            if headcount and headcount > 1:
                formula_parts.append(f"{headcount} people")
            if item_rate:
                formula_parts.append(f"${item_rate}/hr{rate_tag}")
            formula_parts.append("52 wks")
            formula_str = " &times; ".join(formula_parts)

        if annual or derived_annual:
            right_html = (
                f"<span class='wi-amt-val'>{annual_display}</span>"
                f"<div class='wi-amt-label'>per year</div>"
                f"<div class='wi-formula'>{formula_str}</div>"
            )
        elif hrs:
            right_html = (
                f"<span class='wi-unquant'>Needs quantification</span>"
                f"<div class='wi-formula'>{formula_str}</div>"
            )
        else:
            right_html = f"<span class='wi-unquant'>Needs quantification</span><div class='wi-formula'>{formula_str}</div>" if formula_str else "<span class='wi-unquant'>Needs quantification</span>"

        # Build source attribution
        source_label = ""
        if source_document:
            type_prefix = {"document": "Document", "email": "Email", "loom": "Loom"}.get(source_type, "")
            source_label = f"{type_prefix}: {source_document}" if type_prefix else source_document
        elif source_type in ("calculated", "observation"):
            source_label = {"calculated": "Calculated", "observation": "Observed in session"}[source_type]

        # Inline quote on the card
        quote_html = ""
        if quote:
            q_short = escape(quote[:200] + ("…" if len(quote) > 200 else ""))
            attr_parts = [escape(speaker)] if speaker else []
            if source_line:
                attr_parts.append(escape(source_line))
            elif source_label:
                attr_parts.append(escape(source_label))
            attr_str = " · ".join(attr_parts)
            quote_html = f'<blockquote class="wi-quote">“{q_short}”<cite>{attr_str}</cite></blockquote>'
        elif source_label:
            quote_html = f'<div class="wi-source-label">Source: {escape(source_label)}</div>'

        _overlap_parent = w.get("overlap_parent_waste_id")
        overlap_tag = (
            f'<span class="wi-type" style="background:#fff7ed;color:#9a3412;border-color:#fed7aa" '
            f'title="Sub-strategy already counted inside {escape(str(_overlap_parent))}, shown for detail, excluded from the total to avoid double-counting">'
            f'&#8627; within {escape(str(_overlap_parent))} · not in total</span>'
        ) if _overlap_parent else ""

        items_html += f"""
        <div class="waste-item" data-id="{escape(wid)}" role="button" tabindex="0" aria-haspopup="dialog">
          <div class="wi-left">
            <div class="wi-top">
              <span class="wi-id">{escape(wid)}</span>
              <span class="wi-type">{escape(wt_lbl)}</span>
              {overlap_tag}
              <span class="conf-pill" style="background:{bg};color:{fg};border:1px solid {bd}">{conf}</span>
              {rec_badge}{doc_badge}
            </div>
            <div class="wi-desc">{desc_short}</div>
            {quote_html}
          </div>
          <div class="wi-right">
            {right_html}
          </div>
        </div>"""

    items_json = json.dumps(modal_data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company}: Hidden Costs</title>
{APG_FAVICON}
{_PARTIAL_FONT}
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{ --bg: #f7f9fc; --fg: #0f1825; --card: #ffffff; --border: #e2e8f0; --lime: #10B981; --lime-fg: #064E3B; --muted: #64748b; --radius: 10px; }}
body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--fg); font-size: 15px; line-height: 1.5; -webkit-font-smoothing: antialiased; }}
.waste-root {{ max-width: 960px; margin: 0 auto; padding: 40px 24px 80px; }}
.hero {{ background: var(--fg); color: #fff; border-radius: 16px; padding: 40px; margin-bottom: 32px; }}
.hero-eyebrow {{ font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--lime); margin-bottom: 12px; }}
.hero-amount {{ font-size: 64px; font-weight: 900; color: var(--lime); line-height: 1; margin-bottom: 6px; font-variant-numeric: tabular-nums; }}
.hero-label {{ font-size: 16px; color: #9ca3af; margin-bottom: 24px; }}
.hero-stats {{ display: flex; gap: 32px; flex-wrap: wrap; }}
.hero-stat-val {{ font-size: 28px; font-weight: 800; color: #fff; }}
.hero-stat-lbl {{ font-size: 13px; color: #9ca3af; }}
.hero-basis {{ margin-top: 20px; padding: 12px 16px; background: rgba(255,255,255,0.08); border-radius: 8px; font-size: 13px; color: #9ca3af; line-height: 1.5; border-left: 3px solid var(--lime); }}
.hero-basis strong {{ color: #fff; }}
.breakdown {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 32px; }}
.breakdown-title {{ font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 16px; }}
.bar-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
.bar-label {{ font-size: 13px; color: var(--fg); width: 180px; flex-shrink: 0; }}
.bar-track {{ flex: 1; background: var(--border); border-radius: 999px; height: 8px; overflow: hidden; }}
.bar-fill {{ height: 100%; background: var(--lime); border-radius: 999px; transition: width .4s; }}
.bar-amt {{ font-size: 13px; font-weight: 600; color: var(--fg); width: 80px; text-align: right; flex-shrink: 0; }}
.items-list {{ display: flex; flex-direction: column; gap: 10px; }}
.waste-item {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; cursor: pointer; transition: transform .15s, box-shadow .15s, border-color .15s; display: flex; align-items: center; justify-content: space-between; gap: 16px; }}
.waste-item:hover {{ transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,0,0,.07); border-color: #bfdbfe; }}
.wi-left {{ flex: 1; min-width: 0; }}
.wi-top {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }}
.wi-id {{ font-size: 11px; font-weight: 700; color: var(--muted); font-family: monospace; }}
.wi-type {{ font-size: 11px; color: var(--muted); background: var(--bg); border: 1px solid var(--border); padding: 1px 7px; border-radius: 4px; }}
.conf-pill {{ font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: .05em; }}
.wi-desc {{ font-size: 13px; color: var(--fg); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.wi-quote {{ border-left: 3px solid #cbd5e1; padding: 8px 14px; background: #f8fafc; border-radius: 0 6px 6px 0; font-style: italic; font-size: 12px; color: #374151; margin-top: 8px; line-height: 1.5; }}
.wi-quote cite {{ display: block; margin-top: 4px; font-style: normal; font-size: 11px; color: #94a3b8; font-weight: 600; }}
.wi-source-label {{ font-size: 11px; color: #64748b; margin-top: 6px; font-weight: 500; }}
.wi-right {{ text-align: right; flex-shrink: 0; }}
.wi-amt-val {{ font-size: 18px; font-weight: 800; color: var(--fg); display: block; }}
.wi-amt-label {{ font-size: 11px; color: var(--muted); }}
.wi-hrs {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}
.wi-unquant {{ font-size: 12px; color: var(--muted); font-style: italic; }}
.wi-formula {{ font-size: 11px; color: var(--muted); margin-top: 4px; white-space: nowrap; }}
.wi-rec-link {{ display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #1e293b; color: #ffffff; font-size: 10px; text-decoration: none; flex-shrink: 0; transition: opacity .15s; }}
.wi-rec-link:hover {{ opacity: .8; }}
.wi-doc-link {{ display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #e0e7ff; color: #3730a3; font-size: 10px; text-decoration: none; flex-shrink: 0; transition: opacity .15s; }}
.wi-doc-link:hover {{ opacity: .8; }}
.modal-overlay {{ display: none; position: fixed; inset: 0; background: rgba(15,24,37,.55); backdrop-filter: blur(4px); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }}
.modal-overlay.open {{ display: flex; }}
.modal-body {{ background: var(--card); border-radius: 16px; max-width: 600px; width: 100%; max-height: 90vh; overflow-y: auto; padding: 36px; position: relative; box-shadow: 0 24px 60px rgba(0,0,0,.2); }}
.modal-top {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
.modal-id {{ font-size: 12px; font-weight: 700; color: var(--muted); font-family: monospace; background: var(--bg); padding: 3px 8px; border-radius: 4px; }}
.modal-conf {{ font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 4px; }}
.modal-desc {{ font-size: 16px; line-height: 1.6; margin-bottom: 20px; }}
.modal-stats {{ display: flex; gap: 24px; flex-wrap: wrap; background: var(--bg); border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
.modal-stat-val {{ font-size: 22px; font-weight: 800; color: var(--fg); }}
.modal-stat-lbl {{ font-size: 12px; color: var(--muted); }}
.modal-quote {{ border-left: 3px solid #cbd5e1; padding: 12px 18px; background: #f8fafc; border-radius: 0 8px 8px 0; font-style: italic; font-size: 14px; color: #374151; margin-bottom: 16px; line-height: 1.6; }}
.modal-meta {{ font-size: 13px; color: var(--muted); margin-bottom: 24px; }}
.btn-recording {{ display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #ffffff; font-weight: 700; font-size: 13px; padding: 10px 20px; border-radius: 8px; text-decoration: none; margin-bottom: 12px; transition: opacity .15s; }}
.btn-recording:hover {{ opacity: .85; }}
.btn-close {{ display: block; width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--muted); font-size: 13px; font-family: inherit; cursor: pointer; }}
.btn-close:hover {{ background: var(--bg); }}
.modal-close-x {{ position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 20px; color: var(--muted); cursor: pointer; padding: 4px 8px; border-radius: 4px; }}
.modal-close-x:hover {{ background: var(--bg); }}
@media (max-width: 600px) {{ .waste-root {{ padding: 24px 16px 60px; }} .modal-body {{ padding: 24px; }} .bar-label {{ width: 120px; }} }}
{_PORTAL_TOPBAR_CSS}
{_PORTAL_FOOTER_CSS}
{_PORTAL_TYPOGRAPHY_CSS}
</style>
</head>
<body>
{_portal_topbar_html("Hidden costs", company, _portal_status_pill(sections), is_demo=sections.get("is_demo", False))}
<div class="waste-root">
  <div class="hero">
    <div class="hero-eyebrow">Hidden Costs</div>
    <div class="hero-amount">{fmt_aud(total_annual)}</div>
    <div class="hero-label">estimated annual opportunity</div>
    <div class="hero-stats">
      <div><div class="hero-stat-val">{len(waste_items)}</div><div class="hero-stat-lbl">opportunity areas</div></div>
      <div><div class="hero-stat-val">{total_hrs_pw:.1f}</div><div class="hero-stat-lbl">hrs/week recoverable</div></div>
      <div><div class="hero-stat-val">${blended_rate}<span style="font-size:14px;font-weight:600">/hr</span></div><div class="hero-stat-lbl">default hourly rate</div></div>
    </div>
    <div class="hero-basis">Each opportunity area uses a role-specific hourly rate where discussed, falling back to <strong>${blended_rate}/hr</strong> as a default estimate. Rates marked <em>(est)</em> will be validated during your review call. The rate used is shown on each row.</div>
  </div>

  <div class="breakdown">
    <div class="breakdown-title">Breakdown by opportunity type</div>
    {bars_html}
  </div>

  <div class="items-list">
    {items_html}
  </div>

  <div class="modal-overlay" id="waste-modal" role="dialog" aria-modal="true">
    <div class="modal-body">
      <button class="modal-close-x" id="modal-close-x" aria-label="Close">&times;</button>
      <div class="modal-top">
        <span class="modal-id" id="modal-id"></span>
        <span class="modal-conf" id="modal-conf"></span>
      </div>
      <p class="modal-desc" id="modal-desc"></p>
      <div class="modal-stats" id="modal-stats"></div>
      <blockquote class="modal-quote" id="modal-quote-wrap"><span id="modal-quote"></span><cite id="modal-quote-attr" style="display:block;margin-top:8px;font-style:normal;font-size:12px;color:#64748b;font-weight:600"></cite></blockquote>
      <div class="modal-meta" id="modal-meta"></div>
      <div id="modal-calc-note" style="display:none;margin-bottom:16px"><div style="font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#94a3b8;margin-bottom:8px">How we calculated this</div><div id="modal-calc-body" style="font-size:12px;color:#475569;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;line-height:1.7"></div></div>
      <div id="modal-source-doc" style="display:none;margin-bottom:16px"></div>
      <div id="modal-rec-wrap"></div>
      <button class="btn-close" id="modal-close-btn">Close</button>
    </div>
  </div>
</div>

<script>
const ITEMS = {items_json};
const itemMap = Object.fromEntries(ITEMS.map(i => [i.id, i]));
const modal = document.getElementById('waste-modal');
const confColors = {{ HIGH:['#166534', '#ffffff','#14532d'], MEDIUM:['#fef3c7','#92400e','#fcd34d'], LOW:['#f1f5f9','#475569','#cbd5e1'] }};

function fmtAud(v) {{
  if (v == null) return null;
  return '$' + Math.round(v).toLocaleString('en-AU');
}}

function openModal(id) {{
  const d = itemMap[id]; if (!d) return;
  document.getElementById('modal-id').textContent = d.id;
  const conf = document.getElementById('modal-conf');
  conf.textContent = d.confidence;
  const [bg,fg,bd] = confColors[d.confidence] || ['#f1f5f9','#475569','#cbd5e1'];
  conf.style.cssText = `background:${{bg}};color:${{fg}};border:1px solid ${{bd}}`;
  document.getElementById('modal-desc').textContent = d.description;
  const stats = document.getElementById('modal-stats');
  let statsHtml = '';
  if (d.annual || d.derivedAnnual) statsHtml += `<div><div class="modal-stat-val">${{fmtAud(d.annual || d.derivedAnnual)}}</div><div class="modal-stat-lbl">per year${{d.annual ? '' : '*'}}</div></div>`;
  if (d.hoursPerWeek) statsHtml += `<div><div class="modal-stat-val">${{d.hoursPerWeek}}</div><div class="modal-stat-lbl">hrs/week</div></div>`;
  if (d.headcount) statsHtml += `<div><div class="modal-stat-val">${{d.headcount}}</div><div class="modal-stat-lbl">people affected</div></div>`;
  if (d.hourlyRate) statsHtml += `<div><div class="modal-stat-val">${{d.hourlyRate}}/hr</div><div class="modal-stat-lbl">${{d.rateIsEstimated ? 'estimated rate' : 'discussed rate'}}</div></div>`;
  stats.innerHTML = statsHtml;
  stats.style.display = statsHtml ? '' : 'none';
  const qwrap = document.getElementById('modal-quote-wrap');
  if (d.quote) {{
    document.getElementById('modal-quote').textContent = '\u201c' + d.quote + '\u201d';
    const attrParts = [d.speaker, d.sessionLabel, d.timestampFmt].filter(Boolean);
    document.getElementById('modal-quote-attr').textContent = attrParts.join(' \u00b7 ');
    qwrap.style.display = '';
  }} else {{ qwrap.style.display = 'none'; }}
  const metaParts = [];
  if (d.sessionLabel) metaParts.push(d.sessionLabel);
  if (d.timestampFmt) metaParts.push(d.timestampFmt);
  if (!d.sessionLabel && d.sourceDocument) metaParts.push(d.sourceType ? d.sourceType.charAt(0).toUpperCase() + d.sourceType.slice(1) + ': ' + d.sourceDocument : 'Source: ' + d.sourceDocument);
  if (d.correctionNote) metaParts.push('Note: ' + d.correctionNote);
  document.getElementById('modal-meta').textContent = metaParts.join(' \u00b7 ');
  const calcEl = document.getElementById('modal-calc-note');
  const calcBody = document.getElementById('modal-calc-body');
  if (calcEl && calcBody) {{
    let calcText = d.calculationNote;
    if (!calcText && d.hoursPerWeek && d.hourlyRate) {{
      const parts = [d.hoursPerWeek + ' hrs/wk'];
      if (d.headcount && d.headcount > 1) parts.push(d.headcount + ' people');
      parts.push('$' + d.hourlyRate + '/hr');
      parts.push('52 weeks');
      const result = fmtAud(d.annual || d.derivedAnnual);
      calcText = parts.join(' \u00d7 ') + (result ? ' = ' + result + '/yr' : '');
      if (d.rateIsEstimated) calcText += '. Rate is a blended estimate.';
    }}
    if (calcText) {{
      const sentences = calcText.split(/(?<=\.)\s+(?=[A-Z$0-9~])/);
      calcBody.innerHTML = sentences.map(s => '<p style="margin:0 0 6px">' + s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</p>').join('');
      calcEl.style.display = '';
    }} else {{
      calcEl.style.display = 'none';
    }}
  }}
  const srcDocEl = document.getElementById('modal-source-doc');
  if (srcDocEl) {{
    const isFathomTranscript = d.sourceDocument && /^meetings\//.test(d.sourceDocument);
    // Suppress the redundant source-doc section when the source is a Fathom transcript and
    // we already have the Fathom recording button, that button IS the source link.
    if (d.sourceDocument && !(isFathomTranscript && d.recHref)) {{
      const docLabel = d.sourceDocument.split('/').pop().replace(/\.\w+$/, '').replace(/[-_]/g, ' ');
      if (d.sourceDocHref) {{
        srcDocEl.innerHTML = '<div style="font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#94a3b8;margin-bottom:8px">Source</div>'
          + '<a class="btn-recording" href="' + d.sourceDocHref + '" target="_blank" rel="noopener">&#128196; ' + docLabel + '</a>';
      }} else {{
        srcDocEl.innerHTML = '<div style="font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#94a3b8;margin-bottom:8px">Source</div>'
          + '<span style="font-size:12px;color:#64748b">&#128196; ' + docLabel + '</span>';
      }}
      srcDocEl.style.display = '';
    }} else {{
      srcDocEl.style.display = 'none';
    }}
  }}
  const recWrap = document.getElementById('modal-rec-wrap');
  recWrap.innerHTML = d.recHref ? '<a class="btn-recording" href="' + d.recHref + '" target="_blank" rel="noopener">&#9654; Watch in recording &rarr;</a><br>' : '';
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function closeModal() {{ modal.classList.remove('open'); document.body.style.overflow = ''; }}

document.querySelectorAll('.waste-item').forEach(el => {{
  el.addEventListener('click', () => openModal(el.dataset.id));
  el.addEventListener('keydown', e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openModal(el.dataset.id); }} }});
}});
document.getElementById('modal-close-x').addEventListener('click', closeModal);
document.getElementById('modal-close-btn').addEventListener('click', closeModal);
modal.addEventListener('click', e => {{ if (e.target === modal) closeModal(); }});
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});
</script>
{_portal_footer_html()}
</body>
</html>"""


# ─── CLI ───────────────────────────────────────────────────────────────────────

import re as _re_mod

_PRICING_PATTERN = _re_mod.compile(
    r'\$\d|/mo\b|/yr\b|/user|/seat|per.user|per-user|per.seat|per-seat'
    r'|pricing\b|priced|price\b|\bfree\b|\bcosts?\b|\bcheap|\bexpens'
    r'|\bupsell|\bsubscription|\btier\b|\bpaid\b|\bafford',
    _re_mod.IGNORECASE)

def generate_blueprint(ssad: dict, sections: dict = None) -> str:
    """Generate blueprint.html, AI Implementation Blueprint scroll journey.

    Sections: hero stats, three-layer education, current tool stack, four solution
    type explainers, initiative cards with modals, priority matrix, demo videos,
    phased roadmap grouped by payback tier.
    """
    sections = sections or {}
    company = escape(ssad.get("company_name", "Client"))
    generated_date = datetime.now().strftime("%d %b %Y")
    changes = ssad.get("proposed_changes", [])
    plugin_bundles = ssad.get("plugin_bundles", [])
    bundle_by_id = {b.get("bundle_id", ""): b for b in plugin_bundles}
    change_by_id = {c.get("change_id", ""): c for c in changes}
    bundled_cids: set = set()
    for _b in plugin_bundles:
        for _cid in (_b.get("covered_change_ids") or []):
            bundled_cids.add(_cid)
    roi_items = ssad.get("roi_items", [])
    tools = ssad.get("tools", [])
    pain_points = ssad.get("pain_points", [])
    blended_rate = ssad.get("blended_hourly_rate_aud", 40) or 40
    waste_items_all = ssad.get("waste_items", []) or []
    wi_by_id = {w.get("waste_id", ""): w for w in waste_items_all}

    # Build pain point lookup for quote attribution
    pp_by_id = {p.get("pain_point_id", ""): p for p in pain_points}
    # Build roi lookup for payback_tag
    roi_by_id = {r.get("roi_item_id", ""): r for r in roi_items}
    # Build sessions lookup for Fathom URL resolution (source-trail rendering)
    sessions = ssad.get("sessions", []) or []
    session_map = {s.get("session_number"): s for s in sessions}

    def _resolve_fathom_url(sess_num, ts):
        """Reconstruct a Fathom deep-link from a session number + seconds offset."""
        if sess_num is None or ts is None:
            return ""
        sess = session_map.get(sess_num)
        if not sess or not sess.get("fathom_url"):
            return ""
        return f"{sess['fathom_url']}?t={ts}"

    # Build materials index for non-Fathom source documents (Loom transcripts, admin docs,
    # emails, etc.). Mirrors the closure used inside generate_waste, keep behaviour identical.
    import os as _os_bp
    _client_dir_bp = _get_client_dir(ssad.get("client_slug", ""))
    _materials_dir_bp = _get_client_subdir(ssad.get("client_slug", ""), "01-materials/documents")
    _mat_index_bp: dict = {}
    if _materials_dir_bp.is_dir():
        for _root_bp, _dirs_bp, _fnames_bp in _os_bp.walk(_materials_dir_bp):
            for _fname_bp in _fnames_bp:
                _full_bp = Path(_root_bp) / _fname_bp
                _rel_bp = str(_full_bp.relative_to(_materials_dir_bp)).replace("\\", "/")
                _mat_index_bp[_fname_bp.lower()] = _rel_bp
                _mat_index_bp[Path(_fname_bp).stem.lower()] = _rel_bp

    def _resolve_doc_href(doc_path: str):
        """Return a deployable relative URL (materials/...html) for a source_document path,
        or None if the path can't be resolved or points into meetings/ (Fathom-handled).
        Same normalization logic as waste.html's _resolve_waste_href so links resolve to the
        same per-client deploy bundle."""
        if not doc_path:
            return None
        norm = doc_path.replace("\\", "/")
        norm = re.sub(r"^client-provided-materials/", "", norm)
        if norm.startswith("meetings/"):
            return None
        if norm.endswith("/"):
            candidate = norm + "email.txt"
            if (_materials_dir_bp / candidate).exists():
                return f"materials/{str(Path(candidate).with_suffix('.html'))}"
            else:
                return None
        sfx = Path(norm).suffix.lower()
        nm = Path(norm).name
        if "/" not in norm:
            norm = _mat_index_bp.get(nm.lower()) or _mat_index_bp.get(Path(nm).stem.lower())
            if not norm:
                return None
        else:
            if nm.lower() not in _mat_index_bp and Path(nm).stem.lower() not in _mat_index_bp:
                return None
            if norm.lower() not in {v.lower() for v in _mat_index_bp.values()}:
                norm = _mat_index_bp.get(nm.lower()) or _mat_index_bp.get(Path(nm).stem.lower())
                if not norm:
                    return None
        sfx = Path(norm).suffix.lower()
        if sfx in {".docx", ".doc", ".xlsx", ".xls", ".xlsm"}:
            txt_k = (Path(norm).stem + ".txt").lower()
            txt_resolved = _mat_index_bp.get(txt_k)
            if txt_resolved:
                norm = txt_resolved
                sfx = ".txt"
        if sfx in {".md", ".txt"}:
            norm = str(Path(norm).with_suffix(".html"))
        return f"materials/{norm}"

    def _doc_label(doc_path: str) -> str:
        """Short human-readable label for a source_document, used inside the View button."""
        if not doc_path:
            return ""
        name = Path(doc_path).name
        stem = Path(name).stem
        stem = re.sub(r'^[a-z]+-\d+-', '', stem)
        stem = re.sub(r'^batch-\d+-', '', stem)
        lbl = stem.replace("-", " ").replace("_", " ").title()
        return (lbl[:42] + "…") if len(lbl) > 42 else lbl

    def _build_sources_for_change(c):
        """Per-change source list. Prefers `source_evidence[]` (written by EI from v2026-05-13);
        falls back to the legacy 2-hop join over linked_pain_point_ids + linked_waste_item_ids
        (or W-IDs regex-extracted from `value.formula`) for clients audited before that change.
        De-dupes by (source_session, source_timestamp_seconds). Caps at 6 entries.
        """
        sources = []
        ev = c.get("source_evidence") or []
        if ev:
            for e in ev:
                _doc = e.get("source_document") or ""
                sources.append({
                    "ref_id":                    e.get("ref_id", ""),
                    "ref_type":                  e.get("ref_type", ""),
                    "quote":                     e.get("quote", ""),
                    "speaker":                   e.get("speaker", ""),
                    "source_session":            e.get("source_session"),
                    "source_timestamp_seconds":  e.get("source_timestamp_seconds"),
                    "fathom_url":                e.get("fathom_url") or _resolve_fathom_url(e.get("source_session"), e.get("source_timestamp_seconds")),
                    "source_document":           _doc,
                    "source_doc_href":           _resolve_doc_href(_doc),
                })
        else:
            for ppid in (c.get("linked_pain_point_ids") or []):
                pp = pp_by_id.get(ppid, {})
                q = pp.get("source_quote") or pp.get("quote") or ""
                if not q:
                    continue
                sess_num = pp.get("source_session")
                ts = pp.get("source_timestamp_seconds")
                _doc = pp.get("source_document") or pp.get("source_material") or ""
                sources.append({
                    "ref_id": ppid, "ref_type": "pain_point",
                    "quote": q, "speaker": pp.get("speaker", ""),
                    "source_session": sess_num, "source_timestamp_seconds": ts,
                    "fathom_url": _resolve_fathom_url(sess_num, ts),
                    "source_document": _doc,
                    "source_doc_href": _resolve_doc_href(_doc),
                })
            wids = c.get("linked_waste_item_ids") or []
            if not wids:
                formula = (c.get("value", {}) or {}).get("formula", "") or ""
                wids = re.findall(r'W-\d+', formula)
            for wid in wids:
                w = wi_by_id.get(wid, {})
                q = w.get("source_quote") or ""
                if not q:
                    continue
                sess_num = w.get("source_session")
                ts = w.get("source_timestamp_seconds")
                _doc = w.get("source_document") or w.get("source_material") or ""
                sources.append({
                    "ref_id": wid, "ref_type": "waste_item",
                    "quote": q, "speaker": w.get("speaker", ""),
                    "source_session": sess_num, "source_timestamp_seconds": ts,
                    "fathom_url": _resolve_fathom_url(sess_num, ts),
                    "source_document": _doc,
                    "source_doc_href": _resolve_doc_href(_doc),
                })
        # De-dupe by (session, timestamp) for Fathom-sourced entries, by source_document for
        # non-Fathom entries; preserve any item with a unique attribution.
        seen = set()
        deduped = []
        for s in sources:
            sess = s.get("source_session")
            ts = s.get("source_timestamp_seconds")
            doc = s.get("source_document") or ""
            if sess is not None and ts is not None:
                key = ("fathom", sess, ts)
            elif doc:
                key = ("doc", doc)
            else:
                key = ("quote", (s.get("quote") or "")[:80])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(s)
        return deduped[:6]

    def _build_research_sources_for_change(c):
        """Collect research-origin URLs from tools_researched[] and industry_landscape.
        Returns a de-duped list of {tool_name, url, label} dicts for display as link pills."""
        research = c.get("research") or {}
        sources = []
        for tr in (research.get("tools_researched") or []):
            tool_name = tr.get("tool_name", "")
            if not tool_name:
                continue
            for url_field, label in [
                ("pricing_url", "Pricing"),
                ("docs_url", "API Docs"),
                ("url", "Website"),
            ]:
                url = tr.get(url_field)
                if url and str(url).strip():
                    sources.append({"tool_name": tool_name, "url": str(url).strip(), "label": label})
            for surl in (tr.get("source_urls") or []):
                if surl and str(surl).strip():
                    sources.append({"tool_name": tool_name, "url": str(surl).strip(), "label": "Reference"})
            for hc in (tr.get("hidden_costs") or []):
                surl = hc.get("source_url")
                if surl and str(surl).strip():
                    sources.append({"tool_name": tool_name, "url": str(surl).strip(), "label": "Hidden Cost Source"})
        il = research.get("industry_landscape") or {}
        for bm in (il.get("quantitative_benchmarks") or []):
            if not isinstance(bm, dict):
                continue
            surl = bm.get("source_url")
            src_name = bm.get("source") or "Industry Benchmark"
            if surl and str(surl).strip():
                sources.append({"tool_name": src_name, "url": str(surl).strip(), "label": "Benchmark"})
        seen = set()
        deduped = []
        for s in sources:
            if s["url"] not in seen:
                seen.add(s["url"])
                deduped.append(s)
        return deduped

    def _render_research_sources_html(research_sources):
        """Render research tool source URLs as link pills appended inside the Sources section."""
        if not research_sources:
            return ""
        pills = []
        for s in research_sources:
            tool = escape(s.get("tool_name", ""))
            url = escape(s.get("url", ""))
            label = escape(s.get("label", "Reference"))
            pills.append(
                f'<a href="{url}" target="_blank" rel="noopener" onclick="event.stopPropagation()" '
                f'style="display:inline-flex;align-items:center;gap:4px;background:#166534;border:1px solid #14532d;'
                f'border-radius:6px;padding:4px 10px;margin:3px 2px;font-size:11px;color:#ffffff;'
                f'text-decoration:none;font-weight:600">'
                f'{tool}: {label} &#8599;</a>'
            )
        return (
            '<div style="margin-top:12px">'
            '<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'
            'color:#94a3b8;margin-bottom:6px">Research sources</div>'
            '<div style="display:flex;flex-wrap:wrap;gap:2px">'
            + "".join(pills)
            + '</div></div>'
        )

    ACCESS_DOT = {
        "sheets_mcp": "#22c55e", "drive_mcp": "#22c55e",
        "gmail_mcp": "#ef4444",
        "xero_api": "#3b82f6", "other_mcp": "#3b82f6",
        "manual_upload": "#94a3b8", "human_text_input": "#94a3b8",
    }

    def _render_skill_workflow_html(skill_def):
        """Render structured trigger/inputs/steps/outputs visualization for a cowork plugin skill.

        Skills may have inputs/workflow_steps/outputs as either structured lists (with dict items)
        or flat strings (legacy/compact form from sub-agent rate). Both are supported.
        """
        trigger = escape(skill_def.get("trigger", "") or "")
        inputs = skill_def.get("inputs") or []
        steps = skill_def.get("workflow_steps") or []
        outputs = skill_def.get("outputs") or []

        def _plain_block(label, text):
            return (
                '<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;'
                f'color:#94a3b8;margin-bottom:8px">{label}</div>'
                '<div style="font-size:12px;color:#374151;line-height:1.6;margin-bottom:16px">'
                f'{escape(text)}</div>'
            )

        trigger_html = (
            '<div style="display:flex;align-items:center;gap:8px;background:#fff7ed;border:1px solid #fed7aa;'
            'border-radius:8px;padding:10px 14px;margin-bottom:16px">'
            '<span style="font-size:14px">&#9200;</span>'
            f'<span style="font-size:12px;color:#c2410c;font-weight:600">{trigger}</span>'
            '</div>'
        ) if trigger else ""

        input_pills = ""
        if isinstance(inputs, str):
            input_pills = _plain_block("Inputs", inputs)
        elif inputs:
            pills = []
            for inp in inputs:
                if not isinstance(inp, dict):
                    pills.append(
                        '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:5px 10px">'
                        f'<span style="font-size:11px;font-weight:600;color:#0f1825">{escape(str(inp))}</span>'
                        '</div>'
                    )
                    continue
                name = escape(inp.get("name", ""))
                fmt = escape(inp.get("format", ""))
                method = inp.get("access_method", "")
                dot_color = ACCESS_DOT.get(method, "#94a3b8")
                pills.append(
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:5px 10px;'
                    f'display:flex;align-items:center;gap:6px">'
                    f'<span style="width:7px;height:7px;border-radius:50%;background:{dot_color};flex-shrink:0"></span>'
                    f'<span style="font-size:11px;font-weight:600;color:#0f1825">{name}</span>'
                    + (f'<span style="font-size:10px;color:#94a3b8">{fmt}</span>' if fmt else '')
                    + '</div>'
                )
            input_pills = (
                '<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;'
                'color:#94a3b8;margin-bottom:8px">Inputs</div>'
                '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">'
                + "".join(pills)
                + '</div>'
            )

        steps_html = ""
        if isinstance(steps, str):
            steps_html = _plain_block("Process", steps)
        elif steps:
            rows = []
            for i, step in enumerate(steps):
                rows.append(
                    f'<div style="display:flex;gap:12px;align-items:flex-start;padding:6px 0;'
                    f'border-bottom:{("1px solid #f1f5f9" if i < len(steps) - 1 else "none")}">'
                    f'<span style="min-width:20px;height:20px;border-radius:50%;background:#f97316;color:#fff;'
                    f'font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">{i + 1}</span>'
                    f'<span style="font-size:12px;color:#374151;line-height:1.5">{escape(str(step))}</span>'
                    '</div>'
                )
            steps_html = (
                '<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;'
                'color:#94a3b8;margin-bottom:8px">Process</div>'
                '<div style="background:#f8fafc;border-left:3px solid #f97316;border-radius:0 8px 8px 0;'
                'padding:8px 14px;margin-bottom:16px">'
                + "".join(rows)
                + '</div>'
            )

        output_pills = ""
        if isinstance(outputs, str):
            output_pills = _plain_block("Outputs", outputs)
        elif outputs:
            pills = []
            for out in outputs:
                if not isinstance(out, dict):
                    pills.append(
                        '<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:5px 10px">'
                        f'<div style="font-size:11px;font-weight:600;color:#166534">{escape(str(out))}</div>'
                        '</div>'
                    )
                    continue
                name = escape(out.get("name", ""))
                dest = escape(out.get("destination", ""))
                pills.append(
                    f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:5px 10px">'
                    f'<div style="font-size:11px;font-weight:600;color:#166534">{name}</div>'
                    + (f'<div style="font-size:10px;color:#64748b;margin-top:2px">{dest}</div>' if dest else '')
                    + '</div>'
                )
            output_pills = (
                '<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;'
                'color:#94a3b8;margin-bottom:8px">Outputs</div>'
                '<div style="display:flex;flex-wrap:wrap;gap:6px">'
                + "".join(pills)
                + '</div>'
            )

        return (
            '<div class="bp-modal-section"><h4>How This Skill Works</h4>'
            + trigger_html
            + input_pills
            + steps_html
            + output_pills
            + '</div>'
        )

    def _render_sources_html(sources_list):
        """Render the 'Sources' action-panel section for a blueprint modal. Quote + speaker
        + green Fathom button per entry (target=_blank for new-tab opening, matching findings.html)."""
        if not sources_list:
            return ""
        REF_TYPE_BADGES = {
            "pain_point":  ("#fef2f2", "#b91c1c", "Pain Point"),
            "waste_item":  ("#fefce8", "#a16207", "Waste"),
            "optimisation": ("#166534", "#ffffff", "Optimisation"),
        }
        pills = []
        for s in sources_list:
            ref_id = escape(s.get("ref_id", "") or "")
            bg, fg, lbl = REF_TYPE_BADGES.get(s.get("ref_type", ""), ("#f1f5f9", "#475569", "Source"))
            quote_raw = (s.get("quote") or "")[:240]
            quote = escape(quote_raw)
            speaker = escape(s.get("speaker") or "")
            sess_num = s.get("source_session")
            ts = s.get("source_timestamp_seconds")
            rec_href = s.get("fathom_url") or ""
            doc_href = s.get("source_doc_href") or ""
            doc_path = s.get("source_document") or ""
            ts_label = ""
            if isinstance(ts, (int, float)):
                ts_label = f"{int(ts) // 60}:{int(ts) % 60:02d}"
            rec_btn = (
                f'<a class="bp-rec-link" href="{escape(rec_href)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">'
                f'&#9654; Open recording{(" at " + ts_label) if ts_label else ""}</a>'
            ) if rec_href else ""
            doc_btn = ""
            if doc_href:
                doc_btn = (
                    f'<a class="bp-doc-link" href="{escape(doc_href)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" '
                    + (' style="margin-left:8px"' if rec_btn else '') + '>'
                    f'&#128196; View source: {escape(_doc_label(doc_path))}</a>'
                )
            elif doc_path and not rec_btn:
                # We know where it came from but the file isn't deployed (e.g. raw .docx without text-extracted twin).
                doc_btn = (
                    '<span class="bp-doc-link" style="opacity:.55;cursor:default">'
                    f'&#128196; Source: {escape(_doc_label(doc_path))}</span>'
                )
            attribution = ""
            if speaker or sess_num is not None:
                bits = []
                if speaker:
                    bits.append(speaker)
                if sess_num is not None:
                    bits.append(f"Session {sess_num}")
                attribution = (
                    '<div style="margin-top:6px;font-size:11px;color:#64748b;font-weight:600">-'
                    + escape(" · ".join(bits))
                    + '</div>'
                )
            pills.append(
                '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;margin:8px 0">'
                '<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">'
                f'<span style="background:{bg};color:{fg};font-size:9px;font-weight:700;padding:2px 7px;border-radius:4px;text-transform:uppercase;letter-spacing:0.05em">{lbl}</span>'
                + (f'<span style="font-size:10px;color:#94a3b8;font-family:monospace;font-weight:600">{ref_id}</span>' if ref_id else '')
                + '</div>'
                f'<div style="font-size:13px;color:#374151;font-style:italic;line-height:1.55">&ldquo;{quote}&rdquo;</div>'
                + attribution
                + (f'<div style="margin-top:10px;display:flex;flex-wrap:wrap;align-items:center;gap:6px">{rec_btn}{doc_btn}</div>' if (rec_btn or doc_btn) else '')
                + '</div>'
            )
        return (
            '<div class="bp-modal-section"><h4>Sources</h4>'
            + "".join(pills)
            + '</div>'
        )

    # Hero stats
    total_annual_value = sum(
        c.get("value", {}).get("combined_annual_value_aud", 0) or 0
        for c in changes
        if c.get("solution_type") != "process_change"
    )
    n_changes = len([c for c in changes if c.get("solution_type") != "process_change"])
    weekly_hours = round(total_annual_value / blended_rate / 52, 0) if total_annual_value else 0

    # Solution type config
    SOL_COLORS = {
        "cowork_plugin":   {"border": "#f97316", "label": "Cowork Plugin",  "bg": "#fff7ed", "text": "#c2410c", "tag_bg": "#f97316", "tag_label": "Staff-facing"},
        "n8n_automation":  {"border": "#3B82F6", "label": "Automation",     "bg": "#eff6ff", "text": "#1D4ED8", "tag_bg": "#3B82F6", "tag_label": "Background"},
        "custom_build":    {"border": "#22c55e", "label": "Custom Build",   "bg": "#0f1825", "text": "#22c55e", "tag_bg": "#22c55e", "tag_label": "Full platform"},
        "data_migration":  {"border": "#7C3AED", "label": "Data Migration", "bg": "#f5f3ff", "text": "#6D28D9", "tag_bg": "#7C3AED", "tag_label": "Foundation"},
    }
    PAYBACK_COLORS = {"QUICK_WIN": "#22c55e", "CORE_BUILD": "#3B82F6", "FUTURE": "#f97316"}

    def weeks_to_effort(label):
        if not label:
            return 2
        l = label.lower()
        if "<1" in l or "< 1" in l:
            return 0.5
        if "1-2" in l:
            return 1.5
        if "2-4" in l:
            return 3
        if "4+" in l or "4 +" in l:
            return 5
        try:
            return float(re.findall(r"[\d.]+", l)[0])
        except Exception:
            return 2

    def fmt_aud_k(v):
        if v >= 1000:
            return f"${v/1000:.0f}K" if v % 1000 == 0 else f"${v/1000:.1f}K"
        return f"${v:,}"

    # ── INITIATIVE CARDS ─────────────────────────────────────────────────────────
    def _card(c, idx):
        cid = c.get("change_id", f"CH-{idx:03d}")
        title = escape(c.get("title", "Untitled"))
        sol = c.get("solution_type", "n8n_automation")
        sc = SOL_COLORS.get(sol, SOL_COLORS["n8n_automation"])
        val = c.get("value", {}).get("combined_annual_value_aud", 0) or 0
        impl = c.get("implementation", {}) or {}
        weeks = impl.get("weeks_label", "")
        effort_band = impl.get("effort_band", "")
        primary_tool = escape(impl.get("primary_tool", ""))
        roi_item = roi_by_id.get(c.get("linked_roi_item_id", ""), {})
        payback_tag = roi_item.get("payback_tag", "")
        payback_months = roi_item.get("payback_months", 0) or 0

        # Quote from first linked pain point with a source_quote
        quote_html = ""
        for ppid in (c.get("linked_pain_point_ids") or []):
            pp = pp_by_id.get(ppid, {})
            q = pp.get("source_quote", "") or pp.get("quote", "")
            if q:
                speaker = escape(pp.get("speaker") or "Client")
                quote_html = f"""<div style="background:#f8fafc;border-left:3px solid {sc['border']};border-radius:0 8px 8px 0;padding:10px 14px;margin:12px 0;font-size:12px;color:#374151;line-height:1.55;font-style:italic">
  &ldquo;{escape(q[:160])}&rdquo;
  <div style="font-size:10px;color:#64748b;margin-top:4px;font-style:normal;font-weight:600">,  {speaker}</div>
</div>"""
                break

        # Payback badge
        pb_color = PAYBACK_COLORS.get(payback_tag, "#64748b")
        pb_label = payback_tag.replace("_", " ").title() if payback_tag else ""
        pb_html = f'<span style="background:{pb_color};color:#fff;font-size:9px;font-weight:700;padding:3px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:0.05em">{pb_label}</span>' if pb_label else ""

        # Modal content
        mc = c.get("modal_content", {}) or {}
        headline = escape(mc.get("headline", title))
        problem = escape(mc.get("the_problem", c.get("proposed_solution", ""))[:500])
        solution_text = escape(mc.get("the_solution", "")[:500])
        value_text = escape(mc.get("the_value", "")[:400])
        _wwb_raw = mc.get("what_we_build", "") or ""
        if isinstance(_wwb_raw, list):
            _wwb_raw = " ".join(str(x) for x in _wwb_raw)
        what_we_build = escape(str(_wwb_raw)[:400])
        risks = escape(mc.get("risks_and_notes", impl.get("risks_summary", ""))[:300])
        formula = c.get("value", {}).get("formula", "")

        # Calculation box, plain readable text, no monospace code block
        calc_html = (
            '<div style="background:#f8fafc;border-left:3px solid #cbd5e1;border-radius:0 6px 6px 0;'
            'padding:8px 12px;font-size:11px;color:#374151;margin:10px 0;line-height:1.65">'
            '<span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'
            'color:#94a3b8;display:block;margin-bottom:4px">How we calculated this</span>'
            + escape(formula[:400])
            + '</div>'
        ) if formula else ""

        # Source waste item pills, prefer explicit linked_waste_item_ids[], fall back to W-ID regex on formula
        _formula_wids = re.findall(r'W-\d+', formula) if formula else []
        _wids = list(c.get("linked_waste_item_ids") or []) or _formula_wids
        # Preserve order, de-dupe
        _seen = set()
        _wids_ordered = [w for w in _wids if not (w in _seen or _seen.add(w))]
        _waste_sources = [wi_by_id[wid] for wid in _wids_ordered if wid in wi_by_id]
        source_pills_html = ""
        if _waste_sources:
            _pills = []
            for _ws in _waste_sources:
                _wid = escape(_ws.get("waste_id", ""))
                _act = escape(str(_ws.get("activity", ""))[:70])
                _hrs = _ws.get("hours_per_week") or 0
                _hrs_str = (f"{_hrs:.2f}".rstrip('0').rstrip('.') or "0") + " hrs/wk"
                _sq = _ws.get("source_quote", "") or ""
                _spkr = escape(_ws.get("speaker", "") or "")
                _w_sess = _ws.get("source_session")
                _w_ts = _ws.get("source_timestamp_seconds")
                _w_rec = _resolve_fathom_url(_w_sess, _w_ts)
                _w_ts_label = f"{int(_w_ts) // 60}:{int(_w_ts) % 60:02d}" if isinstance(_w_ts, (int, float)) else ""
                _w_doc = _ws.get("source_document") or ""
                _w_doc_href = _resolve_doc_href(_w_doc)
                _rec_btn = (
                    f'<a class="bp-rec-link" href="{escape(_w_rec)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="font-size:11px;padding:5px 10px">'
                    f'&#9654; Open recording{(" at " + _w_ts_label) if _w_ts_label else ""}</a>'
                ) if _w_rec else ""
                _doc_btn = ""
                if _w_doc_href:
                    _doc_btn = (
                        f'<a class="bp-doc-link" href="{escape(_w_doc_href)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="font-size:11px;padding:5px 10px">'
                        f'&#128196; View source: {escape(_doc_label(_w_doc))}</a>'
                    )
                elif _w_doc and not _rec_btn:
                    _doc_btn = (
                        '<span class="bp-doc-link" style="font-size:11px;padding:5px 10px;opacity:.55;cursor:default">'
                        f'&#128196; Source: {escape(_doc_label(_w_doc))}</span>'
                    )
                _action_row = (
                    f'<div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:6px;align-items:center">{_rec_btn}{_doc_btn}</div>'
                ) if (_rec_btn or _doc_btn) else ""
                _quote_block = (
                    '<div style="margin-top:4px;font-size:10px;color:#64748b;font-style:italic;line-height:1.45">'
                    f'&ldquo;{escape(_sq[:120])}&rdquo;'
                    + (f' <span style="font-style:normal;font-weight:600">,  {_spkr}</span>' if _spkr else '')
                    + '</div>'
                ) if _sq else ""
                _pills.append(
                    '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:6px 10px;margin:4px 0">'
                    f'<span style="background:#0f1825;color:#fff;font-size:9px;font-weight:700;padding:2px 5px;border-radius:3px;margin-right:6px">{_wid}</span>'
                    f'<span style="font-size:11px;color:#374151;font-weight:600">{_act}</span>'
                    f'<span style="font-size:10px;color:#64748b;margin-left:6px">{_hrs_str}</span>'
                    + _quote_block
                    + _action_row
                    + '</div>'
                )
            source_pills_html = (
                '<div style="margin-top:10px">'
                '<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'
                'color:#94a3b8;margin-bottom:6px">Source data</div>'
                + "".join(_pills)
                + '</div>'
            )

        modal_id = f"modal-{cid}"
        _section_problem = ('<div class="bp-modal-section"><h4>The Problem</h4><p>' + problem + '</p></div>') if problem else ''
        _section_solution = ('<div class="bp-modal-section"><h4>The Solution</h4><p>' + solution_text + '</p></div>') if solution_text else ''
        _section_value = (
            '<div class="bp-modal-section"><h4>The Value</h4>'
            + ('<p>' + value_text + '</p>' if value_text else '')
            + calc_html
            + source_pills_html
            + '</div>'
        ) if (value_text or formula) else ''
        _skill_def = (c.get("research") or {}).get("skill_definition")
        if sol == "cowork_plugin" and _skill_def:
            _section_build = _render_skill_workflow_html(_skill_def)
        else:
            _section_build = ('<div class="bp-modal-section"><h4>What We Build</h4><p>' + what_we_build + '</p></div>') if what_we_build else ''
        _section_risks = ('<div class="bp-modal-section"><h4>Risks &amp; Notes</h4><p style="color:#64748b">' + risks + '</p></div>') if risks else ''
        _transcript_sources_html = _render_sources_html(_build_sources_for_change(c))
        _research_sources_html = _render_research_sources_html(_build_research_sources_for_change(c))
        if _transcript_sources_html and _research_sources_html:
            _section_sources = _transcript_sources_html[:-6] + _research_sources_html + '</div>'
        elif _research_sources_html:
            _section_sources = (
                '<div class="bp-modal-section"><h4>Sources</h4>'
                + _research_sources_html + '</div>'
            )
        else:
            _section_sources = _transcript_sources_html
        _EFFORT_LABELS = {"S": "Small", "M": "Medium", "L": "Large"}
        _stat_val = ('<div><span style="font-size:20px;font-weight:800;color:#0f1825;display:block">' + fmt_aud(val) + '/yr</span><span style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:#64748b">Annual value</span></div>') if val else ''
        _stat_cost = ('<div><span style="font-size:20px;font-weight:800;color:#0f1825;display:block">' + escape(_EFFORT_LABELS.get(effort_band, effort_band) + ' (' + effort_band + ')') + '</span><span style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:#64748b">Effort</span></div>') if effort_band else ''
        _stat_weeks = ('<div><span style="font-size:20px;font-weight:800;color:#0f1825;display:block">' + weeks + '</span><span style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:#64748b">Timeline</span></div>') if weeks else ''
        _has_tech_spec = bool(c.get("technical_spec"))
        _cid_safe = escape(c.get("change_id", ""))
        _tech_link = (
            f'<a href="#tech-{_cid_safe}" '
            f'onclick="document.getElementById(\'{modal_id}\').style.display=\'none\';'
            f'setTimeout(function(){{var el=document.getElementById(\'tech-appendix\');'
            f'if(el){{var d=el.querySelector(\'details\');if(d)d.open=true;}}var t=document.getElementById(\'tech-{_cid_safe}\');'
            f'if(t)t.scrollIntoView({{behavior:\'smooth\',block:\'start\'}});}},50)" '
            f'style="margin-left:auto;font-size:12px;font-weight:600;color:#166534;text-decoration:none">'
            f'View technical breakdown &#8595;</a>'
        ) if _has_tech_spec else ''
        modal_html = f"""<div id="{modal_id}" class="bp-modal-backdrop" style="display:none" onclick="if(event.target===this)this.style.display='none'">
  <div class="bp-modal">
    <button class="bp-modal-close" onclick="document.getElementById('{modal_id}').style.display='none'">&times;</button>
    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:{sc['border']};margin-bottom:8px">{escape(sc['label'])}</div>
    <h3 style="font-size:18px;font-weight:800;color:#0f1825;margin:0 0 16px;line-height:1.3">{headline}</h3>
    {_section_problem}
    {_section_solution}
    {_section_value}
    {_section_build}
    {_section_risks}
    {_section_sources}
    <div style="display:flex;gap:24px;margin-top:20px;padding-top:16px;border-top:1px solid #E5E7EB;flex-wrap:wrap;align-items:center">
      {_stat_val}{_stat_cost}{_stat_weeks}{_tech_link}
    </div>
  </div>
</div>"""

        is_dark = sol == "custom_build"
        card_bg = "#0f1825" if is_dark else "#fff"
        title_color = "#22c55e" if is_dark else "#0f1825"
        text_color = "#d1d5db" if is_dark else "#374151"
        border_color = sc["border"]

        return f"""{modal_html}
<div onclick="document.getElementById('{modal_id}').style.display='flex'"
     style="background:{card_bg};border:2px solid {border_color};border-radius:14px;padding:24px;cursor:pointer;transition:box-shadow 0.2s,transform 0.15s;position:relative;overflow:hidden"
     onmouseover="this.style.boxShadow='0 8px 32px rgba(0,0,0,0.12)';this.style.transform='translateY(-2px)'"
     onmouseout="this.style.boxShadow='none';this.style.transform='none'">
  <div style="position:absolute;top:0;right:0;background:{sc['tag_bg']};color:{'#0f1825' if sol == 'custom_build' else '#fff'};font-size:9px;font-weight:700;padding:4px 10px;border-radius:0 12px 0 8px;text-transform:uppercase;letter-spacing:0.05em">{escape(sc['tag_label'])}</div>
  <div style="font-size:13px;font-weight:800;color:{sc['text']};margin-bottom:8px;margin-top:4px">{escape(sc['label'])}</div>
  <div style="font-size:15px;font-weight:700;color:{title_color};margin-bottom:8px;line-height:1.35;padding-right:12px">{title}</div>
  {quote_html}
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;align-items:center">
    {'<span style="background:#166534;border:1px solid #14532d;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:700;color:#ffffff">' + fmt_aud(val) + '/yr</span>' if val else ''}
    {'<span style="background:#f8fafc;border:1px solid #E5E7EB;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600;color:#64748b">' + weeks + '</span>' if weeks else ''}
    {'<span style="background:#f8fafc;border:1px solid #E5E7EB;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600;color:#64748b">' + primary_tool + '</span>' if primary_tool else ''}
    {pb_html}
  </div>
  <div style="margin-top:12px;font-size:11px;font-weight:600;color:{'#7DFF00' if is_dark else '#64748b'}">View details &rarr;</div>
</div>"""

    def _bundle_card(bundle):
        bid = escape(bundle.get("bundle_id", ""))
        b_title = escape(bundle.get("plugin_title", ""))
        b_desc = bundle.get("description", "")
        b_val = bundle.get("combined_annual_value_aud", 0) or 0
        b_lo = bundle.get("price_range_low_aud", 0) or 0
        b_hi = bundle.get("price_range_high_aud", 0) or 0
        b_tier = (bundle.get("complexity_tier") or "").replace("_", " ").title()
        skills = bundle.get("skills") or []
        connectors = bundle.get("connectors") or []
        n_skills = len(skills)
        sc = SOL_COLORS["cowork_plugin"]
        modal_id = f"modal-{bid}"

        # Build per-skill blocks for the modal
        skill_blocks = ""
        for sk in skills:
            sk_title = escape(sk.get("skill_title", ""))
            sk_cid = sk.get("change_id", "")
            # Get individual change value
            sk_change = change_by_id.get(sk_cid, {})
            sk_val = sk_change.get("value", {}).get("combined_annual_value_aud", 0) or 0
            sk_val_html = (
                f'<span style="background:#166534;color:#fff;font-size:10px;font-weight:700;'
                f'padding:2px 8px;border-radius:4px;margin-left:8px">{fmt_aud(sk_val)}/yr</span>'
            ) if sk_val else ""
            workflow_html = _render_skill_workflow_html(sk)
            skill_blocks += (
                f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;'
                f'padding:16px 20px;margin-bottom:12px">'
                f'<div style="display:flex;align-items:center;margin-bottom:12px">'
                f'<span style="font-size:13px;font-weight:800;color:#c2410c">{sk_title}</span>'
                f'{sk_val_html}'
                f'</div>'
                + workflow_html
                + '</div>'
            )

        connector_pills = "".join(
            f'<span style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;'
            f'padding:3px 8px;font-size:10px;color:#64748b;font-weight:500">{escape(cn.get("name",""))}</span>'
            for cn in connectors
        )

        # Value breakdown: show how each change contributes to the plugin total
        _vb_rows = ""
        _covered_changes = [change_by_id[x] for x in (bundle.get("covered_change_ids") or []) if x in change_by_id]
        for _vc in _covered_changes:
            _vc_title = escape(_vc.get("title", ""))
            _vc_val = (_vc.get("value") or {}).get("combined_annual_value_aud", 0) or 0
            _vc_flines = _vb_formula_lines(_vc)
            _vc_conf = (_vc.get("value") or {}).get("confidence", "")
            _vc_conf_html = ""
            if _vc_conf:
                _vc_cc = {"HIGH": "#10B981", "MEDIUM": "#F59E0B", "LOW": "#EF4444"}.get(_vc_conf, "#64748b")
                _vc_conf_html = (f' <span style="background:{_vc_cc};color:#fff;padding:1px 5px;border-radius:3px;'
                                 f'font-size:9px;font-weight:600;margin-left:6px;vertical-align:middle">{_vc_conf}</span>')
            _vc_formula_html = "".join(
                f'<div style="color:#64748b;font-size:11px;font-family:monospace;margin-bottom:1px">{escape(fl)}</div>'
                for fl in _vc_flines
            )
            # Linked waste items
            _vc_waste_ids = _vc.get("linked_waste_item_ids") or []
            _vc_waste_html = ""
            if _vc_waste_ids:
                _vc_wchips = ""
                for _vwid in _vc_waste_ids:
                    _vw = wi_by_id.get(str(_vwid))
                    if not _vw:
                        continue
                    _vw_hrs = _vw.get("hours_per_week", 0) or 0
                    _vw_ann = _vw.get("annual_waste_aud", 0) or 0
                    _vw_act = escape((_vw.get("activity") or "")[:90])
                    _vw_quote = (_vw.get("source_quote") or "").strip()
                    _vw_sources = _vw.get("sources") or []
                    if not _vw_quote and _vw_sources:
                        _vw_quote = (_vw_sources[0].get("quote") or "").strip()
                    _vw_speaker = _vw.get("speaker") or ""
                    if not _vw_speaker and _vw_sources:
                        _vw_speaker = _vw_sources[0].get("speaker") or ""
                    _vw_mrefs = _vw.get("meeting_references") or []
                    _vw_furl = ""
                    if _vw_mrefs:
                        _vw_mid = _vw_mrefs[0].get("meeting_id", "")
                        _vw_ts = _vw_mrefs[0].get("timestamp_seconds", 0) or 0
                        if _vw_mid:
                            _vw_furl = f"https://fathom.video/calls/{_vw_mid}" + (f"?t={_vw_ts}" if _vw_ts else "")
                    _vw_link = ""
                    if _vw_furl:
                        _vw_link = (f' <a href="{escape(_vw_furl)}" target="_blank" rel="noopener" '
                                    f'style="font-size:10px;color:#166534;text-decoration:none;font-style:normal">'
                                    f'&#8599; Listen</a>')
                    _vw_qhtml = ""
                    if _vw_quote:
                        _vw_qhtml = (
                            f'<div style="font-size:10px;color:#94a3b8;font-style:italic;margin-top:1px;line-height:1.4">'
                            f'"{escape(_vw_quote[:120])}"'
                            f'{f", {escape(_vw_speaker)}" if _vw_speaker else ""}'
                            f'{_vw_link}'
                            f'</div>'
                        )
                    _vc_wchips += (
                        f'<div style="display:flex;align-items:baseline;gap:6px;padding:3px 0;'
                        f'border-bottom:1px dotted #e2e8f0">'
                        f'<span style="font-size:9px;font-weight:700;color:#166534;white-space:nowrap">{escape(str(_vwid))}</span>'
                        f'<div style="flex:1;min-width:0">'
                        f'<div style="font-size:10px;color:#374151">{_vw_act}</div>'
                        f'{_vw_qhtml}'
                        f'</div>'
                        f'<span style="font-size:10px;color:#64748b;white-space:nowrap;font-family:monospace">'
                        f'{_vw_hrs} hrs/wk</span>'
                        f'<span style="font-size:10px;color:#374151;white-space:nowrap;font-weight:600;font-family:monospace">'
                        f'{fmt_aud(_vw_ann)}/yr</span>'
                        f'</div>'
                    )
                if _vc_wchips:
                    _vc_waste_html = (
                        f'<div style="margin-top:4px;padding:4px 8px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:5px">'
                        f'<div style="font-size:9px;font-weight:700;color:#94a3b8;text-transform:uppercase;'
                        f'letter-spacing:.04em;margin-bottom:3px">Source waste identified in audit</div>'
                        f'{_vc_wchips}'
                        f'</div>'
                    )
            # Meeting reference evidence
            _vc_evidence = _vb_evidence(_vc)
            _vc_ev_html = ""
            if _vc_evidence:
                _vev = _vc_evidence[0]
                _vev_link = (f' <a href="{escape(_vev["url"])}" target="_blank" rel="noopener" '
                             f'style="font-size:10px;color:#166534;margin-left:6px;font-style:normal;text-decoration:none">'
                             f'&#8599; Session {_vev["session"]}</a>'
                             if _vev.get("url") else "")
                _vc_ev_html = (
                    f'<blockquote style="border-left:2px solid #e2e8f0;padding:3px 8px;margin:4px 0 0 0;'
                    f'font-size:10px;color:#64748b;font-style:italic;background:#fff;border-radius:0 4px 4px 0">'
                    f'"{escape(_vev["excerpt"][:150])}"{_vev_link}</blockquote>'
                )
            _vb_rows += (
                f'<div style="padding:8px 0;border-bottom:1px dashed #e2e8f0">'
                f'<div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline">'
                f'<div style="min-width:0;flex:1">'
                f'<div style="color:#0f1825;font-weight:600;font-size:12px;margin-bottom:2px">'
                f'{_vc_title}{_vc_conf_html}</div>'
                f'{_vc_formula_html}'
                f'</div>'
                f'<span style="color:#0f1825;white-space:nowrap;font-weight:700;font-size:13px">'
                f'{fmt_aud(_vc_val)}/yr</span></div>'
                f'{_vc_waste_html}'
                f'{_vc_ev_html}'
                f'</div>'
            )
        # Rollup line
        _vb_total_ts = sum(((c.get("value") or {}).get("time_saving") or {}).get("annual_saving_aud") or 0 for c in _covered_changes)
        _vb_total_pe = sum(((c.get("value") or {}).get("productivity_enhancement") or {}).get("estimated_annual_value_aud") or 0 for c in _covered_changes)
        _vb_total_rr = sum(((c.get("value") or {}).get("risk_reduction") or {}).get("annual_value_aud") or 0 for c in _covered_changes)
        _vb_total_cx = sum(
            ((c.get("value") or {}).get("customer_experience") or {}).get("annual_value_aud") or
            ((c.get("value") or {}).get("customer_experience") or {}).get("revenue_impact_aud") or 0
            for c in _covered_changes
        )
        _vb_rollup_parts = []
        if _vb_total_ts:
            _vb_rollup_parts.append(f"Time savings: {fmt_aud(_vb_total_ts)}")
        if _vb_total_pe:
            _vb_rollup_parts.append(f"Revenue / productivity: {fmt_aud(_vb_total_pe)}")
        if _vb_total_rr:
            _vb_rollup_parts.append(f"Risk reduction: {fmt_aud(_vb_total_rr)}")
        if _vb_total_cx:
            _vb_rollup_parts.append(f"Customer experience: {fmt_aud(_vb_total_cx)}")
        _vb_rollup_str = " + ".join(_vb_rollup_parts) if _vb_rollup_parts else ""
        _vb_rollup = (
            f'<div style="display:flex;justify-content:space-between;padding:8px 0 0 0;font-weight:700;font-size:13px;'
            f'border-top:2px solid #e2e8f0">'
            f'<span style="color:#0f1825">{"= " + _vb_rollup_str if _vb_rollup_str else "Plugin total"}</span>'
            f'<span style="color:#166534">{fmt_aud(b_val)}/yr</span></div>'
        )
        value_breakdown_html = (
            f'<details style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
            f'padding:4px 14px;margin-top:16px;cursor:pointer" open>'
            f'<summary style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;'
            f'color:#64748b;padding:8px 0;list-style:none;display:flex;align-items:center;gap:6px">'
            f'<span style="font-size:12px">&#9660;</span> '
            f'How we calculated {fmt_aud(b_val)}/yr</summary>'
            f'<div style="padding-bottom:10px">'
            f'{_vb_rows}'
            f'{_vb_rollup}'
            f'</div>'
            f'</details>'
        ) if _vb_rows else ""

        modal_html = f"""<div id="{modal_id}" class="bp-modal-backdrop" style="display:none" onclick="if(event.target===this)this.style.display='none'">
  <div class="bp-modal">
    <button class="bp-modal-close" onclick="document.getElementById('{modal_id}').style.display='none'">&times;</button>
    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:{sc['border']};margin-bottom:8px">Cowork Plugin</div>
    <h3 style="font-size:18px;font-weight:800;color:#0f1825;margin:0 0 12px;line-height:1.3">{b_title}</h3>
    {('<p style="font-size:13px;color:#64748b;line-height:1.6;margin:0 0 20px">' + escape(b_desc) + '</p>') if b_desc else ''}
    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;margin-bottom:12px">Skills in this plugin</div>
    {skill_blocks}
    {('<div style="margin-top:16px"><div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#94a3b8;margin-bottom:6px">Connectors</div><div style="display:flex;flex-wrap:wrap;gap:4px">' + connector_pills + '</div></div>') if connectors else ''}
    {value_breakdown_html}
    <div style="display:flex;gap:24px;margin-top:20px;padding-top:16px;border-top:1px solid #E5E7EB;flex-wrap:wrap;align-items:center">
      {('<div><span style="font-size:20px;font-weight:800;color:#0f1825;display:block">' + fmt_aud(b_val) + '/yr</span><span style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:#64748b">Combined annual value</span></div>') if b_val else ''}
      {('<div><span style="font-size:20px;font-weight:800;color:#0f1825;display:block">' + fmt_aud(b_lo) + '-' + fmt_aud(b_hi) + '</span><span style="font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:#64748b">Build cost</span>' + ('<span style="font-size:11px;font-weight:700;color:#166534;display:block;margin-top:3px">&asymp; ' + rnd_effective_range(b_lo, b_hi) + ' after R&amp;D offset</span>' if rnd_effective_range(b_lo, b_hi) else '') + '</div>') if b_lo else ''}
    </div>
  </div>
</div>"""

        # Skill name chips for the card face
        skill_chips = "".join(
            f'<span style="background:#fff7ed;border:1px solid #fed7aa;border-radius:5px;'
            f'padding:2px 8px;font-size:10px;font-weight:600;color:#c2410c">{escape(sk.get("skill_title",""))}</span>'
            for sk in skills
        )

        tier_badge = (
            f'<span style="background:#fff7ed;color:#c2410c;font-size:9px;font-weight:700;'
            f'padding:3px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:0.05em">{escape(b_tier)}</span>'
        ) if b_tier else ""

        return f"""{modal_html}
<div onclick="document.getElementById('{modal_id}').style.display='flex'"
     style="background:#fff;border:2px solid {sc['border']};border-radius:14px;padding:24px;cursor:pointer;transition:box-shadow 0.2s,transform 0.15s;position:relative;overflow:hidden"
     onmouseover="this.style.boxShadow='0 8px 32px rgba(0,0,0,0.12)';this.style.transform='translateY(-2px)'"
     onmouseout="this.style.boxShadow='none';this.style.transform='none'">
  <div style="position:absolute;top:0;right:0;background:{sc['tag_bg']};color:#fff;font-size:9px;font-weight:700;padding:4px 10px;border-radius:0 12px 0 8px;text-transform:uppercase;letter-spacing:0.05em">Staff-facing</div>
  <div style="font-size:13px;font-weight:800;color:{sc['text']};margin-bottom:8px;margin-top:4px">Cowork Plugin</div>
  <div style="font-size:15px;font-weight:700;color:#0f1825;margin-bottom:10px;line-height:1.35;padding-right:12px">{b_title}</div>
  <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px">{skill_chips}</div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;align-items:center">
    {'<span style="background:#166534;border:1px solid #14532d;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:700;color:#ffffff">' + fmt_aud(b_val) + '/yr</span>' if b_val else ''}
    {'<span style="background:#f8fafc;border:1px solid #E5E7EB;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600;color:#64748b">' + str(n_skills) + ' skill' + ('s' if n_skills != 1 else '') + '</span>'}
    {tier_badge}
  </div>
  <div style="margin-top:12px;font-size:11px;font-weight:600;color:#64748b">View details &rarr;</div>
</div>"""

    # ── INITIATIVE CARDS (interleaved: bundle card at first covered change position) ──
    emitted_bundles: set = set()
    card_parts = []
    for i, c in enumerate(changes):
        if c.get("solution_type") == "process_change":
            continue  # process changes are summarised in strategy text, not rendered as cards
        cid = c.get("change_id", "")
        bid = c.get("plugin_bundle_id")
        if bid and cid in bundled_cids:
            if bid not in emitted_bundles:
                bundle = bundle_by_id.get(bid)
                if bundle:
                    card_parts.append(_bundle_card(bundle))
                emitted_bundles.add(bid)
        else:
            card_parts.append(_card(c, i + 1))
    cards_html = "\n".join(card_parts) if card_parts else "<p style='color:#64748b'>Initiatives will appear here once research is complete.</p>"

    # ── PRIORITY MATRIX ────────────────────────────────────────────────────────
    # Build matrix items: one per bundle (aggregated) + one per unbundled change
    _matrix_items = []
    _seen_bundle_ids: set = set()
    for c in changes:
        if c.get("solution_type") == "process_change":
            continue
        _cid = c.get("change_id", "")
        _bid = c.get("plugin_bundle_id")
        if _bid and _cid in bundled_cids:
            if _bid not in _seen_bundle_ids:
                _b = bundle_by_id.get(_bid, {})
                _b_cids = _b.get("covered_change_ids") or []
                _b_changes = [change_by_id[x] for x in _b_cids if x in change_by_id]
                _b_val = _b.get("combined_annual_value_aud", 0) or 0
                _b_effort = sum(weeks_to_effort(x.get("implementation", {}).get("weeks_label", "")) for x in _b_changes)
                _tags = [roi_by_id.get(x.get("linked_roi_item_id", ""), {}).get("payback_tag", "") for x in _b_changes]
                _dominant_tag = max(set(_tags), key=_tags.count) if _tags else ""
                _matrix_items.append({
                    "modal_id": f"modal-{_bid}",
                    "title": _b.get("plugin_title", ""),
                    "val": _b_val,
                    "effort": _b_effort,
                    "payback_tag": _dominant_tag,
                    "weeks_label": f"~{_b_effort:.0f} wks",
                    "is_bundle": True,
                })
                _seen_bundle_ids.add(_bid)
        else:
            _roi_item = roi_by_id.get(c.get("linked_roi_item_id", ""), {})
            _matrix_items.append({
                "modal_id": f"modal-{_cid}",
                "title": c.get("title", ""),
                "val": c.get("value", {}).get("combined_annual_value_aud", 0) or 0,
                "effort": weeks_to_effort(c.get("implementation", {}).get("weeks_label", "")),
                "payback_tag": _roi_item.get("payback_tag", ""),
                "weeks_label": c.get("implementation", {}).get("weeks_label", ""),
                "is_bundle": False,
            })

    if _matrix_items:
        max_val = max(item["val"] for item in _matrix_items) or 1
        max_effort = max(item["effort"] for item in _matrix_items) or 1

        bubbles_html = ""
        legend_html = ""
        for item in _matrix_items:
            mid = item["modal_id"]
            title = escape(item["title"])
            val = item["val"]
            effort = item["effort"]
            payback_tag = item["payback_tag"]
            bubble_color = PAYBACK_COLORS.get(payback_tag, "#64748b")
            if item["is_bundle"]:
                bubble_color = SOL_COLORS["cowork_plugin"]["border"]
            x_pct = effort / max_effort * 85 + 5
            y_pct = 100 - (val / max_val * 85 + 5)
            size = max(18, min(36, int(val / max_val * 28) + 10))
            bubbles_html += f'''<div class="qm-bubble" data-id="{mid}" title="{title}"
  style="width:{size}px;height:{size}px;left:{x_pct:.1f}%;bottom:{100 - y_pct:.1f}%;background:{bubble_color};border-color:{bubble_color};opacity:0.85"
  onclick="document.getElementById(\'{mid}\').style.display=\'flex\'"
  onmouseover="this.querySelector(\'.qm-tip\').style.display=\'block\'"
  onmouseout="this.querySelector(\'.qm-tip\').style.display=\'none\'">
  <div class="qm-tip" style="font-size:11px;min-width:140px">
    <strong>{title[:40]}</strong><br/>{fmt_aud(val)}/yr &middot; {escape(item['weeks_label'])}
  </div>
</div>'''
            legend_html += f'''<button class="qm-legend-btn" onclick="document.getElementById(\'{mid}\').style.display=\'flex\'">
  <span style="width:10px;height:10px;border-radius:50%;background:{bubble_color};display:inline-block;flex-shrink:0"></span>
  <span style="font-size:11px">{title[:35]}</span>
</button>'''

        matrix_html = f"""<div class="qm-container">
  <div class="qm-axis-x"></div><div class="qm-axis-y"></div>
  <div class="qm-mid-x"></div><div class="qm-mid-y"></div>
  <span class="qm-label qm-label-tl">Low impact</span>
  <span class="qm-label qm-label-tr">High impact, low effort</span>
  <span class="qm-label qm-label-br">High effort, high impact</span>
  <span class="qm-label qm-label-bl">Low priority</span>
  <span class="qm-axis-label-x">Implementation effort (weeks) &rarr;</span>
  <span class="qm-axis-label-y">Annual value &uarr;</span>
  {bubbles_html}
</div>
<div class="qm-legend">{legend_html}</div>"""
    else:
        matrix_html = "<p style='color:#64748b;font-style:italic'>Priority matrix will appear once all initiatives have been researched and rated.</p>"

    # ── OUTLOOK & RISKS ────────────────────────────────────────────────────────
    # Read transformation_blueprint solely for the outlook narrative + risks block.
    # The phased-rollout Gantt previously rendered from tb.phases[] has been
    # removed from blueprint.html (the PDF report still consumes phases[] via
    # extract_report_content.py).
    tb = ssad.get("transformation_blueprint") or {}
    tb_phases = tb.get("phases") or []
    # New section authored by Researcher BO. Plain-English short-term and long-term
    # outlook plus a risks narrative. Degrades gracefully when fields are missing.
    short_term = tb.get("short_term_outlook") or {}
    long_term = tb.get("long_term_outlook") or {}
    risk_outlook = tb.get("risk_outlook") or {}

    _RISK_CATEGORY_LABELS = {
        "data_flow_context": "Data flow & context",
        "data_storage_ownership": "Data storage & ownership",
        "ai_training_adoption": "AI training & adoption",
    }
    _RISK_CATEGORY_COLORS = {
        "data_flow_context": "#3B82F6",
        "data_storage_ownership": "#f97316",
        "ai_training_adoption": "#7C3AED",
    }

    def _render_outlook_article(title: str, accent: str, badge_text: str, payload: dict) -> str:
        summary = escape(payload.get("summary", "") or "")
        if not summary:
            return ""
        highlights = payload.get("highlights") or []
        bullets = "".join(
            f'<li style="font-size:13px;color:#0f1825;line-height:1.55;margin:0 0 8px;padding-left:18px;position:relative">'
            f'<span style="position:absolute;left:0;top:8px;width:6px;height:6px;border-radius:50%;background:{accent}"></span>'
            f'{escape(str(h))}</li>'
            for h in highlights if h
        )
        return f'''<article style="background:#fff;border:1px solid #E5E7EB;border-radius:14px;padding:24px;display:flex;flex-direction:column;gap:14px">
  <div style="display:inline-flex;align-items:center;gap:8px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:0.08em;color:{accent}">
    <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{accent}"></span>{escape(badge_text)}
  </div>
  <h3 style="font-size:18px;font-weight:800;color:#0f1825;margin:0">{escape(title)}</h3>
  <p style="font-size:14px;color:#374151;line-height:1.6;margin:0">{summary}</p>
  {('<ul style="list-style:none;padding:0;margin:0">' + bullets + '</ul>') if bullets else ''}
</article>'''

    short_article = _render_outlook_article("Short term (0-3 months)", "#22c55e", "What you'll feel first", short_term)
    long_article = _render_outlook_article("Long term (6-18 months)", "#1d4ed8", "Where this takes you", long_term)

    outlook_articles_html = ""
    if short_article or long_article:
        # Grid renders 2-col when both present, single column otherwise
        outlook_articles_html = f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:32px">{short_article}{long_article}</div>'

    # Risks block
    risk_items_html = ""
    risk_summary = escape(risk_outlook.get("summary", "") or "")
    risks = risk_outlook.get("risks") or []
    if risks:
        cards = ""
        for r in risks:
            cat = r.get("category", "")
            cat_label = _RISK_CATEGORY_LABELS.get(cat, "Risk")
            cat_color = _RISK_CATEGORY_COLORS.get(cat, "#64748b")
            title_text = escape(r.get("title", "") or "")
            description = escape(r.get("description", "") or "")
            mitigation = escape(r.get("mitigation", "") or "")
            cards += f'''<div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid {cat_color};border-radius:10px;padding:18px 20px;display:flex;flex-direction:column;gap:10px">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap">
    <div style="font-size:14px;font-weight:800;color:#0f1825">{title_text}</div>
    <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:{cat_color};background:{cat_color}1a;padding:3px 8px;border-radius:6px">{escape(cat_label)}</span>
  </div>
  <p style="font-size:13px;color:#374151;line-height:1.6;margin:0">{description}</p>
  {('<div style="font-size:12px;color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:8px 12px;line-height:1.5"><strong style="color:#166534">Mitigation: </strong>' + mitigation + '</div>') if mitigation else ''}
</div>'''
        risk_items_html = f'<div style="display:grid;grid-template-columns:1fr;gap:14px">{cards}</div>'
    elif tb_phases is None or not tb_phases:
        # Fallback: surface top 5 risk_labels from proposed_changes when BO has not yet run
        labels = [escape(c.get("risk_label", "") or "") for c in changes if c.get("risk_label")][:5]
        if labels:
            label_html = "".join(
                f'<li style="font-size:13px;color:#374151;line-height:1.55;margin:0 0 6px;padding-left:18px;position:relative">'
                f'<span style="position:absolute;left:0;top:8px;width:6px;height:6px;border-radius:50%;background:#f97316"></span>{lbl}</li>'
                for lbl in labels
            )
            risk_items_html = f'<ul style="list-style:none;padding:0;margin:0">{label_html}</ul>'

    risks_block_html = ""
    if risk_summary or risk_items_html:
        risks_block_html = f'''<div style="background:#fff;border:1px solid #E5E7EB;border-radius:14px;padding:24px;display:flex;flex-direction:column;gap:16px">
  <div style="display:flex;align-items:center;gap:10px">
    <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.08em;color:#c2410c">What we are protecting against</div>
  </div>
  <h3 style="font-size:18px;font-weight:800;color:#0f1825;margin:0">Risks the plan mitigates.</h3>
  {('<p style="font-size:14px;color:#374151;line-height:1.6;margin:0">' + risk_summary + '</p>') if risk_summary else ''}
  {risk_items_html}
</div>'''

    outlook_section_html = ""
    if outlook_articles_html or risks_block_html:
        outlook_section_html = f'''<section id="outlook" style="padding:80px 0;background:#f8fafc;border-bottom:1px solid #E5E7EB">
  <div style="max-width:900px;margin:0 auto;padding:0 24px">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#166534;margin-bottom:12px">WHERE THIS TAKES YOU</div>
    <h2 style="font-size:clamp(24px,4vw,36px);font-weight:800;color:#0f1825;margin:0 0 8px">A clear short and long term view.</h2>
    <p style="font-size:15px;color:#64748b;margin:0 0 32px">Quick wins you will feel inside a quarter, plus the foundations that keep you flexible as AI keeps moving.</p>
    {outlook_articles_html}
    {risks_block_html}
  </div>
</section>'''

    # ── TECHNICAL APPENDIX ─────────────────────────────────────────────────────
    tech_appendix_html = _render_tech_appendix_html(changes)

    # ── TOOL STACK ─────────────────────────────────────────────────────────────
    def _tool_chip(t):
        if not isinstance(t, dict):
            return f'<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:8px 12px;font-size:11px;font-weight:600;color:#0f1825;text-align:center;min-width:70px">{escape(str(t))}</div>'
        name = escape(t.get("tool_name", ""))
        api = t.get("api_available")
        mcp = t.get("mcp_available")
        openness = t.get("integration_openness") or "unknown"
        notes = escape(t.get("integration_notes", "") or "")
        border_color = {"open": "#22c55e", "partial": "#3b82f6", "closed": "#ef4444"}.get(openness, "#E5E7EB")
        dots = ""
        if api is True:
            dots += '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#22c55e;flex-shrink:0" title="Public API available"></span>'
        if mcp is True:
            dots += '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#3b82f6;flex-shrink:0" title="MCP server available"></span>'
        if api is False and mcp is not True:
            dots += '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#ef4444;flex-shrink:0" title="No public API"></span>'
        title_attr = f' title="{notes}"' if notes else ""
        inner = f'<div style="display:flex;align-items:center;justify-content:center;gap:4px">{dots}<span>{name}</span></div>'
        return f'<div style="background:#fff;border:2px solid {border_color};border-radius:8px;padding:8px 12px;font-size:11px;font-weight:600;color:#0f1825;text-align:center;min-width:70px;cursor:default"{title_attr}>{inner}</div>'

    tool_chips = "".join(_tool_chip(t) for t in (tools or [])[:16]) or '<div style="color:#64748b;font-size:13px">Tool stack not yet recorded.</div>'

    has_tool_status = any(
        isinstance(t, dict) and t.get("integration_openness") not in (None, "unknown")
        for t in (tools or [])
    )
    tool_legend = """<div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:10px;font-size:10px;color:#64748b">
  <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#22c55e"></span>Public API</span>
  <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#3b82f6"></span>MCP Server</span>
  <span style="display:flex;align-items:center;gap:4px"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#ef4444"></span>No Public API</span>
</div>""" if has_tool_status else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company}: AI Implementation Blueprint</title>
<link rel="icon" type="image/png" href="{APG_LOGO_URL}">
{_PORTAL_FONTS}
<style>
:root {{ --lime-text: #064E3B; --border: #e2e8f0; }}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; color: #0f1825; font-size: 15px; line-height: 1.6; -webkit-font-smoothing: antialiased; }}
a {{ color: inherit; text-decoration: none; }}
.site-nav {{ position: sticky; top: 0; z-index: 100; background: rgba(247,249,252,0.92); backdrop-filter: blur(12px); border-bottom: 1px solid #E5E7EB; padding: 0 24px; }}
.nav-inner {{ max-width: 960px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; height: 60px; }}
.nav-logo {{ height: 32px; display: block; }}
.nav-client {{ font-size: 12px; color: #64748b; font-weight: 500; }}
.qm-container {{ position:relative; aspect-ratio:16/10; background:#fff; border:1px solid #E5E7EB; border-radius:12px; padding:48px; overflow:visible; margin-top:32px; }}
.qm-axis-x {{ position:absolute; left:48px; right:48px; bottom:48px; height:2px; background:#0f1825; opacity:0.5; }}
.qm-axis-y {{ position:absolute; left:48px; top:48px; bottom:48px; width:2px; background:#0f1825; opacity:0.5; }}
.qm-mid-x {{ position:absolute; left:48px; right:48px; top:50%; height:1px; background:#0f1825; opacity:0.2; }}
.qm-mid-y {{ position:absolute; top:48px; bottom:48px; left:50%; width:1px; background:#0f1825; opacity:0.2; }}
.qm-label {{ position:absolute; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; opacity:0.4; }}
.qm-label-tl {{ top:56px; left:56px; }} .qm-label-tr {{ top:56px; right:56px; opacity:1 !important; }} .qm-label-br {{ bottom:56px; right:56px; opacity:1 !important; }} .qm-label-bl {{ bottom:56px; left:56px; }}
.qm-axis-label-x {{ position:absolute; bottom:8px; left:50%; transform:translateX(-50%); font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; }}
.qm-axis-label-y {{ position:absolute; left:4px; top:50%; transform:translateY(-50%) rotate(-90deg); font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; white-space:nowrap; }}
.qm-bubble {{ position:absolute; border-radius:50%; border:2px solid; transform:translate(-50%,50%); cursor:pointer; transition:all 0.3s ease; }}
.qm-tip {{ display:none; position:absolute; bottom:calc(100% + 8px); left:50%; transform:translateX(-50%); background:#fff; border:1px solid #E5E7EB; border-radius:8px; padding:10px 14px; box-shadow:0 4px 16px rgba(0,0,0,0.12); z-index:20; white-space:nowrap; pointer-events:none; }}
.qm-legend {{ margin-top:20px; display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }}
.qm-legend-btn {{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:8px; border:1px solid #E5E7EB; background:transparent; cursor:pointer; transition:all 0.2s; font-family:inherit; color:#0f1825; }}
.qm-legend-btn:hover {{ border-color:#22c55e; background:rgba(125,255,0,0.08); }}
.bp-modal-backdrop {{ position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.6); z-index:2000; display:flex; align-items:center; justify-content:center; padding:24px; }}
.bp-modal {{ background:#fff; border-radius:14px; max-width:580px; width:100%; max-height:88vh; overflow-y:auto; padding:28px 32px; position:relative; box-shadow:0 20px 60px rgba(0,0,0,0.3); }}
.bp-modal-close {{ position:absolute; top:12px; right:16px; background:none; border:none; font-size:24px; color:#64748b; cursor:pointer; padding:4px 8px; line-height:1; }}
.bp-modal-section {{ margin-bottom:14px; }}
.bp-modal-section h4 {{ font-size:12px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px; }}
.bp-modal-section p {{ font-size:14px; line-height:1.55; color:#0f1825; }}
.bp-rec-link {{ display:inline-flex; align-items:center; gap:6px; background:#7DFF00; color:#166534; font-weight:700; font-size:12px; padding:7px 14px; border-radius:6px; text-decoration:none; transition:opacity .15s; }}
.bp-rec-link:hover {{ opacity:.85; }}
.bp-doc-link {{ display:inline-flex; align-items:center; gap:6px; background:#e0e7ff; color:#3730a3; font-weight:700; font-size:12px; padding:7px 14px; border-radius:6px; text-decoration:none; transition:opacity .15s; }}
.bp-doc-link:hover {{ opacity:.85; }}
@media (max-width:768px) {{
  .qm-container {{ padding:24px; }} .qm-label {{ font-size:8px; }}
  .qm-axis-x {{ left:24px; right:24px; bottom:24px; }} .qm-axis-y {{ left:24px; top:24px; bottom:24px; }}
}}
{_PORTAL_TOPBAR_CSS}
{_PORTAL_FOOTER_CSS}
{_PORTAL_TYPOGRAPHY_CSS}
</style>
</head>
<body>

{_portal_topbar_html("AI blueprint", company, _portal_status_pill(sections), is_demo=sections.get("is_demo", False))}

<section style="padding:80px 0;background:#0f1825;border-bottom:1px solid #1e293b">
  <div style="max-width:900px;margin:0 auto;padding:0 24px">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#22c55e;margin-bottom:16px">THIS IS WHAT WE'RE SOLVING</div>
    <div style="font-size:clamp(48px,8vw,80px);font-weight:900;color:#22c55e;font-variant-numeric:tabular-nums;line-height:1;margin-bottom:8px">{fmt_aud(total_annual_value)}</div>
    <div style="font-size:20px;color:#9ca3af;margin-bottom:32px">identified annual opportunity value</div>
    <div style="display:flex;gap:32px;flex-wrap:wrap;margin-bottom:32px">
      <div><div style="font-size:28px;font-weight:800;color:#fff">{n_changes}</div><div style="font-size:13px;color:#9ca3af">opportunities identified</div></div>
      {'<div><div style="font-size:28px;font-weight:800;color:#fff">' + str(int(weekly_hours)) + ' hrs/wk</div><div style="font-size:13px;color:#9ca3af">recoverable time</div></div>' if weekly_hours else ''}
    </div>
    <a href="4-waste.html" style="display:inline-flex;align-items:center;gap:8px;color:#22c55e;font-size:14px;font-weight:600;text-decoration:underline;text-underline-offset:3px">See the full opportunity breakdown &rarr;</a>
  </div>
</section>

<section style="padding:80px 0;background:#fff;border-bottom:1px solid #E5E7EB">
  <div style="max-width:900px;margin:0 auto;padding:0 24px">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#166534;margin-bottom:12px">HOW YOUR BUSINESS SYSTEMS WORK</div>
    <h2 style="font-size:clamp(24px,4vw,36px);font-weight:800;color:#0f1825;margin:0 0 12px">Every business runs on three layers.</h2>
    <p style="font-size:15px;color:#64748b;margin:0 0 40px;line-height:1.6">Understanding these layers is the key to understanding where AI fits, and where it can&rsquo;t help yet.</p>
    <div style="border:1px solid #E5E7EB;border-radius:16px;overflow:hidden;margin-bottom:48px">
      <div style="background:linear-gradient(135deg,#0f1825 0%,#1e293b 100%);padding:28px 32px;display:flex;align-items:center;gap:20px">
        <div style="min-width:56px;height:56px;background:#22c55e;border-radius:12px;display:flex;align-items:center;justify-content:center"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0f1825" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 1 4 4c0 1.95-1.4 3.58-3.25 3.93"/><path d="M12 2a4 4 0 0 0-4 4c0 1.95 1.4 3.58 3.25 3.93"/><circle cx="12" cy="14" r="4"/><path d="M12 18v4"/><path d="M8 22h8"/></svg></div>
        <div style="flex:1"><div style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.1em;color:#22c55e;margin-bottom:4px">Layer 3: AI</div><div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:4px">The intelligence layer</div><div style="font-size:13px;color:#9ca3af;line-height:1.5">AI reads your data, understands context, and helps your team make better decisions faster. It can draft, analyse, recommend, and automate, but only if it can <em>reach</em> the data.</div></div>
      </div>
      <div style="background:#f8fafc;text-align:center;padding:4px 0"><svg width="24" height="20" viewBox="0 0 24 20"><path d="M12 0v16M6 10l6 6 6-6" stroke="#94a3b8" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg><div style="font-size:10px;color:#64748b;font-weight:600;letter-spacing:0.05em">MCP CONNECTORS</div></div>
      <div style="background:#f0f9ff;padding:28px 32px;display:flex;align-items:center;gap:20px;border-top:1px solid #E5E7EB;border-bottom:1px solid #E5E7EB">
        <div style="min-width:56px;height:56px;background:#3b82f6;border-radius:12px;display:flex;align-items:center;justify-content:center"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg></div>
        <div style="flex:1"><div style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.1em;color:#1d4ed8;margin-bottom:4px">Layer 2: Systems</div><div style="font-size:15px;font-weight:700;color:#0f1825;margin-bottom:4px">The tools your team uses every day</div><div style="font-size:13px;color:#64748b;line-height:1.5">These are the screens your staff look at, CRMs, spreadsheets, booking systems, accounting tools. They visualise and interact with the data underneath.</div></div>
      </div>
      <div style="background:#f8fafc;text-align:center;padding:4px 0"><svg width="24" height="20" viewBox="0 0 24 20"><path d="M12 0v16M6 10l6 6 6-6" stroke="#94a3b8" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg><div style="font-size:10px;color:#64748b;font-weight:600;letter-spacing:0.05em">APIS &amp; DATABASES</div></div>
      <div style="background:#fefce8;padding:28px 32px;display:flex;align-items:center;gap:20px">
        <div style="min-width:56px;height:56px;background:#eab308;border-radius:12px;display:flex;align-items:center;justify-content:center"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></div>
        <div style="flex:1"><div style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.1em;color:#a16207;margin-bottom:4px">Layer 1: Data</div><div style="font-size:15px;font-weight:700;color:#0f1825;margin-bottom:4px">The foundation everything sits on</div><div style="font-size:13px;color:#64748b;line-height:1.5">Customer records, job histories, invoices, schedules, communications. If the data is siloed, messy, or inaccessible, nothing above it works properly, including AI.</div></div>
      </div>
    </div>
    <div style="background:#f8fafc;border:1px solid #E5E7EB;border-radius:12px;padding:24px 28px;margin-bottom:48px">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;margin-bottom:12px">Your current tools (Layer 2)</div>
      <div style="display:flex;flex-wrap:wrap;gap:8px">{tool_chips}</div>
      {tool_legend}
      <div style="font-size:12px;color:#64748b;margin-top:12px;line-height:1.5">Each of these tools stores data separately. Green and blue indicators show which tools have open APIs or MCP connectors that AI can use to access and automate.</div>
    </div>
    <div style="margin-bottom:48px">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;margin-bottom:16px">How a Cowork Plugin connects everything</div>
      <div style="border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;padding:32px;background:#fff">
        <div style="display:flex;align-items:center;justify-content:center;gap:0;flex-wrap:wrap">
          <div style="text-align:center;flex:0 0 auto"><div style="display:flex;flex-direction:column;gap:6px;align-items:center"><div style="background:#f0f9ff;border:2px solid #3b82f6;border-radius:10px;padding:10px 16px;font-size:12px;font-weight:700;color:#1d4ed8">Your Tools</div><div style="font-size:10px;color:#64748b">CRM, email, files</div></div></div>
          <div style="padding:0 8px;color:#94a3b8;font-size:20px">&rarr;</div>
          <div style="text-align:center;flex:0 0 auto"><div style="background:#f8fafc;border:2px dashed #94a3b8;border-radius:10px;padding:10px 16px;font-size:12px;font-weight:700;color:#64748b">MCP Connector</div><div style="font-size:10px;color:#64748b;margin-top:4px">Secure bridge</div></div>
          <div style="padding:0 8px;color:#94a3b8;font-size:20px">&rarr;</div>
          <div style="text-align:center;flex:0 0 auto"><div style="background:#0f1825;border:2px solid #0f1825;border-radius:10px;padding:10px 16px;font-size:12px;font-weight:700;color:#22c55e">Claude AI</div><div style="font-size:10px;color:#64748b;margin-top:4px">Reads &amp; reasons</div></div>
          <div style="padding:0 8px;color:#94a3b8;font-size:20px">&rarr;</div>
          <div style="text-align:center;flex:0 0 auto"><div style="background:#fff7ed;border:2px solid #f97316;border-radius:10px;padding:10px 16px;font-size:12px;font-weight:700;color:#c2410c">Staff Workflow</div><div style="font-size:10px;color:#64748b;margin-top:4px">40-80% faster</div></div>
        </div>
      </div>
    </div>
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#166534;margin-bottom:12px">FOUR TYPES OF SOLUTION</div>
    <h2 style="font-size:clamp(20px,3vw,28px);font-weight:800;color:#0f1825;margin:0 0 8px">Every opportunity maps to one of these.</h2>
    <p style="font-size:14px;color:#64748b;margin:0 0 32px">Each solution type works on a different layer of your business.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px">
      <div style="background:#fff;border:2px solid #f97316;border-radius:12px;padding:24px;position:relative;overflow:hidden"><div style="position:absolute;top:0;right:0;background:#f97316;color:#fff;font-size:9px;font-weight:700;padding:4px 10px;border-radius:0 0 0 8px;text-transform:uppercase">Staff-facing</div><div style="width:36px;height:36px;background:#fff7ed;border-radius:8px;display:flex;align-items:center;justify-content:center;margin-bottom:12px"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div><div style="font-size:14px;font-weight:800;color:#c2410c;margin-bottom:8px">Cowork Plugin</div><div style="font-size:13px;color:#374151;line-height:1.6;margin-bottom:12px">Your team talks to AI in plain English. It reads their data, drafts their work, and learns their job. <strong>4-8 weeks</strong> to build.</div><div style="font-size:11px;color:#64748b;background:#fff7ed;border-radius:6px;padding:8px 10px;line-height:1.4">Works on: <strong>AI + System layers</strong><br/>Best for: tasks staff do repeatedly</div></div>
      <div style="background:#fff;border:2px solid #3B82F6;border-radius:12px;padding:24px;position:relative;overflow:hidden"><div style="position:absolute;top:0;right:0;background:#3B82F6;color:#fff;font-size:9px;font-weight:700;padding:4px 10px;border-radius:0 0 0 8px;text-transform:uppercase">Background</div><div style="width:36px;height:36px;background:#eff6ff;border-radius:8px;display:flex;align-items:center;justify-content:center;margin-bottom:12px"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div><div style="font-size:14px;font-weight:800;color:#1D4ED8;margin-bottom:8px">Automation</div><div style="font-size:13px;color:#374151;line-height:1.6;margin-bottom:12px">Runs in the background with no staff interaction. Triggered by events, a new lead, a form submission, an overdue invoice. <strong>2-6 weeks</strong>.</div><div style="font-size:11px;color:#64748b;background:#eff6ff;border-radius:6px;padding:8px 10px;line-height:1.4">Works on: <strong>System + Data layers</strong><br/>Best for: repeatable data flows</div></div>
      <div style="background:#0f1825;border:2px solid #0f1825;border-radius:12px;padding:24px;position:relative;overflow:hidden"><div style="position:absolute;top:0;right:0;background:#22c55e;color:#0f1825;font-size:9px;font-weight:700;padding:4px 10px;border-radius:0 0 0 8px;text-transform:uppercase">Full platform</div><div style="width:36px;height:36px;background:rgba(255,255,255,0.1);border-radius:8px;display:flex;align-items:center;justify-content:center;margin-bottom:12px"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg></div><div style="font-size:14px;font-weight:800;color:#22c55e;margin-bottom:8px">Custom Build</div><div style="font-size:13px;color:#d1d5db;line-height:1.6;margin-bottom:12px">A platform built from scratch for your exact workflow. All three layers, data, system, and AI, designed together. <strong>3-6 months</strong>.</div><div style="font-size:11px;color:#9ca3af;background:rgba(255,255,255,0.06);border-radius:6px;padding:8px 10px;line-height:1.4">Works on: <strong>All three layers</strong><br/>Best for: core business logic</div></div>
      <div style="background:#fff;border:2px solid #7C3AED;border-radius:12px;padding:24px;position:relative;overflow:hidden"><div style="position:absolute;top:0;right:0;background:#7C3AED;color:#fff;font-size:9px;font-weight:700;padding:4px 10px;border-radius:0 0 0 8px;text-transform:uppercase">Foundation</div><div style="width:36px;height:36px;background:#f5f3ff;border-radius:8px;display:flex;align-items:center;justify-content:center;margin-bottom:12px"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></div><div style="font-size:14px;font-weight:800;color:#6D28D9;margin-bottom:8px">Data Migration</div><div style="font-size:13px;color:#374151;line-height:1.6;margin-bottom:12px">Connect and clean your data so everything else works. Move from spreadsheets to a real database, unify duplicates, standardise formats.</div><div style="font-size:11px;color:#64748b;background:#f5f3ff;border-radius:6px;padding:8px 10px;line-height:1.4">Works on: <strong>Data layer</strong><br/>Best for: siloed or dirty data</div></div>
    </div>
  </div>
</section>

<section style="padding:80px 0;background:#f8fafc;border-bottom:1px solid #E5E7EB">
  <div style="max-width:900px;margin:0 auto;padding:0 24px">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#166634;margin-bottom:12px">YOUR OPPORTUNITIES</div>
    <h2 style="font-size:clamp(24px,4vw,36px);font-weight:800;color:#0f1825;margin:0 0 8px">{n_changes} initiative{'s' if n_changes != 1 else ''} identified.</h2>
    <p style="font-size:14px;color:#64748b;margin:0 0 16px">Click any card to see exactly what we&rsquo;d build, how the value is calculated, and which problems it solves.</p>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px;font-size:12px;color:#374151;margin-bottom:28px;display:flex;flex-wrap:wrap;gap:16px;align-items:center">
      <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;flex-basis:100%">Indicative investment ranges</span>
      <span><strong style="color:#0f1825">Cowork Plugins:</strong> $4K-$12K</span>
      <span style="color:#cbd5e1">|</span>
      <span><strong style="color:#0f1825">Automations:</strong> $1K-$5K</span>
      <span style="color:#cbd5e1">|</span>
      <span><strong style="color:#0f1825">Custom Builds:</strong> quoted separately</span>
      <span style="color:#94a3b8;font-size:11px;flex-basis:100%;margin-top:2px">Detailed pricing is in your Scope of Work, issued after this presentation.</span>
    </div>
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:16px 18px;margin-bottom:28px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span style="font-family:ui-monospace,'SF Mono',Menlo,monospace;font-size:10px;font-weight:700;letter-spacing:0.04em;color:#166534;background:#fff;border:1px solid #bbf7d0;border-radius:6px;padding:3px 7px;line-height:1">R&amp;D</span>
        <span style="font-size:13px;font-weight:800;color:#166534">These builds may cost ~43.5% less after the Australian R&amp;D Tax Incentive</span>
      </div>
      <p style="font-size:12.5px;color:#374151;line-height:1.65;margin:0 0 8px">
        The build work above, Cowork plugins, automations, and custom platforms where we write new
        integration or automation code, is generally <strong>eligible R&amp;D expenditure</strong>.
        Australian companies can claim a <strong>refundable tax offset of ~43.5%</strong> on that spend
        (up to 48.5% on the 30% company tax rate), returned as cash or a reduction in tax payable. So a
        <strong>$4K-$12K</strong> plugin is roughly <strong>$2,260-$6,780 effective</strong>
        once the offset is claimed.
      </p>
      <div style="font-size:11.5px;color:#64748b;line-height:1.6">
        <strong style="color:#374151">Typical criteria:</strong> Australian company &middot; aggregated
        turnover under $20M &middot; at least $20K of eligible R&amp;D spend in the year &middot; genuine
        custom technical work (off-the-shelf configuration doesn&rsquo;t qualify) &middot; activities
        registered with AusIndustry. The audit fee itself is consulting, not R&amp;D. This isn&rsquo;t tax
        advice, confirm eligibility with your accountant or a registered R&amp;D specialist.
      </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px">
      {cards_html}
    </div>
  </div>
</section>

<section style="padding:80px 0;background:#fff;border-bottom:1px solid #E5E7EB">
  <div style="max-width:900px;margin:0 auto;padding:0 24px">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#166534;margin-bottom:12px">WHERE TO START</div>
    <h2 style="font-size:clamp(24px,4vw,36px);font-weight:800;color:#0f1825;margin:0 0 8px">Effort vs Impact</h2>
    <p style="font-size:15px;color:#64748b;margin:0 0 32px">Where your time and money will go furthest. Click any bubble to open that initiative.</p>
    {matrix_html}
  </div>
</section>

<section style="padding:80px 0;background:#f8fafc;border-bottom:1px solid #E5E7EB">
  <div style="max-width:900px;margin:0 auto;padding:0 24px">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#166534;margin-bottom:12px">SEE IT IN PRACTICE</div>
    <h2 style="font-size:clamp(24px,4vw,36px);font-weight:800;color:#0f1825;margin:0 0 8px">What these solutions look like in action.</h2>
    <p style="font-size:15px;color:#64748b;margin:0 0 32px">Explore each solution type below, watch a walkthrough or open a live demo.</p>
    <div style="background:#fff;border:2px solid #f97316;border-radius:14px;padding:24px;margin-bottom:20px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px"><div style="width:32px;height:32px;background:#fff7ed;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div><div style="font-size:14px;font-weight:800;color:#c2410c">Cowork Plugin</div></div>
      <p style="font-size:13px;color:#6b7280;line-height:1.55;margin:0 0 18px">Your team talks to AI about their daily work, reading live data, drafting documents, answering questions in plain English.</p>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
        <div><a href="https://youtu.be/WZ7HmdeyC00" target="_blank" rel="noopener" style="display:block;position:relative;padding-bottom:56.25%;border-radius:8px;overflow:hidden" onmouseover="this.querySelector('.play-btn').style.background='rgba(249,115,22,0.9)'" onmouseout="this.querySelector('.play-btn').style.background='rgba(0,0,0,0.65)'"><img src="https://img.youtube.com/vi/WZ7HmdeyC00/hqdefault.jpg" alt="5 Cowork use cases" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover"><div class="play-btn" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.65);transition:background 0.2s"><svg width="36" height="36" viewBox="0 0 36 36"><circle cx="18" cy="18" r="18" fill="rgba(0,0,0,0.4)"/><polygon points="14,11 28,18 14,25" fill="white"/></svg></div></a><div style="margin-top:8px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#f97316;margin-bottom:2px">Quick Start &middot; 20 min</div><div style="font-size:12px;font-weight:600;color:#0f1825">5 use cases you can install in an hour</div></div></div>
        <div><a href="https://youtu.be/7Rd9yGPrGsM" target="_blank" rel="noopener" style="display:block;position:relative;padding-bottom:56.25%;border-radius:8px;overflow:hidden" onmouseover="this.querySelector('.play-btn').style.background='rgba(249,115,22,0.9)'" onmouseout="this.querySelector('.play-btn').style.background='rgba(0,0,0,0.65)'"><img src="https://img.youtube.com/vi/7Rd9yGPrGsM/hqdefault.jpg" alt="Cowork deep dive" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover"><div class="play-btn" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.65);transition:background 0.2s"><svg width="36" height="36" viewBox="0 0 36 36"><circle cx="18" cy="18" r="18" fill="rgba(0,0,0,0.4)"/><polygon points="14,11 28,18 14,25" fill="white"/></svg></div></a><div style="margin-top:8px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#f97316;margin-bottom:2px">Deep Dive &middot; 45 min</div><div style="font-size:12px;font-weight:600;color:#0f1825">Full Cowork plugin walkthrough</div></div></div>
        <div><a href="https://youtu.be/VBBXNk9TbGc" target="_blank" rel="noopener" style="display:block;position:relative;padding-bottom:56.25%;border-radius:8px;overflow:hidden" onmouseover="this.querySelector('.play-btn').style.background='rgba(249,115,22,0.9)'" onmouseout="this.querySelector('.play-btn').style.background='rgba(0,0,0,0.65)'"><img src="https://img.youtube.com/vi/VBBXNk9TbGc/hqdefault.jpg" alt="Live demo" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover"><div class="play-btn" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.65);transition:background 0.2s"><svg width="36" height="36" viewBox="0 0 36 36"><circle cx="18" cy="18" r="18" fill="rgba(0,0,0,0.4)"/><polygon points="14,11 28,18 14,25" fill="white"/></svg></div></a><div style="margin-top:8px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#f97316;margin-bottom:2px">Live Demo</div><div style="font-size:12px;font-weight:600;color:#0f1825">Watch a real plugin in action</div></div></div>
      </div>
    </div>
  </div>
</section>

{outlook_section_html}

{tech_appendix_html}

{_portal_footer_html()}

</body>
</html>"""


# --- Client handoff zip layout -------------------------------------------------
# The handoff zip is built for a non-technical client: ONE obvious thing to click
# at the top level (the client website itself, renamed below), with every other
# page tucked into a single folder so the client never faces a wall of HTML files.
# The generators emit a flat deliverables/ tree with sibling links, so we rewrite
# the cross-page links for this relocated layout as we add each file to the zip.
HANDOFF_ENTRY_NAME = "OPEN ME.html"        # the client website, as the single entry point
HANDOFF_SUPPORT_DIR = "Supporting Files"   # holds section pages, BPMN assets, process diagrams


def _rewrite_handoff_links(html: str, self_zip_path: str, target_map: dict) -> str:
    """Rewrite intra-bundle deliverable links for the relocated handoff layout.

    In the zip the client website moves to the top level (HANDOFF_ENTRY_NAME) and
    every other page nests under HANDOFF_SUPPORT_DIR/. That breaks the relative
    links the generators emit (which assume a flat deliverables/ folder).

    `target_map` maps each deliverable's flat basename -> its new zip-relative path
    (relative to the bundle root). For each, we rewrite two link forms, at any
    nesting depth, to a path relative to THIS file's new location:
      - static anchors:                href="(../)*basename"
      - the client website downloads JSON:  "file": "(../)*basename"
    Links that don't move (e.g. siblings inside the support folder) are rewritten
    to the identical value, so this is safe to run over every page.

    assets/ and processes/ references are left untouched: they move together with
    the pages that reference them, so their relative relationship is preserved.
    """
    self_dir = posixpath.dirname(self_zip_path) or "."
    for basename, target_zip_path in target_map.items():
        rel = posixpath.relpath(target_zip_path, self_dir).replace(" ", "%20")
        esc = re.escape(basename)
        html = re.sub(r'href="(?:\.\./)*' + esc + r'"',
                      lambda m, r=rel: f'href="{r}"', html)
        html = re.sub(r'("file":\s*)"(?:\.\./)*' + esc + r'"',
                      lambda m, r=rel: f'{m.group(1)}"{r}"', html)
    return html


def build_curated_handoff_zip(ssad: dict, out_dir: Path, client_slug: str) -> Path:
    """Build a curated, client-friendly handoff zip in 03-audit/handoff/v{N}/.

    Built for a non-technical client: the unzipped folder contains exactly ONE file
    to click, the client website, renamed "OPEN ME.html", plus a single
    "Supporting Files" folder holding everything else (the other section pages, the
    BPMN viewer assets, and the interactive process diagrams). Each call creates a
    new versioned directory (v1, v2, ...), previous versions are never deleted.

    Zip structure:
      {Company Name} - APG Audit/
        OPEN ME.html                    (the client website, the single entry point)
        Supporting Files/
          2-process-map.html
          3-findings.html
          4-waste.html
          5-blueprint.html
          assets/                       (bpmn-viewer.min.js, bpmn-viewer.css)
          processes/                    (all BPMN stage subdirs)

    The website's links into the section pages, and every section/process page's
    links back to the website, are rewritten for this relocated layout.
    """
    import zipfile

    company = ssad.get("company_name", client_slug.replace("-", " ").title())
    safe_name = company.replace("/", "-").replace("\\", "-").strip()
    folder_name = f"{safe_name} - APG Audit"
    zip_name = f"{folder_name}.zip"

    handoff_dir = _get_client_subdir(client_slug, "03-audit/handoff")
    handoff_dir.mkdir(parents=True, exist_ok=True)

    # Auto-detect next version number
    existing_versions = [
        int(m.group(1))
        for d in handoff_dir.iterdir()
        if d.is_dir() and (m := re.match(r"^v(\d+)$", d.name))
    ] if handoff_dir.exists() else []
    next_version = max(existing_versions, default=0) + 1
    version_dir = handoff_dir / f"v{next_version}"
    version_dir.mkdir(parents=True, exist_ok=True)
    zip_path = version_dir / zip_name

    website_file = "1-client-website.html"
    section_files = ["2-process-map.html", "3-findings.html", "4-waste.html", "5-blueprint.html"]

    # Map each deliverable's flat basename to its NEW location inside the bundle
    # (relative to folder_name); used to rewrite cross-page links per file.
    target_map = {website_file: HANDOFF_ENTRY_NAME}
    for f in section_files:
        target_map[f] = f"{HANDOFF_SUPPORT_DIR}/{f}"

    included_files = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        def add_html(src: Path, zip_rel: str):
            """Read, rewrite links for the new layout, and write into the zip."""
            html = _rewrite_handoff_links(src.read_text(encoding="utf-8"), zip_rel, target_map)
            zf.writestr(f"{folder_name}/{zip_rel}", html.encode("utf-8"))

        # 1) The client website becomes the single top-level entry point.
        website_src = out_dir / website_file
        if website_src.exists():
            add_html(website_src, HANDOFF_ENTRY_NAME)
            included_files.append(website_file)
        else:
            print(f"WARNING: {website_file} not found, handoff has no "
                  f"'{HANDOFF_ENTRY_NAME}' entry point", file=sys.stderr)

        # 2) Section pages nest under the support folder.
        for filename in section_files:
            src = out_dir / filename
            if src.exists():
                add_html(src, f"{HANDOFF_SUPPORT_DIR}/{filename}")
                included_files.append(filename)

        # 3) BPMN viewer assets, copied verbatim (no links to rewrite).
        assets_dir = out_dir / "assets"
        if assets_dir.exists():
            for item in sorted(assets_dir.iterdir()):
                if item.is_file():
                    zf.write(item, f"{folder_name}/{HANDOFF_SUPPORT_DIR}/assets/{item.name}")

        # 4) Interactive process diagrams: rewrite links in .html pages (depth-aware),
        #    copy .bpmn source files verbatim.
        processes_dir = out_dir / "processes"
        if processes_dir.exists():
            for item in sorted(processes_dir.rglob("*")):
                if not item.is_file():
                    continue
                rel = item.relative_to(out_dir).as_posix()   # processes/{stage}/index.html
                zip_rel = f"{HANDOFF_SUPPORT_DIR}/{rel}"
                if item.suffix == ".html":
                    add_html(item, zip_rel)
                elif item.suffix == ".bpmn":
                    zf.write(item, f"{folder_name}/{zip_rel}")

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Handoff zip v{next_version}: {zip_path} ({size_mb:.1f} MB, {len(included_files)} reports)")
    return zip_path


def main():
    parser = argparse.ArgumentParser(description="APG HTML deliverable generator")
    parser.add_argument("--client-slug", required=True, help="Client slug (matches clients/ folder name)")
    parser.add_argument("--output", required=True,
                        choices=["process-map", "findings", "waste", "client-website", "blueprint", "handoff-zip", "all"],
                        help="Which output to generate")
    args = parser.parse_args()

    ssad = load_audit_data(args.client_slug)
    out_dir = ensure_deliverables_dir(args.client_slug)
    sections = load_client_sections(args.client_slug)
    generated = []

    if args.output == "handoff-zip":
        zip_path = build_curated_handoff_zip(ssad, out_dir, args.client_slug)
        generated.append(str(zip_path))
        result = {
            "status": "ok",
            "client_slug": args.client_slug,
            "generated": generated,
            "company_name": ssad.get("company_name", ""),
            "audit_status": ssad.get("audit_status", ""),
            "sessions_completed": ssad.get("sessions_completed", 0),
        }
        print(json.dumps(result, indent=2))
        return

    targets = (
        ["process-map", "findings", "waste", "blueprint", "client-website"]
        if args.output == "all" else [args.output]
    )

    def _bpmn_process_map(ssad_inner):
        from generate_bpmn import generate_bpmn_deliverables
        client_name = ssad_inner.get("company_name") or args.client_slug.replace("-", " ").title()
        return generate_bpmn_deliverables(ssad_inner, client_name, out_dir)

    generators = {
        "process-map":  (_bpmn_process_map, "2-process-map.html"),
        "client-website": (lambda s: generate_client_website(s, sections), "1-client-website.html"),
        "findings":     (lambda s: generate_findings_partial(s, sections), "3-findings.html"),
        "waste":        (lambda s: generate_waste_partial(s, sections), "4-waste.html"),
        "blueprint":    (lambda s: generate_blueprint(s, sections), "5-blueprint.html"),
    }

    for target in targets:
        # Feature-flagged routing: process-map → BPMN renderer when extraction
        # contains `lanes` + `sequence_flows` on any process. Falls back to the
        # legacy zone renderer otherwise.
        if target == "process-map" and _has_bpmn_processes(ssad):
            import sys as _sys
            _bpmn_path = str(Path(__file__).resolve().parent)
            if _bpmn_path not in _sys.path:
                _sys.path.insert(0, _bpmn_path)
            from bpmn_renderer import render_bpmn_processes
            client_meta = {
                "name": ssad.get("company_name", args.client_slug),
                "audit_version": ssad.get("audit_version", "1.0"),
            }
            written = render_bpmn_processes(ssad, client_meta, out_dir)
            for kind, paths in written.items():
                for p in paths:
                    generated.append(str(p))
                    print(f"Generated ({kind}): {p}")
            continue

        fn, filename = generators[target]
        html = fn(ssad)
        path = out_dir / filename
        path.write_text(html, encoding="utf-8")
        generated.append(str(path))
        print(f"Generated: {path}")

    # Build handoff zip for full runs
    if args.output == "all":
        curated_zip_path = build_curated_handoff_zip(ssad, out_dir, args.client_slug)
        generated.append(str(curated_zip_path))

    # Copy prototype to developer-portal handoff folder if it exists
    prototype_src = _get_client_dir(args.client_slug) / "prototype"
    if prototype_src.exists():
        developer_portal_prototype = _get_client_subdir(args.client_slug, "03-audit/handoff") / "developer-portal" / "prototype"
        developer_portal_prototype.parent.mkdir(parents=True, exist_ok=True)
        if developer_portal_prototype.exists():
            shutil.rmtree(developer_portal_prototype)
        shutil.copytree(prototype_src, developer_portal_prototype)
        print(f"Copied prototype to: {developer_portal_prototype}")
        generated.append(str(developer_portal_prototype))

    result = {
        "status": "ok",
        "client_slug": args.client_slug,
        "generated": generated,
        "company_name": ssad.get("company_name", ""),
        "audit_status": ssad.get("audit_status", ""),
        "sessions_completed": ssad.get("sessions_completed", 0),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
