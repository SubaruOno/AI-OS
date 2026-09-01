---
name: ig-ideas
description: Turns ICP research into Instagram reel ideas backed by real outlier data. Runs in launch mode to produce a complete 10 reel launch plan for a new account, or weekly mode to produce the coming week's menu. Every idea carries a verbatim hook from a real reel with view counts and multipliers attached. Use after ig-icp-research, when planning what to post, when someone asks for reel ideas for their agency or business account, on "what should I post this week", "give me my launch plan", "reel ideas for [niche]", or every Monday once an account is running.
version: 1.0
---

You turn research into a shortlist the member picks from. You never write scripts. That is `ig-script`.

## Read first

1. `ig-research/[niche]/icp.md`. If it does not exist, stop and tell them to run `ig-icp-research`. Do not guess at an ICP.
2. `references/formats.md`. The three content types and their sub-structures.
3. `references/sequencing-rules.md`. Which type goes on which day.

If the research file says **RED**, do not produce ideas. Repeat the verdict and the alternatives.

## Two modes

Ask which, or infer. No reels posted yet means launch mode.

---

## LAUNCH MODE

Runs once, on Day 1. Produces the member's own launch plan covering **Days 1 to 13**, not just the posting days.

This is the most valuable artifact in the pack. They should finish reading it knowing exactly what they are doing every day for two weeks.

### Days 1 to 3 come first, personalised

The guides explain warmup in general. This plan makes it specific to them. Do not skip it and do not send them back to the guide.

```markdown
## DAY 1: Setup and warmup

**Setup, about an hour**
- [ ] Account created, Personal, region set to [their market]
- [ ] Name field: "[their name] | [their offer] for [their ICP]"
- [ ] Bio, two lines, drafted for them right here.
      **Both lines are outcomes. Never mention AI.**
      Line 1 is pain number one from `icp.md`, stated as fixed, in the buyer's
      own words from the reel that proved it lands.
      Line 2 is the result they get. Not the technology, not the method.
      Banned in the bio and the name field: AI, automation, bot, agent, chatbot,
      and every tool name. Also banned: "I help [niche] do [thing]".
      Test: would the buyer nod at line 1 before knowing what is being sold?
- [ ] Booking link live
- [ ] Suggested Accounts ON, Activity Status OFF, apps removed

**Warmup, 2 to 3 sessions of 10 to 15 minutes**
Follow these 8 today, from their ICP pool, by name:
@handle, @handle, ...
- [ ] Like 3 to 5 posts per session
- [ ] Watch reels to the end
- [ ] Zero comments. Zero posts.

## DAY 2: Warmup
Follow these 8, different accounts, listed by name.
Vendor pool today: @handle, @handle
Same caps. Still no comments, still no posts.

## DAY 3: Warmup, film Day 4
Follow the last 8, by name.
- [ ] Explore feed check: does it look like your buyer's feed yet?
- [ ] Run ig-script for Day 4
- [ ] Film it
```

Split their engagement list across the three days, 70 percent ICP pool and 30 percent vendor pool, and name the actual handles per day. A member should never have to decide who to follow.

### Days 4 to 13

Fill every slot from `references/sequencing-rules.md`. For each of the ten:

```markdown
### DAY [n]: [Type], [one line summary]

**Job:** why this slot exists, from sequencing-rules
**Length:** [seconds. vidIQ does not always return duration for Instagram reels. If it is missing, estimate from the format in formats.md and say it is an estimate. Never invent a precise number.]
**Solo filmable:** yes / no, and if no, the solo alternative
**Barrier:** what they need. If it is anything they do not have, pick a different reel.

**Hook**
> "[the hook, with the slot filled for their ICP]"

**Frame:** [the fixed sentence shape, untouchable]
**Slot:** [what was swapped, and what it was in the original]
**Voice:** acting a character is fine, film it as written. Only flag it if the hook makes a
credentials claim in the member's own voice ("after closing 75 homes"), which means drop the reel,
or carries a possessive that claims an identity ("my clients"), which is a one word swap to "your".

**Source:** @handle · [views] · [multiplier] · [followers] · [link]

**Body beats:**
- beat
- beat
- beat

**Spoken CTA:** [said out loud, never written in the caption]

**Caption:**
[keyword first, 2 to 3 lines, no "comment X for Y"]

**Hashtags:** 3 to 5, niche specific
```

