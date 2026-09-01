---
name: build-prototype
description: Generate clickable Next.js prototype using Untitled UI components and MCP integration from architecture documentation. Visual demo for client presentation.
menu-code: BP
---

# Build Prototype (BP)

> **Idempotent.** First run scaffolds the project and generates prototype from scratch. Re-runs regenerate from updated architecture.

## Purpose

Generate a clickable prototype from `architecture_doc` using real Untitled UI React components inside a standalone Next.js project at `clients/{slug}/03-audit/prototype/`. Each prototype is scaffolded from the `untitled-ui/` template project and can diverge independently. The prototype uses the client's actual data from audit-data.json — real names, real tools, real numbers. This is a visual demo for client presentation, not a functional application.

## Untitled UI MCP — Required Tools

This capability relies on the `untitledui` MCP server (`https://www.untitledui.com/react/api/mcp`). The following MCP tools MUST be used throughout prototype generation — do NOT guess component imports or icon names.

| MCP Tool | When to Use | Example Call |
|---|---|---|
| `list_components` | Browse all available components by category | `list_components("application")` |
| `search_components` | Find components by natural language description | `search_components("data table with pagination")` |
| `get_component` | Get exact import path, props, and usage for one component | `get_component("table")` |
| `get_component_bundle` | Retrieve multiple components at once | `get_component_bundle(["table", "pagination", "badge"])` |
| `get_page_templates` | Find pre-built page layouts as starting points | `get_page_templates("dashboard")` |
| `get_page_template_files` | Get install command for a page template | `get_page_template_files("{template_id}")` |
| `search_icons` | Find icons by keyword | `search_icons("calendar")` |

**HARD REQUIREMENT:** All UI components MUST be Untitled UI components. Do NOT generate custom components, raw HTML, or Tailwind-only markup when an Untitled UI component exists. If the MCP is unavailable AND the component cannot be found locally in `clients/{slug}/03-audit/prototype/src/components/`, STOP and notify the user — do not proceed with non-Untitled-UI alternatives.

---

## Pre-flight

1. Load audit data:
   - Check for `clients/{slug}/03-audit/data/audit-manifest.json`. If present (v4): read all domain files directly:
     - `clients/{slug}/03-audit/data/meta.json`
     - `clients/{slug}/03-audit/data/extraction.json`
     - `clients/{slug}/03-audit/data/findings.json`
     - `clients/{slug}/03-audit/data/opportunities.json`
     - `clients/{slug}/03-audit/data/strategy.json`
     - `clients/{slug}/03-audit/data/architecture.json`
   - For v3 files (no manifest, `_schema_version` starts with "3"): load all domains from `audit-data.json`.
   - For v2 files: load the full `audit-data.json`.

   Check `architecture_doc` exists (`architecture.architecture_doc` in v3/v4, top-level in v2).
   - If missing: warn and suggest running [BA] first.

1b. Check `architecture_verification` exists in audit-data.json.
   - If missing: warn "Architecture not verified. Run [VA] first to ensure pain point coverage before building prototype."
   - If `architecture_verification.summary.verification_pass` is `false`: warn "Architecture verification has {n} blocking issues. Fix architecture and re-run [VA] before building prototype." List the `blocking_issues[]`.
   - If present and passing: load `architecture_verification.prototype_brief[]` — this is the explicit brief for what each screen must demonstrate. Every page generated must reference its prototype brief entry, ensuring each screen demonstrates specific pain point resolutions with the correct interaction model.

2. Check the `untitled-ui/` **template** project exists at `{project-root}/untitled-ui/`:
   - Verify `package.json` exists with `untitledui` dependencies
   - Verify `src/components/` has base and application component directories
   - If missing: warn that Untitled UI template project needs to be initialised first

3. Check for the client prototype at `{project-root}/clients/{slug}/03-audit/prototype/`:
   - If it **does not exist**: mark as "needs scaffolding" (will be handled in Stage 0)
   - If it **exists**: verify `package.json` and `src/components/` are present

4. **>>> MCP CALL — REQUIRED:** Verify Untitled UI MCP connectivity:
   - Call `list_components` with category `"base"` — if it returns a component list, MCP is connected
   - **If MCP unavailable:** Check if components exist locally at `clients/{slug}/03-audit/prototype/src/components/base/` and `clients/{slug}/03-audit/prototype/src/components/application/`
   - **If NEITHER MCP nor local components are available: STOP.** Notify the user: "Untitled UI MCP is unavailable and components are not installed locally. Run `claude mcp add --transport http untitledui https://www.untitledui.com/react/api/mcp` or install components in the client prototype project before proceeding."
   - MCP server URL: `https://www.untitledui.com/react/api/mcp` (configured as `untitledui` MCP)

