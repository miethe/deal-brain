# Frontend Architecture Documentation

**Document Version:** 1.0
**Last Updated:** 2025-10-14
**Target Audience:** Frontend developers, technical leads, architects

---

## Table of Contents

1. [Overview](#overview)
2. [Application Structure](#application-structure)
3. [Page Structure](#page-structure)
4. [Component Organization](#component-organization)
5. [State Management](#state-management)
6. [Data Fetching](#data-fetching)
7. [Custom Hooks](#custom-hooks)
8. [TypeScript Types](#typescript-types)
9. [Styling System](#styling-system)
10. [Best Practices](#best-practices)

---

## Overview

Deal Brain's frontend is built with **Next.js 14** using the App Router architecture. The application provides a sophisticated UI for managing PC listings, valuation rules, scoring profiles, and custom fields.

### Technology Stack

- **Framework:** Next.js 14.1.0 (App Router)
- **UI Library:** React 18.2.0
- **State Management:** Zustand 5.0.8 (client state) + React Query 5.24.3 (server state)
- **Styling:** Tailwind CSS 3.4.1 with custom design tokens
- **UI Components:** Radix UI primitives (headless, accessible)
- **Forms:** React Hook Form 7.50.1 + Zod 3.22.4 validation
- **Type Safety:** TypeScript 5.3.3 (strict mode)
- **Icons:** Lucide React
- **Animations:** Framer Motion 11.0.3

### Architecture Principles

1. **Server-first rendering:** Default to server components, use client components only when needed
2. **Colocation:** Keep related code (components, types, hooks) close together
3. **Composition over inheritance:** Build complex UIs from small, reusable components
4. **Type safety:** Comprehensive TypeScript coverage with strict compiler options
5. **Accessibility:** WCAG AA compliance, keyboard navigation, screen reader support
6. **Performance:** Memoization, debouncing, virtualization for large datasets

---

## Application Structure

### Root Layout (`/mnt/containers/deal-brain/apps/web/app/layout.tsx`)

The root layout establishes the core application shell:

```tsx
import { AppShell } from "../components/app-shell";
import { Providers } from "../components/providers";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
```

**Key Features:**
- `suppressHydrationWarning`: Required for next-themes to prevent hydration mismatches
- `Providers`: Wraps app with React Query + Theme providers
- `AppShell`: Provides navigation and layout structure

### Providers Setup (`/mnt/containers/deal-brain/apps/web/components/providers.tsx`)

```tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ThemeProvider>
  );
}
```

**Provider Responsibilities:**
- **QueryClientProvider:** Manages React Query cache and configuration
- **ThemeProvider:** Handles light/dark mode with system preference detection
- Marked as `"use client"` to enable React hooks

### AppShell (`/mnt/containers/deal-brain/apps/web/components/app-shell.tsx`)

Provides the navigation structure:

```tsx
const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/listings", label: "Listings" },
  { href: "/profiles", label: "Profiles" },
  { href: "/valuation-rules", label: "Valuation Rules" },
  { href: "/global-fields", label: "Global Fields" },
  { href: "/import", label: "Import" },
  { href: "/admin", label: "Admin" }
];
```

**Features:**
- Fixed header with mobile hamburger menu
- Sidebar navigation (always visible on desktop, toggleable on mobile)
- Theme toggle button
- Responsive layout with appropriate breakpoints
- Active route highlighting using `usePathname()`

---

## Page Structure

All pages live in `/mnt/containers/deal-brain/apps/web/app/`. Next.js 14 App Router uses file-based routing.

### Dashboard (`/`)

**File:** `/mnt/containers/deal-brain/apps/web/app/page.tsx`

```tsx
export default function HomePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight">Today's snapshot</h1>
      <DashboardSummary />
      {/* Quick action cards */}
    </div>
  );
}
```

**Purpose:** Landing page with key metrics and quick actions
**Components Used:** `DashboardSummary`, `Card`, `Button`
**Data:** Fetches dashboard metrics from `/v1/dashboard`

### Listings

#### Listings Index (`/listings`)

**File:** `/mnt/containers/deal-brain/apps/web/app/listings/page.tsx`

```tsx
"use client";

export default function ListingsPage() {
  const [addModalOpen, setAddModalOpen] = useState(false);
  const activeTab = useCatalogStore((state) => state.activeTab);

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsTrigger value="catalog">Catalog</TabsTrigger>
      <TabsTrigger value="data">Data</TabsTrigger>

      <TabsContent value="catalog">
        <CatalogTab listings={listings} />
      </TabsContent>

      <TabsContent value="data">
        <ListingsTable />
      </TabsContent>
    </Tabs>
  );
}
```

**Features:**
- Two view modes: Catalog (cards) and Data (table)
- URL state synchronization via `useUrlSync()`
- Zustand store for view preferences
- Add listing modal
- Quick edit and details dialogs

#### Listing Detail (`/listings/[id]`)

**File:** `/mnt/containers/deal-brain/apps/web/app/listings/[id]/page.tsx`

**Type:** Server Component (async)
**Data Fetching:** Direct `apiFetch()` in component (RSC pattern)

```tsx
export default async function ListingDetailPage({ params }: { params: { id: string } }) {
  const listing = await apiFetch<ListingDetail>(`/v1/listings/${params.id}`);

  if (!listing) {
    notFound();
  }

  return (
    <div>
      {/* Valuation breakdown, scores, component deductions */}
    </div>
  );
}
```

**Features:**
- Server-side data fetching
- Valuation breakdown table
- Score metrics grid
- Component deduction details

#### New Listing (`/listings/new`)

**File:** `/mnt/containers/deal-brain/apps/web/app/listings/new/page.tsx`

Simple page that renders `AddListingForm` component.

### Valuation Rules (`/valuation-rules`)

**File:** `/mnt/containers/deal-brain/apps/web/app/valuation-rules/page.tsx`

```tsx
"use client";

export default function ValuationRulesPage() {
  const [mode, setMode] = useState<"basic" | "advanced">("basic");
  const [selectedRulesetId, setSelectedRulesetId] = useState<number | null>(null);

  return (
    <div>
      <ModeToggle mode={mode} onChange={setMode} />

      {mode === "basic" ? (
        <BasicModeTabs />
      ) : (
        <>
          <RulesetSelector value={selectedRulesetId} onChange={setSelectedRulesetId} />
          <RulesetSettingsCard ruleset={selectedRuleset} />
          {filteredRuleGroups.map(group => (
            <RulesetCard key={group.id} ruleGroup={group} />
          ))}
        </>
      )}
    </div>
  );
}
```

**Features:**
- Two modes: Basic (simple field-based rules) and Advanced (complex rule builder)
- Mode persisted to localStorage
- Ruleset selector and priority controls
- Condition builder with logical operators (AND/OR)
- Diff & Adopt wizard for baseline updates
- Search and filtering

### Global Fields (`/global-fields`)

**File:** `/mnt/containers/deal-brain/apps/web/app/global-fields/page.tsx`

```tsx
export default function GlobalFieldsPage() {
  return (
    <div>
      <h1>Global catalog workspace</h1>
      <GlobalFieldsWorkspace />
    </div>
  );
}
```

**Purpose:** Manage dynamic custom fields across entities
**Component:** `GlobalFieldsWorkspace` (comprehensive field management UI)

### Profiles (`/profiles`)

**File:** `/mnt/containers/deal-brain/apps/web/app/profiles/page.tsx`

```tsx
export default function ProfilesPage() {
  return (
    <div>
      <h1>Scoring profiles</h1>
      <ProfileList />
    </div>
  );
}
```

**Purpose:** Configure scoring weights for different use cases (Proxmox, Plex, dev workloads)

### Admin (`/admin`)

Administrative functions (valuation recalculation, data management, etc.)

---

## Component Organization

Components are organized by domain in `/mnt/containers/deal-brain/apps/web/components/`.

### Directory Structure

```
components/
├── ui/                        # Base UI primitives (Radix-based)
│   ├── button.tsx
│   ├── card.tsx
│   ├── dialog.tsx
│   ├── input.tsx
│   ├── select.tsx
│   ├── tabs.tsx
│   ├── table.tsx
│   └── ...
├── forms/                     # Form components
│   ├── ram-spec-selector.tsx
│   └── storage-profile-selector.tsx
├── listings/                  # Listing-specific components
│   ├── listings-table.tsx
│   ├── add-listing-form.tsx
│   ├── add-listing-modal.tsx
│   ├── listing-details-dialog.tsx
│   ├── quick-edit-dialog.tsx
│   ├── valuation-breakdown-modal.tsx
│   └── listing-valuation-tab.tsx
├── valuation/                 # Valuation rule components
│   ├── valuation-rules-table.tsx
│   ├── ruleset-card.tsx
│   ├── rule-builder-modal.tsx
│   ├── ruleset-builder-modal.tsx
│   ├── rule-group-form-modal.tsx
│   ├── condition-group.tsx
│   ├── condition-row.tsx
│   ├── action-builder.tsx
│   ├── baseline-field-card.tsx
│   ├── diff-adopt-wizard.tsx
│   └── preview-impact-panel.tsx
├── profiles/                  # Profile components
│   └── profile-list.tsx
├── custom-fields/             # Custom fields components
│   └── global-fields-workspace.tsx
├── dashboard/                 # Dashboard components
│   └── dashboard-summary.tsx
├── app-shell.tsx              # Main layout shell
├── providers.tsx              # Context providers
└── error-boundary.tsx         # Error handling
```

### UI Components (`components/ui/`)

Base components built on **Radix UI** primitives:

- **Headless and accessible:** Built with Radix UI (unstyled, WCAG compliant)
- **Styled with Tailwind:** Consistent design tokens via CSS variables
- **Composable:** Small, focused components that can be combined
- **Variants:** Using `class-variance-authority` for component variants

**Example: Button Component**

```tsx
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground",
        outline: "border border-input hover:bg-accent",
        ghost: "hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3",
        lg: "h-11 px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
```

### Feature Components

#### Listings Table (`components/listings/listings-table.tsx`)

**Features:**
- TanStack Table for column management and sorting
- Virtual scrolling for large datasets (TanStack Virtual)
- Debounced search (200ms)
- Filterable columns (manufacturer, form factor, CPU, GPU)
- Color-coded valuation cells
- Inline actions (edit, delete, view)
- Responsive column visibility

**Key Dependencies:**
- `@tanstack/react-table`: Headless table library
- `@tanstack/react-virtual`: Virtual scrolling
- `use-debounce`: Debounced search inputs

#### Valuation Breakdown Modal (`components/listings/valuation-breakdown-modal.tsx`)

**Purpose:** Display detailed rule-based adjustments and component deductions

**Features:**
- Rule adjustments with action details
- Component deduction breakdown
- Total adjustment calculations
- Color-coded adjustment amounts (green = savings, red = premium)

#### Rule Builder Modal (`components/valuation/rule-builder-modal.tsx`)

**Purpose:** Create and edit valuation rules with conditions and actions

**Features:**
- Multi-step wizard flow
- Condition builder with AND/OR logic
- Action builder (deduct, formula, set value)
- Form validation with Zod
- Preview impact before saving

#### Baseline Field Card (`components/valuation/baseline-field-card.tsx`)

**Purpose:** Display and manage baseline valuation fields with overrides

**Features:**
- Field metadata display (type, unit, range, formula)
- Override controls (custom value, min/max, formula)
- Reset to baseline button
- Visual indicators for overridden fields
- Tooltip with detailed field information

---

## State Management

Deal Brain uses a **hybrid state management** approach:

### 1. Server State (React Query)

**Library:** `@tanstack/react-query`
**Purpose:** Manage server data (listings, rules, profiles, etc.)

**Configuration:**

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
```

**Common Patterns:**

```tsx
// Fetch listings
const { data: listings, isLoading, error } = useQuery({
  queryKey: ["listings", "records"],
  queryFn: () => apiFetch<ListingRecord[]>("/v1/listings"),
  staleTime: 5 * 60 * 1000,
});

// Create listing mutation
const createMutation = useMutation({
  mutationFn: (data: CreateListingPayload) =>
    apiFetch("/v1/listings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["listings"] });
    toast({ title: "Listing created" });
  },
  onError: (error) => {
    toast({ title: "Failed to create", variant: "destructive" });
  },
});
```

**Query Key Conventions:**

- `["listings"]` - All listings
- `["listings", "records"]` - Listing records with full details
- `["listing", id]` - Single listing by ID
- `["rulesets"]` - All rulesets
- `["ruleset", id]` - Single ruleset with rules
- `["baseline-metadata"]` - Baseline valuation metadata
- `["baseline-overrides", entityKey]` - Field overrides for entity

### 2. Client State (Zustand)

**Library:** `zustand`
**Purpose:** Manage UI state (view modes, filters, selections)

**Example: Catalog Store** (`/mnt/containers/deal-brain/apps/web/stores/catalog-store.ts`)

```tsx
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ViewMode = 'grid' | 'list' | 'master-detail';

export interface CatalogState {
  activeView: ViewMode;
  setActiveView: (view: ViewMode) => void;

  filters: FilterState;
  setFilters: (filters: Partial<FilterState>) => void;

  compareSelections: number[];
  toggleCompare: (id: number) => void;
}

export const useCatalogStore = create<CatalogState>()(
  persist(
    (set) => ({
      activeView: 'grid',
      setActiveView: (view) => set({ activeView: view }),

      filters: { searchQuery: '', formFactor: 'all', manufacturer: 'all' },
      setFilters: (partialFilters) =>
        set((state) => ({ filters: { ...state.filters, ...partialFilters } })),

      compareSelections: [],
      toggleCompare: (id) =>
        set((state) => ({
          compareSelections: state.compareSelections.includes(id)
            ? state.compareSelections.filter((listingId) => listingId !== id)
            : [...state.compareSelections, id],
        })),
    }),
    {
      name: 'catalog-store',
      partialize: (state) => ({
        activeView: state.activeView,
        filters: state.filters,
      }),
    }
  )
);
```

**Benefits:**
- Simple API (no boilerplate)
- Middleware support (persist, devtools)
- TypeScript-first
- Fine-grained selectors for performance

### 3. URL State Synchronization

**Hook:** `useUrlSync()` (`/mnt/containers/deal-brain/apps/web/hooks/use-url-sync.ts`)

**Purpose:** Sync Zustand store state with URL query parameters for shareable URLs

```tsx
export function useUrlSync() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Hydrate store from URL on mount
  useEffect(() => {
    const urlView = searchParams.get('view') as ViewMode;
    if (urlView) setActiveView(urlView);
  }, [searchParams]);

  // Update URL when store changes (debounced)
  const updateUrl = useDebouncedCallback(() => {
    const params = new URLSearchParams();
    if (activeView !== 'grid') params.set('view', activeView);
    router.replace(`?${params.toString()}`, { scroll: false });
  }, 300);

  useEffect(() => {
    updateUrl();
  }, [activeView, filters]);
}
```

**URL Parameters:**
- `view`: grid | list | master-detail
- `tab`: catalog | data
- `q`: search query
- `formFactor`: form factor filter
- `manufacturer`: manufacturer filter
- `maxPrice`: price range filter

---

## Data Fetching

### API Utilities

**Base URL Configuration:**

```tsx
// lib/utils.ts
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
```

**Environment Variables:**
- Local development: `http://localhost:8000`
- Docker: `http://<host-ip>:8020` (set via `NEXT_PUBLIC_API_URL`)

**Fetch Wrapper:**

```tsx
// lib/utils.ts
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });

  if (!response.ok) {
    const parsed = await response.json();
    throw new ApiError(parsed.detail, response.status, parsed);
  }

  return response.json();
}
```

**Features:**
- Type-safe responses (generic `<T>`)
- Automatic JSON parsing
- Error extraction from API responses
- Content-Type header management

### API Client Modules

Organized by domain in `/mnt/containers/deal-brain/apps/web/lib/api/`:

**Baseline API** (`lib/api/baseline.ts`):

```tsx
export async function getBaselineMetadata(): Promise<BaselineMetadata> {
  return apiFetch<BaselineMetadata>("/api/v1/baseline/metadata");
}

export async function upsertFieldOverride(
  override: Omit<FieldOverride, "created_at" | "updated_at">
): Promise<FieldOverride> {
  return apiFetch<FieldOverride>("/api/v1/baseline/overrides", {
    method: "POST",
    body: JSON.stringify(override),
  });
}
```

**Listings API** (`lib/api/listings.ts`):

```tsx
export async function createListing(data: CreateListingPayload): Promise<ListingRecord> {
  return apiFetch<ListingRecord>("/v1/listings", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateListing(
  id: number,
  data: Partial<ListingRecord>
): Promise<ListingRecord> {
  return apiFetch<ListingRecord>(`/v1/listings/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}
```

### React Query Patterns

**Data Fetching:**

```tsx
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ["listings"],
  queryFn: () => apiFetch<ListingRecord[]>("/v1/listings"),
  staleTime: 5 * 60 * 1000,
  enabled: true, // Conditional fetching
});
```

**Optimistic Updates:**

```tsx
const mutation = useMutation({
  mutationFn: updateListing,
  onMutate: async (newData) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ["listing", id] });

    // Snapshot previous value
    const previous = queryClient.getQueryData(["listing", id]);

    // Optimistically update
    queryClient.setQueryData(["listing", id], newData);

    return { previous };
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(["listing", id], context.previous);
  },
  onSettled: () => {
    // Refetch after success or error
    queryClient.invalidateQueries({ queryKey: ["listing", id] });
  },
});
```

**Dependent Queries:**

```tsx
const { data: listing } = useQuery({
  queryKey: ["listing", id],
  queryFn: () => apiFetch(`/v1/listings/${id}`),
});

const { data: breakdown } = useQuery({
  queryKey: ["valuation-breakdown", id],
  queryFn: () => apiFetch(`/v1/listings/${id}/breakdown`),
  enabled: !!listing, // Only fetch if listing exists
});
```

---

## Custom Hooks

Custom hooks are located in `/mnt/containers/deal-brain/apps/web/hooks/`.

### `useValuationThresholds`

**File:** `/mnt/containers/deal-brain/apps/web/hooks/use-valuation-thresholds.ts`

**Purpose:** Fetch color-coding thresholds for valuation display

```tsx
export function useValuationThresholds() {
  return useQuery<ValuationThresholds>({
    queryKey: ['settings', 'valuation_thresholds'],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/settings/valuation_thresholds`);
      if (!response.ok) return DEFAULT_THRESHOLDS;
      return response.json();
    },
    staleTime: 5 * 60 * 1000,
    placeholderData: DEFAULT_THRESHOLDS,
  });
}
```

**Usage:**

```tsx
const { data: thresholds } = useValuationThresholds();
const style = getValuationStyle(deltaPercent, thresholds);
```

### `useFieldOptions`

**File:** `/mnt/containers/deal-brain/apps/web/hooks/use-field-options.ts`

**Purpose:** Manage dropdown options for custom fields with inline creation

```tsx
export function useFieldOptions(entity: string, fieldKey: string) {
  const { data: options = [], isLoading } = useQuery({
    queryKey: ["field-options", entity, fieldKey],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/v1/fields-data/${entity}/${fieldKey}/options`);
      const data = await response.json();
      return data.options || [];
    },
  });

  const createOption = useMutation({
    mutationFn: async (value: string) => {
      const response = await fetch(`${API_URL}/v1/fields-data/${entity}/${fieldKey}/options`, {
        method: "POST",
        body: JSON.stringify({ value }),
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["field-options", entity, fieldKey] });
    },
  });

  return { options, isLoading, createOption: (value: string) => createOption.mutateAsync(value) };
}
```

**Usage:**

```tsx
const { options, createOption } = useFieldOptions("listing", "manufacturer");

// Inline option creation
<ComboBox
  options={options}
  onCreateOption={createOption}
  placeholder="Select or create manufacturer..."
/>
```

### `useBaselineOverrides`

**File:** `/mnt/containers/deal-brain/apps/web/hooks/use-baseline-overrides.ts`

**Purpose:** Manage field overrides for baseline valuation with auto-save and unsaved changes tracking

```tsx
export function useBaselineOverrides({ entityKey, autoSave = false }) {
  const [localOverrides, setLocalOverrides] = useState<Map<string, FieldOverride>>(new Map());
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const { data: serverOverrides = [] } = useQuery({
    queryKey: ["baseline-overrides", entityKey],
    queryFn: () => getEntityOverrides(entityKey),
  });

  const applyOverride = useCallback((fieldName: string, overrideData: Partial<FieldOverride>) => {
    const newOverride: FieldOverride = {
      field_name: fieldName,
      entity_key: entityKey,
      is_enabled: true,
      ...overrideData,
    };

    setLocalOverrides((prev) => new Map(prev).set(fieldName, newOverride));
    setHasUnsavedChanges(true);

    if (autoSave) {
      upsertMutation.mutate(newOverride);
    }
  }, [entityKey, autoSave]);

  return {
    overrides: localOverrides,
    hasUnsavedChanges,
    applyOverride,
    resetField,
    saveOverrides,
    discardChanges,
  };
}
```

**Features:**
- Local state with unsaved changes tracking
- Auto-save mode for immediate persistence
- Bulk save for manual confirmation
- Optimistic updates with rollback on error

### `useUrlSync`

**File:** `/mnt/containers/deal-brain/apps/web/hooks/use-url-sync.ts`

**Purpose:** Synchronize Zustand store with URL query parameters

**Features:**
- Hydrate store from URL on mount
- Debounced URL updates (300ms)
- Browser back/forward navigation support
- Shareable URLs with state

---

## TypeScript Types

Type definitions are organized in `/mnt/containers/deal-brain/apps/web/types/`.

### `listings.ts`

**Core Types:**

```tsx
export interface ListingRecord {
  id: number;
  title: string;
  price_usd: number;
  adjusted_price_usd: number | null;
  score_composite: number | null;
  cpu_id?: number | null;
  cpu?: CpuRecord | null;
  gpu_id?: number | null;
  gpu?: { id?: number | null; name?: string | null } | null;
  valuation_breakdown?: ValuationBreakdown | null;
  attributes: Record<string, unknown>;
  // ... more fields
}

export interface ValuationBreakdown {
  listing_price: number;
  adjusted_price: number;
  total_adjustment: number;
  adjustments: ValuationAdjustment[];
  ruleset?: { id?: number; name?: string };
}

export interface ValuationAdjustment {
  rule_id?: number | null;
  rule_name: string;
  adjustment_amount: number;
  actions: ValuationAdjustmentAction[];
}
```

### `baseline.ts`

**Baseline Types:**

```tsx
export type BaselineFieldType = "scalar" | "presence" | "multiplier" | "formula";

export interface BaselineField {
  field_name: string;
  field_type: string;
  proper_name?: string;
  description?: string;
  unit?: string;
  min_value?: number;
  max_value?: number;
  formula?: string;
  nullable: boolean;
}

export interface FieldOverride {
  field_name: string;
  entity_key: string;
  override_value?: number;
  override_min?: number;
  override_max?: number;
  override_formula?: string;
  is_enabled: boolean;
}

export interface BaselineMetadata {
  version: string;
  entities: BaselineEntity[];
  source_hash: string;
  is_active: boolean;
}
```

### Type Safety Best Practices

1. **Strict TypeScript configuration:**

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": false,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

2. **Use discriminated unions for component variants:**

```tsx
type ButtonVariant =
  | { variant: "primary"; onClick: () => void }
  | { variant: "link"; href: string };
```

3. **Type API responses with Zod for runtime validation:**

```tsx
import { z } from "zod";

const ListingSchema = z.object({
  id: z.number(),
  title: z.string(),
  price_usd: z.number(),
  adjusted_price_usd: z.number().nullable(),
});

type Listing = z.infer<typeof ListingSchema>;
```

---

## Styling System

### Tailwind CSS Configuration

**File:** `/mnt/containers/deal-brain/apps/web/tailwind.config.ts`

```tsx
export default {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))"
        },
        // ... more color tokens
      },
    }
  },
  plugins: [require("tailwindcss-animate")]
};
```

### CSS Variables (Design Tokens)

**File:** `/mnt/containers/deal-brain/apps/web/app/globals.css`

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;

    /* Valuation color scheme */
    --valuation-great-deal-bg: 142 76% 36%;
    --valuation-great-deal-fg: 0 0% 100%;
    --valuation-good-deal-bg: 142 71% 45%;
    --valuation-light-saving-bg: 142 52% 96%;
    --valuation-premium-bg: 0 84% 60%;
    --valuation-neutral-bg: 215 20% 65%;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;

    /* Dark mode valuation colors */
    --valuation-great-deal-bg: 142 76% 20%;
    --valuation-good-deal-bg: 142 71% 25%;
    /* ... */
  }
}
```

