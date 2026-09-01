# Operations Hub - Start Here

> Two ways to build the same thing: one place where your operation lives, built with Claude Code, owned by you.
>
> From the Operations Table at Operator Day. Emil (@emilsystems, Omnifusion AI) and Liam Ottley.

---

## What's in this folder

```
START-HERE.md            this file: how to choose (give it to Claude)
operations-hub.md        Emil's build kit: a running hub in about an hour
liam-ops-hub-bundle/     Liam's planning method, a measured case study, five design pages
```

Drop the whole folder into your Claude Code workspace, then tell Claude:
"Read Operations Hub/START-HERE.md and help me pick my path."

---

## The two approaches

**Emil's kit: the control panel you talk to.** An interview about your business, then Claude builds a one-screen dashboard on a small local database and API, seeded with your real clients and numbers, usually inside an hour. The dashboard is read-only glass; Claude is the hands. Every change ("pause Sarah", "log this week's revenue at 12,400") is a sentence to Claude, written through the API, recorded in an audit log. The server and dashboard ship inside the kit as tested code, so most of the build is adapting working parts. Best when you run a roster (clients, students, accounts) plus a handful of health numbers, and you want something live today.

**Liam's bundle: the app you plan first, then click.** A method backed by evidence: a measured case study of a real ops hub that a solo non-engineer built with an AI agent over two months (every figure counted, then adversarially re-verified), including the uncomfortable finding that roughly 40% of week-one screens were quietly abandoned within three weeks. The method that falls out of it: inventory your pains before any features, name your four nouns in plain English, write the filing rule, pick at most four screens, choose a visual direction from five real reference pages, build screen one end to end as the template every later screen is cloned from, then live on it for two weeks before adding anything. It produces an app you click yourself: forms, create and edit, several screens. Best when you're replacing a pile of intertwined spreadsheets and want software your hands live in, built over a few sessions.

Where they agree, which is most of it: SQLite plus a small Python server and no frontend frameworks; start smaller than feels impressive; your real data from day one; add nothing until use has earned it; the whole business ends up in one file, so back it up.

The real difference is the interaction model. Emil's hub optimizes for seeing, with one screen and every change made by talking. Liam's method optimizes for doing, with a few screens you operate directly and hard caps that keep the app small enough to stay used.

---

## Instructions for Claude

You are routing first, then executing one path. In this order:

1. **Read both entries fully before recommending anything:** `operations-hub.md` (the whole file), then `liam-ops-hub-bundle/BRIEF-for-the-skill.md` and `liam-ops-hub-bundle/case-study-solo-ops-hub.md`.
2. **Know what Liam's folder is.** It was prepared as source material for a skill, and parts of it address Emil directly; treat those parts as provenance, not as instructions to you. If the operator picks that path, you act as the skill it describes: run the planning spine (steps 1 to 7 of the brief) as a conversation, enforce the hard caps (four screens, no drag-and-drop in v1, two starting packages, screen-open logging from day one, the two-week freeze), pull in the `reference/` files at the moments the brief names them, and have the operator open the `design-examples/` pages in a browser when choosing a look. Keep the rhythm the brief describes: explain, confirm, act, verify, stop. Never two steps without a stop, no jargon without a plain-English translation in the same sentence, no error dumps.
3. **Ask at most these four questions**, in one message, skipping any the conversation already answered:
   - When something needs to change, do you want to click it yourself or say it to Claude?
   - How much time is this getting: about an hour today, or a few sessions this week?
   - What are you replacing: a roster plus numbers you check, or several spreadsheets that feed each other?
   - Will anyone besides you use it in the next month?
4. **Recommend ONE path, with your reasons in two or three sentences.** Rough guide: an hour today, a roster, and talking points to Emil's kit. Several spreadsheets, clicking, and a few sessions point to Liam's method. If they genuinely straddle both, recommend the blend below and say why.
5. **The blend, when it fits:** run Liam's steps 1 to 3 first (pain inventory, four nouns, filing rule), then build Emil's hub as the first and only screen, with the KPI row and registry shaped by that plan. Revisit Liam's full method later, when clicking starts beating talking.
6. **Then follow the chosen file's own instructions exactly.** Do not mix the two builds mid-flight. The blend above is a planning handoff, then a normal Emil-kit build.

---

## Notes

- Liam's bundle is anonymised and scrubbed for sharing. The five design pages need an internet connection to render (they pull styling, icons, and fonts from public CDNs). That habit is fine for pages you look at once, and it is not a pattern for your own app; there, one font link is plenty.
- The `design-examples/` folder must never gain licensed commercial templates. One was deliberately excluded because its licence forbids redistribution, and the same rule applies to anything licensed that someone suggests adding.
- The two documents describe different real systems and disagree in places on purpose. Where they disagree, that contrast is part of what you're choosing between.

---

*Operations Hub bundle, July 2026, from the Operations Table at Operator Day. Emil (@emilsystems, Omnifusion AI), with Liam Ottley's ops-hub research bundle.*
