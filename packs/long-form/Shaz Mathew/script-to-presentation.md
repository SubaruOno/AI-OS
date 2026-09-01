---
name: script-to-presentation
description: >-
  Converts YouTube scripts into production-ready HTML presentations optimized for filming with a teleprompter.
  Generates self-contained, zero-dependency HTML files with animations, navigation, and speaker notes.
  20+ slides minimum, visual-first design, opens directly in browser. Use when the user says:
  "turn this script into a presentation", "make slides for this", "presentation from this script",
  "convert this to slides", "create a presentation", "slides for my video", or pastes a YouTube
  script and asks for presentation slides.
disable-model-invocation: false
argument-hint: "[paste YouTube script or path to script file]"
---

# Script to Presentation

Transform YouTube scripts into production-ready HTML presentations for filming. Zero dependencies, self-contained HTML files that open directly in the browser. No external tools needed; Claude generates the finished presentation directly.

## Brand Reference (Optional)

If the project has a brand voice, tone, or style guide file (for example `brand-voice.md`, `style-guide.md`, or similar), read it before generating slides so the copy matches the intended tone. If no such file exists, use a clear, educational, structured tone by default, not hyped or salesy.

---

## Design Philosophy

Every presentation must look like a **structured masterclass filmed with a teleprompter**, not a corporate pitch deck.

### Visual Principles
- **One idea per slide**: never overcrowd. If a slide has more than one concept, split it
- **Visual-first**: every slide has icons, charts, cards, or visual elements, never text-only
- **Large, readable text**: viewer can read it in a YouTube video (filmed with a teleprompter)
- **Icon/symbol-heavy, minimal text**: communicate through visuals, not paragraphs
- **Zero dependencies**: single HTML file with inline CSS/JS. No npm, no build tools, no external services

### Filming-Specific Requirements
- **16:9 optimized**: designed for widescreen filming and YouTube playback
- **Extra-large typography**: titles must be readable even when the presentation is background on camera
- **High contrast**: text must pop against the background at any viewing distance
- **Safe margins**: nothing positioned at the extreme edges where camera framing might clip
- **Speaker notes**: embedded as `data-notes` attributes on each slide section, hidden from view but available for reference

### Content Density Limits Per Slide

| Slide Type | Maximum Content |
|------------|-----------------|
| Title slide | 1 heading + 1 subtitle + optional tagline |
| Content slide | 1 heading + 4-5 bullet points OR 1 heading + 2 short paragraphs |
| Feature grid | 1 heading + 4-6 cards (2x2 or 2x3 grid) |
| Stat/number slide | 1 heading + 3 big numbers |
| Comparison slide | 1 heading + 2 side-by-side cards |
| Quote slide | 1 quote (max 2 lines) + attribution |
| Timeline/steps | 1 heading + 4 timeline items |

**Too much content? → Split into multiple slides. Never scroll.**

---

## Default Style: Clean White + Accent Color

Unless the user requests a different style, **always use this style without asking:**

### Colors
```css
:root {
    --bg: #FFFFFF;
    --surface: #F5F5F5;
    --surface2: #EFEFEF;
    --border: #E4E4E4;
    --border-strong: #D0D0D0;
    --text: #111111;
    --text2: #444444;
    --muted: #888888;
    --accent: #FB923C;          /* Default accent color, replace with the user's brand color */
    --accent-deep: #EA580C;
    --accent-light: #FFF7ED;
    --accent-mid: rgba(251, 146, 60, 0.15);
    --green: #16A34A;
    --green-light: #F0FDF4;
    --green-mid: rgba(22, 163, 74, 0.12);
    --blue: #2563EB;
    --blue-light: #EFF6FF;
    --blue-mid: rgba(37, 99, 235, 0.1);
    --amber: #D97706;
    --amber-light: #FFFBEB;
    --red: #DC2626;
}
```

### Typography
```css
/* Fonts: Clash Display (headings) + Satoshi (body) + JetBrains Mono (code) */
--font-display: 'Clash Display', sans-serif;
--font-body: 'Satoshi', sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* FILMING-OPTIMIZED: Must be readable on camera at filming distance */
--title-size: clamp(2.8rem, 7vw, 5.5rem);
--h2-size: clamp(2rem, 4.5vw, 3.6rem);
--h3-size: clamp(1.25rem, 2.6vw, 1.9rem);
--body-size: clamp(1rem, 1.6vw, 1.3rem);
--small-size: clamp(0.85rem, 1.2vw, 1rem);
--mono-size: clamp(0.85rem, 1.2vw, 1rem);
```

