#!/usr/bin/env python3
"""Google Gmail CLI tool for workspace-wide email access.

Claude Code or Codex can call this cross-platform Python CLI.
Supports search, read, thread, draft, send, reply, and inbox management.

Usage:
    python scripts/gmail_tool.py profile                                    # Account info
    python scripts/gmail_tool.py inbox [--max 20]                           # Unread inbox
    python scripts/gmail_tool.py search "from:nick newer_than:30d"          # Search
    python scripts/gmail_tool.py read MESSAGE_ID                            # Read message
    python scripts/gmail_tool.py thread THREAD_ID                           # Full thread
    python scripts/gmail_tool.py labels                                     # List labels
    python scripts/gmail_tool.py attachments MESSAGE_ID                     # List attachments
    python scripts/gmail_tool.py download MESSAGE_ID ATT_ID --output f.pdf  # Download attachment
    python scripts/gmail_tool.py draft "to@x.com" "Subject" "Body"         # Create draft
    python scripts/gmail_tool.py reply THREAD_ID "Body" [--send]            # Reply (draft or send)
    python scripts/gmail_tool.py send DRAFT_ID                              # Send a draft
    python scripts/gmail_tool.py send-new "to@x.com" "Subject" "Body"      # Send directly
    python scripts/gmail_tool.py mark-read MESSAGE_ID                       # Mark as read
    python scripts/gmail_tool.py mark-unread MESSAGE_ID                     # Mark as unread
    python scripts/gmail_tool.py label MESSAGE_ID "LabelName"              # Add label
    python scripts/gmail_tool.py unlabel MESSAGE_ID "LabelName"            # Remove label
    python scripts/gmail_tool.py trash MESSAGE_ID                           # Trash (recoverable)
"""

import argparse
import base64
import re
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from google_auth import get_google_service


