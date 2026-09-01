# Changing the database

Every table and every column arrives through a migration: a file with SQL in it, saved in your project, applied by one command. That way the shape of your database is something you can read, keep, and replay.

## The one way

```bash
pnpm dlx supabase@latest login
pnpm dlx supabase@latest init
pnpm dlx supabase@latest link --project-ref YOUR_PROJECT_REF
pnpm dlx supabase@latest migration new create_orders
# edit supabase/migrations/<timestamp>_create_orders.sql
pnpm dlx supabase@latest db push
pnpm dlx supabase@latest migration list
```

`pnpm dlx` runs the Supabase tool without installing it. There is no Docker and no local database in this setup: you link to your cloud project and push to it directly.

`migration list` should show the same set of migrations locally and remotely. When it does not, something changed the database outside this flow.

The Supabase dashboard offers a SQL editor, a table editor, and an AI assistant that will happily create tables for you. Changes made there skip the footer below, and your migration files stop describing your real database. Create tables through `migration new` so the file and the database stay the same thing.

## The template

Every table migration has this shape. Copy it, change the names, keep the footer.

```sql
-- === the table ===========================================================
create table public.orders (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null default auth.uid() references auth.users (id) on delete cascade,
  customer     text not null,
  amount_cents integer not null check (amount_cents >= 0),
  created_at   timestamptz not null default now()
);

create index orders_user_id_idx on public.orders (user_id);

-- === row security ========================================================
alter table public.orders enable row level security;

-- LEVEL 2 ONLY. Leave this block out entirely at levels 1 and 3.
grant select, insert, update, delete on public.orders to authenticated;

create policy "orders_select_own" on public.orders
  for select to authenticated
  using ( (select auth.uid()) = user_id );

create policy "orders_insert_own" on public.orders
  for insert to authenticated
  with check ( (select auth.uid()) = user_id );

create policy "orders_update_own" on public.orders
  for update to authenticated
  using ( (select auth.uid()) = user_id )
  with check ( (select auth.uid()) = user_id );

create policy "orders_delete_own" on public.orders
  for delete to authenticated
  using ( (select auth.uid()) = user_id );

-- === guardrail. keep this exactly as it is ===============================
do $guard$
declare offenders text;
begin
  select string_agg(format('%I.%I', n.nspname, c.relname), ', ')
    into offenders
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public'
     and c.relkind in ('r', 'p')
     and not c.relrowsecurity;
  if offenders is not null then
    raise exception 'BLOCKED: row security is off on: %', offenders;
  end if;

  select string_agg(format('%s.%s -> %s', table_schema, table_name, grantee), ', ')
    into offenders
    from information_schema.role_table_grants
   where table_schema = 'public' and grantee = 'anon';
  if offenders is not null then
    raise exception 'BLOCKED: signed-out visitors have access to: %', offenders;
  end if;
end
$guard$;
```

## Why the footer

It runs after your table is created and refuses the whole migration when any table in the database has row security off, or when signed-out visitors hold permission on anything.

That means `db push` fails at the exact moment someone forgets a line, including on a table added three migrations ago. The failure is loud, immediate, and names the table. Nobody has to remember anything.

Keep the footer in every table migration. When it fires, the fix is the table it names, never the footer.

## The first migration

Before any table exists, create `supabase/migrations/0000_lockdown.sql`:

```sql
-- Close the automatic web access to the database.
-- Levels 1 and 3 never reopen it. Level 2 reopens it one table at a time.

alter default privileges in schema public revoke all on tables    from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;

revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;

revoke create on schema public from anon, authenticated;
```

Supabase hands out broad permissions to new tables by default so that its automatic API works out of the box. This closes that door. Levels 1 and 3 leave it closed forever, because their server holds the secret key and does not need it. Level 2 opens it for one table at a time with the `grant` line in the template.

## Rules that are easy to get wrong

These are the mistakes that produce a working app with a hole in it.

**Wrap the user check.** Write `(select auth.uid()) = user_id`, not `auth.uid() = user_id`. With the wrapper the database works out who you are once per query; without it, once per row. On a table with 50,000 rows that is the difference between fast and unusable.

**Name the role.** Write `to authenticated` on every policy. A policy with no role named applies to signed-out visitors too.

**Update needs both halves.** `using` decides which rows you may change; `with check` decides what they may become. A policy with only `using` lets someone change a row they own into a row owned by someone else.

**Update needs select.** Without a `select` policy on the table, an update runs, matches nothing, and reports success. The row is unchanged and nobody is told.

**Roles live in a table.** Never check a role by reading `raw_user_meta_data` in a policy. Users can write that field themselves, so a policy that trusts it lets anyone make themselves an admin. Use a table:

```sql
create table public.profiles (
  id   uuid primary key references auth.users (id) on delete cascade,
  role text not null default 'member' check (role in ('member', 'admin'))
);
alter table public.profiles enable row level security;
grant select on public.profiles to authenticated;

create policy "profiles_select_own" on public.profiles
  for select to authenticated
  using ( (select auth.uid()) = id );

-- There is deliberately no update policy here, so nobody can change their own role.

create function public.current_app_role()
returns text
language sql
stable
security definer
set search_path = ''
as $$ select role from public.profiles where id = (select auth.uid()) $$;
```

`set search_path = ''` is required. A function with elevated permissions and no fixed search path can be tricked into running someone else's code.

Then an admin policy reads:

```sql
create policy "orders_admin_all" on public.orders
  for all to authenticated
  using ( public.current_app_role() = 'admin' )
  with check ( public.current_app_role() = 'admin' );
```

## Changing an existing table

Add a new migration. The old ones stay as they are, because they are the record of how the database got to where it is.

```bash
pnpm dlx supabase@latest migration new add_status_to_orders
```

```sql
alter table public.orders add column status text not null default 'new';
```

The footer belongs on this one too.

## Checking it worked

```bash
./scripts/check-rls.sh
```

It reads the live database and reports anything that would let the wrong person see the wrong records. Run it after every migration.