### Font Source
```html
<link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=jet-brains-mono@400&f[]=satoshi@400,500,700&display=swap">
```

### Signature Elements
- Clean white background with light grey surfaces (`--surface`, `--surface2`) for cards and sections
- Accent color used for headings, pills, highlights, and key numbers, never overused
- `.pill` components with colored backgrounds (orange, green, blue, amber) for labels and badges
- Icon boxes (`.icon-box`) with colored SVG icons, orange, green, blue, amber
- Card components (`.card`) with `--border` and subtle box-shadow hover lift
- Subtle floating gradient orbs (low opacity, large radius) on title and CTA slides for visual interest
- Progress bars with animated fills (`.bar-fill`) for data visualization
- Navigation: progress bar (top, accent color), nav dots (right), slide counter (bottom-right)
- Screen share cue slides: dark background (`#0A0A0A`) with amber pulsing border, intentionally contrast the white theme so they're unmissable during filming

---

## Phase 1: GATHER

### Step 1: Capture Input

The user will provide ONE of these:
- A **full YouTube script** (pasted text)
- A **script file path** to read
- A **video topic** with enough context to generate slides from scratch

**If none of these were given yet** (e.g. the skill was invoked with no script attached), ask warmly and simply, don't just state what's missing:

> "Happy to build that! Got a YouTube script for me, either pasted in or a path to the file? Or if you don't have one written yet, just tell me the topic and I'll work from that."

Do NOT ask clarifying questions about style or design. Use the default Clean White + Accent Color style immediately. Only ask if the script/topic is genuinely ambiguous.

### Step 2: Analyze the Script

Break the script into core components:
- **Hook/Opening**: what grabs attention
- **Key insights**: main ideas being taught
- **Frameworks/Systems**: structured processes or models
- **Proof points**: stats, case studies, metrics
- **CTA**: what the viewer should do next
- **Pattern interrupts**: any of the following markers signal a screen share cue slide:
  - `[PATTERN INTERRUPT`
  - `[SCREEN SHARE`
  - `[CUT TO`
  - `[DEMO`
  - `let me show you my screen`
  - `let me show you this`
  - `here's my screen`
  - Any phrase indicating a live demo or screen recording moment

### Step 3: Plan Slide Count

**Minimum: 20 slides.** Calculate based on content density:
- Each major section = 3-5 slides
- Each multi-point list = 1 slide per bullet
- Add transitional slides between major sections
- Add title card + CTA buffer slides
- Dense content → 25-30 slides

### Step 4: Plan Slide Types

Map each slide to a visual type:

| Content | Visual Approach |
|---------|----------------|
| Metrics, results, numbers | Big numbers (`.big-num`) or stat cards |
| Steps, workflows, processes | Timeline (`.timeline`) or step cards (`.step-card`) |
| Lists of features or items | Grid cards (`.grid-2` or `.grid-3`) with icon boxes |
| Before/after, comparisons | Side-by-side columns (`.vs-row`) |
| Key quotes or principles | Centered quote with divider |
| Terminal/code concepts | Terminal prompt styling (`.terminal-prompt`) |
| Proof/validation data | Result cards (`.result-card`) with colored view counts |
| Progress/ratios | Bar tracks (`.bar-track`) with colored fills |
| Section transitions | Pill badge + heading + subtitle |
| **Pattern interrupt / screen share cue** | **Screen share cue slide** (see spec below) |

### Screen Share Cue Slide Spec

Whenever a pattern interrupt or screen share moment is detected in the script, insert a dedicated cue slide at that exact position. This tells the presenter to stop the presentation and cut to screen share during filming.

**Visual design:**
- Full-screen dark slide with an amber/blue animated border pulse
- Large centered icon: monitor/terminal SVG
- Big text: `[ SCREEN SHARE ]` in monospace, amber color
- Below: the specific thing to show, extracted from the script context (e.g. `"Show: the tool's dashboard"`)
- Small muted label at bottom: `"Press any key to return to slides"`
- Distinct from all other slides, so the viewer immediately understands this is a filming cue

Use the `.screen-share-cue` classes already defined in `base-template.html` (see below) instead of hand-rolling new CSS for this.

---

## Phase 2: ACT

### Step 1: Use the base template instead of hand-rolling the CSS/JS

Write `base-template.html` (below) to this skill's folder if it doesn't already exist. **This is the required starting point for every presentation, not a reference to loosely follow.** It already implements the full design system described above: CSS variables, all slide component classes, and the navigation JS (keyboard/touch/scroll/progress bar/nav dots). It's already tested and correct.

