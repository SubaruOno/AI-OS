---
name: ig-carousel
description: Generate premium Instagram carousels with a cinematic cover plus content slides that all share one visual world. Supports TWO selectable styles - "daylight" (photoreal daytime world, voxel mascot, editorial serif) and "hacker-desk" (dark desk, pixel-art mascot, bold sans, code blocks). Use this skill when the user says "ig carousel", "instagram carousel", "make a carousel", "carousel post", "repurpose into a carousel", or wants slide-based social content. Runs in Claude Code using the Higgsfield MCP (Nano Banana Pro), no external API keys.
---

# IG Carousel (Higgsfield Edition) - Two Styles

Cinematic, cover-first carousels. Every slide lives in the same visual world. Built on Higgsfield Nano Banana Pro through the Higgsfield MCP, so it runs natively in Claude Code with no external API setup.

This skill knows **two distinct styles**. They are opposite visual worlds: never mix them inside one carousel. You pick a style at the start of the run and all 6 slides respect it.

| Style | Mood | When | Mascot | Headline font | Background |
|---|---|---|---|---|---|
| **daylight** | bright, warm, premium-playful | educational, lists, announcements, "save this" | terracotta 3D voxel (Minecraft style) | editorial serif, roman + italic | blue sky + clouds + meadow |
| **hacker-desk** | dark, techie, code-forward | prompts, dev tutorials, technical setups, "send Claude this message" | 2D flat pixel-art with orange hoodie | bold condensed sans (Anton/Archivo) | near-black + blurred desk/monitors |

## Prerequisites

- The **Higgsfield MCP** connected to Claude Code (provides `generate_image`, `job_status`, etc.).
- Around **6-12 Higgsfield credits** per carousel (1 cover + 5 referenced slides).
- A topic. Free text, a YouTube transcript, or a video to repurpose.

On the first run, if you do not already know them, ask the user once for:
- **accent color** hex (default terracotta `#C2724F`)
- **social handle** for the footer (e.g. `@username`)

Keep both for the rest of the session.

## What this skill does (in one sentence)

1. Picks the style (daylight or hacker-desk)
2. Generates the cover with `generate_image` (model `nano_banana_2`)
3. Uses the cover as the style reference for every following slide
4. Saves all slides to `outputs/carousels/<slug>/` and writes the caption

At the end the user has a 6-slide deck (1 cover, 4 content, 1 CTA) plus an Instagram caption ready to paste, with the 6 PNGs already downloaded to disk.

## Process

### Step 0: Pick the style

This is the first step, before anything else.

**Auto-select (default):** infer the style from the topic.
- Educational topics, resource lists, product announcements, "save this", soft comparisons, warm and accessible mood → **daylight**
- Technical topics, prompts to copy, dev tutorials, system setups, code, "send this message to Claude", insider mood → **hacker-desk**

**Override:** if the user names a style ("daylight style", "make it dark", "pixel style", "like the sky", "desk style"), use that and do not ask.

If the topic is ambiguous and the user gave no hint, ask once which of the two styles they want (show the short table above), then proceed.

Once the style is chosen, open the matching reference file and follow it for EVERY prompt:
- daylight → `references/style-daylight.md`
- hacker-desk → `references/style-hacker-desk.md`

Each reference file holds the full style spec plus the prompt templates for the cover and all 6 slides. Never mix elements between the two files.

### Step 1: Accent color and handle

Before generating, make sure you have:
- `BRAND_ACCENT` - accent color hex (default terracotta `#C2724F`)
- `SOCIAL_HANDLE` - the @ for the footer (e.g. `@username`)

If you do not have them yet, ask the user for these two values before going further. Note on accent: both style references use a terracotta/rust family. If `BRAND_ACCENT` is very different (e.g. green), use it anyway but apply it consistently across all 6 slides.

### Step 2: Plan the slides

Always 6 slides, always in this logical order (the visual treatment of each "role" changes per style, see the reference file):

1. **Cover** - maximum visual hook, big title, ends on curiosity
2. **What / Start here** - introduces the main concept
3. **Examples / List** - 3-5 items side by side
4. **Comparison / Methods** - old vs new, or several options compared
5. **How-to / Prompt** - the step-by-step or the prompt to copy
6. **CTA** - follow handle + call to action (comment / save / community)

NO context slide. NO transition slide. NO filler. The cover IS the hook. Every other slide delivers value.

### Step 3: Generate the cover

Call the Higgsfield `generate_image` tool with:
- `model`: `nano_banana_2`
- `aspect_ratio`: `4:5`
- `resolution`: `2k`
- `prompt`: the cover template from the chosen style reference, with TITLE, hook, accent, and handle filled in.

Save the returned `job_id`. You will reuse it as the style reference for slides 2-6.

### Step 4: Generate slides 2-6

For each content slide, call `generate_image` again with:
- same `model`, `aspect_ratio`, `resolution`
- `medias`: `[{ "role": "image", "value": "<cover-job-id>" }]`
- `prompt`: always starts with the style match line (e.g. "Match the cover EXACTLY...") then describes the new element, using the slide template in the chosen style reference.

Launch all 5 in parallel (single message, multiple tool calls). They are independent and Higgsfield queues them simultaneously.

### Step 5: Wait, then collect the image URLs

After launching the 5 jobs, wait about 40 seconds. Then call `job_status` for each of the 6 `job_id`s. When a job is complete it returns the generated image URL. If `job_status` does not expose the URL in your setup, call `reveal_generation` or `show_generations` to retrieve it.

### Step 6: Download the PNGs + write the caption

Claude Code runs locally, so download the images directly (no Cowork sandbox limit). Create `outputs/carousels/<slug>/` and for each completed job run `curl` to save the PNG with these names:

```
01_cover.png  02_what.png  03_examples.png  04_comparison.png  05_how_to.png  06_cta.png
```

Then write `caption.txt`: hook + 2-3 value lines + CTA + 5 hashtags. If the `humanizer` skill is installed, pass the caption through it. Otherwise apply the inline caption rules below.

## Output structure

```
outputs/carousels/<slug>/
  ├── caption.txt
  ├── 01_cover.png
  ├── 02_what.png
  ├── 03_examples.png
  ├── 04_comparison.png
  ├── 05_how_to.png
  └── 06_cta.png
```

## Caption rules (inline humanizer fallback)

- Short sentences, 5th-grade reading level.
- No em dashes anywhere. Use commas, periods, or rephrase.
- No "in today's fast-paced world", no inflated promo words, no rule-of-three filler.
- First line is a hook, then 2-3 concrete value lines, then a CTA (comment / save / follow), then 5 specific hashtags.

## Rules

- ALWAYS Higgsfield Nano Banana Pro (`nano_banana_2`). Never Gemini direct, never Playwright/HTML.
- ALWAYS one style per carousel. Never mix daylight and hacker-desk in the same deck.
- ALWAYS cover first, then content slides reference the cover `job_id`.
- ALWAYS 4:5 portrait, 2k resolution.
- Accent color from `BRAND_ACCENT` (default terracotta `#C2724F`), used consistently across all 6 slides.
- `SOCIAL_HANDLE` footer on every slide. Strong community/CTA mention only on the CTA slide.
- 5th-grade reading level on viewer copy. Short sentences.
- NEVER em dashes anywhere (titles, subtitles, hooks, caption, chat). Use commas, periods, or rephrase.
- NEVER auto-post. Posting is out of scope for this skill.

## When NOT to use this skill

- The user wants a single static graphic - use another skill.
- The user wants a video slideshow for YouTube - use another skill.
- The user wants a real PowerPoint - use a slides tool.
