---
id: us-state-privacy-pattern
name: US state comprehensive privacy laws — the Virginia-model pattern (all states except CA deep-dive)
jurisdiction: US (state patchwork)
tier: full
enforcer: state Attorneys General (exclusive — no private lawsuits, except CA's narrow breach right)
last_verified: 2026-07-28
volatile:
  - "state count (24 enacted / ~20 in effect during 2026 — moves several times a year; NEVER print a count without a date)"
  - "every threshold cell in the table below (CT, MT, UT amended 2025–26 — statute-text verification still needed)"
  - "penalty ranges (~$7,500–$10,000/violation pattern)"
flip_dates:
  - "2026-07-01: Connecticut SB 1295 amendments — threshold drops to 35k + expansions (verify statute text)"
  - "2027-01-01: Louisiana and Oklahoma laws take effect"
  - "2027-05-01: Alabama law takes effect"
  - "2028-01-01: Vermont law takes effect (3k sensitive-data trigger — lowest in the country)"
  - "ONGOING: state AI law is deliberately NOT covered by any regime file — too volatile (Colorado's 2024 AI Act was rewritten wholesale by SB 26-189, May 2026, before ever taking effect; a Dec 2025 federal executive order signals preemption pressure). Research state AI live, every time."
---

## Does this apply to you? (triggers)

**24 states enacted, ~20 in effect during 2026** (verified 2026-07-28; counts vary by
whether Florida's $1B-threshold law counts as "comprehensive" — never print a count
without a date). Nearly all follow the **Virginia model**: applicability keyed to
consumer counts and/or data-sale revenue share, AG-exclusive enforcement, cure periods
(some sunsetting), and a shared obligations core.

**The gate, state by state:** you are covered in a state only if you meet ITS
threshold with ITS residents. Below threshold in a state → NOT APPLICABLE there, with
a re-check as your user base grows. Never "green" — nothing was assessed.

**⚠️ THE TWO EXCEPTIONS THAT BREAK THE "YOU'RE PROBABLY UNDER THE THRESHOLDS" MESSAGE:**
- **Texas and Nebraska have NO numeric thresholds at all.** The gate is instead the
  SBA small-business definition — and in Texas even SBA-small businesses need consent
  to **sell sensitive data**. Any "you're too small for this" reassurance must be
  state-qualified.
- **The low-threshold cluster** — DE, NH, MD, RI at 35k/10k consumers, and VT (2028)
  at 3k sensitive-data consumers — is reachable by a modest consumer app: 35k
  residents of one state ≈ a few hundred thousand US users. Founders rarely know
  their per-state user counts; that's the interview question that matters.

Other cross-cutting scope facts (verified 2026-07-28):
- **Employee and B2B data are exempt everywhere except California.**
- Most laws exempt HIPAA-covered entities, GLBA data, and nonprofits (Oregon covers
  nonprofits since 2025).
- Adjacent, NOT in this table but often higher risk: **Washington My Health My Data**
  (private right of action — see `wa-mhmd-il-bipa.md`) and **New York SHIELD Act**
  (data-security duty for anyone holding NY residents' private info, no threshold).

## The shared obligations core (~90% common across states)

Privacy notice; consumer rights to access/delete/correct/port; opt-out of sale,
targeted advertising, and profiling; opt-in consent for sensitive data (health,
biometrics, precise geolocation, kids' data); data-protection assessments for
higher-risk processing; processor contracts; non-discrimination. State deltas worth
flagging: Colorado requires honoring a universal opt-out mechanism; Maryland adds the
strictest substantive duties (data-minimization duty, ban on selling sensitive data);
Connecticut and Vermont add LLM-training disclosure.

## Per-state table

Spot-verified against trackers 2026-07-28. **Re-verify each cell at time of use** —
CT, MT, and UT amended their laws in 2025–26 and those rows in particular still need
verification against statute text, not trackers.

| State | Effective | Applicability trigger (any one unless noted) | Notes |
|---|---|---|---|
| California | 2020 / CPRA 2023 | $26.625M revenue OR 100k consumers/households OR 50% rev. from sale/share | Own file: `ccpa-cpra.md`. Only dedicated agency (CPPA) + narrow breach PRA ($100–$750/consumer/incident) |
| Virginia | Jan 2023 | 100k consumers OR 25k + 50% rev. from sale | No revenue-only trigger — the model most states copy |
| Colorado | Jul 2023 | 100k OR 25k + any revenue from sale | Universal opt-out mechanism required; no small-biz revenue floor |
| Connecticut | Jul 2023 | 100k (excl. payment-only) OR 25k + 25% rev. | **Amended (SB 1295): drops to 35k + expansions eff. Jul 1, 2026 — verify statute text.** First LLM-training disclosure |
| Utah | Dec 2023 | $25M revenue AND (100k OR 25k + 50%) | Most business-friendly; **amendments eff. Jul 1, 2026 — verify statute text** |
| Texas | Jul 2024 | **NO numeric threshold** — any entity doing business in TX processing/selling personal data that is not an SBA-defined small business; even small businesses need consent to sell sensitive data | AG very active (incl. a reported ~$1.375B Google settlement, 2025 — verify figure before citing) |
| Oregon | Jul 2024 | 100k OR 25k + 25% rev. | Covers nonprofits (since 2025); HB 2008 eff. Jan 1, 2026 (precise-geolocation sale ban) |
| Montana | Oct 2024 | 25k OR lower combo — **amended (SB 297) eff. Oct 1, 2025, lowered thresholds — verify statute text** | Verify current figures at time of use |
| Florida | Jul 2024 | **$1B revenue** + other criteria | Effectively big-tech-only; the reason state counts differ |
| Iowa | Jan 2025 | 100k OR 25k + 50% | Narrow, business-friendly |
| Delaware | Jan 2025 | 35k OR 10k + 20% rev. | Low threshold — catches smaller startups |
| Nebraska | Jan 2025 | **Texas model — NO numeric threshold**; SBA small-business exemption | Plus separate Age-Appropriate Design Code eff. Jan 1, 2026 |
| New Hampshire | Jan 2025 | 35k OR 10k + 25% | Low threshold |
| New Jersey | Jan 2025 | 100k OR 25k + any rev. from sale | |
| Tennessee | Jul 2025 | $25M revenue AND (175k OR 25k + 50%) | High bar |
| Minnesota | Jul 2025 | 100k OR 25k + 25% | Small-business exemption |
| Maryland | Oct 2025 | 35k OR 10k + 20% | **Strictest substantive rules** (minimization duty, sensitive-data sale ban) + low threshold |
| Indiana | Jan 2026 | 100k OR 25k + 50% | |
| Kentucky | Jan 2026 | 100k OR 25k + 50% | Amended by HB 473 |
| Rhode Island | Jan 2026 | 35k OR 10k + 20% rev. | Low threshold; unusual drafting — no cure period, penalties up to $10k/violation |
| Louisiana | Jan 2027 | $25M revenue OR 75k consumers/households/devices OR 50% rev. from sale | CCPA-flavored hybrid (enacted May 29, 2026) |
| Oklahoma | Jan 2027 | 100k OR 25k + majority of rev. from sale | Enacted Mar 20, 2026 |
| Alabama | May 2027 | Virginia-model consumer-count triggers — **verify exact figures at time of use** | Enacted Apr 17, 2026 |
| Vermont | Jan 2028 | 35k consumers OR 3k sensitive-data consumers OR 3k sold | Enacted Jun 16, 2026; LLM-training disclosure (2nd after CT); **3k sensitive trigger = lowest bar in the country** |

## Who can punish you, and how

State Attorneys General, exclusively — **no private lawsuits** under any of these
except California's narrow breach right. Many states have cure periods (fix-it-first
notice), several sunsetting. Bucket note: for sub-threshold B2B startups these laws
usually arrive as *contract-mandated* — enterprise customers pushing state-law DPA
terms downstream.

## Penalties & enforcement reality

- Pattern: ~**$7,500–$10,000 per violation**, AG-enforced (verified 2026-07-28;
  per-state figures vary — RI tops at $10k with no cure period).
- Real enforcement outside CA is led by **Texas** (the no-threshold state — see the
  reported Google settlement above). Enforcement history for most other states is
  thin to nonexistent as of 2026-07-28.
- **Honesty statement:** outside California and Texas, no meaningful small-company
  enforcement record was established in source research. The realistic pressure on a
  small startup is contractual (enterprise DPAs) and the low-threshold states'
  reachability, not AG actions.
- State AI laws are deliberately excluded from this file — **research live** (see
  flip_dates; the Colorado rewrite proves anything encoded mid-2025 would now be wrong).

## Gap-check questions

1. Do you know, even roughly, how many users you have in each US state — especially
   Texas, Nebraska, Delaware, New Hampshire, Maryland, and Rhode Island?
2. Do you do business in Texas or Nebraska at all? (Size alone doesn't exempt you
   there — only the federal small-business definition does.)
3. Do you sell or share anything that could be "sensitive" — health, precise location,
   biometrics, kids' data — in any state?
4. Does your privacy notice list the state-law rights (access, delete, correct,
   opt-out of sale/targeted ads), and does the opt-out actually work?
5. Do your contracts with data-touching vendors contain the required processor terms?
6. Has an enterprise customer contractually obligated you to state-privacy compliance
   regardless of thresholds?
7. When did you last re-check your per-state applicability? (Thresholds and states
   change several times a year.)

## First steps

1. Estimate per-state user counts from your analytics; compare against the table
   (hours). Below all thresholds and not in TX/NE scope → record NOT APPLICABLE
   per state with a re-check date.
2. If TX/NE-active: confirm SBA small-business status; in TX, check whether you sell
   sensitive data at all (hours).
3. One privacy notice + rights-intake process built to the strictest applicable state
   (usually MD for duties, CO for universal opt-out) rather than 20 variants (days).
4. Vendor contract pass for processor terms (days).
5. Calendar a quarterly re-check — this table rots fast (minutes).

## Cost baselines

Not established in source research (see `ccpa-cpra.md` for consent-platform
calibration figures, which generalize roughly).

## Sources

All accessed 2026-07-28: MultiState 2026 tracker; IAPP state-privacy coverage; Sidley
effective-dates chart; O'Melveny 2026 checklist; Hunton (Vermont, Oklahoma); Koley
Jessen (Vermont); White & Case (Oklahoma); Inside Privacy (Alabama, Louisiana);
WilmerHale (Louisiana); Mayer Brown (Vermont). Threshold cells are tracker-sourced —
statute-text verification pass still owed, per memo, before this table is treated as
authoritative (CT/MT/UT rows especially).
