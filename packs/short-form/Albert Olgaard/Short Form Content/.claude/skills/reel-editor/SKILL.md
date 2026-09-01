---
name: reel-editor
description: Use when you want to edit/montage a raw talking-head clip (vertical OR landscape 4K) into a finished, styled vertical reel/short with animated motion-graphics schemas. Default look = green-glass "Ambra" style, but the accent color is THEMEABLE (e.g. orange to match a Claude reel) to replicate a reference reel. Triggers - "edit this reel", "make a reel/short from this video", "reel with the animations", "short with the green graphics", "make a short like this <reel link>", or when given a talking-head .mov/.mp4 to turn into a social reel. NOT for posting and NOT for long-form YouTube.
---

# Reel Editor (green-glass "Ambra" style)

Turn ONE raw vertical talking-head clip into a finished 9:16 reel: the speaker in the bottom half, animated green graphics/schemas in the top half, karaoke one-word subtitles, music. Style validated against reference reels (jesserurka, emilsystems on Instagram).

> All commands below assume the skill lives at `~/.claude/skills/reel-editor`. `<skill>` = that folder. Work inside one project folder per reel, e.g. `~/reels/<name>/`.

## Stack
- `scripts/transcribe.py` for TRANSCRIPTION (ElevenLabs Scribe, word-level timestamps). No API key? Use `scripts/transcribe_local.py` (free, local Whisper, same output shape). For the CUT use `scripts/cutjoin.py` (NOT a generic renderer: see ERRORS).
- `hyperframes` (via `npx hyperframes render`) to render the HTML/GSAP cards. `npx` fetches it on first use; needs Node.js.
- `ffmpeg` for composition + music. **Local ffmpeg usually has no libass** → subtitles are baked with PIL (captions.py), NOT with `subtitles=`.
- Caption font: Montserrat (bundled at `assets/fonts/Montserrat-VariableFont_wght.ttf`, weight 900). captions.py finds it automatically.
- Bundled assets: `assets/logos/` (whatsapp, claude, openai, github), `assets/bg-music.m4a` (default background track — swap it for your own with `MUSIC=/path/to/track.m4a`).

## Pipeline (run in order, inside one project folder, e.g. `~/reels/<name>/`)

0. **If you were given a reference reel (IG/TikTok link)**: study it FIRST (see "Replicate a reference reel"). Download, make a contact-sheet, sample the accent color → set the palette in gen.py.
1. **If the RAW is LANDSCAPE** (e.g. 4K 16:9): pre-crop to vertical 1080x1920 centered on the face, then work on `edit/raw9.mp4`:
   `ffmpeg -i <raw.MP4> -vf "crop=1215:2160:<x>:0,scale=1080:1920" -c:v libx264 -crf 18 -c:a aac edit/raw9.mp4`
   (1215 = 2160*9/16; tune `<x>` by extracting a frame and centering the face; for a 3840-wide source `x≈1293`).
2. **Transcribe the RAW**: `python <skill>/scripts/transcribe.py <raw> --edit-dir edit --language en --num-speakers 1`
   (use `--language it` etc. for other languages; or `scripts/transcribe_local.py` with the same args and no API key.)
