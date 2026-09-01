# GH — Generate Handoff Zip

Generate a curated client handoff zip built for a non-technical client: the unzipped folder contains **exactly one file to click** — the client website, renamed `OPEN ME.html` — plus a single `Supporting Files` folder holding everything else. Clients download one zip, unzip it, double-click `OPEN ME.html`, and the whole portal works locally in their browser — no internet required.

## Zip contents

```
{Company Name} - APG Audit/
  OPEN ME.html                   ← the client website — the ONE file the client clicks
  Supporting Files/
    2-process-map.html
    3-findings.html
    4-waste.html
    5-blueprint.html
    assets/                      (bpmn-viewer library — needed for BPMN pages)
    processes/                   (interactive stage and sub-process pages)
```

`OPEN ME.html` *is* the portal (the former `1-client-website.html`). Every other page lives in `Supporting Files/`; the builder rewrites all cross-page links (the website's links into the section pages, and every page's links back to the website) so navigation works from the relocated layout. There is no separate instructions page — the website is the entry point.

Output: `{client_dir}/03-audit/handoff/v{N}/{Company} - Bosar Audit.zip`

## Steps

1. **Check which core files exist.** List the deliverables directory:
   ```bash
   ls "{client_dir}/03-audit/deliverables/"
   ```
   Confirm at minimum `1-client-website.html` is present — it becomes `OPEN ME.html`, the bundle's single entry point. If it is missing, the bundle has nothing for the client to click, so run GW first. If no deliverables exist at all, tell the user to run GP, GF, GV, GW first. Warn about any missing section files (but do not block — the zip includes whatever exists).

2. **Run the generator:**
   ```bash
   cd "{project-root}/apg-audit-plugin/skills/5-deliverable-builder/scripts"
   python3 generate.py --client-slug {client_slug} --output handoff-zip
   ```
   Via MCP: `run_script({ script: "audit/generate", args: "{\"client-slug\": \"{client_slug}\", \"output\": \"handoff-zip\"}" })`

3. **Report the result.** Show:
   - Zip path: `03-audit/handoff/v{N}/{Company} - Bosar Audit.zip`
   - Zip size (from the print output)
   - Which reports are included (the entry `OPEN ME.html` plus the section pages found)

4. **Delivery reminder.** Tell the user: "Send the zip via email or share it from the `03-audit/handoff/` folder in Google Drive. The client unzips it, double-clicks `OPEN ME.html`, and clicks through the portal. Everything works offline."

## Notes

- The zip is also generated automatically as part of `--output all`.
- For backdating existing clients, run `--output handoff-zip` for each client slug — it packages whatever deliverables already exist on disk.
- The handoff zip does NOT include: proposals or materials. These are internal files.
- Output location: `03-audit/handoff/v{N}/{Company} - Bosar Audit.zip`
