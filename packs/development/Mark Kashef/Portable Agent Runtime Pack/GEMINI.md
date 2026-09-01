# Project Agent Runtime

Use `identity.md` as the canonical system identity.

For each task:

1. Read the relevant context in `substrate/`.
2. Apply the relevant constraints in `rules/`.
3. Complete `hooks/preflight.md`.
4. Prefer a matching workflow in `skills/`.
5. Materialize a role from `agents/` only when the task needs several workflows.
6. Complete `hooks/postflight.md`.
7. Persist decisions and open questions to `substrate/`.

Keep this file as a thin Gemini adapter. Do not fork the canonical identity, rules, or workflows here.