To generate a presentation:
1. Copy `base-template.html` as the base for the new file
2. Set `{{TITLE}}` in the `<title>` tag to the video's title
3. If the user gave a brand/accent color, update the `--accent` (and related `--accent-*`) CSS variables. Otherwise leave the defaults
4. Build each slide as a `<section class="slide ...">` following the slide-type reference comments already in the template, and insert them at the `<!-- ADD SLIDES HERE -->` marker
5. Do not rewrite the CSS or the `Deck` JS class. They're already correct; only add slide markup.

The architecture section below describes what's already in the template, for reference only. It's there so you understand the structure, not so you rebuild it from scratch:

```
presentation.html
├── <head>
│   ├── Meta tags (charset, viewport)
│   ├── Font links (Fontshare)
│   └── <style> (all CSS inline, from base-template.html)
├── <body>
│   ├── Progress bar
│   ├── Nav dots container
│   ├── Slide counter
│   ├── <section class="slide" data-notes="Speaker note for this slide">
│   │   └── Slide content...
│   ├── ... (20+ slides, this is what you generate)
│   └── <script> (Deck class, from base-template.html, don't touch)
```

### Speaker Notes

Embed speaker notes as `data-notes` attributes on each slide section:

```html
<section class="slide" data-notes="Talk about how most people try this and get generic results.">
    <!-- slide content -->
</section>
```

Speaker notes should be:
- 1-2 sentences of narration guidance
- 5-10 seconds of speaking per slide
- What to SAY, not what to show (the visual handles that)

### Slide Construction Rules

