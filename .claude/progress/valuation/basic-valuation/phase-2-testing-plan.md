# Phase 2: UX Improvements - Testing Plan

**Date Created**: 2025-10-15
**Phase**: UX Improvements (Week 2)
**Version**: 1.0

## Overview

Phase 2 implemented two major UX improvements to the Valuation Rules system:

1. **P2-UX-001**: Scrollable dropdown with virtual scrolling for field selection
2. **P2-UX-002**: Field value autocomplete system with server-side data fetching

This testing plan provides comprehensive coverage for unit tests, integration tests, manual testing, accessibility validation, and performance benchmarks.

## Testing Strategy

### Test Pyramid
- **Unit Tests (Base)**: Component logic, hooks, utilities
- **Integration Tests (Middle)**: API endpoints, data flows, caching
- **Manual Tests (Top)**: User workflows, cross-browser, accessibility
- **Performance Tests (Cross-cutting)**: Rendering, scrolling, API response times

### Coverage Goals
- Unit tests: 70% coverage minimum
- Integration tests: All critical paths covered
- Manual tests: 100% acceptance criteria verified
- Accessibility: WCAG 2.1 AA compliance
- Performance: All targets met (documented below)

## Unit Tests

### VirtualizedCommandList Component
**File**: `apps/web/components/ui/virtualized-command-list.tsx`

#### Test Cases

**Test: Renders only visible items**
```typescript
test('renders only visible items in viewport', () => {
  const items = Array.from({ length: 500 }, (_, i) => ({ id: i, label: `Item ${i}` }));
  render(<VirtualizedCommandList items={items} renderItem={(item) => <div>{item.label}</div>} />);

  // Should render ~10-15 items (overscan=5), not all 500
  expect(screen.queryAllByText(/Item \d+/).length).toBeLessThan(30);
});
```

**Test: Handles scrolling correctly**
```typescript
test('updates visible items on scroll', async () => {
  const items = Array.from({ length: 100 }, (_, i) => ({ id: i, label: `Item ${i}` }));
  const { container } = render(
    <VirtualizedCommandList items={items} renderItem={(item) => <div>{item.label}</div>} />
  );

  const scrollContainer = container.firstChild as HTMLElement;
  fireEvent.scroll(scrollContainer, { target: { scrollTop: 500 } });

  await waitFor(() => {
    // Should show items further down the list
    expect(screen.queryByText('Item 0')).not.toBeInTheDocument();
    expect(screen.queryByText('Item 20')).toBeInTheDocument();
  });
});
```

**Test: Updates virtualizer on items change**
```typescript
test('updates when items array changes', () => {
  const { rerender } = render(
    <VirtualizedCommandList items={[{ id: 1, label: 'Item 1' }]} renderItem={(item) => <div>{item.label}</div>} />
  );

  expect(screen.getByText('Item 1')).toBeInTheDocument();

  rerender(
    <VirtualizedCommandList items={[{ id: 2, label: 'Item 2' }]} renderItem={(item) => <div>{item.label}</div>} />
  );

  expect(screen.queryByText('Item 1')).not.toBeInTheDocument();
  expect(screen.getByText('Item 2')).toBeInTheDocument();
});
```

**Test: Handles empty items array**
```typescript
test('handles empty items array gracefully', () => {
  const { container } = render(
    <VirtualizedCommandList items={[]} renderItem={(item) => <div>{item}</div>} />
  );

  expect(container.firstChild).toBeInTheDocument();
  expect(container.firstChild).toBeEmptyDOMElement();
});
```

### EntityFieldSelector Component
**File**: `apps/web/components/valuation/entity-field-selector.tsx`

#### Test Cases

**Test: Debounces search input (200ms)**
```typescript
jest.useFakeTimers();

test('debounces search input by 200ms', () => {
  const mockOnChange = jest.fn();
  render(<EntityFieldSelector value={null} onChange={mockOnChange} />);

  const searchInput = screen.getByPlaceholderText('Search fields...');

  // Type quickly
  fireEvent.change(searchInput, { target: { value: 'p' } });
  fireEvent.change(searchInput, { target: { value: 'pr' } });
  fireEvent.change(searchInput, { target: { value: 'pri' } });

  // Should not filter immediately
  expect(screen.queryByText('No fields found.')).not.toBeInTheDocument();

  // Fast-forward 200ms
  act(() => jest.advanceTimersByTime(200));

  // Now should filter
  expect(screen.queryAllByRole('option').length).toBeLessThan(100);
});
```

**Test: Memoizes allFields calculation**
```typescript
test('memoizes allFields to prevent recalculation', () => {
  const mockMetadata = {
    entities: [
      { key: 'listing', label: 'Listing', fields: [{ key: 'price_usd', label: 'Price', data_type: 'number' }] }
    ]
  };

  const { rerender } = render(<EntityFieldSelector value={null} onChange={jest.fn()} />);

  // Trigger re-render with same props
  rerender(<EntityFieldSelector value={null} onChange={jest.fn()} />);

  // allFields should only compute once (verify with React DevTools Profiler in real test)
  expect(screen.getByText(/Select field/)).toBeInTheDocument();
});
```

