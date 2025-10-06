# Implementation Plan: 10-6 UX Enhancements & Bug Fixes

**Version:** 1.0
**Date:** October 6, 2025
**Status:** Ready for Execution
**Estimated Duration:** 16-20 days

---

## 1. Overview

### 1.1 Implementation Philosophy

This implementation plan prioritizes **critical bug fixes first**, then builds UI enhancements on a stable foundation. Each phase is designed for incremental delivery with clear validation checkpoints.

**Core Principles:**
- Bug fixes are non-negotiable blockers for UI work
- Reuse existing patterns from ui-enhancements-context.md
- Follow Deal Brain architectural standards (strict layering, cursor pagination, 3rd-party UI components)
- Test at component boundaries, not implementation details

### 1.2 Phase Summary

| Phase | Focus | Complexity | Duration | Dependencies |
|-------|-------|------------|----------|--------------|
| **Phase 1** | Critical Bug Fixes | High | 2-3 days | None |
| **Phase 2** | Table Foundation | Medium | 2-3 days | Phase 1 |
| **Phase 3** | CPU Intelligence | Medium | 3-4 days | Phase 2 |
| **Phase 4** | Enhanced Dropdowns | Low | 2 days | Phase 2 |
| **Phase 5** | Modal Navigation | Medium | 2-3 days | Phase 2 |
| **Phase 6** | Testing & Polish | Medium | 3-4 days | All phases |

**Total:** 14-19 days (buffer included)

---

## 2. Phase 1: Critical Bug Fixes (BLOCKER)

**Objective:** Fix calculation errors, type issues, and seed script before any UI work.

### 2.1 Bug Fix 1: CPU Mark Calculations

**Root Cause:** Metric calculation not triggered on listing create/update.

**Tasks:**
1. Verify `dollar_per_cpu_mark_single` and `dollar_per_cpu_mark_multi` columns exist in listing table
2. Check `apply_listing_metrics()` in `apps/api/dealbrain_api/services/listings.py` (line 39-135)
3. Add CPU Mark calculations after line 94 (after perf_per_watt calculation):
   ```python
   # Dollar per CPU Mark metrics
   if listing.adjusted_price_usd and cpu:
       if cpu.cpu_mark_single:
           listing.dollar_per_cpu_mark_single = listing.adjusted_price_usd / cpu.cpu_mark_single
       if cpu.cpu_mark_multi:
           listing.dollar_per_cpu_mark_multi = listing.adjusted_price_usd / cpu.cpu_mark_multi
   ```
4. Verify calculation triggers on listing update in `update_listing()` service method
5. Create bulk recalculation script: `scripts/recalculate_cpu_marks.py`
6. Run script on existing listings

**Files to Modify:**
- `apps/api/dealbrain_api/services/listings.py` (add calculations)
- `apps/api/dealbrain_api/models/core.py` (verify columns exist)

**Files to Create:**
- `scripts/recalculate_cpu_marks.py`

**Testing:**
- Unit test: Create listing with CPU + price → verify metrics calculated
- Unit test: Update CPU on listing → verify metrics recalculated
- Unit test: Update price on listing → verify metrics recalculated
- Manual: Check listings table shows calculated values

**Completion Criteria:** All listings with CPU + price display non-null CPU Mark metrics.

---

### 2.2 Bug Fix 2: CPU Save Type Error

**Root Cause:** Frontend sends `cpu_id` as string, backend expects integer.

**Tasks:**
1. Locate CPU dropdown in `apps/web/components/listings/listings-table.tsx` or `add-listing-form.tsx`
2. Find ComboBox value handler for cpu_id field
3. Add type coercion before API call:
   ```typescript
   const cpu_id = cpuValue ? parseInt(cpuValue, 10) : null;
   ```
4. Update Pydantic schema in `apps/api/dealbrain_api/schemas/listings.py`:
   ```python
   from pydantic import field_validator

   class UpdateListingRequest(BaseModel):
       cpu_id: int | None = None

       @field_validator('cpu_id', mode='before')
       @classmethod
       def coerce_cpu_id(cls, v):
           if v is None or v == '':
               return None
           return int(v)
   ```
5. Add defensive casting in service layer (belt-and-suspenders approach)

**Files to Modify:**
- `apps/web/components/listings/listings-table.tsx` (type coercion in mutation)
- `apps/api/dealbrain_api/schemas/listings.py` (add validator)
- `apps/api/dealbrain_api/services/listings.py` (defensive cast if needed)

**Testing:**
- Manual: Select CPU in listings table → save → verify no error
- Manual: Edit CPU in add listing form → save → verify persists
- Unit test: API accepts string cpu_id and casts to int
- Unit test: API accepts integer cpu_id without error

**Completion Criteria:** CPU selection saves successfully with no type errors.

---

### 2.3 Bug Fix 3: Seed Script Port Model Error

**Root Cause:** Script uses `port_profile_id` but model expects `ports_profile_id`.

**Tasks:**
1. Review Port model in `apps/api/dealbrain_api/models/core.py` line 70-80
2. Confirm field is `ports_profile_id` (line 75)
3. Update `scripts/seed_sample_listings.py` line 169-174:
   ```python
   port = Port(
       ports_profile_id=ports_profile.id,  # Changed from port_profile_id
       type=port_data["port_type"],        # Changed from port_type
       count=port_data["quantity"],        # Changed from quantity
   )
   ```
4. Verify Port model field names match script
5. Run seed script in clean database to verify

**Files to Modify:**
- `scripts/seed_sample_listings.py` (fix field names)

**Testing:**
- Run script with `poetry run python scripts/seed_sample_listings.py`
- Verify 5 sample listings created
- Verify PortsProfile and Port records exist
- Query database to confirm relationships

**Completion Criteria:** Seed script executes without errors and creates valid data.

---

## 3. Phase 2: Table Foundation

**Objective:** Restore column resizing and fix dropdown width consistency.

### 3.1 Restore Column Resizing

**Context:** Column resizing was working previously but broke. DataGrid component has infrastructure (line 100-143 in data-grid.tsx) but may not be enabled.

**Tasks:**
1. Check `useReactTable` options in `apps/web/components/ui/data-grid.tsx` (around line 250-300)
2. Ensure `enableColumnResizing: true` in table options
3. Verify `columnResizeMode: "onChange"` is set
4. Check column definitions have resize enabled (not disabled per column)
5. Verify resize handle rendering in TableHead component
6. Test `useColumnSizingPersistence` hook is wired correctly (line 100-143)
7. Add visual resize handle if missing:
   ```tsx
   <div
     onMouseDown={header.getResizeHandler()}
     onTouchStart={header.getResizeHandler()}
     className="absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-primary"
     style={{ userSelect: 'none' }}
   />
   ```
8. Apply column-specific minimum widths from PRD:
   - Title/Name columns: 200px minimum
   - Price/Valuation columns: 120px minimum
   - Short enum fields: 100px minimum
