---
id: eu-ai-act
name: EU AI Act (Regulation (EU) 2024/1689), as amended by the Digital Omnibus on AI
jurisdiction: EU (extraterritorial reach)
tier: full
enforcer: national market-surveillance authorities; EU AI Office/Commission (centralized post-Omnibus, incl. GPAI); enterprise customers via "AI Act warranty" contract clauses
last_verified: 2026-07-28
volatile:
  - enforcement record (zero public fines as of 2026-07-28 — will change)
  - SMC definition (verified against OJ text 2026-07-28 — Reg. (EU) 2026/1744 Art 3(14b) via Rec. (EU) 2025/1099)
  - watermarking-feasibility enforcement posture (tech reportedly lags mandate for text)
flip_dates:
  - "2026-08-02: Art 50 transparency duties (chatbot disclosure, deepfake/AI-text labels, synthetic-content marking for new systems) become applicable; GPAI enforcement machinery + fines (Commission/AI Office) switch on."
  - "2026-12-02: marking grace period ends for systems already on market before 2 Aug 2026; new NCII ('nudifier') + CSAM-generation prohibition transitional period ends."
  - "2027-08-02: member-state deadline for national regulatory sandboxes (moved by Omnibus); EU-level sandbox with priority SME/startup access."
  - "2027-12-02: high-risk obligations, Annex III stand-alone use cases (hiring, credit, education, essential services…) become applicable (was 2 Aug 2026)."
  - "2028-08-02: high-risk obligations, Annex I (AI embedded in regulated products) become applicable (was 2 Aug 2027)."
---

**Timing warning:** the Digital Omnibus on AI was signed 8 Jul 2026, published in the OJ 24 Jul 2026, in force 27 Jul 2026. Any source published before July 2026 describes AI Act timing that is no longer law. This file reflects the post-Omnibus position only (verified 2026-07-28). Do not confuse with the *data/GDPR* Digital Omnibus, which is a separate instrument still in trilogue.

## Does this apply to you? (triggers)
Role determines duties — most startups are one of these:
- **Deployer** (most common): you use an AI system under your own authority (builds on OpenAI/Anthropic APIs, RAG, agents). Today: document AI-literacy training efforts. From 2 Aug 2026: label deepfakes and AI-generated public-interest text you publish. High-risk deployer duties only from Dec 2027+ if the use case matches Annex III.
- **Provider**: you develop/place an AI system on the EU market under your own name. A startup **becomes a provider of the app it ships** even when the model underneath is someone else's — chatbot disclosure (Art 50(1)) is a provider duty. Calling an API does not make you a GPAI *model* provider; heavy fine-tuning can create GPAI-provider-style obligations scoped to the modification (fact-dependent; ordinary prompt-engineering/RAG does not).
- Reclassification risk: putting your name on a high-risk system, substantially modifying one, or repurposing one to high-risk moves you toward provider-of-high-risk obligations (Art 25).
- Extraterritorial: applies to providers placing systems on the EU market wherever established, and where output is used in the EU.
- No AI features and no AI output reaching EU users → NOT APPLICABLE; re-check when AI ships.

### Per-obligation status (verified 2026-07-28 — keep these dates separated)
**In force now:**
- Prohibited practices (Art 5) — since 2 Feb 2025, penalties since 2 Aug 2025: manipulative techniques, social scoring, emotion recognition in workplace/education, untargeted face scraping.
- AI literacy (Art 4) — since 2 Feb 2025, **relaxed by Omnibus**: document training efforts; no duty to guarantee individual competence.
- GPAI provider obligations (Arts 53/55) — since 2 Aug 2025 for new models (enforcement machinery from 2 Aug 2026).

**Imminent — 2 Aug 2026 (days away at verification date; unchanged by Omnibus):**
- Art 50 transparency: visible disclosure when users interact with AI; deepfake labels; disclosure of AI-generated public-interest text; machine-readable marking of synthetic content for new systems. Terms-of-service mention is NOT sufficient — plain-language notice at the point of interaction (Commission guidance).
- Grace: systems already on market before 2 Aug 2026 have until **2 Dec 2026** for machine-readable marking (Omnibus change).

**Deferred (do NOT present as current duties):**
- Annex III high-risk (hiring, credit, education, essential services…) → **2 Dec 2027**.
- Annex I high-risk (AI in regulated products) → **2 Aug 2028**.
- New Art 5 prohibition (NCII/CSAM generation, added by Omnibus) → transitional until **2 Dec 2026**.

## Who can punish you, and how
- National market-surveillance authorities (still maturing); post-Omnibus the **AI Office gains centralized supervisory authority**, including over systems built on same-provider GPAI models and AI in VLOP platforms. GPAI enforcement (documentation requests, model evaluations, recalls, fines) is Commission/AI Office, live from 2 Aug 2026.
- Contract channel: enterprise buyers already push "AI Act warranties" into vendor contracts ahead of legal deadlines.
- (Bucket assigned per founder in the report.)

