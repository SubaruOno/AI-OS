---
name: start
description: Write the project brief and set up the starter. Use when someone describes something they want to build, describes a business problem they want software for, or asks where to begin, and project/BRIEF.md does not exist yet.
---

# Start

Turn what someone says into a **brief**, route them to a level, and build the starter.

Take this slowly. The interview decides what gets built.

## 1. Check for an existing brief

Read `project/`.

If `BRIEF.md` exists, summarise it in five lines and ask whether to continue that project or replace it.

**Done when:** `project/` holds no brief, or they have chosen continue or replace.

## 2. Interview the person

Work through the profile questions in [INTAKE.md](INTAKE.md). One question at a time. Wait for each answer before asking the next.

Give two named options wherever you can, and say what each means for their business rather than for the code.

**Done when:** every profile question in INTAKE.md has an answer in this conversation. None batched, none skipped, none assumed.

## 3. Interview the project

Work through the brief questions in INTAKE.md the same way.

Then read back a five-line brief: the one person it is for, the recurring problem in their words, the one job the app does, what working looks like, what is out of scope.

**Done when:** they have confirmed that brief, in their own words, and corrected anything you got wrong.

## 4. Route to a level

Work `docs/decision-tree.md` in order and stop at the first question that decides.

State the level, quote the question that decided it word for word, and say in one sentence what they can and cannot do there. Say what it will cost per month.

When the answer is level 0, recommend it plainly. Not building is the right answer more often than people expect, and it is worth more than a website they will abandon. Say what would move them up to level 1 later.

**Done when:** they have agreed to a level, and you can quote the exact question that set it.

## 5. Write the memory

Create `project/PROFILE.md`, `project/BRIEF.md`, `project/SLICES.md`, and `project/DECISIONS.md` from the templates in INTAKE.md. Write the level into `.stack-level` as `l0`, `l1`, `l2`, or `l3`.

Seed `SLICES.md` with the three smallest slices that would prove the app works, smallest first.

**Done when:** all four files exist, `.stack-level` holds a valid level, and every heading in every template carries a real answer. No placeholder text remains anywhere.

## 6. Build the starter

For level 0, run `/make-skill` and stop here. There is nothing to scaffold.

For levels 1 to 3, follow [SCAFFOLD.md](SCAFFOLD.md).

**Done when:** for level 0, they have run their new skill once on a real instance of the job. For levels 1 to 3, the dev server is running and they confirm they can see the first screen in their own browser.

## 7. Tell them what happens next

Three things:

- Say what you want and it gets built. There are no commands to learn.
- `project/DECISIONS.md` is the record of everything they decide, in plain English.
- `./scripts/preflight.sh` is the safety check, and it runs before anything goes live.

Then ask what the first slice should be, and run `/build`.
