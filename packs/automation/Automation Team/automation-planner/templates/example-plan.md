# Invoice Chaser

*This is a worked example of a finished routine-path plan. Match its tone and level of detail when filling in `automation-plan.md`. It would live at `automations/spec/invoice-chaser/automation-plan.md`.*

**What this automation does:** Finds invoices marked overdue in your invoice sheet and sends the customer a polite reminder email, so you never have to chase payments by hand again.

**Why this one:** If customers grew tenfold, getting paid on time is what would break first; chasing invoices is the biggest by-hand chore inside it.

**Where it lives:** A Claude routine: an assistant that runs on a schedule and follows the steps below.

## When it runs

Every weekday morning around 9:00, Rome time.

## The apps it connects

- **Google Sheets**: the invoice tracker where amounts, due dates, and payment status live
- **Gmail**: sends the reminder emails from your own address
- **Slack**: tells you what it did each morning

## Step by step

1. Every weekday at 9:00, open the invoice sheet and find invoices that are past their due date and not marked paid.
2. Skip any invoice that was already reminded in the last 7 days, so customers aren't nagged.
3. For each remaining invoice, check how late it is and pick the right message: a friendly nudge under 14 days, a firmer reminder after that.
4. Send the reminder email from Gmail to the customer's billing address.
5. Post a short summary in your Slack #finance channel: who was reminded, who was skipped, and anything that needs your attention.

```
[Every weekday, 9:00]
         |
         v
+----------------------+   none overdue
| Check the invoice    |------> post "all paid up"
| sheet for overdue    |        in Slack, done
+----------------------+
         |
         v
+----------------------+   reminded < 7 days ago
| For each invoice:    |------> skip it
| pick friendly or     |
| firm reminder        |
+----------------------+
         |
         v
+----------------------+
| Send email via Gmail |
+----------------------+
         |
         v
+----------------------+
| Post summary in      |
| Slack #finance       |
+----------------------+
```

## When something goes wrong

- **An invoice has no email address:** it gets sent to you in Slack to handle by hand; the automation carries on with the rest.
- **The same invoice shows up twice:** the second one is ignored; each customer gets at most one reminder per invoice per week.
- **The sheet or Gmail is briefly unreachable:** the automation stops for that morning and lets you know in Slack, then simply tries again on its next scheduled run.

## How you'll know it's working

A short Slack message in #finance each weekday morning: how many reminders went out, who was skipped, and anything that needs your attention. Silence means it didn't run, so if a morning goes by with no message, tell your builder.

## What we still need from you

- Connect Google Drive, Gmail, and Slack at claude.ai/customize/connectors (takes a minute each; the builder can walk you through it)
- The wording you'd like for the friendly and the firm reminder (or approve a draft the builder writes)
- A "last reminded" column in the invoice sheet, so the 7-day skip has somewhere to look (the builder can add it)

---

## Notes for the builder

*This section is technical. It's for the person or AI who will build the automation.*

**Target:** Claude routine (scheduled cloud agent). Create with the `/schedule` flow in Claude Code; manage or delete at https://claude.ai/code/routines. The routine runs in the cloud with no access to the owner's machine, local files, or local logins.

**Schedule:** weekdays 09:00 Europe/Rome. Convert to a UTC cron expression at creation time (09:00 CEST = 07:00 UTC, so `0 7 * * 1-5` in summer; re-check at DST changes). Minimum interval is 1 hour.

**Connections needed:** Google Drive (for the sheet), Gmail, Slack. Verify each is connected at claude.ai/settings/connectors before creating the routine; the owner connects missing ones at claude.ai/customize/connectors.

**To confirm at creation time:** environment; git repository (any default repo works, the routine doesn't need project files); model (default claude-sonnet-5).

**Draft instructions for the routine** (self-contained; adjust as needed):

```
You are the Invoice Chaser routine. Your job: remind customers about overdue
invoices, then report what you did.

1. Open the Google Sheet named "Invoice Tracker" (Finance folder). Find rows
   where the due date is in the past and the Status column is not "Paid".
2. Skip any invoice whose "Last reminded" date is within the last 7 days.
3. For each remaining invoice: if it is fewer than 14 days late, send the
   friendly reminder; 14 days or more, send the firm reminder. Send from the
   owner's Gmail to the address in the "Billing email" column. Use the approved
   wording stored in the sheet's "Templates" tab.
4. After sending, write today's date in that row's "Last reminded" column.
5. If an invoice has no billing email, do not guess an address. Add it to the
   report as "needs your attention".
6. Post one short summary message in Slack #finance: how many reminders sent
   (friendly vs firm), who was skipped and why, and anything needing attention.
   If nothing is overdue, post "All paid up today."
7. If the sheet or Gmail cannot be reached, post a one-line notice in Slack
   #finance and stop; the next scheduled run will try again.

Never email anyone except addresses found in the "Billing email" column.
Never send more than one reminder per invoice per run.
```

**Plan date:** 2026-07-28

**Change log:**

- 2026-07-28: first version of this plan.
