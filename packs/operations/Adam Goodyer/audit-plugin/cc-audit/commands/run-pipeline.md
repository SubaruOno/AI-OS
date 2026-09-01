---
description: Run the full Process Mapper extraction pipeline for a client in one trigger — sync → ingest → process review → findings review → waste review.
---

Activate the `3-audit-extractor` skill. When the skill menu is presented, immediately run **[RX] Run Extractor Pipeline**, forwarding any arguments the user provided after `/audit:run-pipeline` (e.g. `--force`, `--gate`, `--from PR`, `--only FR,WR`, `--skip IM`), without waiting for the user to choose.

Client: $ARGUMENTS
