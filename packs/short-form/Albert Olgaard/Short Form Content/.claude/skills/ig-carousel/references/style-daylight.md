# "Daylight" Style - Bright photoreal daytime world

A bright, warm world. Photoreal blue sky with soft clouds, a slightly blurred green meadow along the bottom. A terracotta 3D voxel mascot (Minecraft style, blocky, cute) lives in the scene. Wooden signs and pinned ivory paper cards hold the text. Headlines in editorial serif that alternates roman and italic, with accent words in terracotta. A pill at the top, an italic footer at the bottom.

Mood: educational, accessible, premium but playful. Perfect for resource lists, announcements, "save this post".

Keep prompts in English (Higgsfield renders English prompts best). The `[ ]` variables are filled from `BRAND_ACCENT` and `SOCIAL_HANDLE` (the accent color and handle the user gave you) or from user input.

## Visual DNA (applies to every slide)

- **Background:** photorealistic bright blue sky, soft white cumulus clouds, a green grassy meadow along the bottom with shallow depth of field (bokeh). Soft natural daylight, gentle sun.
- **Mascot:** a cute terracotta/orange VOXEL robot character (Minecraft-style blocky 3D), matte clay texture, simple dot eyes and smile, sometimes tiny crown or pixel sunglasses. It interacts with the scene (holds a sign, stands by a signpost, pushes keycap blocks, raises a card overhead). Never photoreal-human.
- **Text furniture:** wooden signposts and signboards (warm oak planks with bolts), plus cream/ivory paper cards and torn note papers, each pinned with a small pin and slightly rotated, casting a soft drop shadow. Headline on sky or on a card; body always on a card/sign.
- **Typography:** editorial serif (Playfair Display style). Headline mixes roman bold and italic. Emphasis words and big numbers in accent color `[BRAND_ACCENT]`, the rest in dark charcoal `#2B2622`. Body in a clean dark serif/sans on paper.
- **Accent glyph:** a small terracotta sunburst/asterisk (Claude spark, 10+ tapered rays) used as decoration, not a big logo.
- **Bullet:** small filled terracotta squares.
- **Pill label (top):** rounded ivory/white pill with a thin border, dark text in spaced small caps (e.g. ALL FREE, START HERE, PICK ANY METHOD, FREE GUIDE).
- **Footer (every slide):** `[SOCIAL_HANDLE]` bottom-left in serif italic; bottom-right a micro-call in serif italic (`swipe`, `save for later`, `save this post`). No carousel dots, no emojis, no downward arrows.

## Cover

```
Generate a 1080x1350 portrait (4:5) Instagram carousel cover.
Photorealistic, bright daylight, blue sky with soft white cumulus
clouds, a green grassy meadow along the bottom with shallow depth of
field. Cinematic but cheerful, premium.

SCENE: A cute terracotta voxel robot (Minecraft-style blocky 3D,
matte clay, dot eyes, small smile, tiny crown) [scene action, e.g.
standing proudly on a hill of terracotta keycap blocks, arms raised].
Small floating keycap cubes drift around. A tiny terracotta sunburst
glyph in the top corner.

TEXT OVERLAY (upper two thirds, on the sky):
- '[TITLE LINE 1]' in massive serif, with the key word/number in
  accent color ([BRAND_ACCENT]); the rest in dark charcoal. Mix bold
  roman and italic.
- '[TITLE LINE 2]' just below, smaller serif, italic for emphasis.

PILL LABEL (small rounded ivory pill near the title): '[LABEL]' in
spaced uppercase dark text.

FOOTER: '[SOCIAL_HANDLE]' bottom-left in dark serif italic, '[swipe]'
bottom-right in dark serif italic.

No carousel dots. No emojis. No downward arrows.
```

Fields: `[TITLE LINE 1/2]` the title (number or key word in accent), `[LABEL]` the pill (ALL FREE, START HERE...), `[scene action]` what the mascot does. The cover title must not promise a number the carousel does not deliver.

## Slide 2 - What / Start here