Close with a summary table: day, type, hook, source multiplier.

---

## WEEKLY MODE

Every Monday from Day 14. Fresh outliers, seven slots, same type rotation.

**Return a menu, not a plan.** At least five options per slot. The member picks. Nothing gets scripted until they do.

---

## Hard rules

### Never return a single answer

Every slot offers at least five options. If everyone in the community gets handed the same top-scoring reel, everyone posts the same reel, Instagram's duplicate detection finds it, and everyone gets buried.

Weight the ranking by their specific offer, ICP and pain list so two members with different inputs get genuinely different tops.

### Frame is fixed, slot is theirs

Every hook has a fixed sentence shape (the frame) and a variable part (the slot). Print both on every idea so the member can see exactly what they may touch.

Print this on every output:

> The frame is untouchable. Fill the slot with your ICP and your pain, even when the slot is long. Rewrite the frame and you threw away the only tested thing you had. Same frame plus same concept plus same tool is a duplicate and it buries both of you.

### Verify every link before showing it

**No credits, no excuse.** A dead link destroys trust in the whole file.

Fetch each reel URL and confirm it resolves to a real post. Instagram returns 200 for invalid shortcodes, so status codes prove nothing. Check the page metadata instead: a real reel returns `og:type` and an `og:url`, and where the handle appears in that URL it must match the handle you are citing. A fake shortcode returns no metadata at all.

Instagram reel URL: `https://www.instagram.com/reel/[shortcode]/`

Drop anything that fails and say so.

### When the build pool is thin

The offer-proof pool is always the smallest. Far more people complain about a niche's problems than sell software into it. Two proven build hooks for three build slots is normal.

**Reuse the proven structure with a different build.** "How to connect Claude to the MLS" becomes "how to connect your open house sign in sheet to your phone." Frame kept, tool name dropped. Same proven hook shape, different thing built, different screens, different problem. That is not a duplicate.

Never fill a build slot with an unproven hook, and never move a pain hook into a build slot. Say in the plan which slots reuse a structure and why.

### Filter by barrier

Drop any reel whose `effort.barrier` the member cannot clear. Job site access, clinical settings, specialist equipment, a second actor they do not have.

Say what you dropped and why. Do not silently hand someone a reel they physically cannot film.

### Tag solo-filmable

Some pain comedy needs two people. Every idea says whether it can be filmed alone, and gives a solo version when it cannot.

### Flag partnerships

Any source carrying a brand partner tag gets flagged. The format may still work, but without the deal and the brand's amplification they are not running the same play.

### ICP bucket only

Only build from results in the ICP bucket of the research file. Never from the ICP's customers bucket, no matter how big the numbers are.

### Capture hooks in one batch

Capture every hook word for word here, in this run. `ig-script` must never need to spend credits re-fetching.

## Ranking

Score each candidate:

1. **Evidence.** Multiplier first, follower count second. A 300 follower account at 100x is worth more than a 300K account at 3x, because it proves the format works without an audience.

   **The sweet spot is 10x to 200x.** That is where a format is genuinely working. Below 10x it is noise. **Above 500x it is a lottery ticket, not a template.** Never rank an anomaly first. Handing someone a 14,657x reel to copy wastes their best slot and teaches them the system does not work.
2. **Buyer pull.** Would the ICP stop for this? Their pain beats your technology every time.
3. **Feasibility.** Can they film it this week with what they own?
4. **Freshness.** Posted in the last 30 days.
5. **Difference.** Does it add something the last five reels did not?

## Output location

Launch mode: `ig-research/[niche]/launch-plan.md`
Weekly mode: `ig-research/[niche]/week-[n]-menu.md`

Report credits used.
