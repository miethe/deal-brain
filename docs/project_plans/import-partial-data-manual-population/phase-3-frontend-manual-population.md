---
title: "Phase 3: Frontend - Manual Population Modal"
description: "Build accessible modal component for completing partial imports with extracted data review"
audience: [ai-agents, developers]
tags:
  - implementation
  - frontend
  - ui
  - react
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: pending
related:
  - /docs/project_plans/import-partial-data-manual-population/implementation-plan.md
  - /docs/project_plans/import-partial-data-manual-population/phase-2-backend-api-services.md
---

# Phase 3: Frontend - Manual Population Modal

**Duration**: 2-3 days
**Dependencies**: Phase 2 complete (API endpoints ready)
**Risk Level**: Low (UI implementation)

## Phase Overview

Phase 3 builds the user-facing modal component for completing partial imports. The modal displays extracted data as read-only and provides editable fields for missing data (typically price).

**Key Outcomes**:
- PartialImportModal component renders correctly
- Modal integrated into import flow
- Calls completion API and handles responses
- Fully accessible and keyboard navigable
- Responsive on all device sizes

---

## Task 3.1: Create PartialImportModal Component

**Agent**: `ui-engineer`
**File**: `apps/web/components/imports/PartialImportModal.tsx`
**Duration**: 4-6 hours

### Objective
Build accessible, user-friendly modal for completing partial imports.

### Component Structure