5. Show readiness summary:
   ```
   PROTOTYPE BUILD — {company_name}
   Strategy: {selected_strategy_id}
   Pages to generate: {n} (from architecture_doc.page_structure.pages)
   User journeys to wire: {n} (from architecture_doc.user_journeys)
   Roles for switcher: {n} (from architecture_doc.access_policies)
   Modules: {n} ({list of module names})

   Template project: untitled-ui/ {found|missing}
   Client prototype: clients/{slug}/03-audit/prototype/ {scaffolded|needs scaffolding}
   Untitled UI MCP: {connected|unavailable}
   Output: clients/{slug}/03-audit/prototype/src/app/(prototype)/
   ```

6. Ask user for prototype scope:
   ```
   Prototype scope:
     A) Full prototype — all {n} pages, all {n} journeys
     B) Key journeys — top 5 journeys by annual value
     C) Single module — prototype one module in depth

   Select scope:
   ```

7. If `clients/{slug}/03-audit/prototype/src/app/(prototype)/` already exists, ask:
   ```
   Existing prototype found.
   Options:
     A) Full rebuild — regenerate all screens
     B) Cancel
   ```

---

## Stage 0: Scaffold Client Prototype

> **Skip if `clients/{slug}/03-audit/prototype/` already exists and is valid.**

If the client prototype directory does not exist, scaffold it from the `untitled-ui/` template.

### 0a. Copy template files

Copy the entire `untitled-ui/` project to `clients/{slug}/03-audit/prototype/`, EXCLUDING:
- `node_modules/`
- `.next/`
- `src/app/(prototype)/` (each client starts fresh)
- `src/app/home-screen.tsx` (template homepage, not needed)
- `bun.lockb` (will be regenerated)

```bash
rsync -a --exclude='node_modules' --exclude='.next' --exclude='src/app/(prototype)' --exclude='src/app/home-screen.tsx' --exclude='bun.lockb' untitled-ui/ clients/{slug}/03-audit/prototype/
```

### 0b. Extract Client Branding

Before building, scrape the client's website to extract their brand colors and logo. This makes the prototype feel tailor-made.

1. **Find the client's website URL** — check `audit-data.json` for `company_website`, or `prospect-profile.json` for `research.website`, or ask the user.

2. **>>> WebFetch** the client's homepage HTML. Extract branding signals:

   **Colors** (check in order, use first found):
   - `<meta name="theme-color" content="...">` 
   - CSS custom properties in `<style>` blocks: `--primary`, `--brand`, `--color-primary`
   - Header/hero `background-color` or `background` in inline styles or `<style>` blocks
   - CTA button colors (look for `.btn`, `.button`, `[class*="cta"]` styles)
   - Link color (`a { color: ... }`)
   - If homepage CSS is in an external stylesheet URL, **>>> WebFetch** that stylesheet too

   **Logo** (check in order, use first found):
   - `<meta property="og:image" content="...">` (often the logo or branded image)
   - `<link rel="apple-touch-icon" href="...">` 
   - `<img>` inside `<header>` or `<nav>` with "logo" in `src`, `alt`, or `class`
   - `<link rel="icon" href="...">` (favicon, last resort)

3. **Store** extracted branding in the audit data:
   - v4: load `clients/{slug}/03-audit/data/architecture.json`, merge `branding` into the existing dict, write the full dict back to `clients/{slug}/03-audit/data/architecture.json`, then update `audit-manifest.json`: set `domains.architecture.updated_at` and root `updated_at`.
   - v3: write into `architecture.branding` in `audit-data.json`
   - v2: write to top-level `branding` in `audit-data.json`
   ```json
   "branding": {
     "primary_color": "#hex",
     "secondary_color": "#hex",
     "accent_color": "#hex",
     "logo_url": "https://...",
     "source_url": "https://client-website.com"
   }
   ```
   If only one color found, set `primary_color` and leave others null.

4. **Show** extracted colors and logo URL to the user for confirmation before proceeding. Display color swatches if possible.

5. **Fallback** — if the website is unavailable, returns errors, or no colors can be extracted:
   - Ask the user to provide hex codes manually
   - If the user has no preference, proceed with Untitled UI default brand palette
   - Set `branding: null` in audit-data.json