```
Match the daylight cover EXACTLY - same blue sky, clouds, grassy
meadow, soft daylight, same palette. A large wooden signpost stands
in the grass; pinned to it is a big cream paper card, slightly tilted,
soft drop shadow. The terracotta voxel robot stands at the base of
the post waving, holding a small glowing cube.

SMALL PILL above the card: '[LABEL e.g. START HERE]'.

ON THE CARD:
- Tiny eyebrow line, spaced uppercase dark: '[KICKER e.g. REPO 01]'
- Headline in editorial serif, accent word in italic accent color
  ([BRAND_ACCENT]): '[Headline 2-4 words]'
- One plain sentence dark serif: '[one-line explanation]'
- 3 bullet lines, each with a small terracotta square bullet:
  '[point 1]'
  '[point 2]'
  '[point 3]'
- A small mono/dark URL or label line at the bottom: '[url or note]'

FOOTER: same as cover. No carousel dots. No emojis.
```

## Slide 3 - Examples / List (3-5 items)

```
Match the daylight cover EXACTLY. Three (or up to five) wooden
signposts stand in a row in the grass, each with a cream paper card
pinned to it, slightly different tilt, soft shadows. A small terracotta
voxel robot stands beside each post (different poses).

SMALL PILL at top: '[LABEL e.g. PICK ANY METHOD]'.

HEADLINE above the cards, big serif, second part italic accent color
([BRAND_ACCENT]):
'[Headline line 1]'
'[Headline line 2 italic accent]'

EACH CARD (left to right):
- eyebrow uppercase dark: '[METHOD/ITEM 0X]'
- bold serif title: '[item title]'
- 1-2 small dark lines: '[short description]'

FOOTER: same as cover. Identical daylight photoreal style. No dots.
```

## Slide 4 - Comparison (old vs new)

```
Match the daylight cover EXACTLY. Two wooden signboards stand side by
side in the grass, each with a cream paper card. The terracotta voxel
robot points from the left board toward the right one.

HEADLINE above, big serif with key word italic accent color
([BRAND_ACCENT]): '[sharp comparison line]'

LEFT CARD (muted, slightly faded):
- header in muted gray serif: '[Old way]'
- 3-4 faded gray bullet lines (small gray squares):
  '[old downside 1]'
  '[old downside 2]'
  '[old downside 3]'

RIGHT CARD (crisp, warm):
- header in accent color serif ([BRAND_ACCENT]): '[New way]'
- 3-4 dark bullet lines (small terracotta squares):
  '[new benefit 1]'
  '[new benefit 2]'
  '[new benefit 3]'

FOOTER: same as cover. Identical daylight photoreal style. No dots.
```

## Slide 5 - How-to / Prompt

```
Match the daylight cover EXACTLY. A single large cream index card is
pinned to a wooden signpost with a pin, slightly tilted, soft drop
shadow. The terracotta voxel robot leans on the post.

HEADLINE above the card, serif, accent word italic ([BRAND_ACCENT]):
'[how-to title]'

ON THE CARD (dark clean text, key phrase highlighted in accent color
[BRAND_ACCENT]):
'[step / prompt line 1]'
'[step / prompt line 2]'
'[step / prompt line 3]'
'[step / prompt line 4]'

Small line below the card, dark serif italic: '[result line]'

FOOTER: same as cover. Identical daylight photoreal style. No dots.
```

## Slide 6 - CTA

```
Match the daylight cover EXACTLY. The terracotta voxel robot stands
center in the meadow holding a big cream signboard overhead with both
arms. A small terracotta sunburst glyph floats above. A little pile
of terracotta cubes at its feet.

SMALL PILL at top: 'FREE GUIDE' (or relevant CTA label).

ON THE BOARD, big serif, second word italic accent color
([BRAND_ACCENT]):
'[CTA line 1 e.g. Comment]'
'[CTA line 2 accent e.g. SKILLS]'
'[supporting line, plain dark serif e.g. and I will DM you the list]'

Small dark line under: '[mini detail e.g. all 5 repos]'

FOOTER: '[SOCIAL_HANDLE]' bottom-left serif italic; 'save this post'
bottom-right serif italic. Optionally a center line 'also follow
[SOCIAL_HANDLE] for more'. No carousel dots. No emojis.
```

## Daylight-specific rules

- Always sky + clouds + meadow, always warm daylight. Never dark, never neon.
- The terracotta voxel mascot appears in (almost) every slide, always consistent: same blocky shape, same color.
- Text always on paper cards or wooden signs, never painted on the grass or sky (except the big cover headline, which can sit on the sky).
- Headline in editorial serif, roman + italic. Accent only on key words and numbers.
- Footer identical on every slide. Pill only where a label is needed.
- No em dashes. 5th-grade reading level.
