# Next.js rules

These apply to levels 1 and 2. Read this once, then follow `l1.md` or `l2.md`.

## Scaffolding

Both levels start the same way. The only difference is the package list in the last step.

```bash
pnpm dlx create-next-app@latest app \
  --ts --tailwind --eslint --app --no-src-dir \
  --import-alias "@/*" --use-pnpm --skip-install --disable-git --yes
cd app
```

`--skip-install` matters. The generator writes its own versions, some of them days old, and the cooldown policy has to be in place before anything installs.

The generator also wrote its own `pnpm-workspace.yaml`. Merge into it, keeping its `ignoredBuiltDependencies` block:

```yaml
ignoredBuiltDependencies:
  - sharp
  - unrs-resolver
savePrefix: ""
minimumReleaseAge: 10080
minimumReleaseAgeStrict: true
```

Strip the generator's versions so the policy decides them:

```bash
node -e 'const f="package.json",p=require("./"+f);delete p.dependencies;delete p.devDependencies;p.packageManager="pnpm@"+require("child_process").execSync("pnpm --version").toString().trim();p.scripts.typecheck="tsc --noEmit";require("fs").writeFileSync(f,JSON.stringify(p,null,2)+"\n")'
```

Then add by bare name. The dev packages are the same at both levels:

```bash
pnpm add -D typescript @types/node @types/react @types/react-dom \
            tailwindcss @tailwindcss/postcss eslint eslint-config-next
```

The runtime packages differ:

```bash
pnpm add next react react-dom @supabase/supabase-js               # level 1
pnpm add next react react-dom @supabase/ssr @supabase/supabase-js # level 2
```

`server-only` needs no install. Next.js resolves it internally.

## Where code runs

Next.js runs code in two places, and the difference is the whole security model.

**On the server**, code can read secret keys and talk to the database. The visitor never sees it. This is the default: every file is server code unless it says otherwise.

**In the browser**, code can respond to typing and clicking. Everything in it is visible to the visitor, including anything it imports. A file becomes browser code with `"use client"` as its first line.

A browser file that imports a server file drags the server file into the browser with it. `scripts/check-secrets.sh` checks for exactly this.

## The layout

| Concern | Rule |
| --- | --- |
| Router | App Router only. `app/` at the root, no `src/`, no `pages/` |
| Reading data | In the page itself: `export default async function Page()`, call Supabase directly |
| Writing data | A server action in `app/actions.ts`, then `revalidatePath()` to refresh the screen |
| `app/api/*/route.ts` | Only for webhooks from other services, file downloads, and sign-in callbacks |
| `"use client"` | Only for interactivity: typing, clicking, dialogs. Never imports `lib/supabase/` or `lib/env.server.ts` |
| Proxy | `proxy.ts` at the root, named export `proxy` |

Your own forms do not need a route handler. A server action is less code and cannot be called without going through your own function.

## Server actions are public endpoints

A server action compiles to a URL that anyone can call. The form is not the gate; the function is.

Check permission on the first line of every action that reads or changes data:

```ts
"use server";

export async function deleteOrder(id: string) {
  await requireSession();          // first line, every time
  // ...
}
```

`proxy.ts` redirects visitors who are not signed in, which is good for the screens. It does not protect a server action, because the action can be called directly.

## Next.js 16 specifics

The version this recipe targets renamed and changed a few things. Most examples online are older.

```ts
// The file is proxy.ts, not middleware.ts. The export is proxy, not middleware.
export function proxy(request: NextRequest) { }

// These return promises now.
const cookieStore = await cookies();
const headerList = await headers();
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
}
```

The proxy runs on Node, and that cannot be changed.

## Reading settings

One file reads the environment, and nothing else does.

`lib/env.server.ts` for server-side settings. `lib/env.ts` for the two public ones at level 2. Everything else imports from those.

Write `process.env.NEXT_PUBLIC_SUPABASE_URL` in full, spelled out. Next.js replaces that exact text at build time, so a computed name like `process.env[key]` produces nothing.

## Checking after a change

```bash
pnpm lint
pnpm typecheck
pnpm build
```

There is no test suite. The build and the type check catch the mechanical mistakes; you catch the rest by doing the job in the browser.