### 0c. Install dependencies

```bash
cd clients/{slug}/03-audit/prototype && npm install
```

### 0d. Update metadata

Edit `clients/{slug}/03-audit/prototype/src/app/layout.tsx`:
- Change `title` from "Starter kit — Untitled UI" to `"{company_name} — Prototype"`
- Change `description` to `"Clickable prototype for {company_name}"`

### 0e. Replace landing page

Replace `clients/{slug}/03-audit/prototype/src/app/page.tsx` with a redirect to `/dashboard`:

```tsx
import { redirect } from "next/navigation";
export default function Home() {
    redirect("/dashboard");
}
```

### 0f. Verify scaffold

Confirm the project compiles:
```bash
cd clients/{slug}/03-audit/prototype && npx next build
```

If build succeeds (ignoring pre-existing type errors in unused template components), scaffold is complete.

---

## Stage 1: Project Setup

Create the prototype route group and shared infrastructure inside `clients/{slug}/03-audit/prototype/`.

### 1a. Create route group

Create `clients/{slug}/03-audit/prototype/src/app/(prototype)/` as a Next.js route group. This keeps prototype routes separate from any other pages.

### 1b. Create prototype layout

> **IMPORTANT: Match your-crm-app patterns.** Read `references/demo-crm-patterns.md` for the target visual structure. The actual build will duplicate the your-crm-app project and modify it, so the prototype must look and feel like that app. The sidebar, page layouts, navigation patterns, and component usage should all match.

Create `clients/{slug}/03-audit/prototype/src/app/(prototype)/layout.tsx`.

**Required imports** — use the Untitled UI navigation components already installed in the prototype:
```tsx
import { NavList } from "@/components/application/app-navigation/base-components/nav-list";
import { MobileNavigationHeader } from "@/components/application/app-navigation/base-components/mobile-header";
import type { NavItemType, NavItemDividerType } from "@/components/application/app-navigation/config";
```

**Navigation data** — define a `NavSection[]` array with role filtering, then convert to `(NavItemType | NavItemDividerType)[]` with dividers between sections:
```tsx
function buildNavItems(filteredNav: NavSection[]): (NavItemType | NavItemDividerType)[] {
    const items: (NavItemType | NavItemDividerType)[] = [];
    filteredNav.forEach((section, i) => {
        if (i > 0) items.push({ divider: true });
        section.items.forEach((item) => {
            items.push({ label: item.label, href: item.href, icon: item.icon });
        });
    });
    return items;
}
```

**Active URL matching** — handle sub-route highlighting since NavList only does exact matching:
```tsx
function findActiveUrl(navItems, pathname) {
    for (const item of navItems) {
        if (item.divider) continue;
        if (item.href && (pathname === item.href || pathname.startsWith(item.href + "/"))) return item.href;
    }
}
```

**Collapsible sidebar** — the `<aside>` MUST use the your-crm-app's collapse pattern:
- `group/sidebar` CSS class on `<aside>` — uses a **named group** so child collapse-aware classes use `lg:group-hover/sidebar:*` (avoids conflicts with other `group` usages in NavItemBase)
- `lg:w-[72px] lg:hover:w-[280px]` — collapsed/expanded widths
- `lg:transition-all lg:duration-300 lg:ease-in-out` — smooth transition
- `lg:hover:shadow-lg lg:hover:shadow-black/10` — shadow on hover
- Fixed positioning: `lg:fixed lg:inset-y-0 lg:left-0 lg:z-50`

**NavItemBase collapse modifications** — the Untitled UI `NavItemBase` component must be updated to hide text in collapsed state. Edit `src/components/application/app-navigation/base-components/nav-item.tsx`:
- **Label span**: add `lg:max-w-0 lg:overflow-hidden lg:opacity-0 lg:group-hover/sidebar:max-w-52 lg:group-hover/sidebar:opacity-100 lg:transition-[max-width,opacity] lg:duration-300 lg:ease-in-out`
- **Icon**: add `lg:mr-0 lg:group-hover/sidebar:mr-2` (center icon when collapsed, restore margin on hover)
- **Root styles**: add `lg:justify-center lg:group-hover/sidebar:justify-start` (center icon when collapsed)
- **Badge**: add `lg:hidden lg:group-hover/sidebar:inline-flex`
- **ChevronDown** (collapsible type): add `lg:hidden lg:group-hover/sidebar:block`