1. **Every slide has a visual element**: icons, cards, grids, charts, comparisons, timelines, or styled components. No plain text slides.
2. **Maximum 20 words of on-screen text per slide** (excluding heading). Communicate through visuals.
3. **Headings max 8 words**, subtitles max 12 words.
4. **Use SVG icons inline**: stroke-based, 24x24 viewBox, no fills (stroke only). Common icons: layers, eye, calendar, user, chart, check, x, arrow, bell, shield, star, code, folder, file, mic, globe.
5. **Stagger animations**: use `.reveal` with `nth-child` delays for sequential entrance (already handled by the template's CSS, just apply the `.reveal` class).
6. **Color-code semantically**: accent = primary/brand, green = positive/success, blue = info/secondary, amber = warning/attention, red = negative/problem.

### Narrative Flow

Follow this arc for slide ordering:
```
Title Card → Problem/Hook → Analogy/Context → The Fix →
System Deep-Dive (expandable) → Proof/Results →
[CTA SLIDE, at ~35% of total slides, if the user has a free resource/link to promote] →
How-To Steps → Compound Effect → Hidden Insight → Final CTA
```

**Mid-deck CTA, 35% Rule (only if the user has something to promote):**
If the user has a free resource, link, or offer they want mentioned, place that CTA slide at approximately 35% through the total slide count, the retention sweet spot, after the first "value delivery" moment (a completed demo, a working example, the first big insight). Never place it at the very end only. Calculate: `Math.floor(totalSlides * 0.35)`. Use the `.slide-lm` class from the template (green-tinted, high-contrast) for this slide. Skip this entirely if the user has nothing to promote. Don't invent one.

### Step 2: Save and Open

Save the HTML file to the workspace:
```
workspace/{YYYY-MM-DD}/{slug}/presentation.html
```

If the script was loaded from an existing workspace folder, save it there. Otherwise create the folder.

Then open it:
```bash
open workspace/{path}/presentation.html
```

### Step 3: Present Summary

```
Your presentation is ready!

📁 File: workspace/{path}/presentation.html
🎨 Style: Clean White + Accent Color
📊 Slides: {count}

**Navigation:**
- Arrow keys or Space to navigate
- Scroll/swipe also works
- Click dots on the right to jump

**Speaker notes:** Embedded as data-notes attributes on each slide.

**For filming:** Optimized for teleprompter use, large text, high contrast, safe margins.

Want me to adjust anything?
```

---

## Phase 3: VERIFY

### Viewport Fitting Checks
- [ ] `html, body` have `scrollbar-width: none` + `::-webkit-scrollbar { display: none }`: no scrollbar visible on the right
- [ ] Every `.slide` has `height: 100vh; height: 100dvh; overflow: hidden;`
- [ ] All font sizes use `clamp(min, preferred, max)`
- [ ] All spacing uses `clamp()` or viewport units
- [ ] Content per slide respects density limits
- [ ] No fixed pixel heights on content elements

### Structural Checks
- [ ] Minimum 20 slides generated
- [ ] HTML is valid and self-contained (no external dependencies except the font CDN link)
- [ ] Base template's CSS and JS were used as-is, not rewritten
- [ ] Every slide has a `data-notes` attribute with speaker guidance

### Content Checks
- [ ] Narrative flows: Hook → Insight → Framework → Proof → CTA
- [ ] Each slide communicates one idea only
- [ ] No text-only slides, every slide has a visual element
- [ ] Script's actual CTA is preserved in the final slide
- [ ] Max 20 words of body text per slide
- [ ] Headings max 8 words

### Filming Checks
- [ ] Text is large enough to read in a YouTube video
- [ ] High contrast, text pops against white background
- [ ] No content at extreme edges (safe margin for camera framing)
- [ ] Speaker notes provide 5-10 seconds of narration guidance per slide
- [ ] Every screen-share moment in the script has a corresponding cue slide
- [ ] Title slide does NOT include video length ("15 min", "10 min", etc.)

---

## Output Specification

- **Format**: Self-contained HTML file (inline CSS + JS, only external dependency is the font CDN)
- **Location**: `workspace/{YYYY-MM-DD}/{slug}/presentation.html`
- **Auto-open**: Yes, open in browser immediately after generation
- **Speaker notes**: Embedded as `data-notes` attributes (hidden from view)

---

## Key Rules

1. **Use `base-template.html` as the literal starting point, never hand-roll the CSS/JS from scratch.**
2. **Minimum 20 slides**: always. Expand through transitional slides and individual bullet slides.
3. **One idea per slide**: never overcrowd. When in doubt, split.
4. **Visual-first**: every slide has icons, cards, grids, or visual components. No text-only.
5. **Self-contained HTML**: single file, zero dependencies (besides the font CDN), opens in any browser.
6. **Filming-optimized**: large text, high contrast, safe margins, designed for teleprompter use.
7. **Default style: Clean White + Accent Color**: don't ask, just generate.
8. **Speaker notes on every slide**: `data-notes` attribute, 5-10 seconds of narration.
9. **8-word title limit**: slide titles must be punchy and scannable.
10. **Max 20 words body text per slide**: communicate through visuals, not paragraphs.
11. **Preserve the script's CTA**: use the actual CTA from the script in the final slide.
12. **Screen share cue slides are mandatory**: every pattern interrupt in the script becomes a `.screen-share-cue` slide inserted at that exact position. Never skip or merge them.
13. **No video length on the title slide**: never add "X min" or any duration indicator.
14. **No scrollbar**: always hidden. The white scrollbar on the right is never acceptable.

---

## Embedded template, write this to `base-template.html` in this skill's folder if it doesn't already exist

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=jet-brains-mono@400&f[]=satoshi@400,500,700&display=swap">
<style>
/*
 * Presentation Template, Default Style
 *
 * USE THIS FILE as the CSS/JS base for every new presentation.
 * Do NOT introduce new design systems or minimal/editorial layouts.
 * The full design system below is the approved look. Customize
 * the --accent color variable to match the user's brand.
 */

:root {
  --bg: #FFFFFF;
  --surface: #F5F5F5;
  --surface2: #EFEFEF;
  --border: #E4E4E4;
  --border-strong: #D0D0D0;
  --text: #111111;
  --text2: #444444;
  --muted: #888888;
  --accent: #FB923C;
  --accent-deep: #EA580C;
  --accent-light: #FFF7ED;
  --accent-mid: rgba(251,146,60,0.15);
  --green: #16A34A;
  --green-light: #F0FDF4;
  --green-mid: rgba(22,163,74,0.12);
  --blue: #2563EB;
  --blue-light: #EFF6FF;
  --blue-mid: rgba(37,99,235,0.1);
  --amber: #D97706;
  --amber-light: #FFFBEB;
  --red: #DC2626;
  --font-display: 'Clash Display', sans-serif;
  --font-body: 'Satoshi', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  /* FILMING-OPTIMIZED, do not go below these */
  --title-size: clamp(2.8rem, 7vw, 5.5rem);
  --h2-size: clamp(2rem, 4.5vw, 3.6rem);
  --h3-size: clamp(1.25rem, 2.6vw, 1.9rem);
  --body-size: clamp(1rem, 1.6vw, 1.3rem);
  --small-size: clamp(0.85rem, 1.2vw, 1rem);
  --mono-size: clamp(0.85rem, 1.2vw, 1rem);
  --slide-padding: clamp(3rem, 6vw, 6rem);
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;overflow:hidden;scrollbar-width:none;-ms-overflow-style:none;background:var(--bg);}
html::-webkit-scrollbar,body::-webkit-scrollbar{display:none;}
html{scroll-snap-type:y mandatory;scroll-behavior:smooth;}
body{font-family:var(--font-body);color:var(--text);}

#progress-bar{position:fixed;top:0;left:0;height:3px;background:var(--accent);z-index:100;transition:width .3s ease;width:0%;}
#nav-dots{position:fixed;right:1.5rem;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:.5rem;z-index:100;}
.nav-dot{width:6px;height:6px;border-radius:50%;background:var(--border-strong);cursor:pointer;transition:background .2s,transform .2s;}
.nav-dot.active{background:var(--accent);transform:scale(1.5);}
#slide-counter{position:fixed;bottom:1.5rem;right:1.5rem;font-family:var(--font-mono);font-size:.7rem;color:var(--muted);z-index:100;}

.slide{width:100vw;height:100vh;height:100dvh;overflow:hidden;scroll-snap-align:start;display:flex;flex-direction:column;justify-content:center;align-items:center;position:relative;padding:var(--slide-padding);background:var(--bg);}
.slide-content{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;max-height:100%;overflow:hidden;width:100%;max-width:1100px;}
.slide-content.left{align-items:flex-start;}

.h1{font-family:var(--font-display);font-weight:700;font-size:var(--title-size);line-height:1.05;letter-spacing:-.03em;color:var(--text);}
.h1 em,.h2 em,.h3 em{font-style:normal;color:var(--accent);}
.h2{font-family:var(--font-display);font-weight:600;font-size:var(--h2-size);line-height:1.1;letter-spacing:-.02em;color:var(--text);}
.h3{font-family:var(--font-display);font-weight:600;font-size:var(--h3-size);line-height:1.2;letter-spacing:-.01em;color:var(--text);}
.body-t{font-size:var(--body-size);line-height:1.65;color:var(--text2);}
.small-t{font-size:var(--small-size);color:var(--muted);}
.mono{font-family:var(--font-mono);font-size:var(--mono-size);}
.text-center{text-align:center;}
.mt-xs{margin-top:clamp(.4rem,.8vw,.65rem);}
.mt-sm{margin-top:clamp(.75rem,1.5vw,1.25rem);}
.mt-md{margin-top:clamp(1.25rem,2.5vw,2rem);}
.mt-lg{margin-top:clamp(2rem,4vw,3.5rem);}

/* Pills */
.pill{display:inline-flex;align-items:center;gap:.4rem;padding:.35em .85em;border-radius:100px;font-size:var(--small-size);font-weight:600;letter-spacing:.02em;}
.pill-orange{background:var(--accent-mid);color:var(--accent-deep);}
.pill-green{background:var(--green-mid);color:var(--green);}
.pill-blue{background:var(--blue-mid);color:var(--blue);}
.pill-amber{background:rgba(217,119,6,.12);color:var(--amber);}

/* Cards */
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:clamp(1.2rem,2.5vw,1.8rem);}
.icon-box{width:clamp(2.5rem,4vw,3.2rem);height:clamp(2.5rem,4vw,3.2rem);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.icon-box svg{width:clamp(1.2rem,2vw,1.5rem);height:clamp(1.2rem,2vw,1.5rem);stroke-width:1.8;fill:none;stroke-linecap:round;stroke-linejoin:round;}
.icon-orange{background:var(--accent-light);}
.icon-orange svg{stroke:var(--accent);}
.icon-green{background:var(--green-light);}
.icon-green svg{stroke:var(--green);}
.icon-blue{background:var(--blue-light);}
.icon-blue svg{stroke:var(--blue);}
.icon-amber{background:var(--amber-light);}
.icon-amber svg{stroke:var(--amber);}

/* Grids */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:clamp(.75rem,1.5vw,1.25rem);width:100%;}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:clamp(.75rem,1.5vw,1.25rem);width:100%;}

