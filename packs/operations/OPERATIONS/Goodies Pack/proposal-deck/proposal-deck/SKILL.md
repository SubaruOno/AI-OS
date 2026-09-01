---
name: proposal-deck
description: Create a premium, on-brand sales proposal deck as a single self-contained HTML file the user edits visually in their browser and exports to PDF in one click. No server, no installs beyond this skill, works the same on Mac, Windows and Linux. Triggers on "make a proposal", "proposal for [client]", "sales deck", "pitch deck", "quote for [client]", "create an offer", "proposal from this call". First run walks the user through a one-time brand setup (logo, colors, font) pulled from their website or entered by hand. Content can be generated from a recorded call (Fathom / Fireflies / Google Meet via Composio) or written by the user with the skill asking follow-up questions where the brief is thin.
---

# Proposal Deck — on-brand, browser-editable, one-click PDF

Generate a design-studio-quality sales proposal as **one self-contained `proposal.html` file**. The user opens it in any browser, edits every text inline, and clicks **Export PDF** to get the final file. Everything runs client-side: no server, no Python, no Playwright. It works identically on Mac, Windows (Lenovo etc.) and Linux.

There are two things this skill does: a **one-time brand setup**, and then **generating a deck** (as many times as they want).

---

## STEP 0 — Brand setup (first run only, then remembered)

Check whether `brand.json` exists in this skill folder.
- If it exists, load it and skip to STEP 1.
- If it does not, run this setup once and save `brand.json`.

Ask the user (single question, offer both paths):

> "Do you have a company website? Paste the URL and I'll pull your logo, colors and font from it. Or, if you prefer, just tell me your brand color and font and I'll set them by hand."

**Path A — from a website (preferred).**
Use the `firecrawl` skill to scrape the URL (the user already has it installed).
1. Scrape the site (request raw HTML, not just markdown, so you can read CSS).
2. Extract, and then **show the user for confirmation** (never assume):
   - **Accent color** — the dominant brand color (from CSS custom properties, prominent buttons/links, or the logo). Give a hex value.
   - **Background** — usually near-black `#050505` for this dark deck style, or the site's dark surface. Keep it dark; light decks are out of scope for v1.
   - **Font** — the site's heading `font-family` (from `<link>` to Google Fonts or `font-family` declarations).
   - **Logo** — download the best candidate (header logo, then `apple-touch-icon`, then `og:image`). Present it and ask "is this your logo?"
3. Be honest that color/font are reliable and the logo is a best-guess the user confirms.

**Path B — manual.**
Ask for: accent color (hex), font name (any Google Font, or a safe system font), and optionally a logo image path. Background stays dark by default.

Write `brand.json`:
```json
{
  "company_name": "Acme Studio",
  "accent": "#4ADE80",
  "background": "#050505",
  "card": "#0A0A0A",
  "ink": "#FFFFFF",
  "font": "Manrope",
  "font_mono": "JetBrains Mono",
  "logo_path": ""
}
```
If the user gave a logo, base64-encode it now and store it (see "Applying the logo" below) or keep the path and encode at generation time.

---

## STEP 1 — Ask what the deck is about

Ask this first, in one message:

> "Should I build this proposal from a recorded call, or will you give me the details?"

**If from a call:** the user has **Composio** with a meeting recorder connected. Use `ToolSearch` to find the connected meeting toolkit and pull the transcript:
- Fathom, Fireflies, and Google Meet are all supported through Composio and all expose transcript retrieval.
- Search for available tools (e.g. `ToolSearch` query `fireflies transcript`, `fathom meeting`, `google meet transcript`) and use whichever the user has connected. List recent meetings, let the user pick the right one, fetch the transcript.
- If no meeting toolkit is connected, fall back to "paste the transcript here".
From the transcript extract: who the proposal is for, the problem, the proposed solution, scope, timeline, and pricing.

**If the user gives the details:** collect what they have (recipient, what they sell, the problem, price, timeline). **Where the brief is thin, ask short follow-up questions** rather than inventing. Never fabricate numbers, case studies, or claims.

---

## STEP 2 — Generate the deck

