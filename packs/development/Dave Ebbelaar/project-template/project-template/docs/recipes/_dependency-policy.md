# Dependencies

Every package you add is one more thing that can break, one more thing to keep current, and one more author you are trusting with your customers' data. Prefer what the language and the platform already give you.

## No version numbers in these recipes

None of the recipe files name a version. A version written today is stale next week, and a stale pin combined with the cooldown below is a hard install failure at the worst moment.

Instead the recipes fix the **mechanism**, and the mechanism picks the version at the moment you scaffold. Always in this order:

1. Write the policy file first, before adding anything.
2. Add packages by bare name: `pnpm add react`, not `pnpm add react@19.2.7`.
3. The policy resolves each name to the newest version that is at least seven days old, and writes it as an exact pin.
4. Commit the lockfile.
5. Record what you ended up with in `docs/STACK.md`.

This is self-dating. The recipe written today still produces a correct, current, pinned project a year from now.

## The seven-day cooldown

A package published in the last seven days has not been looked at by many people yet. Most supply-chain attacks are caught within days of publication, so waiting a week removes most of that risk for free.

**For JavaScript**, `pnpm-workspace.yaml`:

```yaml
savePrefix: ""
minimumReleaseAge: 10080
minimumReleaseAgeStrict: true
```

`10080` is seven days in minutes. `savePrefix: ""` is what writes exact versions instead of `^19.2.7`.

**For Python**, in `pyproject.toml`:

```toml
[tool.uv]
add-bounds = "exact"
exclude-newer = "7 days"
package = false
```

Write these before the first `pnpm add` or `uv add`. A package added before the policy exists gets a loose version and has to be redone.

## Installing

```bash
pnpm install --frozen-lockfile
uv sync --locked
```

Both refuse to change the lockfile. What you tested is what installs, on your machine and on the server. Startup scripts install nothing.

## Adding one

Ask first. Then say three things:

> `date-fns`, resolved to 4.1.0 by the policy. It handles the timezone edge cases around month boundaries that would take about forty lines to get right here.

Name, resolved version, and one sentence on why it beats writing the code. If the honest answer is "it saves eight lines," write the eight lines.

## When the cooldown blocks a build

Two packages that have to move together sometimes release on the same day, and one of them is inside the seven-day window. The install fails.

The fix is to wait, and waiting is usually fine. When it genuinely cannot wait, exempt the single package by name and write down why:

```yaml
minimumReleaseAgeExclude:
  - eslint-config-next   # must match the next major. Remove after 2026-08-04.
```

One package, a date, and a reason. Remove it once the release ages past seven days.

Relaxing `minimumReleaseAgeStrict` to make a build pass turns the guardrail off for everything, which is a different decision than the one you were trying to make.

## Recording what you got

After scaffolding, write the resolved set into `docs/STACK.md`:

```bash
pnpm list --depth 0 > docs/STACK.md          # JavaScript
uv tree --depth 1 >> docs/STACK.md           # Python
```

Six months later this is how you know what you were running.