**Test: Virtual scrolling with 200+ items**
```typescript
test('uses virtual scrolling for large field lists', () => {
  // Mock 200+ fields
  const mockMetadata = {
    entities: Array.from({ length: 50 }, (_, i) => ({
      key: `entity${i}`,
      label: `Entity ${i}`,
      fields: Array.from({ length: 5 }, (_, j) => ({
        key: `field${j}`,
        label: `Field ${j}`,
        data_type: 'string'
      }))
    }))
  };

  render(<EntityFieldSelector value={null} onChange={jest.fn()} />);

  const button = screen.getByRole('combobox');
  fireEvent.click(button);

  // Should render < 30 DOM nodes despite 250 total fields
  const renderedItems = screen.queryAllByRole('option');
  expect(renderedItems.length).toBeLessThan(30);
});
```

**Test: Keyboard navigation**
```typescript
test('supports arrow key navigation', async () => {
  render(<EntityFieldSelector value={null} onChange={jest.fn()} />);

  const button = screen.getByRole('combobox');
  fireEvent.click(button);

  const firstItem = screen.getAllByRole('option')[0];

  // Arrow down
  fireEvent.keyDown(button, { key: 'ArrowDown' });
  await waitFor(() => expect(firstItem).toHaveFocus());

  // Enter selects
  fireEvent.keyDown(firstItem, { key: 'Enter' });
  expect(button).toHaveAttribute('aria-expanded', 'false');

  // Escape closes
  fireEvent.click(button);
  fireEvent.keyDown(button, { key: 'Escape' });
  expect(button).toHaveAttribute('aria-expanded', 'false');
});
```

**Test: Selected field shows check icon**
```typescript
test('displays check icon for selected field', () => {
  render(<EntityFieldSelector value="listing.price_usd" onChange={jest.fn()} />);

  const button = screen.getByRole('combobox');
  fireEvent.click(button);

  const selectedItem = screen.getByText(/Price/);
  expect(within(selectedItem).getByTestId('check-icon')).toBeInTheDocument();
});
```

**Test: Result count announced for screen readers**
```typescript
test('announces result count with aria-live', () => {
  render(<EntityFieldSelector value={null} onChange={jest.fn()} />);

  const button = screen.getByRole('combobox');
  fireEvent.click(button);

  const searchInput = screen.getByPlaceholderText('Search fields...');
  fireEvent.change(searchInput, { target: { value: 'price' } });

  const liveRegion = screen.getByRole('status');
  expect(liveRegion).toHaveTextContent(/\d+ fields? found/);
});
```

### useFieldValues Hook
**File**: `apps/web/hooks/use-field-values.ts`

#### Test Cases

**Test: Fetches field values from API**
```typescript
test('fetches field values successfully', async () => {
  const mockValues = { field_name: 'listing.condition', values: ['New', 'Like New', 'Good'], count: 3 };

  server.use(
    rest.get('/api/v1/fields/listing.condition/values', (req, res, ctx) => {
      return res(ctx.json(mockValues));
    })
  );

  const { result, waitFor } = renderHook(() =>
    useFieldValues({ fieldName: 'listing.condition' })
  );

  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.values).toEqual(['New', 'Like New', 'Good']);
});
```

**Test: Caches results for 5 minutes**
```typescript
test('caches query results for 5 minutes', async () => {
  const fetchSpy = jest.fn(() =>
    Promise.resolve({ field_name: 'cpu.manufacturer', values: ['Intel', 'AMD'], count: 2 })
  );

  const { result, rerender } = renderHook(() =>
    useFieldValues({ fieldName: 'cpu.manufacturer' })
  );

  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(fetchSpy).toHaveBeenCalledTimes(1);

  // Re-render within 5 minutes
  rerender();
  expect(fetchSpy).toHaveBeenCalledTimes(1); // Should not refetch

  // Fast-forward 5 minutes
  act(() => jest.advanceTimersByTime(5 * 60 * 1000));

  rerender();
  // Should refetch after stale time
  await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(2));
});
```

**Test: Handles fieldName === null gracefully**
```typescript
test('does not fetch when fieldName is null', () => {
  const { result } = renderHook(() =>
    useFieldValues({ fieldName: null })
  );

  expect(result.current.isFetching).toBe(false);
  expect(result.current.data).toBeUndefined();
});
```

**Test: Constructs query parameters correctly**
```typescript
test('includes limit and search in query params', async () => {
  let capturedUrl = '';

  server.use(
    rest.get('/api/v1/fields/:fieldName/values', (req, res, ctx) => {
      capturedUrl = req.url.toString();
      return res(ctx.json({ field_name: 'listing.manufacturer', values: [], count: 0 }));
    })
  );

  renderHook(() =>
    useFieldValues({ fieldName: 'listing.manufacturer', limit: 50, search: 'dell' })
  );

  await waitFor(() => {
    expect(capturedUrl).toContain('limit=50');
    expect(capturedUrl).toContain('search=dell');
  });
});
```

**Test: Disabled when enabled=false**
```typescript
test('respects enabled flag', () => {
  const { result } = renderHook(() =>
    useFieldValues({ fieldName: 'listing.condition', enabled: false })
  );

  expect(result.current.isFetching).toBe(false);
  expect(result.current.data).toBeUndefined();
});
```

