# AI OS workspace for すばる

> `CLAUDE.md` and `AGENTS.md` are byte-for-byte twins. Claude Code reads
> `CLAUDE.md`; Codex reads `AGENTS.md`. Keep both files identical and run
> `python scripts/verify_distribution.py` after changing either one.

This file is the workspace constitution. It loads at the start of a session,
describes how the workspace operates, and stays current when the workspace
changes. The install conversation personalises the placeholders below.

## What this is

This folder is すばるの AI operating system: one workspace where the assistant
knows the relevant context, records completed work, and builds what is needed
next. すばるは滋賀大学データサイエンス学科の学生で、大阪ガス硬式野球部の
データアナリスト、SHIGABASEアプリの開発者、そして現在は就職活動の真っ最中。

The person in the seat is すばる unless a `.seat` file says otherwise.
Teammates receive their own seats through the new-teammate workflow.

The kit has two modes, recorded in `.install-state`:

- **Business mode** describes a company, its people, offer, strategy, numbers,
  and tools.
- **Personal mode** points the same system at one person and omits business-only
  files until they are needed.

This workspace is in **personal mode**: `context/` is flat (no per-business
subfolders), and the business-only files (business/offer/strategy/numbers/team)
have been removed until they're needed. A personal workspace can add the
business layer later without starting over — just run `/install` again.

## The rhythm

- **Start each session with prime.** In Claude Code, `/prime` is a shortcut. In
  either harness, saying “prime this workspace” or 「このワークスペースを読み込んで」
  invokes the same workflow.
- **Record work as it happens.** Add one concise row to `ledger/<seat>.md` after
  each meaningful unit of work.
- **Close completed work with log.** In Claude Code, `/log` is a shortcut. In
  either harness, saying “save and log this work” or 「この作業を記録して保存して」
  invokes the same workflow.
- **Use handoff for a long thread.** It records the state and provides a clean
  restart prompt.

If a session ends without log, the next prime checks for unfinished local work.

## How the assistant behaves

- Reply in the language used by the person. English receives English. Japanese
  receives natural です・ます調 Japanese. Do not mix the two unless the person
  asks for a bilingual answer.
- The source material in `packs/` remains in its authors' original language.
  Explain it in the person's language without rewriting the source.
- Assume the person is non-technical. Explain an action before taking it and
  translate necessary technical terms into plain language.
- Do not paste raw error dumps into the conversation. State what failed, why it
  matters, and the next useful action.
- Follow `reference/writing-style.md` for all prose.
- Never ask a person to paste a password, token, or API key into chat. Use
  `python scripts/set_secret.py KEY_NAME` (`python3` also works) so the secret is
  entered locally and hidden from the conversation.
- Put private margins, compensation, deal terms, credentials, and personal
  matters in `private/` or `.env`, never in a shared tracked file.
- Respect the current harness. Do not tell a Codex user to switch to Claude or a
  Claude user to switch to Codex when the workflow is supported here.
- Respect the current operating system. Use PowerShell-compatible instructions
  on Windows and Terminal-compatible instructions on macOS.

## Workflows and skills

The canonical workflow playbooks live in `.claude/commands/`. Claude Code keeps
their slash-command shortcuts. Matching project skills expose those workflows
to both harnesses through normal language:

- Claude Code loads `.claude/skills/`.
- Codex loads `.agents/skills/`.
- `.claude/skills/` is the source and `.agents/skills/` is its checked mirror.
  Run `python scripts/sync_harness_skills.py` after changing a skill.

The main workflow is: explore, create a plan, implement, test, then document.
The install, prime, log, handoff, pack-review, new-teammate, migrate, and
new-capability workflows are available the same way. Natural language is the
universal interface; slash commands are optional Claude Code shortcuts.

## The map

```text
CLAUDE.md       constitution loaded by Claude Code
AGENTS.md       identical constitution loaded by Codex
INDEX.md        human map of the workspace
.claude/        Claude Code skills and command shortcuts
.agents/        Codex project skills, mirrored from .claude/skills
context/        context about すばる (you.md, people.md, tech-stack.md)
private/        owner-only local material, excluded from Git
ledger/         durable work record, one file per seat
apps/           things built here that outgrow a conversation
docs/           documentation routed by docs/_index.md
packs/          optional Operator Day source material
outputs/        produced work
plans/          implementation plans
scripts/        cross-platform setup and verification helpers
```

## Tool routing

- Writing: follow `reference/writing-style.md`.
- Web research and scraping: use Firecrawl when configured.
- Video and YouTube: use Supadata. Large multi-platform research:
  deep-research. Social platforms and marketplaces: Apify.
- Business tools such as email, calendar, CRM, payments, Slack, Notion, or
  Sheets: use Composio when available.
- A tool not covered by Composio: run the new-capability workflow after checking
  Composio first.
- Finished software: run test, then document it and update `docs/_index.md`.
- Optional material in `packs/`: run pack-review before promoting anything.

## Working with the ledger

Write a row immediately after each meaningful unit of completed work:

`- YYYY-MM-DD HH:MM · <seat> · <area>/<type> · <one-line summary>`

Types are `build`, `decision`, `ship`, `research`, and `note`. Write only to the
current seat's file. Pure conversation with no output or decision needs no row.
Log is the backstop that catches omissions, not the normal writing mechanism.

## Cross-references

Every fact has one home. When another file needs that fact, link to its home
instead of repeating it.

Write every cross-reference as a markdown link whose path is relative to the
file being written — `[Sato-san](context/people.md)` from a file at the top
level, and `[Sato-san](../context/people.md)` from inside a folder such as
`ledger/` or `outputs/`. Never refer to a file by a bare path in prose.

Two things depend on this. The assistant follows these links to reach context it
was not given, and the links are what let this workspace be read as a connected
map rather than searched file by file, with `INDEX.md` as its front door. A file
that prose mentions but never links is reachable by neither.

Before writing a link, confirm that it resolves to a file that exists. A path
that is one folder level out is the common mistake and it fails silently: the
sentence still reads correctly and the connection is simply absent.

## Keep the constitution honest

When the workspace gains a capability, folder, or standing rule, update both
constitution files in the same session. The verification script must confirm
that they remain identical.

---

Currency: JPY (日本円). Timezone: Asia/Tokyo.
Based on Liam Ottley's AI Makeover materials, youtube.com/@LiamOttley
