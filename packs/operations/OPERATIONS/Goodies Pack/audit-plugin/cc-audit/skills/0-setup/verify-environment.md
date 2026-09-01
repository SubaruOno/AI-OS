# Verify Audit Environment [VE]

Re-run all audit checks without changing config. Standalone Bosar install: no PM plugin, no CRM - never report either as a failure.

## Procedure

1. **Config:** Read `${CLAUDE_PLUGIN_ROOT}/config.yaml`. Report `user_name` and `paths.clients_dir` (pass if set, fail if blank).

2. **Paths:** Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/_paths.py` and report whether `clients_dir` resolves and `clients.json` is found.

3. **Client folders:** For each client in `clients.json`, check the standard folder structure (00-admin, 01-materials/{meetings,documents,emails}, 02-sales, 03-audit/{data,deliverables,handoff}). Report per client.

4. **Data mode:** Report "local folders (standalone, no CRM)" - informational, always a pass.

5. **Python deps:** Check `python-pptx` and `Pillow` imports. Report pass/fail with the install command if missing.

6. **Display report:** Same format as Setup Wizard Step 5. Do not modify any files in this mode.