### Utility Functions

**cn() - Class Name Utility:**

```tsx
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Usage:**

```tsx
<div className={cn(
  "base-class",
  isActive && "active-class",
  className // Override with props
)} />
```

### Component Variants (CVA)

**Example:**

```tsx
import { cva } from "class-variance-authority";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        secondary: "bg-secondary text-secondary-foreground",
        destructive: "bg-destructive text-destructive-foreground",
        outline: "border border-input text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export function Badge({ variant, className, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
```

### Responsive Design

**Breakpoints:**

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

**Responsive Patterns:**

```tsx
<div className="
  flex flex-col                 // Mobile: stack vertically
  md:flex-row                   // Tablet+: horizontal layout
  lg:grid lg:grid-cols-3        // Desktop: 3-column grid
">
```

---

## Best Practices

### 1. Component Composition

**Good:**

```tsx
function ListingCard({ listing }: { listing: ListingRecord }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{listing.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ValuationBadge listing={listing} />
        <PriceDisplay price={listing.price_usd} />
      </CardContent>
    </Card>
  );
}
```

**Avoid:** Monolithic components with excessive logic

### 2. Performance Optimization

**Memoization:**

```tsx
const ExpensiveComponent = memo(({ data }: { data: DataType }) => {
  return <div>{/* expensive rendering */}</div>;
});