/* Icon cards */
.icon-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:clamp(1rem,2vw,1.5rem);display:flex;flex-direction:column;gap:.65rem;}
.icon-card .card-title{font-family:var(--font-display);font-weight:600;font-size:clamp(1rem,1.7vw,1.35rem);color:var(--text);}
.icon-card .card-desc{font-size:clamp(.85rem,1.2vw,1rem);color:var(--text2);line-height:1.5;}

/* Big numbers */
.big-num{font-family:var(--font-display);font-weight:700;font-size:clamp(4rem,10vw,8rem);line-height:1;letter-spacing:-.04em;color:var(--accent);}
.big-num-label{font-size:var(--body-size);color:var(--text2);margin-top:.4rem;}

/* Stat row */
.stat-row{display:flex;gap:clamp(2rem,5vw,4rem);align-items:flex-end;}
.stat-item{display:flex;flex-direction:column;gap:.25rem;}
.stat-value{font-family:var(--font-display);font-weight:700;font-size:clamp(2.8rem,7vw,5.5rem);line-height:1;letter-spacing:-.04em;color:var(--text);}
.stat-value.accent{color:var(--accent);}
.stat-label{font-size:var(--small-size);color:var(--muted);}

/* Timeline */
.timeline{display:flex;flex-direction:column;gap:clamp(.75rem,1.5vw,1.25rem);width:100%;}
.tl-item{display:flex;gap:clamp(1rem,2vw,1.5rem);align-items:flex-start;}
.tl-dot{width:10px;height:10px;border-radius:50%;background:var(--accent);flex-shrink:0;margin-top:.45rem;}
.tl-title{font-family:var(--font-display);font-weight:600;font-size:clamp(1rem,1.7vw,1.35rem);color:var(--text);}
.tl-desc{font-size:clamp(.85rem,1.2vw,1rem);color:var(--text2);margin-top:.2rem;line-height:1.5;}

