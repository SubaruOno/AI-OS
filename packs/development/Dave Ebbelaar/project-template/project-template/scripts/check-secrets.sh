#!/usr/bin/env bash
#
# Checks that no password, key, or database address can reach a visitor's browser.
#
# Reads .stack-level to decide which settings names are allowed to be public.
# Exits 0 when everything passes, 1 when something needs fixing.

set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

fail=0
bad() { printf 'FAIL  %s\n' "$1"; fail=1; }
ok()  { printf 'ok    %s\n' "$1"; }

level="$(cat .stack-level 2>/dev/null || echo '')"

case "$level" in
  l0)
    echo "Level 0 has no website and no database. Nothing to check."
    exit 0
    ;;
  l1)
    prefix='NEXT_PUBLIC_'
    allow=''
    bundle='.next'
    src='app lib components'
    ;;
  l2)
    prefix='NEXT_PUBLIC_'
    allow='NEXT_PUBLIC_SUPABASE_URL NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY'
    bundle='.next'
    src='app lib components'
    ;;
  l3)
    prefix='VITE_'
    allow='VITE_API_BASE_URL VITE_SUPABASE_URL VITE_SUPABASE_PUBLISHABLE_KEY'
    bundle='frontend/dist'
    src='frontend/src'
    ;;
  *)
    echo "FAIL  .stack-level is missing or unreadable."
    echo "      It should hold one of: l0, l1, l2, l3."
    echo "      Ask your assistant to run the start procedure."
    exit 1
    ;;
esac

# Only look at directories that actually exist yet.
present=''
for dir in $src; do
  [ -d "$dir" ] && present="$present $dir"
done

if [ -z "$present" ]; then
  echo "FAIL  none of these folders exist yet: $src"
  echo "      Build the app before running this check."
  exit 1
fi

echo "Checking a level $(echo "$level" | tr -d 'l') project."
echo

# 1. No settings file was ever committed to git.
tracked_env="$(git ls-files 2>/dev/null | grep -E '(^|/)\.env($|\.)' | grep -v '\.example$' || true)"
if [ -n "$tracked_env" ]; then
  bad "a settings file is committed to git: $(echo "$tracked_env" | tr '\n' ' ')"
  echo "      Anyone who can see this repository can read those values."
else
  ok "no settings file is tracked by git"
fi

# 2. Only allowlisted names carry a browser-visible prefix.
found="$(grep -rhoE "${prefix}[A-Z0-9_]+" $present 2>/dev/null | sort -u || true)"
unlisted=0
for name in $found; do
  case " $allow " in
    *" $name "*) ;;
    *)
      bad "$name is published to every visitor's browser and is not on the allowlist"
      echo "      Rename it without the ${prefix} prefix and read it on the server."
      unlisted=1
      ;;
  esac
done
[ "$unlisted" -eq 0 ] && ok "every browser-visible setting is on the allowlist"

# 3. No secret-shaped text is written directly into the code.
if grep -rInE 'sb_secret_|sbp_[A-Za-z0-9]{20}|service_role|postgres(ql)?://' $present 2>/dev/null; then
  bad "a key or database address is written directly into the code, above"
  echo "      Move the value into .env.local and read it through the settings file."
else
  ok "no keys or database addresses written into the code"
fi

# 4. Anything reading the secret key is marked as server-only.
while IFS= read -r file; do
  [ -n "$file" ] || continue
  grep -q 'server-only' "$file" || {
    bad "$file reads the secret key without the server-only marker"
    echo "      Add: import \"server-only\";  as its first line."
  }
done < <(grep -rlE 'SUPABASE_SECRET_KEY' $present 2>/dev/null || true)

# 5. No browser component reaches into a server-only file.
while IFS= read -r file; do
  [ -n "$file" ] || continue
  if head -3 "$file" | grep -q '"use client"'; then
    bad "$file runs in the browser and imports a server-only file"
    echo "      Move that work into a server action and call it from here."
  fi
done < <(grep -rlE "from ['\"]@/lib/(env\.server|supabase/admin)" $present 2>/dev/null || true)

# 6. The decisive check: does a real secret value appear in what ships to browsers?
if [ -d "$bundle" ]; then
  leaked=0
  for var in SUPABASE_SECRET_KEY DATABASE_URL APP_PASSWORD APP_SESSION_SECRET SUPABASE_ACCESS_TOKEN POSTGRES_PASSWORD; do
    value="$(grep -hs "^${var}=" .env.local .env backend/.env frontend/.env 2>/dev/null | head -1 | cut -d= -f2- | tr -d "\"'")"
    [ -n "${value:-}" ] && [ "${#value}" -ge 12 ] || continue
    if grep -rqsF -- "$value" "$bundle"; then
      bad "the value of $var is inside $bundle, which ships to browsers"
      echo "      This is a live leak. Rotate that value in Supabase before deploying."
      leaked=1
    fi
  done
  if grep -rqsE 'sb_secret_|sbp_[A-Za-z0-9]{20}' "$bundle"; then
    bad "a secret key pattern is present in $bundle"
    leaked=1
  fi
  [ "$leaked" -eq 0 ] && ok "no secret values found in $bundle"
else
  bad "$bundle does not exist"
  echo "      Run the production build first, then run this check again."
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "PASS  nothing secret can reach a visitor's browser"
else
  echo "Fix the findings above before deploying."
fi
exit "$fail"
