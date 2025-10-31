# TASK-006 Implementation Specification

**Status:** Ready for Implementation
**Assigned To:** Frontend Developer
**Estimated Effort:** L (1-2 days)
**Started:** 2025-10-26

---

## Objective

Reorganize the Specifications tab (`apps/web/components/listings/specifications-tab.tsx`) into logical subsections (Compute, Memory, Storage, Connectivity) with empty state handling.

---

## Current Implementation Analysis

**File:** `/mnt/containers/deal-brain/apps/web/components/listings/specifications-tab.tsx`
**Lines:** 406 total
**Current Structure:**
- Hardware Section (lines 41-187) - needs reorganization
- Product Details Section (lines 189-204) - preserve as-is
- Listing Info Section (lines 206-261) - preserve as-is
- Performance Metrics Section (lines 263-306) - preserve as-is
- Metadata Section (lines 308-320) - preserve as-is
- Custom Fields Section (lines 322-340) - preserve as-is

---

## Implementation Requirements

### 1. Create SpecificationSubsection Component

Add this reusable component within the file (after imports, before SpecificationsTab):

```tsx
/**
 * Reusable subsection component for specifications
 */
interface SpecificationSubsectionProps {
  title: string;
  children: React.ReactNode;
  isEmpty?: boolean;
  onAddClick?: () => void;
}

function SpecificationSubsection({
  title,
  children,
  isEmpty,
  onAddClick
}: SpecificationSubsectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center justify-between">
          {title}
          {isEmpty && onAddClick && (
            <Button variant="ghost" size="sm" onClick={onAddClick}>
              Add +
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <p className="text-sm text-muted-foreground">No data available</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {children}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### 2. Add Button Import

Update the imports section to include Button:

```tsx
import { Button } from "@/components/ui/button";
```

### 3. Replace Hardware Section

Replace lines 40-187 (the entire Hardware section) with these 4 subsections:

```tsx
{/* Compute Subsection */}
<SpecificationSubsection
  title="Compute"
  isEmpty={!listing.cpu && !listing.cpu_name && !listing.gpu}
  onAddClick={() => console.log('Add compute data')}
>
  {/* CPU */}
  {(listing.cpu || listing.cpu_name) && (
    <FieldGroup label="CPU">
      {listing.cpu && listing.cpu.id ? (
        <EntityTooltip
          entityType="cpu"
          entityId={listing.cpu.id}
          tooltipContent={(cpu) => <CpuTooltipContent cpu={cpu} />}
          fetchData={fetchEntityData}
          variant="inline"
        >
          {listing.cpu.model || listing.cpu_name || "—"}
        </EntityTooltip>
      ) : (
        <span>{listing.cpu_name || "—"}</span>
      )}
    </FieldGroup>
  )}

  {/* GPU */}
  {listing.gpu && listing.gpu.id && (
    <FieldGroup label="GPU">
      <EntityTooltip
        entityType="gpu"
        entityId={listing.gpu.id}
        tooltipContent={(gpu) => <GpuTooltipContent gpu={gpu} />}
        fetchData={fetchEntityData}
        variant="inline"
      >
        {listing.gpu.model || listing.gpu.name || listing.gpu_name || "—"}
      </EntityTooltip>
    </FieldGroup>
  )}

  {/* Performance Scores */}
  {listing.score_cpu_multi !== null && (
    <FieldGroup label="CPU Multi-Thread Score" value={listing.score_cpu_multi.toFixed(1)} />
  )}
  {listing.score_cpu_single !== null && (
    <FieldGroup label="CPU Single-Thread Score" value={listing.score_cpu_single.toFixed(1)} />
  )}
  {listing.score_gpu !== null && (
    <FieldGroup label="GPU Score" value={listing.score_gpu.toFixed(1)} />
  )}

  {/* Performance Metrics */}
  {listing.dollar_per_cpu_mark !== null && (
    <FieldGroup
      label="$/CPU Mark (Multi)"
      value={`$${listing.dollar_per_cpu_mark.toFixed(3)}`}
    />
  )}
  {listing.dollar_per_cpu_mark_single !== null &&
    listing.dollar_per_cpu_mark_single !== undefined && (
      <FieldGroup
        label="$/CPU Mark (Single)"
        value={`$${listing.dollar_per_cpu_mark_single.toFixed(3)}`}
      />
    )}
  {listing.perf_per_watt !== null && listing.perf_per_watt !== undefined && (
    <FieldGroup label="Performance/Watt" value={listing.perf_per_watt.toFixed(2)} />
  )}
