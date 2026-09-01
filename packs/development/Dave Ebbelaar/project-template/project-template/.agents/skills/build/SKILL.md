---
name: build
description: Build one slice of the app, end to end. Use when the app should do something new, should do something differently, or has stopped working.
---

# Build

One **slice** at a time: a screen someone looks at, the rule that decides what happens, and the place the answer is stored.

## 1. Name the slice

Read everything in `project/`. If it is empty, run `/start` first.

Restate what they asked for as one sentence in this shape:

> so that [person] can [do thing] and see [result]

If that sentence needs an "and" in the middle, it is two slices. Split it, take the smaller one, and put the rest in `project/SLICES.md` as planned.

If the slice needs people to sign in and `.stack-level` says `l1`, run `/level-up` first.

**Done when:** they agree to one sentence that touches a screen, a rule, and a stored record, and everything split off is written into `SLICES.md`.

## 2. Ask the design questions

At most three questions, from [QUESTIONS.md](QUESTIONS.md). One at a time.

Two named options each, with what each means for their business. When there is no real choice, pick the sensible thing and say you picked it.

**Done when:** three or fewer questions are answered, and each one is appended to `project/DECISIONS.md` with the date, the question as you asked it, their choice, one line of why, and what it rules out.

## 3. Place the seam

Two sentences: where this behaviour will live, and what stays out of it. That place is the **seam**, and putting it well is what makes the next change cheap.

Aim for a deep module: one door into a big room. `sendInvoiceReminder(order)` is one thing a caller has to learn, hiding formatting, sending, and recording. Five functions the caller has to call in the right order is the same work with the cost pushed onto everyone who uses it.

Then list every file you are about to create or change, by path, before writing any of them.

**Done when:** one seam is named, and the full list of files is on screen.

## 4. Build it

Follow `docs/recipes/l<n>.md` for the level in `.stack-level`.

Screen, rule, and storage together. A screen with nothing behind it is not a slice.

New tables go through `/add-data`, never by hand and never through the Supabase dashboard.

**Done when:** the slice runs start to finish in the browser, the record it created is visible in the Supabase table editor, and `pnpm lint`, `pnpm typecheck`, and `pnpm build` all pass.

## 5. Hand them the mouse

Walk them through doing the job themselves. Give the address and the steps, then wait.

Watching someone use it is how you find out what you built wrong.

**Done when:** they confirm they did the action in their own browser and saw the result, and `SLICES.md` marks this slice built with today's date.

## 6. Say what changed

One line per file from step 3, in their words, at the level of detail in `project/PROFILE.md`.

Then name one thing they could safely change and try right now, with the file and the value.

**Done when:** every file in step 3's list has its line.

## When something is broken rather than missing

Steps 1 and 2 change; the rest is the same.

First reproduce it. Have them show you the exact thing that goes wrong, or do it yourself. A bug you cannot reproduce is a bug you cannot fix.

Then find why it happens before changing anything. Say the cause out loud in one sentence. If you cannot, keep looking rather than guessing.

Then continue from step 3.
