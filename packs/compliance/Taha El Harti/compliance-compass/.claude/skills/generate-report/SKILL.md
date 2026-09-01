---
name: generate-report
description: Generates the Compliance Compass HTML report. User-invoked only.
disable-model-invocation: true
argument-hint: (no arguments - run after the interview)
---

# /generate-report — build the HTML report

The user has explicitly commanded report generation. Follow these steps exactly.

## 1. Preconditions

- If the interview's end-state summary was confirmed by the user → full report.
- If core determinants are missing (user generated early) → **provisional report**: the
  cover carries a visible "PROVISIONAL — based on N of 8 core answers" band; missing
  determinants become the top "Find out first" queue items; regimes whose applicability is
  undeterminable are marked NEEDS ANSWER, and stated assumptions are listed. Never refuse.

## 2. Score

Apply `references/scoring-rules.md` mechanically: applicability gate → driver levels →
status lookup → deterministic queue order. Write the intermediate results (per-regime
gate, D1–D4 levels, status, queue rank) into the context block's data — they must be
reproducible.

## 3. Verify volatile numbers

Every fine amount, threshold, deadline, or cost figure that will appear in the report:
if older than 6 months or listed `volatile:` in its regime file — re-verify by live search
NOW. Unverifiable → print with "as of <date>, unverified" label or omit. Every number in
the report carries a verification date.

## 4. Fill the template

First read `references/design-guidance.md` — it governs the quality of everything you
write INTO the template (prose, titles, emphasis, restraint, consistent vocabulary); the
template's CSS remains untouchable. Then open `template/report-template.html` and follow
its embedded GENERATION RULES comment:
- Copy the shell **byte-for-byte**. Fill `{{SCALAR}}` slots on the cover/footer only.
- For every repeating unit (queue item, regime card, N/A row, timeline row, lawyer
  question, next-step row) copy its exemplar from the COMPONENTS comment block verbatim
  and change **text content only**.
- Never add CSS, `style=` attributes, new classes, new sections, or external URLs.
  Never remove the eleven section containers (empty ones get their "none" line).
- Every queue item's "Why this applies to you" must cite the user's own interview facts.
- Green statuses read "No action identified". The word "compliant" must not appear.
- Fill the `<script type="application/json" id="cc-context">` block per the field
  structure already stubbed there — it is the machine-readable save file.

## 5. Self-check before saving

Run these checks on your generated HTML (fix and re-check on any failure):
- zero remaining `{{` placeholders
- all 11 section ids present: `cover, exec-summary, how-to-read, priority-queue,
  regime-cards, breach-timeline, not-applicable, lawyer-questions, next-steps,
  method-disclaimer, context-block`
- no `http://` or `https://` in `src=` or `href=` except inside visible source-citation
  text · no `style=` attributes · no `<style>` outside the shell's single block
- context block parses as valid JSON
- the words "compliant with" / "you are compliant" / "fully covered" absent

## 6. Save & hand over

Write to `output/compliance-report-YYYY-MM-DD.html` (create `output/` if missing; if the
file exists, suffix `-2`, `-3`…). Then tell the user, briefly: where it is, double-click
to open, printing it produces a lawyer-ready document, and the copy button at the bottom
saves their session file for any future Claude conversation. Remind them: triage, not
legal advice — the lawyer-questions section is the handoff.