/* VS / Before-After */
.vs-row{display:grid;grid-template-columns:1fr auto 1fr;gap:clamp(1rem,2vw,1.5rem);align-items:center;width:100%;}
.vs-label{font-family:var(--font-display);font-weight:700;font-size:clamp(1rem,1.8vw,1.4rem);text-align:center;color:var(--muted);}
.vs-card-bad{background:#FEF2F2;border:1px solid #FECACA;border-radius:12px;padding:clamp(1rem,2vw,1.5rem);}
.vs-card-good{background:var(--green-light);border:1px solid #BBF7D0;border-radius:12px;padding:clamp(1rem,2vw,1.5rem);}

/* Workflow steps */
.wf-steps{display:flex;flex-direction:column;gap:clamp(.5rem,1vw,.85rem);width:100%;}
.wf-step{display:flex;gap:clamp(.8rem,1.5vw,1.25rem);align-items:flex-start;padding:clamp(.7rem,1.3vw,1rem) clamp(1rem,1.8vw,1.4rem);background:var(--surface);border:1px solid var(--border);border-radius:10px;}
.wf-num{font-family:var(--font-display);font-weight:700;font-size:clamp(1rem,1.8vw,1.4rem);color:var(--accent);flex-shrink:0;min-width:2rem;}
.wf-title{font-family:var(--font-display);font-weight:600;font-size:clamp(1rem,1.7vw,1.35rem);color:var(--text);}
.wf-desc{font-size:clamp(.85rem,1.2vw,1rem);color:var(--text2);margin-top:.15rem;}

/* Quote */
.quote-block{border-left:3px solid var(--accent);padding-left:clamp(1.25rem,2.5vw,2rem);}
.quote-text{font-family:var(--font-display);font-weight:600;font-size:clamp(1.1rem,2.2vw,1.8rem);line-height:1.35;color:var(--text);}
.quote-source{font-size:var(--small-size);color:var(--muted);margin-top:.75rem;}

/* Dividers */
.divider{width:100%;height:1px;background:var(--border);}
.divider-accent{width:40px;height:3px;background:var(--accent);border-radius:2px;}

/* Progress bars */
.bar-track{height:10px;background:var(--surface2);border-radius:100px;overflow:hidden;width:100%;}
.bar-fill{height:100%;border-radius:100px;}

/* Section transition slides */
.slide-section{background:var(--surface)!important;}

/* Screen share cue slides */
.screen-share-cue{background:#09090B!important;}
.screen-share-cue .cue-border{position:absolute;inset:12px;border:2px solid rgba(251,191,36,.35);border-radius:12px;animation:border-pulse 2.5s ease-in-out infinite;pointer-events:none;}
@keyframes border-pulse{0%,100%{border-color:rgba(251,191,36,.35);box-shadow:0 0 0 0 rgba(251,191,36,0);}50%{border-color:rgba(251,191,36,.7);box-shadow:0 0 30px rgba(251,191,36,.15);}}
.cue-icon{width:clamp(4rem,10vw,7rem);height:clamp(4rem,10vw,7rem);margin:0 auto;}
.cue-icon svg{width:100%;height:100%;stroke:var(--amber);fill:none;stroke-width:1;stroke-linecap:round;stroke-linejoin:round;}
.cue-label{font-family:var(--font-mono);font-size:clamp(1.4rem,3vw,2.5rem);color:var(--amber);letter-spacing:.1em;}
.cue-title{font-family:var(--font-display);font-weight:600;font-size:clamp(1.1rem,2.2vw,1.8rem);color:#E5E7EB;}
.cue-desc{font-size:clamp(.9rem,1.3vw,1.1rem);color:#6B7280;max-width:500px;line-height:1.5;text-align:center;}
.cue-hint{font-family:var(--font-mono);font-size:clamp(.75rem,1vw,.9rem);color:#374151;letter-spacing:.05em;}
.cue-flex{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;gap:clamp(.5rem,1.2vw,1rem);}

/* Lead magnet slide */
.slide-lm{background:var(--green-light)!important;}
.lm-card{background:#fff;border:1px solid #BBF7D0;border-radius:16px;padding:clamp(1.5rem,3vw,2.5rem);max-width:640px;width:100%;box-shadow:0 0 0 4px rgba(22,163,74,.08);}
.lm-dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:lm-pulse 2s ease-in-out infinite;flex-shrink:0;}
@keyframes lm-pulse{0%,100%{transform:scale(1);opacity:1;}50%{transform:scale(1.8);opacity:.45;}}

/* CTA slide */
.slide-cta{background:#0A0A0A!important;}
.orb,.cta-orb{position:absolute;border-radius:50%;pointer-events:none;filter:blur(80px);opacity:.12;}

/* Animations */
.reveal{opacity:0;transform:translateY(20px);transition:opacity .7s cubic-bezier(.16,1,.3,1),transform .7s cubic-bezier(.16,1,.3,1);}
.slide.visible .reveal{opacity:1;transform:translateY(0);}
.reveal:nth-child(1){transition-delay:.05s;}
.reveal:nth-child(2){transition-delay:.15s;}
.reveal:nth-child(3){transition-delay:.28s;}
.reveal:nth-child(4){transition-delay:.42s;}
.reveal:nth-child(5){transition-delay:.56s;}
.reveal:nth-child(6){transition-delay:.70s;}
.reveal:nth-child(7){transition-delay:.84s;}
.reveal:nth-child(8){transition-delay:.98s;}

@media(max-height:700px){:root{--slide-padding:clamp(2rem,4vw,4rem);}
  .h1{font-size:clamp(2.2rem,5.5vw,4rem);}
  .big-num{font-size:clamp(3rem,8vw,6rem);}
  .wf-step{padding:.55rem .9rem;}}
@media(max-height:600px){#nav-dots{display:none;}:root{--slide-padding:clamp(1.5rem,3vw,3rem);}}
@media(max-width:768px){.grid-2,.grid-3{grid-template-columns:1fr;}.vs-row{grid-template-columns:1fr;}.stat-row{flex-direction:column;gap:1.5rem;}}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none;}.cue-border,.lm-dot{animation:none;}}
</style>
</head>
<body>

<div id="progress-bar"></div>
<div id="nav-dots"></div>
<div id="slide-counter">1 / N</div>

<!--
  SLIDE TYPES REFERENCE:

  TITLE SLIDE (white bg, orb gradients):
  <section class="slide" data-notes="...">
    <div class="orb" style="width:600px;height:600px;background:var(--accent);top:-200px;right:-100px;"></div>
    <div class="slide-content left">
      <div class="reveal"><span class="pill pill-orange">Label</span></div>
      <h1 class="h1 mt-md reveal">Title with <em>Accent Word</em></h1>
      <div class="divider-accent mt-md reveal"></div>
      <p class="body-t mt-md reveal">Subtitle text.</p>
    </div>
  </section>

  SECTION TRANSITION (grey bg):
  <section class="slide slide-section" data-notes="...">
    <div class="slide-content text-center">
      <div class="reveal"><span class="pill pill-orange">Section 01</span></div>
      <h2 class="h2 mt-md reveal">Section <em>Title</em></h2>
      <div class="divider-accent mt-md reveal" style="margin:1.5rem auto 0;"></div>
      <p class="body-t mt-sm reveal" style="max-width:480px;">One-line summary.</p>
    </div>
  </section>

  SCREEN SHARE CUE (dark bg, amber pulse):
  <section class="slide screen-share-cue" data-notes="CUT TO SCREEN SHARE: What to show.">
    <div class="cue-border"></div>
    <div class="cue-flex">
      <div class="cue-icon reveal"><svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg></div>
      <div class="cue-label reveal">[ SCREEN SHARE ]</div>
      <div class="cue-title reveal">What to show</div>
      <div class="cue-desc reveal">Specific instructions for filming.</div>
      <div class="cue-hint reveal mt-md">Press any key to continue →</div>
    </div>
  </section>

  LEAD MAGNET / CTA CARD (green bg):
  <section class="slide slide-lm" data-notes="Drop CTA here.">
    <div class="slide-content text-center">
      <div class="lm-card">
        <div style="display:flex;align-items:center;gap:.75rem;justify-content:center;" class="reveal">
          <div class="lm-dot"></div>
          <span class="pill pill-green">Free, Link in Description</span>
        </div>
        <h2 class="h2 mt-md reveal" style="color:var(--green);">Resource Title</h2>
      </div>
    </div>
  </section>

  CTA SLIDE (dark bg):
  <section class="slide slide-cta" data-notes="Close here.">
    <div class="cta-orb" style="width:500px;height:500px;background:var(--accent);top:-200px;right:-100px;"></div>
    <div class="slide-content text-center">
      <h2 class="h2 mt-md reveal" style="color:#FFF;">CTA <em>Heading</em></h2>
    </div>
  </section>
-->

<!-- ADD SLIDES HERE -->

<script>
class Deck {
  constructor() {
    this.slides = document.querySelectorAll('.slide');
    this.total = this.slides.length;
    this.current = 0;
    this.bar = document.getElementById('progress-bar');
    this.dotsEl = document.getElementById('nav-dots');
    this.counter = document.getElementById('slide-counter');
    this.counter.textContent = '1 / ' + this.total;
    this.buildDots();
    this.observe();
    this.keys();
    this.touch();
    this.wheel();
  }
  buildDots() {
    this.slides.forEach((_,i) => {
      const d = document.createElement('div');
      d.className = 'nav-dot';
      d.onclick = () => this.go(i);
      this.dotsEl.appendChild(d);
    });
    this.dots = document.querySelectorAll('.nav-dot');
  }
  observe() {
    const io = new IntersectionObserver(es => {
      es.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          this.current = [...this.slides].indexOf(e.target);
          this.update();
        } else { e.target.classList.remove('visible'); }
      });
    }, {threshold: 0.5});
    this.slides.forEach(s => io.observe(s));
  }
  keys() {
    document.addEventListener('keydown', e => {
      if (['ArrowDown','ArrowRight','Space','PageDown'].includes(e.code)) { e.preventDefault(); this.next(); }
      else if (['ArrowUp','ArrowLeft','PageUp'].includes(e.code)) { e.preventDefault(); this.prev(); }
      else if (e.code==='Home') { e.preventDefault(); this.go(0); }
      else if (e.code==='End') { e.preventDefault(); this.go(this.total-1); }
    });
  }
  touch() {
    let sy=0,sx=0;
    document.addEventListener('touchstart', e => { sy=e.touches[0].clientY; sx=e.touches[0].clientX; }, {passive:true});
    document.addEventListener('touchend', e => {
      const dy=sy-e.changedTouches[0].clientY, dx=sx-e.changedTouches[0].clientX;
      if (Math.abs(dy)>Math.abs(dx) && Math.abs(dy)>40) { dy>0?this.next():this.prev(); }
    }, {passive:true});
  }
  wheel() {
    let last=0;
    document.addEventListener('wheel', e => {
      e.preventDefault();
      const now=Date.now(); if(now-last<600) return; last=now;
      e.deltaY>0?this.next():this.prev();
    }, {passive:false});
  }
  next() { if(this.current<this.total-1) this.go(this.current+1); }
  prev() { if(this.current>0) this.go(this.current-1); }
  go(i) { this.slides[i].scrollIntoView({behavior:'smooth'}); this.current=i; this.update(); }
  update() {
    const pct = this.total>1 ? (this.current/(this.total-1))*100 : 0;
    this.bar.style.width = pct+'%';
    this.dots.forEach((d,i) => d.classList.toggle('active', i===this.current));
    this.counter.textContent = (this.current+1)+' / '+this.total;
  }
}
window.addEventListener('load', () => new Deck());
</script>
</body>
</html>
```
