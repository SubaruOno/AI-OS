# Project Agent Runtime

Read `identity.md` before acting.

Then:

1. Read the relevant files in `substrate/`.
2. Apply every relevant rule in `rules/`.
3. Run `hooks/preflight.md` before consequential work.
4. Use an existing skill from `skills/` before inventing a workflow.
5. Use an agent from `agents/` only when several skills form one recurring role.
6. Run `hooks/postflight.md` before claiming completion.
7. Write durable decisions and unresolved questions back to `substrate/`.

Canonical files win over this adapter. Nested `AGENTS.md` files may specialize instructions for their own subtree but must not weaken safety, privacy, or verification rules.