9. Enable text wrapping for Title column in listings-table.tsx:
   ```tsx
   meta: {
     minWidth: 200,
     enableTextWrap: true,
   }
   ```

**Files to Modify:**
- `apps/web/components/ui/data-grid.tsx` (enable resizing, add handle)
- `apps/web/components/listings/listings-table.tsx` (column meta configs)

**Testing:**
- Manual: Hover between column headers → cursor changes to col-resize
- Manual: Drag column border → width changes smoothly
- Manual: Resize Title column → text wraps instead of truncating
- Manual: Refresh page → column widths persist
- Verify localStorage key: `dealbrain_listings_table_state_v1:columnSizing`

**Completion Criteria:** All table columns resizable with persisted widths and minimum constraints.

---

### 3.2 Dropdown Width Consistency

**Context:** Existing ComboBox component used for dropdowns, but width calculation may be missing or inconsistent.

**Tasks:**
1. Locate ComboBox component in `apps/web/components/forms/combobox.tsx`
2. Create width calculation utility:
   ```typescript
   // apps/web/lib/dropdown-utils.ts
   export function calculateDropdownWidth(options: string[]): number {
     if (!options.length) return 120; // minimum

     // Calculate longest option (approximate: 8px per character + padding)
     const maxLength = Math.max(...options.map(o => o.length));
     const width = maxLength * 8 + 40 + 24; // text + padding + chevron

     return Math.min(Math.max(width, 120), 400); // clamp 120-400px
   }
   ```
3. Apply width to ComboBox trigger button:
   ```tsx
   const width = useMemo(
     () => calculateDropdownWidth(options.map(o => o.label)),
     [options]
   );

   <Button
     style={{ width: `${width}px`, minWidth: '120px' }}
     className="justify-between"
   >
   ```
4. Update Popover to match or exceed button width:
   ```tsx
   <PopoverContent style={{ width: `${width}px` }}>
   ```
5. Test with Condition and Status dropdowns in listings table (currently too small per request)
6. Apply to all dropdown fields: RAM, Storage, Storage Type, Condition, Status

**Files to Create:**
- `apps/web/lib/dropdown-utils.ts`

**Files to Modify:**
- `apps/web/components/forms/combobox.tsx` (width calculation)
- `apps/web/components/listings/listings-table.tsx` (verify all dropdowns use ComboBox)

**Testing:**
- Manual: Condition dropdown displays full option text without truncation
- Manual: RAM dropdown shows "128 GB" fully visible
- Manual: Dropdown width exceeds column width if necessary (not constrained)
- Visual: All dropdowns have consistent styling

**Completion Criteria:** All dropdown fields auto-size to longest option with consistent padding.

---

## 4. Phase 3: CPU Intelligence

**Objective:** Add CPU tooltip with specs and full details modal.

### 4.1 CPU Data API Integration

**Tasks:**
1. Verify listings API includes full CPU object in response
2. Check `GET /v1/listings` endpoint in `apps/api/dealbrain_api/api/listings.py`
3. Ensure CPU relationship uses `selectin` loading (already set in models/core.py line 41)
4. Update ListingRow interface in listings-table.tsx to include full CPU data:
   ```typescript
   interface ListingRow extends ListingRecord {
     cpu?: {
       id: number;
       name: string;
       manufacturer: string;
       cpu_mark_single: number | null;
       cpu_mark_multi: number | null;
       igpu_model: string | null;
       igpu_mark: number | null;
       tdp_w: number | null;
       release_year: number | null;
       cores: number | null;
       threads: number | null;
       socket: string | null;
       notes: string | null;
     } | null;
   }
   ```
5. Verify API response includes CPU data in list queries
6. Add CPU to API response schema if missing

**Files to Modify:**
- `apps/web/components/listings/listings-table.tsx` (ListingRow interface)
- `apps/api/dealbrain_api/schemas/listings.py` (ensure CpuResponse nested)
- `apps/api/dealbrain_api/api/listings.py` (verify selectin loading)

**Testing:**
- API test: GET /v1/listings → response includes nested cpu object
- Frontend test: useQuery for listings → cpu data available in rows

**Completion Criteria:** Listings API returns full CPU data without separate requests.

---

### 4.2 CPU Tooltip Component

**Pattern Reference:** Follow DeltaBadge + ValuationCell pattern from ui-enhancements-context.md

**Tasks:**
1. Create `apps/web/components/listings/cpu-tooltip.tsx`:
   ```tsx
   import { Info } from "lucide-react";
   import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
   import { Button } from "../ui/button";

   interface CpuTooltipProps {
     cpu: CpuData;
     onViewDetails: () => void;
   }

   export function CpuTooltip({ cpu, onViewDetails }: CpuTooltipProps) {
     return (
       <Popover>
         <PopoverTrigger asChild>
           <Button
             variant="ghost"
             size="sm"
             className="h-4 w-4 p-0"
             aria-label="View CPU details"
           >
             <Info className="h-4 w-4 text-muted-foreground" />
           </Button>
         </PopoverTrigger>
         <PopoverContent className="w-80">
           <div className="space-y-2">
             <h4 className="font-semibold text-sm">{cpu.name}</h4>

             <div className="grid grid-cols-2 gap-2 text-xs">
               <div>
                 <span className="text-muted-foreground">Single-Thread:</span>
                 <span className="ml-1">{cpu.cpu_mark_single?.toLocaleString() ?? 'N/A'}</span>
               </div>
               <div>
                 <span className="text-muted-foreground">Multi-Thread:</span>
                 <span className="ml-1">{cpu.cpu_mark_multi?.toLocaleString() ?? 'N/A'}</span>
               </div>
               <div>
                 <span className="text-muted-foreground">iGPU:</span>
                 <span className="ml-1">{cpu.igpu_model ?? 'No'}</span>
               </div>
               <div>
                 <span className="text-muted-foreground">iGPU Mark:</span>
                 <span className="ml-1">{cpu.igpu_mark?.toLocaleString() ?? 'N/A'}</span>
               </div>
               <div>
                 <span className="text-muted-foreground">TDP:</span>
                 <span className="ml-1">{cpu.tdp_w ? `${cpu.tdp_w}W` : 'N/A'}</span>
               </div>
               <div>
                 <span className="text-muted-foreground">Year:</span>
                 <span className="ml-1">{cpu.release_year ?? 'N/A'}</span>
               </div>
             </div>

             <Button
               onClick={onViewDetails}
               variant="outline"
               size="sm"
               className="w-full mt-2"
             >
               View Full CPU Details
             </Button>
           </div>
         </PopoverContent>
       </Popover>
     );
   }
   ```

