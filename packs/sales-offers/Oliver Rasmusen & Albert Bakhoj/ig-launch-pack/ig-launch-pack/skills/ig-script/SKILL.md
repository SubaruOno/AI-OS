---
name: ig-script
description: Writes a complete, film-ready Instagram reel script from a chosen idea. Outputs the hook word for word, body beats with timings, on-screen text, a keyword-first caption, hashtags, and a filming spec. On build reels it also writes a full step by step guide to actually build the thing being demoed, so the member ends the day owning a working asset as well as a post. Use after picking an idea from ig-ideas, or on "write the script for day 4", "script this reel", "I'm filming today", "turn this idea into a script".
version: 1.0
---

You turn one chosen idea into something the member can film in the next hour.

## One reel at a time, with one exception

Default is one reel per run. It keeps quality high and lets later reels react to what the early ones actually did.

**The exception is a batch filming session.** If they ask for several days at once, only allow it for reels with no build guide: pain and advice. Those are the ones people film in a single sitting. Write each one to its own file, and add a shared setup note at the end: what to wear, what order to shoot in, and a reminder to change shirts between takes so it does not look like one session.

**Never batch a build reel.** The build guide should be generated the day they build it, so the steps match whatever the tool looks like that week.

## Read first

1. `references/hooks.md`. The verbatim rule. This is the part people ruin.
2. `references/formats.md`. The three types and their structures.
3. The launch plan or weekly menu, and the `icp.md` research file.

Never invent a hook. If the idea has no source hook with a view count attached, go back to `ig-ideas`.

## The hook is used word for word

Copy the source hook exactly. You may change the industry noun, the number, or the job title. Nothing else.

- Source: "5 reasons your RDH isn't 3k a day"
- Allowed: "5 reasons your techs aren't 3k a day"
- **Banned:** "Here are five reasons your technicians may not be hitting revenue targets"

Proven hooks are ugly. They start mid-thought and break grammar. That roughness is why they read as a real person instead of an ad. Leave them ugly.

Every output states the source handle, views and multiplier next to the hook so the member can see it is not a guess.

## Run the plausibility check

**Before writing anything.** The member does not work in this industry. Their buyer does, every day, and will spot a fake in half a second.

For every claim, number, and piece of jargon:

- Does this come from the research file, from a real reel, with evidence?
- Would someone who actually runs this business say it this way?
- Is any number invented?

If something fails, cut it or replace it with something sourced. Say what you cut and why.

One wrong detail costs more than a weak reel. It costs credibility with the only people who matter.

## Claims come from the reel, never from you

Do not invent statistics. Do not go looking for statistics.

**Take the claims from the scripts that already went viral on this ICP.** The outlier reel is proof that the claim landed on this exact audience. That is stronger evidence than a study nobody will read.

- A coach at 176.5x said "not calling people back is costing you clients." Use that framing.
- If a proven reel used a specific number, use that number and say where it came from.
- If no proven reel gives you a number, do not create one. Use a truth they feel instead: "a lead that sits overnight is usually gone."

Your buyer never argues with a truth they feel. They always argue with a statistic you cannot back, and that argument happens on the sales call, not in the comments.

Market pricing is always safe because it is checkable. "Tools like this run $300 to $1,500 a month" is fine. "I made an agent $40,000" is not, until it is true.

## How much of the build to show: mirror the source

**Match the reveal depth of the reel you are copying.**

If the proven reel handed over the full recipe, hand over the full recipe. It worked for them on this audience, and most owners still will not build it themselves. If the proven reel showed the outcome and only part of the method, do the same.

Do not impose a rule the source did not follow. The source is the evidence.

Two things stay constant either way:

- **Always show the outcome completely.** Problem in, result out. That is the part that sells.
- **Never show credentials, API keys or client data on screen.**

State in every build script which the source did, and which you are doing.

## Output changes by type

### THEIR PAIN

No build guide. They need staging direction.

```markdown
## DAY [n]: [title]
Type: Their pain · [seconds] · Solo filmable: yes/no

**Hook, word for word**
> "[exact]"
Source: @handle · [views] · [multiplier] · [link]

**On-screen text:** [large, top third, matches the spoken hook]

**Setup**
Location, props, camera position, wardrobe. All of it must be things they own.

**The beats**
0:00-0:03 [what happens, what is said]
0:03-0:08 ...

**How to play it**
Deadpan or exasperated. Where the pause goes. Where the punchline lands.
Most of these fail from overacting. Underplay it.

**Solo version** (if the reel needs two people)

**Caption** [keyword first, 2 to 3 lines]
**Hashtags** [3 to 5]
**Audio** [trending sound or voice only, and why]
```

### YOUR ADVICE

No build guide. The advice itself must be real and sourced.

Same structure, plus:

```markdown
**The advice**
The actual thing they say, written out, ready to read.

**Where it came from**
Source. Research file, a real operator, or a proven reel.
Never invented. Generic advice reads as an outsider guessing
and it is worse than posting nothing.
```

### YOUR BUILD

This one gets the build guide.

Same structure, plus:

```markdown
**What to screen record**
Exactly which screens, in which order, at which moment.

## THE BUILD GUIDE

What you are building: [the thing, for their offer, for their ICP]
Time: [realistic]
Tools: [what they need, with links]

### Step 1: [action]
[Specific. Real tool names. Real settings. Real prompts to paste.]
**Record this:** [what to capture for the reel]

### Step 2: ...

### Test it
How to prove it works before filming.

### What this is worth
Market rate for this service, sourced. This is what they say
on the call, and what goes in the reel as borrowed proof.
```

The build guide must be specific enough to follow with no prior knowledge. Real tools, real steps, real prompts. If a step needs an account or a paid tool, say so up front.

## The caption

**Keyword first.** Hashtags barely move reach since Instagram killed hashtag following. Keywords in the caption and in the on-screen text do the ranking now.

- Line 1: the hook or a close variant, with the keywords in it
- Line 2 to 3: the value, plainly
- No "comment X for Y". It is the most penalized caption pattern on Reels and it will cap a new account at its seed audience.

3 to 5 niche hashtags. Not 30. Specific to the buyer, not generic.

## The CTA

**Spoken out loud in the reel. Never written in the caption.**

Under 1,000 followers, the CTA is the bio link or a simple follow. Comment gates come later, once the account is established.

## Both delivery versions

Every script gets:

1. **To camera.** Face on screen.
2. **Screen record with voiceover.** Face optional.

Face is optional. **Their real voice is not.** Voice is what makes someone trust you enough to book a call.

## Filming spec

Every script ends with:

- Length target
- Number of cuts
- Trending audio or voice only, and why. Creator accounts have the full music library, this is the entire reason the account is Creator and not Business.
- On-screen text placement
- One thing to get right, and the one mistake that kills this format

## Output location

`ig-research/[niche]/scripts/day-[n]-[slug].md`

One file per reel. Everything needed to film in it.
