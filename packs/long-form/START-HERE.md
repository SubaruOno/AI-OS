# Start here, Table 01: Long Form

> Written 29 July 2026, Operator Day, Porto Montenegro.
>
> This file is addressed to Claude, not to the person who downloaded it. If you're the person: drop this whole folder into the workspace you built this morning, then tell Claude "read Table-01-Long-Form/START-HERE.md and take me through it."

---

## What this folder is, and what it isn't

Two speakers from the Long Form table handed over pieces of their own working systems. Shaz Mathew and Samin Yasar both run content operations at a level most people don't, and what's in here is a slice of how they do it.

It is not a product. Nothing in this folder was built for the person sitting in front of you. Every piece carries assumptions that came from someone else's business: their channel, their upload cadence, their editing stack, their idea of what a good video is. Some of those assumptions will fit. Most won't, exactly.

**Treat this folder as a signal bank.** It's evidence about how experienced operators solve a problem. Your job isn't to install it. Your job is to read it, work out what it's really doing underneath the specifics, and then build the version that fits the business you already know.

A pack that runs but doesn't fit is worse than no pack. It becomes a thing they never open, sitting in their workspace making them feel behind.

---

## The rule

**Adapt, don't install.** Installing is the fallback, not the goal.

There are three honest outcomes for each piece in here, and you should be willing to land on any of them:

1. **Take it as-is.** The problem it solves is their problem and the assumptions happen to fit. Rare, but it happens. Install it and move on.
2. **Take the idea, rebuild the piece.** The most common outcome. The approach is right, the implementation assumes tools or a workflow they don't have. Build their version, borrowing the structure.
3. **Take nothing, keep the note.** The problem isn't theirs yet. Say so plainly and write a line in their workspace explaining what's here and when it'd become relevant. That's a real result, not a failure.

Never pretend option 1 happened when it was really option 2. And never install something in silence because it was easier than having the conversation.

---

## Step 1: load the business first

Before you open a single file in this folder, read what you already know:

- `CLAUDE.md`
- `context/business.md`, `context/you.md`, `context/offer.md`
- `context/strategy.md`, `context/numbers.md`, `context/team.md`
- `context/tech-stack.md`

Do this quietly. Don't narrate the file reads.

You're looking for four things specifically, because they decide everything downstream on this table:

- **Do they publish long form at all today?** YouTube, podcast, newsletter, webinars, anything over about five minutes. If the answer is no, that changes the whole session and you should say so early.
- **Who makes it?** Them, a team member, an editor, an agency. Named, from `team.md`.
- **Where does it die?** Ideas, scripting, filming, editing, packaging, distribution. Every content operation has one stage that's the bottleneck, and it's rarely the one people talk about.
- **What's already connected?** From `tech-stack.md` and whatever Composio linked this morning.

If those context files don't exist (they're reading this at home in a different folder, or Session I didn't finish), don't guess. Ask five short questions covering the same ground, one at a time, then carry on.

---

## Step 2: survey what's actually in here

Open every file before you form an opinion. Here's the map so you know what you're looking at.

### Shaz Mathew, three standalone skills

`outlier-report-creator.md`
Scans YouTube channels you're tracking and finds videos that massively outperform that channel's own normal numbers, then turns the pattern into video ideas. The interesting design choice: a Python script does the mechanical part (API calls, computing outliers, writing a data table) and Claude does the creative part (reading the data next to what it knows about the business and suggesting what to actually make). The skill explicitly says a report with no suggestions at the end is an incomplete run.

*Assumes:* a YouTube channel worth benchmarking against competitors, a free YouTube Data API key (it walks the setup), and that outlier-chasing is the right idea strategy for them.

`youtube-analytics-reviewer.md`
Takes a YouTube Studio CSV export and produces a plain-language diagnostic: what's working, what isn't, what to do next. No API key. The first-run handling is worth studying on its own; it checks for a CSV already sitting in the folder, explains the export path, tells them the literal folder to drop it into, and runs `open` on that folder so they're not hunting through Finder.

*Assumes:* an existing channel with enough history for the analytics to mean anything.