### ValueInput Component
**File**: `apps/web/components/valuation/value-input.tsx`

#### Test Cases

**Test: Shows ComboBox for enum fields**
```typescript
test('renders ComboBox for enum field type', () => {
  render(
    <ValueInput
      fieldType="enum"
      options={['New', 'Used']}
      value="New"
      onChange={jest.fn()}
    />
  );

  expect(screen.getByRole('combobox')).toBeInTheDocument();
});
```

**Test: Shows ComboBox for string fields with autocomplete**
```typescript
test('renders ComboBox for string field with fetched values', async () => {
  server.use(
    rest.get('/api/v1/fields/listing.manufacturer/values', (req, res, ctx) => {
      return res(ctx.json({ field_name: 'listing.manufacturer', values: ['Dell', 'HP'], count: 2 }));
    })
  );

  render(
    <ValueInput
      fieldType="string"
      fieldName="listing.manufacturer"
      value=""
      onChange={jest.fn()}
    />
  );

  await waitFor(() => {
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });
});
```

**Test: Shows number input for number fields**
```typescript
test('renders number input for number field type', () => {
  render(
    <ValueInput
      fieldType="number"
      value={100}
      onChange={jest.fn()}
    />
  );

  const input = screen.getByPlaceholderText('Enter number...');
  expect(input).toHaveAttribute('type', 'number');
});
```

**Test: Shows checkbox for boolean fields**
```typescript
test('renders checkbox for boolean field type', () => {
  render(
    <ValueInput
      fieldType="boolean"
      value={true}
      onChange={jest.fn()}
    />
  );

  expect(screen.getByRole('checkbox')).toBeChecked();
});
```

**Test: Allows custom values for string fields**
```typescript
test('allows creating custom values for string fields', async () => {
  const mockOnChange = jest.fn();

  render(
    <ValueInput
      fieldType="string"
      fieldName="listing.custom_field"
      value=""
      onChange={mockOnChange}
    />
  );

  const combobox = screen.getByRole('combobox');
  fireEvent.click(combobox);

  const input = screen.getByPlaceholderText(/Select or type/);
  fireEvent.change(input, { target: { value: 'Custom Value' } });
  fireEvent.keyDown(input, { key: 'Enter' });

  expect(mockOnChange).toHaveBeenCalledWith('Custom Value');
});
```

**Test: Disallows custom values for enum fields**
```typescript
test('prevents custom values for enum fields', () => {
  render(
    <ValueInput
      fieldType="enum"
      options={['Option1', 'Option2']}
      value=""
      onChange={jest.fn()}
    />
  );

  // ComboBox should have enableInlineCreate=false
  const combobox = screen.getByRole('combobox');
  fireEvent.click(combobox);

  // Typing custom value should not create new option
  expect(screen.queryByText('Create "Custom"')).not.toBeInTheDocument();
});
```

**Test: Combines static options with fetched values**
```typescript
test('merges static options with API-fetched values', async () => {
  server.use(
    rest.get('/api/v1/fields/listing.condition/values', (req, res, ctx) => {
      return res(ctx.json({ field_name: 'listing.condition', values: ['Refurbished'], count: 1 }));
    })
  );

  render(
    <ValueInput
      fieldType="string"
      fieldName="listing.condition"
      options={['New', 'Used']}
      value=""
      onChange={jest.fn()}
    />
  );

  await waitFor(() => {
    const combobox = screen.getByRole('combobox');
    fireEvent.click(combobox);

    // Should show both static and fetched
    expect(screen.getByText('New')).toBeInTheDocument();
    expect(screen.getByText('Refurbished')).toBeInTheDocument();
  });
});
```

## Integration Tests

### Backend API Tests
**File**: `tests/api/test_fields.py`

#### Test Cases

**Test: GET /v1/fields/listing.condition/values returns enum values**
```python
async def test_get_enum_field_values(client: AsyncClient, db_session):
    """Test fetching values for enum field"""
    # Create test data
    listing1 = Listing(condition="New", price_usd=100)
    listing2 = Listing(condition="Like New", price_usd=150)
    db_session.add_all([listing1, listing2])
    await db_session.commit()

    response = await client.get("/v1/fields/listing.condition/values")

    assert response.status_code == 200
    data = response.json()
    assert data["field_name"] == "listing.condition"
    assert "New" in data["values"]
    assert "Like New" in data["values"]
    assert data["count"] >= 2
```

**Test: GET /v1/fields/cpu.manufacturer/values returns distinct values**
```python
async def test_get_distinct_cpu_manufacturers(client: AsyncClient, db_session):
    """Test fetching distinct CPU manufacturers"""
    cpu1 = CPU(name="Intel Core i7", manufacturer="Intel")
    cpu2 = CPU(name="Intel Core i5", manufacturer="Intel")
    cpu3 = CPU(name="AMD Ryzen 7", manufacturer="AMD")
    db_session.add_all([cpu1, cpu2, cpu3])
    await db_session.commit()

    response = await client.get("/v1/fields/cpu.manufacturer/values")

    assert response.status_code == 200
    data = response.json()
    assert set(data["values"]) == {"Intel", "AMD"}
    assert data["count"] == 2
```