**NavList divider modification** — edit `src/components/application/app-navigation/base-components/nav-list.tsx`:
- Divider `<li>`: add `lg:hidden lg:group-hover/sidebar:block` (hide dividers when collapsed)

**Sidebar sections (top to bottom):**
1. **Logo header** — 32x32 logo (image or text fallback) + company name. Name hidden when collapsed using `lg:max-w-0 lg:overflow-hidden lg:opacity-0 lg:group-hover/sidebar:max-w-52 lg:group-hover/sidebar:opacity-100` with transition.
2. **Role switcher** — wrapped in grid-rows animation for smooth collapse/expand: `lg:grid-rows-[0fr] lg:group-hover/sidebar:grid-rows-[1fr]` with `transition-[grid-template-rows]`. Separate always-visible mobile version with `lg:hidden`.
3. **Spacer** — `lg:h-20 lg:group-hover/sidebar:h-0` with transition, keeps icons vertically centered when collapsed.
4. **Navigation** — `<NavList>` component with `activeUrl` and converted `navItems`. Wrap in `<nav>` with `overflow-y-auto overflow-x-hidden`.
5. **User footer** — avatar circle (initials) + name/email. Name/email hidden when collapsed using same max-width/opacity technique as logo.

**Shell layout:**
```tsx
<div className="flex min-h-screen bg-secondary">
    {/* Mobile: MobileNavigationHeader wraps SidebarContent in a drawer */}
    <MobileNavigationHeader logo={logoUrl} companyName={name}>
        <SidebarContent />
    </MobileNavigationHeader>

    {/* Desktop: fixed sidebar */}
    <div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-50 lg:flex">
        <SidebarContent />
    </div>

    {/* Spacer matching collapsed sidebar width */}
    <div className="hidden lg:block lg:w-[72px] lg:shrink-0" />

    <main className="min-w-0 flex-1 px-4 py-6 lg:px-8">{children}</main>
    <PrototypeBanner />
</div>
```

**Reference implementation:** See `clients/brightside-services/03-audit/prototype/src/app/(prototype)/layout.tsx` for a complete working example of this pattern.

The layout includes:
- **Collapsible sidebar** — 72px collapsed, 280px on hover, using `NavList`/`NavItemBase` from Untitled UI
- **Client logo** — if `branding.logo_url` exists in audit-data.json, display the client's logo (32x32) in the sidebar header. Otherwise use a text fallback with the company initials.
- **Role switcher** — native `<select>` dropdown, animated with grid-rows collapse
- **Main content area** — where page routes render via `{children}`
- **Toast container** — for journey feedback notifications
- **Mobile responsive** — `MobileNavigationHeader` with hamburger menu and drawer overlay (pass `logo` and `companyName` props)

### 1c. Create prototype context provider

Create `clients/{slug}/03-audit/prototype/src/app/(prototype)/prototype-context.tsx`:

```tsx
// React context for:
// - activeRole: string (current role for visibility filtering)
// - roles: string[] (all available roles from architecture)
// - companyName: string
// - setActiveRole: (role: string) => void
```

This provider wraps the layout and enables role switching across all screens.

### 1d. Create prototype data file

Create `clients/{slug}/03-audit/prototype/src/app/(prototype)/data.ts`:

Export static data extracted from audit-data.json, including:
- Company info (name, entity names)
- Staff names and roles (from process step owners and headcount data)
- Sample entity records (participants, leads, shifts, invoices) using real names/numbers
- Financial figures (from `session_economics`, `waste_items[]`, `strategic_approaches` value totals)
- Module names and descriptions

This is a static TypeScript file — not a database connection. Use real client data to make the prototype feel authentic.

### 1e. Brand configuration

Check `audit-data.json` for the `branding` block (populated by Stage 0b). If `branding` exists and has `primary_color`:

1. **Generate `brand.css`** at `clients/{slug}/03-audit/prototype/src/app/(prototype)/brand.css`:
   ```css
   :root {
     --color-brand-25: /* lightest tint of primary */;
     --color-brand-50: /* ... */;
     --color-brand-100: /* ... */;
     --color-brand-200: /* ... */;
     --color-brand-300: /* ... */;
     --color-brand-400: /* ... */;
     --color-brand-500: /* primary_color */;
     --color-brand-600: /* slightly darker for hover/interactive */;
     --color-brand-700: /* ... */;
     --color-brand-800: /* ... */;
     --color-brand-900: /* ... */;
     --color-brand-950: /* darkest shade */;
   }
   ```
   Derive the full 25-950 scale from `branding.primary_color` by adjusting lightness. Use `secondary_color` for `--color-brand-accent` if available.