```typescript
import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { Listing } from '@/types/listings';

interface PartialImportModalProps {
  listing: Listing;
  onComplete: () => void;
  onSkip: () => void;
}

export function PartialImportModal({
  listing,
  onComplete,
  onSkip,
}: PartialImportModalProps) {
  const [price, setPrice] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    // Validate price
    const priceNum = parseFloat(price);
    if (!price.trim()) {
      setError('Price is required');
      return;
    }
    if (isNaN(priceNum) || priceNum <= 0) {
      setError('Price must be a positive number');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/v1/listings/${listing.id}/complete`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price: priceNum }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save listing');
      }

      onComplete();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save listing. Please try again.';
      setError(message);
      console.error('Error completing import:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading && price.trim()) {
      handleSubmit();
    }
  };

  return (
    <Dialog open={true} onOpenChange={onSkip}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Complete Listing Import</DialogTitle>
          <DialogDescription>
            We extracted most data for this listing, but need your help with one field to complete it
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Extracted Data (Read-Only) */}
          <div className="border-l-4 border-green-500 bg-green-50 p-4 rounded-r-md">
            <h3 className="font-semibold text-sm flex items-center gap-2 text-green-900 mb-3">
              <CheckCircle className="w-4 h-4" />
              Extracted Data (Read-Only)
            </h3>

            <div className="text-sm space-y-2 text-green-800">
              <div className="flex justify-between">
                <span className="font-medium">Title:</span>
                <span>{listing.title}</span>
              </div>

              {listing.cpu?.name && (
                <div className="flex justify-between">
                  <span className="font-medium">CPU:</span>
                  <span>{listing.cpu.name}</span>
                </div>
              )}

              {listing.ram_gb && (
                <div className="flex justify-between">
                  <span className="font-medium">RAM:</span>
                  <span>{listing.ram_gb}GB</span>
                </div>
              )}

              {listing.primary_storage_gb && (
                <div className="flex justify-between">
                  <span className="font-medium">Storage:</span>
                  <span>
                    {listing.primary_storage_gb}GB {listing.primary_storage_type || 'SSD'}
                  </span>
                </div>
              )}

              {listing.condition && (
                <div className="flex justify-between">
                  <span className="font-medium">Condition:</span>
                  <span className="capitalize">{listing.condition}</span>
                </div>
              )}

              {listing.gpu?.name && (
                <div className="flex justify-between">
                  <span className="font-medium">GPU:</span>
                  <span>{listing.gpu.name}</span>
                </div>
              )}
            </div>
          </div>

          {/* Missing Fields (Editable) */}
          <div className="border-l-4 border-yellow-400 bg-yellow-50 p-4 rounded-r-md">
            <h3 className="font-semibold text-sm flex items-center gap-2 text-yellow-900 mb-3">
              <AlertCircle className="w-4 h-4" />
              Complete These Fields
            </h3>

            <div className="space-y-3">
              <div>
                <Label htmlFor="price" className="text-yellow-900 font-medium">
                  Price (USD)
                  <span className="text-red-500 ml-1" aria-label="required">
                    *
                  </span>
                </Label>
                <Input
                  id="price"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="299.99"
                  value={price}
                  onChange={(e) => {
                    setPrice(e.target.value);
                    if (error) setError('');
                  }}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                  className={`mt-1 ${error ? 'border-red-500 focus:border-red-500' : ''}`}
                  autoFocus
                  aria-label="Listing price in USD"
                  aria-required="true"
                  aria-invalid={!!error}
                  aria-describedby={error ? 'price-error' : undefined}
                />
                {error && (
                  <p
                    id="price-error"
                    className="text-xs text-red-600 mt-1"
                    role="alert"
                  >
                    {error}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Info Message */}
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800 text-sm">
              After you complete these fields, we'll calculate the deal rating and metrics for this listing.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter className="flex gap-2">
          <Button
            variant="outline"
            onClick={onSkip}
            disabled={isLoading}
            className="flex-1 sm:flex-initial"
          >
            Skip for Now
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isLoading || !price.trim()}
            className="flex-1 sm:flex-initial"
          >
            {isLoading ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save & Complete'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### Acceptance Criteria

- [ ] Modal renders with extracted data displayed read-only
- [ ] Price input auto-focuses on open
- [ ] Validates price is positive number
- [ ] Validates price field not empty
- [ ] Shows error message for invalid price
- [ ] Error message cleared when user starts typing
- [ ] Calls completion API on submit with correct format
- [ ] Shows loading state during submission
- [ ] Disables submit button while loading
- [ ] Closes on successful completion (calls onComplete)
- [ ] Keyboard accessible (Tab, Enter, Esc)
- [ ] Esc key triggers onSkip
- [ ] Screen reader announces sections correctly
- [ ] Responsive design (works on mobile, tablet, desktop)
- [ ] Aria labels and descriptions present
- [ ] Error messages have proper role="alert"
- [ ] All extracted fields displayed in read-only section

### Testing

```typescript
// apps/web/components/imports/__tests__/PartialImportModal.test.tsx
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PartialImportModal } from '../PartialImportModal';
import { Listing } from '@/types/listings';

describe('PartialImportModal', () => {
  const mockListing: Listing = {
    id: 1,
    title: 'Dell OptiPlex 7090',
    cpu: { name: 'Intel Core i5-10500' },
    ram_gb: 8,
    primary_storage_gb: 256,
    primary_storage_type: 'SSD',
    condition: 'refurbished',
    quality: 'partial',
    price_usd: null,
    adjusted_price_usd: null,
  };

  const mockOnComplete = vi.fn();
  const mockOnSkip = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders extracted data as read-only', () => {
    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText('Dell OptiPlex 7090')).toBeInTheDocument();
    expect(screen.getByText(/Intel Core i5-10500/)).toBeInTheDocument();
    expect(screen.getByText('8GB')).toBeInTheDocument();
  });

  it('auto-focuses price input', () => {
    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);
    expect(input).toHaveFocus();
  });

  it('validates price is positive', async () => {
    const user = userEvent.setup();

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);
    const submitButton = screen.getByText('Save & Complete');

    await user.type(input, '-100');
    await user.click(submitButton);

    expect(
      screen.getByText(/must be a positive number/)
    ).toBeInTheDocument();
    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('validates price not empty', async () => {
    const user = userEvent.setup();

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const submitButton = screen.getByText('Save & Complete');
    await user.click(submitButton);

    expect(screen.getByText('Price is required')).toBeInTheDocument();
    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('submits valid price', async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    );

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);
    const submitButton = screen.getByText('Save & Complete');

    await user.type(input, '299.99');
    await user.click(submitButton);

    await waitFor(() => expect(mockOnComplete).toHaveBeenCalled());

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/listings/1/complete',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ price: 299.99 }),
      })
    );
  });

  it('disables submit button while loading', async () => {
    const user = userEvent.setup();

    let resolveRequest: (value: any) => void;
    global.fetch = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveRequest = resolve;
        })
    );

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);
    const submitButton = screen.getByText('Save & Complete');

    await user.type(input, '299.99');
    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Saving...')).toBeInTheDocument();

    resolveRequest({ ok: true, json: () => Promise.resolve({}) });

    await waitFor(() => expect(mockOnComplete).toHaveBeenCalled());
  });

  it('shows error on API failure', async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid price' }),
      })
    );

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);
    const submitButton = screen.getByText('Save & Complete');

    await user.type(input, '299.99');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Invalid price')).toBeInTheDocument();
    });

    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('clears error when user types', async () => {
    const user = userEvent.setup();

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);
    const submitButton = screen.getByText('Save & Complete');

    await user.click(submitButton);
    expect(screen.getByText('Price is required')).toBeInTheDocument();

    await user.type(input, '299.99');
    expect(screen.queryByText('Price is required')).not.toBeInTheDocument();
  });

  it('handles Enter key for submission', async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    );

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);
    await user.type(input, '299.99{Enter}');

    await waitFor(() => expect(mockOnComplete).toHaveBeenCalled());
  });

  it('calls onSkip when dialog closed', async () => {
    const user = userEvent.setup();

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const skipButton = screen.getByText('Skip for Now');
    await user.click(skipButton);

    expect(mockOnSkip).toHaveBeenCalled();
  });
});
```

---

## Task 3.2: Integrate Modal with Import Flow

**Agent**: `ui-engineer`
**File**: `apps/web/app/dashboard/import/page.tsx`
**Duration**: 2-3 hours

### Objective
Auto-open modal when partial import completes and handle completion flow.

### Implementation

```typescript
'use client';

import { useState, useEffect } from 'react';
import { PartialImportModal } from '@/components/imports/PartialImportModal';
import { ImportProgress } from '@/components/imports/ImportProgress';
import { Listing } from '@/types/listings';
import { useQueryClient } from '@tanstack/react-query';

export default function ImportPage() {
  const [partialListing, setPartialListing] = useState<Listing | null>(null);
  const [completedListings, setCompletedListings] = useState<Listing[]>([]);
  const queryClient = useQueryClient();

  // Listen for import completion events from bulk status polling
  useEffect(() => {
    const handleImportComplete = (event: CustomEvent<{
      listing: Listing;
      quality: string;
    }>) => {
      const { listing, quality } = event.detail;

      if (quality === 'partial') {
        setPartialListing(listing);
      } else {
        setCompletedListings(prev => [...prev, listing]);
      }
    };

    window.addEventListener(
      'import-complete',
      handleImportComplete as EventListener
    );

    return () => {
      window.removeEventListener(
        'import-complete',
        handleImportComplete as EventListener
      );
    };
  }, []);

  const handlePartialComplete = () => {
    if (partialListing) {
      setCompletedListings(prev => [...prev, partialListing]);
      setPartialListing(null);

      // Invalidate queries to refresh listings
      queryClient.invalidateQueries({ queryKey: ['listings'] });
    }
  };

  const handlePartialSkip = () => {
    setPartialListing(null);
  };

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-bold">Import Listings</h1>

      {/* Import Progress Component */}
      <ImportProgress
        completedListings={completedListings}
        onPartialEncountered={setPartialListing}
      />

      {/* Modal for completing partial import */}
      {partialListing && (
        <PartialImportModal
          listing={partialListing}
          onComplete={handlePartialComplete}
          onSkip={handlePartialSkip}
        />
      )}

      {/* Results section */}
      {completedListings.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">
            Imported Listings ({completedListings.length})
          </h2>
          {/* Display completed listings */}
        </div>
      )}
    </div>
  );
}
```

### Acceptance Criteria

- [ ] Modal shows when partial import detected
- [ ] Modal closes after successful completion
- [ ] Modal can be skipped, returns to import flow
- [ ] Completed listings tracked and displayed
- [ ] Query cache invalidated after completion
- [ ] Import flow continues after modal close
- [ ] Multiple partial imports can be completed in sequence
- [ ] Error handling works (shows error message, doesn't crash)

### Testing

```typescript
// apps/web/app/dashboard/import/__tests__/page.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ImportPage from '../page';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

describe('ImportPage', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  it('shows partial import modal when event dispatched', async () => {
    renderWithProviders(<ImportPage />);

    const mockListing = {
      id: 1,
      title: 'Test PC',
      quality: 'partial',
      price_usd: null,
    };

    window.dispatchEvent(
      new CustomEvent('import-complete', {
        detail: { listing: mockListing, quality: 'partial' },
      })
    );

    await waitFor(() => {
      expect(screen.getByText('Complete Listing Import')).toBeInTheDocument();
    });
  });

  it('closes modal and continues import after completion', async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    );

    renderWithProviders(<ImportPage />);

    const mockListing = {
      id: 1,
      title: 'Test PC',
      quality: 'partial',
      price_usd: null,
    };

    window.dispatchEvent(
      new CustomEvent('import-complete', {
        detail: { listing: mockListing, quality: 'partial' },
      })
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/Listing price/)).toBeInTheDocument();
    });

    const input = screen.getByLabelText(/Listing price/);
    const submitButton = screen.getByText('Save & Complete');

    await user.type(input, '299.99');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.queryByText('Complete Listing Import')).not.toBeInTheDocument();
    });
  });

  it('closes modal on skip', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ImportPage />);

    const mockListing = {
      id: 1,
      title: 'Test PC',
      quality: 'partial',
      price_usd: null,
    };

    window.dispatchEvent(
      new CustomEvent('import-complete', {
        detail: { listing: mockListing, quality: 'partial' },
      })
    );

    await waitFor(() => {
      expect(screen.getByText('Complete Listing Import')).toBeInTheDocument();
    });

    const skipButton = screen.getByText('Skip for Now');
    await user.click(skipButton);

    await waitFor(() => {
      expect(screen.queryByText('Complete Listing Import')).not.toBeInTheDocument();
    });
  });
});
```

---

## Integration Testing for Phase 3

### Modal + API Integration Test

```typescript
// apps/web/__tests__/phase3_integration.test.tsx
async function test_e2e_partial_import_flow() {
  /**
   * Tests complete flow:
   * 1. User imports URL
   * 2. System extracts partial data
   * 3. Modal appears
   * 4. User enters price
   * 5. API completes import
   * 6. Modal closes, listing added to results
   */
  const { render } = renderWithMocks();

  // ... test implementation
}
```

---

## Accessibility Checklist

- [ ] Modal properly labeled with aria-labelledby
- [ ] Form inputs have associated labels
- [ ] Error messages have role="alert"
- [ ] All buttons keyboard accessible
- [ ] Focus outline visible
- [ ] Color not only indicator (error + text)
- [ ] Sufficient color contrast (WCAG AA)
- [ ] Read-only section marked appropriately
- [ ] Modal closes with Escape key
- [ ] Tab order logical

---

## Success Criteria

All of the following must be true to consider Phase 3 complete:

- [ ] PartialImportModal component renders correctly
- [ ] Modal displays all extracted data read-only
- [ ] Price input validates and shows errors
- [ ] API call made on submit with correct format
- [ ] Modal closes on success
- [ ] Modal can be skipped
- [ ] Integrated into import page flow
- [ ] All tests pass (unit + integration)
- [ ] Component accessible (WCAG AA compliant)
- [ ] Responsive on all device sizes
- [ ] Multiple partial imports handled sequentially
- [ ] Ready to proceed to Phase 4 (Real-Time Updates)
