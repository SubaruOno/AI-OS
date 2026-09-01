# Cowork Demo HTML Template — Solution Architect Reference

Reference for `build-cowork-demo.md` Stage 3.7. Contains the APG brand shell, HTML component fragments, fragment-selection logic, and the Section 4b instruction block to embed in the demo prompt.

---

## Fragment Selection

At Stage 3.7, pick fragments based on `scene_bundle.observed_artefact_structure` and `selected_plugin.output_summary`:

| `observed_artefact_structure` shape | Fragments to include |
|---|---|
| `{columns: [...], per_person_output: "sms"}` | page-shell + roster-grid + sms-card + metric-bar |
| `{columns: [...]}` with no per-person output | page-shell + table-view + metric-bar |
| `{type: "calendar"}` or scheduling without SMS | page-shell + roster-grid + metric-bar |
| `{type: "report"}` or aggregated output | page-shell + table-view + metric-bar |
| Single-output action (email, invoice, update) | page-shell + table-view + metric-bar |

Always include **page-shell** and **metric-bar**. The page-shell goes first; metric-bar goes before the footer.

---

## Section 4b — Instruction Block (embed verbatim in demo prompt)

Copy this block into the demo prompt after Section 4 (Output format). Replace `{client_slug}` and the placeholder descriptions with scenario-specific equivalents.

```
**Section 4b — Visual Demo Artifact**

After printing the run sheet table and the SMS fabrication lines above, produce a
complete self-contained HTML file using the shell and fragments below.

Rules for filling the HTML:
- Replace every `{{PLACEHOLDER}}` with the real data you computed above.
- `{{STAFF_COLUMNS}}` → one `<th>` per staff member (their first name, bold).
- `{{TIME_ROWS}}` → one `<tr>` per 30-min time slot from the earliest start to latest end.
  In each cell: if that staff member has a task in that slot, render an `.apg-roster__block`
  div with the task name and location. Use `--transport` modifier for pickup/drop-off tasks,
  `--home` modifier for home visits, no modifier for cafe/floor work.
- `{{SMS_CARDS}}` → one `.apg-sms-card` block per staff member, in roster order.
  Use their first initial for the avatar. For `.apg-sms-card__bubble`, paste the exact
  SMS text you generated above (no markdown, preserve line breaks with \n).
- `{{STAFF_COUNT}}` → integer count of staff columns (e.g. 7).
- `{{RUN_TITLE}}` → e.g. "Brightside Services — Monday Run Sheet".
- `{{DEMO_DATE}}` → e.g. "Mon 14 Apr 2025".
- `{{BEFORE_TIME}}`, `{{AFTER_TIME}}` → from the scenario (e.g. "3–5 hrs / day", "~30 sec").
- `{{BEFORE_LABEL}}`, `{{AFTER_LABEL}}` → e.g. "Daily run build (before)", "With Claude Cowork".
- `{{STAFF_COUNT_SUMMARY}}`, `{{PARTICIPANT_COUNT}}`, `{{SMS_COUNT}}` → from the summary line.

After writing the file, print:
`Visual demo written → clients/{client_slug}/cowork-demo/live-demo.html`

Then emit the complete HTML in a single fenced code block:
```html
[the completed HTML]
```
```

---

## HTML Shell

The full HTML to embed in Section 4b of the demo prompt. Paste from `<!-- PAGE SHELL START -->` to `<!-- PAGE SHELL END -->` inclusive. Replace `{{PLACEHOLDER}}` values as instructed above.

---

### FRAGMENT: page-shell

