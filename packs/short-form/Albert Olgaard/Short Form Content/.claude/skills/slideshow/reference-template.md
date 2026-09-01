# Slideshow Reference Template

This is the complete component library for building HTML slideshows. The canonical working example is at `3. Slideshows/freeclaude/index.html` — read it for the full implementation.

## HTML Skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SLIDESHOW TITLE</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    /* ALL CSS HERE */
  </style>
</head>
<body>
  <div class="progress" id="progress"></div>
  <div class="click-zone left" onclick="navigate(-1)"></div>
  <div class="click-zone right" onclick="navigate(1)"></div>

  <div class="deck" id="deck">
    <!-- SLIDES HERE -->
  </div>

  <div class="nav-dots" id="dots">
    <!-- ONE BUTTON PER SLIDE -->
  </div>
  <div class="slide-counter" id="counter">1 / N</div>

  <script>
    /* ALL JS HERE */
  </script>
</body>
</html>
```

## CSS Design System

### Variables (adapt accent color per slideshow)

```css
:root {
  --bg-void: #0d0d0d;
  --bg-primary: #141414;
  --bg-card: #1c1c1c;
  --bg-code: #1a1a1a;
  --bg-elevated: #252525;
  --accent: #3B82F6;          /* CHANGE PER SLIDESHOW */
  --accent-bright: #60A5FA;   /* CHANGE PER SLIDESHOW */
  --accent-glow: rgba(96, 165, 250, 0.35);   /* CHANGE */
  --accent-subtle: rgba(96, 165, 250, 0.12); /* CHANGE */
  --text-primary: #f0f0f0;
  --text-secondary: #999999;
  --text-muted: #555555;
  --green: #4ade80;
  --blue: #60a5fa;
  --font-display: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --radius: 16px;
  --radius-sm: 10px;
}
```

### Reset & Base

```css
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
  width: 100%; height: 100%;
  overflow: hidden;
  background: var(--bg-void);
  color: var(--text-primary);
  font-family: var(--font-display);
  -webkit-font-smoothing: antialiased;
}
```

### Progress Bar

```css
.progress {
  position: fixed; top: 0; left: 0;
  height: 3px;
  background: var(--accent);
  z-index: 100;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 12px var(--accent-glow);
}
```

### Deck & Slides

```css
.deck {
  display: flex;
  width: {N}00vw;  /* N = number of slides */
  height: 100vh;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide {
  width: 100vw; height: 100vh;
  display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
}
.slide-inner {
  max-width: 1000px; width: 90%;
  text-align: center; z-index: 2;
}
```

### Entrance Animations

```css
.slide .animate-in {
  opacity: 0; transform: translateY(30px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.slide.active .animate-in { opacity: 1; transform: translateY(0); }
.slide.active .animate-in:nth-child(2) { transition-delay: 0.1s; }
.slide.active .animate-in:nth-child(3) { transition-delay: 0.2s; }
.slide.active .animate-in:nth-child(4) { transition-delay: 0.3s; }
.slide.active .animate-in:nth-child(5) { transition-delay: 0.4s; }
```

### Typography

```css
h1 {
  font-family: var(--font-display); font-weight: 800;
  font-size: clamp(2.4rem, 6vw, 4.5rem);
  line-height: 1.1; letter-spacing: -0.02em;
}
h2 {
  font-family: var(--font-display); font-weight: 800;
  font-size: clamp(2rem, 4.5vw, 3.5rem);
  line-height: 1.15; letter-spacing: -0.02em;
  margin-bottom: 1.5rem;
}
.accent { color: var(--accent-bright); }
.subtitle {
  font-family: var(--font-mono);
  font-size: clamp(0.9rem, 1.8vw, 1.2rem);
  color: var(--text-secondary); margin-top: 1.2rem;
}
.description {
  font-size: clamp(1rem, 2vw, 1.35rem);
  color: var(--text-secondary); line-height: 1.5;
  max-width: 700px; margin: 0 auto;
}
```

### Slide Backgrounds

Each slide gets a radial glow via `::before` and a grid overlay via `::after`:

```css
.slide::before {
  content: ''; position: absolute; inset: 0;
  z-index: 0; pointer-events: none;
}
/* Per-slide glow — vary position, size, color */
.slide-1::before {
  background: radial-gradient(ellipse 60% 50% at 50% 55%, var(--accent-subtle) 0%, transparent 70%);
}
/* Grid texture */
.slide::after {
  content: ''; position: absolute; inset: 0;
  z-index: 1; pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 60px 60px;
}
```

## Components

### Badge

```html
<span class="badge">LABEL TEXT</span>
```
```css
.badge {
  display: inline-block; background: var(--accent); color: #fff;
  font-family: var(--font-mono); font-size: 0.75rem; font-weight: 700;
  padding: 0.35rem 0.9rem; border-radius: 100px;
  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1.5rem;
}
```

### Cards (3-column)

```html
<div class="cards">
  <div class="card">
    <div class="card-icon">EMOJI</div>
    <div class="card-title">Title</div>
    <div class="card-text">Description text</div>
  </div>
  <!-- repeat -->
</div>
```
```css
.cards {
  display: flex; gap: clamp(0.8rem, 2vw, 1.5rem);
  margin-top: 2.5rem; justify-content: center; flex-wrap: wrap;
}
.card {
  background: var(--bg-card); border-radius: var(--radius);
  padding: clamp(1.5rem, 3vw, 2.2rem); flex: 1;
  min-width: 200px; max-width: 280px;
  border-top: 3px solid var(--accent);
  transition: transform 0.3s ease, box-shadow 0.3s ease; text-align: left;
}
.card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.4), 0 0 20px var(--accent-subtle);
}
.card-icon {
  width: 52px; height: 52px; border-radius: 12px;
  background: var(--accent-subtle); display: flex;
  align-items: center; justify-content: center;
  font-size: 1.6rem; margin-bottom: 1rem;
}
.card-title { font-weight: 800; font-size: clamp(1.1rem, 2vw, 1.4rem); margin-bottom: 0.5rem; }
.card-text { font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; }
```

### Stat Cards (big numbers)

```html
<div class="stat-cards">
  <div class="stat-card">
    <div class="sc-icon">EMOJI</div>
    <div class="sc-label">LABEL</div>
    <div class="sc-value">85.2%</div>
    <div class="sc-desc">Description</div>
  </div>
</div>
```
```css
.stat-cards { display: flex; gap: clamp(0.8rem, 2vw, 1.5rem); margin-top: 2rem; justify-content: center; flex-wrap: wrap; }
.stat-card {
  background: var(--bg-card); border-radius: var(--radius);
  padding: clamp(1.2rem, 2.5vw, 2rem); flex: 1;
  min-width: 200px; max-width: 260px; text-align: center;
  border-top: 3px solid var(--accent);
}
.stat-card .sc-value {
  font-family: var(--font-mono); font-weight: 700;
  font-size: clamp(2rem, 4vw, 3rem); color: var(--accent-bright); line-height: 1;
}
.stat-card .sc-label { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
.stat-card .sc-desc { font-size: 0.85rem; color: var(--text-muted); }
```

### Flow Diagram (A -> B -> C)

```html
<div class="flow">
  <div class="flow-node">
    <span class="icon">EMOJI</span>
    <span class="label">Label</span>
  </div>
  <span class="flow-arrow">→</span>
  <!-- repeat nodes and arrows -->
</div>
```
```css
.flow { display: flex; align-items: center; justify-content: center; gap: clamp(0.5rem, 2vw, 1.5rem); margin-top: 2.5rem; flex-wrap: wrap; }
.flow-node {
  background: var(--bg-card); border: 2px solid var(--bg-elevated);
  border-radius: var(--radius); padding: clamp(1rem, 2.5vw, 1.8rem) clamp(1.2rem, 3vw, 2.2rem);
  display: flex; flex-direction: column; align-items: center; gap: 0.6rem;
}
.flow-node .icon { font-size: 2.2rem; }
.flow-node .label { font-family: var(--font-mono); font-size: clamp(0.75rem, 1.4vw, 0.95rem); color: var(--text-secondary); font-weight: 700; }
.flow-arrow { font-size: 1.8rem; color: var(--accent); animation: pulse-arrow 2s ease-in-out infinite; }
@keyframes pulse-arrow { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
```

### Harness Diagram (two-box with connector)

```html
<div class="harness-diagram">
  <div class="harness-body">
    <div class="harness-body-title">EMOJI TITLE</div>
    <div class="harness-feature"><span class="hf-icon">EMOJI</span> Feature text</div>
    <!-- more features -->
  </div>
  <div class="harness-connector">→</div>
  <div class="brain-box">
    <span class="brain-emoji">EMOJI</span>
    <span class="brain-label">Label</span>
    <span class="brain-sub">Subtitle</span>
  </div>
</div>
```
```css
.harness-diagram { display: flex; align-items: stretch; justify-content: center; gap: 0; margin-top: 2.5rem; flex-wrap: wrap; }
.harness-body {
  background: var(--bg-card); border: 2px dashed var(--accent);
  border-radius: var(--radius); padding: clamp(1.2rem, 2.5vw, 2rem);
  display: flex; flex-direction: column; gap: 0.8rem;
  box-shadow: 0 0 25px var(--accent-subtle); max-width: 340px;
}
.harness-body-title { font-family: var(--font-mono); font-size: 0.85rem; color: var(--accent-bright); font-weight: 700; text-transform: uppercase; }
.harness-feature { display: flex; align-items: center; gap: 0.7rem; padding: 0.5rem 0.7rem; background: var(--bg-elevated); border-radius: var(--radius-sm); font-size: clamp(0.8rem, 1.4vw, 0.95rem); color: var(--text-secondary); }
.harness-connector { display: flex; align-items: center; justify-content: center; padding: 0 clamp(0.5rem, 1.5vw, 1.2rem); font-size: 1.5rem; color: var(--accent); }
.brain-box {
  background: var(--bg-card); border: 2px solid var(--accent);
  border-radius: var(--radius); padding: clamp(1.5rem, 3vw, 2.5rem);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.8rem;
  box-shadow: 0 0 30px var(--accent-glow); min-width: 160px;
}
.brain-box .brain-emoji { font-size: 3rem; }
.brain-box .brain-label { font-weight: 800; font-size: 1.3rem; color: var(--accent-bright); }
.brain-box .brain-sub { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted); }
```

### Hub Diagram (center with spokes)

```html
<div class="hub">
  <div class="hub-spokes">
    <div class="hub-spoke">
      <div class="platform-icon">EMOJI</div>
      <span class="spoke-label">Label</span>
    </div>
  </div>
  <div class="connector">←</div>
  <div class="hub-center">
    <img src="assets/logo.png" alt="Center">
  </div>
  <div class="connector">→</div>
  <div class="hub-spokes">
    <!-- right spokes -->
  </div>
</div>
```
```css
.hub { display: flex; align-items: center; justify-content: center; gap: clamp(1rem, 3vw, 2.5rem); margin-top: 2.5rem; flex-wrap: wrap; }
.hub-center {
  width: clamp(100px, 16vw, 150px); height: clamp(100px, 16vw, 150px);
  border: 2px dashed var(--accent); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 30px var(--accent-subtle);
}
.hub-center img { width: 60%; }
.hub-spokes { display: flex; flex-direction: column; gap: 1.5rem; }
.hub-spoke { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }
.platform-icon { width: 56px; height: 56px; border-radius: 14px; background: var(--bg-card); border: 2px solid var(--bg-elevated); display: flex; align-items: center; justify-content: center; font-size: 1.8rem; }
.spoke-label { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted); }
.connector { color: var(--accent); font-size: 1.5rem; }
```

### Price Cards

```html
<div class="price-cards">
  <div class="price-card tier-premium">
    <div class="pc-emoji">EMOJI</div>
    <div class="pc-name">Name</div>
    <div class="pc-provider">Provider</div>
    <div class="pc-price-row">
      <span class="pc-price-label">Input</span>
      <span class="pc-price-value">$5 / M</span>
    </div>
    <div class="pc-price-row">
      <span class="pc-price-label">Output</span>
      <span class="pc-price-value">$25 / M</span>
    </div>
    <div class="savings-badge">SAVINGS TEXT</div>
  </div>
</div>
```
Tiers: `.tier-premium` (accent border), `.tier-mid` (blue border), `.tier-budget` (green border).

### Tip Box

```html
<div class="tip-box">
  <div class="tip-label">EMOJI LABEL</div>
  <div class="tip-text">Tip content with <strong>emphasis</strong>.</div>
</div>
```
```css
.tip-box {
  background: var(--bg-card); border: 1px solid var(--bg-elevated);
  border-left: 3px solid var(--accent); border-radius: var(--radius-sm);
  padding: 1rem 1.5rem; margin-top: 1.5rem; text-align: left;
  max-width: 700px; margin-left: auto; margin-right: auto;
}
.tip-box .tip-label { font-family: var(--font-mono); font-size: 0.75rem; color: var(--accent-bright); font-weight: 700; text-transform: uppercase; }
.tip-box .tip-text { font-size: 1rem; color: var(--text-secondary); line-height: 1.5; }
```

### Code Block

```html
<div class="code-block"><code><span class="comment"># Comment</span>
<span class="cmd">command</span> <span class="flag">--flag</span> <span class="val">value</span></code></div>
```
```css
.code-block {
  background: var(--bg-void); border-left: 3px solid var(--accent);
  border-radius: var(--radius-sm); padding: 1rem 1.2rem; overflow-x: auto;
}
.code-block code { font-family: var(--font-mono); font-size: clamp(0.7rem, 1.2vw, 0.85rem); color: var(--text-secondary); line-height: 1.7; white-space: pre; }
.code-block .cmd { color: var(--accent-bright); }
.code-block .flag { color: var(--blue); }
.code-block .val { color: var(--green); }
.code-block .comment { color: var(--text-muted); }
```

### Big Question (transition slide)

```html
<div class="big-question">?</div>
```
```css
.big-question {
  font-size: clamp(6rem, 15vw, 12rem); font-weight: 800;
  color: var(--accent); line-height: 1;
  text-shadow: 0 0 60px var(--accent-glow), 0 0 120px var(--accent-glow);
  animation: pulse-q 3s ease-in-out infinite;
}
@keyframes pulse-q {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.05); }
}
```

### VS Row

```html
<div class="vs-row">
  <div class="vs-block">
    <div class="vs-icon">EMOJI</div>
    <div class="vs-label">Label</div>
  </div>
  <div class="vs-divider">vs</div>
  <div class="vs-block">
    <div class="vs-icon">EMOJI</div>
    <div class="vs-label">Label</div>
  </div>
