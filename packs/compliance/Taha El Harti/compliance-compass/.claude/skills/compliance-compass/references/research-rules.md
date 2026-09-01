# Research rules — when and how the engine searches

## When search fires (these six situations — and only these)

1. **Launch website research** — the user gave a URL: fetch/search the site, build the
   profile guess, then identity-check before trusting any of it.
2. **Business type identified** — search "what regulations apply to <this kind of
   business>" (plus jurisdiction). Merge findings into the coverage checklist.
3. **Non-anchor jurisdiction** — any country without a file in `regimes/` enters the
   picture → live-research it (protocol below).
4. **Volatile value needed** — any fine amount, threshold, deadline, or cost figure you're
   about to rely on or quote, if its `last_verified` is older than 6 months OR it's listed
   under `volatile:` in its regime file and will appear in the report.
5. **Unrecognized reference** — a framework, law, or document type in the user's files or
   answers that you don't recognize.
6. **Self-uncertainty** — you are not sure whether a rule applies, what it currently
   requires, or whether your knowledge is current. Search BEFORE speaking or concluding —
   including for your own internal exhaustiveness-loop questions, and **including "that's
   fine / not required" claims**: a green assertion is a compliance conclusion and needs
   the same verification as a red one. Never resolve a compliance question from memory
   alone.

Search failure or no search available: say so plainly, label the affected statements
"as of <last_verified date>, unverified", and log the item as UNKNOWN if it's load-bearing.

**Never search to fact-check the user's statements about their own business.**

## Staleness discipline

- Every regime file carries `last_verified`, `volatile:`, and `flip_dates:`.
- Check `flip_dates` whenever you load a regime file — a passed flip date means the file's
  content may be outdated: verify live before relying on it, and tell the user the file
  needs an update.
- Numbers quoted to the user or destined for the report always carry their verification
  date ("up to €20M or 4% of global revenue — verified July 2026").
- You may OFFER to update a regime file after live research ("Want me to save this to your
  regime library? I'll mark it as unreviewed live research."). Never rewrite library files
  silently.

## Live-research protocol (jurisdictions/regimes with no file)

Use `regimes/_SCHEMA.md` as the checklist — answer each schema section from current
sources: triggers, enforcer, penalties + enforcement reality, thresholds/exemptions, gap
checks, first steps. Shortcuts:
- Most national privacy laws follow the GDPR skeleton — start from
  `regimes/gdpr-family-pattern.md`, which also lists the known deviants (China: transfers
  dominate; India: consent managers, phased enforceability). Never apply the skeleton to a
  deviant without checking its deviations.
- Prefer regulator/primary sources; date every fact; label confidence honestly
  ("researched live today — have your lawyer confirm before acting").
- AI-law content anywhere: treat anything published before July 2026 as suspect for EU
  material (the Digital Omnibus on AI changed the deadlines) and verify against
  post-July-2026 sources.

## Website research (launch)

**No website, app-store page only** (the modal solo mobile founder): treat the store
listing as the research target — identity-check it the same way, and read: install bands,
content rating, category, the data-safety/privacy-nutrition section (a goldmine: it's the
founder's own declared data practices — confirm, don't assume), reviews mentioning kids,
listed SDK/ad disclosures. Same rules apply: guesses until confirmed.

Look for: what the product does, who it serves, pricing/customers page (B2B vs B2C),
countries/languages served, careers page (team locations, HR data), privacy policy +
cookie banner (existence and claims), visible AI features, checkout mechanics. These are
GUESSES until the user confirms them — present as guesses with confidence markers. If
something on the site looks non-compliant (no privacy policy, pre-consent trackers), note
it internally for the gap-check stage; in a quick scan you may mention at most one such
observation, framed neutrally.

## Knowledge folder

Inventory filenames/sizes first. Skim selectively for: what the document is, who sent it,
what it demands (clocks, frameworks, audit rights), anything unrecognized (→ search #5).
Summarize each file in one line to the user at launch. Many/huge files: ask which matter
most rather than bulk-reading. Facts from documents beat guesses but still get confirmed
with the user if load-bearing ("this DPA commits you to 48-hour breach notice — did you
know that's in there?").
