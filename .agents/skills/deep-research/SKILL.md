---
name: deep-research
description: >
  Multi-platform deep research system using parallel topic-scoped AI agents. Orchestrates
  research across Firecrawl (web), Supadata (YouTube/video), X-Search
  (real-time discourse and community), Academic (papers), Podcast-Search (audio), and Substack (newsletters).
  Two-phase: recon scan to find where signal lives, then parallel topic workers go 3+ levels
  deep on topic angles with signal scoring, triangulation, source profiling, and critic review.
  Use when: deep research, research this topic, investigate, find signal, who are the thought
  leaders on, what's happening in, multi-platform research, intelligence gathering, dive deep,
  research agents. Returns per-agent synthesized reports + master synthesis in
  outputs/deep-research/{date}-{slug}/. Prompt templates live in prompts/ — improve them
  over time as research runs reveal better patterns.
---

# Deep Research Skill

> Kit note: this workspace ships no Reddit client, so treat Reddit as unavailable. Community and platform signal comes via X, Substack, YouTube, and **Apify**, which reaches Instagram, TikTok, LinkedIn, marketplaces, review sites and Google Maps. Before deciding a platform is out of reach, search the Apify store for an actor built for it.

Multi-agent research orchestration across 7 platforms. Topic-scoped parallel agents go
3+ levels deep, score sources rigorously, triangulate claims, and produce critically cited
synthesis reports.

**Output location:** `outputs/deep-research/{date}-{topic-slug}/`
**Prompt templates:** the `prompts/` folder beside this `SKILL.md`

---


## Apify: don't stop at the platforms already wired up

The other sources cover the web, video, X, papers and newsletters. Apify covers everything those can't reach, and it's the difference between research that answers the question and research that answers the easy version of the question.

**The move:** before you settle for the sources you have, ask what the ideal source for this question would be, then search the store for an actor built for it.

```bash
curl -s "https://api.apify.com/v2/store?search=<platform or task keywords>&limit=5" | head -c 2000
```

This example uses POSIX shell syntax. On Windows, use PowerShell or Python for
the same HTTP request. Never send Bash continuations or `head` to PowerShell.

Read the actor's input shape on its store page before running it, because a wrong input shape is the usual cause of a failed run. Then **adapt the research angle to what that actor actually returns.** If you wanted engagement data and the actor gives you post text and timestamps, say so and use what you have rather than reporting nothing.

Worth reaching for when the question involves: Instagram or TikTok comments and followers, LinkedIn profiles or company pages, Google Maps and local listings, marketplace pricing, review sites, app store reviews, or job boards.

If no suitable actor exists, say so plainly and route around it. Never invent numbers to fill the gap.


## The Flow

```
deep-research "brain dump"
  → Scope Interview (3-4 questions)
  → Recon worker (fast available reasoning mode) → recon.md
  → HUMAN CHECKPOINT — review recon, confirm agent roster
  → Parallel topic workers (strongest available reasoning mode) → 01-angle.md, 02-angle.md, ...
  → Critic worker (strongest available, review-only) → critic-notes.md
  → Synthesis worker (strongest available) → synthesis.md
```

---

## Phase 1 MVP (Start Here)

For the first research run, skip recon and critic. Run topic agents directly.

1. Ask the user the scope interview questions
2. Determine 3-6 topic angles based on the brain dump
3. Create session folder: `outputs/deep-research/{date}-{topic-slug}/`
4. Launch all topic agents simultaneously (batch in one message)
5. Run synthesis agent on all outputs

---

## Phase 2: Full Flow

Add recon and critic once the core loop is validated.

1. Scope interview
2. Launch recon agent using `prompts/recon.md` template — populate all variables
3. Show recon.md to user, ask for confirmation/adjustments to agent roster
4. Generate topic angle list from recon + user input
5. Launch all topic agents simultaneously — each populated from `prompts/topic-agent.md`
6. Launch critic agent from `prompts/critic.md` once all topic agents complete
7. Launch synthesis agent from `prompts/synthesis.md`

---

## Scope Interview Questions

Ask these at the start of every session:

1. **Core question:** What's the main thing you're trying to find out or understand?
2. **Time period:** How recent does the information need to be? (last 30 days / 90 days / 1 year / any)
3. **Starting points:** Any known people, publications, repos, or platforms to prioritize?
4. **Depth vs breadth:** Focused on one specific angle, or broad survey of the space?

