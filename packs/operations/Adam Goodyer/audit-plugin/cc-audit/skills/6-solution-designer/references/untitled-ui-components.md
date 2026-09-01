# Untitled UI Component Reference — Solution Architect

**HARD REQUIREMENT:** ALL UI components in prototypes MUST be Untitled UI components. No custom components, no raw HTML elements, no Tailwind-only markup. If a needed component cannot be found via MCP or locally — STOP and notify the user.

Quick-reference mapping architecture `components[]` to Untitled UI implementations.
For full component docs, use the Untitled UI MCP (`search_components`, `list_components`, `get_component`).

## MCP Tools Available

| Tool | Purpose |
|---|---|
| `search_components` | Natural language search (e.g., "data table with pagination") |
| `list_components` | Browse by category: base, application, marketing, foundations, shared-assets |
| `get_component` | Retrieve single component with install command |
| `get_component_bundle` | Install multiple components at once |
| `get_page_templates` | Find pre-built page layouts (dashboard, settings, auth, list) |
| `get_page_template_files` | Generate CLI install command for page templates |
| `search_icons` | Find icons by keyword (returns from @untitledui/icons) |

## Component Mapping (Architecture → Untitled UI)

| Architecture Name | Untitled UI Path | Category |
|---|---|---|
| `Table` | `@/components/application/table/` | application |
| `Tabs` | `@/components/application/tabs/` | application |
| `Modal` | `@/components/application/modals/` | application |
| `DatePicker` | `@/components/application/date-picker/` | application |
| `Pagination` | `@/components/application/pagination/` | application |
| `EmptyState` | `@/components/application/empty-state/` | application |
| `FileUpload` | `@/components/application/file-upload/` | application |
| `AppNavigation` | `@/components/application/app-navigation/` | application |
| `Charts` | `recharts` (separate package, already installed) | application |
| `Carousel` | `@/components/application/carousel/` | application |
| `Button` | `@/components/base/buttons/button` | base |
| `Input` | `@/components/base/input/input` | base |
| `Select` | `@/components/base/select/select` | base |
| `Checkbox` | `@/components/base/checkbox/checkbox` | base |
| `Radio` | `@/components/base/radio-buttons/` | base |
| `Toggle` | `@/components/base/toggle/` | base |
| `Badge` | `@/components/base/badges/badges` | base |
| `Avatar` | `@/components/base/avatar/avatar` | base |
| `Tooltip` | `@/components/base/tooltip/` | base |
| `Dropdown` | `@/components/base/dropdown/` | base |
| `Textarea` | `@/components/base/textarea/` | base |
| `Slider` | `@/components/base/slider/` | base |
| `Tags` | `@/components/base/tags/` | base |
| `FeaturedIcon` | `@/components/foundations/featured-icon/featured-icon` | foundations |

## Key Import Patterns

```tsx
// Components — direct import
import { Button } from "@/components/base/buttons/button";
import { Input } from "@/components/base/input/input";
import { Select } from "@/components/base/select/select";
import { Badge, BadgeWithDot } from "@/components/base/badges/badges";
import { Avatar, AvatarLabelGroup } from "@/components/base/avatar/avatar";

// Icons — named import (tree-shakeable)
import { Home01, Users01, Calendar01, Settings01 } from "@untitledui/icons";

// React Aria — MUST prefix with Aria*
import { Button as AriaButton } from "react-aria-components"; // ✅
```

## Color System (Semantic Tokens)

Use semantic color classes, NOT raw color values:

| Purpose | Class |
|---|---|
| Primary text | `text-primary` |
| Secondary text | `text-secondary` |
| Tertiary text | `text-tertiary` |
| Brand text | `text-brand-primary` |
| Error text | `text-error-primary` |
| Success text | `text-success-primary` |
| Primary background | `bg-primary` |
| Secondary background | `bg-secondary` |
| Brand solid | `bg-brand-solid` |
| Primary border | `border-primary` |
| Secondary border | `border-secondary` |
| Primary foreground (icons) | `fg-primary` |
| Brand foreground | `fg-brand-primary` |

## Icon Naming Convention

Icons use PascalCase with numeric suffix: `Home01`, `Users01`, `Calendar01`, `ChevronDown`, `Check`, `X`

Common icon names for business apps:
- Navigation: `Home01`, `Users01`, `Calendar01`, `Settings01`, `BarChart01`, `FileText01`
- Actions: `Plus`, `Edit01`, `Trash02`, `Download01`, `Upload01`, `Search01`
- Status: `CheckCircle`, `AlertCircle`, `XCircle`, `Clock`
- Finance: `CurrencyDollar`, `Receipt`, `CreditCard01`
- Communication: `Mail01`, `Phone01`, `MessageSquare01`

Use MCP `search_icons("keyword")` for best matches.

## File Naming Convention

All files must be **kebab-case**: `lead-pipeline.tsx`, `shift-roster.tsx`, `prototype-context.tsx`

## Page Template Hints

Use MCP `get_page_templates` to find starting points:
- **Dashboard** → search "dashboard" for metric cards + activity feed layouts
- **List/Table** → search "list" for table + filter + pagination layouts
- **Detail** → search "detail" or "profile" for header + tabs layouts
- **Settings** → search "settings" for form section layouts
- **Auth** → search "login" for sign-in page layouts (if prototype includes auth screens)
