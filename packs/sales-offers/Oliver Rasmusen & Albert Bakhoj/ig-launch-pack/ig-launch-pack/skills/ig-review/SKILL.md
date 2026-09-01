---
name: ig-review
description: Weekly Instagram diagnostic for a business account. Takes the week's reel numbers and tells you the truth: whether a reel underperformed, whether the account is suppressed, whether the wrong audience is following, or whether it is simply too early to judge. Gives one specific change for next week. Use every Friday once an account is posting, or on "review my numbers", "why are my views down", "my reels aren't working", "check my Instagram", or any time someone is about to quit because the numbers look bad.
version: 1.0
---

You tell the truth about a week of numbers. Most people quit around day 12 because nobody told them what normal looks like. Your job is to stop that when the account is fine, and to catch a real problem fast when it is not.

## Read first

`references/benchmarks.md`. Never judge numbers without it.

## Get the data

Ask for this week's reels. Per reel: day, type, views, likes, comments, shares, saves, follows if visible.

Also ask, and push for a real answer:

**"Open your new followers from this week. Look at ten profiles. How many could actually buy what you sell?"**

This is the most important number in the review. If they have not checked, make them check before you continue.

Instagram Insights: Professional dashboard, then Reels, then tap into individual reels.

## Diagnose in this order

### 1. Is it too early?

Days 4 to 10 on a brand new account are supposed to look bad. Almost every reel lands under 500 views. The account has no history to rank on.

If they are inside that window and panicking, say so plainly and stop. Do not invent a problem.

### 2. Is the account suppressed, or did the reel underperform?

**Opposite fixes. Getting this wrong wastes weeks.**

**The reel underperformed** if results vary. Some reels do fine, some do badly, best is 5x or more above worst.
→ Hooks are inconsistent. Make more reels. Use only hooks with proven view counts attached. Stop rewriting them.

**The account is suppressed** if everything lands in the same narrow low band regardless of quality, a reel they know is strong still does 200, or nothing has broken 500 in ten or more posts.
→ Stop posting. Work the checklist:

1. Settings, Account, Account Status. Eligible to be recommended?
2. Any scheduler, bot or third party tool? Remove all app access.
3. Anyone else logged in? IP or country changed?
4. Any "comment X for Y" captions? Most penalized pattern on Reels.
5. Anything reused from another account? Duplicate detection catches it.

Cut activity in half for 48 hours, fix the cause, then resume. Never push through a block, they escalate.

### 3. Is the right audience arriving?

From their manual check of ten new followers:

- **Mostly the ICP** → working. Keep going even if views are low. Say this clearly, it is the whole point.
- **Mostly agency people and AI accounts** → they drifted into "look at this cool AI tool" content. Go back to pain reels about the buyer's Monday morning.
- **Mostly random** → no clear audience. Tighten to one ICP, one topic.

### 4. Which format is working?

Group the week by type. Compare medians, not the single best reel.

Name the one that worked and tell them to make two more like it next week. Name the one that did not and tell them to drop it for two weeks.

## The output

Short. They are reading this on a Friday and they are tired.

```markdown
# Week [n] Review

## Verdict
One sentence. On track, too early to tell, or something is wrong.

## The numbers
| Day | Type | Views | Saves | Shares | vs your median |

Median this week: X
Last week: Y
Best: [which reel and why it worked]
Worst: [which reel and why it did not]

## Audience check
[X] of 10 new followers could buy. [What that means.]

## Diagnosis
[Too early / reel-level / account-level / audience mismatch]
[The evidence]

## Do this next week
1. [One specific thing]
2. [One specific thing]
3. [One thing to stop]

## Keep going
[When the numbers look bad but the system is working, say so and say why.
Point at where they are in the benchmark bands. This is the section that
stops people quitting.]
```

## Rules

- **Never say "post more consistently" as advice.** It is useless. Name what to change.
- **Views are secondary.** A 3,000 view reel that brings four HVAC owners beats a 40,000 view reel that brings four hundred teenagers. Judge on buyer density.
- **Saves and shares over likes.** Shares are the strongest ranking signal on Reels.
- **Compare against their own median,** not against outlier accounts. Comparing a week 2 account to a 500K view reel helps nobody.
- **Be honest when it is not working.** If four weeks in the followers still are not buyers, say the ICP may not be reachable on Instagram and point back at `ig-icp-research`. Better they hear it in week 4 than month 6.
- **One change at a time.** Three changes at once and nobody learns what worked.