2. Integrate into CPU column in listings-table.tsx:
   ```tsx
   {
     id: "cpu_name",
     header: "CPU",
     cell: ({ row }) => {
       const cpu = row.original.cpu;
       if (!cpu) return <span className="text-muted-foreground">—</span>;

       return (
         <div className="flex items-center gap-2">
           <span>{cpu.name}</span>
           <CpuTooltip
             cpu={cpu}
             onViewDetails={() => {
               setSelectedCpu(cpu);
               setCpuModalOpen(true);
             }}
           />
         </div>
       );
     },
   }
   ```

3. Add React.memo for performance:
   ```tsx
   export const CpuTooltip = React.memo(CpuTooltipComponent);
   ```

**Files to Create:**
- `apps/web/components/listings/cpu-tooltip.tsx`

**Files to Modify:**
- `apps/web/components/listings/listings-table.tsx` (integrate tooltip)

**Testing:**
- Manual: Hover over Info icon → tooltip appears with CPU specs
- Manual: Click "View Full Details" → triggers modal open
- Accessibility: Tab to Info icon → Enter shows tooltip
- Accessibility: Screen reader announces "View CPU details"
- Performance: React.memo prevents unnecessary re-renders

**Completion Criteria:** CPU tooltip displays key specs with accessible interactions.

---

### 4.3 CPU Details Modal

**Pattern Reference:** Follow ValuationBreakdownModal pattern from ui-enhancements-context.md

**Tasks:**
1. Create `apps/web/components/listings/cpu-details-modal.tsx`:
   ```tsx
   import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
   import { Separator } from "../ui/separator";

   interface CpuDetailsModalProps {
     cpu: CpuData | null;
     open: boolean;
     onOpenChange: (open: boolean) => void;
   }

   export function CpuDetailsModal({ cpu, open, onOpenChange }: CpuDetailsModalProps) {
     if (!cpu) return null;

     return (
       <Dialog open={open} onOpenChange={onOpenChange}>
         <DialogContent className="max-w-2xl">
           <DialogHeader>
             <DialogTitle>{cpu.name}</DialogTitle>
           </DialogHeader>

           <div className="space-y-4">
             <Section title="Core Specifications">
               <SpecRow label="Manufacturer" value={cpu.manufacturer} />
               <SpecRow label="Socket" value={cpu.socket} />
               <SpecRow label="Cores" value={cpu.cores} />
               <SpecRow label="Threads" value={cpu.threads} />
             </Section>

             <Separator />

             <Section title="Performance Metrics">
               <SpecRow label="CPU Mark (Multi)" value={cpu.cpu_mark_multi?.toLocaleString()} />
               <SpecRow label="CPU Mark (Single)" value={cpu.cpu_mark_single?.toLocaleString()} />
               <SpecRow label="iGPU Mark" value={cpu.igpu_mark?.toLocaleString()} />
             </Section>

             <Separator />

             <Section title="Power & Thermal">
               <SpecRow label="TDP" value={cpu.tdp_w ? `${cpu.tdp_w}W` : null} />
               <SpecRow label="Release Year" value={cpu.release_year} />
             </Section>

             {cpu.igpu_model && (
               <>
                 <Separator />
                 <Section title="Graphics">
                   <SpecRow label="Integrated GPU" value={cpu.igpu_model} />
                 </Section>
               </>
             )}

             {cpu.notes && (
               <>
                 <Separator />
                 <Section title="Notes">
                   <p className="text-sm">{cpu.notes}</p>
                 </Section>
               </>
             )}
           </div>
         </DialogContent>
       </Dialog>
     );
   }

   function Section({ title, children }: { title: string; children: React.ReactNode }) {
     return (
       <div>
         <h4 className="text-sm font-semibold mb-2">{title}</h4>
         <div className="grid grid-cols-2 gap-3">{children}</div>
       </div>
     );
   }

   function SpecRow({ label, value }: { label: string; value: any }) {
     return (
       <div className="flex justify-between text-sm">
         <span className="text-muted-foreground">{label}:</span>
         <span className="font-medium">{value ?? 'N/A'}</span>
       </div>
     );
   }
   ```

2. Integrate into listings-table.tsx:
   ```tsx
   const [selectedCpu, setSelectedCpu] = useState<CpuData | null>(null);
   const [cpuModalOpen, setCpuModalOpen] = useState(false);

   return (
     <>
       <DataGrid ... />

       <CpuDetailsModal
         cpu={selectedCpu}
         open={cpuModalOpen}
         onOpenChange={setCpuModalOpen}
       />
     </>
   );
   ```

**Files to Create:**
- `apps/web/components/listings/cpu-details-modal.tsx`

**Files to Modify:**
- `apps/web/components/listings/listings-table.tsx` (state management, modal integration)

**Testing:**
- Manual: Click "View Full Details" → modal opens with all CPU fields
- Manual: ESC key closes modal
- Manual: Click outside modal → closes
- Accessibility: Focus trapped in modal when open
- Accessibility: Focus returns to tooltip button on close

**Completion Criteria:** CPU modal displays all specification fields with proper layout.

---

## 5. Phase 4: Enhanced Dropdowns

**Objective:** Convert Secondary Storage to dropdown and replace browser prompt with custom modal.

### 5.1 Secondary Storage Dropdown

**Context:** Reuse pattern from Phase 2 (Primary Storage dropdown).

**Tasks:**
1. Update DROPDOWN_FIELD_CONFIGS in listings-table.tsx (already has primary_storage_gb pattern):
   ```typescript
   const DROPDOWN_FIELD_CONFIGS: Record<string, string[]> = {
     'ram_gb': ['4', '8', '16', '24', '32', '48', '64', '96', '128'],
     'primary_storage_gb': ['128', '256', '512', '1024', '2048', '4096'],
     'secondary_storage_gb': ['128', '256', '512', '1024', '2048', '4096'], // Add this
     'storage_type': ['SSD', 'HDD', 'NVMe', 'eMMC'],
   };
   ```

2. Verify EditableCell component handles secondary_storage_gb as dropdown
3. Update add-listing-form.tsx to use ComboBox for secondary storage:
   ```tsx
   <FormField label="Secondary Storage (GB)">
     <ComboBox
       options={STORAGE_OPTIONS}
       value={formData.secondary_storage_gb?.toString() ?? ''}
       onChange={(value) => handleChange('secondary_storage_gb', parseInt(value))}
       placeholder="Select storage..."
       enableInlineCreate
       fieldId={/* get from schema */}
       fieldName="Secondary Storage (GB)"
     />
   </FormField>
   ```

4. Ensure inline creation works (uses existing ComboBox infrastructure)

**Files to Modify:**
- `apps/web/components/listings/listings-table.tsx` (add to dropdown configs)
- `apps/web/components/listings/add-listing-form.tsx` (replace number input with dropdown)

**Testing:**
- Manual: Click Secondary Storage cell → dropdown appears with options
- Manual: Select 512 GB → value saves correctly
- Manual: Type custom value → inline creation modal appears
- Verify stored as number in database (no schema change needed)

**Completion Criteria:** Secondary Storage uses dropdown matching Primary Storage pattern.

