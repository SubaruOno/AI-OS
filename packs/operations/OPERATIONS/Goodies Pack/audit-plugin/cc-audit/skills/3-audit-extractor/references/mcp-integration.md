# CRM Data Integration Reference

This document is the source of truth for how external data is fetched and stored using the APG CRM HTTP MCP at `your-crm.example.com/api/mcp`. All meetings, emails, SMS, and calls are accessed through contact-level endpoints. No separate platform integrations (Fathom, Gmail, Drive, Deepgram) are required.

---

## Integration Strategy

All external data is fetched via the APG CRM:

- **Meetings** -- `list_contact_meetings` (Fathom recordings synced by CRM, full transcript inline)
- **Emails** -- `list_contact_emails` (Gmail synced by CRM, full body text inline)
- **SMS** -- `list_contact_sms`
- **Calls** -- `list_contact_calls` + `get_call_transcript`

After fetching via CRM, the agent writes files to the local filesystem in the exact same folder/format contracts the rest of the pipeline expects. Nothing downstream changes.

---

## Contact Lookup

Use `crm.contact_id` from `meta.json`. If not set, look it up:

```
search_contacts(query: "{company_name}")
```

Falls back to email domain if name search returns no match. Store the returned UUID as `crm.contact_id` in `meta.json`.

---

## Meeting Fetch

### Tool

```
list_contact_meetings(
  contact_id: "{crm.contact_id}",
  limit: 50,            // optional, default 20, max 50
  since: "{iso_date}",  // optional — only meetings after this date
  before: "{iso_date}"  // optional — only meetings before this date
)
```

### Response Fields

```json
{
  "id": "uuid",                          // CRM meeting UUID — used as recording_id
  "title": "Adam and Jordan",
  "started_at": "2026-04-16T04:01:14+00:00",
  "ended_at": "2026-04-16T04:45:59+00:00",
  "duration_seconds": 2685,
  "attendees": [
    {"name": "Jordan Lee", "email": "jordan@brightsideservices.com.au"},
    {"name": "Adam Goodyer", "email": "hello@apgsoftware.com"}
  ],
  "transcript": [
    {
      "text": "Hi Adam.",
      "speaker": {"display_name": "Jordan Lee", "matched_calendar_invitee_email": "jordan@..."},
      "timestamp": "00:00:00"
    }
  ],
  "ai_analysis": {
    "summary": "...",
    "actionItems": ["..."],
    "meetingType": "client_checkin",
    "overallScore": 7
  },
  "recording_url": "https://fathom.video/share/..."
}
```

The full transcript is returned inline — no second call needed.

### Transcript Conversion

CRM returns `timestamp` as `"HH:MM:SS"`. Convert to `[MM:SS] Speaker: text` for transcript.txt:

```
Parse HH:MM:SS → total_seconds = H*3600 + M*60 + S
Display: if total_seconds < 3600: "[MM:SS]", else "[H:MM:SS]"
Speaker: transcript[i].speaker.display_name
```

For `timestamp_seconds` in source attribution: `H*3600 + M*60 + S`.

### Output Files

Write to `clients/{slug}/01-materials/meetings/{YYYY-MM-DD}-{title-slug}/`:

**transcript.txt:**
```
Meeting: {title}
Date: {started_at}

[00:00] Jordan Lee: Hi Adam.
[00:04] Adam Goodyer: Good thanks.
```

**metadata.json:**
```json
{
  "recording_id": "{meeting.id}",
  "title": "{meeting.title}",
  "date": "{meeting.started_at}",
  "duration_seconds": 2685,
  "participants": [
    {"name": "Jordan Lee", "email": "jordan@brightsideservices.com.au"},
    {"name": "Adam Goodyer", "email": "hello@apgsoftware.com"}
  ],
  "fathom_url": "{meeting.recording_url}",
  "share_url": "{meeting.recording_url}"
}
```

`fathom_url` and `share_url` are both set to `recording_url` from the CRM response (a Fathom share link). This preserves backward compatibility with downstream deliverable renderers that construct deep-links from `fathom_url`.

### Deduplication

Scan existing `metadata.json` files for a matching `recording_id`. If found, skip that meeting.

### Timestamp Deep-Links

Fathom deep-link format is NOT available from the share URL alone — share links (`/share/...`) do not support `?t=` timestamps. For source attribution, `timestamp_seconds` is still recorded in the audit data so future CRM enhancements can resolve direct call links.

### Video Download

```bash
yt-dlp -o "clients/{slug}/01-materials/meetings/{folder}/recording.mp4" "{meeting.recording_url}"
```

