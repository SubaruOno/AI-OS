# Project Agent Runtime

Read `identity.md` first. Treat it as the canonical purpose and behavior contract.

Before work:

1. Load relevant context from `substrate/`.
2. Apply relevant files from `rules/`.
3. Run `hooks/preflight.md`.

During work:

- Use a procedure in `skills/` when one matches.
- Use a role in `agents/` only for work that composes several skills.
- Keep unrelated project and client context isolated.

Before completion:

1. Run `hooks/postflight.md`.
2. Record durable decisions, evidence, and open questions in `substrate/`.

Do not duplicate the full operating system in this adapter. Canonical files win.

