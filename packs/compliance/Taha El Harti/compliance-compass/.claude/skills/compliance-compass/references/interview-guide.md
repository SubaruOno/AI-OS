# Interview guide — question wording & branching

Proposed wording below is calibrated for plain, B1-level English. Adapt naturally to the
conversation — but keep one fact per question, a concrete example inside the question, and
zero legal terms. Ask only what website research + knowledge files didn't already answer.

## Stage 1 — sorting questions

| # | Ask (or confirm) | Listen for → branch |
|---|---|---|
| S1 | "In a sentence or two — what does your business do, and who does it serve?" | Concrete business type → **SEARCH: regulations for this business type.** B2B vs B2C shapes S6. Marketplaces/platforms: whose data is it? |
| S2 | "What do you know about the people who use it — do you have their emails, names, payment details, health info, anything like that?" | Payments taken directly (not just Stripe checkout) → PCI branch. Health-ish data → HIPAA-vs-wellness decision tree (`regimes/hipaa-hbnr.md`). Photos/voice/faces → biometrics flag. **Always follow up once: "And your own team — employees, contractors? Where are they?"** (HR data is data too; founders forget it.) |
| S3 | "Where are the people whose data you handle — customers, users, and your team?" | Any EU country → GDPR-family branch. Any non-EU/US country → live-research it. Multiple US states → state-pattern file. |
| S4 | "And the company itself — where is it registered? Any offices or people anywhere else?" | EU establishment triggers EU law with zero EU users. Non-EU company with EU users → the EU-representative check happens in the GDPR gap checks; if gap checks don't run, log it as UNKNOWN — never assert it in the summary without having asked. |
| S5 | "Is your product used in any regulated area — health, money or finance, education, insurance, government, or by kids?" | Kids possible (even "maybe") → children's escalator: "Could people under 18 realistically end up using it?" Health → S2 branch deepens. Finance → NIS2/DORA screen + sector research. |
| S6 | "Who pays you — consumers, businesses, or government?" *(one question; the enterprise probe is a SEPARATE follow-up message: "Any bigger companies as customers, or are you hoping for them?")* | Enterprise buyers current/target → counterparty branch: SOC 2 pressure, DPAs, questionnaires (`regimes/soc2.md`, `regimes/dpas-security-questionnaires.md`). Determines controller-vs-processor: "Is the data yours, or your customers' users' data that you handle for them?" |
| S7 | "Do you use AI in the product? If yes — did you build the model yourselves, or are you using someone else's, like OpenAI or Anthropic?" | Ships AI to users → AI escalator: "Do people chat with an AI in your product? Is it labeled as AI? Do you generate images/audio/video?" (`regimes/eu-ai-act.md` if any EU exposure). Hiring/credit/education use cases → high-risk screen. |
| S8 | "Roughly how big are you — team size, and about how many people's data do you hold? Ballpark is completely fine." | Resolves thresholds: state-law applicability, SME/small-mid-cap reliefs, microenterprise exemptions. Remember: Texas/Nebraska have NO threshold — "small" never auto-means "exempt". |
| S9 | "Do you send marketing emails or texts? And do you run analytics or ad tracking on your site?" | Texts → TCPA (litigation risk). Cookies/analytics + EU visitors → `regimes/eprivacy-cookies.md`. Email → CAN-SPAM quick-ref. |

Order is a default, not a script: follow the conversation. Tom says "I help e-commerce
businesses" → S6 (who pays) and the controller/processor question naturally come second,
not S2. Just cover all rows before Stage 2 exits.

## Escalator probes (fire when flagged, 1–2 questions each)

- **Children**: could under-18s / under-13s realistically use it? Any age gate? Ads/SDKs in
  a kids' context?
- **Health**: do any customers bill insurance? Do you sign BAAs? (These two separate HIPAA
  from wellness faster than "is it health data?")
- **Payments**: does card data ever touch YOUR systems/pages, or is it fully handed to a
  processor's checkout?
- **AI shipped to users**: labeled as AI? synthetic media generated? any hiring/credit/
  education/essential-services use case (even on the roadmap)?
- **Enterprise buyers**: anyone sent a security questionnaire or asked for SOC 2 / a DPA
  in the last 12 months?

## The coverage checklist (Stage 2 exit criteria)

All must be ANSWERED or logged UNKNOWN before the end-state summary:
1. Business + who it serves  2. Data categories (incl. HR)  3. People locations
4. Establishment  5. Sector  6. Buyers + controller/processor role  7. AI posture
8. Scale band — plus every escalator flag raised, and every regime candidate from the
Stage-1 business-type search dispositioned (applies / not applicable + why / unknown).

## Unknowns

Each UNKNOWN gets: what's missing, why it matters (one line), how to find out (one line).
They surface in the summary and land at the TOP of the report queue as "Find out first".
Worst-case bounding rule (fixed, so identical interviews bound identically): bound —
explicitly and labeled — ONLY when the unknown gates a regime whose worst-case status
would be ACTION REQUIRED ("Since we don't know whether under-13s use it, I'm including
the children's-data items — strike them if that's wrong."). Everything else is logged
UNKNOWN, never bounded.

## Tone calibration

Neutral analyst. No fear, no hype, no "great question!", and no superlatives about the
user's situation ("the single most important fact…") — rank by ordering, not by drama.
Every legal assertion — not just numbers — carries its verification date or an explicit
"as of <date>, unverified" label; if you catch yourself stating a requirement undated,
date it or flag it. After any live research that goes beyond what the regime library
contains, make the save-offer once ("Want me to save this to your regime library? I'll
mark it as unreviewed live research."). Numbers with dates. When a regime
doesn't apply, say so with the specific reason — founders remember what they DON'T have to
do. When enforcement reality is mild, say that too; when it demonstrably reaches small
companies (children's apps, health apps, EU complaint-driven), say that plainly with the
evidence, not adjectives.