3. **Read the transcript word-by-word** (`edit/transcripts/*.json`, print indices+times). Raw clips are often **multi-take with spoken director's notes** ("put a clip of…", "ok so…", "show the bit where…"). Those must NOT end up in the voiceover. **Hand-pick the CLEAN take of every sentence** and build an EDL of KEEP-ranges (the final narration), discarding repetitions, false starts, and director's notes.
4. **Write the EDL** by hand (list of `ranges` with start/end of the good takes) — see the format in `make_edl.py`. `make_edl.py` is fine ONLY for single-take raws; for multi-take, build the keep-list manually. **EXTEND each `end` by +0.2/0.4s** to include the word release + a breath (otherwise you clip it). If the transcriber collapses a multi-take zone into ONE very long "word" (e.g. a 4s blob), that's a red flag: inspect that window with `silencedetect`, SPLIT keeping the clean take and dropping the blob in the middle.
5. **Cut**: `python <skill>/scripts/cutjoin.py edit/edl.json edit/cut.mp4` (extract+concatenate, native resolution, no OOM).
6. **Trim residual silences** (CRITICAL): `python <skill>/scripts/silence_keep.py edit/cut.mp4 edit/edl_sil.json` (defaults: -40dB / MIN 0.35 / PAD 0.12, protects the last word; for a very punchy short add `... -40 0.30`) → `python <skill>/scripts/cutjoin.py edit/edl_sil.json edit/cutF.mp4`. **NEVER -30/-32dB**: it eats the soft word releases. Afterwards, CHECK the gaps in the re-transcribed cut: a `gap = start - prev_end` > 0.30s between two sentences = a pause to tighten.
7. **RE-TRANSCRIBE the final cut** (exact sync): `python <skill>/scripts/transcribe.py edit/cutF.mp4 --edit-dir edit/tF --language en --num-speakers 1`. Then **VERIFY no word is clipped**: the transcriber AUTO-COMPLETES cut words (it prints "output" even if the file only contains "out"). Signs of a clip: a word whose `end` exceeds the file duration, sentences that "jump", a vanishing last word. If you find one → extend that range's `end` in the EDL and re-cut. **Do NOT trust the transcript text alone.**
8. **Author the BEATS** in `cards/gen.py` (copy from `<skill>/scripts/gen.py`, or from one of the example generators in `references/examples/`) by reading `edit/tF/transcripts/cutF.json`. Each card has a `trigger` = the word/phrase it MUST appear on. Cards are **contiguous**. Timing rule: a beat lasts as long as its sentence; if you need a multi-stage sequence (logo→price→strike) anchor the stages to DIFFERENT words and finish BEFORE the beat's last word (otherwise the exit clips it).
9. **Project assets**: `mkdir -p cards/assets/logos && cp <skill>/assets/logos/* cards/assets/logos/`. Missing logos: find them on svgl, GitHub org avatars, or the brand CDN. For real screenshots (e.g. an A/B comparison of two pages) resize them into `cards/assets/` and show them inside a browser-frame.
10. **Generate + render cards**: `cd cards && python gen.py ../edit/tF/transcripts/cutF.json && npx --yes hyperframes render . -o cards_all.mp4`
11. **Patch transcriber errors + Subtitles**: the transcriber mangles names/terms ("Claude"→"Cloud", etc.); patch the JSON in `cutF_cap.json` (substitute on the "text" field) and generate: `python <skill>/scripts/captions.py edit/tF/transcripts/cutF_cap.json edit/capt 12 92` (last arg = font size; ~92 default, long words like AUTOMATICALLY at 100 fall off-frame). captions.py already has a **soft shadow** (readable over bright B-roll, no hard stroke). The card triggers stay on the ORIGINAL transcript.
12. **Compose + music**: `bash <skill>/scripts/compose.sh edit/cutF.mp4 cards/cards_all.mp4 edit/capt renders/<name>-FINAL.mp4 <crop_y>`. For a head-and-shoulders crop (already-vertical source) crop_y varies per clip (~120-300; c0886 needed 300). ALWAYS tune it on test frames (`scale=1080:-2,crop=1080:1056:0:$cy` at 3-4 values, contact-sheet them) so the face sits in the UPPER part of the lower band — "too far down" was real user feedback. compose puts the voice at dialog level (loudnorm) and music at 6% (`MUSIC_VOL=...` to change it, `MUSIC=...` to swap the track) and adds `+faststart`.
13. **Self-evaluate**: extract a frame (`ffmpeg -ss T -i ...`) of each schema, build a contact-sheet (PIL or `tile`) and COMPARE against the reference reels BEFORE showing it. Show only if it's decent. **Always also check**: first word (not clipped), last word + subtitle (not clipped), subtitles readable over every B-roll, beat-to-beat transitions with no flash, **A/V sync** (`ffprobe` video stream duration ~= audio, drift < 1 frame) and **subtitle == spoken word** (sample 3-4 points at mid/end: the caption must match the transcript, see the desync error).
14. **Retro + self-learning** (MANDATORY, see section below): when the reel is done, say what went well and what went badly, and update THIS skill with the lessons.

