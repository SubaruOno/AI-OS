---
description: Sync latest meeting transcripts for the current client via the CRM and update audit-data.json
---

Run the process mapper's sync-and-update workflow for the specified client:

1. Fetch new meetings via the APG CRM (`list_contact_meetings`)
2. Fetch new emails via the APG CRM (`list_contact_emails`)
3. Extract process data from any new transcripts into `audit-data.json`
4. Report what was found and any new follow-up questions

Client: $ARGUMENTS