## Penalties & enforcement reality
- Prohibited practices: up to €35M or 7% of global turnover. Most other violations incl. Art 50: up to €15M or 3%. Incorrect info to authorities: up to €7.5M or 1%. GPAI providers: up to €15M or 3%, from 2 Aug 2026. (All verified 2026-07-28.)
- **SME/SMC reliefs (Omnibus):** SME reliefs extended to "small mid-caps" (SMC), defined in the OJ text (Art 3(14b), via Recommendation (EU) 2025/1099) as: not an SME, **fewer than 750 employees AND (annual turnover ≤€150M OR annual balance-sheet total ≤€129M)** — verified against EUR-Lex 2026-07-28. Reliefs: simplified technical-documentation templates (notified bodies must accept), proportionate quality-management expectations, priority sandbox access, tailored/lower penalty caps. The postponed high-risk dates (2 Dec 2027 / 2 Aug 2028) are **fixed and unconditional** in the final text — the Commission's proposed standards-availability trigger was abandoned in trilogue (verified 2026-07-28).
- **Honesty statement:** no public AI Act fines exist as of 2026-07-28, despite prohibitions being enforceable since Aug 2025 — national machinery is still maturing. The nearest real enforcement against AI products today is data protection authorities using GDPR.

## Gap-check questions
1. Do users ever talk to an AI (chatbot, agent, voice) that isn't clearly labeled as AI at the point of interaction?
2. Do you generate images, audio, video, or text at scale? Is the output machine-readably marked as AI-generated, and do you preserve upstream watermarks/provenance rather than stripping them?
3. Do you publish AI-written content on matters of public interest without disclosing it?
4. Does any feature infer people's emotions at work or in education, score people socially, or scrape faces from the internet?
5. Is any current or planned use case about hiring, credit decisions, education access, or access to essential services?
6. Are you fine-tuning models heavily enough that you're effectively shipping your own model, versus prompting someone else's?
7. Is your company under 750 employees and ≤€150M turnover? (→ small-mid-cap reliefs)
8. Have you documented any AI training you give your team?

## First steps
1. By 2 Aug 2026 (now): add a visible, plain-language "you're talking to an AI" disclosure to any chatbot/agent, unless obvious. (hours)
2. By 2 Aug 2026 / 2 Dec 2026 (grace for pre-existing systems): machine-readable marking of AI-generated content — for API-based startups, largely means not stripping upstream provenance (C2PA/watermarks) and marking own outputs. Note: sources report the mandate outpaces available tech, especially for text; enforcement posture unclear. (hours–days)
3. Label deepfakes and AI-generated public-interest text you publish. (hours)
4. Screen everything you ship against the prohibited list (emotion recognition at work/school, social scoring, manipulation, face scraping; from Dec 2026 NCII/CSAM generation capability). (hours)
5. Screen the roadmap against Annex III use cases — if any match, calendar Dec 2027; don't build high-risk compliance now, but don't design into a corner. Document AI-literacy efforts (lightweight post-Omnibus). (hours)

## Cost baselines
- Art 50 tier (deployer/app provider): mostly engineering hours — disclosure UI, provenance passthrough — low thousands €; no mandatory audits or fees at this tier (verified 2026-07-28).
- High-risk tier (deferred to Dec 2027/Aug 2028): materially heavier (QMS, conformity assessment, documentation) — cost data premature; not encoded.

## Sources
All accessed 2026-07-28, post-Omnibus except statutory background:
- Gibson Dunn "EU AI Act Omnibus Agreement"; Lewis Silkin "Digital Omnibus on AI enters into force today" (27-Jul-2026); Freshfields "EU AI Act unpacked #34"; Digital Watch; TechTimes 27-Jul-2026 (OJ publication/entry into force) and 21-Jul-2026 (watermarking feasibility).
- Orrick "7 Key Changes" (May 2026, pre-final — SMC ≤750/€150M figure, cross-checked).
- Commission AI Act Service Desk Art 50 FAQ (digital-strategy.ec.europa.eu); Greenberg Traurig on Art 50 guidance (Jun 2026); artificialintelligenceact.eu (Art 5/Art 50 explainers); MediaLaws/CSA (GPAI enforcement from 2 Aug 2026); FPF (prohibited practices).
- OJ text reviewed 2026-07-28: EUR-Lex Reg. (EU) 2026/1744; Rec. (EU) 2025/1099 Annex pt 2 (SMC definition); NicFab OJ analysis + Gibson Dunn (fixed, unconditional dates).