## Style (fixed, except the accent color)
- 9:16, talking-head in the bottom ~55% (overlay y=864), top band 0-864 black for the schemas.
- **ONE accent color per video** on black. Default **green #2fe081**. Themeable: for Claude/GLM content use **orange #f0813f** (bright #ffa766). Red/#ff5a5a for "no/lost/expensive", steel-grey #7f93ad for the "neutral competitor". The accent is set at the top of `gen.py` (tokens A/AB/AD/GL).
- Subtitles: Montserrat **Black**, white, UPPERCASE, **ONE word**, **no black outline**, at the edge with the video (CY=700 + overlay y=78). Font ~100px (parametric in captions.py).
- Decorative layer ALWAYS on: rising particles, streaks, a breathing glow, a scrolling grid → the top band is never empty/static.
- Big schemas that FILL the band (keyword ~112px, numbers ~200px, tall graphs).

## Replicate a reference reel (when you're given a link)
1. **Download**: `yt-dlp -o ref.%(ext)s "<reel url>"` (IG/TikTok ok).
2. **Study it closely**: contact-sheet at 2fps with ffmpeg `tile` (`ffmpeg -ss A -t 15 -i ref.mp4 -vf "fps=2,scale=216:384,tile=5x6:padding=4:color=black" sheetA.jpg`) and READ it. Extract: layout (where the talking-head sits, where the schemas go), the VOCABULARY of schemas used (terminal? grid? versus? count-up? command-bar?), the rhythm (how often the graphic changes), the subtitle style.
3. **Sample the accent**: extract a frame with a vivid color and read the bright pixels (PIL) → set A/AB in gen.py.
4. **Map** your beats onto the schemas observed in the reference. Do NOT copy the reference's text: use YOUR content.

## Schema vocabulary
Implemented in the `gen.py` template: intro-plane · stat+count-up · self-drawing line graph (down=red / up=green) · CRM contacts · checklist · calendar · step-by-step compare · iPhone reveal · WhatsApp dark chat + logo · template message ([name]/[place] highlighted) · vertical flow · CTA meter.

**Ready-made cards (copy-paste CODE in `references/card-snippets.md`)**: staged hook with logo · TERMINAL that types (typewriter) · per-word pill + result · numbered blocks 1-2-3-4 · before/after swap · skilltitle (badge+name+chip) · bigstat pop · colored-word CTA. **Complete working generator**: `references/examples/gen-reel1-skills.py` (all these cards + B-roll in `references/examples/compose-broll.sh`). Copy the card you need, don't rewrite it.