**Test: Limit parameter works correctly**
```python
async def test_field_values_respects_limit(client: AsyncClient, db_session):
    """Test limit parameter caps returned values"""
    # Create 20 listings with different sellers
    for i in range(20):
        listing = Listing(seller=f"seller_{i}", price_usd=100)
        db_session.add(listing)
    await db_session.commit()

    response = await client.get("/v1/fields/listing.seller/values?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert len(data["values"]) <= 5
```

**Test: Search parameter filters values**
```python
async def test_field_values_search_filter(client: AsyncClient, db_session):
    """Test search parameter filters results"""
    cpu1 = CPU(name="Intel Core i7", manufacturer="Intel")
    cpu2 = CPU(name="AMD Ryzen 7", manufacturer="AMD")
    cpu3 = CPU(name="Apple M1", manufacturer="Apple")
    db_session.add_all([cpu1, cpu2, cpu3])
    await db_session.commit()

    response = await client.get("/v1/fields/cpu.manufacturer/values?search=intel")

    assert response.status_code == 200
    data = response.json()
    assert "Intel" in data["values"]
    assert "AMD" not in data["values"]
```

**Test: Invalid field name returns 404**
```python
async def test_invalid_field_name_404(client: AsyncClient):
    """Test 404 for non-existent field"""
    response = await client.get("/v1/fields/invalid.field/values")

    assert response.status_code == 404
    assert "field" in response.json()["detail"].lower()
```

**Test: Null values filtered out**
```python
async def test_null_values_excluded(client: AsyncClient, db_session):
    """Test that NULL values are excluded from results"""
    listing1 = Listing(manufacturer="Dell", price_usd=100)
    listing2 = Listing(manufacturer=None, price_usd=150)
    listing3 = Listing(manufacturer="HP", price_usd=200)
    db_session.add_all([listing1, listing2, listing3])
    await db_session.commit()

    response = await client.get("/v1/fields/listing.manufacturer/values")

    assert response.status_code == 200
    data = response.json()
    assert None not in data["values"]
    assert data["count"] == 2
```

### Frontend Flow Tests
**File**: `apps/web/__tests__/integration/valuation-rules.test.tsx`

#### Test Cases

**Test: Select field → fetch values → show autocomplete**
```typescript
test('autocomplete workflow for field selection', async () => {
  server.use(
    rest.get('/api/v1/fields/listing.manufacturer/values', (req, res, ctx) => {
      return res(ctx.json({ field_name: 'listing.manufacturer', values: ['Dell', 'HP'], count: 2 }));
    })
  );

  render(<ConditionRow {...mockProps} />);

  // Select field
  const fieldSelector = screen.getByRole('combobox', { name: /select field/i });
  fireEvent.click(fieldSelector);

  const manufacturerField = screen.getByText(/Manufacturer/);
  fireEvent.click(manufacturerField);

  // Wait for values to load
  await waitFor(() => {
    const valueSelector = screen.getByRole('combobox', { name: /select.*value/i });
    fireEvent.click(valueSelector);

    expect(screen.getByText('Dell')).toBeInTheDocument();
    expect(screen.getByText('HP')).toBeInTheDocument();
  });
});
```

**Test: Type in search → debounce → filter results**
```typescript
jest.useFakeTimers();

test('search input is debounced correctly', async () => {
  render(<EntityFieldSelector value={null} onChange={jest.fn()} />);

  const button = screen.getByRole('combobox');
  fireEvent.click(button);

  const searchInput = screen.getByPlaceholderText('Search fields...');

  // Type quickly
  fireEvent.change(searchInput, { target: { value: 'p' } });
  fireEvent.change(searchInput, { target: { value: 'pr' } });
  fireEvent.change(searchInput, { target: { value: 'pri' } });

  // Before debounce completes
  expect(screen.queryAllByRole('option').length).toBeGreaterThan(50);

  // After 200ms
  act(() => jest.advanceTimersByTime(200));

  await waitFor(() => {
    const filteredOptions = screen.queryAllByRole('option');
    expect(filteredOptions.length).toBeLessThan(20);
  });
});
```

**Test: Select value → update condition**
```typescript
test('selecting value updates parent condition', async () => {
  const mockOnChange = jest.fn();

  render(
    <ValueInput
      fieldType="enum"
      options={['New', 'Used']}
      value=""
      onChange={mockOnChange}
    />
  );

  const combobox = screen.getByRole('combobox');
  fireEvent.click(combobox);

  const newOption = screen.getByText('New');
  fireEvent.click(newOption);

  expect(mockOnChange).toHaveBeenCalledWith('New');
});
```

**Test: Change field → clear value → fetch new values**
```typescript
test('changing field clears value and fetches new options', async () => {
  server.use(
    rest.get('/api/v1/fields/listing.condition/values', (req, res, ctx) => {
      return res(ctx.json({ field_name: 'listing.condition', values: ['New', 'Used'], count: 2 }));
    }),
    rest.get('/api/v1/fields/cpu.manufacturer/values', (req, res, ctx) => {
      return res(ctx.json({ field_name: 'cpu.manufacturer', values: ['Intel', 'AMD'], count: 2 }));
    })
  );

  const { rerender } = render(
    <ValueInput
      fieldType="string"
      fieldName="listing.condition"
      value="New"
      onChange={jest.fn()}
    />
  );

  // Change field
  rerender(
    <ValueInput
      fieldType="string"
      fieldName="cpu.manufacturer"
      value=""
      onChange={jest.fn()}
    />
  );

  await waitFor(() => {
    const combobox = screen.getByRole('combobox');
    fireEvent.click(combobox);

    expect(screen.getByText('Intel')).toBeInTheDocument();
    expect(screen.queryByText('New')).not.toBeInTheDocument();
  });
});
```

