# Portable Agent Runtime

Copy this folder into any project, then ask:

> Read `START-HERE.md`, inspect this folder, and help me customize the smallest useful runtime for my goal.

## The six layers

1. `identity.md` defines purpose, audience, defaults, and refusals.
2. `substrate/` holds evidence, decisions, memory, and trusted context.
3. `rules/` contains constraints that apply across workflows.
4. `skills/` contains reusable procedures.
5. `agents/` contains roles that compose several skills.
6. `tools.md` records live connections, permissions, and owners.

## Start here

1. Replace the prompts in `identity.md`.
2. Add trusted sources to `substrate/sources.md`.
3. Delete rules that do not apply. Add goal-specific rules.
4. Keep only the skills you expect to use.
5. Materialize an agent only when several skills form a recurring job.
6. Record every connection and permission in `tools.md`.

`AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are thin adapters. The canonical operating system lives in the files and folders above.

