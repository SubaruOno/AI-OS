# Design: picking a direction and keeping it

*Updated 2026-07-28.*

Two halves. The bake-off, which is how you choose a look. And the three files, which are how the look
survives two months of an AI agent editing your app.

**Five worked reference pages ship with this, in `../design-examples/`.** They're scrubbed copies of
real designs: no real people, companies, phone numbers, social profiles, analytics tags or
third-party hosted images. See the README in that folder for exactly what was removed and what was
left out entirely.

They still load a CSS framework, an icon set and web fonts from public CDNs, so **they need a network
connection to render properly.** That's fine for looking at them. It's not a pattern to copy into
your own app, where one font link is plenty.

---

## Part 1: the bake-off

**Write the one sentence first.** Before any prototype, answer in plain English: what should this
look like? "Quiet, dense, and boring on purpose, like an airline crew terminal." "Warm and papery,
closer to a notebook than a dashboard." That sentence is the input to the prototypes, not a summary
you write afterward. The reference app wrote it at extraction time, from an already-chosen mockup,
and it would have gotten better mockups by writing it first.

**Build the app before you design it.** One ugly working screen with real records on it. A prototype
full of placeholder text can't tell you whether a layout survives your actual row counts, your
longest client name, or an empty state. In the reference app the working screen came first and the
first prototype followed **about an hour later**.

**Then ask for four to six full-page prototypes of the same screen.** One self-contained HTML file
each, no shared CSS, deliberately distinct. Give them names so you can talk about them. Then one
gallery page showing all of them side by side in scaled-down frames, because comparing six things on
one screen is the entire point.

They are **not wired to your database.** They're static HTML with your real content pasted in as
markup. Say that to your agent explicitly or you'll get six half-built apps instead of six pictures.

Then point at one. You can't describe a look well enough in words to get one you like, but you can
pick one out of six in thirty seconds, and you can say "that one, but the header from the third one".

**One refinement round.** Have the agent rebuild the winner as the real app shell: nav, buttons, a
form, a modal, an empty state, mobile width. Then have it screenshot desktop and mobile and critique
its own work against your sentence. Two lenses catch most of what a static mockup hides:

- Is any two different kinds of information accidentally sharing a colour?
- Does anything break at phone width, or at your longest real string?

Overrule the critic when it's wrong. It's a second opinion, not a boss.

**If you don't like the result, that's normal.** The recovery move is to rebuild the winning
direction as a fresh prototype rather than patching the extracted CSS. Patching is how you end up
with something that's neither.

## Part 2: six directions to choose between

Hand these to your agent as the brief for the bake-off. All six are picked for dense internal tools,
where you're reading rows rather than being sold to.

Five of them ship with a **real, full, working reference page** in `../design-examples/`. Open those
in a browser first. Looking at five finished pages for two minutes beats reading six descriptions.

| # | Direction | Reference page | Pick it when |
|---|---|---|---|
| 1 | Quiet Swiss | `swiss-light.html` | Default choice. You want it calm and out of the way |
| 2 | Terminal dark | `terminal-dark.html` | You stare at it all day and want density |
| 3 | Control panel | `control-panel.html` | Lots of states, boards, things that look like they do something |
| 4 | Product dark | `product-dark.html` | You want it to feel like a polished product, not a tool |
| 5 | High contrast bold | `bold-contrast.html` | Mostly on a phone, or you want the opposite of grey |
| 6 | Paper | *(none, describe it)* | The app is mostly reading and writing, not scanning numbers |

**1. Quiet Swiss.** Light. Near-white background, one strong ink colour for text, a single accent used
sparingly and only ever to mean something. Generous whitespace, tight left-aligned grid, small
uppercase mono labels above values. No card shadows, hairline borders only. One neutral grotesk, two
weights. *Best default for most ops apps, and closest to what the reference app landed on.*

**2. Terminal dark.** Near-black background, one bright accent, monospace for all numbers and
identifiers, sans for prose. Dense rows, minimal padding, thin bright borders on focus. Feels fast and
fits a lot on screen.

**3. Control panel.** Mid-dark greys with clear panel edges, chunky status chips, colour used
systematically to encode state rather than decorate. Segmented controls instead of dropdowns. The
biggest of the five reference pages by a distance, so skim it rather than reading it.

**4. Product dark.** Dark, but softer than the terminal look: rounded cards, gradients, generous
spacing, a marketing-grade polish applied to an internal tool. *The trap here is that it's built for
selling, so watch that it still works at 200 rows.*

**5. High contrast bold.** White background, heavy black type, one saturated accent at full strength,
large numerals, flat blocks of colour, no gradients. Loud and legible.

