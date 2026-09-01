#!/usr/bin/env bash
#
# Audits the live Supabase project for ways the wrong person could read your data.
#
# Needs curl and Python 3. Both are present on macOS; on Windows use Git Bash.
# Exits 0 when the database is locked down, 1 when it is not.

set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Find a working Python 3. The command is python3 on macOS and often python on
# Windows, where a bare python3 may also be a stub that opens the Microsoft
# Store instead of running. Ask each candidate to prove it executes.
PY=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done

if [ -z "$PY" ]; then
  cat <<'EOF'
FAIL  Python 3 is not available, and this check needs it to read the results.

      macOS:   it is already installed. Try opening a new terminal.
      Windows: install it from https://www.python.org/downloads/
               and tick "Add python.exe to PATH" during setup.
EOF
  exit 1
fi

level="$(cat .stack-level 2>/dev/null || echo '')"
if [ "$level" = "l0" ]; then
  echo "Level 0 has no database. Nothing to check."
  exit 0
fi

if [ -z "${SUPABASE_ACCESS_TOKEN:-}" ]; then
  cat <<'EOF'
FAIL  SUPABASE_ACCESS_TOKEN is not set.

      This check reads your database settings, so it needs permission.
      1. Open https://supabase.com/dashboard/account/tokens
      2. Generate a token and copy it.
      3. Run:  export SUPABASE_ACCESS_TOKEN=sbp_your_token_here

      Keep that line in your terminal only. It does not belong in a project file.
EOF
  exit 1
fi

if [ -z "${SUPABASE_PROJECT_REF:-}" ]; then
  cat <<'EOF'
FAIL  SUPABASE_PROJECT_REF is not set.

      It is the 20-character id in your Supabase address:
      https://<this-part>.supabase.co

      Run:  export SUPABASE_PROJECT_REF=your_project_ref
EOF
  exit 1
fi

read -r -d '' SQL <<'EOSQL' || true
select 'ROW SECURITY IS OFF' as issue,
       format('%I.%I', n.nspname, c.relname) as object,
       'Anyone who knows your project address can read, change, and delete everything in this table.' as why
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relkind in ('r','p') and not c.relrowsecurity

union all
select 'RULE IS OPEN TO THE PUBLIC',
       format('%I.%I -> %s', schemaname, tablename, policyname),
       'This rule lets signed-out visitors read rows with no restriction at all.'
  from pg_policies
 where schemaname = 'public'
   and roles::text[] && array['anon','public']
   and coalesce(qual, 'true') = 'true'

union all
select 'RULE TRUSTS SELF-SERVICE DATA',
       format('%I.%I -> %s', schemaname, tablename, policyname),
       'This rule checks a field that users can edit themselves, so anyone can grant themselves access.'
  from pg_policies
 where schemaname = 'public'
   and (coalesce(qual,'') || coalesce(with_check,'')) like '%user_metadata%'

union all
select 'VIEW SKIPS ROW SECURITY',
       format('%I.%I', n.nspname, c.relname),
       'This view runs with its owner''s permissions, so it hands out rows the viewer should not see.'
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relkind = 'v'
   and coalesce((select option_value from pg_options_to_table(c.reloptions)
                  where option_name = 'security_invoker'), 'false') <> 'true'

union all
select 'SAVED VIEW IS PUBLIC',
       format('%I.%I', n.nspname, c.relname),
       'Materialized views cannot carry row security and are served to anyone who asks.'
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relkind = 'm'

union all
select 'FUNCTION CAN BE HIJACKED',
       format('%I.%I', n.nspname, p.proname),
       'This function runs with elevated permissions and has no fixed search path, so it can be tricked into running someone else''s code.'
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.prosecdef
   and not exists (select 1 from unnest(coalesce(p.proconfig,'{}')) cfg
                    where cfg like 'search_path=%')

union all
select 'FILE STORAGE IS PUBLIC', id,
       'Every file in this bucket can be downloaded by anyone who guesses its address.'
  from storage.buckets where public

union all
select 'SIGNED-OUT VISITORS HAVE ACCESS',
       format('%s.%s (%s)', table_schema, table_name, privilege_type),
       'The signed-out role still holds permission on this table.'
  from information_schema.role_table_grants
 where table_schema = 'public' and grantee = 'anon';
EOSQL

body="$("$PY" -c 'import json,sys; print(json.dumps({"query": sys.stdin.read(), "read_only": True}))' <<<"$SQL")"

response="$(curl -sS -X POST \
  "https://api.supabase.com/v1/projects/${SUPABASE_PROJECT_REF}/database/query" \
  -H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  --data "$body")" || {
    echo "FAIL  could not reach Supabase. Check your internet connection and try again."
    exit 1
  }

"$PY" - "$response" <<'EOPY'
import json, sys

try:
    rows = json.loads(sys.argv[1])
except json.JSONDecodeError:
    print("FAIL  Supabase returned something unexpected:")
    print(sys.argv[1][:500])
    sys.exit(1)

if isinstance(rows, dict):
    message = rows.get("message") or rows.get("error") or rows
    print(f"FAIL  Supabase refused the request: {message}")
    print("      Check that SUPABASE_ACCESS_TOKEN and SUPABASE_PROJECT_REF are correct.")
    sys.exit(1)

if not rows:
    print("PASS  database security audit: nothing to fix")
    sys.exit(0)

print(f"FAIL  database security audit: {len(rows)} thing(s) to fix\n")
for row in rows:
    print(f"  {row['issue']}")
    print(f"    where: {row['object']}")
    print(f"    why:   {row['why']}\n")
print('Do not deploy yet. Tell your assistant: "fix the database security findings".')
sys.exit(1)
EOPY
