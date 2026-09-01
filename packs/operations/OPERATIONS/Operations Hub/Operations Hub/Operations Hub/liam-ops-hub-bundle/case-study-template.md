# Case study template

*Updated 2026-07-28.*

Fill this in for your own ops hub. Two case studies only help a founder if they're the same shape,
because the skill's instruction is "read the one whose shape matches yours", and that comparison only
works if both files answer the same questions in the same order.

Save as `examples/<business>-ops-hub.md`. Business-named, flat file, **never numbered**. Numbering
reads as a ranking and forces a rename the moment a third one lands.

---

## Rules

**Length:** 150 to 250 lines. Long enough for the story, short enough that an agent loads it on
demand without thinking about it.

**Voice:** second person, to the founder. "You'll hit this in week one", not "the founder will
encounter". Both files have to read as peers, and register is what breaks that first.

**Never use a filesystem path.** Refer to things by role: "the app's single migrations folder", "the
connection helper". Paths contain usernames and point into private repositories nobody can open.

**Code excerpts cap at 25 lines**, and say what they're a slice of.

**Numbers must be measured, not remembered.** Run the count. The survey that produced the first case
study got the commit count wrong by a factor of two, the test-file count wrong by 50, and the table
count wrong by seven, all from memory rather than counting.

**Date it, and re-verify before reuse.** An app this young changes shape monthly.

## The scrub checklist

Run all of these before you send it. Nothing on this list belongs in a file that gets passed around.

- [ ] No client, customer or staff names. Not even first names in code comments.
- [ ] No revenue, fees, invoice numbers, account balances or transaction amounts.
- [ ] No legal identifiers: tax numbers, company registration numbers, addresses.
- [ ] No API keys, tokens or credentials. Variable *names* are fine; values never are.
- [ ] No hostnames, IP addresses or private network addresses.
- [ ] No email addresses, including in default values inside schema files.
- [ ] No filesystem paths containing a username.
- [ ] No third-party material you don't have the right to redistribute.

The two that actually catch people: **real names hiding in code comments and in seed data**, and
**email addresses baked in as database defaults**. Both were found in the first case study's source
app, in files that looked completely innocuous.

## The sections, in this order

Copy these headings verbatim.

**Header block.** Six lines, fenced: `business` (one line, what it sells), `app` (what the internal
app actually runs), `stack`, `built_by`, `age` (months live), `updated` (date).

**1. The app in one screen.** Five to eight bullets of the real surfaces. No architecture. What a
person sees when they open it.

**2. The Tuesday test.** *The one section nobody can skip.* How often it gets opened, by whom, what
makes them open it instead of a spreadsheet, and which screens were built and are never opened. Every
document in this space describes how a thing was built and none says whether it's used. If you have
no usage data, say that plainly, because that's a finding too.

**3. The shape that forced everything.** Four to six facts about your situation, each paired with
what it forced you to build. How many humans use it, where it runs, how many agents write to it, how
many databases it's been through. This is what lets a reader tell whether your answers apply to them.

**4. What we'd build again.** Five to eight patterns. Each gets a one-line why and the *smallest*
version of it, not the version you ended up with.

**5. Don't copy this.** A four-column table: mechanism, the failure it exists for, the shape that
causes that failure, what a solo founder does instead. The fourth column is the whole point. Close it
with a "keep no matter what" line: the two or three things that survive every shape.

**6. What it actually cost.** Measured. Commits, calendar span, lines, files, tables, screens. Plus
one honest sentence about how much of it shouldn't have been built.

**7. What we'd do differently.** Three to five items, specific enough to act on.

## Two things worth knowing before you start

**Section 5 will be longer than you expect**, probably 25 to 40 lines on its own. That's correct.
It's the section doing the real work, because the reader's instinct is to copy everything.

**Section 2 is the one you'll want to soften.** Don't. A case study that only says what got built is
the exact failure the skill exists to prevent.
