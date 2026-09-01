# Case study: a solo operator's ops hub

```
business    a one-person studio running multi-week client engagements on site, filmed, published after
app         an internal web app for the engagements, the trips, the people, the to-dos and the money
stack       Python + FastAPI + SQLite + plain JavaScript. No build step, no npm, no framework
built_by    one non-engineer operator working with an AI coding agent
age         2 months live at time of writing, used daily by one person
updated     2026-07-28
```

Everything below is measured from the real codebase, not remembered. Where the app does something
worth copying, it says so. Where it does something you should not copy, it says that louder, because
most of what's impressive in here exists to solve problems you don't have.

---

## 1. The app in one screen

- A **board of live client engagements**, one card each, with the current stage on the card.
- A **Today / Tomorrow / Coming up** to-do planner, which is the screen that actually gets opened.
- **People**: one searchable table holding leads, clients, crew and suppliers together.
- **Trips**: dated on-site blocks with people attached, costs attached, and a per-trip page.
- **Money in / money out**, with transactions taggable to the engagement that caused them.
- Roughly a dozen more tabs that grew on afterwards. That count is a warning, not a feature.

## 2. The Tuesday test

Read this section before any of the others, and be suspicious that it's the shortest one.

**The app has no usage tracking of any kind.** Every migration and every route was checked for a
view counter, a last-opened stamp, a page-view table, anything. There is one unrelated counter and
nothing else. There's no logging hook on route changes either. So after two months and 98 schema
migrations, this app **cannot answer which of its 18 tabs get opened**, and neither can its owner
beyond memory.

What can be measured is which screens kept getting worked on, and that's damning enough. **Thirteen
screens were built in the first four days.** Eight are still being edited two months later, with 11
to 35 commits each. The other five have **four commits or fewer in their entire life**, four of them
went untouched after 20 June, and one hasn't been edited since the day after it was created.

None of the five was ever deleted. They're all still in the navigation.

So the honest headline is not "look what one person built in two months". It's: **nearly 40% of what
you build in week one is abandoned within three weeks, you can't tell which 40% at the time, and
without an open-counter you never find out.** The cheapest thing this app should have done on day one,
and didn't, is log `(screen, timestamp)` on every screen open and put the four-week counts on the home
page, where they'd be impossible to ignore.

One more piece of the same shape: there's a table holding 40 rows of AI-generated improvement
suggestions, and no screen anywhere renders it. The only way to read those 40 rows is a command-line
verb. A write path with no read screen is a feature that was never finished, and it's easy to build
dozens of them without noticing.

## 3. The shape that forced everything

Four facts about this app explain most of its complexity. If your facts differ, most of its
mechanisms are dead weight for you.

| Fact | What it forced |
|---|---|
| **One human uses it.** Not a team. | Six kinds of login principal, row-level database security, role-scoped navigation. Months of work protecting one person from themselves. |
| **Up to seven AI agent sessions edit the code at once**, on one branch, against one live database. | A commit-path guard hook, an append-only migrations rule, one-file-per-feature routing, four separate concurrency mechanisms. |
| **It moved from a laptop file to a hosted database** partway through. | Two parallel migration lineages (98 files and 96 more), a dialect translator, a row-shim, a second frozen schema file kept only to satisfy one test. |
| **It runs on a private cloud server** the owner administers. | Containers, a deploy platform, a private mesh network, firewall rules, secret distribution across eight destinations. |

None of those four facts is likely to be true of you on day one. Two of them may never be.

## 4. What we'd build again

Nine things. Each is small, each survived contact with real use, and each is written here at the size
a solo founder should build it, not the size it grew to.

**One `people` table with a `kind` column.** Not Contacts plus Customers plus Team plus Leads. One
table, one column holding `lead` / `client` / `crew` / `supplier`. Someone who starts as a lead and
becomes a client changes one word and keeps the same row, so every task and invoice pointing at them
stays pointed at them. This is the highest-payoff decision in the whole data model. Index the column.

**Four nouns written as four English sentences before any schema.** The app's own data-model doc opens
with exactly that and nothing else: who the humans are, what the short dated thing is, what the long
delivered thing is, what a to-do is. It grew from 18 tables to about a hundred and **those four
sentences never changed.** That's the number that should reassure you. When a new feature shows up,
the first question is which of your four nouns it hangs off, not what fifth noun you need.

**The filing rule, decided before the table exists.** A to-do can belong to an engagement, or a
client, or a loose area of the business. Pick a fixed precedence (engagement beats client beats area
beats inbox), make every write path null the lower tags when a higher one is set, and partition your
reads with the same order. Then every to-do appears in exactly one list. The app enforces this in
four separate write paths, which is the real cost: **an agent auditing the code found three of the
four.** Don't verify it by reading code. File the same to-do from every screen that can file one and
confirm it shows up once.

**One request per detail page.** Open an engagement, and one endpoint returns the record plus every
attached list plus the derived totals, as a single JSON object. Four plain SELECTs, one response, one
render. The default an AI agent reaches for is six parallel fetches and six spinners, and unwinding
that later is expensive.

**Derived, not stored.** If a status can be computed from the record plus its related rows plus
today's date, compute it every time you display it. It can then never go stale. One ceiling, because
this app blew through it: if the derivation needs more than about ten lines or more than three
inputs, store the fact instead. The real finance-status function here is a 43-line six-stage
precedence ladder fed by a three-query assembler, and that's past the point where a founder should
follow.

