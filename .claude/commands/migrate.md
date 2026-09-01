# /migrate

> For someone who already has an AI workspace and doesn't need building from scratch. Points at what they've got, compares it against this one, and walks them through what's worth taking, one decision at a time.

## Variables

args: $ARGUMENTS (a path to their existing workspace, or empty to ask)

---

## For the assistant

- **You are advising, not converting.** They built something that works. The job is to show them what's missing and let them choose, not to talk them into this structure.
- **Read-only until they approve a specific change.** Never write into their existing workspace before they've said yes to that exact thing.
- **Three hard safety rules.** Check these before touching anything:
  1. Their workspace must be a **git repository**. If it isn't, do the analysis and write it up, but change nothing. Say so plainly.
  2. It must have **no uncommitted changes**. If it does, stop and tell them to commit or stash first. Do not offer to do it for them.
  3. If anything is unexpected, **degrade into conversation** rather than erroring. Explain what you found and ask.
- **Never delete anything of theirs.** Every change is additive or a clearly-labelled proposal.
- All prose follows `reference/writing-style.md`.

---

## PHASE 0, Check the available engine (1 min)

This command does a genuinely heavy piece of analysis: reading two entire workspaces, comparing them across four layers, and reasoning about what's worth moving. It's worth spending a minute making sure it can do that properly, because a thin version of this analysis is worse than none.

Use the strongest reasoning mode currently available in the chosen harness. If
the harness offers safe parallel workers and the workspace permits them, split
the read-only comparison by context, workflows and skills, work records, and
integrations. Otherwise perform the same audit sequentially. Do not hardcode a
model name or optional feature, and never block the migration because a feature
is unavailable.

**One rule regardless of horsepower:** the analysis doc can be as long and as thorough as it needs to be, but **what you say in the chat stays simple**. Walk them through it one plain-English step at a time. They should never have to read the doc to follow the conversation.

---

## PHASE 1, Find it (2 min)

If a path was passed, use it. Otherwise: *"Where does your existing workspace live? Give me the folder path."*

Then check the safety rules above. Report what you found in one line: the path, whether it's a git repo, whether it's clean.

**If they turn out not to have much,** say so honestly and offer the install workflow. A folder with a few prompt files is not yet a workspace, and the normal path will serve them better.

---

## PHASE 2, Read both sides (5 min)

Read their workspace properly, don't skim the folder names.

- Their constitution file, whatever it's called: `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, a README.
- Every command and skill they have, and what each actually does.
- Their context or memory files: what's documented about the business, and what's stale.
- How they record work, if they do. Is there any record that survives a session.
- Their integrations and keys.
- Their folder structure and what it implies about how they work.

Then read this workspace's equivalents so the comparison is real rather than from memory.

---

## PHASE 3, The delta (write it down)

Write `outputs/migrate-analysis.md`. This is the artifact they keep, so make it good.

Four layers, and for each, three buckets: **what they have that this doesn't**, **what both have**, **what this has that they're missing**.

1. **Context.** A constitution loaded every session. Docs on the business, the founder, strategy, the team, the workspace's own shape. A private boundary for what shouldn't be shared.
2. **Rhythm.** Something that loads context at session start. Something that records work at the end. A durable record across sessions. Version control and an off-machine backup.
3. **Capability.** Web, video, social. The business tools actually connected. A way to add a capability without hand-writing it. A way for it to check its own work.
4. **Team.** Can a second person get a seat. Is there a sharing boundary if they do.

For every row where they're missing something, write **one sentence on what it actually buys them**, in terms of their work rather than in terms of features. "You'd stop losing what you decided last Tuesday" beats "adds a ledger".

Close with **the three highest-value gaps**, ranked, and be opinionated about the order.

**Also record what they do better.** They will have things worth stealing in the other direction, and saying so is what makes the rest credible. Flag those clearly; they're the ones worth contributing back to the room.

---

## PHASE 4, Walk it, one decision at a time

Go through the ranked gaps **one at a time**. Never bulk-apply.

**Keep the chat simple even though the doc is dense.** They shouldn't need to read `migrate-analysis.md` to follow you. One system, explained in plain English, then a decision. If you catch yourself reading the document out loud, stop and say it in a sentence instead.

For each:
1. What it is, in a sentence.
2. What it changes about their week.
3. What it would cost to adopt: files added, habits changed, anything it might break.
4. **Then ask: take it, skip it, or come back to it?**

On **take it**: make that one change, show them the diff, confirm it's what they wanted, then move to the next. On **skip**: record why in the analysis doc. That reasoning matters more than the decision.

Take it in either direction. If something of theirs is better, port it into this workspace instead.

---

## PHASE 5, Close and point them forward

1. Update `outputs/migrate-analysis.md` with what was taken, what was skipped and why.
2. Run their equivalent of prime, or prime here, and confirm nothing broke.
3. Write the ledger row.

Then the handoff into the rest of the day:

```
Your workspace now has [what they took]. The analysis is in
outputs/migrate-analysis.md if you want to revisit the ones you skipped.

Next: pack-review walks the pack folders one at a time and works out
how each one maps to your business, so you arrive this afternoon knowing
exactly what to ask.
```

---

## Finish with log (automatic)

Run the log workflow as the final step. Don't ask.
