# Brief: the "plan and build your own ops hub" skill

For Emil. Written 2026-07-28, the night before the Operator Day.

This is the thinking behind the case study sitting next to it, and the part that matters more. The
case study is raw material. This is the argument for how to use it.

---

## What the skill has to do

A non-technical founder finishes the morning install with a working AIOS workspace. In the afternoon
they sit at the Operations table and want an internal app for their business: the thing that replaces
four spreadsheets and the sticky notes. The skill walks them from "I have a mess" to a running app
with three or four screens they actually open.

They don't write code. They talk to an agent. The skill is mostly instructions **to the agent**, wearing
the clothes of a conversation with the founder.

## The inversion, which is the whole point

A deep survey of a real, working, solo-built ops hub produced about 150 findings. Every one of them
measured that codebase by how well it's engineered. Not one of them contained evidence the app is
**used**. That absence turned out to be the finding.

Nearly every impressive mechanism in that codebase is a scar from a failure mode that only exists at
its particular shape: seven AI agent sessions editing one branch at once, a shared live database, a
self-administered server, six kinds of login, two SQL dialects. A founder who copies the mechanisms
inherits machinery guarding against problems they'll never have. They spend month one on rails
instead of on the four screens that would change their week, and they quit before the thing earns a
habit.

So the skill optimises for something different from what the source app optimises for. The source app
survives contact with many agents. **The skill has to produce an app that survives contact with a
founder's Tuesday.**

In practice that means: fewer tabs, a create/edit form that actually works, a path for the
spreadsheet they already have, and a gate that stops them adding anything for two weeks. All the
concurrency, deploy, auth and second-database material becomes an appendix they're actively told not
to read first.

## Two facts from the source app that should shape the skill

**It cannot tell you which of its 18 tabs get opened.** No view counters, no last-opened stamps, no
route logging. Two months, 98 schema migrations, and no answer to the most basic question about its
own value. Make screen-open logging a day-one step, and make the counts visible on the home screen,
or the founder will build the same blind app.

**Thirteen screens were built in the first four days, and five were abandoned within three weeks.**
Those five have four commits or fewer in their whole life, and not one of them was ever removed from
the navigation. The instinct is "whatever you build first is the app". The evidence is messier: most
of week one survives, a large minority dies quietly, you can't tell which at the time, and dead
screens accumulate because deleting them is nobody's job. That argues for building fewer screens more
slowly, and letting open-counts decide what earns a second one.

## Mirror the install flow, don't invent a new shape

These founders learn one interaction pattern that morning, from the `/install` command: explain,
confirm, act, verify, celebrate, stop. Never two steps without a stop. Assume non-technical. No
jargon without a plain-English translation in the same sentence. **No error dumps, ever.**

Use the same shape. A founder who just spent 45 minutes learning that rhythm shouldn't have to learn
a second one after lunch.

## The planning spine

Eleven steps. Steps 1 and 8 have no supporting material in any codebase and have to be written from
scratch; they're also the two that decide whether the app gets used.

1. **Pain inventory, not features.** What do you check every morning, who do you chase, what's in
   which spreadsheet, what got dropped last month. Nothing exists for this step anywhere. It's the
   one that decides whether any of the rest matters.
2. **Name your four nouns**, as four English sentences, before any schema. Who the humans are, what
   the short dated thing is, what the long delivered thing is, what a to-do is. Include *why* two
   things are separate, because that's what an agent guesses wrong.
3. **Write the filing rule and the vocabularies before any table.** Where does a to-do appear, and
   appear only once. Then split every choice-list into "this will change" (plain text) and "this must
   never change" (a hard database constraint). Lean hard toward plain text; the constraint is
   expensive to widen later.
4. **Pick three or four screens from the menu**, and for each name the one screen that must exist.
   Start with the Today/Tomorrow planner: it's the smallest and the most opened.
5. **List what's derived, not stored.** Every stored status is a future backfill.
6. **Safety rails before the first feature.** Throwaway-database switch, a migrations folder with one
   rule, a backup you've restored once, and commit each working piece the moment it works.
7. **Visual direction:** four to six full-page prototypes of the *same* screen, pick one, iterate
   once, then extract three files. Comes after the data model, because you can't mock a screen for
   entities you haven't named. See the design section below.
