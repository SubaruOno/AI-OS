# Demo Internal CRM — Visual Patterns Reference

> **Source**: `~/path/to/your-crm`
> **Purpose**: Prototypes MUST match these patterns so the actual build (duplicating your-crm-app and modifying it) starts from a visually consistent base.

---

## 1. Application Shell

The demo CRM uses a `CustomSidebar` component (`components/layouts/CustomSidebar.tsx`) as the primary layout wrapper.

**Structure:**
```
┌──────────────────────────────────────────────────────┐
│ ┌──────────┐ ┌──────────────────────────────────────┐│
│ │ Sidebar  │ │ Main Content Area                    ││
│ │ (280px)  │ │                                      ││
│ │          │ │  {children} — page routes render here ││
│ │ Collapses│ │                                      ││
│ │ to 72px  │ │                                      ││
│ │ on desktop│ │                                      ││
│ │          │ │                                      ││
│ │ Expands  │ │                                      ││
│ │ on hover │ │                                      ││
│ └──────────┘ └──────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

**Sidebar anatomy (top to bottom):**
1. **Logo + Company Name** — 32x32 logo image (or SVG fallback), company name hidden when collapsed
2. **Theme Toggle + Notification Bell** — top-right of sidebar header
3. **Search Bar** — intelligent search, visible on hover/expand (desktop) or inline (mobile)
4. **Navigation Items** — `NavList` with icon + label per item, collapsible sub-items
5. **Footer Items** — Settings link at bottom
6. **User Account Section** — avatar, name, email, sign-out action

**Responsive behaviour:**
- Desktop: fixed left sidebar, 72px collapsed, 280px on hover/expand, smooth 300ms transition
- Mobile: `MobileNavigationHeader` with hamburger menu, full-width overlay
- Mobile bottom nav: `MobileCRMBottomNav` for admin/PM roles

**Key props for `CustomSidebar`:**
```tsx
{
  activeUrl: string           // Current pathname for active highlighting
  items: NavItemType[]        // Main navigation items
  footerItems: NavItemType[]  // Bottom nav items (Settings)
  logo: string | null         // Company logo URL
  companyName: string         // Company name display
  user: { name, email, avatar }
  modeToggle?: ReactNode      // CRM/Workspace toggle (optional)
}
```

---

## 2. Sidebar Navigation Structure

### CRM Mode Navigation Items

| Label | Icon | Route | Sub-items |
|-------|------|-------|-----------|
| Dashboard | `HomeLine` | `/dashboard` | — |
| Contacts | `Users01` | `/contacts` | — |
| Leads | `TrendUp01` | `/leads` | — |
| Projects | `Rows01` | `/projects` | — |
| Transactions | `Receipt` | `/transactions` | — |
| Payroll | `CurrencyDollarCircle` | `/payroll` | — |
| Inventory | `Box` | `/inventory` | — |
| Scheduling | `CalendarDate` | `/scheduling` | — |

### Workspace Mode Navigation Items

| Label | Icon | Route | Sub-items |
|-------|------|-------|-----------|
| My Projects | `Grid01` | `/workspace` | Dynamic project list |
| Tasks | `CheckSquare` | `/workspace/tasks` | — |
| Messages | `MessageChatCircle` | `/workspace/chat` | — |
| Timesheets | `Clock` | `/workspace/timesheets` | — |
| Meetings | `VideoRecorder` | `/workspace/meetings` | — |

### Footer Items

| Label | Icon | Route |
|-------|------|-------|
| Settings | `Settings01` | `/settings` |

**All icons** from `@untitledui/icons`. Use MCP `search_icons()` to verify exact icon names.

**NavItemType structure:**
```tsx
{
  label: string
  href: string
  icon: ComponentType  // Untitled UI icon component
  items: { label: string; href: string }[]  // Sub-items (optional)
}
```

---

## 3. List Page Pattern

Standard pattern used by Contacts, Leads, Projects, Transactions, etc.

```
┌──────────────────────────────────────────────┐
│ Page Header                                  │
│   Title (h1, text-lg font-semibold)          │
│   Subtitle (text-sm text-tertiary)           │
├──────────────────────────────────────────────┤
│ Tab Bar (optional — e.g. Contacts has        │
│   Customers | Suppliers | Archived | Comms)  │
├──────────────────────────────────────────────┤
│ Controls Row                                 │
│   [Search Input w/ SearchLg icon]            │
│   [Filter Button w/ FilterLines icon]        │
│   [View Toggle (Board/Calendar/Table)]       │
│   [+ New Entity Button — primary, sm]        │
├──────────────────────────────────────────────┤
│ Data Table                                   │
│   Checkbox | Name (Avatar+Label) | Email     │
│   Phone | Type Badge | Status | Actions (⋯)  │
│   ─────────────────────────────────────────  │
│   Row click → opens detail or slideout       │
├──────────────────────────────────────────────┤
│ Pagination (PaginationPageMinimalCenter)     │
│   [← Previous] Page X of Y [Next →]         │
└──────────────────────────────────────────────┘
```

**Key components:**
- `@/components/application/table/table` — sortable columns, row selection
- `@/components/application/pagination/pagination` — `PaginationPageMinimalCenter`
- `@/components/base/input/input` — search with `SearchLg` icon
- `@/components/base/buttons/button` — primary for "New", secondary for filters
- `@/components/base/badges/badges` — `BadgeWithDot` for status indicators
- `@/components/base/avatar/avatar` — contact/entity avatars with fallback
- `@/components/base/dropdown/dropdown` — row action menus (edit, archive, delete)
- `@/components/base/checkbox/checkbox` — bulk selection

**Leads variation:** Uses Kanban board (`LeadsKanban`) as default view with calendar toggle option. Stats cards row above the board showing total leads, pipeline value, conversion rate.

---

## 4. Detail Page Pattern

Standard pattern used by Contact Detail, Project Detail, Lead Detail, etc.

```
┌──────────────────────────────────────────────┐
│ Breadcrumbs                                  │
│   Home > Contacts > {Entity Name}            │
├──────────────────────────────────────────────┤
│ Header Row                                   │
│   [Avatar] Entity Name | Type Badge          │
│   [Edit Button] [Call Button] [⋯ More]       │
├──────────────────────────────────────────────┤
│ Tab Navigation                               │
│   Details | Files | Projects | Invoices      │
│   | Bills | Messages & Calls | Activity      │
├──────────────────────────────────────────────┤
│ Tab Content (varies by tab)                  │
│   Details tab: key-value info, notes         │
│   Files tab: document list with CMS          │
│   Projects tab: linked project cards         │
│   Invoices/Bills: financial table            │
│   Messages: communication timeline           │
│   Activity: chronological feed               │
└──────────────────────────────────────────────┘
```

**Key components:**
- `@/components/application/breadcrumbs/breadcrumbs` — navigation trail
- `@/components/application/tabs/tabs` — `TabList`, `Tabs` for section switching
- `@/components/application/section-headers/section-headers` — `SectionHeader`
- `@/components/application/activity-feed/activity-feed` — `FeedItem` for activity logs
- `@/components/application/slideout-menus/` — right-side detail panels

**Tab content patterns:**
- **Details tab**: Two-column grid of key-value pairs, editable notes section
- **Table tabs** (Invoices, Bills, Projects): Same table pattern as list pages but scoped to entity
- **Activity tab**: Chronological `FeedItem` list with entity-linked actions
- **Communication tab**: Timeline of SMS/calls with timestamps and previews

---

## 5. Dashboard Pattern

```
┌──────────────────────────────────────────────┐
│ Dashboard Header                             │
├──────────────────────────────────────────────┤
│ Metrics Cards Row (4 columns, responsive)    │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│ │ Total│ │ Cash │ │ Cash │ │ Open │         │
│ │  Rev │ │  In  │ │  Out │ │Leads │         │
│ └──────┘ └──────┘ └──────┘ └──────┘         │
├──────────────────────────────────────────────┤
│ Charts Section (2-col grid, stacks on mobile)│
│ ┌────────────────┐ ┌────────────────┐        │
│ │ Revenue Trend  │ │ Expense        │        │
│ │ (Line Chart)   │ │ Breakdown (Pie)│        │
│ ├────────────────┴─┴────────────────┤        │
│ │ Cash Flow (Bar Chart, full width) │        │
│ └───────────────────────────────────┘        │
├──────────────────────────────────────────────┤
│ Recent Activity Feed                         │
│   FeedItem[] — 18 most recent activities     │
└──────────────────────────────────────────────┘
```

**Key components:**
- `@/components/application/metrics/metrics` — `MetricsSimple` card with value + trend
- `recharts` — `Bar`, `Line`, `Pie` + `Tooltip`, `XAxis`, `Legend` (already installed)
- `@/components/application/charts/LazyCharts` — lazy-loaded chart wrappers
- `@/components/application/activity-feed/activity-feed` — `FeedItem`

**Data pattern:** Parallel data fetches for metrics, charts, and activity. Date range selector for filtering.

---

## 6. Common UI Patterns

### Mode Toggle (CRM / Workspace)
A segmented control in the sidebar with sliding indicator. Switching modes changes the navigation items and redirects to the mode's default page.

### Role Switcher (Prototype-specific)
Use a `Select` dropdown in the sidebar header. When role changes, navigation items and page content filter by role visibility. Show toast: "Now viewing as {role}".

### Toast Notifications
Lightweight toast for action feedback: "Lead created successfully", "Shift assigned to {name}", etc.

### Empty States
Use `@/components/application/empty-state/` with illustration, message, and CTA button.

### Loading States
Use `@/components/application/loading-indicator/` — `line-spinner` variant for page loads, `dots` for inline loading.

### Slideout Panels
Right-side panels (`@/components/application/slideout-menus/`) for quick-edit without navigating away from list views. Used for lead editing, contact editing.

---

## 7. Component Import Path Summary

| Pattern | Import Path |
|---------|-------------|
| Sidebar shell | `@/components/layouts/CustomSidebar` |
| Nav items | `@/components/application/app-navigation/base-components/nav-item`, `nav-list` |
| Mobile header | `@/components/application/app-navigation/base-components/mobile-header` |
| Table | `@/components/application/table/table` |
| Pagination | `@/components/application/pagination/pagination` |
| Tabs | `@/components/application/tabs/tabs` |
| Breadcrumbs | `@/components/application/breadcrumbs/breadcrumbs` |
| Section header | `@/components/application/section-headers/section-headers` |
| Activity feed | `@/components/application/activity-feed/activity-feed` |
| Metrics card | `@/components/application/metrics/metrics` |
| Empty state | `@/components/application/empty-state/` |
| Loading | `@/components/application/loading-indicator/` |
| Slideout | `@/components/application/slideout-menus/` |
| Modal | `@/components/application/modals/` |
| Button | `@/components/base/buttons/button` |
| Input | `@/components/base/input/input` |
| Badge | `@/components/base/badges/badges` |
| Avatar | `@/components/base/avatar/avatar` |
| Dropdown | `@/components/base/dropdown/dropdown` |
| Select | `@/components/base/select/` |
| Toggle | `@/components/base/toggle/` |
| Checkbox | `@/components/base/checkbox/` |
| Tooltip | `@/components/base/tooltip/` |
| Icons | `@untitledui/icons` |
| Charts | `recharts` |

> **Important**: Always verify exact import paths via Untitled UI MCP (`get_component()`) before using. These paths reflect the your-crm-app installation and may differ in the `untitled-ui/` template scaffold.