2. **Import `brand.css`** in the prototype layout or in `globals.css` so it overrides the defaults.

3. **Download client logo** — if `branding.logo_url` is set:
   - Download the image to `clients/{slug}/03-audit/prototype/public/client-logo.png` (or `.svg` if applicable)
   - Reference it in the sidebar layout as the company logo (32x32)
   - If download fails, fall back to text-based company name display

If `branding` is null or missing, use the default Untitled UI brand palette and a text logo.

---

## Stage 2: Generate Page Routes

> **MANDATORY: Demo CRM Visual Consistency.** Before generating each page, consult `references/demo-crm-patterns.md` for the equivalent page pattern in your-crm-app. The prototype must visually and structurally match these patterns — same sidebar layout, same table styles, same page structures. The actual build will duplicate the your-crm-app project and modify it, so visual consistency is critical.
>
> **Pattern matching guide:**
> - **List pages** (contacts, leads, projects, etc.) → follow Section 3 (List Page Pattern): header + controls row + data table + pagination
> - **Detail pages** ([id] routes) → follow Section 4 (Detail Page Pattern): breadcrumbs + header + tabs + tab content
> - **Dashboard** → follow Section 5 (Dashboard Pattern): metrics cards + charts grid + activity feed
> - **All pages** → use the same Untitled UI component imports documented in Section 7 (Component Import Paths)

### 2a. Create page files

For each page, create:
```
clients/{slug}/03-audit/prototype/src/app/(prototype)/{route}/page.tsx
```

Route mapping from architecture:
- `"/dashboard"` → `src/app/(prototype)/dashboard/page.tsx`
- `"/crm/leads"` → `src/app/(prototype)/crm/leads/page.tsx`
- `"/crm/leads/[id]"` → `src/app/(prototype)/crm/leads/[id]/page.tsx`
- `"/scheduling/roster"` → `src/app/(prototype)/scheduling/roster/page.tsx`

**CRITICAL — Dynamic routes with `output: "export"`**

Any route containing a `[param]` segment **must** export `generateStaticParams()`. Without it the `npm run build` will fail with: `Page "..." is missing "generateStaticParams()"`.

Because these pages use `"use client"` (they access `usePrototype`, `useState`, etc.), `generateStaticParams` cannot live in the same file — it must be in a server component. Use the split-file pattern:

**`[id]/client.tsx`** — the full client component (paste the implementation here, keep `"use client"` at the top):
```tsx
"use client";
// ... full component implementation
export default function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) { ... }
```

**`[id]/page.tsx`** — thin server wrapper that exports `generateStaticParams` and renders the client:
```tsx
import LeadDetailPage from "./client";

export function generateStaticParams() {
    // Return every ID that exists in data.ts for this resource
    return ["l1", "l2", "l3", "l4", "l5"].map((id) => ({ id }));
}

export default function Page({ params }: { params: Promise<{ id: string }> }) {
    return <LeadDetailPage params={params} />;
}
```

The IDs in `generateStaticParams` must exactly match the `id` fields in `data.ts` for that resource. Apply this pattern to every dynamic route in the prototype.

### 2b. Component selection via MCP

**IMPORTANT: Use the Untitled UI MCP tools (configured as `untitledui` MCP server) to discover and retrieve components. Do NOT guess import paths — always verify via MCP.**

For each page, follow this MCP-first workflow:

#### Step 1 — Page templates (fastest path)
**>>> MCP CALL:** `get_page_templates("{page_type}")` for each page type:
- Dashboard screens → `get_page_templates("dashboard")`
- Settings screens → `get_page_templates("settings")`
- List/table screens → `get_page_templates("list")`
- Detail/profile screens → `get_page_templates("detail")`
- Auth screens → `get_page_templates("login")`

If a template matches, **>>> MCP CALL:** `get_page_template_files("{template_id}")` to get the install command and use it as the starting point.

#### Step 2 — Individual components (when no template matches)
**>>> MCP CALL:** `search_components("{natural language description}")` for each component needed:
- `search_components("data table with sorting and pagination")`
- `search_components("metric card with trend indicator")`
- `search_components("form with validation and error states")`
- `search_components("sidebar navigation with collapsible sections")`
- `search_components("modal dialog with form")`
- `search_components("empty state with illustration")`

