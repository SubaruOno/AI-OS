---
name: ig-icp-research
description: Researches an Instagram content strategy for anyone selling a service to a specific type of business. Takes what you sell and who you sell it to, then scans Instagram and TikTok to find what your buyers actually watch, what they complain about in their own words, which accounts to engage with, and which reels have already sold your kind of offer to your kind of buyer. Use this before setting up an Instagram account for an agency, before planning any content, or when someone asks what to post to reach business owners. Also triggers on "who should I target on Instagram", "what content reaches [niche]", "research my ICP", or when a new account is being launched.
version: 1.0
---

You are running market research for someone selling a service to businesses. The goal is not content ideas. The goal is to find out whether their buyer can be reached on Instagram at all, and if so, exactly how.

Everything downstream depends on this file being right. Take your time.

## Read first

1. `references/icp-match.md`. The filter that makes this skill work. Do not skip it.
2. `references/manual-research.md`. The by-hand version. You need it in both modes.

## Two modes

Check `vidiq_balance` at the start.

**vidIQ available.** Run the four sweeps below. Then also produce the personalised manual search list, because a sweep only finds what the query asked for and their own eyes find what it missed.

**No vidIQ.** Do not stop, and do not fake data. Switch to manual mode: build them a complete personalised search list from `references/manual-research.md`, hand them the logging table, and tell them plainly it is 60 to 90 minutes of their time instead of two minutes of tool time. Same output file either way, they fill in the rows.

Never invent a reel, a view count or a hook. If you did not pull it, the member finds it.

## Step 1: Get the inputs

Ask for these. Do not proceed without the first two.

1. **What do you sell?** The specific service. "AI receptionist that answers missed calls", not "AI automation".
2. **Who do you sell it to?** The specific business type. "HVAC companies", not "small businesses".
3. **Where?** Country or city.
4. **What do you charge?** Setup and monthly.
5. **Any results yet?** Clients, case studies, numbers. If none, say so, that is normal and handled.

### Refuse vague input

If they answer "AI automation" and "small businesses", stop. Do not spend a credit. Vague inputs return garbage that looks like data.

Push back once, concretely:

> "Small businesses is not an ICP. Which one? HVAC, dental, gyms, restaurants, law firms? Pick the one where you have already spoken to someone, or where you have any unfair advantage. If you genuinely do not know yet, run niche research first and come back."

If they still cannot name a specific business type, tell them to work that out first. This skill cannot fix an undefined market.

## Step 2: Four sweeps

Use `vidiq_instagram_tiktok_outlier_search`. Check `vidiq_balance` first. Each search costs 5 credits, budget about 20 to 30 for a full run.

**Every sweep sets `audienceQuery` to the ICP, never to the member.** Format:
`Culture/Region: US; Global: false; Demographics: HVAC company owners and contractors 30-55, lead generation, dispatching, technician hiring, service calls;`

### Sweep 1: The pain sweep

What does this ICP complain about? Query their daily frustrations, not their industry.

Good: "missed calls, no shows, technicians quitting, customers wanting free quotes, chasing invoices"
Bad: "HVAC industry"

This is the most important sweep. It returns the pain comedy pool and, more valuable, the exact language your buyer uses about their own problems.

Use `viewsMin: 20000`. Run two variations with different pain words.

### Sweep 2: The authority sweep

Who already advises this ICP, and which advice gets watched? Business coaches, consultants, trainers who sell into the niche.

Query: "advice for [ICP], growing a [business type], getting more [customers], [industry] business tips"

### Sweep 3: The offer-proof sweep

**This is the sweep that decides whether the business case works.**

Find reels that already sold something like their offer to this ICP. Query the outcome their offer produces, in the buyer's language, not the technology.

For an AI receptionist sold to home services: "stop missing calls from customers, missed call text back, AI answering service and automated booking for home service contractors"

Note what that phrasing does. It leads with the problem and the outcome. It does not lead with "AI".

### Sweep 4: Accounts

The handles that appear across sweeps 1 to 3. Run `vidiq_ig_profile` on the three or four strongest to confirm follower counts and bio positioning.

## Step 3: Dedupe, then run the ICP-match check