</div>
```

### Rank Blocks

```html
<div class="rank-row">
  <div class="rank-block">
    <div class="rank-number primary">#3</div>
    <div class="rank-label">Model Name</div>
    <div class="rank-sub">Subtitle</div>
  </div>
</div>
```

### Conclusion Points

```html
<div class="conclusion-points">
  <div class="conclusion-point">
    <span class="cp-icon">EMOJI</span>
    <span class="cp-text">Point with <strong>emphasis</strong></span>
  </div>
</div>
```

### Benchmark Image

```html
<img src="assets/chart.png" alt="Description" class="benchmark-img">
```
```css
.benchmark-img {
  width: min(90%, 800px); border-radius: var(--radius);
  border: 1px solid var(--bg-elevated);
  box-shadow: 0 0 40px var(--accent-glow);
}
```

### Logo (floating)

```css
.logo {
  width: clamp(100px, 18vw, 180px);
  filter: drop-shadow(0 0 30px var(--accent-glow)) drop-shadow(0 0 60px var(--accent-glow));
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}
```

## Navigation System

### Dots & Counter

```html
<div class="nav-dots" id="dots">
  <button class="dot active" onclick="goTo(0)"></button>
  <button class="dot" onclick="goTo(1)"></button>
  <!-- one per slide -->
