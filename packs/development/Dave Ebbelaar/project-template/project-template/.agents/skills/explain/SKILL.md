---
name: explain
description: Give a plain-English tour. Use when someone asks what a file does, what just changed, what a technical word means, or says they are lost.
---

# Explain

A **tour** of one thing, pitched at the person in front of you.

Someone asking this is usually mid-task and lost. Answer the question they asked, at the size they asked it.

## 1. Find the right altitude

Read `project/PROFILE.md` for how much detail they asked for.

- *Just do it* wants two sentences and an offer of more.
- *Tell me what you did* wants a short paragraph.
- *Teach me why* wants the reasoning, and will follow a tangent.

Read `project/BRIEF.md` too, so you can explain in the vocabulary of their business rather than in the vocabulary of software.

**Done when:** every technical word in your answer is either defined in the same sentence or is a term in `docs/glossary.md`.

## 2. Give the tour

Four parts, in this order.

**What it is for.** In their words, in one sentence. Not "this module handles order persistence" but "this is where an order gets saved so it's still there tomorrow."

**What it does.** Three to five lines, in sequence. Enough that they could describe it to someone else.

**What would break if it vanished.** Imagine deleting it. If nothing gets harder, say so plainly, because that is worth knowing. If the same work would reappear in five other places, say where.

**What to change to make it behave differently.** The one or two things in this file someone would realistically want to alter.

**Done when:** all four parts are present.

The third part is the one that teaches. It turns "this file exists" into "this file earns its keep", and it is the same test used to decide whether code should exist at all. `docs/glossary.md` calls it the deletion test.

## 3. Leave them something to try

Name one thing they could safely change right now: the file, the line, and what would visibly happen.

> In `app/page.tsx`, line 34 says `limit(20)`. Change it to `limit(5)` and save. The list will show five rows. That is the whole change.

People learn this by turning a knob and watching, not by reading an explanation of the knob.

**Done when:** the suggestion names a file and a specific value.

## When they say they are lost

Different shape. Do not tour a file.

Ask what they were trying to do. Then say, in three lines, where they are and what the next single action is.

Then do that action with them.

Being lost is usually about the next step, not about understanding the system.

## When they ask what just changed

Read the recent changes and list one line per file, in their words, most important first.

Then say what is now possible that was not possible before. That is the part they actually asked about.
