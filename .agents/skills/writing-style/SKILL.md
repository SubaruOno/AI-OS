---
name: writing-style
description: >
  Anti-AI-slop writing enforcement for all prose, copy, and documentation output.
  Use when writing marketing copy, website copy, strategy documents, briefs,
  newsletters, emails, reports, summaries, plans, content concepts, module
  documentation, team communications, or any text output. Covers banned words,
  structural patterns to avoid, punctuation rules, rhythm guidance, and
  before/after examples. Ensures all output sounds like a sharp human writer,
  not a language model.
---

# Writing Style Enforcement

This skill enforces human-sounding writing across all workspace output. The core rule is in both workspace constitutions and this skill provides the full reference and self-check protocol.

## Quick Reference

Read `reference/writing-style.md` for the complete guide including:
- Tiered banned word lists (Tier 1: never use, Tier 2: avoid clustering)
- Banned phrases (openers, closers, promotional fluff, chatbot artifacts)
- Seven dangerous expression formulas to avoid
- Punctuation and formatting rules
- What human writing actually sounds like (discourse markers, fragments, register shifts)
- Before/after examples showing slop vs. human copy

## Model-Specific Tells

These are patterns common to assistant-written prose across models. Watch for and eliminate:

1. **Epistemic hedging.** "I should note that," "it's worth mentioning," "it bears noting." Just say the thing.
2. **Copula avoidance.** Writing "serves as" or "stands as" instead of "is." Use "is."
3. **Over-qualification.** Wrapping every claim in caveats. Commit to a position.
4. **Balanced framing.** Presenting "both sides" when a clear stance would be more useful. Have opinions.
5. **Meta-commentary.** Commenting on your own response. Don't narrate, just deliver.
6. **Nested clauses.** Sentences with multiple subordinate clauses stacked together. Break them up.
7. **Verbosity without substance.** Using more words without adding information. Cut aggressively.
8. **Explanation over opinion.** Explaining what something is rather than arguing why it matters.

## Self-Check Protocol

Before delivering any prose output, scan for:

1. **Em dashes** (find and replace with commas, periods, or parentheses)
2. **Tier 1 banned words** (replace with plain, specific language)
3. **Binary contrast patterns** ("It's not X, it's Y") (rewrite as direct statements)
4. **Three or more consecutive similar-length sentences** (vary them)
5. **Filler transitions** ("Furthermore," "Moreover," "Additionally") (delete)
6. **Chatbot artifacts** ("I hope this helps!", "Great question!") (delete)
7. **Vague claims without specifics** (add numbers, names, concrete details)
8. **The Horoscope Test**: could this paragraph appear in any document about any topic? If yes, rewrite with specifics only this context would produce.

## Maintenance

- This skill was created 2026-03-11 based on research across 70+ web sources, 15 YouTube transcripts, and 5 GitHub anti-slop repositories.
- Full research files at the research these rules came from and three supporting research docs.
- If new AI-isms emerge as models change, update `reference/writing-style.md` and the banned word lists.
- Future enhancement: add Liam's personal voice profile (V.O.I.C.E. framework) for "sounds like Liam" on top of "doesn't sound like AI."