```html
<!-- PAGE SHELL START -->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{RUN_TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/* APG brand tokens — sourced from apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py */
:root {
  --apg-lime: #7DFF00;
  --apg-lime-muted: rgba(125,255,0,0.12);
  --apg-lime-border: rgba(125,255,0,0.3);
  --apg-dark: #0f1825;
  --apg-dark-2: #1a2535;
  --apg-dark-3: #243044;
  --apg-grey: #64748b;
  --apg-light: #f7f9fc;
  --apg-white: #ffffff;
  --apg-border: rgba(255,255,255,0.08);
  --apg-transport: rgba(59,130,246,0.18);
  --apg-transport-border: #3b82f6;
  --apg-home: rgba(168,85,247,0.18);
  --apg-home-border: #a855f7;
  --font: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--apg-dark);
  color: var(--apg-white);
  font-family: var(--font);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

/* ── Header ── */
.apg-header {
  background: var(--apg-dark-2);
  border-bottom: 1px solid var(--apg-border);
  padding: 14px 32px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.apg-header__logo {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--apg-dark-3);
  display: flex;
  align-items: center;
  justify-content: center;
}
.apg-header__logo img { width: 100%; height: 100%; object-fit: contain; }
.apg-header__logo-fallback {
  font-size: 15px;
  font-weight: 700;
  color: var(--apg-lime);
}
.apg-header__info { flex: 1; }
.apg-header__title { font-size: 15px; font-weight: 600; line-height: 1.3; }
.apg-header__sub { font-size: 12px; color: var(--apg-grey); margin-top: 2px; }
.apg-header__badge {
  background: var(--apg-lime-muted);
  border: 1px solid var(--apg-lime-border);
  color: var(--apg-lime);
  font-size: 10px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  white-space: nowrap;
}

/* ── Layout ── */
.apg-main { padding: 32px; max-width: 1440px; margin: 0 auto; }
.apg-section { margin-bottom: 40px; }
.apg-section-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--apg-lime);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 14px;
}

/* ── FRAGMENT: roster-grid ── */
.apg-roster-wrap {
  background: var(--apg-dark-2);
  border: 1px solid var(--apg-border);
  border-radius: 12px;
  overflow: hidden;
  overflow-x: auto;
}
.apg-roster {
  display: grid;
  grid-template-columns: 72px repeat({{STAFF_COUNT}}, minmax(120px, 1fr));
  min-width: 560px;
}
.apg-roster__cell {
  padding: 8px 10px;
  border-right: 1px solid var(--apg-border);
  border-bottom: 1px solid var(--apg-border);
  font-size: 12px;
  min-height: 36px;
  vertical-align: top;
}
.apg-roster__cell:last-child { border-right: none; }
.apg-roster__cell--head {
  background: var(--apg-lime-muted);
  color: var(--apg-lime);
  font-weight: 700;
  font-size: 11px;
  text-align: center;
  letter-spacing: 0.3px;
  padding: 10px;
}
.apg-roster__cell--time {
  color: var(--apg-grey);
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  padding-top: 10px;
}
.apg-roster__block {
  background: var(--apg-lime-muted);
  border-left: 3px solid var(--apg-lime);
  border-radius: 4px;
  padding: 5px 8px;
  font-size: 11px;
  line-height: 1.4;
  margin: 2px 0;
}
.apg-roster__block--transport {
  background: var(--apg-transport);
  border-left-color: var(--apg-transport-border);
}
.apg-roster__block--home {
  background: var(--apg-home);
  border-left-color: var(--apg-home-border);
}
.apg-roster__block strong { display: block; font-weight: 600; }
.apg-roster__block span { color: rgba(255,255,255,0.55); font-size: 10px; }
.apg-roster__legend {
  display: flex;
  gap: 16px;
  padding: 12px 14px;
  border-top: 1px solid var(--apg-border);
  background: var(--apg-dark-2);
  flex-wrap: wrap;
}
.apg-roster__legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--apg-grey);
}
.apg-roster__legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

/* ── FRAGMENT: sms-card ── */
.apg-sms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}
.apg-sms-card {
  background: var(--apg-dark-2);
  border: 1px solid var(--apg-border);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s;
}
.apg-sms-card.sent { border-color: var(--apg-lime-border); }
.apg-sms-card__header {
  padding: 12px 14px 10px;
  border-bottom: 1px solid var(--apg-border);
  display: flex;
  align-items: center;
  gap: 10px;
}
.apg-sms-card__avatar {
  width: 34px;
  height: 34px;
  background: var(--apg-lime-muted);
  border: 1px solid var(--apg-lime-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: var(--apg-lime);
  flex-shrink: 0;
}
.apg-sms-card__name { font-weight: 600; font-size: 13px; }
.apg-sms-card__phone { font-size: 11px; color: var(--apg-grey); }
.apg-sms-card__body { padding: 12px 14px; flex: 1; }
.apg-sms-card__bubble {
  background: var(--apg-dark-3);
  border-radius: 12px 12px 12px 4px;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apg-white);
  border: 1px solid var(--apg-border);
}
.apg-sms-card__footer {
  padding: 10px 14px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-top: 1px solid var(--apg-border);
}
.apg-sms-card__chars { font-size: 11px; color: var(--apg-grey); flex: 1; }
.apg-btn-send {
  background: var(--apg-lime);
  color: var(--apg-dark);
  border: none;
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font);
  transition: opacity 0.15s, transform 0.1s;
  white-space: nowrap;
}
.apg-btn-send:hover:not(:disabled) { opacity: 0.85; transform: translateY(-1px); }
.apg-btn-send:active:not(:disabled) { transform: translateY(0); }
.apg-btn-send:disabled {
  background: var(--apg-lime-muted);
  border: 1px solid var(--apg-lime-border);
  color: var(--apg-lime);
  cursor: default;
  transform: none;
  opacity: 1;
}

/* ── FRAGMENT: table-view ── */
.apg-table-wrap {
  background: var(--apg-dark-2);
  border: 1px solid var(--apg-border);
  border-radius: 12px;
  overflow: hidden;
  overflow-x: auto;
}
.apg-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.apg-table th {
  background: var(--apg-lime-muted);
  color: var(--apg-lime);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 11px 16px;
  text-align: left;
  border-bottom: 1px solid var(--apg-border);
  white-space: nowrap;
}
.apg-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--apg-border);
  vertical-align: top;
  line-height: 1.5;
  font-size: 13px;
}
.apg-table tr:last-child td { border-bottom: none; }
.apg-table tr:nth-child(even) td { background: rgba(255,255,255,0.02); }
.apg-table tr:hover td { background: rgba(125,255,0,0.03); }
.apg-badge {
  display: inline-block;
  background: var(--apg-lime-muted);
  border: 1px solid var(--apg-lime-border);
  color: var(--apg-lime);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 20px;
  letter-spacing: 0.3px;
}

/* ── FRAGMENT: metric-bar ── */
.apg-metrics {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}
.apg-metric {
  background: var(--apg-dark-2);
  border: 1px solid var(--apg-border);
  border-radius: 12px;
  padding: 18px 22px;
  flex: 1;
  min-width: 160px;
}
.apg-metric__label {
  font-size: 10px;
  font-weight: 700;
  color: var(--apg-grey);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 10px;
}
.apg-metric__before {
  font-size: 14px;
  color: #f87171;
  text-decoration: line-through;
  margin-bottom: 4px;
  font-weight: 500;
}
.apg-metric__after {
  font-size: 26px;
  font-weight: 700;
  color: var(--apg-lime);
  line-height: 1;
}

/* ── Footer ── */
.apg-footer {
  border-top: 1px solid var(--apg-border);
  padding: 18px 32px;
  font-size: 11px;
  color: var(--apg-grey);
  text-align: center;
}
</style>
</head>
<body>

<header class="apg-header">
  <div class="apg-header__logo">
    <img src="https://pub-66c549f8c8d44c16ab441b6668d7a12a.r2.dev/APG%20Logo%20Rounded.png"
         alt="APG"
         onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
    <span class="apg-header__logo-fallback" style="display:none">A</span>
  </div>
  <div class="apg-header__info">
    <div class="apg-header__title">{{RUN_TITLE}}</div>
    <div class="apg-header__sub">{{DEMO_DATE}} · Generated by Claude Cowork</div>
  </div>
  <span class="apg-header__badge">Live Demo</span>
</header>

<main class="apg-main">
```