---

### 5.2 Custom Inline Creation Modal

**Context:** ComboBox already supports inline creation (ui-enhancements-context.md Phase 2). This task improves the UI from browser prompt to custom modal.

**Tasks:**
1. Check existing inline creation in `apps/web/components/forms/combobox.tsx`
2. Verify confirmation dialog is used (from ui-enhancements-context.md):
   ```tsx
   const { showConfirmation } = useConfirmation();

   const handleCreateOption = async () => {
     const confirmed = await showConfirmation({
       title: `Add New ${fieldName} Option`,
       message: `Add "${searchValue}" as a new option for all listings?`,
     });

     if (!confirmed) return;

     // Call API to create option...
   };
   ```

3. If browser `prompt()` is still used anywhere, replace with confirmation dialog
4. Add input validation in confirmation dialog:
   - Non-empty value
   - No duplicate check (handled server-side)
   - Appropriate format for field type (number fields: numeric validation)

5. Enhance with custom modal if needed (future: multi-field option creation)

**Files to Modify:**
- `apps/web/components/forms/combobox.tsx` (verify confirmation dialog, no prompt())

**Testing:**
- Manual: Type "48" in RAM dropdown → click "Create new option: 48"
- Verify: Confirmation dialog appears (not browser prompt)
- Manual: Confirm → option added and selected
- Manual: Cancel → modal closes, no option added
- API test: New option available globally for field

**Completion Criteria:** All inline creation uses custom confirmation dialog, no browser prompts.

---

## 6. Phase 5: Modal Navigation

**Objective:** Enhance Add Entry modal with expandable behavior and add dashboard listing modals.

### 6.1 Add Entry Modal Expandable

**Context:** Existing modal pattern from ui-enhancements-context.md Phase 1 (modal-shell component).

**Tasks:**
1. Create `apps/web/components/listings/add-listing-modal.tsx`:
   ```tsx
   import { useState } from "react";
   import { Maximize2, Minimize2 } from "lucide-react";
   import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
   import { Button } from "../ui/button";
   import { AddListingForm } from "./add-listing-form";

   interface AddListingModalProps {
     open: boolean;
     onOpenChange: (open: boolean) => void;
     onSuccess?: () => void;
   }

   export function AddListingModal({ open, onOpenChange, onSuccess }: AddListingModalProps) {
     const [expanded, setExpanded] = useState(false);

     if (expanded) {
       // Full-screen mode
       return (
         <div className="fixed inset-0 z-50 bg-background">
           <div className="flex h-full flex-col">
             <div className="border-b px-6 py-4 flex items-center justify-between">
               <h2 className="text-lg font-semibold">Add New Listing</h2>
               <div className="flex gap-2">
                 <Button
                   variant="ghost"
                   size="sm"
                   onClick={() => setExpanded(false)}
                   aria-label="Collapse to modal"
                 >
                   <Minimize2 className="h-4 w-4" />
                 </Button>
                 <Button
                   variant="ghost"
                   size="sm"
                   onClick={() => onOpenChange(false)}
                 >
                   Close
                 </Button>
               </div>
             </div>

             <div className="flex-1 overflow-auto p-6">
               <AddListingForm onSuccess={onSuccess} />
             </div>
           </div>
         </div>
       );
     }

     // Modal mode
     return (
       <Dialog open={open} onOpenChange={onOpenChange}>
         <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
           <DialogHeader>
             <DialogTitle className="flex items-center justify-between">
               Add New Listing
               <Button
                 variant="ghost"
                 size="sm"
                 onClick={() => setExpanded(true)}
                 aria-label="Expand to full screen"
               >
                 <Maximize2 className="h-4 w-4" />
               </Button>
             </DialogTitle>
           </DialogHeader>

           <AddListingForm onSuccess={onSuccess} />
         </DialogContent>
       </Dialog>
     );
   }
   ```

2. Update Data Tab (Global Fields page) "Add entry" button:
   ```tsx
   // apps/web/app/data/page.tsx or equivalent
   const [addModalOpen, setAddModalOpen] = useState(false);

   <Button onClick={() => setAddModalOpen(true)}>
     Add Entry
   </Button>

   <AddListingModal
     open={addModalOpen}
     onOpenChange={setAddModalOpen}
     onSuccess={() => {
       setAddModalOpen(false);
       refetchListings();
     }}
   />
   ```

3. Update /listings page "Add Listing" button similarly
4. Ensure form data persists when toggling expanded state
5. Add smooth transition animation (200ms ease-in-out)

**Files to Create:**
- `apps/web/components/listings/add-listing-modal.tsx`

**Files to Modify:**
- `apps/web/app/data/page.tsx` (if Data Tab exists, otherwise document location)
- `apps/web/app/listings/page.tsx` (update Add Listing button)

**Testing:**
- Manual: Click "Add Entry" → modal opens
- Manual: Click expand icon → transitions to full screen
- Manual: Fill form fields → toggle expanded → data persists
- Manual: Click collapse → returns to modal mode
- Manual: Submit form in modal mode → closes on success
- Manual: Submit form in expanded mode → closes on success
- Accessibility: Focus management during expand/collapse

**Completion Criteria:** Add Listing modal supports expand/collapse with state preservation.

---

### 6.2 Dashboard Listing Overview Modals

**Context:** Dashboard likely exists at `apps/web/app/page.tsx` or `apps/web/components/dashboard/dashboard-summary.tsx`.