Then **>>> MCP CALL:** `get_component("{component_name}")` to retrieve the exact import path, props, and usage pattern.

For bulk retrieval: **>>> MCP CALL:** `get_component_bundle(["{comp1}", "{comp2}", ...])` to fetch multiple components at once.

#### Step 3 — Icons
**>>> MCP CALL:** `search_icons("{keyword}")` for every icon needed:
- `search_icons("calendar")` → for scheduling screens
- `search_icons("users")` → for contact/staff screens
- `search_icons("chart")` → for dashboard metrics
- `search_icons("invoice")` → for financial screens
- `search_icons("check")` → for success states
- `search_icons("settings")` → for configuration screens

Import from `@untitledui/icons` (free) or `@untitledui-pro/icons` (PRO).

#### Step 4 — Verify locally
After MCP discovery, verify the component exists in `clients/{slug}/03-audit/prototype/src/components/` before importing. If the component is not installed locally, use the install command from `get_component` to add it.

### 2c. Component rendering per page type

Map `architecture_doc.page_structure.pages[].components[]` to Untitled UI implementations:

| Architecture Component | Untitled UI Implementation | Data Source |
|---|---|---|
| `Table` | `@/components/application/table/` — with column definitions, sortable headers, `Pagination` | Entity records from `data.ts`, fields from `data_models[]` |
| `Input` (search) | `@/components/base/input/` — with search icon, placeholder | Filter entity list |
| `Badge` | `@/components/base/badges/` — `BadgeWithDot` for status indicators | Entity status enum values |
| `Button` | `@/components/base/buttons/button` — primary for CTAs, secondary for actions | Journey step actions |
| `Select` | `@/components/base/select/` — for filters, dropdowns | Entity field enums, role lists |
| `Tabs` | `@/components/application/tabs/` — for detail view sections | Detail page sections (overview, activity, documents) |
| `Charts` | `recharts` (already installed) — bar, line, area charts | Financial metrics, trend data from `session_economics` |
| `DatePicker` | `@/components/application/date-picker/` | Scheduling screens |
| `Modal` | `@/components/application/modals/` | Confirmation dialogs, create/edit forms |
| `Avatar` | `@/components/base/avatar/` — `AvatarLabelGroup` for staff lists | Staff names from `data.ts` |
| `EmptyState` | `@/components/application/empty-state/` | Screens with no sample data |
| `Toggle` | `@/components/base/toggle/` | Settings, notification preferences |
| `Checkbox` | `@/components/base/checkbox/` | Multi-select in tables, form checkboxes |
| `Tooltip` | `@/components/base/tooltip/` | Help text, data point explanations |
| `Dropdown` | `@/components/base/dropdown/` | Row actions (edit, delete, view) |
| `FileUpload` | `@/components/application/file-upload/` | Document upload screens |
| `Pagination` | `@/components/application/pagination/` | List views |

### 2d. Populate with real client data

Every screen must use real data from the client's audit:

- **Names**: Staff names from process step owners (e.g., "Jordan Lee", "Alex", "Chris")
- **Entities**: Business entity names (e.g., participant names, organisation names)
- **Numbers**: Financial figures from `session_economics` and `waste_items[]`
- **Counts**: Headcount figures (staff count, participant count)
- **Statuses**: Realistic status distributions (e.g., 60% active, 20% pending, 20% inactive)
- **Dates**: Use relative dates (today, yesterday, last week) for freshness

Import all data from the `data.ts` file created in Stage 1d.

### 2e. Role-based visibility

Each page component checks the prototype context for the active role:

```tsx
const { activeRole } = usePrototypeContext();

// Hide entire page if role not allowed
if (!page.roles.includes(activeRole)) {
  return <ForbiddenScreen />;
}

// Hide specific sections within a page
{activeRole === 'admin' && <AdminOnlySection />}
```

---

## Stage 3: Wire Navigation + Role Switching

### 3a. Sidebar navigation

> **This was already built in Stage 1b** using `NavList` and `NavItemBase`. Stage 3a wires the navigation data from `architecture_doc.page_structure.navigation[]` into the existing collapsible sidebar layout.

Build the `navigation: NavSection[]` array from architecture data:
- Each architecture `section` (module) becomes a `NavSection` with its items
- Each `item` gets `label`, `href`, `icon`, and `roles` (from architecture access policies)
- Convert to `NavItemType[]` with dividers between sections using `buildNavItems()`
- Pass to `<NavList activeUrl={activeUrl} items={navItems} />` in the sidebar