---

### FRAGMENT: roster-grid (insert inside `<main>`, after the `page-shell` opening)

```html
  <!-- Roster grid -->
  <section class="apg-section">
    <div class="apg-section-label">Run Sheet — {{DEMO_DATE}}</div>
    <div class="apg-roster-wrap">
      <div class="apg-roster">
        <!-- Header row: Time label + one column per staff member -->
        <div class="apg-roster__cell apg-roster__cell--head">Time</div>
        {{STAFF_COLUMNS}}
        <!-- Example of one staff column header:
        <div class="apg-roster__cell apg-roster__cell--head">Jay</div>
        Repeat for each staff member. -->

        {{TIME_ROWS}}
        <!-- Example of one time row:
        <div class="apg-roster__cell apg-roster__cell--time">7:30am</div>
        <div class="apg-roster__cell"></div>
        <div class="apg-roster__cell"></div>
        <div class="apg-roster__cell">
          <div class="apg-roster__block apg-roster__block--transport">
            <strong>Northside pickup</strong>
            <span>1 participant</span>
          </div>
        </div>
        ... (one <div class="apg-roster__cell"> per staff, for each time row)
        Repeat for each 30-min or 1-hr slot across the full day. -->
      </div>
      <div class="apg-roster__legend">
        <div class="apg-roster__legend-item">
          <div class="apg-roster__legend-dot" style="background:var(--apg-lime)"></div>
          Cafe / floor support
        </div>
        <div class="apg-roster__legend-item">
          <div class="apg-roster__legend-dot" style="background:var(--apg-transport-border)"></div>
          Transport run
        </div>
        <div class="apg-roster__legend-item">
          <div class="apg-roster__legend-dot" style="background:var(--apg-home-border)"></div>
          Home visit / community
        </div>
      </div>
    </div>
  </section>
```

