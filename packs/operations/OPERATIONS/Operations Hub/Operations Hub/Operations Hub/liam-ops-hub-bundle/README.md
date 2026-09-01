# Ops hub case study bundle

For Emil, building the "plan and build your own ops hub" skill for the Operations pack.
Prepared 2026-07-28.

**Point your Claude at `START-HERE-CLAUDE.md` first.** It's the routing doc: what this is, what to
build, what not to do, and which file to open when.

## What's here

```
START-HERE-CLAUDE.md        give this to Claude first. Routing + the non-negotiables
BRIEF-for-the-skill.md      read this first (you). The framing, the planning spine, the gaps
case-study-solo-ops-hub.md  the example: a real solo-built ops hub, fully anonymised
case-study-template.md      the contract, so your own example matches this one
reference/
  zero-to-running.md        empty folder to a page in a browser. Nothing covered this
  tab-template.md           the one screen every later screen is cloned from
  forms-and-modals.md       create and edit. The bulk of an ops app, missed by everything
  agent-worker.md           background AI jobs. The pattern this app has genuinely nailed
  design-directions.md      six directions to pick from, and the three-file discipline
design-examples/            five scrubbed, working reference pages, one per direction
```

Drop it in as `.claude/skills/<your-skill>/examples/` plus `references/`. The AIOS template has no
`packs/` folder and doesn't need one: skills live at `.claude/skills/<name>/`, and apps the founder
builds live at `apps/`.

## Read it in this order

1. **`BRIEF-for-the-skill.md`.** Twelve minutes. It contains the one argument that changes what the
   skill should be, which is that the source app's engineering quality is not evidence that the app
   gets used, and nearly every clever mechanism in it is a scar from a problem your founders won't
   have.
2. **`case-study-solo-ops-hub.md`.** The example itself, and the shape your own should match.
3. **The reference files**, as you need them. They exist because those five topics had no material
   anywhere and are exactly what a beginner hits in the first two sessions.

## Where this came from

An eight-dimension survey of a real, live, two-month-old ops hub (583 commits, 96 tables, 18 screens,
one non-engineer operator plus an AI agent), followed by an adversarial verification pass on every
dimension. The verification changed a lot: it corrected around 60 specific claims, including three of
the headline numbers, and it caught several confidently-stated findings that were simply false. Where
this bundle states a figure, it was counted rather than recalled.

## Three things to know

**Everything is anonymised.** No business, person, client, sponsor, amount, host or address. The
technical detail is exact, because none of it identifies anyone. If you spot something that slipped
through, it's a bug, tell Liam.

**The design examples are scrubbed copies, and one set was excluded.** Five working reference pages
are in `design-examples/`, with real people, brands, a phone number, social profiles, an analytics tag
and nine third-party hosted images all removed. A purchased commercial template was left out
entirely: its licence forbids redistributing the template or sharing its files publicly, which a
scrub can't fix. Details in `design-examples/README.md`.

**The build half of the skill can't be finished tonight.** The honest deliverable for tomorrow is the
planning half plus the design-direction flow. The reference files here already carry the build half's
content, so finishing it later is writing, not research.