**Dedupe across sweeps first.** The same account and the same reel will show up in two or three sweeps. Merge before counting, or the file looks twice as full as it is.

Then classify every single result using `references/icp-match.md`. ICP, ICP's customers, adjacent, or aspirant.

**Apply the anomaly guard.** Anything above roughly 500x is a lottery result, not a format. Flag it, use it as proof the pain is real, and never hand it over as something to copy. A real run returned a reel at 14,657x. Copying that reel would waste the member's best slot.

Report the split out loud. Never hide it.

## Step 4: Give the verdict

GREEN, AMBER or RED, per `references/icp-match.md`.

On RED, tell them not to do it and give them the two alternatives. Do not soften it. Saving someone 30 days of daily filming is the most valuable thing this skill does.

## Step 5: Write the file

Save to `ig-research/[niche-slug]/icp.md`. This file is the input for every other skill in the pack.

```markdown
# ICP Research: [offer] to [buyer]

Date: [today]
Verdict: GREEN / AMBER / RED

## Inputs
Offer, buyer, location, pricing, current proof.

## ICP-match
  ICP                 X   built from
  ICP's customers     X   dropped
  Adjacent            X   flagged

## The pain list
Ranked by evidence. Each one:
- The pain in THEIR words, quoted from a real reel
- Which reel, the handle, views, multiplier, follower count
- Link
- Whether the member's offer removes it

## Their pain: content pool
Reels in the ICP bucket, pain type. Verbatim hook, format, barrier, link.

**Every row in every table carries its link.** A member scanning the tables must be able to open any reel from where they are looking. Never put a link only in the prose above a table.

## Your advice: content pool
Same structure.

## Your build: content pool
The offer-proof reels. Same structure. If empty, say EMPTY and explain what that means.

## Already doing this to your ICP
Anyone already selling this kind of offer to this ICP on Instagram.
Handle, follower count, what they post, their best multiplier.
This is their competitor and their best template at the same time.
Tell them to watch it before scripting anything.

## Bio, drafted
Both lines are outcomes. **Never mention AI, automation, or any tool name.**
Line 1: pain number one, stated as fixed, in their words.
Line 2: the result they get.
The buyer does not want AI. They want the phone answered and the calendar full.
Naming the technology makes them think cost, complexity and firing staff.

## Offer to pain map
| What they sell | Which pain it removes | Evidence |

## Engagement targets
30 to 50 handles for warmup.
- ICP pool (70%): accounts this buyer follows
- Vendor pool (30%): who already sells into this niche

## Dropped
What got filtered and why. Members must be able to check the work.

## Your search list
Personalised to this ICP. Always produced, in both modes.

- 8 to 10 search bar terms, Accounts tab
- 8 to 12 hashtags to open on the Reels tab
- 3 to 5 seed accounts to run the suggested-accounts chain from
- 2 to 3 big reels whose comments are worth mining

Tell them: open a profile, tap Reels, read the view counts down the grid,
and anything at 5x that account's normal is a format that worked.

## Beyond Instagram
The pain list in their own words is cold email subject lines, cold call openers,
discovery questions and website headlines. Every pain here has a view count
proving it lands before anyone says it on a call.
```

## Rules

- **Never invent a pain.** Every pain in the file traces to a real reel with a real number. A member writing about an industry they do not work in will get details wrong and their buyer will feel it instantly.
- **Capture hooks word for word.** Downstream skills use exact wording. Paraphrase breaks the whole system.
- **Log the barrier** on every reel. If it needs job-site access or a second actor, say so. The member is not an insider and cannot film inside an attic.
- **Flag partnership tags.** `#[brand]partner` means brand amplification. The format may be real but they are not running the same play without the deal.
- **Verify every link before it goes in the file.** Costs no credits. Fetch the URL and confirm it resolves to a real post. Instagram returns 200 for invalid shortcodes, so status codes prove nothing. Check page metadata: a real reel returns `og:type` and an `og:url`, and where the handle appears in that URL it must match the handle you are citing. A fake shortcode returns no metadata. Drop anything that fails and say so. One dead link and the member stops trusting the whole file.
- **Report credits used** at the end.
- **If a sweep comes back thin,** say so and try different wording once. Do not pad the file with weak results to make it look full.
