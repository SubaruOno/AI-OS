# 01-materials — Client Inputs

All raw inputs from the client, organized by source type.

| Subfolder | Contents | Written by |
|-----------|----------|------------|
| meetings/ | Meeting transcripts (Fathom recordings fetched via CRM) | Extractor [SU] via CRM |
| documents/ | Client-provided files: process docs, spreadsheets, org charts, screenshots | Manual |
| emails/ | Client email threads | Extractor [SU] via CRM |

## meetings/

Each session gets its own folder named `YYYY-MM-DD-title-slug/` containing:
- `transcript.txt` — full meeting transcript
- `metadata.json` — Meeting metadata (recording_id, duration, participants, fathom_url)
- `recording.mp4` — optional, only if downloaded

The folder name's date prefix is used by the Extractor to match sessions against `extraction.json` sessions[].

## documents/

Flat folder. Client-provided files go here as-is:
- Process documentation PDFs
- Spreadsheets (.xlsx, .csv)
- Org charts and diagrams
- Screenshots from client systems

Naming: use original filenames where possible. Prefix with `YYYY-MM-DD-` if date matters.

## emails/

Each email thread gets its own folder named `YYYY-MM-DD-subject-slug/` containing:
- `email.html` — full email body
- `metadata.json` — sender, recipients, date, subject, thread ID
- `attachments/` — any email attachments

Do NOT put generated outputs here. Do NOT put audit data here. Generated HTML deliverables go in `../03-audit/deliverables/`.