def _get_gmail():
    """Get authenticated Gmail API service."""
    return get_google_service("gmail", "v1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_body(payload: dict, preferred_mime: str = "text/plain") -> str:
    """Recursively extract body text from a Gmail message payload.

    Walks the MIME tree looking for preferred_mime first, then falls back
    to text/html with tag stripping.
    """
    # Single-part message
    if "parts" not in payload:
        mime = payload.get("mimeType", "")
        data = payload.get("body", {}).get("data", "")
        if data and mime == preferred_mime:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        if data and mime == "text/html" and preferred_mime == "text/plain":
            html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            return _strip_html(html)
        return ""

    # Multipart: recurse into parts
    texts = []
    html_fallback = ""
    for part in payload.get("parts", []):
        mime = part.get("mimeType", "")
        if mime.startswith("multipart/"):
            result = _get_body(part, preferred_mime)
            if result:
                return result
        elif mime == preferred_mime:
            data = part.get("body", {}).get("data", "")
            if data:
                texts.append(base64.urlsafe_b64decode(data).decode("utf-8", errors="replace"))
        elif mime == "text/html" and not texts:
            data = part.get("body", {}).get("data", "")
            if data:
                html_fallback = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    if texts:
        return "\n".join(texts)
    if html_fallback:
        return _strip_html(html_fallback)
    return ""


def _strip_html(html: str) -> str:
    """Basic HTML tag stripping for fallback body extraction."""
    # Remove style and script blocks
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Convert <br> and </p> to newlines
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</p>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</div>", "\n", html, flags=re.IGNORECASE)
    # Strip remaining tags
    html = re.sub(r"<[^>]+>", "", html)
    # Collapse whitespace
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def _get_header(headers: list, name: str) -> str:
    """Get a header value by name (case-insensitive)."""
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value", "")
    return ""


def _format_message_summary(msg: dict) -> str:
    """Format a message for list display (one line)."""
    headers = msg.get("payload", {}).get("headers", [])
    subject = _get_header(headers, "Subject") or "(no subject)"
    sender = _get_header(headers, "From")
    date_str = _get_header(headers, "Date")
    msg_id = msg["id"]
    thread_id = msg.get("threadId", "")

    # Parse and format date
    date_display = date_str[:22] if date_str else ""
    try:
        # Try common formats
        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %z"]:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                date_display = dt.strftime("%Y-%m-%d %H:%M")
                break
            except ValueError:
                continue
    except Exception:
        pass

    # Shorten sender
    if "<" in sender:
        sender_short = sender.split("<")[0].strip().strip('"')
        if not sender_short:
            sender_short = sender.split("<")[1].rstrip(">")
    else:
        sender_short = sender

    labels = msg.get("labelIds", [])
    unread = " *" if "UNREAD" in labels else "  "

    return f"{unread} {date_display}  {sender_short[:25]:<25}  {subject[:60]}  [id:{msg_id} t:{thread_id}]"


def _format_message_full(msg: dict) -> str:
    """Format a full message for display."""
    headers = msg.get("payload", {}).get("headers", [])
    lines = []

    lines.append(f"From:    {_get_header(headers, 'From')}")
    lines.append(f"To:      {_get_header(headers, 'To')}")
    cc = _get_header(headers, "Cc")
    if cc:
        lines.append(f"Cc:      {cc}")
    lines.append(f"Date:    {_get_header(headers, 'Date')}")
    lines.append(f"Subject: {_get_header(headers, 'Subject')}")
    lines.append(f"ID:      {msg['id']}  Thread: {msg.get('threadId', '')}")

    labels = msg.get("labelIds", [])
    if labels:
        lines.append(f"Labels:  {', '.join(labels)}")

    lines.append("")
    lines.append("-" * 60)

    body = _get_body(msg.get("payload", {}))
    if body:
        lines.append(body)
    else:
        lines.append("(no readable body)")

    return "\n".join(lines)


def _build_mime(to: str, subject: str, body: str, cc: str = None, bcc: str = None,
                in_reply_to: str = None, references: str = None, thread_id: str = None) -> dict:
    """Build a Gmail-compatible MIME message payload."""
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    msg.set_content(body)

    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    result = {"raw": encoded}
    if thread_id:
        result["threadId"] = thread_id
    return result


def _lookup_label_id(service, label_name: str) -> str:
    """Find label ID by name (case-insensitive)."""
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"].lower() == label_name.lower():
            return label["id"]
    print(f"ERROR: Label '{label_name}' not found. Run 'labels' to see available labels.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Read commands
# ---------------------------------------------------------------------------

def cmd_profile(args):
    """Show Gmail account profile."""
    service = _get_gmail()
    profile = service.users().getProfile(userId="me").execute()
    print(f"Account:  {profile.get('emailAddress', 'unknown')}")
    print(f"Messages: {profile.get('messagesTotal', 0):,}")
    print(f"Threads:  {profile.get('threadsTotal', 0):,}")


def cmd_inbox(args):
    """Show unread inbox messages."""
    service = _get_gmail()
    max_results = args.max

    results = service.users().messages().list(
        userId="me", q="is:unread in:inbox", maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    estimate = results.get("resultSizeEstimate", 0)
    print(f"Inbox: ~{estimate} unread (showing {len(messages)})\n")

    if not messages:
        print("  No unread messages.")
        return

    # Batch fetch message details
    for m in messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        print(_format_message_summary(msg))


def cmd_search(args):
    """Search messages using Gmail query syntax."""
    service = _get_gmail()
    max_results = args.max

    all_messages = []
    page_token = None

    while len(all_messages) < max_results:
        kwargs = {
            "userId": "me",
            "q": args.query,
            "maxResults": min(max_results - len(all_messages), 100),
        }
        if page_token:
            kwargs["pageToken"] = page_token

        results = service.users().messages().list(**kwargs).execute()
        batch = results.get("messages", [])
        all_messages.extend(batch)

        page_token = results.get("nextPageToken")
        if not page_token or not batch:
            break

    print(f"Search: \"{args.query}\" ({len(all_messages)} results)\n")

    if not all_messages:
        print("  No messages found.")
        return

    for m in all_messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        print(_format_message_summary(msg))


def cmd_read(args):
    """Read a full message by ID."""
    service = _get_gmail()

    if args.format == "raw":
        msg = service.users().messages().get(
            userId="me", id=args.message_id, format="raw"
        ).execute()
        raw = base64.urlsafe_b64decode(msg["raw"]).decode("utf-8", errors="replace")
        print(raw)
    else:
        msg = service.users().messages().get(
            userId="me", id=args.message_id, format="full"
        ).execute()
        print(_format_message_full(msg))


def cmd_thread(args):
    """Read all messages in a thread."""
    service = _get_gmail()

    thread = service.users().threads().get(
        userId="me", id=args.thread_id, format="full"
    ).execute()

    messages = thread.get("messages", [])
    print(f"Thread: {args.thread_id} ({len(messages)} messages)\n")

    for i, msg in enumerate(messages):
        if i > 0:
            print()
            print("=" * 60)
            print()
        print(_format_message_full(msg))


def cmd_labels(args):
    """List all labels."""
    service = _get_gmail()

    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    # Sort: system labels first, then user labels
    system = [l for l in labels if l.get("type") == "system"]
    user = [l for l in labels if l.get("type") != "system"]
    system.sort(key=lambda x: x["name"])
    user.sort(key=lambda x: x["name"])

    print(f"Labels ({len(labels)} total)\n")
    if user:
        print("User labels:")
        for l in user:
            print(f"  {l['name']:<40} [id:{l['id']}]")

    print("\nSystem labels:")
    for l in system:
        print(f"  {l['name']:<40} [id:{l['id']}]")


def cmd_attachments(args):
    """List attachments on a message."""
    service = _get_gmail()

    msg = service.users().messages().get(
        userId="me", id=args.message_id, format="full"
    ).execute()

    attachments = []

    def _walk_parts(parts):
        for part in parts:
            filename = part.get("filename", "")
            if filename:
                body = part.get("body", {})
                size = body.get("size", 0)
                att_id = body.get("attachmentId", "")
                mime = part.get("mimeType", "unknown")
                attachments.append({
                    "filename": filename,
                    "mime": mime,
                    "size": size,
                    "attachmentId": att_id,
                })
            if "parts" in part:
                _walk_parts(part["parts"])

    payload = msg.get("payload", {})
    if "parts" in payload:
        _walk_parts(payload["parts"])

    headers = payload.get("headers", [])
    subject = _get_header(headers, "Subject") or "(no subject)"
    print(f"Attachments for: {subject}")
    print(f"Message ID: {args.message_id}\n")

    if not attachments:
        print("  No attachments found.")
        return

    for att in attachments:
        size_kb = att["size"] / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
        print(f"  {att['filename']:<40} {att['mime']:<30} {size_str}")
        if att["attachmentId"]:
            print(f"    attachment_id: {att['attachmentId'][:40]}...")


def cmd_download(args):
    """Download an attachment."""
    service = _get_gmail()

    att = service.users().messages().attachments().get(
        userId="me", messageId=args.message_id, id=args.attachment_id
    ).execute()

    data = base64.urlsafe_b64decode(att["data"])

    output = Path(args.output)
    output.write_bytes(data)
    print(f"Downloaded: {output} ({len(data):,} bytes)")


# ---------------------------------------------------------------------------
# Write commands
# ---------------------------------------------------------------------------

def cmd_draft(args):
    """Create a draft email."""
    service = _get_gmail()

    message = _build_mime(args.to, args.subject, args.body, cc=args.cc, bcc=args.bcc)
    draft = service.users().drafts().create(
        userId="me", body={"message": message}
    ).execute()

    draft_id = draft["id"]
    print(f"Draft created: {draft_id}")
    print(f"  To: {args.to}")
    print(f"  Subject: {args.subject}")
    print(f"\nSend with: python scripts/gmail_tool.py send {draft_id}")


def cmd_reply(args):
    """Reply to a thread. Creates draft by default, --send to send immediately."""
    service = _get_gmail()

    # Get the last message in the thread for reply headers
    thread = service.users().threads().get(
        userId="me", id=args.thread_id, format="metadata",
        metadataHeaders=["From", "Subject", "Message-ID", "To"]
    ).execute()

    messages = thread.get("messages", [])
    if not messages:
        print("ERROR: Thread is empty.", file=sys.stderr)
        sys.exit(1)

    last_msg = messages[-1]
    headers = last_msg.get("payload", {}).get("headers", [])

    # Build reply headers
    message_id = _get_header(headers, "Message-ID")
    subject = _get_header(headers, "Subject")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Reply to the sender of the last message
    reply_to = _get_header(headers, "From")

    message = _build_mime(
        to=reply_to,
        subject=subject,
        body=args.body,
        in_reply_to=message_id,
        references=message_id,
        thread_id=args.thread_id,
    )

    if args.send:
        sent = service.users().messages().send(userId="me", body=message).execute()
        print(f"Reply sent: {sent['id']}")
        print(f"  To: {reply_to}")
        print(f"  Thread: {args.thread_id}")
    else:
        draft = service.users().drafts().create(
            userId="me", body={"message": message}
        ).execute()
        draft_id = draft["id"]
        print(f"Reply draft created: {draft_id}")
        print(f"  To: {reply_to}")
        print(f"  Subject: {subject}")
        print(f"  Thread: {args.thread_id}")
        print(f"\nSend with: python scripts/gmail_tool.py send {draft_id}")


def cmd_send(args):
    """Send an existing draft."""
    service = _get_gmail()

    result = service.users().drafts().send(
        userId="me", body={"id": args.draft_id}
    ).execute()

    msg_id = result.get("id", "unknown")
    thread_id = result.get("threadId", "")
    print(f"Sent: {msg_id}")
    print(f"  Thread: {thread_id}")


def cmd_send_new(args):
    """Compose and send a new message directly."""
    service = _get_gmail()

    message = _build_mime(args.to, args.subject, args.body, cc=args.cc, bcc=args.bcc)
    result = service.users().messages().send(userId="me", body=message).execute()

    msg_id = result.get("id", "unknown")
    print(f"Sent: {msg_id}")
    print(f"  To: {args.to}")
    print(f"  Subject: {args.subject}")


def cmd_mark_read(args):
    """Mark a message as read."""
    service = _get_gmail()
    service.users().messages().modify(
        userId="me", id=args.message_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()
    print(f"Marked read: {args.message_id}")


def cmd_mark_unread(args):
    """Mark a message as unread."""
    service = _get_gmail()
    service.users().messages().modify(
        userId="me", id=args.message_id,
        body={"addLabelIds": ["UNREAD"]}
    ).execute()
    print(f"Marked unread: {args.message_id}")


def cmd_label(args):
    """Add a label to a message."""
    service = _get_gmail()
    label_id = _lookup_label_id(service, args.label_name)
    service.users().messages().modify(
        userId="me", id=args.message_id,
        body={"addLabelIds": [label_id]}
    ).execute()
    print(f"Added label '{args.label_name}' to {args.message_id}")


def cmd_unlabel(args):
    """Remove a label from a message."""
    service = _get_gmail()
    label_id = _lookup_label_id(service, args.label_name)
    service.users().messages().modify(
        userId="me", id=args.message_id,
        body={"removeLabelIds": [label_id]}
    ).execute()
    print(f"Removed label '{args.label_name}' from {args.message_id}")


def cmd_trash(args):
    """Move a message to trash (recoverable for 30 days)."""
    service = _get_gmail()
    service.users().messages().trash(userId="me", id=args.message_id).execute()
    print(f"Trashed: {args.message_id}")
    print("  Recoverable for 30 days.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gmail CLI tool")
    sub = parser.add_subparsers(dest="command", required=True)

    # profile
    sub.add_parser("profile", help="Account info")

    # inbox
    p = sub.add_parser("inbox", help="Unread inbox messages")
    p.add_argument("--max", type=int, default=20, help="Max results (default 20)")

    # search
    p = sub.add_parser("search", help="Search messages (Gmail query syntax)")
    p.add_argument("query", help="Gmail search query")
    p.add_argument("--max", type=int, default=10, help="Max results (default 10)")

    # read
    p = sub.add_parser("read", help="Read a message")
    p.add_argument("message_id")
    p.add_argument("--format", choices=["full", "raw"], default="full")

    # thread
    p = sub.add_parser("thread", help="Read all messages in a thread")
    p.add_argument("thread_id")

    # labels
    sub.add_parser("labels", help="List all labels")

    # attachments
    p = sub.add_parser("attachments", help="List attachments on a message")
    p.add_argument("message_id")

    # download
    p = sub.add_parser("download", help="Download an attachment")
    p.add_argument("message_id")
    p.add_argument("attachment_id")
    p.add_argument("--output", required=True, help="Output file path")

    # draft
    p = sub.add_parser("draft", help="Create a draft email")
    p.add_argument("to", help="Recipient email")
    p.add_argument("subject")
    p.add_argument("body")
    p.add_argument("--cc")
    p.add_argument("--bcc")

    # reply
    p = sub.add_parser("reply", help="Reply to a thread (draft by default)")
    p.add_argument("thread_id")
    p.add_argument("body")
    p.add_argument("--send", action="store_true", help="Send immediately instead of drafting")

    # send (existing draft)
    p = sub.add_parser("send", help="Send an existing draft")
    p.add_argument("draft_id")

    # send-new
    p = sub.add_parser("send-new", help="Compose and send directly")
    p.add_argument("to", help="Recipient email")
    p.add_argument("subject")
    p.add_argument("body")
    p.add_argument("--cc")
    p.add_argument("--bcc")

    # mark-read
    p = sub.add_parser("mark-read", help="Mark message as read")
    p.add_argument("message_id")

    # mark-unread
    p = sub.add_parser("mark-unread", help="Mark message as unread")
    p.add_argument("message_id")

    # label
    p = sub.add_parser("label", help="Add a label to a message")
    p.add_argument("message_id")
    p.add_argument("label_name")

    # unlabel
    p = sub.add_parser("unlabel", help="Remove a label from a message")
    p.add_argument("message_id")
    p.add_argument("label_name")

    # trash
    p = sub.add_parser("trash", help="Trash a message (recoverable)")
    p.add_argument("message_id")

    args = parser.parse_args()
    cmd_map = {
        "profile": cmd_profile,
        "inbox": cmd_inbox,
        "search": cmd_search,
        "read": cmd_read,
        "thread": cmd_thread,
        "labels": cmd_labels,
        "attachments": cmd_attachments,
        "download": cmd_download,
        "draft": cmd_draft,
        "reply": cmd_reply,
        "send": cmd_send,
        "send-new": cmd_send_new,
        "mark-read": cmd_mark_read,
        "mark-unread": cmd_mark_unread,
        "label": cmd_label,
        "unlabel": cmd_unlabel,
        "trash": cmd_trash,
    }
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
