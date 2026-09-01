---
name: google-gmail
description: >
  Gmail API integration via CLI tool. Email search, read, thread, draft, send, reply, inbox
  management, label operations, attachments. Find emails, email context, inbox triage,
  draft reply, send email, thread lookup, attachment download, mark read, Gmail search syntax.
---

# Gmail API

CLI tool at `scripts/gmail_tool.py`. All commands run via Bash. Auth handled by shared Google OAuth module (`scripts/google_auth.py`).

**Account:** Your Gmail account (configured during Google OAuth setup)
**Scope:** `gmail.modify` (read, write, send, labels, trash. No permanent delete.)

## CLI Reference

```bash
# Account
python scripts/gmail_tool.py profile

# Read
python scripts/gmail_tool.py inbox [--max 20]
python scripts/gmail_tool.py search "QUERY" [--max 10]
python scripts/gmail_tool.py read MESSAGE_ID [--format raw]
python scripts/gmail_tool.py thread THREAD_ID
python scripts/gmail_tool.py labels
python scripts/gmail_tool.py attachments MESSAGE_ID
python scripts/gmail_tool.py download MESSAGE_ID ATTACHMENT_ID --output path/file.pdf

# Write
python scripts/gmail_tool.py draft "to@email.com" "Subject" "Body" [--cc "cc@x.com"] [--bcc "b@x.com"]
python scripts/gmail_tool.py reply THREAD_ID "Body text" [--send]
python scripts/gmail_tool.py send DRAFT_ID
python scripts/gmail_tool.py send-new "to@email.com" "Subject" "Body" [--cc "cc@x.com"]

# Manage
python scripts/gmail_tool.py mark-read MESSAGE_ID
python scripts/gmail_tool.py mark-unread MESSAGE_ID
python scripts/gmail_tool.py label MESSAGE_ID "LabelName"
python scripts/gmail_tool.py unlabel MESSAGE_ID "LabelName"
python scripts/gmail_tool.py trash MESSAGE_ID
```

## Gmail Search Syntax

The `search` command accepts full Gmail search syntax via the `q` parameter.

### People
| Operator | Example | What it finds |
|----------|---------|---------------|
| `from:` | `from:alice` | Messages from Alice (partial match) |
| `to:` | `to:you@email.com` | Messages sent to you |
| `cc:` | `cc:bob` | Messages where Bob is CC'd |

### Content
| Operator | Example | What it finds |
|----------|---------|---------------|
| `subject:` | `subject:invoice` | Subject contains "invoice" |
| `"exact phrase"` | `"board meeting minutes"` | Exact phrase in body or subject |
| `filename:` | `filename:pdf` | Attachments with .pdf extension |
| `has:attachment` | `has:attachment` | Any message with attachments |

### Date
| Operator | Example | What it finds |
|----------|---------|---------------|
| `newer_than:Nd` | `newer_than:7d` | Last 7 days |
| `newer_than:Nm` | `newer_than:3m` | Last 3 months |
| `newer_than:Ny` | `newer_than:1y` | Last year |
| `older_than:` | `older_than:6m` | Older than 6 months |
| `after:` | `after:2026/01/01` | After specific date |
| `before:` | `before:2026/03/01` | Before specific date |

### Status and Location
| Operator | Example | What it finds |
|----------|---------|---------------|
| `is:unread` | `is:unread` | Unread messages |
| `is:read` | `is:read` | Read messages |
| `is:starred` | `is:starred` | Starred messages |
| `is:important` | `is:important` | Important messages |
| `in:inbox` | `in:inbox` | Inbox only |
| `in:sent` | `in:sent` | Sent messages |
| `in:drafts` | `in:drafts` | Draft messages |
| `in:trash` | `in:trash` | Trashed messages |
| `in:anywhere` | `in:anywhere` | All mail including trash/spam |

### Size
| Operator | Example | What it finds |
|----------|---------|---------------|
| `larger:` | `larger:5M` | Larger than 5MB |
| `smaller:` | `smaller:100K` | Smaller than 100KB |

### Boolean
| Operator | Example | What it finds |
|----------|---------|---------------|
| `OR` | `from:alice OR from:bob` | From either person |
| `-` | `-category:promotions` | Exclude promotions |
| `( )` | `(from:alice OR from:bob) subject:project` | Grouped conditions |