const MemoizedList = useMemo(
  () => listings.filter(l => l.score_composite > 50),
  [listings]
);
```

**Debouncing:**

```tsx
import { useDebouncedCallback } from 'use-debounce';

const handleSearch = useDebouncedCallback((query: string) => {
  setFilters({ searchQuery: query });
}, 200);

<Input onChange={(e) => handleSearch(e.target.value)} />
```

### 3. Accessibility

**Keyboard Navigation:**

```tsx
<button
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
  aria-label="View listing details"
  tabIndex={0}
>
```

**ARIA Attributes:**

```tsx
<div role="dialog" aria-labelledby="dialog-title" aria-describedby="dialog-description">
  <h2 id="dialog-title">Delete Listing</h2>
  <p id="dialog-description">This action cannot be undone.</p>
</div>
```

**Focus Management:**

```tsx
useEffect(() => {
  if (isOpen) {
    dialogRef.current?.focus();
  }
}, [isOpen]);
```

### 4. Error Handling

**Error Boundaries:**

```tsx
<ErrorBoundary fallback={<ErrorFallback />}>
  <ExpensiveComponent />
</ErrorBoundary>
```

**Query Error Handling:**

```tsx
const { data, error, isError } = useQuery({
  queryKey: ["listings"],
  queryFn: fetchListings,
  retry: 3,
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
});