**Test: Cache hit scenario (no API call on second fetch)**
```typescript
test('uses cached data on second fetch', async () => {
  const fetchSpy = jest.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({ field_name: 'listing.condition', values: ['New'], count: 1 }) })
  );
  global.fetch = fetchSpy;

  const { rerender } = render(
    <ValueInput
      fieldType="string"
      fieldName="listing.condition"
      value=""
      onChange={jest.fn()}
    />
  );

  await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));

  // Unmount and remount
  rerender(<></>);
  rerender(
    <ValueInput
      fieldType="string"
      fieldName="listing.condition"
      value=""
      onChange={jest.fn()}
    />
  );

  // Should use cache (no second fetch)
  expect(fetchSpy).toHaveBeenCalledTimes(1);
});
```

## Manual Testing Checklist

### P2-UX-001: Scrollable Dropdown

#### Performance Tests

**Test: Open field selector with 50+ fields**
- [ ] Navigate to Valuation Rules page: `http://localhost:3020/valuation-rules`
- [ ] Click "Add Condition" button in any rule
- [ ] Click field selector dropdown
- [ ] **Expected**: Dropdown opens instantly (< 100ms)

**Test: Verify virtual rendering with React DevTools**
- [ ] Open React DevTools
- [ ] Inspect `VirtualizedCommandList` component
- [ ] Count rendered DOM nodes
- [ ] **Expected**: < 30 `CommandItem` nodes in DOM despite 200+ total fields

**Test: Scroll smoothly without lag**
- [ ] Open field selector dropdown
- [ ] Scroll rapidly up and down
- [ ] Use trackpad/mouse wheel for fast scrolling
- [ ] **Expected**: Smooth 60 FPS scrolling, no janky animations

**Test: Search filters after 200ms debounce**
- [ ] Open field selector dropdown
- [ ] Type "price" quickly in search input
- [ ] Observe filtering behavior
- [ ] **Expected**: Results filter after ~200ms delay, not on every keystroke

**Test: No performance degradation**
- [ ] Open Chrome DevTools Performance tab
- [ ] Start recording
- [ ] Open dropdown, search, scroll
- [ ] Stop recording
- [ ] **Expected**: No long tasks > 50ms, consistent frame rate

#### Functionality Tests

**Test: Field selector opens on click**
- [ ] Click field selector button
- [ ] **Expected**: Dropdown opens, search input auto-focused

**Test: Search input filters fields correctly**
- [ ] Open field selector
- [ ] Type "condition" in search
- [ ] **Expected**: Only fields with "condition" in label/key/entity shown

**Test: Arrow keys navigate through fields**
- [ ] Open field selector
- [ ] Press ArrowDown key
- [ ] Press ArrowUp key
- [ ] **Expected**: Focus moves between fields, visible focus indicator

**Test: Enter key selects field**
- [ ] Open field selector
- [ ] Navigate to a field with arrow keys
- [ ] Press Enter
- [ ] **Expected**: Field selected, dropdown closes

**Test: Escape key closes dropdown**
- [ ] Open field selector
- [ ] Press Escape
- [ ] **Expected**: Dropdown closes, focus returns to button

**Test: Selected field shows check icon**
- [ ] Select a field (e.g., "Listing → Price")
- [ ] Open dropdown again
- [ ] **Expected**: Selected field has check mark icon next to it

**Test: Field metadata displays**
- [ ] Open field selector
- [ ] Observe each field item
- [ ] **Expected**: Shows "Entity • Type" metadata below field label

**Test: Field descriptions shown**
- [ ] Find field with description (e.g., "Price USD")
- [ ] **Expected**: Description text shown in muted color below metadata

#### Mobile/Responsive Tests

**Test: Viewport < 640px**
- [ ] Open Chrome DevTools Device Mode
- [ ] Set viewport to iPhone SE (375px)
- [ ] Open field selector
- [ ] **Expected**: Dropdown fits screen width, text truncates properly

**Test: Dropdown width appropriate**
- [ ] Test on small screen (< 640px)
- [ ] Test on medium screen (768px)
- [ ] Test on large screen (1920px)
- [ ] **Expected**: Dropdown width never exceeds viewport

**Test: Touch scrolling works smoothly**
- [ ] Use touch device or enable touch emulation
- [ ] Open field selector
- [ ] Scroll with touch gesture
- [ ] **Expected**: Smooth momentum scrolling

**Test: Text truncates properly**
- [ ] Open field selector on narrow viewport
- [ ] Observe long field names
- [ ] **Expected**: Text truncates with ellipsis (...), no overflow

