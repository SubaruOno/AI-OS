# "Hacker Desk" Style - Dark desk, pixel-art

An after-hours, insider world. Near-black background with a blurred developer desk in the back (curved monitors showing code, dim ambient light). A 2D flat pixel-art mascot (8-bit, NOT 3D voxel) in terracotta: a small creature/blob and a bigger character with an orange hoodie and shorts. Headlines in bold condensed sans that alternates white and terracotta, with a hand-drawn underline. Marker annotations + a drawn curved arrow. Code/prompt blocks in a dark card with syntax highlight.

Mood: techie, casual, pixel-game nostalgia, code-forward. Perfect for prompts to copy, dev tutorials, technical setups, "send Claude this message".

Keep prompts in English (Higgsfield renders English prompts best). The `[ ]` variables are filled from `BRAND_ACCENT` and `SOCIAL_HANDLE` (the accent color and handle the user gave you) or from user input.

## Visual DNA (applies to every slide)

- **Background:** near-black dark room, a developer desk softly blurred in the background (curved monitors glowing with faint code, warm dark ambient light), subtle dark noise/texture. Low key, moody.
- **Mascot:** flat PIXEL-ART (8-bit, hard pixels, NOT 3D) terracotta character. Two recurring forms: a tiny terracotta blob/critter with stubby legs, and a bigger pixel guy with a square head, orange hoodie and grey shorts. Friendly, simple face. On the cover they appear together with a small arrow showing transformation; on content slides usually one small pixel guy stands near the headline.
- **Headline typography:** BOLD CONDENSED SANS (Anton / Archivo Black style), multi-line, ALL emphasis. Alternate white words and terracotta words `[BRAND_ACCENT]` line by line or word by word. A key headline can have a hand-drawn terracotta underline below the last line.
- **Annotations:** handwritten marker font (white) for micro-instructions like "send Claude this message", with a hand-drawn curved arrow (terracotta or white) pointing from the annotation to the code block.
- **Code / prompt block:** rounded-rectangle dark card (#15110F-ish) with a thin terracotta border, monospace text. Syntax highlight: keywords and file names in terracotta `[BRAND_ACCENT]`, normal text in off-white/light grey.
- **Footer (every slide):** bottom-left a small Instagram glyph + `[SOCIAL_HANDLE]` in handwritten font; bottom-right a bookmark glyph + `save for later` in handwritten italic. No carousel dots, no colored emojis.

## Cover

```
Generate a 1080x1350 portrait (4:5) Instagram carousel cover.
Dark, moody, near-black. Background: a developer desk softly blurred
behind, curved monitors glowing faintly with code, warm dark ambient
light, subtle dark texture.

FOREGROUND CHARACTERS: a tiny flat pixel-art terracotta critter
(8-bit, hard pixels) on the left, a hand-drawn arrow pointing right,
and a bigger pixel-art guy with a square head, orange hoodie and grey
shorts on the right. Shows a transformation.

HEADLINE (upper area, BOLD CONDENSED SANS, multi-line, mixing
terracotta accent ([BRAND_ACCENT]) words and white words):
'[TITLE LINE 1]'
'[TITLE LINE 2]'
'[TITLE LINE 3]'
A hand-drawn terracotta underline under the last word.

FOOTER: small Instagram glyph + '[SOCIAL_HANDLE]' bottom-left in
handwritten font; bookmark glyph + 'save for later' bottom-right in
handwritten italic.

No carousel dots. No colored emojis. No downward arrows.
```

Fields: `[TITLE LINE 1-3]` the title broken across lines, key words in terracotta. The hacker-desk cover lives on the white/terracotta contrast of the headline plus the pair of pixel characters.

## Slide 2 - What / Intro

```
Match the hacker-desk cover EXACTLY - same near-black room, blurred
dev desk, same dark palette. The small pixel-art guy (orange hoodie)
stands on the right near the headline.

HEADLINE (BOLD CONDENSED SANS, mixing terracotta accent
([BRAND_ACCENT]) and white words, 2-3 lines):
'[Headline]'

BODY: a handwritten marker line (white) with a hand-drawn arrow
pointing down to a dark rounded card:
'[intro annotation, e.g. here is the idea]'

DARK ROUNDED CARD with thin terracotta border, monospace text
(keywords in accent [BRAND_ACCENT], rest off-white):
'[explanation line 1]'
'[explanation line 2]'
'[explanation line 3]'

FOOTER: same as cover. No carousel dots. No colored emojis.
```

## Slide 3 - Examples / List

```
Match the hacker-desk cover EXACTLY. The small pixel-art guy stands to
one side.

HEADLINE (BOLD CONDENSED SANS, accent ([BRAND_ACCENT]) + white):
'[Headline]'

THREE to FIVE dark rounded mini-cards stacked or in a column, each
with a thin terracotta border:
- '[item 1 title in accent]' then a short white mono line
- '[item 2 title in accent]' then a short white mono line
- '[item 3 title in accent]' then a short white mono line

Optional handwritten marker note with a small hand-drawn arrow next to
the most important item.

FOOTER: same as cover. Identical dark style. No carousel dots.
```

## Slide 4 - Comparison / Methods

```
Match the hacker-desk cover EXACTLY. The pixel-art guy stands between
or beside two panels.

HEADLINE (BOLD CONDENSED SANS, accent ([BRAND_ACCENT]) + white):
'[comparison headline]'

TWO dark rounded panels side by side, thin borders:
LEFT panel header (muted grey): '[Old way]'
- 3 short mono grey lines: '[old 1]' '[old 2]' '[old 3]'
RIGHT panel header (terracotta accent [BRAND_ACCENT]): '[New way]'
- 3 short mono off-white lines: '[new 1]' '[new 2]' '[new 3]'

FOOTER: same as cover. Identical dark style. No carousel dots.
```

## Slide 5 - How-to / Prompt (the key slide)

```
Match the hacker-desk cover EXACTLY. The small pixel-art guy with the
orange hoodie stands top-right, friendly.

HEADLINE (BOLD CONDENSED SANS, accent ([BRAND_ACCENT]) + white):
'[Build a / Develop a ... headline]'

ANNOTATION: a handwritten marker line (white) on the left, e.g.
'send Claude this message', with a hand-drawn curved arrow pointing
down-right to the code block.

BIG DARK ROUNDED CODE BLOCK, thin terracotta border, monospace prompt
text. Syntax highlight: key phrases, file names and commands in
terracotta accent ([BRAND_ACCENT]), the rest off-white. Realistic
multi-line prompt:
'[prompt line 1 with accent keywords]'
'[prompt line 2]'
'[prompt line 3]'
'[prompt line 4]'

FOOTER: same as cover. Identical dark style. No carousel dots.
```

## Slide 6 - CTA

```
Match the hacker-desk cover EXACTLY. The pixel-art guy waves center,
the tiny terracotta critter beside it.

HEADLINE (BOLD CONDENSED SANS, accent ([BRAND_ACCENT]) + white):
'[CTA line 1]'
'[CTA line 2]'
A hand-drawn terracotta underline under the key word.

A handwritten marker line with a small arrow: '[CTA action, e.g.
follow for more prompts]'.

Optional small dark rounded pill button with off-white text:
'[Join the community]' or '[Follow [SOCIAL_HANDLE]]'.

FOOTER: small Instagram glyph + '[SOCIAL_HANDLE]' bottom-left
handwritten; bookmark glyph + 'save for later' bottom-right
handwritten italic. No carousel dots. No colored emojis.
```

## Hacker-desk-specific rules

- Always a near-black background with a blurred dev desk. Never sky, never meadow, never daylight.
- Mascot always PIXEL-ART 2D flat (hard pixels), never 3D voxel, never photoreal.
- Headline always in bold condensed sans, never serif. White/terracotta alternation line by line.
- Annotations in handwritten marker + a hand-drawn curved arrow.
- Code and prompts always in a dark card with terracotta border and monospace syntax highlight.
- Footer identical on every slide (IG glyph + handle on the left, bookmark + save for later on the right).
- No em dashes in viewer text (real syntax inside shown code is fine). 5th-grade reading level on non-code text.