if (isError) {
  return <ErrorDisplay error={error} />;
}
```

### 5. Testing Considerations

**Component Testing (Future):**

```tsx
// Example structure for component tests
describe('ListingCard', () => {
  it('displays listing title and price', () => {
    render(<ListingCard listing={mockListing} />);
    expect(screen.getByText(mockListing.title)).toBeInTheDocument();
  });
});
```

**API Mocking:**

```tsx
// Mock API responses for testing
const mockListings = [
  { id: 1, title: "Test Listing", price_usd: 500 }
];

queryClient.setQueryData(["listings"], mockListings);
```

---

## Appendix: File Paths Reference

### Key Files

| File | Path |
|------|------|
| Root Layout | `/mnt/containers/deal-brain/apps/web/app/layout.tsx` |
| Providers | `/mnt/containers/deal-brain/apps/web/components/providers.tsx` |
| App Shell | `/mnt/containers/deal-brain/apps/web/components/app-shell.tsx` |
| API Utilities | `/mnt/containers/deal-brain/apps/web/lib/utils.ts` |
| Catalog Store | `/mnt/containers/deal-brain/apps/web/stores/catalog-store.ts` |
| Listings Page | `/mnt/containers/deal-brain/apps/web/app/listings/page.tsx` |
| Valuation Rules Page | `/mnt/containers/deal-brain/apps/web/app/valuation-rules/page.tsx` |
| Tailwind Config | `/mnt/containers/deal-brain/apps/web/tailwind.config.ts` |
| TypeScript Config | `/mnt/containers/deal-brain/apps/web/tsconfig.json` |
| Package Config | `/mnt/containers/deal-brain/apps/web/package.json` |

### Directory Structure

```
apps/web/
├── app/                          # Next.js 14 App Router pages
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Dashboard
│   ├── listings/                 # Listings pages
│   ├── valuation-rules/          # Valuation rules pages
│   ├── profiles/                 # Profiles pages
│   ├── global-fields/            # Global fields pages
│   ├── import/                   # Import pages
│   └── admin/                    # Admin pages
├── components/                   # React components
│   ├── ui/                       # Base UI components (Radix)
│   ├── listings/                 # Listing components
│   ├── valuation/                # Valuation components
│   ├── profiles/                 # Profile components
│   ├── custom-fields/            # Custom field components
│   ├── dashboard/                # Dashboard components
│   ├── forms/                    # Form components
│   └── app-shell.tsx             # App shell
├── hooks/                        # Custom React hooks
├── lib/                          # Utility functions and API clients
│   ├── api/                      # API client modules
│   ├── utils.ts                  # General utilities
│   └── valuation-utils.ts        # Valuation utilities
├── stores/                       # Zustand stores
├── types/                        # TypeScript types
├── public/                       # Static assets
└── styles/                       # Global styles
```

---

**End of Document**