1. **Pick a build location.** Default to a `proposals/<client-slug>/` folder next to where the user is working (or the Desktop). Create it.
2. **Copy the template:** `assets/template.html` → `<build>/proposal.html`. This is the whole engine — do not rebuild it.
3. **Apply the brand** (surgical edits to `proposal.html`, never regenerate the file):
   - In the `:root` block, set only these lines from `brand.json`:
     ```
     --brand-accent: <accent>;
     --brand-bg:     <background>;
     --brand-card:   <card>;
     --brand-ink:    <ink>;
     --brand-font:   '<font>', -apple-system, BlinkMacSystemFont, sans-serif;
     --brand-mono:   '<font_mono>', ui-monospace, monospace;
     ```
   - Update the Google Fonts `<link>` in `<head>` to load the chosen font(s). For true offline fidelity you may instead embed the font as base64 `@font-face`, but the CDN link is fine by default.
   - **Applying the logo (optional):** the brand mark is the `.dot` element (an accent circle by default). If the user has a square/icon logo, base64-encode it and, in the two `.dot` CSS rules, replace `background: var(--brand-accent); border-radius: 50%;` with `background: url('data:image/png;base64,<...>') center/contain no-repeat; border-radius: 0;`. If the logo is a wide wordmark, prefer leaving the accent circle and just using the company name text (it reads cleaner) — or widen the `.dot` rule to fit.
   - Replace the `.brand-name` text (appears on every slide) with the company name.
4. **Fill the content** with surgical `Edit`s to the 9 slides. The universal structure is:

   | # | Slide | What goes here |
   |---|-------|----------------|
   | 1 | Cover | Company name, one-line promise, recipient, date, validity |
   | 2 | Context | The client's situation in their words. Two columns. |
   | 3 | The problem | The core problem, sharpened. Strike-through + pain list. |
   | 4 | Approach | How the user works — 3 steps. |
   | 5 | Scope | Included vs excluded, so nothing is ambiguous. |
   | 6 | Deliverables | 6 concrete things the client receives. |
   | 7 | Timeline | 4 phases from kickoff to live. |
   | 8 | Investment | Up to 3 pricing options (middle = featured/recommended). |
   | 9 | Next steps | Close: 3 steps, contact details, validity. |

   Slides the deal doesn't need can be deleted (delete the whole `<section class="slide">…</section>`). Keep the tone concrete and specific: real names, real numbers, real consequences. Short sentences. No filler.
5. **Open it in the browser** (cross-platform):
   - macOS: `open <build>/proposal.html`
   - Windows: `start "" "<build>\proposal.html"`
   - Linux: `xdg-open <build>/proposal.html`

---

## STEP 3 — Hand off to the user

Tell the user this is a full visual editor (everything is in the browser, nothing to install):
- **Edit text:** click any text to change it. Font, size and colour are in the top toolbar. Changes autosave in this browser (per file — multiple proposals never clash).
- **Move / resize boxes:** hover a block → grab the round handle to drag it; **auto-alignment guides** snap it to other blocks. Drag a card's bottom-right corner to resize. `✕` deletes a block, `+` duplicates it.
- **Select many:** drag a lasso over empty space, or Shift+click blocks; the floating **+ / −** bar scales the whole selection. **Cmd+Z** undoes anything. **Cmd+C / Cmd+V** copies blocks.
- **Save HTML:** keeps a copy of the edited file to reopen later.
- **Export PDF:** one click, downloads `proposal.pdf` (no print dialog, no checkboxes).

---

## Rules

- **English output.** The deck and all copy are in English.
- **Never invent facts.** No fake case studies, metrics, client names, or guarantees. If you don't have it, ask or leave a clear placeholder.
- **Surgical edits only.** Once `proposal.html` exists, only `Edit` it. Never overwrite the whole file (it holds the editor engine and any manual edits).
- **Keep it self-contained.** Do not add external image/script references to `proposal.html`; inline anything new as base64. The file must work by double-click, offline.
- The template is fixed at 9 slides of 1920×1080. That's what makes the one-click PDF clean (one slide = one page).
