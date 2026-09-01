# New teammate

> Add a person to the shared workspace with their own seat and a bilingual,
> dual-harness onboarding pack. Claude Code also exposes this as
> `/new-teammate`.

## Variables

`args: $ARGUMENTS` may contain the person's name.

## Rules

- Use a conversation, explain before acting, and confirm between phases.
- Default open on direction and working context. Default closed on margins,
  compensation, deal terms, and personal material.
- Require a private GitHub backup before creating a shared seat.
- Generate user-facing install documents in both English and Japanese.
- Offer Claude Code and Codex equally, on Windows and macOS.
- Never place the owner's `.env` or secrets in the onboarding pack.

## 1. Define the role

Ask for the person's name and what they will own. Read existing team context and
write `team/<name>.md`: role, mandate, success measures, ownership, and working
notes. Read it back and correct it until approved.

## 2. Audit sharing

Review every context document and classify it as shared, role-scoped, or
owner-only. Move private material to `private/` with approval. Explain that
moving a tracked secret protects future versions but does not erase old Git
history.

Write `context/shared-manifest.md` with the shared documents and per-seat extras.

## 3. Create the seat

Create `ledger/<name>.md` with the ledger format. Prepare a `.seat` file for the
pack containing `person: <name>`. A teammate prime loads the active constitution,
the shared manifest, `team/<name>.md`, and the recent ledger. It never loads
`private/`.

## 4. Grant access

Guide the owner through adding the teammate as a GitHub collaborator. Build a
role-scoped `.env.example` containing variable names and official sign-up links
only. The teammate creates their own keys through the hidden local secret
prompt.

## 5. Create the bilingual onboarding pack

Create `outputs/onboarding/welcome-<name>/` and a matching zip containing:

1. **WELCOME.md**, with complete English and Japanese sections. Explain what the
   shared workspace is, what their seat provides, and these choices:
   - Windows or macOS;
   - Claude desktop app and Claude Code, or ChatGPT desktop app and Codex;
   - open the onboarding folder and say “Read INSTALL.md and set me up” or
     「INSTALL.mdを読んで、設定してください」.
2. **INSTALL.md**, written for either Claude Code or Codex. It must:
   - detect the harness, OS, and conversation language;
   - welcome the teammate by name;
   - help them accept the GitHub invitation and clone the company repository;
   - write `.seat` into the clone;
   - create `.env` locally and use `scripts/set_secret.py` for every key;
   - open the cloned folder in the chosen harness;
   - ask them to say “Prime this workspace” or
     「このワークスペースを読み込んでください」;
   - complete one small real task and run log once;
   - explain prime, log, and handoff in ordinary language.
3. **.env.example**, with only the role's variable names and links.

Do not say that a Claude subscription is the only supported cost. Say that each
person needs access to whichever product they choose, and that external services
may have their own current plans.

## 6. Give the owner a brief

Save `outputs/onboarding/<name>-brief.md` with what the teammate can and cannot
see, what to send, what to expect in their ledger, and the one habit to teach:
prime at the start, log when a unit of work is complete.

Run the log workflow automatically.