**6. Paper.** Warm off-white, soft serif headings, sans body, rounded corners, generous line height,
almost no borders. Reads like a notebook. No reference page bundled, so describe it to your agent
from this paragraph. *Good if a dashboard aesthetic would put you off opening the thing at all.*

For each prototype, the agent should produce the full page plus a short note listing the palette, the
fonts, and the two or three signature moves that make it recognisable. That note is what you'll
actually reuse.

**Fonts:** one font for everything, loaded from one place, and let the agent wire it. The reference
app runs four faces across two sources, which is far more than you need and will read as required if
you look at it.

## Part 3: the three files

Once you've picked, say **"extract the design system from this"** and accept exactly three files.

| File | What's in it | How often you'll touch it |
|---|---|---|
| `tokens.css` | Every colour, spacing step, radius, shadow and type size, as a CSS variable | Rarely |
| `components.css` | Every reusable class, built **only** from those variables. Zero raw colour values | Constantly |
| `DESIGN.md` | The spec both you and the agent read | Occasionally |

Real ratio from the reference app over two months: 18 commits to tokens, **81** to components, 47 to
the spec. So tokens are stable, not frozen. Its token file also grew from 122 variables to 167 in
that time, which is a 37% increase. Plan on revisiting it about a fifth as often as your components.

Refuse anything else at this stage. No render-helper library, no component ledger, no style-guide
page. **Your app is the style guide.**

**Name tokens by role, not by colour.** `--ink-600` and `--accent`, not `--blue-500`, because the day
you change the accent you don't want to rename everything. Honest counter-texture: the reference app
states this rule and then carries two dozen hue-named tokens for its chip palettes, so it's a rule
that bends under pressure. Know that going in and decide deliberately where you'll allow it.

**`DESIGN.md` opens with one sentence and closes with DON'Ts.** The DON'Ts are what stop drift six
weeks later. Don't invent new colour values. Don't add a new coloured chip family. Don't fill large
surfaces with colour. The reference app's version runs 10 DOs and 8 DON'Ts.

## Part 4: keeping it

**Put four hard rules in the file your agent auto-loads for this app.** Not in the design system, in
the agent's instructions, which is the difference between a document and a constraint:

```markdown
- Read DESIGN.md before writing any markup.
- Colours only via var(--token). If the colour you need isn't a token, add the token first.
- Check components.css for an existing class before writing new CSS.
- Never restyle a component ad hoc. Change it in components.css so every use moves together.
```

**The CANDIDATE rule.** When you need a pattern that doesn't exist, write it inline with a comment:
`/* CANDIDATE: promote when a second screen needs this */`. The second time you need it, move it into
`components.css`. This kills the hardest ongoing question, which is whether something is a component
yet. Watch the failure mode though: the reference app has one helper function copy-pasted into two
files instead of promoted, so the rule only works if someone looks for the marker.

**One check, run by the agent, not typed by you.** "Report every raw colour value anywhere outside
the design-system folder." Expect zero. That single question is the load-bearing part of any design
audit, and the reference app still answers zero across 1.4MB of app code after two months and a
hundred commits, with no linter and no automated gate.

**Every later mockup starts by linking `tokens.css`.** Once the palette is locked, you keep exploring
layout forever and you stop reopening the aesthetic by accident. The tell that it's being reopened:
a new mockup contains raw colour values. The reference app only started doing this six weeks late,
and only three of its seven post-lock prototypes link the real tokens, which is exactly why its
palette kept moving. When a mockup you like disagrees with the app, the ruling is: **the mockup
supplies the layout, the design system supplies the colours.**

**After real UI work, screenshot and critique.** Desktop and mobile, against `DESIGN.md`, fix,
repeat. Stop when two consecutive rounds find nothing. That's what makes an app look considered, and
it needs no tooling beyond a browser.

## If you already have five screens in mixed states

The common case, and the bake-off assumes you're starting today. The retrofit: grow the system until
it covers everything you already need, cut every screen over in **one pass**, then delete the old CSS
in the same change. A gradual migration leaves two systems live and you'll be able to tell, forever.

## When to add more machinery

At roughly **40 components**. Below that, a component ledger and a multi-check audit command are
overhead with no payoff. The reference app generated a ledger on day one at 29 entries and it sat
decorative until the app grew past 40, when 22 categories meant nobody could remember what existed.
Your internal ops app will most likely land around 15 and never need either.

**One warning about forking.** If you copy this design system into a second app, it starts diverging
immediately and nothing tells you. The reference app's second product still carries the first app's
name in the title line of its design spec five weeks on, and the two token files already differ by
112 lines. Fork deliberately, or share one file properly. Don't drift.
