---
name: add-data
description: Add or change what the app stores. Use when the app needs to keep track of something new, when a stored record needs a new field, or when a table needs changing.
---

# Add data

Every table and every column arrives through a migration carrying its **guardrail**.

This is the moment where a mistake becomes a data leak, so there is one way to do it and the database itself refuses the alternatives.

## 1. Name the thing in their words

Ask what they call it. Their word wins: if they say "jobs", the table is `jobs`, not `projects`.

Then ask what they need to know about each one. Push for the smallest set. Columns are easy to add later and awkward to remove once something depends on them.

**Done when:** the table has a name they used themselves, and every column has a reason they gave.

## 2. Decide who each row belongs to

For each table, one of three:

- **One person owns it.** Gets a `user_id` column pointing at their account. Levels 2 only.
- **Everyone shares it.** A price list, a set of categories. Everyone signed in reads it.
- **Nobody, it is reference data.** Country codes, tax rates. Written by migration, read by all.

At levels 1 and 3 everything is effectively shared, because the server decides who sees what.

**Done when:** every table has one of these three recorded.

## 3. Write the migration

```bash
pnpm dlx supabase@latest migration new create_<name>
```

Use the template in `docs/security/migrations.md` exactly. Read the "Rules that are easy to get wrong" section in that file before writing a policy: those five mistakes each produce an app that looks right and leaks.

Include the level 2 grant and policy block only at level 2. Levels 1 and 3 get the table, row security on, and no policies.

Keep the footer as it is. It is what refuses the migration when any table anywhere has row security off.

**Done when:** the migration file exists, carries the footer unchanged, and every column from step 1 is in it.

## 4. Push it

```bash
pnpm dlx supabase@latest db push
```

If the footer raises an exception, it names the table with the problem. Fix that table. The footer is reporting something true.

Then confirm local and remote agree:

```bash
pnpm dlx supabase@latest migration list
```

**Done when:** the push succeeded, and `migration list` shows the same migrations locally and remotely.

## 5. Check the database

```bash
./scripts/check-rls.sh
```

**Done when:** it reports nothing to fix. Any finding gets a follow-up migration, never a change to the script.

## 6. Prove it, at level 2

Run the two-account test in `docs/security/rls.md` against the new table.

**Done when:** the second account sees nothing of the first account's, and they watched that happen.

## 7. Say what changed

One line in their words: what the app now remembers, and who can see it.

Append to `project/DECISIONS.md`: the table, who owns each row, and what that rules out.

## Changing an existing table

A new migration. The old ones stay as they are, because together they are the record of how the database got here.

```bash
pnpm dlx supabase@latest migration new add_<column>_to_<table>
```

```sql
alter table public.orders add column status text not null default 'new';
```

A new column on an existing table needs a default, or the migration fails on every row already there. Ask what an existing record should say, and make that the default.

The footer goes on this migration too.