8. **Build screen one end to end as the template:** list, detail, create form, edit form, empty
   state, error state. Every later screen is cloned from this file. It has to be written; no existing
   file is safe to point at.
9. **Clone for screens two to four.**
10. **Live on it for two weeks before adding anything.**
11. **Auth and a second human, only when a second human exists.**

## The six gaps, and why they matter more than the survey material

The survey covered the codebase well and missed everything a beginner hits first. These are written
up as reference files in this bundle because none of them existed anywhere.

- **Zero to running.** Completely uncovered. Three landmines verified by hand: the AIOS template's own
  dependency file has no web framework in it at all, so the recommended stack isn't installable as
  shipped; the source app's launch script hardcodes one machine's absolute path; and its database
  path is resolved by counting parent directories, which silently encodes how deep the app sits.
  There's also a guard in that file that hard-fails on the default path, so a naive copy won't boot.
- **Forms and modals.** The bulk of a real ops app, and absent from every survey fragment. Day one is
  "add a person". Day two is "change this person". No template, no validation UX, no answer to what
  the user sees when a save fails.
- **Search.** Zero search endpoints across 59 route files, 18 tabs and 96 tables. A founder with 300
  contacts asks "where do I type a name" in week one.
- **Getting existing data in.** Exports exist; there's no import anywhere. Meanwhile the source app's
  setup script seeds real client names and amounts from a tracked file. Importing the spreadsheet
  they already have *is* the real first session.
- **Timezones and money.** The two data bugs every ops app gets. Rules are in the reference files.
- **Backup.** The whole business ends up in one file on a laptop. Nothing in the source material
  addresses that shape.

## Hard caps to build into the skill

- **Four screens.** Not a guideline. The source app has 18 and can't tell you which get used.
- **No drag-and-drop in the first version.** The source app's to-do file is 68KB across 1,323 lines
  with 86 references to dragging. It's the second-most-edited file in the app.
- **Two packages** to start: a web framework and a server. The source app's dependency list started
  at three and is now 121 lines. Every later line should carry a comment saying which feature forced
  it, which is a habit worth teaching on its own.
- **No optional screen** until the core four have four weeks of open-counts behind them.

## The design half

The founder picks from six directions, five of which ship as **real working reference pages** in
`design-examples/`, scrubbed for redistribution. What came out of them: real people's names, a phone
number, Instagram and LinkedIn profiles, real company and product brands, a live Google Analytics
measurement tag, and nine images hosted on third-party services including someone else's storage
bucket. No credentials were present, which was checked rather than assumed.

Two things to know:

1. **A purchased commercial template was excluded entirely.** Its licence permits use in your own
   products and client work but forbids redistributing the template or sharing its files publicly.
   That's a property of the files, so scrubbing doesn't touch it. Don't add it back.
2. **The pages still need a network connection**, because they pull a CSS framework, icons and fonts
   from public CDNs. Fine for choosing a look. Say plainly in the skill that it's not a pattern to
   copy into the founder's own app, where one font link is enough.

The process around the menu matters more than the menu, and it's in the same file: write the
one-sentence aesthetic *before* the prototypes, not after; prototypes are self-contained HTML with
real content pasted in as static markup, not wired to the database; extract exactly three files
afterward. See `reference/design-directions.md`.

## How the examples folder works

Two case studies, from two different businesses, in the same shape. One from the studio described in
`case-study-solo-ops-hub.md`, one from yours. `case-study-template.md` is the contract: same
headings, same length target, same scrub rules, same voice (second person, to the founder).

Keep the coordination light. Two examples don't need a catalog file, a registry and a template. One
template and a four-line pointer in the skill body is enough. Add a catalog at the fifth example.

The one section neither of us should skip is **the Tuesday test**: how often it gets opened, by whom,
what makes them open it instead of a spreadsheet, and which screens were built and are never opened.
Every precedent document in this space describes how a thing was built. None says whether it's used.
That's the section a founder actually needs, and it's the one that's easiest to leave out because it's
unflattering.

## What can't be done tonight

The build half of this skill can't be written and tested before tomorrow. The honest deliverable for
the room is **the planning half (steps 1 to 7) plus the design-direction flow**, with the build half
following after. The reference files here cover the build half's content, so it's a matter of turning
them into guided steps rather than research.
