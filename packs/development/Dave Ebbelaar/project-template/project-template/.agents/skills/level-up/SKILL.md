---
name: level-up
description: Renovate a level 1 app so it serves more than one person. Use when the app needs sign-ins, when different people should see different records, or when roles like admin are needed.
---

# Level up

A **renovation**: same building, new front door, locks on the internal rooms. They keep living in it while the work happens.

Going from level 1 to level 2 changes who can see what. Nothing gets rebuilt.

## 1. Confirm it is the right move

Read `project/BRIEF.md`. Ask one question:

> Does each person need to see a different set of records, or does everyone see the same thing behind one shared password?

**Everyone sees the same thing** means level 1 is still right. Stop here, and append the question and answer to `project/DECISIONS.md` so the next person to ask gets the answer without redoing this.

**Different people, different records** continues.

Say what this costs them: every person needs their own email sign-in, and existing records need an owner. Fifteen minutes of their time in step 3.

**Done when:** they have chosen, and the choice is in `DECISIONS.md`.

## 2. Inventory what exists

List every table, every screen, and every place data is read or written.

Nothing gets summarised as "and the others". Every table that is missed here is a table that leaks in step 4.

**Done when:** the list accounts for every file under the app directory and every table in the database, each named.

## 3. Give every row an owner

For each table from step 2, one of three:

- **One person owns it.** Gets a `user_id` column pointing at `auth.users`.
- **Everyone shares it.** A price list, a set of categories.
- **Only admins touch it.** Needs the `profiles` table and role function.

Then the awkward part: rows that already exist have no owner. Ask who should own them. Usually it is them, and the migration sets their account id as the default for existing rows.

**Done when:** every table from step 2 has a recorded decision, and existing rows have an owner named.

## 4. Turn on the locks

Follow the auth section of `docs/recipes/l2.md` and the template in `docs/security/migrations.md`.

Each person-owned table gets the grant and all four policies. Read the "Rules that are easy to get wrong" section before writing them; those five mistakes each produce an app that looks right and leaks.

For roles, use the `profiles` table and the `security definer` function in that same file. A role check that reads `raw_user_meta_data` lets anyone make themselves an admin, because users can write that field.

Then run `./scripts/check-rls.sh`.

**Done when:** `check-rls.sh` reports nothing, and every table from step 2 has policies covering select, insert, update, and delete.

## 5. Add the front door

Follow `docs/recipes/l2.md` for the three Supabase clients, `proxy.ts`, and the sign-in screens.

Then the part the proxy does not cover: every server action re-checks who is asking on its first line. A server action is a URL anyone can call, and the proxy only guards screens.

Delete the shared password from level 1: `lib/session.ts`, the login screen, and the `APP_PASSWORD` and `APP_SESSION_SECRET` settings.

**Done when:** a signed-out visitor is sent to sign-in from every screen in step 2's list, and every server action checks on its first line.

## 6. Prove it with two accounts

Run the two-account test in `docs/security/rls.md`, covering every table from step 2. This is the step that makes the renovation real.

**Done when:** the second account sees nothing belonging to the first, in every table from step 2, and they watched it happen.

Anything visible means a policy is missing or wrong. Fix it and run the test again from the start.

## 7. Rewrite the brief

Set `.stack-level` to `l2`. Update `project/BRIEF.md` to say level 2, and name the roles.

Append the renovation to `project/DECISIONS.md`: why they moved, which tables became person-owned, and what the shared password was replaced with.

Add any new slices to `project/SLICES.md`. Sign-in usually reveals two or three: inviting people, resetting a password, a screen showing who has access.

## 8. Redeploy

Run `/deploy`. The settings change: the two public ones replace the four private ones. Remove the old ones from the hosting provider rather than leaving them.

**Done when:** the live app requires sign-in, and they signed in on it themselves.