---

### FRAGMENT: sms-card (insert inside `<main>`, after roster-grid)

```html
  <!-- SMS cards -->
  <section class="apg-section">
    <div class="apg-section-label">Staff SMS — {{SMS_COUNT}} messages</div>
    <div class="apg-sms-grid">
      {{SMS_CARDS}}
      <!-- Example of one SMS card:
      <div class="apg-sms-card" id="sms-jay">
        <div class="apg-sms-card__header">
          <div class="apg-sms-card__avatar">J</div>
          <div>
            <div class="apg-sms-card__name">Jay</div>
            <div class="apg-sms-card__phone">+61 4XX XXX XXX</div>
          </div>
        </div>
        <div class="apg-sms-card__body">
          <div class="apg-sms-card__bubble">Jay
Mon 14 Apr
8:30am — Cafe Lead — Riverside Cafe — Alex Brown, Sam Taylor, Jamie Lee, Casey Morgan, Robin Clark, Drew Evans, Pat Wilson
3:30pm — End
Qs call Jordan 0412 XXX XXX</div>
        </div>
        <div class="apg-sms-card__footer">
          <span class="apg-sms-card__chars">234 chars · 2 segments</span>
          <button class="apg-btn-send" onclick="sendSMS(this, 'jay')">Send</button>
        </div>
      </div>
      Repeat for each staff member. -->
    </div>
  </section>
```

---

### FRAGMENT: metric-bar (insert inside `<main>`, after sms-card or table-view)

```html
  <!-- Metrics -->
  <section class="apg-section">
    <div class="apg-section-label">Impact</div>
    <div class="apg-metrics">
      <div class="apg-metric">
        <div class="apg-metric__label">{{BEFORE_LABEL}}</div>
        <div class="apg-metric__before">{{BEFORE_TIME}}</div>
        <div class="apg-metric__after">{{AFTER_TIME}}</div>
      </div>
      <div class="apg-metric">
        <div class="apg-metric__label">Staff rostered</div>
        <div class="apg-metric__after" style="font-size:26px">{{STAFF_COUNT_SUMMARY}}</div>
      </div>
      <div class="apg-metric">
        <div class="apg-metric__label">Participants covered</div>
        <div class="apg-metric__after" style="font-size:26px">{{PARTICIPANT_COUNT}}</div>
      </div>
      <div class="apg-metric">
        <div class="apg-metric__label">SMS messages</div>
        <div class="apg-metric__after" style="font-size:26px">{{SMS_COUNT}}</div>
      </div>
    </div>
  </section>
```

