# INSTALL — read this and install the skill

**You are Claude Code. The user just gave you this folder (unzipped) and wants the "Proposal Deck" skill installed. Do the following, then stop and report.**

## 1. Place the skill

Copy this whole folder to the user's Claude Code skills directory, named `proposal-deck`:

- macOS / Linux: `~/.claude/skills/proposal-deck/`
- Windows: `%USERPROFILE%\.claude\skills\proposal-deck\`

Create the `skills` directory if it does not exist. If a `proposal-deck` already exists, ask the user before overwriting.

The folder must end up containing:
```
proposal-deck/
  SKILL.md
  INSTALL.md
  assets/template.html          <- the self-contained editor engine
  brand.example.json
```

## 2. Verify

Confirm `assets/template.html` exists and is ~600 KB or larger (it bundles the PDF engine). If it's missing or tiny, the download was incomplete — tell the user to re-unzip.

## 3. Offer the one-time brand setup

Ask the user:

> "Skill installed. Want to set up your brand now? Paste your website URL and I'll pull your logo, colors and font — or just tell me your brand color and font."

Follow **STEP 0** in `SKILL.md` to create `brand.json`. This only happens once.

## 4. Report

Tell the user it's ready and how to use it:

> "Done. Any time you want a proposal, just say *'make a proposal for [client]'*. I'll build a branded deck you edit in your browser and export to PDF in one click — no other setup needed."

## Notes

- The skill needs **no** extra installs (no Python, no Playwright). It only writes an HTML file and opens it in the browser.
- Pulling a call transcript is optional and uses the user's **Composio** connection (Fathom / Fireflies / Google Meet). If they don't use it, they can paste or type the content instead.
- The generated `proposal.html` is fully self-contained: it works by double-click, offline, on any OS.