</SpecificationSubsection>

{/* Memory Subsection */}
<SpecificationSubsection
  title="Memory"
  isEmpty={!listing.ram_gb && !listing.ram_type}
  onAddClick={() => console.log('Add memory data')}
>
  <FieldGroup label="RAM">
    {listing.ram_spec && listing.ram_spec_id ? (
      <EntityTooltip
        entityType="ram-spec"
        entityId={listing.ram_spec_id}
        tooltipContent={(ram) => <RamSpecTooltipContent ramSpec={ram} />}
        fetchData={fetchEntityData}
        variant="inline"
      >
        {listing.ram_gb ? `${listing.ram_gb} GB` : "—"}
        {listing.ram_type && ` ${listing.ram_type}`}
        {listing.ram_speed_mhz && ` @ ${listing.ram_speed_mhz} MHz`}
      </EntityTooltip>
    ) : (
      <span>
        {listing.ram_gb ? `${listing.ram_gb} GB` : "—"}
        {listing.ram_type && ` ${listing.ram_type}`}
        {listing.ram_speed_mhz && ` @ ${listing.ram_speed_mhz} MHz`}
      </span>
    )}
  </FieldGroup>
</SpecificationSubsection>

{/* Storage Subsection */}
<SpecificationSubsection
  title="Storage"
  isEmpty={!listing.primary_storage_gb && !listing.secondary_storage_gb}
  onAddClick={() => console.log('Add storage data')}
>
  {/* Primary Storage */}
  {listing.primary_storage_gb && (
    <FieldGroup label="Primary Storage">
      {listing.primary_storage_profile && listing.primary_storage_profile_id ? (
        <EntityTooltip
          entityType="storage-profile"
          entityId={listing.primary_storage_profile_id}
          tooltipContent={(storage) => <StorageProfileTooltipContent storageProfile={storage} />}
          fetchData={fetchEntityData}
          variant="inline"
        >
          {listing.primary_storage_gb} GB
          {listing.primary_storage_type && ` ${listing.primary_storage_type}`}
        </EntityTooltip>
      ) : (
        <span>
          {listing.primary_storage_gb} GB
          {listing.primary_storage_type && ` ${listing.primary_storage_type}`}
        </span>
      )}
    </FieldGroup>
  )}

  {/* Secondary Storage */}
  {listing.secondary_storage_gb && (
    <FieldGroup label="Secondary Storage">
      {listing.secondary_storage_profile && listing.secondary_storage_profile_id ? (
        <EntityTooltip
          entityType="storage-profile"
          entityId={listing.secondary_storage_profile_id}
          tooltipContent={(storage) => <StorageProfileTooltipContent storageProfile={storage} />}
          fetchData={fetchEntityData}
          variant="inline"
        >
          {listing.secondary_storage_gb} GB
          {listing.secondary_storage_type && ` ${listing.secondary_storage_type}`}
        </EntityTooltip>
      ) : (
        <span>
          {listing.secondary_storage_gb} GB
          {listing.secondary_storage_type && ` ${listing.secondary_storage_type}`}
        </span>
      )}
    </FieldGroup>
  )}
</SpecificationSubsection>

{/* Connectivity Subsection */}
<SpecificationSubsection
  title="Connectivity"
  isEmpty={!listing.ports_profile}
  onAddClick={() => console.log('Add connectivity data')}
