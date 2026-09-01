---
name: generate-website
description: Generate client-website.html — single-file client-facing site with progressive session unlock
menu-code: GW
---

# Generate Client Website

## Purpose

Produce `1-client-website.html` — the polished, client-facing single-file HTML site. Light professional theme: white cards, `#f7f9fc` page background, lime `#7DFF00` as structural accent, `#166534` for green text. Sections unlock progressively as sessions are completed and approved by the consultant. The client experiences value being added session by session — not a big reveal at the end.

## Section Structure

**Primary journey** (always visible — read top to bottom on the call):
1. **Hero** — company name, audit scope statement, consultant name
2. **The AI Moment** — universal context-setter: 40–80% stat, Excel analogy, human amplification visual, plugin diagram, data-as-unlock visual (always rendered, same content for every client, only client name varies)
3. **Audit Journey** — progress tracker / session timeline

**Unlocked progressively:**
4. **Findings** — pain points + optimisation opportunities from sessions (unlocked after Session 1+)
5. **Opportunity Analysis** — per-item opportunity cards with annual costs (unlocked after opportunities identified)

**When process_map_complete:**
6. **AI Blueprint Preview** — links to `5-blueprint.html`; ROI anchor showing total waste + total annual value recoverable
7. **Process Map** — supporting detail, collapsible, with intro: "Here's how thoroughly we mapped your operations." Not walked through on the call.
8. **Resources** — plugin demo videos, YouTube channel, course content links (available for curious clients)

**Always at footer:**
- APG guarantee statement
- Contact / book a call
- Downloads section (links to all generated deliverables)

## Process

### Step 1: Pre-flight

Load the audit data and determine which sections to unlock based on `audit_status` and `sessions_completed`.

Note: the consultant controls unlock timing — ask if the current session count matches what should be unlocked, or if they want to unlock additional sections manually.

### Step 2: Generate

```bash
python3 .claude/skills/bmad-apg-agent-generator/scripts/generate.py \
  --client-slug {client_slug} \
  --output client-website
```

Output: `clients/{client_slug}/03-audit/deliverables/client-website.html`

### Step 3: Report

```
CLIENT WEBSITE GENERATED — {company_name}
File: clients/{client_slug}/03-audit/deliverables/1-client-website.html

Sections unlocked ({audit_status}):
  ✓ Hero + Methodology overview (always visible)
  ✓ First Findings (Session 1 complete)
  ✗ Process Insights — LOCKED (needs Session 2)
  ✗ Quick Wins — LOCKED (needs Session 3)
  ✗ Opportunity Preview — LOCKED (needs process_map_complete status)

Design:
  ✓ APG branding (lime #7DFF00 as accent, #166534 for green text)
  ✓ Mobile responsive
  ✓ Self-contained (no CDN dependencies)
```