---

## Populating the Agent Templates

### Session variables (set at scope interview):
- `{TOPIC_BRAIN_DUMP}` — user's full brain dump, verbatim
- `{TIME_PERIOD}` — recency requirement from scope interview
- `{STARTING_POINTS}` — known people/publications/repos (or "none")
- `{SESSION_SLUG}` — `{YYYY-MM-DD}-{kebab-case-topic}`, e.g. `2026-03-27-ai-engineering-tooling`

### Recon variables:
- All session variables

### Topic agent variables:
- All session variables
- `{TOPIC_ANGLE}` — the specific angle this agent is researching
- `{N}` — agent number (01, 02, 03...)
- `{ANGLE_SLUG}` — kebab-case version of the angle, e.g. `practitioner-shipping-reality`
- `{RECON_HOT_PLATFORMS}` — from recon.md (or "unknown, check all" if skipping recon)
- `{RECON_KEY_PEOPLE}` — from recon.md (or "none identified yet")
- `{RECON_QUERIES}` — from recon.md (or "generate your own")

### Critic variables:
- `{TOPIC_BRAIN_DUMP}` — session context
- `{SESSION_SLUG}` — session folder name
- `{LIST_OF_AGENT_REPORT_FILES}` — comma-separated list of report filenames

### Synthesis variables:
- All session variables
- `{LIST_OF_AGENT_REPORT_FILES}` — comma-separated list of report filenames

---

## Launching workers

If the current harness exposes parallel workers and the task permits them, launch
all topic workers together. If it does not, run the same populated templates
sequentially and keep the file boundaries. Do not block or switch harnesses just
because parallel execution is unavailable.

Each topic worker should:
- Use a general-purpose worker when the harness exposes worker types
- Have the full populated prompt from `prompts/topic-agent.md`
- Write output to its specific file path

---

## Typical Agent Roster Examples

**"AI engineering tooling trends"** (4 agents):
- Agent 1: What practitioners are actually shipping and what's breaking in production
- Agent 2: Key thought leaders and their frameworks — who's setting the direction
- Agent 3: Academic and research frontier vs production reality gap
- Agent 4: Tool ecosystem — what's emerging, what's consolidating, what's dying

**"Understanding [person]'s work and influence"** (3 agents):
- Agent 1: Their published work, talks, and primary sources
- Agent 2: How their ideas are being applied by others — reception and criticism
- Agent 3: The people and ideas that influenced them — intellectual lineage

**"Market landscape for [category]"** (5 agents):
- Agent 1: Incumbent players and their positioning
- Agent 2: Emerging challengers and new entrants
- Agent 3: Practitioner sentiment — what's working, what's not
- Agent 4: Academic research direction
- Agent 5: Business model and pricing landscape

---

## Signal Quality Quick Reference

```
RECENCY:     Primary work (any date): 2 | <30d: 3 | <90d: 2 | <1yr: 1 | old current-tech: 0
SOURCE:      Primary/academic: 3 | Named practitioner: 2 | Tech journalism: 1 | Aggregator: 0
SPECIFICITY: Numbers/code/failures: 2 | Some specifics: 1 | Generic: 0
INDEPENDENT: Not citing existing: 1 | Cites existing: 0.5 | Same org: 0
Score ≥5: pursue | 3-4: include with caveat | <3: drop
```

High-value domains: arxiv.org, github.com/issues, github.com/discussions, official docs
Low-value domains: SEO farms, /blog/ai-guide-YYYY patterns, AI-pivot domains post-2023

---

## Maintenance

> **Self-improvement rule:** If you used this skill and discovered something not documented
> here — a better prompt pattern, a tool syntax quirk, a more effective research method,
> a common failure mode — update the relevant prompt template in `prompts/` and add a
> gotcha below. This is how the skill gets sharper over time.

### Known Gotchas

1. **Parallel execution is harness-dependent.** Batch topic workers when the current harness supports it; otherwise run them sequentially and say so in the final methodology note.

2. **Match effort to the phase.** Use a fast available mode for recon and the strongest available reasoning mode for topic work, critique, and synthesis. Never hardcode a product-specific model name.

