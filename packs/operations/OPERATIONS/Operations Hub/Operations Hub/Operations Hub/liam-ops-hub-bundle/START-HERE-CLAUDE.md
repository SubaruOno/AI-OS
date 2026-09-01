# Start here (for Claude)

You're reading this because Emil dropped this folder into a workspace and asked you to help build
something from it. This doc tells you what it is, what to build, and what not to do. Read it fully
before opening anything else.

## What this folder is

A research bundle about **one real internal ops app**, built by a solo non-engineer operator with an
AI coding agent over two months. It was surveyed across eight dimensions, then every dimension was
adversarially verified, which corrected roughly 60 claims including three headline numbers. Every
figure in here was counted, not remembered.

It has been fully anonymised. No business, person, client, amount, host or address.

## What Emil is building

A **skill that walks a non-technical founder through planning and building their own ops hub** inside
their AIOS workspace: the internal app that replaces four spreadsheets and a pile of sticky notes.

The founder does not write code. They talk to you. So the skill is mostly instructions **to the
agent**, written as a conversation with the founder.

Two case studies live in that skill's `examples/` folder: the one in this bundle, and one Emil writes
about his own ops hub. `case-study-template.md` is the contract that keeps them the same shape.

## The one idea that has to survive

**This bundle is not a "copy this app" document. Treat it as one and you'll produce the exact failure
it exists to prevent.**

The surveyed app is well engineered. Nothing in ~150 findings showed it was actually *used*: no view
counters, no usage logging, no answer to "which of my 18 screens do I open". Meanwhile nearly every
clever mechanism in it is a scar from a failure mode that only exists at its shape (seven AI agent
sessions on one branch, a shared live database, a self-run server, six kinds of login, two SQL
dialects). A founder who copies those inherits machinery for problems they'll never have, spends
month one on rails instead of on the four screens that would change their week, and quits before the
thing earns a habit.

So: **the app you help a founder build has to survive their Tuesday, not survive many agents.**

## Read these, in this order

| Read | When |
|---|---|
| `BRIEF-for-the-skill.md` | **First, always.** The framing, the 11-step planning spine, the six gaps, the hard caps |
| `case-study-solo-ops-hub.md` | Next. The worked example, and the shape Emil's own must match |
| `case-study-template.md` | When Emil writes his own case study. Headings, length, voice, scrub checklist |
| `reference/zero-to-running.md` | Founder has nothing yet and needs a running app. Includes 4 verified landmines |
| `reference/tab-template.md` | Building the first screen. This is the file every later screen is cloned from |
| `reference/forms-and-modals.md` | Anything involving create, edit, delete or validation |
| `reference/agent-worker.md` | Founder wants a background AI job. The strongest pattern in the source app |
| `reference/design-directions.md` | Choosing a look, and keeping it coherent afterwards |
| `design-examples/*.html` | Show the founder five real pages so they can point at one |

## Hard constraints, not suggestions

- **Four screens. A hard cap, not a guideline.** The source app has 18 and cannot say which get used.
- **No drag-and-drop in v1.** The source app's to-do screen is 68KB across 1,323 lines with 86
  references to dragging, and it's the second-most-edited file in the whole app.
- **Two packages to start:** a web framework and a server. The source app's dependency list began at
  three and is now 121 lines.
- **Log screen opens on day one, and put the counts on the home screen.** The single most valuable
  thing the source app failed to do. A write path with no read screen is a feature that was never
  finished.
- **No optional screen** until the core four have four weeks of open-counts behind them.
- **Two-week freeze.** The founder lives on it before anything else gets added.

## Do not do these

- **Don't recommend the source app's deploy, auth, observability or second-database material.** It's
  an appendix, and the founder should be actively discouraged from reading it first. One environment
  switch that defaults to open is the entire auth story until a second human exists.
- **Don't let the planning flow produce an eighteen-screen app.** Cap it at four and say why.
- **Don't present the case study's numbers as targets.** 583 commits over two months is a cost
  anchor, and roughly half of that work shouldn't have been built.
- **Don't re-verify nothing.** If you cite a figure from this bundle in something new, and the source
  has moved on, re-count it. The original survey got the commit count wrong by a factor of two.
- **Never add `nexus/` back to `design-examples/`.** It was deliberately excluded: a purchased
  commercial template whose licence forbids redistributing it or sharing its files publicly. That's a
  property of the files, and no amount of scrubbing changes it. Same rule applies to anything else
  licensed that someone suggests bundling.
- **Don't copy the design pages' CDN habit into a founder's app.** Those pages pull a CSS framework,
  icons and fonts from public CDNs because they're artifacts to look at once. One font link is plenty
  in a real app.

## Match the install flow's shape

These founders learn one interaction pattern the morning they set up their workspace, from the
`/install` command: **explain, confirm, act, verify, celebrate, stop. Never two steps without a
stop.** Assume non-technical. No jargon without a plain-English translation in the same sentence.
**No error dumps, ever.** Name the problem simply, fix it together, or park it.

Use that same rhythm. Don't invent a second one.

## What to do first

1. Read `BRIEF-for-the-skill.md` end to end.
2. Skim `case-study-solo-ops-hub.md`, paying attention to sections 2 (the Tuesday test) and 5 (don't
   copy this). Those two carry the argument.
3. Ask Emil which half he's building now. The **planning half** (steps 1 to 7 of the spine, plus the
   design-direction flow) is self-contained and shippable. The **build half** (steps 8 to 11) leans
   on the four reference files and is more work.
4. If he's writing his own case study, open `case-study-template.md` and work through the headings
   with him. Run its scrub checklist before anything leaves his machine.

## One warning from doing this

The scrub on the design pages was done by script, and the script reported all five files clean. Then
someone opened one in a browser and a brand name was sitting in the headline that the regex had
missed. It happened twice, on two different files, including a real person's employer.

**If you scrub something, render it and read it.** A pattern match is necessary and nowhere near
sufficient.

---

*Prepared 2026-07-28. Figures verified against the source repository on that date. Re-check before
reusing them; an app this young changes shape monthly.*
