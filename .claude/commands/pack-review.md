# Pack review

> Map optional source packs to the person's needs and portability requirements.
> Claude Code also exposes this as `/pack-review`.

## Variables

`args: $ARGUMENTS` may name one pack or be empty.

## Rules

- Read `packs/README.md` and `packs/COMPATIBILITY.md` first.
- The output is decisions and useful questions, not a folder summary.
- Ground every recommendation in the person's context.
- Be honest when a pack does not apply.
- A source pack is not installed and is not automatically cross-harness.
- Follow `reference/writing-style.md` and use the person's language.

## 1. Orient

Read the relevant context files, then inventory the actual folders under
`packs/`. Choose the order by likely value, not alphabetically.

## 2. Review each pack

For each selected pack, provide:

1. **What it does.** Two or three sentences, not a file list.
2. **Where it touches this person's work.** Name the process, cost, bottleneck,
   or opportunity. Mark guesses as guesses.
3. **Compatibility.** Classify it as likely portable, needs adaptation, or
   harness-native. Name external tools, hooks, settings, shell commands, path
   assumptions, and OS dependencies that must be tested.
4. **Verdict.** Now, later, or not for you, with one reason.
5. **Questions.** Two or three sharp questions that cannot be answered by merely
   reading the pack.

Stop after each pack so the person can correct the context or move on.

## 3. Produce the review

Write `outputs/pack-questions.md` with the verdict, compatibility note, and
questions for each reviewed pack. Put the two or three best next actions at the
top.

## 4. Promote only when explicitly chosen

If the person chooses a capability for installation:

1. read the whole source skill and its resources;
2. adapt harness-specific tool names and OS-specific commands;
3. put the reviewed copy in `.claude/skills/<name>/`;
4. run `python scripts/sync_harness_skills.py`;
5. test a realistic task in the current harness and OS;
6. do not claim support for the other harness or OS until it has been tested;
7. run `python scripts/verify_distribution.py`.

Finish with the log workflow automatically.