yt-dlp supports Fathom share URLs. No API key required.

---

## Email Fetch

### Tool

```
list_contact_emails(
  contact_id: "{crm.contact_id}",
  limit: 100,
  since: "{iso_date}",
  before: "{iso_date}"
)
```

### Response Fields

```json
{
  "id": "uuid",
  "from_email": "jordan@brightsideservices.com.au",
  "from_name": "Jordan Lee",
  "to_emails": ["hello@apgsoftware.com"],
  "cc_emails": [],
  "subject": "Re: Process docs",
  "snippet": "Short preview...",
  "body_text": "Full email body text...",
  "received_at": "2026-05-18T01:00:55+00:00",
  "thread_id": "19e3899baad11bb7",
  "is_read": true,
  "has_attachments": false,
  "attachments": [
    {
      "id": "uuid",
      "filename": "process.pdf",
      "size_bytes": 12345,
      "mime_type": "application/pdf"
    }
  ]
}
```

Full body text is returned inline — no second call needed.

### Attachment Download

```
get_email_attachment(attachment_id: "{attachment.id}")
```

Returns a signed download URL (1hr expiry). Then:

```bash
curl -L -o "clients/{slug}/01-materials/emails/{folder}/{filename}" "{signed_url}"
```

### Output Files

Write to `clients/{slug}/01-materials/emails/{YYYY-MM-DD}-{subject-slug}/`:

**email.txt:**
```
From: jordan@brightsideservices.com.au
To: hello@apgsoftware.com
CC:
Date: 2026-05-18
Subject: Re: Process docs

Full email body text...
```

**metadata.json:**
```json
{
  "email_id": "{email.id}",
  "thread_id": "{email.thread_id}",
  "from": "{email.from_email}",
  "to": ["{email.to_emails}"],
  "cc": ["{email.cc_emails}"],
  "subject": "{email.subject}",
  "date": "2026-05-18",
  "date_iso": "{email.received_at}",
  "attachments": [
    {"filename": "process.pdf", "size_bytes": 12345, "mime_type": "application/pdf", "attachment_id": "{id}"}
  ]
}
```

### Deduplication

Scan existing `metadata.json` files for a matching `email_id`. If found, skip.

---

## SMS Fetch

### Tool

```
list_contact_sms(
  contact_id: "{crm.contact_id}",
  limit: 100,
  since: "{iso_date}",
  before: "{iso_date}"
)
```

### Output Files

Write to `clients/{slug}/01-materials/documents/crm-sms/{YYYY-MM-DD}-sms/`:

**sms.txt** (append all messages for that date):
```
[2026-03-12T09:14:00Z] outbound: Hey Jordan, just checking in on the timeline...
[2026-03-12T09:22:00Z] inbound: All good! We're on track.
```

**metadata.json:**
```json
{
  "sms_id": "{sms.id}",
  "sent_at": "{sms.sent_at}",
  "direction": "inbound|outbound",
  "body": "{sms.body}"
}
```

---

## Call Transcript Fetch

### Tools

```
list_contact_calls(contact_id: "{crm.contact_id}", limit: 100)
get_call_transcript(call_log_id: "{call.id}")
```

`list_contact_calls` returns transcript text inline. If detailed timed segments are needed, call `get_call_transcript` for the specific call.

### Output Files

Write to `clients/{slug}/01-materials/documents/crm-calls/{YYYY-MM-DD}-call-{N}/`:

**transcript.txt:**
```
Call: {started_at}
Duration: {duration_seconds}s

[00:00:00] Adam Goodyer: Hey Jordan, calling about the timeline...
[00:01:12] Jordan Lee: Hi Adam, yes we're all good.
```

**metadata.json:**
```json
{
  "call_id": "{call.id}",
  "started_at": "{call.started_at}",
  "duration_seconds": 120,
  "direction": "outbound"
}
```

---

## Source Attribution

SMS and call data use `kind: "document"` in the `sources[]` array:

```json
{
  "kind": "document",
  "quote": "verbatim text from SMS or call",
  "speaker": "Jordan Lee",
  "confidence": "MEDIUM",
  "document_path": "clients/{slug}/01-materials/documents/crm-sms/2026-03-12-sms/sms.txt"
}
```

Meeting transcripts continue to use `kind: "fathom"` (the CRM syncs FROM Fathom — meetings still originate from Fathom recordings):

```json
{
  "kind": "fathom",
  "quote": "verbatim text from meeting",
  "speaker": "Jordan Lee",
  "confidence": "HIGH",
  "session_id": 1,
  "timestamp_seconds": 1422
}
```