**Tasks:**
1. Locate dashboard summary cards (Best CPU Mark, Top Perf/Watt, etc.)
2. Create `apps/web/components/listings/listing-overview-modal.tsx`:
   ```tsx
   import { useQuery } from "@tanstack/react-query";
   import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
   import { Button } from "../ui/button";
   import { Separator } from "../ui/separator";
   import { ValuationCell } from "./valuation-cell";
   import { DualMetricCell } from "./dual-metric-cell";
   import { PortsDisplay } from "./ports-display";
   import { apiFetch } from "../../lib/utils";

   interface ListingOverviewModalProps {
     listingId: number | null;
     open: boolean;
     onOpenChange: (open: boolean) => void;
   }

   export function ListingOverviewModal({ listingId, open, onOpenChange }: ListingOverviewModalProps) {
     const { data: listing, isLoading } = useQuery({
       queryKey: ['listing', listingId],
       queryFn: async () => {
         const response = await apiFetch(`/v1/listings/${listingId}`);
         return response.json();
       },
       enabled: open && !!listingId,
       staleTime: 5 * 60 * 1000, // 5 minutes
     });

     if (!open || !listingId) return null;

     return (
       <Dialog open={open} onOpenChange={onOpenChange}>
         <DialogContent className="max-w-3xl">
           {isLoading ? (
             <div>Loading...</div>
           ) : listing ? (
             <>
               <DialogHeader>
                 <DialogTitle>{listing.title}</DialogTitle>
               </DialogHeader>

               <div className="space-y-4">
                 {listing.thumbnail_url && (
                   <img
                     src={listing.thumbnail_url}
                     alt={listing.title}
                     className="w-full max-w-md rounded-lg"
                   />
                 )}

                 <Section title="Pricing">
                   <ValuationCell
                     basePrice={listing.price_usd}
                     adjustedPrice={listing.adjusted_price_usd}
                     listingId={listing.id}
                   />
                 </Section>

                 <Separator />

                 <Section title="Performance Metrics">
                   <DualMetricCell
                     singleValue={listing.dollar_per_cpu_mark_single}
                     multiValue={listing.dollar_per_cpu_mark_multi}
                   />
                   <div className="text-sm">
                     <span className="text-muted-foreground">Composite Score:</span>
                     <span className="ml-2 font-medium">{listing.composite_score}</span>
                   </div>
                 </Section>

                 <Separator />

                 <Section title="Hardware">
                   <SpecRow label="CPU" value={listing.cpu?.name} />
                   <SpecRow label="RAM" value={listing.ram_gb ? `${listing.ram_gb} GB` : null} />
                   <SpecRow label="Storage" value={listing.primary_storage_gb ? `${listing.primary_storage_gb} GB ${listing.primary_storage_type}` : null} />
                   {listing.ports_profile && (
                     <PortsDisplay ports={listing.ports_profile.ports} />
                   )}
                 </Section>

                 <Separator />

                 <Section title="Metadata">
                   <SpecRow label="Condition" value={listing.condition} />
                   <SpecRow label="Status" value={listing.status} />
                   <SpecRow label="Manufacturer" value={listing.manufacturer} />
                   <SpecRow label="Form Factor" value={listing.form_factor} />
                 </Section>
               </div>

               <div className="flex gap-2 mt-6">
                 <Button asChild className="flex-1">
                   <Link href={`/listings?highlight=${listing.id}`}>
                     View Full Listing
                   </Link>
                 </Button>
                 {listing.valuation_breakdown && (
                   <Button variant="outline" className="flex-1">
                     View Valuation Breakdown
                   </Button>
                 )}
               </div>
             </>
           ) : (
             <div>Listing not found</div>
           )}
         </DialogContent>
       </Dialog>
     );
   }
   ```

3. Make dashboard cards clickable:
   ```tsx
   // apps/web/components/dashboard/dashboard-summary.tsx
   const [selectedListingId, setSelectedListingId] = useState<number | null>(null);
   const [overviewOpen, setOverviewOpen] = useState(false);

   <Card
     className="cursor-pointer hover:bg-accent transition-colors"
     onClick={() => {
       setSelectedListingId(listing.id);
       setOverviewOpen(true);
     }}
   >
     {/* Existing card content */}
   </Card>

   <ListingOverviewModal
     listingId={selectedListingId}
     open={overviewOpen}
     onOpenChange={setOverviewOpen}
   />
   ```

4. Add keyboard accessibility (Enter/Space on card click)

**Files to Create:**
- `apps/web/components/listings/listing-overview-modal.tsx`

**Files to Modify:**
- `apps/web/components/dashboard/dashboard-summary.tsx` (make cards clickable, integrate modal)

**Testing:**
- Manual: Click dashboard "Best Value" card → modal opens with listing details
- Manual: Click "View Full Listing" → navigates to /listings with highlight
- Manual: ESC closes modal
- Accessibility: Tab to card → Enter opens modal
- Performance: Modal data cached for 5 minutes

**Completion Criteria:** Dashboard listings open overview modals with navigation to full listing.

---

## 7. Phase 6: Testing & Polish

**Objective:** Comprehensive testing, accessibility verification, performance optimization.

### 7.1 Integration Testing

**Test Scenarios:**

1. **CPU Intelligence Flow:**
   - Create listing with CPU → CPU Mark metrics calculate
   - Hover CPU tooltip → specs display
   - Click "View Full Details" → modal opens with all fields
   - Edit CPU → metrics recalculate

2. **Dropdown Flows:**
   - Edit RAM via dropdown → inline creation works
   - Edit Secondary Storage → dropdown matches Primary Storage
   - Dropdown widths consistent across Condition, Status, Storage fields

3. **Modal Flows:**
   - Add Entry from Data Tab → modal opens → expand → collapse → submit
   - Add Listing from /listings → same behavior
   - Dashboard listing click → overview modal → "View Full" navigation

4. **Table Flows:**
   - Resize columns → persist on refresh
   - Title column text wraps → no truncation
   - Filter by CPU → results update
   - Sort by CPU Mark → correct ordering

**Testing Checklist:**
- [ ] All bug fixes verified (CPU Mark calculations, CPU save, seed script)
- [ ] Column resizing persists across sessions
- [ ] Dropdowns auto-size correctly
- [ ] CPU tooltip displays all specs
- [ ] CPU modal shows full details
- [ ] Secondary Storage dropdown works
- [ ] Inline creation uses custom modal (no browser prompt)
- [ ] Add Entry modal expands/collapses
- [ ] Dashboard modals open and navigate correctly
- [ ] All interactions keyboard accessible
- [ ] Screen reader announces all elements correctly
- [ ] No console errors or warnings
- [ ] React Query cache working (no duplicate requests)

**Files to Create:**
- `tests/integration/test_cpu_intelligence.py` (backend integration tests)
- `apps/web/__tests__/cpu-tooltip.test.tsx` (frontend unit tests)
- `apps/web/__tests__/listing-overview-modal.test.tsx`

---

### 7.2 Accessibility Verification

**WCAG AA Checklist:**

**Keyboard Navigation:**
- [ ] All interactive elements reachable via Tab
- [ ] Modals trap focus when open
- [ ] ESC closes all modals
- [ ] Enter/Space activates buttons and triggers
- [ ] Arrow keys navigate dropdown options

**Screen Reader Support:**
- [ ] CPU Info icon: `aria-label="View CPU details"`
- [ ] Expand button: `aria-label="Expand to full screen"`
- [ ] Collapse button: `aria-label="Collapse to modal"`
- [ ] Dashboard cards: `role="button"` or semantic button
- [ ] Modals: `aria-modal="true"`, `aria-labelledby` for title
- [ ] Loading states: `aria-busy="true"`

**Color Contrast:**
- [ ] Info icon (muted-foreground): 4.5:1 minimum
- [ ] Dropdown text: 4.5:1 minimum
- [ ] Modal text: 4.5:1 minimum
- [ ] Focus indicators: 3:1 minimum

**Testing Tools:**
- Run axe DevTools on all pages
- Test with keyboard only (no mouse)
- Test with NVDA/JAWS screen reader
- Test with macOS VoiceOver

**Completion Criteria:** Zero critical accessibility violations.

---

### 7.3 Performance Optimization

