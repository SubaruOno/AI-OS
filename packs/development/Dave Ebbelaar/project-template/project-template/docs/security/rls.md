# Row security

Row security is the database's own answer to "which rows is this person allowed to see." It runs underneath your website, so it still holds when the website has a bug.

"The screen does not show other people's records" is a design choice. "Other people's records cannot be read" is security. Only the second survives a bug.

## The three postures

Each level protects data a different way. Knowing which one you are on tells you what to check.

| | Level 1 | Level 2 | Level 3 |
| --- | --- | --- | --- |
| Who talks to the database | your server only | the browser directly | your backend only |
| Automatic web API | on, unused | on, used | **off** |
| Row security | on, **no rules** | on, **one rule set per table** | on, **no rules** |
| Signed-out visitors | no access | no access | no access |
| Who decides access | the shared password | **the database** | your backend code |

Levels 1 and 3 are safe because the correct number of rules is zero. Nobody can write a bad rule that does not exist. Row security stays on so that if the automatic API is ever reachable, it returns nothing.

Level 2 is the one that depends on rules being right, because the browser talks to the database directly. That is why level 2 owns the strictest template and why `/level-up` ends by proving the rules work with a second test account.

## What a rule looks like

```sql
create policy "orders_select_own" on public.orders
  for select to authenticated
  using ( (select auth.uid()) = user_id );
```

Read it aloud: for signed-in people, when reading orders, show a row when the row's `user_id` matches the person asking.

Four things are load-bearing:

- `for select` names the action. Each of select, insert, update, delete needs its own rule.
- `to authenticated` names who. Leaving it out includes signed-out visitors.
- `using` decides which existing rows are visible or changeable.
- `with check` decides what a row is allowed to become. Insert and update need it.

A table with the four rules from `docs/security/migrations.md` is fully covered: each person reads, creates, changes, and deletes their own rows, and nobody else's.

## Proving it works

Reading the rules is not proof. Two accounts is proof.

1. Sign in as one account, create a record.
2. Sign out, sign in as a second account.
3. Look for the first account's record.

Seeing nothing is the pass. It is the only check that tells you whether a level 2 app is safe.

`/level-up` finishes on exactly this test, and it does not report done without it.

## The automated check

```bash
./scripts/check-rls.sh
```

It asks the live database eight questions and reports anything that would leak data:

- A table with row security off
- A rule that lets signed-out visitors read everything
- A rule that trusts a field users can edit themselves
- A view that runs with its owner's permissions instead of the viewer's
- A saved view, which cannot carry row security at all
- A function with elevated permissions and no fixed search path
- A file storage bucket set to public
- Any leftover permission held by signed-out visitors

Each finding says what it is, where it is, and what someone could do with it. Run it after every migration and before every deploy. `./scripts/preflight.sh` runs it for you.

## The human backstop

Supabase runs its own security review. Open the dashboard, then Advisors, then Security Advisor, once after your first deploy. Confirm there are no errors.

It catches a few things the script does not, and it is free.

## When a finding appears

Fix the database, not the check. The script reports what is true; changing the script changes what you know, not what is real.

Tell your assistant:

> fix the database security findings

It will write a migration that closes the hole and push it.
