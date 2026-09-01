---
name: make-skill
description: Write a reusable recipe the assistant follows the same way every time. Use when a job repeats and only one person does it, when someone asks for a skill or a slash command, or when the decision tree lands on level 0.
---

# Make a skill

Turn a job someone does by hand into a **recipe** their assistant follows.

A skill is a text file with instructions. It costs nothing, works in five minutes, and needs no website, no database, and no monthly bill. For a job that repeats and that only they do, it beats software.

## 1. Watch them do the job

Have them walk through the last real time they did it. Not the general shape, the actual last time.

Ask what they opened, what they looked at, what they decided, and what came out at the end. Where they say "and then I check whether it's worth chasing", stop and find out how they decide that. The judgement is the part worth writing down; the clicking is not.

**Done when:** you can describe the job start to finish, including every decision point, and they agree that description is right.

## 2. Find the leading word

One word this job is about, that they already use. *Chase*, *reconcile*, *triage*, *draft*, *quote*.

The right word carries the meaning by itself, so the skill is shorter and the assistant reaches for it more reliably. It goes in the name, in the description, and through the body.

**Done when:** one word is chosen and it is a word they used unprompted.

## 3. Ask what varies

Two or three questions, no more, about what changes between runs. What comes in, what goes out, what makes a run unusual.

The answer decides how much the skill has to handle. A job that is the same every time is a short skill. A job with three genuinely different shapes needs those three named.

**Done when:** every recorded answer is written into `project/DECISIONS.md`.

## 4. Write the skill

Create `.agents/skills/<name>/SKILL.md` and `.agents/skills/<name>/agents/openai.yaml`.

Follow [SKILL-RULES.md](SKILL-RULES.md). It is short and it is what separates a skill that behaves the same every run from one that improvises.

**Done when:** both files exist, the skill has numbered steps, and every step ends on a condition you could check.

## 5. Run it

Have them run it, in their own assistant, on a real instance of the job. Not a made-up example.

Watch what it does. Where it guesses, the skill was vague there; sharpen that step and run it again.

**Done when:** they have run it on real work and the output is something they would actually use.

## 6. Write it down

Append to `project/DECISIONS.md`: what the skill does, why a skill rather than a website, and what would change that.

Update `project/SLICES.md` with the skill as a built slice.

**Done when:** both files are updated and they know the one thing that would move them to level 1: the day a second person needs to use this.

## Where it lives

`.agents/skills/<name>/` in this repository. Codex reads that path directly, and Claude Code reaches the same folder through the `.claude/skills` symlink.

To use it in every project rather than this one, copy the folder to `~/.agents/skills/` for Codex and `~/.claude/skills/` for Claude Code.
