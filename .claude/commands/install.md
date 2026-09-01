# Install

> Zero to a working AI operating system. The core path takes about 45 to 60 minutes; all ten steps with optional integrations and demonstrations can take up to about three hours. Interactive throughout: the assistant asks, the person answers, and the assistant builds.

## Variables

args: $ARGUMENTS (usually empty, and that's fine)

**Always check `.install-state` first, whatever the arguments are.** If the file exists and isn't marked complete, greet them back by name and resume at the first step that isn't done. Never restart a founder who already answered forty minutes of questions. `START-HERE.md` promises them exactly this, so it has to hold.

---

## For the assistant

- **This is a conversation, not a script.** Explain before doing. Wait for confirmation between steps. Never two steps without a stop.
- **Use the person's language for every visible word.** English prompts, headings, and summaries for an English speaker. Natural です・ます調 Japanese for a Japanese speaker. Do not print an English header in a Japanese installation. The playbook stays in English internally; the conversation does not.
- **Assume a non-technical person** who may never have used Claude Code or Codex before. Smart person, zero coding. No jargon without a plain-language explanation in the same sentence.
- **The pattern for every step:** explain → confirm → act → verify → celebrate → stop.
- **No error dumps, ever.** Name the problem simply, fix it together, or park it without blocking the rest.
- **Track state.** After each step, rewrite `.install-state` in exactly this shape, so any later session can resume without re-asking anything:

  ```
  founder: <name>
  mode: personal | business
  os: mac | windows
  harness: claude | codex
  access: confirmed | unknown
  language: en | ja
  structure: <the Step 2c decision, one line>
  steps:
    0: done | skipped | pending
    1: done | skipped | pending
    ... through 10
  keys: <platforms whose keys are in .env and tested>
  tools: <platforms connected via composio>
  remote: <github url, or none>
  notes: <anything a resuming session needs, e.g. git still downloading>
  ```

  A step marked `skipped` is finished, not pending: never re-offer it. When Step 10 lands, add `complete: yes`.

- **Write a ledger row as each step lands, not at the end.** After every step, append one row to `ledger/<owner-first-name>.md` (create it at Step 1, once you know their name), per the standing rule in the constitution. By Step 9 they should be looking at eight or nine rows of their own morning. An install that only logs at the end shows them an empty file.
- **Maintain both constitutions as you go.** Every step that changes what the workspace can do updates `CLAUDE.md`, copies the identical result to `AGENTS.md`, and verifies byte equality. Never add harness-specific workspace facts to only one file.
- **Maintain both skill folders.** `.claude/skills/` is the canonical source. After any skill change, run `python scripts/sync_harness_skills.py` (`python3` is also acceptable) and then `--check`.
- **Keys come from `reference/getting-keys.md`.** Follow its rules exactly: sign-up link first on its own, wait for them to confirm they're in, then the key page. Never both links at once. If a console has moved, find the current path, use it, and update that file.
- **Secrets never enter chat.** When a key is needed, run `python scripts/set_secret.py KEY_NAME` (`python3` on a Mac if needed). The person enters it into the hidden local prompt. Never ask them to paste a password, token, recovery code, or API key into the conversation, and never print a value from `.env`.
- **Test every key the moment it lands.** `getting-keys.md` has a verified test per platform. Run it, and don't call the step done until it comes back clean. A mistyped or half-copied key is the most common thing that quietly breaks a workspace a week later.
- **Voice matters.** Encourage talking over typing. Celebrate real milestones in one line, not confetti.
- All prose you write during this install follows `reference/writing-style.md`.
- **Timings below are guidance, not a clock.** They exist so you know what deserves the most room. Step 2 is the one that pays for everything else.

---

## STEP 0, Orient (2 min)

No header, no ceremony. Translate every quoted question into the person's language before displaying it. Ask only what cannot be detected safely.

**First know the current harness and language.** You already know whether you are Claude Code or Codex and which language the person used. Record both. The ten steps are the same. Claude Code may expose slash-command shortcuts; natural-language workflow requests work in both harnesses.

1. **Detect Windows or macOS, then confirm only if uncertain.** Every command from here must match. On Windows, use PowerShell-compatible commands and Git for Windows. On macOS, use Terminal-compatible commands. If a third-party installer only supports a different shell, explain that before using it and give a working alternative.

2. **"Is this for you, or for your business?"** [Added by Terakoya.AI, 2026-08-03; not part of Liam's original.] Ask it plainly, and don't dress it up as a big decision, because it isn't one — the folder is the same either way and they can add the business side later without redoing anything.

   - **"For me"** → `mode: personal`. Students, freelancers, anyone building a second brain before they have a company. Follow **THE PERSONAL PATH** below, which changes about five things and leaves the rest identical.
   - **"For my business"** → `mode: business`. The default, and the rest of this command as written.
   - **Unsure, or "both"** → personal. It is the smaller start and grows into the business one by running install again later. Say that aloud so they know nothing is closed off.

3. **"Do you already have an AI workspace folder that loads your context at the start of every session?"**
   - **No** → the normal path. Continue to Step 1. This is nearly everyone, including people who are very good with AI but run it all out of a chat window.
   - **Yes** → ask one more: *"Does it load context about your business automatically, and does it keep a record of work that survives between sessions?"*
     - **Yes again:** they have a real system, and sitting them through a beginner install wastes them. **Eject now:** *"You don't need this install. What's more useful is comparing what you've already built against what's in here and taking whatever's worth taking."* Invoke migrate and stop. Do not continue to Step 1.
     - **No:** it's a folder with a few prompt files in it, which isn't the same thing. Come back to Step 1 and treat that folder as an import in Step 2.

4. **Confirm product access, not a particular plan name.** For Claude, confirm the account can open Claude Code. For Codex, confirm the account can open Codex in the app or CLI. Plan names and entitlements can change, so use the product's current account screen rather than hardcoding Pro, Max, Plus, or another tier. If access is missing, give the current official account link and pause cleanly.

5. **Then start the git download before you do anything else.** Don't announce this as a step, just do it: run `git --version` quietly.

   - **If it returns a version,** say nothing and move on.
   - **If it doesn't,** this is the one thing that has to start now, because it's a one to two gigabyte download and Step 4 can't happen without it. Say so plainly: *"One thing to kick off in the background before we start talking. It's a big download and I want it running while we do the interesting part."* Then:
     - **Mac:** run `xcode-select --install`. A box appears. Tell them to click **Install** and let it finish in the background while you continue.
     - **Windows:** try `winget install --id Git.Git -e --source winget` first. It installs silently with no dialog and no clicks, and it works on Windows 10 1709 and later. If winget isn't recognised, fall back to https://git-scm.com/download/win, run the installer, accept every default. **Either way they must close and reopen PowerShell afterwards**, or `git` still won't be found even though it installed fine. That one catches everybody.
   - Either way, do **not** wait for it. Note in `.install-state` that git was still installing, carry on to Step 1 immediately, and re-check quietly at the top of Step 4.

   The whole point is that the download runs through the forty-minute context interview and is finished before anything needs it. Never let a founder sit and watch a progress bar.

Write `.install-state`. **STOP.**

---

## THE PERSONAL PATH

> [Added by Terakoya.AI, 2026-08-03; not part of Liam's original.] Read this only if Step 0 landed on `mode: personal`. On `mode: business`, skip the whole section and run the ten steps exactly as written.

**It is the same folder and the same ten steps.** Five things change, and nothing else. Do not build a different workspace or describe it as cut down. Everything they build survives the day they start a business: they run install again, it sees `mode: personal` in `.install-state`, and adds the business layer. Say that once, early, then stop talking about it.

**1. Step 1's framing.** The gap is theirs, not a company's. They already have tools that do work when triggered, and chats that forget them by tomorrow. What's missing is a place where *they* are written down in a form the AI reads automatically — what they're working on, what they're learning, what they decided last month and why. Same layers, same "today is the bottom four."

**2. Step 2 is still the step everything stands on, and it is still forty minutes.** Do not shorten it because the subject is a person. The import in 2a becomes their own material: chat export first (same instruction, same reason — it is months of them explaining themselves in their own words), then coursework, notes, a CV, applications, writing they're proud of, a reading list, half-finished projects. Links become their GitHub, LinkedIn, a portfolio, anything public.

**3. Four sub-steps change shape:**
   - **2c (how many businesses)** → skip entirely. The flat `context/` structure is right. Do not ask.
   - **2d (the team pass)** → becomes the people pass, and keep it, because it is worth as much here as it is for a company. The handful of people who matter to their work: a supervisor, a study group, a co-founder, whoever they'd ask for a reference. Name, how they're connected, what they'd go to that person for.
   - **2e (the questions)** → *them*: what they're working on now, what they're trying to become good at, what they want off their plate, what they keep re-explaining to an AI every time they open a chat. Then the near horizon: what's due, what's undecided, what a good three months would look like.
   - **2f (the drawer)** → same principle, different line: *"anything you wouldn't hand a classmate or a new colleague on day one — grades, money, health, family, anything half-formed you're not ready to be judged on."* The drawer matters more here, not less, because a personal brain fills up with personal things. Say the safety line properly.

**4. Which files get written.** Create files as they are filled, never before — a blank file is homework and homework does not get done. On the personal path write `context/you.md` (expanded well past the stub: who they are, how they work, what they're doing now) and `context/people.md`. Then **delete the business stubs from the folder**: `business.md`, `offer.md`, `numbers.md`, `strategy.md`, `team.md`, and `tech-stack.md` unless they actually build things, in which case keep it. Also remove the empty `team/` and `data/` directories. Tell them plainly what you removed and that `/install` puts it all back if they ever need it. A folder with three real files beats one with nine, six of them empty.

**5. The packs.** Four of the eight assume a business with clients and should be flagged as such rather than walked: `sales-offers/`, `operations/`, `compliance/`, `sponsorships/`. The other four may be relevant to an individual, but none is assumed portable or installed. `packs/COMPATIBILITY.md` and pack-review govern promotion.

**Everything else runs as written.** Steps 3 through 10 are identical. Prime and log are worth as much to a student as to a founder, because nobody else is keeping their record for them.

---

## STEP 1, What we're building (8 min)

Print:
```
════════════════════════════════════
  AIOS SETUP, Step 1/10: The shape of it
════════════════════════════════════
```

You're painting the whole picture before they type anything. Keep it to a few short paragraphs and check they're with you at the end.

**The gap they're in.** They already have two things: tools that do work when triggered, and chats where they think out loud with something that forgets everything by tomorrow. Neither of those is their business knowing itself. What's missing is the layer underneath both, a place where the business is written down in a form the AI reads automatically. That's what this folder is.

**The layers, bottom to top.** Context (what the business is). Data (the numbers and records it runs on). The workspace and its integrations (this folder, reaching your actual tools). Then what you build on top: exploring it by hand, turning repeated work into skills, handing skills to agents that run without you, and eventually small apps with a screen.

**Today is the bottom four.** Context, data, integrations, and using it. Everything above that gets easier once these exist, and none of it works without them.

**What changes.** Right now they re-explain their business every time they open a chat, they bounce between a dozen tabs, and they type when they could talk. All three of those are hours a week, and all three go away.

Then one question to make it theirs: **"what should I call you?"**

Write state. **STOP: "Ready for the part that does the work?"**

---

## STEP 2, Your business, in my head (40 min)

Print the step header (2/10: Your business, in my head).

**The step everything else stands on.** Say that out loud, and say you'd rather they took the time here than rushed to the fun bit. The order matters: **feed it everything first, analyse, then ask questions to fill the gaps.** Interviewing before reading wastes their breath on things you could have read.

### 2a. Get the raw material in (5 min of their effort, then it runs in the background)

1. **"Which AI have you been using — ChatGPT, Claude, Gemini, or more than one?"** Then send them to export it. **If they use more than one, bring all of them.**

   Make the case before giving the instruction, because this is effort they have to go to and it is worth it: it's months of them explaining their own business in their own words, unprompted and unedited, and it's the single richest context source they own. It is **optional** — the install works without it — but nobody who fetches it regrets it.

   - **Claude:** Settings → Privacy → Export data. **Usually arrives within minutes.**
   - **ChatGPT:** Settings → Data controls → Export data. **Allow up to a day.** Observed 2026-08: far slower than Claude in practice. Request it first, then forget about it.
   - **Gemini:** not in the Gemini app at all — it's in **Google Takeout** (takeout.google.com). *Deselect all* → tick **My Activity** → *All activity data included* → *Deselect all* → tick **Gemini Apps** only → OK → *Next step* → *Create export*. Google's own guidance is a few minutes to a few days, most people the same day.

   Four things about the Gemini route specifically, each of which catches people:
   - The output is an **HTML activity log**, not the JSON the other two produce. Readable, but noisier — expect to do more filtering.
   - The archive **expires in about seven days** and can be downloaded only five times. Requesting it three weeks ahead of a session is wasted effort; request it a day or two before.
   - On a **managed account** (a university, a company), an administrator can switch Takeout off entirely — Admin console → Data → Data import & export. If the option is missing or errors, that is why, and it is not something they can fix. Have them use a personal Google account instead.
   - Advanced Protection Program enrolment schedules the archive **two days out** by design, not as a fault.

   **Have them request it right now** even if it won't arrive until later, then carry on. When it lands, they drop it into `context/import/` and you re-read it. Never let the interview wait on an email.

2. **"Now throw everything else into `context/import/`."** Be expansive about this, people are too conservative: business plans, pitch decks, an old strategy doc, their offer or pricing sheet, a services page, onboarding docs, SOPs, a spreadsheet of clients, financial summaries, brand guidelines, anything half-finished. **Nothing is too messy.** They don't need to organise it, that's the point of the folder.

   Say the safety line as you ask, because you're asking for their real documents: *"That folder stays on this machine. It's git-ignored, so none of it reaches the backup or a teammate. I read it, pull out what belongs in the shared context, and the originals stay put."* That's what makes it safe to be greedy here.

3. **"And any links."** Their website, their LinkedIn, Instagram, YouTube, X, a Substack, their booking page, a podcast they've been on. Anything public that describes what they do.

### 2b. Analyse it all before asking anything

Read every file in `context/import/`, then research the links. Actually go and look at the sites, don't guess from the URL.

Then **tell them what you learned**, in a few sentences, before you ask a single question. This does two jobs: it proves you actually read it, and it exposes what's wrong so they correct you rather than reciting things you already know.

### 2c. Decide the shape before writing anything

A real consulting moment, and don't skip it just because it's a conversation rather than a task.

**"How many businesses am I setting this up for?"**

- **One business:** the default flat `context/` structure. Move on.
- **Two or more:** work out the right shape together, out loud. The failure mode to avoid is ten near-identical docs per business, which nobody maintains and which makes every session load noise. Options to walk with them:
  - **A shared top level plus a folder per business.** `context/` holds what's true across all of them (who they are, how they work, the shared team) and `context/businesses/<name>/` holds only what differs. This is usually right.
  - **One primary plus light satellites,** where one business gets the full treatment and the others get a single page each. Right when there's one real business and a couple of side projects.
  - **Fully separate workspaces,** if the businesses share nothing and different people work on each. Say so honestly if that's the answer; it's better than a bloated single workspace.
- Whichever you land on, **write down why** in both constitutions so the next session does not relitigate it.

### 2d. The team pass (required)

Not optional, and worth more than people expect. For each person: **name spelled correctly, their email, their role, and a short paragraph on what they actually own.**

Say why: this is loaded every session, so the workspace stops saying "your team" and starts saying "ask Sarah, she owns onboarding". It's also exactly what `/new-teammate` reads later to build someone a seat, so getting it right now saves that conversation twice.

If the team is large, **the core people only.** Anyone who'd be in the room for a decision.

### 2e. Now the questions

Only the gaps. One question at a time, digging where an answer is thin. Skip anything the documents already answered, and say you're skipping it.

- *The business:* what it does in their words, who the customers are, who the ideal one is specifically, what's sold and roughly at what price, how customers find them, what makes them different.
- *The founder:* their role, where the time actually goes, what decisions land on their desk, what they want off their plate first.
- *The strategy:* the two or three current priorities, what success looks like in three to six months, what's undecided.
- *The numbers:* what they track, roughly where things stand, where those numbers live.

### 2f. The drawer

"Anything you wouldn't hand a brand-new hire on day one, real margins, what people are paid, deal terms, personal notes, lives in `private/`. It stays on this machine, never syncs, never reaches a teammate. From everything you've told me, what belongs in there?" Split it: full detail into `private/`, the team-safe version into `context/numbers.md`.

### 2g. Write, read back, correct

Write the context docs to the structure agreed in 2c. Thirty to eighty lines each, clear and scannable. Then read a short summary of each back: "does this capture it? what's off?" Correct until they say yes.

Close by stamping both `CLAUDE.md` and `AGENTS.md`: name, one-liner, owner, currency, timezone, context structure decision, and standing instructions. Verify the files are identical.

Verify every context file is populated, team included, readback approved. Update `.install-state`. **STOP.**

---

## STEP 3, Proof (5 min)

Print the step header (3/10: Watch this).

Short, and it lands hard. Don't over-explain it, just do it.

1. "Close this session and open a fresh one." Wait for them.
2. Ask them to say “Prime this workspace and catch me up.” In Claude Code, mention `/prime` only as an optional shortcut. It loads the brain and reports where things stand.
3. "Now ask me something you'd normally have to explain from scratch. Anything about your business."

Answer with full context. Let the moment sit. Then name what just happened in one line: a brand-new session, no explaining, and it already knew.

Update state. **STOP.**

---

## STEP 4, Save points and backup (15 min)

Print the step header (4/10: Nothing you do here is ever risky).

Teach, check they've got it, then act. After each idea, ask lightly: "in your own words, what does that give you?" One sentence back and you move on.

1. **Save points.** "Git gives this folder save points, like a game. Every version of every file, kept. Nothing you do here can't be undone." Re-check `git --version` quietly. It should already be there, either because they had it or because Step 0 started the download an hour ago. If it's still going, park this step, carry on to Step 5, and come back: never make the room wait on one machine. If it never started (they skipped Step 0 or clicked the wrong thing), start it now per Step 0 and do Step 5 while it runs. Then `git init`, main branch. Show them `.gitignore` and say what it means: "your keys and your private drawer are physically excluded. They cannot reach the backup." First commit, narrated as save point one.

2. **The cloud copy.** "GitHub is where the backup lives, and later, where teammates connect. Free, private, yours." Walk the signup click by click if they need it. Then the important sentence: "now I get access, so you never have to touch this again." Sign in with the device flow, a short code pasted into the browser, no tokens to copy around. Connect the remote, push.

3. **Prove it works, don't just claim it.** Make a trivial change, commit it, push it, and have them refresh github.com to watch it appear. They should see the loop close with their own eyes once.

4. **Then take git off their plate, explicitly.** Say it plainly: *"That's the last time you'll think about any of this. Branches, commits, merges, conflicts, none of it is your job. I run all of it. If two people ever edit the same document, I'll read both versions and just ask you which bits to keep, in plain English. You will never see a merge conflict."* This matters more than it sounds: git is the single most intimidating thing in the kit and the whole design is that they never touch it.

5. **Mention the GitHub habit.** From here, whenever a developer tool offers "Continue with GitHub", take it. One identity, one place to turn on two-factor, and the same pattern their teammates will use.

6. **The trust moment.** "Open github.com and look. Your files are there. Now notice what isn't: no private folder, no keys, and none of the raw documents you dumped in this morning. The drawer stayed home."

   Before you say that sentence, **check it's true.** Run `git ls-files` and confirm nothing from `private/`, `context/import/` or `.env` is tracked. If any of it is, don't say the line: fix it first (`git rm -r --cached <path>`, confirm it's in `.gitignore`, commit), then say it. Never make this promise on trust.

Skippable if they are nervous or short on time. If skipped, record it; log will commit locally and remind them occasionally. Note that skipping also removes the GitHub sign-in shortcut used by some later services.

Verify: clean `git status`, confirmed push, or a recorded skip. Update state. **STOP.**

---

## STEP 5, Your tools, connected (15 min)

Print the step header (5/10: Reaching your actual world).

1. **Frame it, because this is the point of the whole workspace.** *"Everything your business runs on is about to be reachable from this one folder. Your context is here, your data is here, and now your tools are here too. The goal is that you stop leaving: no bouncing between twelve tabs to answer one question."* One account reaches around a thousand tools, so there's no integration to build per platform.

   Be greedy here. **Connect as much as they'll let you.** Every tool that stays outside is a tab they'll keep opening, and each one they connect makes everything downstream better: the research, the apps they build later, the agents.

2. **Install if supported.** Follow the Composio block in `reference/getting-keys.md`. If its current installer is unsupported on their OS, park it rather than changing shells without explanation. Use the new-capability workflow for their most important missing tool.

3. **Which tools.** "What runs this business day to day? Everything: CRM, payments, booking, email, project tool, spreadsheets." Write the full list to `context/tech-stack.md`. Then: "**which two or three do you actually live in?**" Connect those now with `composio link <tool>`, one OAuth click each.

4. **Prove one.** Run a real command against a real account: their last five deals, this week's bookings, today's unread. Their data, on screen, from here. Land it: "that's your [tool], reachable from this folder, permanently."

5. **Gmail and Calendar** go through Composio too, not a Google Cloud project. One click each.

Update `context/tech-stack.md` and both constitutions' routing. Update state. **STOP.**

---

## STEP 6, The utility stack (20-25 min)

Print the step header (6/10: Eyes and ears on the outside world).

**All four of these get set up, not a pick-one.** Each is cheap or free to start and takes about five minutes.

**Give them the reasoning before the first signup, because otherwise this feels like admin.** Two things this buys them:
- **Now:** their workspace can see the outside world properly. Any site, any video, any platform, pulled in clean rather than guessed at. It's also what makes deep research work at Step 9, and that's the single most impressive thing in the kit.
- **Later:** these same connections drop straight into whatever they build. When they make an app, an automation or an agent in a month, the scraping is already wired up. They won't be starting from a blank page and hunting API docs; they'll be assembling from parts they already own.

Do them in order and land each one before starting the next.

**How to run every single one** (the rules are in `reference/getting-keys.md`, follow them exactly):
- Give the **sign-up link on its own**, then stop and wait for them to say they're in. Never hand over both links at once.
- Then the key page, then run `python scripts/set_secret.py KEY_NAME` and have them enter the key into the hidden local prompt.
- **Then run that block's test.** Don't move to the next tool until it comes back clean.
- Give each one its thirty-second why as it lands, in terms of *their* business.

1. **Firecrawl.** Reads JavaScript-heavy pages, bot-protected sites, and PDFs. When it lands, update both constitutions' routing and tell them. Live test: scrape a competitor's pricing page.

2. **Supadata.** Turns video into text. YouTube, TikTok, Instagram, X, plus YouTube search. Live test: pull the transcript of a video in their niche.

3. **Apify.** Reaches what nothing else can: Instagram, TikTok, LinkedIn, Google Maps, marketplaces, review sites. Live test: pull something from whichever of those matters to them.

4. **X search (Grok).** What's being said in their market right now. This one is paid with no free tier, so say that plainly and let them skip it if they'd rather. Everything else still works without it.

**Zero-setup wins, mentioned as you go:** writing style is always on, so nothing this workspace produces sounds like a bot. Academic and Substack search need nothing at all. Demo one quickly on their industry.

**If someone is falling behind,** get Firecrawl and Supadata in and move on. Those two carry most of the value and the other two are a one-sentence ask on any day.

Update both constitutions' routing as each lands. Run the skill sync check, update state, and **STOP.**

---

## STEP 7, Make it do something (15 min)

Print the step header (7/10: Now put it to work).

Step 3 proved it knows them. This proves it can act.

1. Ask for a fresh session, then have them say “Prime this workspace.” Mention `/prime` only as an optional Claude Code shortcut.

2. **Build the menu from what they've actually connected**, not from a generic list. You know their tools from `context/tech-stack.md` and you know their business from Step 2, so the options should be specific enough that they recognise their own week in them. Offer three or four, one line each:
   - *If a CRM or pipeline is connected:* pull the last thirty days and tell them what's stalled.
   - *If email is connected:* draft the follow-ups for everyone who went quiet.
   - *If a spreadsheet or finance tool is connected:* turn last month into a one-page PDF.
   - *If they're content-led:* pull a competitor's recent videos and summarise what's working.
   - *Always available:* build a deck from the strategy doc written an hour ago.

3. **Then get out of the way and let them watch.** This is the moment the room goes quiet, so don't narrate over it. The output has to be a real file or a real page they can open, not a wall of chat.

Update state. **STOP.**

---

## STEP 8, The branch (25 min)

Print the step header (8/10: Your pick).

Three lanes, and **the honest default is to skip straight past this if nothing here fits.** Don't manufacture work. If they haven't got spreadsheets and their tools are already connected, send them to Step 9 early and give the room back the time.

### Lane A, get your data into one place

For anyone running the business out of spreadsheets. **Look first, then offer.** If Sheets or Drive is connected, go and see: how many spreadsheets, how many touched recently, which ones are doing a database's job. Come back with the finding, not a question. "You've got thirty-four sheets, nine touched this month, and three of them are really a customer database wearing a spreadsheet costume."

Then:
1. Supabase, per `reference/getting-keys.md`. GitHub sign-in, so it's a few clicks. Two projects free.
2. Pick two or three sheets that matter.
3. **Audit before you migrate.** Profile them: columns, types, row counts, duplicates, blank columns, inconsistent dates, mixed types in one column. Show them what you found. This alone is worth the step, and it's worth doing even if the database doesn't happen.
4. Propose a schema, including how the sheets relate to each other, and get a yes.
5. Build the tables, import, verify the row counts match, and report what you cleaned versus what you left alone.
6. Then ask it something the spreadsheets couldn't answer. That's the payoff.

They never touch Supabase directly. You build it, you move the data.

### Lane B, connect the rest

For anyone whose problem is tool sprawl rather than spreadsheet sprawl. Work down `context/tech-stack.md` with `composio link`, testing each one live. Stop when they've got what they need.

### Lane C, or just move on

Take something genuinely on their plate this week and do it together. Or, if they'd rather push on, go to Step 9. Finishing early with a working workspace beats padding the hour.

Update state. **STOP.**

---

## STEP 9, How the whole thing runs (12 min)

Print the step header (9/10: How this stays alive).

They have run prime twice and seen log by now, so most of this is naming what they have already felt. Walk the whole system once and keep each item to a couple of sentences.

**The rhythm**

- **Prime,** at the start of every session. It pulls the latest, catches unfinished work, loads the context, and reports where things stand. In Claude Code, `/prime` is an optional shortcut.
- **Log,** at the end of completed work. It catches anything unlogged, checks context drift, saves, and backs up. In Claude Code, `/log` is an optional shortcut.
- **Handoff,** when a session gets long and the thread frays. It packages the state and provides the exact text for a fresh session.
- **The ledger.** Rows are written as work happens, not at the end. Point at their own file and show them today's rows. Then the payoff: in six months this answers "what did we decide about pricing in July" without anyone remembering.
- **The safety net.** If they close the laptop mid-session and never log, the next prime notices stale unfinished work and helps recover it without touching recent work from another session.

**Building things**

- **Explore** to think an idea through, **create-plan** to write the plan, **implement** to build it, and **test** to check the result. Natural-language requests invoke them in both harnesses.
- **New-capability** when Composio does not have a tool: it researches that platform's API and builds the integration.
- **New-teammate** when someone joins: it writes their role, decides what they can see, and creates their onboarding pack.

**Under the hood, so they know it's there and then forget it**

- The workspace **documents itself** as they build, and keeps an index so sessions load the right doc rather than everything.
- **Writing style** is always on, so nothing it produces sounds like a bot.
- **Git** is entirely handled. They never touch it.

**Then the model consoles.** Not a signup exercise, just knowing where things are for the day they build something.

- **Anthropic**, `platform.claude.com/settings/keys`. The strong models, and what agents run on.
- **OpenAI**, `platform.openai.com/api-keys`. Mainly Whisper, so call recordings and voice notes into text.
- **Gemini**, `aistudio.google.com/apikey`. Cheap and multimodal, good for volume and for reading images, audio and video.

All three are in `reference/getting-keys.md` with the current routes. Say plainly that **none is needed for the workspace itself**; it runs through the Claude Code or Codex access already confirmed. These keys are for products built on top.

**Then stop and take questions.** This section always opens a lot of them, and answering three real ones here is worth more than finishing on time.

Update state. **STOP.**

---

## STEP 10, Where to from here (5 min)

Print the step header (10/10: Done).

Quick health check as a green list: context populated, team loaded, prime accurate, backup live, tools connected, first real output made.

Then close with options rather than a goodbye:

```
Your AIOS is live. Where to from here:

→ RECOMMENDED: use it for a week. Prime to start, log to end.
  Anything still on your setup list is one sentence away.

→ "teach me to build". Now your tools are connected, I'll walk you
  through building your first app: explore → create-plan →
  implement → test, on something real from your business.

→ "add a teammate", when you're ready to give someone their own seat.
  One command writes their role, decides what they can see, and mints
  their onboarding pack.

→ "connect my [platform]", any tool, any day.
```

Translate the closing block into the person's language. Mark `.install-state` complete. Run `python scripts/sync_harness_skills.py`, `python scripts/verify_distribution.py`, and the relevant live checks. Write the install's rows into `ledger/<name>.md`, commit, and push if a remote was configured.
