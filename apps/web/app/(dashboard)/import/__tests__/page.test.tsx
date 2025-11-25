import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ImportPage from '../page';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ListingRecord } from '@/types/listings';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

jest.mock('@/lib/telemetry', () => ({
  telemetry: {
    info: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock the child components to simplify testing
jest.mock('@/components/ingestion/single-url-import-form', () => ({
  SingleUrlImportForm: () => <div data-testid="single-url-form">Single URL Form</div>,
}));

jest.mock('@/components/ingestion/bulk-import-dialog', () => ({
  BulkImportDialog: () => <div data-testid="bulk-dialog">Bulk Dialog</div>,
}));

jest.mock('@/components/import/importer-workspace', () => ({
  ImporterWorkspace: () => <div data-testid="importer-workspace">Importer Workspace</div>,
}));

jest.mock('@/components/imports/PartialImportModal', () => ({
  PartialImportModal: ({ listing, onComplete, onSkip }: {
    listing: ListingRecord;
    onComplete: () => void;
    onSkip: () => void;
  }) => (
    <div data-testid="partial-import-modal">
      <h2>Complete Listing Import</h2>
      <p>Title: {listing.title}</p>
      <label htmlFor="price">Listing price in USD</label>
      <input id="price" type="number" />
      <button onClick={onComplete}>Save &amp; Complete</button>
      <button onClick={onSkip}>Skip for Now</button>
    </div>
  ),
}));

describe('ImportPage - PartialImportModal Integration', () => {
  let queryClient: QueryClient;
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    originalFetch = global.fetch;
    global.fetch = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  const dispatchImportCompleteEvent = (listing: ListingRecord, quality: string) => {
    act(() => {
      window.dispatchEvent(
        new CustomEvent('import-complete', {
          detail: { listing, quality },
        })
      );
    });
  };

  const createMockListing = (overrides?: Partial<ListingRecord>): ListingRecord => ({
    id: 1,
    title: 'Test PC',
    listing_url: 'https://example.com/listing',
    other_urls: null,
    seller: null,
    price_usd: 0,
    adjusted_price_usd: null,
    score_composite: null,
    score_cpu_multi: null,
    score_cpu_single: null,
    score_gpu: null,
    dollar_per_cpu_mark: null,
    dollar_per_single_mark: null,
    condition: 'new',
    status: 'active',
    cpu_id: null,
    cpu_name: null,
    gpu_id: null,
    gpu_name: null,
    ram_gb: 16,
    ram_spec_id: null,
    ram_spec: null,
    ram_type: null,
    ram_speed_mhz: null,
    primary_storage_gb: 512,
    primary_storage_type: 'SSD',
    primary_storage_profile_id: null,
    primary_storage_profile: null,
    secondary_storage_gb: null,
    secondary_storage_type: null,
    secondary_storage_profile_id: null,
    secondary_storage_profile: null,
    manufacturer: null,
    series: null,
    model_number: null,
    form_factor: null,
    thumbnail_url: null,
    valuation_breakdown: null,
    cpu: {
      id: 1,
      name: 'Intel i5-12400',
      manufacturer: 'Intel',
      socket: null,
      cores: 6,
      threads: 12,
      tdp_w: null,
      igpu_model: null,
      cpu_mark_multi: null,
      cpu_mark_single: null,
      igpu_mark: null,
      release_year: null,
      notes: null,
    },
    gpu: null,
    ports_profile: null,
    attributes: {},
    ruleset_id: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  });

  describe('Event Listening', () => {
    it('shows partial import modal when import-complete event dispatched with quality=partial', async () => {
      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing();

      dispatchImportCompleteEvent(mockListing, 'partial');

      await waitFor(() => {
        expect(screen.getByTestId('partial-import-modal')).toBeInTheDocument();
        expect(screen.getByText('Complete Listing Import')).toBeInTheDocument();
        expect(screen.getByText('Title: Test PC')).toBeInTheDocument();
      });
    });

    it('does not show modal when quality is not partial', async () => {
      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing();

      dispatchImportCompleteEvent(mockListing, 'complete');

      await waitFor(() => {
        expect(screen.queryByTestId('partial-import-modal')).not.toBeInTheDocument();
      });
    });

    it('adds complete listings to completed list', async () => {
      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing();

      dispatchImportCompleteEvent(mockListing, 'complete');

      await waitFor(() => {
        expect(screen.getByText('Imported Listings (1)')).toBeInTheDocument();
        expect(screen.getByText('Test PC')).toBeInTheDocument();
      });
    });

    it('handles multiple partial imports sequentially', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ImportPage />);

      const listing1 = createMockListing({ id: 1, title: 'First PC' });
      const listing2 = createMockListing({ id: 2, title: 'Second PC' });

      // Dispatch first partial import
      dispatchImportCompleteEvent(listing1, 'partial');

      await waitFor(() => {
        expect(screen.getByText('Title: First PC')).toBeInTheDocument();
      });

      // Skip first modal
      const skipButton = screen.getByText('Skip for Now');
      await user.click(skipButton);

      await waitFor(() => {
        expect(screen.queryByTestId('partial-import-modal')).not.toBeInTheDocument();
      });

      // Dispatch second partial import
      dispatchImportCompleteEvent(listing2, 'partial');

      await waitFor(() => {
        expect(screen.getByTestId('partial-import-modal')).toBeInTheDocument();
        expect(screen.getByText('Title: Second PC')).toBeInTheDocument();
      });
    });
  });

  describe('Completion Flow', () => {
    it('closes modal and adds to completed list after completion', async () => {
      const user = userEvent.setup();

      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        } as Response)
      );

      const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing();

      dispatchImportCompleteEvent(mockListing, 'partial');

      await waitFor(() => {
        expect(screen.getByTestId('partial-import-modal')).toBeInTheDocument();
      });

      const completeButton = screen.getByText('Save & Complete');
      await user.click(completeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('partial-import-modal')).not.toBeInTheDocument();
      });

      // Check that listing was added to completed list
      expect(screen.getByText('Imported Listings (1)')).toBeInTheDocument();
      expect(screen.getByText('Test PC')).toBeInTheDocument();

      // Check that queries were invalidated
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['listings'] });
    });

    it('invalidates React Query cache after completion', async () => {
      const user = userEvent.setup();

      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        } as Response)
      );

      const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing();

      dispatchImportCompleteEvent(mockListing, 'partial');

      await waitFor(() => {
        expect(screen.getByTestId('partial-import-modal')).toBeInTheDocument();
      });

      const completeButton = screen.getByText('Save & Complete');
      await user.click(completeButton);

      await waitFor(() => {
        expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['listings'] });
      });
    });
  });

  describe('Skip Flow', () => {
    it('closes modal without adding to completed list on skip', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing();

      dispatchImportCompleteEvent(mockListing, 'partial');

      await waitFor(() => {
        expect(screen.getByTestId('partial-import-modal')).toBeInTheDocument();
      });

      const skipButton = screen.getByText('Skip for Now');
      await user.click(skipButton);

      await waitFor(() => {
        expect(screen.queryByTestId('partial-import-modal')).not.toBeInTheDocument();
      });

      // Should not show completed listings section
      expect(screen.queryByText('Imported Listings')).not.toBeInTheDocument();
    });

    it('does not invalidate queries on skip', async () => {
      const user = userEvent.setup();

      const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing();

      dispatchImportCompleteEvent(mockListing, 'partial');

      await waitFor(() => {
        expect(screen.getByTestId('partial-import-modal')).toBeInTheDocument();
      });

      const skipButton = screen.getByText('Skip for Now');
      await user.click(skipButton);

      await waitFor(() => {
        expect(screen.queryByTestId('partial-import-modal')).not.toBeInTheDocument();
      });

      // Queries should not be invalidated on skip
      expect(invalidateQueriesSpy).not.toHaveBeenCalled();
    });
  });

  describe('Event Listener Cleanup', () => {
    it('removes event listener on unmount', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = renderWithProviders(<ImportPage />);

      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'import-complete',
        expect.any(Function)
      );

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'import-complete',
        expect.any(Function)
      );
    });
  });

  describe('Completed Listings Display', () => {
    it('displays completed listings with correct information', async () => {
      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing({
        title: 'Gaming PC',
        cpu: {
          id: 1,
          name: 'AMD Ryzen 5 5600X',
          manufacturer: 'AMD',
          socket: null,
          cores: 6,
          threads: 12,
          tdp_w: null,
          igpu_model: null,
          cpu_mark_multi: null,
          cpu_mark_single: null,
          igpu_mark: null,
          release_year: null,
          notes: null,
        },
        ram_gb: 32,
        price_usd: 599.99,
      });

      dispatchImportCompleteEvent(mockListing, 'complete');

      await waitFor(() => {
        expect(screen.getByText('Gaming PC')).toBeInTheDocument();
        expect(screen.getByText(/CPU: AMD Ryzen 5 5600X/)).toBeInTheDocument();
        expect(screen.getByText(/RAM: 32GB/)).toBeInTheDocument();
        expect(screen.getByText(/\$599.99/)).toBeInTheDocument();
      });
    });

    it('increments count when multiple listings completed', async () => {
      renderWithProviders(<ImportPage />);

      const listing1 = createMockListing({ id: 1, title: 'PC 1' });
      const listing2 = createMockListing({ id: 2, title: 'PC 2' });
      const listing3 = createMockListing({ id: 3, title: 'PC 3' });

      dispatchImportCompleteEvent(listing1, 'complete');

      await waitFor(() => {
        expect(screen.getByText('Imported Listings (1)')).toBeInTheDocument();
      });

      dispatchImportCompleteEvent(listing2, 'complete');

      await waitFor(() => {
        expect(screen.getByText('Imported Listings (2)')).toBeInTheDocument();
      });

      dispatchImportCompleteEvent(listing3, 'complete');

      await waitFor(() => {
        expect(screen.getByText('Imported Listings (3)')).toBeInTheDocument();
      });
    });
  });

  describe('TypeScript Type Safety', () => {
    it('handles events with correct custom event typing', async () => {
      renderWithProviders(<ImportPage />);

      const mockListing = createMockListing();

      // This should not cause TypeScript errors
      const event = new CustomEvent<{
        listing: ListingRecord;
        quality: string;
      }>('import-complete', {
        detail: { listing: mockListing, quality: 'partial' },
      });

      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(screen.getByTestId('partial-import-modal')).toBeInTheDocument();
      });
    });
  });
});
