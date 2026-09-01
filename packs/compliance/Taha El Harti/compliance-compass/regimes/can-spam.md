---
id: can-spam
name: CAN-SPAM Act (commercial email)
jurisdiction: US
tier: quick-ref
enforcer: market (Gmail/Yahoo bulk-sender rules — what actually disciplines founders); FTC in theory
last_verified: 2026-07-28
volatile:
  - "$53,088 per-email maximum civil penalty (Jan 2025 adjustment, frozen through 2026; expect movement Jan 2027)"
  - "mailbox-provider bulk-sender requirements (provider-set, change on their schedule)"
flip_dates:
  - "2027-01: next federal civil-penalty inflation adjustment expected (2026 round cancelled government-wide)"
---

## Does this apply to you? (triggers)

All commercial email to US recipients — every business that sends marketing email; no
thresholds. **This is an OPT-OUT regime: no consent is required to send** — a common
founder overcorrection from GDPR thinking. What IS required: truthful headers and
subject lines, identification as an ad, a physical postal address in the message, and
a working opt-out honored within **10 business days** (verified 2026-07-28).

## Who can punish you, and how

Three-bucket teaching example:
- **Law:** FTC — max civil penalty **$53,088 per non-compliant email** (verified
  2026-07-28; Jan 2025 adjustment, frozen through 2026 because the government-wide
  2026 adjustment was cancelled — expect movement Jan 2027). No private right of
  action. Enforcement is rare in practice.
- **Market (the real discipline):** Gmail/Yahoo bulk-sender rules — one-click
  unsubscribe, SPF/DKIM/DMARC authentication, spam-rate thresholds. Break these and
  your mail silently stops landing; no regulator needed.

## Penalties & enforcement reality

**Honesty statement:** government enforcement is rare and no small-company action
pattern was established in source research. The operative penalty for a startup is
deliverability collapse — market-imposed, immediate, un-appealable.

## Gap-check questions

1. Does every marketing email contain your physical mailing address and a working
   unsubscribe link?
2. Are unsubscribes honored within 10 business days — automatically, not manually?
3. Are your subject lines and from-names honest about who's sending and why?
4. Is your sending domain authenticated (SPF, DKIM, DMARC), with one-click
   unsubscribe for bulk sends?
5. Do you keep sending to addresses that opted out through any channel?

## First steps

1. Add postal address + working unsubscribe to every template (hours).
2. Wire opt-outs to auto-suppress across all sending tools (hours).
3. Set up SPF/DKIM/DMARC + one-click unsubscribe to meet mailbox-provider rules —
   exceeds the statute, but it's what keeps mail flowing (hours).

## Cost baselines

Not established in source research (authentication is configuration, not spend, on
mainstream email platforms).

## Sources

All accessed 2026-07-28: FTC CAN-SPAM compliance guide for business; Federal Register
2026 inflation-adjustment notices (frozen-adjustment note).
