#!/usr/bin/env bash
#
# Every check that has to pass before your app goes on the internet.
#
# Run this yourself any time: ./scripts/preflight.sh

set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

step() { printf '\n=== %s\n' "$1"; }

level="$(cat .stack-level 2>/dev/null || echo '')"

if [ "$level" = "l0" ]; then
  echo "Level 0 is a skill, not a website. There is nothing to deploy."
  echo "Run your skill in your assistant to check it works."
  exit 0
fi

if [ -z "$level" ]; then
  echo "FAIL  .stack-level is missing. Ask your assistant to run the start procedure."
  exit 1
fi

step "Lockfiles are committed"
dirty="$(git status --porcelain -- pnpm-lock.yaml frontend/pnpm-lock.yaml backend/uv.lock 2>/dev/null || true)"
if [ -n "$dirty" ]; then
  echo "FAIL  a lockfile changed but was not committed:"
  echo "$dirty"
  echo "      Commit it so the deployed version installs exactly what you tested."
  exit 1
fi
echo "ok    lockfiles match what is committed"

case "$level" in
  l1|l2)
    step "Installing exactly what is locked"
    pnpm install --frozen-lockfile || exit 1

    step "Checking code style"
    pnpm lint || exit 1

    step "Checking types"
    pnpm typecheck || exit 1

    step "Building for production"
    pnpm build || exit 1
    ;;

  l3)
    step "Backend: installing exactly what is locked"
    (cd backend && uv sync --locked) || exit 1

    step "Backend: checking code style"
    (cd backend && uv run --locked --no-sync ruff check .) || exit 1
    (cd backend && uv run --locked --no-sync ruff format --check .) || exit 1

    step "Frontend: installing exactly what is locked"
    (cd frontend && pnpm install --frozen-lockfile) || exit 1

    step "Frontend: checking code style"
    (cd frontend && pnpm lint) || exit 1

    step "Frontend: checking types"
    (cd frontend && pnpm typecheck) || exit 1

    step "Frontend: building for production"
    (cd frontend && pnpm build) || exit 1
    ;;

  *)
    echo "FAIL  .stack-level holds '$level', which is not one of: l0, l1, l2, l3"
    exit 1
    ;;
esac

step "Checking nothing secret reaches the browser"
./scripts/check-secrets.sh || exit 1

step "Checking the database is locked down"
./scripts/check-rls.sh || exit 1

echo
echo "PASS  everything checks out. Safe to deploy."