**React Memoization:**
```typescript
// Memoize expensive components
export const CpuTooltip = React.memo(CpuTooltipComponent);
export const CpuDetailsModal = React.memo(CpuDetailsModalComponent);
export const ListingOverviewModal = React.memo(ListingOverviewModalComponent);
```

**React Query Optimization:**
```typescript
// Listings query with CPU data
const { data: listings } = useQuery({
  queryKey: ['listings'],
  queryFn: fetchListings,
  staleTime: 5 * 60 * 1000, // 5 minutes
  select: useCallback((data) => data.items, []), // Memoize selector
});
```

**Debouncing:**
- Column resize: 150ms (already implemented)
- Dropdown search: 200ms (already implemented)
- Verify no unnecessary debouncing on form inputs

**Bundle Size:**
- Check bundle impact: `pnpm build && pnpm analyze`
- Verify dynamic imports for modals (if bundle > 5KB increase)
- Tree-shake unused Radix components

**Performance Targets:**
- CPU tooltip render: < 100ms
- Modal open: < 200ms
- Column resize: < 150ms (debounced)
- Table initial render with 100 rows: < 2s

**Testing:**
- Use React DevTools Profiler
- Measure with Chrome Lighthouse
- Test with 100+ listings in table

**Completion Criteria:** All interactions feel instant, no janky animations.

---

## 8. Technical Details

### 8.1 Component Architecture

```
apps/web/components/
├── listings/
│   ├── cpu-tooltip.tsx           (NEW: CPU specs popover)
│   ├── cpu-details-modal.tsx     (NEW: Full CPU modal)
│   ├── listing-overview-modal.tsx (NEW: Dashboard quick view)
│   ├── add-listing-modal.tsx     (NEW: Expandable add form)
│   ├── listings-table.tsx        (MODIFIED: Integrate CPU tooltip, Secondary Storage dropdown)
│   ├── add-listing-form.tsx      (MODIFIED: Secondary Storage dropdown)
│   ├── valuation-cell.tsx        (EXISTING: Reuse in overview modal)
│   ├── dual-metric-cell.tsx      (EXISTING: Reuse in overview modal)
│   └── ports-display.tsx         (EXISTING: Reuse in overview modal)
├── forms/
│   └── combobox.tsx              (MODIFIED: Verify custom modal, no prompt())
├── ui/
│   └── data-grid.tsx             (MODIFIED: Enable column resizing)
└── dashboard/
    └── dashboard-summary.tsx     (MODIFIED: Clickable cards, overview modal)
```

### 8.2 API Response Schemas

**Listing with Full CPU:**
```json
{
  "id": 13,
  "title": "Dell OptiPlex 7090",
  "price_usd": 499.99,
  "adjusted_price_usd": 449.99,
  "cpu_id": 42,
  "cpu": {
    "id": 42,
    "name": "Intel Core i7-10700",
    "manufacturer": "Intel",
    "cpu_mark_multi": 17500,
    "cpu_mark_single": 2850,
    "igpu_model": "Intel UHD Graphics 630",
    "igpu_mark": 1200,
    "tdp_w": 65,
    "release_year": 2020,
    "cores": 8,
    "threads": 16,
    "socket": "LGA1200",
    "notes": null
  },
  "dollar_per_cpu_mark_single": 0.158,
  "dollar_per_cpu_mark_multi": 0.026,
  "secondary_storage_gb": 1024,
  "thumbnail_url": "/uploads/thumbnails/listing-13.jpg"
}
```

### 8.3 State Management Strategy

**Component-Level State:**
- Modal open/close: `useState<boolean>`
- Selected CPU for modal: `useState<CpuData | null>`
- Expanded modal state: `useState<boolean>`

**React Query Cache:**
- Listings with CPU data: 5-minute stale time
- Single listing for overview modal: 5-minute stale time
- Field options: 5-minute stale time (existing)
- Valuation thresholds: 5-minute stale time (existing)

**localStorage Persistence:**
- Column widths: `dealbrain_listings_table_state_v1:columnSizing`
- Expanded modal preference (future): `dealbrain_add_listing_expanded`

### 8.4 Error Handling Approach

**API Errors:**
```typescript
// CPU save error
try {
  await updateListing({ cpu_id: parseInt(cpuId, 10) });
} catch (error) {
  if (error instanceof ApiError && error.status === 400) {
    toast.error("Invalid CPU selection. Please try again.");
  } else {
    toast.error("Failed to save CPU. Please check your connection.");
  }
}
```

**Missing Data:**
```tsx
// CPU tooltip with null checks
{cpu?.cpu_mark_single?.toLocaleString() ?? 'N/A'}
```

**Loading States:**
```tsx
// Overview modal
{isLoading ? (
  <div className="flex items-center justify-center p-8">
    <Spinner />
    <span className="ml-2">Loading listing...</span>
  </div>
) : listing ? (
  /* Content */
) : (
  <div>Listing not found</div>
)}
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Backend Tests:**
```python
# tests/unit/test_listing_metrics.py
def test_cpu_mark_calculation():
    """Dollar per CPU Mark metrics calculated on listing create."""
    listing = create_listing(cpu=cpu_with_marks, price=450)
    assert listing.dollar_per_cpu_mark_single == 450 / cpu.cpu_mark_single
    assert listing.dollar_per_cpu_mark_multi == 450 / cpu.cpu_mark_multi

def test_cpu_id_type_coercion():
    """API accepts string cpu_id and casts to int."""
    response = client.patch("/v1/listings/13", json={"cpu_id": "42"})
    assert response.status_code == 200
    listing = response.json()
    assert listing["cpu_id"] == 42