3. **Session slug collision.** If two research runs happen on the same day on similar topics, slugs may collide. Append a number suffix: `2026-03-27-ai-tooling-2/`.

4. **Rate limits mid-research.** X-Search (Grok) costs ~$0.004-0.01 per call and Apify bills per actor run. Tell agents to handle 429s gracefully — log and continue, don't abort the run.

5. **Topic agent context fills up on long runs.** If an agent is tasked with too broad an angle, its context fills and quality drops. Keep topic angles specific — "what practitioners are shipping in production" not "everything about AI engineering".

6. **X-Search import path.** `scripts/x-search/` is hyphenated, so `from scripts.x_search.client import ...` fails. Use `import sys; sys.path.insert(0, "scripts/x-search")` then `from client import XSearchClient`. Templates fixed 2026-06-12.


8. **Critic verification queue is cheap to clear inline.** When the critic's queue has 1-2 concrete items (e.g. "re-read this repo's README"), resolve them with a direct check before synthesis and pass the resolution into the synthesis prompt as settled fact. Settled a cross-report contradiction in one `gh api` call on 2026-06-12.


10. **The verify→critic→synthesis convergence is best run as a single Workflow.** After the parallel topic agents finish, one Workflow (6 parallel fact-checkers pinning prices/versions/repo-liveness → 2 adversarial critic lenses reading all reports → 1 synthesis writing `synthesis.md`) beats a loose critic+synthesis. The fact-check phase caught real errors on the 2026-06-19 run (Suno Premier $24 not the report's guessed ~$30; Ozone is v12 not 11; soothe2→soothe3; confirmed Splice ships an official first-party MCP server). Feed verified facts + critic notes into the synthesis prompt as authoritative overrides.

11. **One topic agent hit an X-Search client dict-shape error** (2026-06-19, agent 01) and lost X sentiment for that angle. Non-fatal (the agent logged it and finished on other platforms), but if X coverage matters for an angle, have the agent fall back to Grok-only `xclient.search()` (skip `discover_and_enrich`'s enrichment step) on a shape error instead of dropping X entirely.

12. **Firecrawl requires a current Node runtime.** If it throws `EventTarget is not defined` under Node 20, use Node 22 or newer through the operating system's normal Node installation. Do not hardcode a macOS home path in a portable workspace.

13. **Deep agents that spawn their OWN child fact-checkers can stop without writing their report file.** On 2026-07-23 three topic agents (treatments, life-manifestation, and one first pass) fanned out to sub-agents, then hallucinated that they were the *orchestrator* waiting on those children, and returned a "standing by" completion with no deliverable on disk. Two mitigations: (a) after the topic agents finish, `ls` the session folder and check every expected `NN-*.md` exists and is non-trivial before synthesis; (b) resume any missing one via SendMessage with an explicit "you are the topic agent, not the orchestrator — write your full report to <path> NOW, don't wait on children." Cheap to catch, silent if you don't.

14. **OpenAlex (the `academic` client backend) 429-rate-limits hard when many workspace tabs run at once.** On the 2026-07-23 run its shared IP pool was saturated, so citation *counts* were unavailable and agents fell back to verifying author/year/venue/DOI against PubMed/Europe PMC via WebSearch+WebFetch. That fallback is fine and produces working URLs; just tell citation-heavy agents to expect the 429s and verify against PubMed/Europe PMC rather than retrying OpenAlex in a loop.

### Improvement Backlog

- Add SlopTotal integration as an optional slop filter for borderline sources (self-hosted, MIT, `github.com/pablocaeg/sloptotal`)
- Add HN Algolia API as a source: `https://hn.algolia.com/api/v1/search?query={topic}&tags=story&numericFilters=points>50` — free, no auth, high signal (validated 2026-06-12: HOT on a technical-tooling topic; fold into the prompt templates)
- Add GitHub as a source: issues, discussions, trending repos for technical topics (validated 2026-06-12: `gh api` for maintainer health, licenses, liveness checks was decisive on adopt-vs-build questions; fold into the prompt templates)
- Experiment with a second recon pass after deep agents to catch things the initial recon missed
- ~~Build a session index at `outputs/deep-research/INDEX.md` that lists all past research runs with 1-line summaries~~ DONE 2026-06-19 (`outputs/deep-research/INDEX.md` created; keep it updated newest-first each run)