</div>
<div class="slide-counter" id="counter">1 / N</div>
```
```css
.nav-dots { position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); display: flex; gap: 10px; z-index: 100; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--text-muted); cursor: pointer; transition: all 0.3s ease; border: none; padding: 0; }
.dot.active { background: var(--accent); box-shadow: 0 0 10px var(--accent-glow); transform: scale(1.3); }
.slide-counter { position: fixed; bottom: 30px; right: 30px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted); z-index: 100; }
```

### Click Zones

```css
.click-zone { position: fixed; top: 0; width: 15%; height: 100%; z-index: 50; cursor: pointer; }
.click-zone.left { left: 0; }
.click-zone.right { right: 0; }
.click-zone:hover { background: rgba(255,255,255,0.02); }
```

### JavaScript

```javascript
const deck = document.getElementById('deck');
const dots = document.querySelectorAll('.dot');
const slides = document.querySelectorAll('.slide');
const progress = document.getElementById('progress');
const counter = document.getElementById('counter');
const total = N; // MATCH SLIDE COUNT
let current = 0;

function goTo(n) {
  current = Math.max(0, Math.min(total - 1, n));
  deck.style.transform = `translateX(-${current * 100}vw)`;
  dots.forEach((d, i) => d.classList.toggle('active', i === current));
  slides.forEach((s, i) => s.classList.toggle('active', i === current));
  progress.style.width = `${((current + 1) / total) * 100}%`;
  counter.textContent = `${current + 1} / ${total}`;
}

