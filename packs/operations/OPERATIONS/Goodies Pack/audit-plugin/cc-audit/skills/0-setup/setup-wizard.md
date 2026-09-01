# Audit Setup Wizard [SW]

Verify and configure audit prerequisites. This is a STANDALONE Bosar install: there is no PM plugin and no CRM MCP. Meeting transcripts, emails, and documents are placed directly into the client folder under `01-materials/`. Never ask the user to run `/pm:0-setup` and never treat a missing CRM as a blocker.

## Step 1: Client Data Directory

Read `${CLAUDE_PLUGIN_ROOT}/config.yaml` for `paths.clients_dir`.

**If `clients_dir` is set:** show "Client data directory: `{clients_dir}`" and ask "Keep this path? [Y/n]". If no, ask for a new absolute path and write it back to `${CLAUDE_PLUGIN_ROOT}/config.yaml` -> `paths.clients_dir`.

**If `clients_dir` is blank:** ask the user for the absolute path where client folders live (a local folder or a Google Drive for Desktop mount both work). Write it to `${CLAUDE_PLUGIN_ROOT}/config.yaml` -> `paths.clients_dir`.

**Verification:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/_paths.py
```

Show the output. Confirm `clients_dir` resolves correctly and `clients.json` is found (offer to create a minimal one if missing).

## Step 2: Data Sources (informational, never a blocker)

This install has no CRM. Explain briefly:

- Meeting transcripts go in `{clients_dir}/{slug}/01-materials/meetings/{YYYY-MM-DD}-{title-slug}/transcript.txt` (+ optional `metadata.json`)
- Client emails go in `{clients_dir}/{slug}/01-materials/emails/{YYYY-MM-DD}-{subject-slug}/email.html` (+ `metadata.json`)
- Documents go in `{clients_dir}/{slug}/01-materials/documents/`

All extraction skills work from these local folders. CRM sync steps in any skill are skipped automatically (no `crm.project_id` means all CRM updates are silently skipped by design).

Show: "CRM: not configured (standalone mode) - transcripts are read from local meeting folders."

## Step 3: Client Folder Structure

Ask which client to verify (or verify all from `clients.json`).

For each selected client, verify the folder structure exists (use the `clients_dir` from Step 1):
```
{clients_dir}/{slug}/
  00-admin/                   {exists/missing}
  01-materials/meetings/      {exists/missing}
  01-materials/documents/     {exists/missing}
  01-materials/emails/        {exists/missing}
  02-sales/                   {exists/missing}
  03-audit/data/              {exists/missing}
  03-audit/deliverables/      {exists/missing}
  03-audit/handoff/           {exists/missing}
  _archive/                   {exists/missing}
```

Create any missing directories:
```bash
mkdir -p "{clients_dir}/{slug}/00-admin" "{clients_dir}/{slug}/01-materials/meetings" "{clients_dir}/{slug}/01-materials/documents" "{clients_dir}/{slug}/01-materials/emails" "{clients_dir}/{slug}/02-sales" "{clients_dir}/{slug}/03-audit/data" "{clients_dir}/{slug}/03-audit/deliverables" "{clients_dir}/{slug}/03-audit/handoff" "{clients_dir}/{slug}/_archive"
```

## Step 4: Python Dependencies

Check the packages the pipeline scripts need:

```bash
python3 -c "import pptx" 2>&1   # python-pptx, for follow-up question decks
python3 -c "import PIL" 2>&1    # Pillow, used by image tooling
```

If missing, offer to install: `pip3 install python-pptx Pillow`

## Step 5: Verification Report

```
Bosar Audit Setup -- Verification Report
=======================================
Clients dir:         {path} ✓
clients.json:        found ({N} clients) ✓
Client folders:      {N} clients verified ✓
Data mode:           local folders (standalone, no CRM) ✓
Python deps:         python-pptx ✓  Pillow ✓

Status: READY -- run /audit:3-audit-extractor to begin
```