```

**Frontend Tests:**
```tsx
// apps/web/__tests__/cpu-tooltip.test.tsx
describe('CpuTooltip', () => {
  it('renders info icon when CPU present', () => {
    render(<CpuTooltip cpu={mockCpu} onViewDetails={jest.fn()} />);
    expect(screen.getByLabelText('View CPU details')).toBeInTheDocument();
  });

  it('displays CPU specs on hover', async () => {
    render(<CpuTooltip cpu={mockCpu} onViewDetails={jest.fn()} />);
    await userEvent.hover(screen.getByLabelText('View CPU details'));
    expect(await screen.findByText('Intel Core i7-10700')).toBeInTheDocument();
    expect(screen.getByText('2850')).toBeInTheDocument(); // Single-thread
  });

  it('calls onViewDetails when button clicked', async () => {
    const onViewDetails = jest.fn();
    render(<CpuTooltip cpu={mockCpu} onViewDetails={onViewDetails} />);
    await userEvent.click(screen.getByText('View Full CPU Details'));
    expect(onViewDetails).toHaveBeenCalled();
  });
});
```

### 9.2 Manual Testing Checklist

**Pre-Deployment Validation:**

- [ ] **Bug Fixes:**
  - [ ] All listings with CPU + price show CPU Mark metrics
  - [ ] CPU selection saves without type error
  - [ ] Seed script runs successfully

- [ ] **Table Features:**
  - [ ] Column resizing works on all columns
  - [ ] Column widths persist after page refresh
  - [ ] Title column wraps text when narrow
  - [ ] Dropdown fields auto-size to content

- [ ] **CPU Intelligence:**
  - [ ] CPU tooltip shows on hover
  - [ ] Tooltip displays all 6 spec fields
  - [ ] "View Full Details" opens modal
  - [ ] Modal shows complete CPU data
  - [ ] Modal closes on ESC

- [ ] **Dropdowns:**
  - [ ] Secondary Storage uses dropdown
  - [ ] Inline creation uses custom modal (not browser prompt)
  - [ ] New options appear immediately after creation

- [ ] **Modals:**
  - [ ] Add Entry modal opens from Data Tab
  - [ ] Add Listing modal opens from /listings
  - [ ] Expand/collapse transitions smooth
  - [ ] Form data persists during expand/collapse
  - [ ] Dashboard cards open overview modal
  - [ ] "View Full Listing" navigates correctly

- [ ] **Accessibility:**
  - [ ] All interactions keyboard accessible
  - [ ] Focus indicators visible
  - [ ] Screen reader announces all elements
  - [ ] No color-only indicators

- [ ] **Performance:**
  - [ ] Table renders 100 rows in < 2s
  - [ ] Modals open in < 200ms
  - [ ] No console errors or warnings
  - [ ] React Query cache prevents duplicate requests

### 9.3 Accessibility Testing Checklist

**Keyboard Navigation:**
- [ ] Tab through all interactive elements in order
- [ ] Enter/Space activates buttons
- [ ] ESC closes modals
- [ ] Arrow keys navigate dropdowns
- [ ] Focus trapped in open modals
- [ ] Focus returns to trigger after modal close

**Screen Reader:**
- [ ] NVDA/JAWS announces all labels
- [ ] Modal titles announced on open
- [ ] Loading states announced
- [ ] Error messages announced

**Visual:**
- [ ] Focus indicators meet 3:1 contrast
- [ ] Text meets 4.5:1 contrast
- [ ] No flashing content > 3Hz
- [ ] Works at 200% zoom

---

## 10. Rollout Plan

### 10.1 Git Commit Strategy

**Phase-Based Commits:**

```bash
# Phase 1: Bug Fixes
git add apps/api/dealbrain_api/services/listings.py scripts/recalculate_cpu_marks.py
git commit -m "fix: Calculate CPU Mark metrics on listing create/update

- Add dollar_per_cpu_mark_single and dollar_per_cpu_mark_multi calculations
- Trigger recalculation on price or CPU updates
- Include bulk recalculation script for existing listings

Fixes calculation bug causing empty metric fields"

git add apps/web/components/listings/listings-table.tsx apps/api/dealbrain_api/schemas/listings.py
git commit -m "fix: Coerce cpu_id to integer on save

- Add Pydantic field validator for cpu_id type coercion
- Update frontend to send cpu_id as number
- Prevents 'str object cannot be interpreted as integer' error

Fixes CPU save type error"

git add scripts/seed_sample_listings.py
git commit -m "fix: Correct Port model field name in seed script

- Use ports_profile_id instead of port_profile_id
- Match field names to Port model definition
- Seed script now runs successfully

Fixes Port creation error in seed_sample_listings.py"

# Phase 2: Table Foundation
git add apps/web/components/ui/data-grid.tsx apps/web/components/listings/listings-table.tsx
git commit -m "feat: Restore column resizing with persistence

- Enable column resizing in DataGrid component
- Add visual resize handles with hover states
- Persist column widths to localStorage
- Enforce minimum widths per column type

Implements table UX improvements"

git add apps/web/lib/dropdown-utils.ts apps/web/components/forms/combobox.tsx
git commit -m "feat: Auto-size dropdowns to content width

- Calculate dropdown width based on longest option
- Apply minimum and maximum width constraints
- Update all dropdown fields for consistency

Fixes narrow dropdown visibility issues"

# Phase 3: CPU Intelligence
git add apps/web/components/listings/cpu-tooltip.tsx apps/web/components/listings/cpu-details-modal.tsx apps/web/components/listings/listings-table.tsx
git commit -m "feat: Add CPU tooltip and details modal

- Create CpuTooltip component with key specs
- Create CpuDetailsModal with full CPU data
- Integrate into listings table CPU column
- Add React.memo for performance

Implements CPU intelligence features"

# Phase 4: Enhanced Dropdowns
git add apps/web/components/listings/listings-table.tsx apps/web/components/listings/add-listing-form.tsx
git commit -m "feat: Convert Secondary Storage to dropdown

- Add Secondary Storage to dropdown field configs
- Match Primary Storage dropdown pattern
- Support inline option creation

Implements Secondary Storage dropdown enhancement"

# Phase 5: Modal Navigation
git add apps/web/components/listings/add-listing-modal.tsx apps/web/app/data/page.tsx apps/web/app/listings/page.tsx
git commit -m "feat: Add expandable Add Listing modal

- Create AddListingModal with expand/collapse
- Integrate with Data Tab and /listings page
- Preserve form state during expand/collapse
- Add smooth transitions

Implements expandable modal pattern"

git add apps/web/components/listings/listing-overview-modal.tsx apps/web/components/dashboard/dashboard-summary.tsx
git commit -m "feat: Add dashboard listing overview modals

- Create ListingOverviewModal with quick details
- Make dashboard cards clickable
- Add 'View Full Listing' navigation
- Reuse existing components (ValuationCell, DualMetricCell)

Implements dashboard interactivity"

# Phase 6: Testing & Polish
git add tests/ apps/web/__tests__/
git commit -m "test: Add comprehensive test coverage for UX enhancements

- Unit tests for CPU tooltip and modals
- Integration tests for bug fixes
- Accessibility verification
- Performance optimization

Completes testing phase"

git add apps/web/components/
git commit -m "perf: Optimize component rendering with memoization

- Memoize CpuTooltip, CpuDetailsModal, ListingOverviewModal
- Add React Query cache optimizations
- Verify debouncing on interactions