function navigate(dir) { goTo(current + dir); }

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); navigate(1); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); navigate(-1); }
});

let touchX = 0;
document.addEventListener('touchstart', e => { touchX = e.touches[0].clientX; });
document.addEventListener('touchend', e => {
  const delta = e.changedTouches[0].clientX - touchX;
  if (Math.abs(delta) > 50) navigate(delta < 0 ? 1 : -1);
});

goTo(0);
```

## Responsive & Print

```css
@media (max-width: 600px) {
  .flow { flex-direction: column; }
  .flow-arrow { transform: rotate(90deg); }
  .hub { flex-direction: column; }
  .cards, .stat-cards, .price-cards, .model-cards { flex-direction: column; align-items: center; }
  .card, .stat-card, .price-card, .model-card { max-width: 100%; }
  .harness-diagram { flex-direction: column; align-items: center; }
  .harness-connector { transform: rotate(90deg); padding: 0.5rem 0; }
  .rank-row, .vs-row { flex-direction: column; }
}

@media print {
  .deck { width: auto; transform: none !important; flex-direction: column; }
  .slide { height: auto; min-height: 100vh; page-break-after: always; }
  .nav-dots, .slide-counter, .click-zone, .progress { display: none; }
  .slide .animate-in { opacity: 1 !important; transform: none !important; }
}
```