**Icon selection**: Use icons consistent with the demo CRM's icon choices. Map client modules to the closest equivalent:
  - Dashboard → `Home01`, CRM/Contacts → `Users01`, Leads/Pipeline → `Target04` or `TrendUp01`, Projects → `Rows01`
  - Finance/Invoices → `Receipt`, Scheduling → `CalendarDate`, Tasks → `CheckSquare`
  - Messages → `MessageChatCircle`, Settings → `Settings01`
  - **>>> MCP CALL:** For any module without an obvious mapping, call `search_icons("{keyword}")` to find the correct icon

**Active state**: Use `findActiveUrl()` helper with `startsWith` matching, then pass to `NavList`'s `activeUrl` prop.

**CRITICAL — use Next.js `<Link>`, never `<a>`**: Every nav item must render with Next.js `<Link href={item.href}>`, not a plain `<a href>`. With the static export configured for relative delivery (`basePath: ""`, `assetPrefix: "./"`), `<Link>` resolves hrefs correctly when the export is opened from a Google Drive folder. A plain `<a>` with a root-relative href (e.g. `/marketing`) breaks when opened from the filesystem. The same rule applies to any other inline anchor tags in page files — always use `<Link>` from `next/link` for internal navigation.

**Reference implementation:** See `clients/brightside-services/03-audit/prototype/src/app/(prototype)/layout.tsx` for the complete pattern.

### 3b. Role switcher

Build a native `<select>` dropdown in a `RoleSwitcher` component (used in sidebar). This is wrapped in the grid-rows animation section so it collapses when the sidebar is collapsed and animates open on hover (see Stage 1b layout pattern).

When role changes:
- Navigation items filter to show only items where `roles[]` includes the active role
- Page content re-renders with role-appropriate visibility
- Toast notification: "Now viewing as {role_name}"

### 3c. Breadcrumbs

Generate breadcrumbs from the page hierarchy:
- Dashboard → CRM → Leads → Lead Detail
- Use `route` and `parent` fields from page structure
- Render using a simple breadcrumb component with links

---

## Stage 4: Wire Journey Flows

Make the prototype clickable by connecting user journey steps.

### 4a. Navigation actions

For each user journey in `architecture_doc.user_journeys[]`, wire click handlers:

- **Table rows** → `<Link href="/{entity}/{id}">` to detail pages
- **"Create" buttons** → navigate to create/new page or open modal
- **Form submit buttons** → show success toast + navigate to next screen in journey
- **Dashboard action cards** → navigate to the relevant module page
- **Back/cancel buttons** → `router.back()` or navigate to parent route

### 4b. Visual journey indicators

On the "happy path" for key journeys:
- Primary-colored `Button` components for the main action (e.g., "Assign Shift", "Create Lead")
- Secondary-colored buttons for alternative actions
- `Badge` components showing step progress ("Step 2 of 4")

### 4c. Toast feedback

Use a simple toast system for action feedback:
- Form submissions: "Lead created successfully"
- Assignments: "Shift assigned to {worker_name}"
- Notifications: "SMS notification sent"
- Errors: "Unable to process — demo only"

Implement with a lightweight toast component or use Untitled UI's notification patterns.

### 4d. Modal interactions

For create/edit actions that should stay on the same page:
- Use Untitled UI `Modal` component from `@/components/application/modals/`
- Pre-fill forms with sample data
- Submit button shows toast + closes modal

---

## Stage 5: Output & Summary

### 5a. File structure

All generated files live under `clients/{slug}/03-audit/prototype/src/app/(prototype)/`:

```
clients/{slug}/03-audit/prototype/src/app/(prototype)/
  layout.tsx                    — sidebar nav + role switcher + main content
  prototype-context.tsx         — role switching context provider
  data.ts                       — static client data
  brand.css                     — client brand overrides (optional)
  dashboard/
    page.tsx                    — overview dashboard
  crm/
    leads/
      page.tsx                  — lead pipeline list
      [id]/
        page.tsx                — lead detail
    contacts/
      page.tsx                  — contacts list
      [id]/
        page.tsx                — contact detail
  scheduling/
    roster/
      page.tsx                  — weekly roster view
    shifts/
      page.tsx                  — shift list
  compliance/
    page.tsx                    — compliance dashboard
    documents/
      page.tsx                  — document tracking
  finance/
    invoices/
      page.tsx                  — invoice list
    funding/
      page.tsx                  — funding tracker
  settings/
    page.tsx                    — user settings
  components/
    forbidden-screen.tsx        — role-restricted access message
    toast-provider.tsx          — toast notification system
    breadcrumbs.tsx             — breadcrumb navigation
```