---

### FRAGMENT: table-view (alternative to roster-grid for spreadsheet-output demos)

```html
  <!-- Data table -->
  <section class="apg-section">
    <div class="apg-section-label">{{TABLE_TITLE}}</div>
    <div class="apg-table-wrap">
      <table class="apg-table">
        <thead>
          <tr>
            {{TABLE_HEADERS}}
            <!-- Example: <th>Staff</th><th>Time</th><th>Task</th><th>Location</th><th>Participants</th><th>Notes</th> -->
          </tr>
        </thead>
        <tbody>
          {{TABLE_ROWS}}
          <!-- Example:
          <tr>
            <td><strong>Jordan</strong></td>
            <td>7:45am–9:00am</td>
            <td>City transport run</td>
            <td>Main St → Park Rd → North Ave → Riverside</td>
            <td>3 participants</td>
            <td></td>
          </tr>
          -->
        </tbody>
      </table>
    </div>
  </section>
```

---

### Page shell closing (always include — goes after all fragments, before `</body>`)

```html
</main>

<footer class="apg-footer">
  Note: send actions are simulated for this demo — live deployment connects to your real accounts.
</footer>

<script>
function sendSMS(btn, staffId) {
  btn.disabled = true;
  btn.textContent = '✓ Sent';
  const card = btn.closest('.apg-sms-card');
  if (card) card.classList.add('sent');
}

// Optional: wire "Send All" if you add a global button
function sendAll() {
  document.querySelectorAll('.apg-btn-send:not(:disabled)').forEach(function(btn) {
    const staffId = btn.closest('.apg-sms-card')?.id || '';
    sendSMS(btn, staffId);
  });
}
</script>

</body>
</html>
<!-- PAGE SHELL END -->
```

---

## Stage 3.7 Checklist

When executing Stage 3.7 in `build-cowork-demo.md`:

1. Read this file.
2. Consult fragment selection table above — pick fragments based on `scene_bundle.observed_artefact_structure`.
3. Assemble the full HTML by concatenating: page-shell opening → selected body fragment(s) → metric-bar → page-shell closing.
4. Pre-fill static placeholders you already know (from `scene_bundle`):
   - `{{RUN_TITLE}}` → `{company_name} — {selected_plugin.title}`
   - `{{DEMO_DATE}}` → the scenario date (e.g. "Mon 14 Apr")
   - `{{STAFF_COUNT}}` → integer from `scene_bundle.concrete_examples[]` staff count
   - `{{BEFORE_TIME}}`, `{{BEFORE_LABEL}}` → from `selected_plugin.simplification_metric`
   - Leave `{{STAFF_COLUMNS}}`, `{{TIME_ROWS}}`, `{{SMS_CARDS}}`, `{{TABLE_ROWS}}` etc. as-is — the demo-time model fills those from the run it just built.
5. Insert the assembled HTML into Section 4b of the demo prompt, wrapped by the Section 4b instruction block (above).
6. The prompt body (including Section 4b) is then copied identically into both `SKILL.md` and `demo-prompt.md`.

---

## Cowork Inline Render Status

*To be filled in after the first empirical test with Jordan Brightside Services demo:*

```
Tested: [date]
Outcome: [1 / 2 / 3]
1 — Inline interactive artifact rendered correctly (Send button JS fired) → primary demo mode
2 — Inline artifact rendered but JS did not fire → use open live-demo.html for interactive beats
3 — Only fenced code block shown, no inline render → always use open live-demo.html on calls
Notes: [any observations]
```