**One `get_db()` and nothing else touches the database.** A context manager that opens the
connection, sets three settings, hands it over, commits or rolls back, closes. The three settings
matter: a busy timeout so a second process waits instead of erroring, write-ahead logging so reading
doesn't block writing, and foreign keys ON because the database ships with them OFF. This app shipped
without the first two and had to add them five days later, the moment a second process appeared.

**One file per feature, on both sides.** One backend file per feature holding its own routes, one
frontend file per screen. Nothing shared to edit when you add a feature. This is the structural
reason an AI agent can work on this app without breaking a screen it wasn't asked to touch, and it's
the single most useful thing here for anyone building with agents. Worth knowing the real scale: the
app's routes lived in one file that hit 1,364 lines four days in, and got split **into 11 files, on
the same day**. Not 59. Eleven is a number you can picture.

**Append-only migrations, applied on boot.** A folder of `.sql` files named by timestamp. On start,
the app runs any it hasn't run and records the filename. The rule is absolute: a schema change is a
**new file**, never an edit to one that already ran. Editing one means your machine and every other
copy silently disagree about what the database looks like.

**The AI agent is denied every write.** The background agent that researches and drafts has no write
tools at all, and any shell command containing a SQL write is blocked by a pattern check plus a
second hook using the same rule. The agent returns JSON. The worker does every database write. This
one boundary is why a bad AI run costs you a bad draft you reject, instead of a corrupted customer
record. Everything else downstream only works because of it.

## 5. Don't copy this

| Mechanism | The failure it exists for | The shape that causes that failure | What you do instead |
|---|---|---|---|
| Two parallel migration lineages, 194 files, a dialect translator, a row-shim | Same code has to run on two different databases | A mid-life move from a local file to a hosted database | Pick one database and stay on it. Delete the second-dialect branch entirely |
| A second frozen schema file with 89 table definitions | A test compares two ways of building the schema | Historical duplication nobody removed | Migrations only. One source of truth |
| A hard guard that refuses to open the default database file | Writes leaking into a phantom local copy | A laptop that used to be the server and is now a client | Nothing. Your database is one file next to your app |
| Six login principal kinds, row-level security, role-scoped nav, token allowlists | Different humans and agents needing different data | Multiple people plus external agent consumers | One environment switch that defaults to open. Add nothing until a second human exists |
| Deploy chain: containers, a deploy platform, a private mesh, firewall rules, uid matching | Running a public-ish service on your own server | Self-administered infrastructure | A managed host with a login, later. Localhost, now |
| A 907-line observability subsystem, traces, uptime probes, incidents | Knowing why a thing broke at 3am | An always-on service with automations | One `/healthz` route, about nine lines |
| Undo/redo with two stacks, a browser mirror, a journal table and a nightly pruner | Destructive edits with no recovery | A dense multi-select UI | A confirm dialog that counts what it's about to delete, out loud |
| A 108-entry component ledger and a six-check design audit command | Nobody remembering what components exist | 108 components across 22 categories | Three design files. Add the ledger past 40 components, never before |
| A commit-path guard hook | Parallel agent sessions clobbering each other's files | Many agent tabs, one branch, one checkout | Commit each working piece the moment it works. Don't run two sessions on one screen |
| Hand-rolled dropdowns, icon tinting, pixel-geometry layout tests | Visual polish beyond what the browser gives | Time and taste | Native form controls. They're fine |
| 18 tabs | Growth with no signal about what's used | No usage tracking | **Four tabs. Hard cap.** |

**Keep no matter what, whatever your shape:** one `get_db()`; one file per feature; append-only
migrations; the throwaway-database environment switch; a backup you have restored once.

## 6. What it actually cost

Measured, not estimated, as of 2026-07-28:

- **583 commits** touching the app, over **two months** (29 May to 28 July).
- **14,313 lines** of backend route code across 59 files.
- **23,388 lines** of frontend JavaScript across 38 files.
- **194 migration files** (98 for the first database, 96 for the second).
- **96 distinct tables.** 18 navigation tabs. 236 test files.
- A dependency file of 121 lines holding 31 packages, which started as **three**.

Built by one operator who does not write code professionally, working with an AI coding agent, most
days, for two months. Four working tabs is a few sessions. This is what two months of near-daily work
looks like, and about half of it should not have been built.

## 7. Four things we'd do differently

1. **Log screen opens on day one**, and put the counts where you'll see them. Without that, you're
   guessing about your own app forever, which is exactly what happened here.
2. **Never seed real data from a tracked script.** This app's setup script contains real client
   names, real crew, real destinations and real amounts, committed to the repository. Seed fictional
   rows. Type your real ones into the app like a user.
3. **Fix the timezone rule before the second screen.** The server stamps times with the database's
   own naive UTC string, which carries no timezone marker, and the browser parses that string as
   local time. Anyone not on UTC gets "completed today" and due-date rollover wrong by up to a day.
   Store timestamps as ISO-8601 with a trailing `Z`, store plain dates as `YYYY-MM-DD` text with no
   time at all, and convert exactly once, at display.
4. **Render the navigation from one list.** This app keeps a desktop nav and a mobile nav as two
   hand-written blocks. They have already drifted: one tab is live on desktop and **unreachable from
   the phone right now**, and nothing anywhere reports it. One array, both menus generated from it.

---

*Written from a direct read of the codebase, with every figure re-verified against the repository on
2026-07-28. Names, clients, amounts, hosts and addresses are removed throughout. Re-verify the
numbers before reusing them; an app this young changes shape monthly.*