### 5b. Verification

After generation, verify the prototype works:

```bash
cd clients/{slug}/03-audit/prototype && npm run dev
```

Open `http://localhost:3000/dashboard` and verify:
- [ ] Sidebar navigation renders with all module sections
- [ ] Role switcher dropdown shows all roles
- [ ] Switching roles hides/shows navigation items
- [ ] Clicking nav items navigates to correct pages
- [ ] Pages display real client data (names, numbers)
- [ ] Table rows are clickable (navigate to detail)
- [ ] "Create" buttons open modals or navigate to forms
- [ ] Toast notifications appear on actions
- [ ] Breadcrumbs update correctly
- [ ] Mobile responsive (sidebar collapses)

### 5c. Display summary

```
PROTOTYPE BUILT — {company_name}

Strategy: {strategy_name}
Output: clients/{slug}/03-audit/prototype/src/app/(prototype)/

Files generated:
  layout.tsx + context          — navigation shell with role switcher
  data.ts                       — {n} sample records from audit data
  {n} page routes               — across {n} modules
  {n} detail pages              — entity detail views
  components/                   — shared prototype components

To view: cd clients/{slug}/03-audit/prototype && npm run dev → http://localhost:3000/dashboard

Roles available: {list of roles}
Journeys wired: {n} interactive user flows
Modules covered: {list of modules}

NOTE: This is a visual demo, not a functional application.
      Data is static. Forms do not submit to a backend. No authentication.

Delivery: the prototype is built as a static export and shared via the client's Google Drive folder.
```

### 5d. Build & delivery configuration

After the prototype builds and verifies locally, configure it for delivery:

1. **Set static export** in the client's `03-audit/prototype/next.config.mjs`:
   ```js
   output: "export",
   basePath: "",
   assetPrefix: "./",
   ```
   An empty `basePath` with a relative `assetPrefix` makes the export self-contained so it opens correctly from a Google Drive folder (no portal routing required).

   **Before building**, verify every dynamic route (`[param]`) has the split-file pattern described in Section 2a — a `client.tsx` with the component and a `page.tsx` with `generateStaticParams`. Missing this causes a hard build failure.

2. **Build the static export:**
   ```bash
   cd <client>/03-audit/prototype && npm run build
   ```
   This produces a self-contained `out/` directory.

3. **Regenerate client-website.html** so the prototype is linked:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/5-deliverable-builder/scripts/generate.py --client-slug {slug} --output client-website
   ```

The built `out/` directory is delivered via the client's Google Drive folder (and is picked up by `build_handover.py` when assembling the handover bundle). There is no external hosting step.

---

## MCP Fallback

If the Untitled UI MCP is unavailable during generation:

1. Check if components are installed locally at `clients/{slug}/03-audit/prototype/src/components/`
2. If local components exist: use `references/untitled-ui-components.md` mapping guide + `clients/{slug}/03-audit/prototype/CLAUDE.md` for import patterns + browse `clients/{slug}/03-audit/prototype/src/components/` directly
3. **If a required component cannot be found via MCP OR locally: STOP and notify the user.** Do NOT substitute with custom markup, raw HTML, or Tailwind-only elements. Every UI element must use an Untitled UI component.
4. The only exceptions are: layout containers (`div`, `main`, `section`), Next.js primitives (`Link`, `Image`), and prototype-specific wiring (`prototype-context.tsx`, `data.ts`)

---

## Context Window Management

For large prototypes (15+ pages), generation may need to be split across sessions:

1. **Session 1**: Stage 0 (scaffold, only on first run) + Stage 1 (project setup) + Stage 2 for Phase 1 modules (Quick Wins)
2. **Session 2**: Stage 2 for Phase 2 modules (Core Platform)
3. **Session 3**: Stage 2 for Phase 3 modules (AI Enablement) + Stage 3 (navigation) + Stage 4 (journeys)

The scaffold (Stage 0) only runs once per client. Subsequent sessions resume from Stage 2 onwards, generating pages into the existing `clients/{slug}/03-audit/prototype/` project.

Use [SM] Save Memory between sessions to persist progress. The prototype is additive — each session adds more pages without breaking existing ones.
