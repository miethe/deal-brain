# Phase 2: UX Improvements (Week 2)

## Implementation Plan

### Overview
Enhance user experience with scrollable dropdowns and improved field selection.

### Task List

#### P2-UX-001: Implement Scrollable Dropdown for Field Selection
**Priority**: High
**Time Estimate**: 6 hours
**Dependencies**: None

**Description**:
The Condition builder dropdown extends beyond viewport when list is long. Implement virtual scrolling.

**Acceptance Criteria**:
- [ ] Dropdown constrained to viewport height
- [ ] Smooth scrolling with 200+ items
- [ ] Keyboard navigation works
- [ ] Search/filter functionality
- [ ] Selected item remains visible
- [ ] Mobile responsive

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/web/components/valuation/entity-field-selector.tsx`
- `/mnt/containers/deal-brain/apps/web/components/ui/command.tsx`
- `/mnt/containers/deal-brain/apps/web/components/valuation/condition-group.tsx`

**Implementation Notes**:
```typescript
// New ScrollableFieldSelector component
import { useVirtualizer } from '@tanstack/react-virtual';

export function ScrollableFieldSelector({
  fields,
  onSelect,
  maxHeight = 400
}: Props) {
  const parentRef = useRef<HTMLDivElement>(null);
  const [search, setSearch] = useState('');

  const filteredFields = useMemo(() =>
    fields.filter(f =>
      f.label.toLowerCase().includes(search.toLowerCase())
    ),
    [fields, search]
  );

  const virtualizer = useVirtualizer({
    count: filteredFields.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 35,
    overscan: 5
  });

  return (
    <Command className="border rounded-lg">
      <CommandInput
        placeholder="Search fields..."
        value={search}
        onValueChange={setSearch}
      />
      <CommandList
        ref={parentRef}
        className="max-h-[400px] overflow-y-auto"
      >
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative'
          }}
        >
          {virtualizer.getVirtualItems().map((virtualItem) => {
            const field = filteredFields[virtualItem.index];
            return (
              <CommandItem
                key={field.name}
                value={field.name}
                onSelect={() => onSelect(field)}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualItem.size}px`,
                  transform: `translateY(${virtualItem.start}px)`
                }}
              >
                <div className="flex items-center justify-between w-full">
                  <span>{field.label}</span>
                  <Badge variant="outline" className="ml-2">
                    {field.type}
                  </Badge>
                </div>
              </CommandItem>
            );
          })}
        </div>
      </CommandList>
    </Command>
  );
}
```

**Testing Requirements**:
- [ ] Performance test with 500+ items
- [ ] Keyboard navigation test
- [ ] Mobile viewport test
- [ ] Accessibility audit (WCAG AA)

---

#### P2-UX-002: Add Field Value Autocomplete
**Priority**: Medium
**Time Estimate**: 5 hours
**Dependencies**: P2-UX-001

**Description**:
When selecting field values in conditions, provide autocomplete from existing values.

**Acceptance Criteria**:
- [ ] Fetch existing values for selected field
- [ ] Show autocomplete suggestions
- [ ] Allow free text input
- [ ] Cache field values for performance
- [ ] Handle enum fields specially

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/web/components/valuation/value-input.tsx`
- `/mnt/containers/deal-brain/apps/web/hooks/useFieldValues.ts` (new)
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/endpoints/fields.py`

**Implementation Notes**:
```typescript
// New hook for field values
export function useFieldValues(fieldName: string) {
  return useQuery({
    queryKey: ['fieldValues', fieldName],
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/api/v1/fields/${fieldName}/values`
      );
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    enabled: !!fieldName
  });
}

// Enhanced ValueInput component
export function ValueInput({
  field,
  value,
  onChange
}: ValueInputProps) {
  const { data: fieldValues } = useFieldValues(field.name);
  const [isOpen, setIsOpen] = useState(false);

  if (field.type === 'enum' && fieldValues?.length > 0) {
    return (
      <Combobox
        options={fieldValues}
        value={value}
        onValueChange={onChange}
        placeholder="Select or type value..."
        allowCustomValue
      />
    );
  }

  // Fallback to appropriate input type
  return <Input ... />;
}
```

**Testing Requirements**:
- [ ] Test with enum fields
- [ ] Test with text fields
- [ ] Test with numeric fields
- [ ] Performance test with many values
- [ ] Test custom value entry