### Compound Examples

```
# Company formation docs buried in history
from:lawyer subject:"company formation" has:attachment

# Recent correspondence with someone
from:alice newer_than:30d

# Old invoices
subject:invoice has:attachment filename:pdf older_than:6m

# Urgent inbox (filter noise)
is:unread in:inbox -category:promotions -category:social -category:updates

# Large attachments
has:attachment larger:10M newer_than:90d

# Find a specific document
filename:pdf "contract" in:anywhere
```

## Common Patterns

### Deep Document Search
Find specific documents buried in email history:
```bash
python scripts/gmail_tool.py search "has:attachment filename:pdf subject:contract in:anywhere"
python scripts/gmail_tool.py attachments MESSAGE_ID
python scripts/gmail_tool.py download MESSAGE_ID ATTACHMENT_ID --output ./document.pdf
```

### Person/Thread Lookup
Find all recent emails from someone and read the full thread:
```bash
python scripts/gmail_tool.py search "from:alice newer_than:90d"
python scripts/gmail_tool.py thread THREAD_ID
```

### Urgent Inbox Triage
Check unread, draft a reply, send after review:
```bash
python scripts/gmail_tool.py inbox
python scripts/gmail_tool.py read MESSAGE_ID
python scripts/gmail_tool.py reply THREAD_ID "Reply body here"
python scripts/gmail_tool.py send DRAFT_ID
```

### Inbox Management
```bash
python scripts/gmail_tool.py mark-read MESSAGE_ID
python scripts/gmail_tool.py label MESSAGE_ID "Follow-up"
python scripts/gmail_tool.py trash MESSAGE_ID
```

## Message Structure

Search and inbox commands return one-line summaries with IDs:
```
 * 2026-03-15 09:30  Alice Smith     Project update  [id:18e1234abcde t:18e1234abcdf]
```

- `*` = unread, space = read
- `id:` = message ID (use with `read`, `attachments`, `mark-read`, etc.)
- `t:` = thread ID (use with `thread`, `reply`)

The `read` command shows full headers + decoded body. `thread` shows all messages in order.

## Rate Limits

- 15,000 quota units/min per user
- Reads: 5 units each (3,000 reads/min)
- Sends: 100 units each (150/min)

## Safety

- **No permanent delete.** `trash` moves to trash (recoverable for 30 days). The CLI doesn't expose `messages.delete`.
- **Draft-then-send pattern.** Default for `reply` is to create a draft. Use `--send` flag for immediate send.
- **Scope is `gmail.modify`**, not `mail.google.com`. Prevents permanent deletion at the API level.

## Auth

Shared Google OAuth with Calendar. Token stored at `credentials/google-oauth-token.json` after OAuth setup.

If token is missing or expired:
```bash
# First: save your OAuth client JSON as credentials/google-client.json
# (console.cloud.google.com → Credentials → OAuth client ID → Desktop app)
python scripts/setup_google_oauth.py
# On macOS, use python3 if python is unavailable.
```

**Account:** Set up via scripts/setup_google_oauth.py

## Maintenance

**Known gotchas:**
1. `messages.list` returns only `{id, threadId}`, not message content. Each message needs a separate `messages.get` call.
2. All message content is base64url encoded (not standard base64). The CLI handles this.
3. UNREAD is a label, not a field. Read/unread is managed via label add/remove.
4. Replying requires `In-Reply-To` + `References` headers + `threadId` for correct threading. The `reply` command handles this.
5. Attachments >2MB have empty `body.data` and need a separate `attachments.get` call. The `download` command handles this.
6. Date search operators use PST timezone internally. Use `newer_than:Nd` for relative dates (timezone-safe).
7. `resultSizeEstimate` in search results is approximate. Don't trust it for exact counts.
8. Adding Gmail scope to an existing Calendar-only token requires re-running `setup_google_oauth.py` (deletes old token, re-authorizes all scopes).

**Files:**
- CLI tool: `scripts/gmail_tool.py`
- Auth module: `scripts/google_auth.py`
- Setup: `scripts/setup_google_oauth.py`
- Token: `credentials/google-oauth-token.json`
