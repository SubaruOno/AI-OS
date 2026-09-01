# How to write a skill

A skill exists to get the same behaviour out of a system that would otherwise improvise. **Predictability** is the point: the same process every run, not the same words.

Adapted from [Matt Pocock's writing-great-skills](https://github.com/mattpocock/skills).

## The shape

```markdown
---
name: chase-invoices
description: Draft follow-up emails for overdue invoices. Use when someone wants to chase late payments, asks who owes them money, or mentions overdue accounts.
---

# Chase invoices

One line saying what this does.

## 1. First step

What to do.

**Done when:** the condition that says this step is finished.

## 2. Second step

...
```

And beside it, `agents/openai.yaml`, so it works in Codex too:

```yaml
interface:
  display_name: "Chase Invoices"
  short_description: "Draft follow-ups for overdue invoices"
```

## The rules

### Frontmatter is name and description

Nothing else. The description does two jobs: say what the skill is, and list the situations that should trigger it.

One trigger per distinct situation. "chase late payments" and "follow up on overdue invoices" are the same situation written twice, and the second one is waste. Keep the ones that are genuinely different.

Put the leading word at the front.

### One leading word, repeated

Pick a word the job is already about and use it throughout: *chase*, *reconcile*, *draft*, *slice*, *guardrail*.

Repeat the word, not its definition. A word the model already knows carries a whole region of behaviour in one token. Spelling out "carefully, methodically, without skipping anything" three different ways costs more and does less than the word *relentless*.

Hunt for restatements and collapse them into a word.

### Every step ends on a condition you could check

This is the difference between a skill that finishes the work and one that stops early.

Weak: **Done when:** the emails are drafted.

Strong: **Done when:** every invoice more than 14 days overdue has a draft, and the count of drafts matches the count of overdue invoices.

The second one can be checked, and it says how much. Vague endings let the assistant declare victory and move on.

### Say what to do, not what to avoid

Telling a model what not to do puts the thing in front of it. "Don't write long emails" makes long emails the pattern it just read.

Write the target instead: "Keep each email to three sentences."

Keep a prohibition only when there is no positive form, and even then say what to do instead.

### Move long reference out

When the skill grows past a screen, move the reference material into a file beside it and link to it:

```markdown
Follow the tone rules in [TONE.md](TONE.md).
```

The link's wording decides whether it gets read. "See TONE.md" is weak. "Follow the tone rules in TONE.md" is an instruction.

Keep in the main file what every run needs. Move out what only some runs need.

### Cut anything the assistant would do anyway

Read each sentence and ask whether it changes the behaviour. "Be helpful and accurate" changes nothing; it is already trying. Delete whole sentences rather than trimming words out of them.

Most first drafts lose a third of their length this way and get better.

## When it misbehaves

| What happens | What to change |
| --- | --- |
| Stops before the work is done | Sharpen that step's "Done when" |
| Does it differently each time | Add a leading word, make the steps more specific |
| Never fires on its own | Rewrite the description with the words actually used when wanting it |
| Fires when it should not | Cut the triggers that overlap another skill |
| Ignores a linked file | Reword the link so it reads as an instruction |

## Keep it short

Fifty to a hundred lines is normal. A skill of seven lines is fine when seven lines is the job.

Length costs twice: the assistant wades through more before acting, and every extra line is one more to keep true.
