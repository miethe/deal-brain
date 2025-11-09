/**
 * PartialImportModal Component Tests
 *
 * Tests for the partial import modal component ensuring:
 * - Correct rendering of extracted data
 * - Price validation and submission
 * - Proper accessibility attributes
 * - Loading states and error handling
 * - Keyboard navigation
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PartialImportModal } from '../PartialImportModal';
import { ListingRecord } from '@/types/listings';

describe('PartialImportModal', () => {
  const mockListing: ListingRecord = {
    id: 1,
    title: 'Dell OptiPlex 7090',
    listing_url: null,
    seller: null,
    price_usd: 0,
    adjusted_price_usd: null,
    score_composite: null,
    score_cpu_multi: null,
    score_cpu_single: null,
    score_gpu: null,
    dollar_per_cpu_mark: null,
    dollar_per_single_mark: null,
    condition: 'refurbished',
    status: 'active',
    cpu_id: 1,
    cpu_name: 'Intel Core i5-10500',
    cpu: {
      id: 1,
      name: 'Intel Core i5-10500',
      manufacturer: 'Intel',
      socket: null,
      cores: 6,
      threads: 12,
      tdp_w: 65,
      igpu_model: null,
      cpu_mark_multi: null,
      cpu_mark_single: null,
      igpu_mark: null,
      release_year: null,
      notes: null,
    },
    ram_gb: 8,
    primary_storage_gb: 256,
    primary_storage_type: 'SSD',
    attributes: {},
    created_at: '2025-11-08T00:00:00Z',
    updated_at: '2025-11-08T00:00:00Z',
  };

  const mockOnComplete = jest.fn();
  const mockOnSkip = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
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
    expect(screen.getByText(/256GB/)).toBeInTheDocument();
    expect(screen.getByText(/refurbished/i)).toBeInTheDocument();
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
    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const submitButton = screen.getByText('Save & Complete');

    // Button should be disabled when price is empty
    expect(submitButton).toBeDisabled();

    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('submits valid price', async () => {
    const user = userEvent.setup();

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response)
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
      expect.stringContaining('/api/v1/listings/1/complete'),
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ price: 299.99 }),
      })
    );
  });

  it('disables submit button while loading', async () => {
    const user = userEvent.setup();

    let resolveRequest: (value: any) => void = () => {};
    global.fetch = jest.fn(
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

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid price' }),
      } as Response)
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

    // Enter invalid price to trigger error
    await user.type(input, '-100');
    await user.click(submitButton);
    expect(screen.getByText(/must be a positive number/)).toBeInTheDocument();

    // Clear input and type valid price
    await user.clear(input);
    await user.type(input, '299.99');
    expect(screen.queryByText(/must be a positive number/)).not.toBeInTheDocument();
  });

  it('handles Enter key for submission', async () => {
    const user = userEvent.setup();

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response)
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

  it('renders all extracted fields when present', () => {
    const listingWithGpu: ListingRecord = {
      ...mockListing,
      gpu: {
        id: 1,
        name: 'NVIDIA GeForce GTX 1650',
      },
    };

    render(
      <PartialImportModal
        listing={listingWithGpu}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText('Dell OptiPlex 7090')).toBeInTheDocument();
    expect(screen.getByText(/Intel Core i5-10500/)).toBeInTheDocument();
    expect(screen.getByText('8GB')).toBeInTheDocument();
    expect(screen.getByText(/256GB/)).toBeInTheDocument();
    expect(screen.getByText(/refurbished/i)).toBeInTheDocument();
    expect(screen.getByText('NVIDIA GeForce GTX 1650')).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);

    expect(input).toHaveAttribute('aria-required', 'true');
    expect(input).toHaveAttribute('aria-invalid', 'false');
    expect(input).toHaveAttribute('aria-label', 'Listing price in USD');

    // Check that required indicator is present
    expect(screen.getByText('*')).toHaveAttribute('aria-label', 'required');
  });

  it('shows error with proper aria attributes', async () => {
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

    // Enter invalid price to trigger error
    await user.type(input, '-100');
    await user.click(submitButton);

    const errorMessage = screen.getByText(/must be a positive number/);
    expect(errorMessage).toHaveAttribute('role', 'alert');
    expect(errorMessage).toHaveAttribute('id', 'price-error');

    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', 'price-error');
  });

  it('disables inputs while loading', async () => {
    const user = userEvent.setup();

    let resolveRequest: (value: any) => void = () => {};
    global.fetch = jest.fn(
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
    const skipButton = screen.getByText('Skip for Now');

    await user.type(input, '299.99');
    await user.click(submitButton);

    expect(input).toBeDisabled();
    expect(submitButton).toBeDisabled();
    expect(skipButton).toBeDisabled();

    resolveRequest({ ok: true, json: () => Promise.resolve({}) });

    await waitFor(() => expect(mockOnComplete).toHaveBeenCalled());
  });

  it('validates zero price', async () => {
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

    await user.type(input, '0');
    await user.click(submitButton);

    expect(
      screen.getByText(/must be a positive number/)
    ).toBeInTheDocument();
    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('validates non-numeric input', async () => {
    const user = userEvent.setup();

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);

    // Type non-numeric input - the number input should prevent this or result in empty value
    await user.type(input, 'abc');

    // Submit button should be disabled since input is effectively empty
    const submitButton = screen.getByText('Save & Complete');
    expect(submitButton).toBeDisabled();

    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('handles network errors gracefully', async () => {
    const user = userEvent.setup();

    global.fetch = jest.fn(() =>
      Promise.reject(new Error('Network error'))
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
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('prevents Enter key submission when empty', async () => {
    const user = userEvent.setup();

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response)
    );

    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const input = screen.getByLabelText(/Listing price in USD/);
    await user.type(input, '{Enter}');

    // Should not call the API or complete
    expect(global.fetch).not.toHaveBeenCalled();
    expect(mockOnComplete).not.toHaveBeenCalled();
  });

  it('prevents Enter key submission while loading', async () => {
    const user = userEvent.setup();

    let resolveRequest: (value: any) => void = () => {};
    global.fetch = jest.fn(
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

    await user.type(input, '299.99{Enter}');

    // Try pressing Enter again while loading
    await user.type(input, '{Enter}');

    // Should only be called once
    expect(global.fetch).toHaveBeenCalledTimes(1);

    resolveRequest({ ok: true, json: () => Promise.resolve({}) });

    await waitFor(() => expect(mockOnComplete).toHaveBeenCalled());
  });
});
