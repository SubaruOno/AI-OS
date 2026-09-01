---
description: Build a zippable client handover bundle — the offline portal + comprehensive PDF + source audit JSON
---

Package an offline copy of the specified client's portal (everything that is
deployed, navigable locally) plus the comprehensive PDF and the source audit
JSON, zipped for handing to the client. Packaging only — does not regenerate or
deploy.

1. Identify the client-key or slug from `$ARGUMENTS` or the active conversation
   context.
2. Check that current HTML deliverables exist in
   `clients/{slug}/deliverables/`. If stale or missing, regenerate first
   (`generate.py --output all`, then GC for the PDF) before packaging.
3. From the **repo root**, run:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/5-deliverable-builder/scripts/build_handover.py --client {client-key-or-slug}`
4. Report the zip path + size and the bundle folder. Tell the user to open the
   unzipped `index.html` to verify navigation before sending the zip.

**Important:** Package only the client explicitly named. The script copies the
current deliverables as-is — it never deploys.

Client: $ARGUMENTS
