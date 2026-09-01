# Short Form Content

Workspace for producing short-form social content (Instagram reels, shorts, carousels).

## Project skills

Two project-specific skills live in `.claude/skills/`:

### 1. `reel-editor` — talking-head clip → finished vertical reel
Turns ONE raw talking-head clip (vertical or landscape 4K) into a styled 9:16 reel: speaker in the bottom half, animated motion-graphics cards in the top half, karaoke one-word captions, background music. Default look is the green-glass "Ambra" style, but the accent color is themeable to match a reference reel.

- **Trigger it with**: "edit this reel", "make a reel/short from this video", "make a short like this <reel link>", or just handing over a talking-head .mov/.mp4.
- **Full pipeline lives in** `.claude/skills/reel-editor/SKILL.md` — follow it step by step (transcribe → hand-built EDL → cut → silence trim → re-transcribe → cards → captions → compose → self-evaluate).
- **Path note**: the SKILL.md's commands say the skill lives at `~/.claude/skills/reel-editor`; in this project `<skill>` = `.claude/skills/reel-editor` (project-relative). Use that path in every command.
- **Requirements**: `ffmpeg`, Node.js (for `npx hyperframes`), Python 3 with PIL. Transcription uses ElevenLabs Scribe (`ELEVENLABS_API_KEY`) or falls back to free local Whisper via `scripts/transcribe_local.py`. See `SETUP.md` in the skill folder.
- **Work layout**: one folder per reel (e.g. `reels/<name>/` inside this project) containing `edit/`, `cards/`, `renders/`.
- NOT for posting/publishing and NOT for long-form YouTube.

### 2. `ig-carousel` — premium Instagram carousels
Generates a cinematic cover + content slides that share one visual world, via the Higgsfield MCP (Nano Banana Pro) — no external API keys.

- **Trigger it with**: "ig carousel", "make a carousel", "carousel post", "repurpose this into a carousel".
- **Two styles — pick ONE at the start, never mix**:
  - `daylight`: bright photoreal world, voxel mascot, editorial serif — for educational/list/announcement posts.
  - `hacker-desk`: dark desk, pixel-art mascot, bold condensed sans, code blocks — for prompts, dev tutorials, technical content.
- Style specs live in `.claude/skills/ig-carousel/references/style-daylight.md` and `style-hacker-desk.md`.
- **Requirements**: Higgsfield MCP connected (it is in this environment).

## Conventions

- Keep all generated media inside this project (per-reel folders, `carousels/<name>/`), not in Downloads or /tmp.
- Both skills include self-evaluation steps — always run them before presenting output.
- `reel-editor` has a mandatory retro step: after finishing a reel, update its SKILL.md with lessons learned.
