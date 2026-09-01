# Start here, Table 05: Sales and Offers

> Written 29 July 2026, Operator Day, Porto Montenegro.
>
> This file is addressed to Claude, not to the person who downloaded it. If you're the person: drop this whole folder into the workspace you built this morning, then tell Claude "read Table-05-Sales-and-Offers/START-HERE.md and take me through it."

---

## What this folder is, and what it isn't

Two contributions, and they're different in kind. Serdar Bisi handed over a working build kit that gives Claude perfect memory of every sales call you've recorded. Lauren Tickner handed over a note pointing at a tool bundle she's giving away, hosted outside this folder.

Serdar's kit is real code shaped around one specific meeting recorder. Lauren's is a link, and the thing behind it hasn't launched publicly yet, so she's asked for feedback from anyone here who uses it.

**Treat this folder as a signal bank.** The kit isn't a product to install unchanged. It's evidence of how someone turned a pile of dead recordings into the most useful data in their business, and the structure travels further than the specific tool it was built for.

---

## The rule

**Adapt, don't install.** Three honest outcomes:

1. **Take it as-is.** Only if they already use Fathom. Then it genuinely is a five-minute setup.
2. **Take the idea, rebuild the piece.** The likely one. They record calls somewhere else, and the cache-plus-search structure ports.
3. **Take nothing, keep the note.** They don't record calls, or they don't sell over calls at all. Say so plainly.

---

## Step 1: load the business first

Read quietly before opening anything:

- `CLAUDE.md`
- `context/business.md`, `context/you.md`, `context/offer.md`
- `context/strategy.md`, `context/numbers.md`, `context/team.md`
- `context/tech-stack.md`

Five things decide this session:

- **Do they sell over calls?** If sales happen through a checkout page or a DM, Serdar's kit is the wrong shape and you should say so in the first two minutes rather than the last ten.
- **What records those calls?** Fathom, Fireflies, Granola, Otter, Zoom, Google Meet, or nothing. This single answer determines whether the kit installs or gets rebuilt.
- **How many calls, over how long?** A cache of forty calls and a cache of four thousand are different products. It changes what's worth building.
- **Who else takes calls?** From `team.md`. If a team sells, the cache becomes shared knowledge rather than personal memory, which is a bigger idea.
- **What's the offer, in their words?** From `offer.md`. You'll need it to ask useful questions later.

If those files don't exist, ask five short questions and carry on.

---

## Step 2: survey what's actually in here

### `Serdar Bisi/fathom-call-intelligence-kit/`

Small and complete. A README, an agent definition, a skill, and four Python scripts: `build_cache.py`, `enrich_cache.py`, `fetch_meetings.py`, `search_cache.py`.

The premise is the good part, and it's worth reading his README aloud with them:

> You record every call. And then nobody ever watches them again. Buried in those recordings: every objection a prospect raised, every commitment you made, every price discussion, every "let me think about it" that never got followed up.

After setup, they ask in plain English and get answers with exact quotes and timestamps. "What objections came up this month." "I've got a call with Jamie tomorrow, brief me on everything we've discussed." "What did I commit to in my last five calls." "When did we decide to change the offer, and who suggested it."

The architecture is two-part: a local cache for instant search across everything, and live API calls for transcripts and anything new. That split is the thing to steal. It's why the search is fast and why it works offline.

*Assumes:* Fathom, and a Fathom API key. Read the README's install line before doing anything, since the whole kit is designed to be handed to Claude with one sentence.

### `Lauren Tickner/AI Sales Tools.docx`

A short note and a link to a free AI tool bundle she built from ten-plus years of growing audiences and converting sales from social. Three things it aims at: generating revenue from written content, duplicating their voice so content sounds like them, and converting sales through DMs.

The bundle lives behind the link, not in this folder. Nothing here to analyse offline, so open it with them if the fit looks right and judge it live. She's noted it hasn't launched publicly and would welcome feedback from anyone here, which is worth passing on.

*Assumes:* their sales actually happen through social and DMs. For a founder selling through referrals or outbound email, this is the wrong door.

---

## Step 3: name the gap out loud

Show a ranked view in their language.

Something like:

> Serdar's kit is built for Fathom. You record on Granola. The good news is the structure ports cleanly: a local cache for instant search, live calls for transcripts. We'd swap `fetch_meetings.py` for Granola's API and keep everything else. That's about forty minutes rather than five.
>
> You've got roughly 200 calls over eighteen months, which is enough for the search to be genuinely useful rather than a novelty. And from `offer.md` you've changed your pricing twice in that window, so "when did we decide to change the offer and who pushed for it" is a question you could actually answer this afternoon.
>
> Lauren's bundle is aimed at selling through social and DMs. You sell through referral and one webinar a month. I'd skip it today, but the voice-duplication piece might matter when you start posting properly in Q4.

---

## Step 4: pick one and go deep

If they record calls, build the call intelligence. It's the highest-value hour available on this table because the data already exists and is currently doing nothing.

If they don't record calls, the honest recommendation is usually to start recording, and to spend the session setting that up plus writing the plan for the cache. That's a real outcome, just a smaller one.

---

## Step 5: adapt and build

- **Confirm the recorder before you write a line of code.** Everything downstream depends on it.
- **Port the structure, not the endpoints.** Cache locally, search locally, hit the API only for what's new or for a full transcript. Whatever tool they use, that shape holds.
- **Handle the key properly.** It goes into `.env`, which is git-ignored. Test it the moment it lands rather than discovering it's wrong after the cache build.
- **Build the cache on their real history**, then immediately ask it a question that matters to them. Not a demo question. Something they've genuinely wondered about. That's the moment it lands.
- **Think about who else should reach it.** If a team sells, this stops being personal memory and starts being shared. Say so, and note what that would take.
- **Mind the privacy line.** Call transcripts hold client information and sometimes things said in confidence. The cache lives on their machine and should stay there. If anything sensitive surfaces, point at `private/`.
- **Rewrite trigger phrases** to match how they talk.
- **Update `CLAUDE.md`** so future sessions know the calls are queryable.

---

## Step 6: record what happened

Write a row into `ledger/`: what came from this table, what got built, what got skipped and why.

If the cache got built, note how many calls it covers and what date range. That number is the thing they'll want to check against later.

---

## If they're doing this at home

Same process. Load the context first. Have them log into their meeting recorder before you start, since the API key is the one step you can't do for them.

---

*Table 05, Sales and Offers. Speakers: Serdar Bisi, Lauren Tickner.*
*From Liam Ottley's AI Makeover, youtube.com/@LiamOttley*