>
  {listing.ports_profile && (
    <FieldGroup label="Ports">
      <div className="flex flex-wrap gap-1">
        {listing.ports_profile.usb_a_count !== undefined &&
          listing.ports_profile.usb_a_count !== null &&
          listing.ports_profile.usb_a_count > 0 && (
            <Badge variant="secondary" className="text-xs">
              USB-A ×{listing.ports_profile.usb_a_count}
            </Badge>
          )}
        {listing.ports_profile.usb_c_count !== undefined &&
          listing.ports_profile.usb_c_count !== null &&
          listing.ports_profile.usb_c_count > 0 && (
            <Badge variant="secondary" className="text-xs">
              USB-C ×{listing.ports_profile.usb_c_count}
            </Badge>
          )}
        {listing.ports_profile.hdmi_count !== undefined &&
          listing.ports_profile.hdmi_count !== null &&
          listing.ports_profile.hdmi_count > 0 && (
            <Badge variant="secondary" className="text-xs">
              HDMI ×{listing.ports_profile.hdmi_count}
            </Badge>
          )}
        {listing.ports_profile.displayport_count !== undefined &&
          listing.ports_profile.displayport_count !== null &&
          listing.ports_profile.displayport_count > 0 && (
            <Badge variant="secondary" className="text-xs">
              DisplayPort ×{listing.ports_profile.displayport_count}
            </Badge>
          )}
      </div>
    </FieldGroup>
  )}
</SpecificationSubsection>
```

### 4. Remove Performance Metrics Section

Remove the standalone "Performance Metrics" section (lines 263-306) since those metrics are now in the Compute subsection.

---

## Testing Checklist

After implementation, verify:

- [ ] TypeScript compiles without errors: `pnpm --filter "./apps/web" typecheck`
- [ ] Four subsections render correctly (Compute, Memory, Storage, Connectivity)
- [ ] Empty subsections show "No data available" message
- [ ] "Add +" button appears for empty subsections
- [ ] Non-empty subsections display data correctly
- [ ] EntityTooltips still work for CPU, GPU, RAM, Storage
- [ ] Grid layout is responsive (1 col mobile, 2 col tablet, 3 col desktop)
- [ ] Spacing and visual hierarchy are correct
- [ ] No console errors or warnings
- [ ] Accessibility maintained (keyboard navigation, screen readers)

---

## Deal Brain Patterns to Follow

- **Component Pattern:** shadcn/ui components (Card, CardHeader, CardTitle, CardContent, Button, Badge)
- **TypeScript:** Strict mode, no `any` types
- **Responsive Design:** Tailwind CSS with mobile-first breakpoints
- **Accessibility:** WCAG 2.1 AA compliance
- **Entity Pattern:** Preserve all EntityTooltip integrations exactly as-is

---

## Expected Outcome

The Specifications tab will have better organization with clear subsections:
- Easier to scan and understand listing specifications
- Clear visual hierarchy with subsection titles
- Empty states with affordances for adding data
- All existing functionality preserved (tooltips, links, badges)

---

## Notes for Implementation

1. **Preserve Existing Code:** Keep all other sections (Product Details, Listing Info, Metadata, Custom Fields) unchanged
2. **Move Performance Metrics:** Move performance metrics from standalone section into Compute subsection
3. **Empty State Logic:** Use conditional checks for isEmpty prop
4. **Placeholder Handlers:** Use `console.log` for onAddClick handlers (will be replaced in TASK-007)
5. **Component Placement:** Add SpecificationSubsection component definition after imports, before SpecificationsTab export

---

## Related Tasks

- **TASK-007:** Create Quick-Add Dialogs (depends on this task)
- **TASK-008:** Optimize Detail Page Layout (independent)
- **TASK-009:** Phase 2 Testing & Integration (depends on all tasks)