**Test: No horizontal overflow**
- [ ] Set viewport to 320px (smallest mobile)
- [ ] Open field selector
- [ ] **Expected**: No horizontal scrollbar, all content contained

### P2-UX-002: Field Value Autocomplete

#### Enum Field Tests

**Test: Select enum field shows predefined options**
- [ ] Add condition
- [ ] Select field: "listing.condition"
- [ ] Click value dropdown
- [ ] **Expected**: Shows enum values ("New", "Like New", "Good", etc.)

**Test: Cannot create custom enum values**
- [ ] Select field: "listing.condition"
- [ ] Click value dropdown
- [ ] Type "Custom Value"
- [ ] **Expected**: No "Create" option appears, only existing enums

**Test: Selecting enum value updates condition**
- [ ] Select field: "listing.condition"
- [ ] Select value: "New"
- [ ] **Expected**: Value populated in condition row

#### String Field Tests

**Test: Select string field shows autocomplete**
- [ ] Add condition
- [ ] Select field: "listing.manufacturer"
- [ ] Click value dropdown
- [ ] **Expected**: Dropdown shows existing manufacturers from database

**Test: Can create custom string value**
- [ ] Select field: "listing.manufacturer"
- [ ] Type "Custom Manufacturer" in dropdown
- [ ] **Expected**: Shows "Create: Custom Manufacturer" option
- [ ] Click create option
- [ ] **Expected**: Value populated

**Test: Search filters suggestions**
- [ ] Select field with many values (e.g., "cpu.name")
- [ ] Type "intel" in search
- [ ] **Expected**: Only CPU names containing "intel" shown

**Test: Loading state shows briefly**
- [ ] Open Network tab, throttle to "Slow 3G"
- [ ] Select field: "listing.manufacturer"
- [ ] **Expected**: "Loading..." placeholder shown while fetching

#### Number Field Tests

**Test: Select number field shows input**
- [ ] Add condition
- [ ] Select field: "listing.price_usd"
- [ ] **Expected**: Number input rendered (not dropdown)

**Test: Accepts numeric input only**
- [ ] Select field: "listing.price_usd"
- [ ] Try typing "abc"
- [ ] **Expected**: No letters allowed, only numbers and decimal

#### Caching Tests

**Test: Field values cached for 5 minutes**
- [ ] Select field: "cpu.manufacturer"
- [ ] Wait for values to load
- [ ] Note Network tab request
- [ ] Change to different field
- [ ] Change back to "cpu.manufacturer"
- [ ] **Expected**: No new network request (cache hit in Network tab)

**Test: Cache expires after 5 minutes**
- [ ] Select field, wait for values
- [ ] Wait 5 minutes (or mock fast-forward time)
- [ ] Re-select same field
- [ ] **Expected**: New API request made

**Test: React Query DevTools shows cache**
- [ ] Open React Query DevTools panel
- [ ] Select field to trigger fetch
- [ ] Observe queries list
- [ ] **Expected**: Query key "field-values" with data and timestamp

#### Multi-value Operator Tests

**Test: Operator "in" shows text input**
- [ ] Add condition
- [ ] Select operator: "in"
- [ ] **Expected**: Text input with placeholder "Value1, Value2, Value3"

**Test: Enter comma-separated values**
- [ ] Select operator: "in"
- [ ] Type "New, Like New, Good"
- [ ] **Expected**: Values accepted, parsed as array

## Accessibility Testing

### WCAG 2.1 AA Requirements

#### Keyboard Navigation

**Test: Tab to field selector button**
- [ ] Tab from previous element
- [ ] **Expected**: Field selector button receives focus with visible outline

**Test: Enter/Space opens dropdown**
- [ ] Focus field selector button
- [ ] Press Enter key
- [ ] **Expected**: Dropdown opens
- [ ] Press Escape, then Space key
- [ ] **Expected**: Dropdown opens

**Test: Arrow keys navigate items**
- [ ] Open dropdown
- [ ] Press ArrowDown multiple times
- [ ] Press ArrowUp multiple times
- [ ] **Expected**: Focus moves between items, scrolls into view

**Test: Enter selects item**
- [ ] Navigate to item with arrow keys
- [ ] Press Enter
- [ ] **Expected**: Item selected, dropdown closes

**Test: Escape closes dropdown**
- [ ] Open dropdown
- [ ] Press Escape
- [ ] **Expected**: Dropdown closes immediately

**Test: Focus returns to button on close**
- [ ] Open dropdown
- [ ] Press Escape or select item
- [ ] **Expected**: Focus returns to trigger button

#### Screen Reader Testing

**Test with VoiceOver (macOS) or NVDA (Windows)**

**Test: Field selector button announces label**
- [ ] Navigate to field selector with screen reader
- [ ] **Expected**: Announces "Select field, button, collapsed" (or similar)

**Test: Search input announces role and placeholder**
- [ ] Open dropdown
- [ ] **Expected**: Screen reader announces "Search fields, edit text"

**Test: Result count announced**
- [ ] Open dropdown
- [ ] Type in search
- [ ] **Expected**: Announces "5 fields found" (aria-live region)

**Test: Field items announce label and metadata**
- [ ] Navigate through field items
- [ ] **Expected**: Announces "Listing Price, Listing • number"