**Cards added in reel2 (in `references/examples/gen-reel2-claude.py`, ORANGE accent)**: **claudehero** (big logo + wordmark + sub, logo pops on its word) · **asciiwin** (mac window typing an ASCII WIREFRAME, e.g. a landing page: nav/hero/CTA/features/footer, typewriter via `textContent` on `<pre>`) · **staged terminal** (typed `/command` + lines appearing after: the model's questions, or scan + ⚠ vulnerability + ✓ done) · **mdfile** (markdown file viewer, `#`/`##`/`li`/`tx` lines revealed in stagger, filename tab + MD badge) · **githubcard** (big logo + top + chip, logo pops on the word) · **risinggraph** (exponential curve that draws itself + stamp) · **triple-pulse hooks** (giant word scale-punch + expanding ring on EACH repetition, for rhetorical triads "X, X, X") · **twopill** (two stacked pills entering on their word). For `<` `>` tags inside the typewriter use `json.dumps(string)` to embed the JS string safely.

**Wider palette to vary (don't limit yourself to the schemas above):** see `references/animation-library.md` — bar chart, gauge/donut, heatmap, star rating, code-diff, terminal, table, map+pin, odometer, carousel, timeline, toast, etc. `references/style.md` has the base catalog + the reference-reel URLs.

## User B-roll in the top band (over the face)
Sometimes you'll get clips (a screen-recording of a site, a report, a list) to show "over the face" while talking about them. They go in the top band (0-864), in their time window, ON TOP of the cards.
- **Map the windows** to the words (e.g. report on "report", site on "website", list on "skills"). Each window = `enable='between(t,A,B)'`.
- **Cover the card** underneath with a black-band for the whole B-roll window (`color=black:s=1080x864` overlay with `enable`), extended to the START of the next beat (so the card doesn't reappear at the edges).
- **Framing**: landscape/screen clip → full-bleed `scale=-2:864,crop=1080:864` (fills the band, no letterbox); portrait clip (a document) → `scale=-2:824` centered. Dark B-roll blends into the black; for bright ones rely on the subtitle shadow.
- **Clip timing**: `[N:v]trim=0:DUR,setpts=PTS-STARTPTS,fps=25,scale=...,setpts=PTS+A/TB[bv]` then `overlay` with enable in the window. Full example: `references/examples/compose-broll.sh`.

## ERRORS NOT TO REPEAT (learned the hard way)
| Error | Rule |
|--------|--------|
| Card = text inside a box | NO. Use **schemas/graphs/summary phrases**. The WORDS are carried by the subtitles; the cards carry the VISUAL. |
| Boxes that pulse on every word | NEVER per-word pop-scale on the cards. Movement = snappy entrances + continuous decorative layer + self-drawing graphs. |
| Sync computed on paper | It accumulates drift. **ALWAYS re-transcribe the final cut** and anchor cards+subtitles to the real word times. |
| Trimming only word-gaps | Leaves 0.6-1.1s silences. ALWAYS run `silence_keep.py` (silencedetect on the audio). |
| Graphics only at the top | Fill the whole top band + animated decorative layer. |
| Black outline on subtitles | Clean white only, no stroke. |
| Sparse cards (1 every 5s) | Cards **contiguous**, one always present, each on the word that triggers it. |
| "you-plural / everyone" subtitles | Use singular second person consistently (the creator's voice). |
| Showing half-baked versions | Self-evaluate on frames vs reference; come back only if it's decent. |
| **Keeping director's notes in the voiceover** | Raws are multi-take with spoken notes ("put a clip", "ok so"). Hand-pick the clean take of each sentence (keep-EDL), drop the rest. |
| **A generic renderer for the cut** | A renderer that resolves the source path relative to the EDL folder (→ `edit/edit/...`) and forces `scale=1920` will OOM on many segments. Use `cutjoin.py`. |
| **Music too loud** | Old default 0.15 covered the voice. compose now: voice loudnorm -16, music 0.06. Measure levels (`volumedetect`) if the voice was recorded low. |
| **File won't open (QuickTime/IG)** | Needs `+faststart` (moov atom up front). Already in compose.sh; if you remux by hand: `ffmpeg -i in.mp4 -c copy -movflags +faststart out.mp4`. |
| **Subtitles with transcriber typos** | Patch "Cloud"→"Claude" etc. in the CAPTION JSON before generating (card triggers stay on the original transcript). |
| **Multi-stage sequence in a short beat** | Logo→price→strike won't fit if the trigger is the last word. Anchor stages to different words and close before the beat exit. |
| **Clipping words (THE MOST EXPENSIVE)** | At -30dB the silence-trimmer eats soft tails → "output"→"out" etc., 3 rounds of fixes. Rule: silence_keep defaults (-40dB, last word protected) + extended EDL `end`s + **VERIFY the cut's AUDIO**, NOT the transcript alone (it auto-completes cut words). |
| **find() grabs the FIRST occurrence** | A word that occurs earlier (e.g. in the hook AND the next sentence) starts the beat on the wrong occurrence (animation too early). Use `find_after(trig, after)` to anchor to the right one. |
| **White subtitle on white B-roll** | A bright screen-recording (a site) + white subtitle = illegible. captions.py now has the soft shadow; also send bright B-roll full-bleed so the subtitle sits at the dark bottom edge. |
| **TextPlugin for the typewriter** | TextPlugin writes to innerHTML → eats tags like `<role>` (parses them as HTML). To type text with `<` `>` use a tween on a counter + `textContent=val.slice(0,n)`. |
| **Count-up in a tiny beat** | A count-up from 0 to 91,000 in 0.9s is unreadable: if the beat lasts <1.2s, POP the final number (scale-in), no counting. |
| **Card under the B-roll reappearing at the edges** | When a B-roll covers a card in its window, the faded card can flash 1-2 frames when the B-roll detaches. Cover with a black-band (`enable=between`) up to the start of the next beat, not just to the end of the B-roll. |
| **Dupes/false-starts hidden in one long word** | The RAW transcriber collapses repeated takes into ONE long word (a 2s "save" hiding a repeated phrase; an "I'll ma--" before "I'll make"). They only show up by re-transcribing the cut: after cutF, SCAN the transcript for consecutive duplicate phrases and micro-truncations (`ma--`, `us--`), then `silencedetect` the original window to find the split, divide the range dropping the dupe, re-cut. Dropping director's notes from the RAW isn't enough. |
| **A/V desync that grows mid/late clip** | Concat-COPY of AAC segments (old `cutjoin.py`: `concat -c copy`) accumulates encoder priming per segment → audio drifts from video, visible after ~40s (mouth not aligned, so subtitles aren't either). FIX: `cutjoin.py` now JOINS segments with the **concat FILTER** (`[0:v][0:a]...concat=n=N:v=1:a=1`), which re-decodes and concatenates decoded streams → sample-accurate sync. Runs on short segments, no OOM. Verify: `ffprobe` video stream duration ~= audio (drift < 1 frame). |
| **A logo SVG that was broken** | github.svg once had `viewBox 0 0 1024 1024` but path coords 0-16 → invisible. Verify ALL logos on a black background before rendering: no fill = black-on-black. A `currentColor` logo (e.g. openai.svg) loaded via `<img>` = BLACK: bake `fill="#fff"`. |
| **Inter-sentence pauses too long (short not punchy)** | Old `silence_keep.py` default (MIN 0.5, PAD 0.16) left 0.3-0.5s pauses → "too much pause" feedback. Default now MIN **0.35**, PAD_AFTER **0.12** (word tails still protected by -40dB + PAD_LAST 0.45). For a very punchy short pass `MIN 0.30`. After the cut CHECK the gaps in the transcript (`gap = start - prev_end`): if >0.30s between two sentences, tighten. |
| **Key visual entering on the LAST word** | The main element of a card anchored to the beat's last word leaves the card half-empty for 2-3s and "appears late". Anchor the key visual EARLY in the beat (one of the first words or `s+0.2`), not the last; keep it present for the whole beat. |
| **User image with window chrome "baked" in** | Screenshots of windows have the light window border INSIDE the PNG: on a black band it makes an ugly edge. Detect the frame via PIL (bbox of non-cream pixels) and CROP the inside; then on black add an **accent border** via CSS (`border:4px solid {A}`) to separate the dark logo from the black. |
| **Spoken triplets repeated identically** | If the RAW repeats the SAME sentence 3 times ("use hooks, use hooks, use hooks") you usually want to keep ONE in the cut (the cleanest/most emphatic take), not all three. Different from content rule-of-three (lists/numbers): keep those. When in doubt, one. |
| **A bare number stat = sterile** | A big static number ("1000+ HOURS") is flat. Make it a VISUAL: a curve/area that draws itself (svg path + gradient + glow) with the number popping at the peak. Applies to hours/percentages/counts. |
| **"Landscape" source that's actually vertical** | ffprobe can report 1920x1080 while a rotation side_data makes the clip VERTICAL (phone/camera metadata; ffmpeg auto-rotates on decode). Extract a frame and LOOK at it before pre-cropping — a needless crop=1215:2160 here would have failed/mangled. If the frame is portrait, skip step 1 entirely. |
| **silence_keep finds 0 silences (noisy room)** | With a noise floor above -40dB, silence_keep's default threshold detects nothing and long emphasis pauses (0.5-1.1s) survive. Diagnose with `silencedetect=n=-35dB:d=0.35`, then hand-write a tight keep-EDL on the cut (pad ~0.15s around each detected window, protect word tails) and re-cut + re-transcribe. Don't blindly lower silence_keep to -30/-32 (eats releases). |
| **Word-index anchors without a guard** | Anchoring cards to word INDICES is precise but one miscounted index desyncs a beat silently. Put an `EXPECT={idx:"word"}` assert block at the top of gen.py that verifies every anchor word before building the timeline — it catches off-by-ones at generation time instead of in the rendered video. |
| **npx hyperframes ETARGET flake** | npm registry can transiently 404 the latest hyperframes version ("No matching version found"). The package is already in the npx cache: run it directly via `find ~/.npm/_npx -name hyperframes -type d` → `<that>/node_modules/.bin/hyperframes render ...`. |

## Self-learning (MANDATORY at the end of a reel)
The goal is to **one-shot** the reel. Every edit must make the skill better. When the reel is delivered and approved (or after the last feedback round):
1. **Honest retro in chat**: in brief, say **what went well** and **what went badly** in THIS reel (where you cut it, which bugs, how many rounds, what you should have anticipated). No self-praise: the useful part is the error.
2. **Distill the lesson into a rule**: if the error is repeatable, update this skill WITHOUT asking:
   - recurring technical error → a row in the **ERRORS NOT TO REPEAT** table + a fix in the right script (`silence_keep.py`, `captions.py`, `gen.py`, ...).
   - new technique/animation requested → an entry in `references/animation-library.md` (with the snippet) and in the **Schema vocabulary**.
   - a style/content preference → in the Style section or the notes.
3. **Update the examples**: add the new project's generator to `references/examples/` so the next reel starts from a better reference.
Over time the errors table + the animation-library get rich enough to do it all on the first try. Every feedback not repeated twice = a skill converging to one-shot.

## Notes
- `hyperframes render` outputs `yuv420p` (no alpha): that's why cards run on a black band and get cropped (0-864). Fine, because the top band is already black.
- yt-dlp for downloading YouTube audio/music needs **deno** + an up-to-date yt-dlp (else 403). For reference IG reels yt-dlp works directly.
- Reference reels (study these for the look): instagram DYu6wymj8Vu, DYBv913x2IV, DYZs9FiDIii, DZpZb6-jAYv (green/tech). DZ4sE1RlGT- (**orange Claude**: terminal, contribution-grid, versus, stopwatch count-up, command-bar).
- Working example generators are in `references/examples/`:
  - `gen-reel1-skills.py` (**green, 4 skills**: staged hook LOGO→stamp, count-up + 4 numbered blocks anchored with `find_after`, skilltitle 01-04, per-word pills with emoji + result, **TYPEWRITER terminal** messy→clean, bigstat pop "91,000+", colored-word CTA. **3 user B-roll clips in the top band** → `compose-broll.sh`. Example of the anti-clipping pipeline.).
  - `gen-reel2-claude.py` (**orange Claude, "Claude Code tricks"**: 14 beats, landscape 4K source → raw9. New cards: claudehero, asciiwin, staged terminal + questions, staged terminal + vulnerability, mdfile, githubcard, risinggraph, triple-pulse hooks, twopill. Lesson: a dupe + a false-start hidden inside long RAW words, found only by re-transcribing the cut. caption font 84 for long words. crop_y=40 head-and-shoulders.).