Completes performance optimization"
```

### 10.2 Validation Checkpoints

**After Phase 1 (Bug Fixes):**
- [ ] Run full test suite: `make test`
- [ ] Verify all listings show CPU Mark metrics
- [ ] Test CPU save in UI (no errors)
- [ ] Run seed script successfully
- [ ] Deploy to staging for QA validation

**After Phase 2 (Table Foundation):**
- [ ] Test column resizing on all tables
- [ ] Verify localStorage persistence works
- [ ] Test dropdown width on all fields
- [ ] Verify no layout regressions

**After Phase 3 (CPU Intelligence):**
- [ ] Test CPU tooltip on 10+ listings
- [ ] Verify CPU modal shows all fields
- [ ] Check React Query cache (no duplicate requests)
- [ ] Accessibility audit with axe DevTools

**After Phase 4 (Enhanced Dropdowns):**
- [ ] Test Secondary Storage dropdown
- [ ] Verify inline creation uses custom modal
- [ ] Test all dropdown fields for consistency

**After Phase 5 (Modal Navigation):**
- [ ] Test Add Entry modal from both locations
- [ ] Verify expand/collapse transitions
- [ ] Test dashboard modal navigation
- [ ] Full keyboard navigation test

**After Phase 6 (Testing & Polish):**
- [ ] Run full test suite (unit + integration)
- [ ] Accessibility audit (WCAG AA)
- [ ] Performance audit (Lighthouse)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Final QA sign-off

**Pre-Production Deployment:**
- [ ] Staging deployment successful
- [ ] Database migration tested (if any)
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Release notes prepared

---

## 11. Subagent Delegation Points

**When to Delegate:**

### 11.1 Backend Bug Fixes (Phase 1)
**Delegate to:** `backend-typescript-architect` or `debugger`
- Complex SQL query optimization
- Database migration issues
- Service layer refactoring

**Coordination:**
```
@backend-typescript-architect
Task: Investigate and fix CPU Mark calculation bug
Context: /apps/api/dealbrain_api/services/listings.py line 39-135
Requirements:
- Add dollar_per_cpu_mark_single and dollar_per_cpu_mark_multi calculations
- Trigger on listing create/update
- Handle null CPU/price gracefully
Expected Output: Updated service with calculations, unit tests
```

### 11.2 Frontend Component Creation (Phase 3-5)
**Delegate to:** `ui-engineer` or `frontend-architect`
- Complex component state management
- Advanced animation implementations
- React Query optimization

**Coordination:**
```
@ui-engineer
Task: Create CpuTooltip and CpuDetailsModal components
Context: Follow DeltaBadge pattern from ui-enhancements-context.md
Requirements:
- CpuTooltip: Popover with 6 spec fields
- CpuDetailsModal: Full CPU details in sections
- React.memo for performance
- WCAG AA compliant
Expected Output: 2 components, integration code, accessibility verified
```

### 11.3 Testing & QA (Phase 6)
**Delegate to:** `senior-code-reviewer` or `debugger`
- Comprehensive test suite creation
- Performance profiling
- Accessibility audit

**Coordination:**
```
@senior-code-reviewer
Task: Create test suite for CPU intelligence features
Context: CpuTooltip and CpuDetailsModal components
Requirements:
- Unit tests for tooltip interactions
- Integration tests for modal flow
- Accessibility tests (keyboard, screen reader)
- Performance tests (render time < 100ms)
Expected Output: Test files, coverage report, accessibility audit results
```

---

## 12. Key Patterns from Codebase

### 12.1 Modal Pattern (Existing)
```tsx
// From ui-enhancements-context.md Phase 1
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";

export function ExampleModal({ open, onOpenChange }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Title</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Content */}
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

### 12.2 ComboBox with Inline Creation (Existing)
```tsx
// From ui-enhancements-context.md Phase 2
<ComboBox
  options={RAM_OPTIONS}
  value={value}
  onChange={onChange}
  placeholder="Select RAM..."
  enableInlineCreate
  fieldId={fieldId}
  fieldName="RAM (GB)"
/>
```

### 12.3 React Query Pattern (Existing)
```tsx
// From ui-enhancements-context.md Phase 1
const { data, isLoading } = useQuery({
  queryKey: ['listings'],
  queryFn: async () => {
    const response = await apiFetch('/v1/listings');
    return response.json();
  },
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

### 12.4 Memoization Pattern (Existing)
```tsx
// From ui-enhancements-context.md Phase 5
import React from 'react';

const ValuationCellComponent = ({ basePrice, adjustedPrice }: Props) => {
  // Component logic
};

export const ValuationCell = React.memo(ValuationCellComponent);
```

---

## 13. Success Criteria Summary

**Phase 1 Complete:**
- [ ] All CPU Mark metrics calculate correctly
- [ ] CPU saves without type errors
- [ ] Seed script executes successfully

**Phase 2 Complete:**
- [ ] All columns resizable with persistence
- [ ] Dropdowns auto-size to content width

**Phase 3 Complete:**
- [ ] CPU tooltip displays on hover
- [ ] CPU modal shows full specifications

**Phase 4 Complete:**
- [ ] Secondary Storage uses dropdown
- [ ] Inline creation uses custom modal

**Phase 5 Complete:**
- [ ] Add Entry modal expands/collapses
- [ ] Dashboard listings open overview modals

**Phase 6 Complete:**
- [ ] All tests passing (unit + integration)
- [ ] Zero accessibility violations (axe audit)
- [ ] Performance targets met (< 100ms interactions)

**Overall Success:**
- [ ] All features from PRD implemented
- [ ] No regressions in existing functionality
- [ ] Documentation updated (CLAUDE.md)
- [ ] Stakeholder sign-off received

---

## 14. Appendix: File Manifest

### New Files Created
1. `apps/web/components/listings/cpu-tooltip.tsx`
2. `apps/web/components/listings/cpu-details-modal.tsx`
3. `apps/web/components/listings/listing-overview-modal.tsx`
4. `apps/web/components/listings/add-listing-modal.tsx`
5. `apps/web/lib/dropdown-utils.ts`
6. `scripts/recalculate_cpu_marks.py`
7. `tests/unit/test_cpu_mark_calculations.py`
8. `tests/integration/test_cpu_intelligence.py`
9. `apps/web/__tests__/cpu-tooltip.test.tsx`
10. `apps/web/__tests__/listing-overview-modal.test.tsx`

### Modified Files
1. `apps/api/dealbrain_api/services/listings.py`
2. `apps/api/dealbrain_api/schemas/listings.py`
3. `apps/web/components/listings/listings-table.tsx`
4. `apps/web/components/listings/add-listing-form.tsx`
5. `apps/web/components/forms/combobox.tsx`
6. `apps/web/components/ui/data-grid.tsx`
7. `apps/web/components/dashboard/dashboard-summary.tsx`
8. `apps/web/app/data/page.tsx` (if exists)
9. `apps/web/app/listings/page.tsx`
10. `scripts/seed_sample_listings.py`
11. `CLAUDE.md` (documentation update)

### Estimated Lines of Code
- **New Components:** ~800 lines
- **Modified Components:** ~300 lines
- **Backend Changes:** ~150 lines
- **Tests:** ~400 lines
- **Scripts:** ~100 lines
- **Total:** ~1,750 lines

---

**End of Implementation Plan**

**Next Steps:**
1. Review plan with team for feedback
2. Assign phases to sprints or agents
3. Begin Phase 1 (Bug Fixes) immediately
4. Create tracking document for progress

**Questions/Clarifications:**
- Data Tab location confirmed? (assumed /data page exists)
- Dashboard component location confirmed? (assumed dashboard-summary.tsx)
- Feature flags desired for gradual rollout?
- Deployment schedule constraints?