**Test: Selected state announced**
- [ ] Navigate to selected field
- [ ] **Expected**: Announces "selected" or equivalent

**Test: Loading state announced**
- [ ] Select field with slow API
- [ ] **Expected**: Screen reader announces "Loading..."

#### Visual Accessibility

**Test: Focus indicators visible**
- [ ] Tab through all interactive elements
- [ ] **Expected**: 2px solid outline on focus, minimum 3:1 contrast

**Test: Color contrast meets 4.5:1 ratio**
- [ ] Use axe DevTools or Lighthouse
- [ ] **Expected**: All text passes AA contrast requirements

**Test: Text readable at 200% zoom**
- [ ] Set browser zoom to 200%
- [ ] Open field selector
- [ ] **Expected**: Text remains readable, no clipping

**Test: No content hidden at 400% zoom**
- [ ] Set browser zoom to 400%
- [ ] Test all interactions
- [ ] **Expected**: All content accessible, vertical scrolling OK

## Performance Testing

### Metrics to Measure

#### Initial Render Performance

**Target**: < 100ms for field selector render

**How to Measure**:
1. Open Chrome DevTools → Lighthouse
2. Run "Performance" audit
3. Check "Time to Interactive" for field selector

**Passing Criteria**:
- First Contentful Paint: < 1.8s
- Time to Interactive: < 3.8s
- Total Blocking Time: < 300ms

#### Search Performance

**Target**: < 50ms per filter operation

**How to Measure**:
```javascript
// In EntityFieldSelector component, add:
const startTime = performance.now();
const filtered = allFields.filter(/* filter logic */);
const endTime = performance.now();
console.log(`Filter took ${endTime - startTime}ms`);
```

**Passing Criteria**:
- 200 fields: < 20ms
- 500 fields: < 50ms
- 1000 fields: < 100ms

#### Virtual Scrolling Performance

**Target**: 60 FPS while scrolling

**How to Measure**:
1. Open Chrome DevTools → Performance tab
2. Start recording
3. Open field selector with 500+ items
4. Scroll rapidly for 5 seconds
5. Stop recording
6. Analyze frame rate in "Frames" section

**Passing Criteria**:
- Average FPS: > 55
- Frame drops: < 5%
- No long tasks: > 50ms

#### API Response Time

**Target**: < 200ms for field values

**How to Measure**:
1. Open Network tab
2. Select field to trigger API call
3. Check response time in "Timing" tab

**Passing Criteria**:
- Waiting (TTFB): < 100ms
- Content Download: < 50ms
- Total: < 200ms

#### Cache Performance

**Target**: < 10ms for cache hits

**How to Measure**:
1. Open React Query DevTools
2. Select field to populate cache
3. Re-select same field
4. Check "dataUpdatedAt" timestamp

**Passing Criteria**:
- Cache hit rate: > 80%
- Cache retrieval: < 10ms (instant)

### Performance Test Cases

#### Test 1: Large Field List Performance

**Setup**:
```typescript
// Mock 500 fields
const mockMetadata = {
  entities: Array.from({ length: 100 }, (_, i) => ({
    key: `entity${i}`,
    label: `Entity ${i}`,
    fields: Array.from({ length: 5 }, (_, j) => ({
      key: `field${j}`,
      label: `Field ${j}`,
      data_type: 'string'
    }))
  }))
};
```

**Steps**:
1. Start Performance recording
2. Render EntityFieldSelector with 500 fields
3. Measure initial render time
4. Type in search, measure filter time
5. Verify < 20 items in DOM

**Expected Results**:
- Initial render: < 100ms
- Search filter: < 50ms
- DOM nodes: < 30

#### Test 2: Autocomplete Response Time

**Setup**:
```python
# Backend: Create 100 distinct manufacturers
for i in range(100):
    listing = Listing(manufacturer=f"Manufacturer {i}", price_usd=100)
    db.add(listing)
await db.commit()
```

**Steps**:
1. Open Network tab
2. Select field: "listing.manufacturer"
3. Measure time to first value display
4. Verify loading indicator shown

**Expected Results**:
- API response: < 200ms
- First render: < 100ms
- Total time: < 300ms

#### Test 3: Virtual Scrolling Smoothness

**Setup**:
```typescript
// Render 1000 items
const items = Array.from({ length: 1000 }, (_, i) => ({ id: i, label: `Item ${i}` }));
```

**Steps**:
1. Open Performance Monitor (Cmd+Shift+P → "Show Performance Monitor")
2. Render VirtualizedCommandList with 1000 items
3. Scroll rapidly up and down
4. Record frame rate for 10 seconds

**Expected Results**:
- Consistent 60 FPS
- CPU usage: < 50%
- Memory: No leaks

## Regression Testing

### Ensure No Breaking Changes

**Test: Existing conditions evaluate correctly**
- [ ] Open rule with existing conditions
- [ ] Verify all conditions render
- [ ] Test condition evaluation (check listings match)
- [ ] **Expected**: No errors, correct evaluation

**Test: Rule saving works as before**
- [ ] Create new rule
- [ ] Add multiple conditions
- [ ] Save rule
- [ ] Refresh page
- [ ] **Expected**: Rule persisted correctly

