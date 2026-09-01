# What this costs

Prices and free-tier limits change. Look them up rather than trusting this page for numbers.

- [Supabase pricing](https://supabase.com/pricing)
- [Vercel pricing](https://vercel.com/pricing)
- [Railway pricing](https://railway.com/pricing)

Before someone commits to a level, open those pages, read the current figures, and tell them the total in their own currency.

## What to look up, per level

| Level | Needs | Look up |
| --- | --- | --- |
| 0 | nothing | nothing, it runs on their own machine |
| 1 | Supabase + Vercel | both paid tiers |
| 2 | Supabase + Vercel | both paid tiers |
| 3 | Supabase + Vercel + Railway | all three |

## The catches, which do not change as fast as the prices

These are the shapes that surprise people. Check whether each still applies when you look up the price.

**Supabase pauses a free project after a stretch of inactivity.** A tool used every Monday will be asleep on Monday. Waking it takes a few clicks. This is usually the first reason to start paying.

**Vercel's free plan is for non-commercial personal use.** A tool that runs part of a business is commercial use, by Vercel's own terms rather than by interpretation.

**Vercel's free plan cannot put a login wall in front of a live site.** Protection covers preview links. This is why level 1 ships its own password screen.

**Railway has no ongoing free tier.** There is a one-off trial credit, then services pause.

Confirm each of these on the pricing or docs page as you read it. When one has changed, say so, and update this page.

## The comparison that matters

Before the monthly figure feels like a lot, price what it replaces. An off-the-shelf tool for the same job is usually charged per person per month, so three people on a mid-priced tool often costs several times the whole hosting bill.

The number to compare against is what they pay today, not zero.

## Where a bill runs away

Three things, and they are the ones small businesses actually hit.

**File uploads with no size limit.** Someone uploads a huge video by accident. Always set `file_size_limit` on a bucket. See [`../security/storage.md`](../security/storage.md).

**AI calls in a loop.** A retry that never gives up calls a paid model as fast as the network allows. Cap the retries.

**A scheduled job that overlaps itself.** A job set to run every minute that takes ninety seconds accumulates copies of itself, all doing work that is being paid for.

## Keeping it cheap on purpose

Stay on free tiers while nobody else depends on it. Move to paid the day someone other than the builder needs it to work on a Monday.

Then pick the lowest level that answers the questions in [`../decision-tree.md`](../decision-tree.md). Level 3 costs more and takes longer, and most first projects are not level 3.

Level 0 costs nothing and often does the job. Take it seriously before paying monthly for a website only one person will open.
