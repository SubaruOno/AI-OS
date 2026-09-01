# Start here, Table 02: Short Form

> Written 29 July 2026, Operator Day, Porto Montenegro.
>
> This file is addressed to Claude, not to the person who downloaded it. If you're the person: drop this whole folder into the workspace you built this morning, then tell Claude "read Table-02-Short-Form/START-HERE.md and take me through it."

---

## What this folder is, and what it isn't

Albert Olgaard handed over his actual short-form production workspace. Not a cleaned-up sample, the real thing, including a worked example reel with its source files still in place.

That makes it the most useful and the most dangerous pack in the room. Useful because you can see exactly how a working pipeline is put together, every step, including the ugly parts. Dangerous because it's tuned to one person's look, one person's machine, and a fairly heavy set of tools.

**Treat this folder as a signal bank.** You're not installing Albert's studio. You're reading it to understand how someone who ships short form daily actually structures the work, then building the version that fits the person in front of you and the software they're willing to run.

---

## The rule

**Adapt, don't install.** Three honest outcomes for each piece:

1. **Take it as-is.** Their setup and taste happen to line up. Uncommon here, because this pack has real dependencies.
2. **Take the idea, rebuild the piece.** The likely one. The pipeline shape is right, the specific tools and the visual style need to become theirs.
3. **Take nothing, keep the note.** They don't publish short form, or they have an editor who already does this. Say so and write down what's here for later.

Never install something in silence because it was easier than the conversation.

---

## Step 1: load the business first

Read before you open anything in this folder:

- `CLAUDE.md`
- `context/business.md`, `context/you.md`, `context/offer.md`
- `context/strategy.md`, `context/numbers.md`, `context/team.md`
- `context/tech-stack.md`

Do it quietly. Four things decide everything on this table:

- **Do they appear on camera?** Most of this pack starts from a talking-head clip. If they don't film themselves, the reel side is dead and the carousel side becomes the whole conversation.
- **Who edits today?** Them, a freelancer, an agency, nobody. If they pay an editor, the honest recommendation might be to hand that editor this pack rather than to build anything.
- **What's the actual bottleneck?** Filming, editing, or deciding what to post. Different answers point at different pieces in here.
- **How much software will they tolerate?** This matters more here than on any other table. Some of this needs command-line tools installed. If they flinch at that, say so early and steer to the lighter pieces rather than burning the session on setup.

If those files don't exist, ask five short questions covering the same ground, one at a time, then carry on.

---

## Step 2: survey what's actually in here

`Albert Olgaard/Short Form Content/` is a complete Claude Code workspace. Read its `CLAUDE.md` first, it's a good short document and it explains the two headline skills better than a summary can.

Seven skills live in `.claude/skills/`:

**`reel-editor`** is the centrepiece. One raw talking-head clip becomes a finished 9:16 reel: speaker in the bottom half, animated motion-graphics cards in the top half, one-word karaoke captions, background music. The pipeline is spelled out step by step (transcribe, hand-built edit list, cut, silence trim, re-transcribe, cards, captions, compose, self-evaluate). It has a mandatory retro step where the skill updates its own SKILL.md with lessons after each reel, which is the single best idea in this pack and worth stealing even if nothing else here survives.

*Assumes:* ffmpeg, Node (for `npx hyperframes`), Python with PIL, and either an ElevenLabs API key for transcription or a local Whisper fallback. Also assumes the green-glass "Ambra" look, though the accent colour is themeable.

**`ig-carousel`** generates a cinematic cover plus content slides sharing one visual world. Two styles you pick between and never mix: `daylight` (bright, photoreal, voxel mascot, editorial serif, for educational and list posts) and `hacker-desk` (dark desk, pixel-art mascot, condensed sans, code blocks, for technical posts).

*Assumes:* the Higgsfield MCP is connected. Without it this skill does nothing, so check before you promise it.

**The five YouTube helpers:** `youtube-clipper`, `youtube-broll-maker`, `youtube-popup-graphic`, `youtube-thumbnail-maker`, and `slideshow`. Lighter, more self-contained, and easier to adapt than the two above. If the person's answer in Step 1 was "I flinch at installing things", start here.

**The worked example.** `reels/c0886/` holds a real reel mid-production, and `outputs/carousels/` holds finished carousel images. Read these to understand the file layout the pipeline expects. Be aware the edit lists inside carry absolute paths from Albert's own machine, so the example won't replay as-is. That's fine, it's reference material, not a demo. Don't try to run it and don't apologise for it.

---

## Step 3: name the gap out loud

For each piece worth considering, work out what it assumes, what's actually true here, and how far apart those are. Then show them a short ranked view using their own details.

Something like:

> The thumbnail maker and the clipper are the two I'd start with. They're light, they don't need anything installed beyond what you've got, and from `strategy.md` your problem is volume, not polish.
>
> The reel editor is the impressive one and I want to be straight with you about the cost. It needs three tools installed on your machine and a transcription key. If you're up for twenty minutes of setup, the thing it produces is genuinely good and you'd own the pipeline permanently. If not, we skip it today and I'll write down exactly what it'd take.
>
> The carousel skill needs an MCP you don't have connected. Worth revisiting, not today.
>
> Albert's look is his. Green glass, his fonts, his mascots. Whatever we build, we're rebuilding the style layer around your brand, and I'll need your colours and fonts to do that.

Be specific. Use their handles, their audience, their last post.

---

## Step 4: pick one and go deep

One piece properly beats four half-installed. On this table that's more true than anywhere else, because half-installed here means a broken ffmpeg command and a bad taste.

Recommend the one that hits the bottleneck from Step 1. If the bottleneck is deciding what to post rather than producing it, the honest answer might be that this table's pack doesn't solve their problem and Table 01's outlier work does. Say that.

---

## Step 5: adapt and build

- **Check the dependencies before you promise anything.** Run the version checks. Finding out ffmpeg is missing halfway through a build is a bad moment for a non-technical person.
- **Rewrite every path.** These files came from another machine, and the example folder is full of absolute paths that point at a Mac that isn't theirs.
- **Rebuild the style layer from their brand, not Albert's.** Colours, fonts, logo, tone. The structure stays, the look changes completely. If they don't have brand assets to hand, pull them from their site.
- **Rewrite the trigger phrases** to match how they actually talk.
- **Keep the self-evaluation and retro steps.** Both headline skills end by checking their own output and writing down what they learned. That's the part that makes a skill get better instead of going stale, and it's the easiest thing to accidentally delete while simplifying.
- **Test on their real footage.** A clip they shot, not a sample.
- **Update `CLAUDE.md`** so future sessions know what exists.

---

## Step 6: record what happened

Write a row into `ledger/` covering what came from this table, what got built, and what got skipped and why. For anything skipped on dependency grounds, write down the exact missing piece, because that's a fifteen-minute fix on a quiet evening and they'll want to know.

Close by naming what's left and what would make each piece worth another look.

---

## If they're doing this at home

Same process, two changes. Load the workspace context first. And set expectations honestly at the start: this is the heaviest pack from the day in terms of setup, and the right outcome might be one small skill working properly rather than the full pipeline half-running.

---

*Table 02, Short Form. Speakers: Albert Olgaard, Oliver. Pack from Albert.*
*From Liam Ottley's AI Makeover, youtube.com/@LiamOttley*