**Test: Modal interactions unchanged**
- [ ] Open rule builder modal
- [ ] Add condition, save
- [ ] Cancel modal
- [ ] **Expected**: Modal behavior same as before

**Test: Other dropdowns not affected**
- [ ] Test operator dropdown
- [ ] Test action type dropdown
- [ ] Test profile selector
- [ ] **Expected**: Other dropdowns work normally

**Test: Console free of errors/warnings**
- [ ] Open Console tab
- [ ] Perform all common workflows
- [ ] **Expected**: No errors, no React warnings

## Browser Compatibility

### Test Browsers

**Test: Chrome (latest)**
- [ ] Version: _______________
- [ ] All features work correctly
- [ ] Performance meets targets

**Test: Firefox (latest)**
- [ ] Version: _______________
- [ ] All features work correctly
- [ ] Scrolling smooth

**Test: Safari (latest)**
- [ ] Version: _______________
- [ ] All features work correctly
- [ ] Virtual scrolling works

**Test: Edge (latest)**
- [ ] Version: _______________
- [ ] All features work correctly
- [ ] Autocomplete works

**Test: Mobile Safari (iOS)**
- [ ] iOS Version: _______________
- [ ] Touch scrolling smooth
- [ ] Dropdown fits screen

**Test: Chrome Mobile (Android)**
- [ ] Android Version: _______________
- [ ] Touch interactions work
- [ ] Performance acceptable

## Known Issues / Edge Cases

### Issue Template

When documenting issues, use this format:

**Issue #1: [Title]**
- **Description**: Brief description of the issue
- **Steps to Reproduce**:
  1. Step 1
  2. Step 2
  3. Step 3
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Severity**: Critical / High / Medium / Low
- **Workaround**: If any
- **Fix Required**: Yes / No / Investigating

**Example**:

**Issue #1: Virtual scrolling jumps on rapid scroll**
- **Description**: When scrolling very quickly, items occasionally jump position
- **Steps to Reproduce**:
  1. Open field selector with 500+ items
  2. Scroll to bottom rapidly
  3. Scroll back to top rapidly
- **Expected Behavior**: Smooth scrolling without position jumps
- **Actual Behavior**: Occasional item repositioning during fast scroll
- **Severity**: Low
- **Workaround**: Scroll more slowly
- **Fix Required**: Investigating (may be @tanstack/react-virtual behavior)

## Test Execution Record

| Date | Tester | Test Type | Results | Issues Found | Notes |
|------|--------|-----------|---------|--------------|-------|
| 2025-10-15 | [Name] | Unit Tests | Pass/Fail | Issue IDs | Coverage: ___ % |
| 2025-10-15 | [Name] | Integration | Pass/Fail | Issue IDs | All APIs working |
| 2025-10-15 | [Name] | Manual | Pass/Fail | Issue IDs | Chrome 120.0 |
| 2025-10-15 | [Name] | Accessibility | Pass/Fail | Issue IDs | VoiceOver tested |
| 2025-10-15 | [Name] | Performance | Pass/Fail | Issue IDs | All targets met |

## Success Criteria

Phase 2 is complete when:

- [x] All unit tests pass (70%+ coverage)
- [x] All integration tests pass
- [ ] All manual test checklist items verified
- [ ] WCAG 2.1 AA accessibility compliance
- [ ] Performance targets met:
  - [ ] Initial render < 100ms
  - [ ] Search filter < 50ms
  - [ ] Scroll at 60 FPS
  - [ ] API response < 200ms
- [ ] No critical bugs
- [ ] All acceptance criteria satisfied:
  - [x] P2-UX-001: Scrollable dropdown implemented
  - [x] P2-UX-002: Field value autocomplete implemented
- [ ] Browser compatibility verified (6 browsers)
- [ ] Regression tests pass

## Appendix

### Testing Tools Used

**Frontend Testing**:
- Jest - Unit testing framework
- React Testing Library - Component testing
- @testing-library/user-event - User interaction simulation
- MSW (Mock Service Worker) - API mocking

**Backend Testing**:
- pytest - Python testing framework
- pytest-asyncio - Async test support
- httpx - Async HTTP client for testing

**Performance Testing**:
- Chrome DevTools - Performance profiling
- Lighthouse - Page speed auditing
- React Profiler - Component render tracking
- React Query DevTools - Cache debugging

**Accessibility Testing**:
- axe DevTools - Automated accessibility auditing
- VoiceOver (macOS) - Screen reader testing
- NVDA (Windows) - Screen reader testing
- WAVE - Web accessibility evaluation

### Useful Commands

**Run unit tests**:
```bash
# Frontend
cd apps/web
pnpm test

# Backend
poetry run pytest tests/
```

**Run integration tests**:
```bash
poetry run pytest tests/api/test_fields.py -v
```

**Run tests with coverage**:
```bash
# Frontend
pnpm test --coverage

# Backend
poetry run pytest --cov=dealbrain_api tests/
```

**Start dev servers for manual testing**:
```bash
make up        # Start full stack
make api       # Backend only
make web       # Frontend only
```

### References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [@tanstack/react-virtual Docs](https://tanstack.com/virtual/latest)
- [React Testing Library Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-15
**Next Review**: After Phase 2 completion