`script-to-presentation.md`
Turns a video script into a self-contained HTML presentation built for filming with a teleprompter. Zero dependencies, opens in a browser, 20+ slides, speaker notes embedded as data attributes. Reads a brand voice file if the workspace has one.

*Assumes:* they film to a script, and they want on-screen slides in their videos. This one is the most stack-independent piece on the table.

### Samin Yasar, a link list

`Long form Skills .pdf` is one page pointing at four public repos:

- `github.com/Samin12/viral-video-script`, idea to hook, setup, talking points, CTA
- `github.com/Samin12/content-skill-pack`, plans YouTube content and repurposes a video into shorts, blogs, threads, LinkedIn posts
- `github.com/Samin12/b-roll-finder`, finds B-roll candidates and places approved clips on the spoken word
- `github.com/Samin12/cut-video`, strips dead air, fillers and retakes while keeping laughs and intentional pauses

The content lives on GitHub, not in this folder. If the two editing skills look relevant, go and read the repos before recommending them, because you can't judge them from a one-line description. They'll also carry heavier setup than Shaz's do, most likely ffmpeg and a transcription step.

---

## Step 3: name the gap out loud

Now put the two halves together. For each piece worth considering, work out three things:

- **What it assumes** about the business it was built for
- **What's actually true** here, quoting their own context back at them
- **The distance between those**, and whether it's a five-minute change or a rebuild

Then show them a short ranked view. Something like:

> Shaz's analytics reviewer is closest to ready. You've got 14 months of uploads and it needs nothing but a CSV, so we could run it in about five minutes and you'd have a real diagnostic today.
>
> The outlier report is the one I think matters most for you, because from `strategy.md` your problem isn't production, it's deciding what to make. It needs a free API key and a list of channels to track. We'd swap his tracked-channel setup for the eight people in your space you already watch.
>
> The script-to-presentation skill assumes you film to a script with slides on screen. You film unscripted walk-and-talks. I'd skip it, or repurpose the HTML generator for your client-facing decks instead, which is a different job it happens to be good at.

Be specific. Use their customer names, their tools, their numbers. A generic recommendation is one they'll ignore.

---

## Step 4: pick one and go deep

One piece, properly, beats four half-installed.

Let them choose, but recommend. Your recommendation should be the one that hits the bottleneck you identified in Step 1, not the one that's easiest to install.

If the honest answer is "none of these, but the idea underneath the outlier report is exactly what you need in a different shape", say that and build the different shape. That's the best possible use of this folder.

---

## Step 5: adapt and build

Now do the work. Some things to hold onto:

- **Rewrite paths, don't inherit them.** These files came from other machines. Any absolute path in here is wrong for this workspace.
- **Rewrite the trigger phrases** in a skill's frontmatter to match how this person actually talks. If they say "check the competition" and the skill listens for "run the outlier report", the skill will never fire.
- **Keep the judgment, change the specifics.** Shaz's threshold for what counts as an outlier came from his channel's numbers. The threshold should change. The idea that you compare a video to its own channel's baseline rather than to the whole platform should not.
- **Test it on something real.** Their actual channel, their actual competitors, their actual last video. Never a demo URL.
- **Update `CLAUDE.md`** so future sessions know the capability exists and when to reach for it.

---

## Step 6: record what happened

Before you finish, write it down so it survives the week.

Write a row into `ledger/` covering what came from this table, what got built, and what got deliberately skipped and why. The skipped ones matter more than people expect. In three weeks when they think "wasn't there something about competitor videos", the answer should be in their own workspace.

Then close with what's left. Name the pieces you didn't build, one line each on what would make each one worth revisiting, and remind them that any of it is one sentence away on any future day.

---

## If they're doing this at home

Everything above still applies, with two changes. Get the workspace context loaded first, because without it you're guessing and the whole point of this file is that you shouldn't be. And take the survey slower, since there's no speaker in the room to ask.

Say up front that this is a working session, not a reading exercise, and that they should have their channel open.

---

*Table 01, Long Form. Speakers: Jack Roberts, Shaz Mathew, Samin Yasar. Packs from Shaz and Samin.*
*From Liam Ottley's AI Makeover, youtube.com/@LiamOttley*
