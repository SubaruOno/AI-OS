# The interview

Questions and file templates for `/start`. Ask one at a time. Wait for each answer.

## Profile questions

About them, not the project. Four questions.

**1. What does your business do, and what is your part in it?** One or two sentences, in their words. This is where the vocabulary of the whole project comes from, so write down the nouns they use. If they say "jobs" rather than "projects", the code says jobs.

**2. How much do you want to know about what I'm doing?**

- Just do it, tell me when it works
- Tell me what you did, in a line or two
- Teach me why, I want to understand the choices

Record the answer. Every later explanation is pitched at this level.

**3. Are you on a Mac or a Windows machine?** One word. It decides which commands you hand them, and it goes in the profile. `docs/your-computer.md` has the differences.

**4. What software do you already pay for?** Accounting, CRM, email, spreadsheets, scheduling. Two reasons: the new thing may need to talk to one of them, and sometimes the honest answer is that a tool they already own does this.

## Brief questions

About the project. Five questions.

**1. Who has this problem?** One person, named by role. "Me" is a fine answer. "Our customers" needs narrowing to one kind of customer.

**2. What do they do today, step by step?** Have them walk through the last time they did it. Concrete beats general: "last Tuesday I opened the spreadsheet, filtered by date, and emailed nine people" tells you far more than "we track follow-ups."

**3. What goes wrong?** Slow, forgotten, wrong, or expensive. This is the problem the software solves, and it belongs in the brief in their words.

**4. What does working look like?** How would they know, at the end of a week, that this helped? Push for something observable. "I stop chasing invoices on Sunday evening" is good. "Better visibility" is not.

**5. What is not in this?** Name three things it will deliberately not do. This is the most useful question in the interview. A first build that does one thing well beats one that half-does five.

## Routing

Then work `docs/decision-tree.md` in order.

## File templates

Fill every heading with a real answer. Delete nothing; leave nothing as a placeholder.

### `project/PROFILE.md`

```markdown
# Profile

## The business
[one or two sentences, their words, and their role in it]

## How much detail they want
[just do it | tell me what you did | teach me why]

## Machine
[Mac | Windows, and which shell]

## Tools they already pay for
- [tool, what it is for]
```

### `project/BRIEF.md`

```markdown
# Brief

## Who this is for
[one person, by role]

## The problem
[in their words, from the walkthrough]

## The one job this app does
[a single sentence]

## What working looks like
[something they could observe at the end of a week]

## Not in this
- [thing one]
- [thing two]
- [thing three]

## Level
Level [n].

Decided by: "[the exact question from the decision tree]"
Their answer: [what they said]

Costs [looked-up amount] per month to run properly, checked on [date].

## Live at
[address and date, once deployed]
```

### `project/SLICES.md`

```markdown
# Slices

One thing a person can do, start to finish. Smallest first.

| # | Slice | Status | Date |
| --- | --- | --- | --- |
| 1 | [so that <person> can <do thing> and see <result>] | planned | |
| 2 | [...] | planned | |
| 3 | [...] | planned | |
```

Status is `planned`, `built`, or `live`.

### `project/DECISIONS.md`

```markdown
# Decisions

Every choice made on this project, oldest first. New entries go at the bottom.
Nothing here gets edited after it is written.

---

## [date] Level [n]

**Question asked:** [the deciding question from the decision tree]

**Chosen:** Level [n]

**Why:** [one line]

**Rules out:** [what this level cannot do]
```

## How to ask

Two named options, and what each one means for their business.

Good:

> Would you rather see everything on one page and scroll, or click into each order for the detail? The first is faster once you know what you're looking for. The second stays readable when there are hundreds.

Not this:

> Should we use a modal or a route for the detail view?

When there is no genuine choice, do not invent one. Pick the sensible thing, say you picked it, and move on. A fake question wastes the attention you need for the real ones.
