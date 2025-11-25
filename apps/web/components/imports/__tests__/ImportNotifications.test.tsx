import { render, screen, waitFor } from '@testing-library/react';
import { ImportNotifications } from '../ImportNotifications';
import { useToast } from '@/hooks/use-toast';
import type { BulkImportStatus, PerRowImportStatus } from '@/hooks/useImportPolling';

// Mock the useToast hook
jest.mock('@/hooks/use-toast', () => ({
  useToast: jest.fn(),
}));

describe('ImportNotifications', () => {
  const mockToast = jest.fn();
  const bulkJobId = 'test-job-123';

  beforeEach(() => {
    jest.clearAllMocks();
    (useToast as jest.Mock).mockReturnValue({ toast: mockToast });
  });

  afterEach(() => {
    // Clean up any remaining event listeners
    jest.restoreAllMocks();
  });

  describe('Partial Import Notifications', () => {
    it('should show toast when partial import is found', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      // Emit partial import event
      const partialData: PerRowImportStatus = {
        url: 'https://example.com/listing/123',
        status: 'complete',
        listing_id: 456,
        quality: 'partial',
        error: null,
      };

      window.dispatchEvent(
        new CustomEvent('import-partial-found', { detail: partialData })
      );

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Data Needed',
          description: 'Listing imported with partial data. Please complete the missing information.',
          variant: 'default',
        });
      });
    });

    it('should handle multiple partial import events', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const partial1: PerRowImportStatus = {
        url: 'https://example.com/listing/1',
        status: 'complete',
        listing_id: 1,
        quality: 'partial',
        error: null,
      };

      const partial2: PerRowImportStatus = {
        url: 'https://example.com/listing/2',
        status: 'complete',
        listing_id: 2,
        quality: 'partial',
        error: null,
      };

      window.dispatchEvent(
        new CustomEvent('import-partial-found', { detail: partial1 })
      );

      window.dispatchEvent(
        new CustomEvent('import-partial-found', { detail: partial2 })
      );

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Job Complete Notifications', () => {
    it('should show success toast when all imports succeed', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const completeStatus: BulkImportStatus = {
        bulk_job_id: bulkJobId,
        status: 'complete',
        total_urls: 5,
        completed: 5,
        success: 5,
        partial: 0,
        failed: 0,
        running: 0,
        queued: 0,
        per_row_status: [],
        offset: 0,
        limit: 100,
        has_more: false,
      };

      window.dispatchEvent(
        new CustomEvent('import-job-complete', { detail: completeStatus })
      );

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Import Complete',
          description: 'Successfully imported 5 listings.',
          variant: 'default',
        });
      });
    });

    it('should show partial toast when some imports are partial', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const partialStatus: BulkImportStatus = {
        bulk_job_id: bulkJobId,
        status: 'partial',
        total_urls: 10,
        completed: 10,
        success: 7,
        partial: 3,
        failed: 0,
        running: 0,
        queued: 0,
        per_row_status: [],
        offset: 0,
        limit: 100,
        has_more: false,
      };

      window.dispatchEvent(
        new CustomEvent('import-job-complete', { detail: partialStatus })
      );

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Import Complete',
          description: 'Successfully imported 7 listings, 3 need more data.',
          variant: 'default',
        });
      });
    });

    it('should show failure toast when all imports fail', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const failedStatus: BulkImportStatus = {
        bulk_job_id: bulkJobId,
        status: 'failed',
        total_urls: 3,
        completed: 3,
        success: 0,
        partial: 0,
        failed: 3,
        running: 0,
        queued: 0,
        per_row_status: [],
        offset: 0,
        limit: 100,
        has_more: false,
      };

      window.dispatchEvent(
        new CustomEvent('import-job-complete', { detail: failedStatus })
      );

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Import Failed',
          description: 'All 3 imports failed. Please check the URLs and try again.',
          variant: 'destructive',
        });
      });
    });

    it('should show partial-only toast when only partial imports exist', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const partialOnlyStatus: BulkImportStatus = {
        bulk_job_id: bulkJobId,
        status: 'partial',
        total_urls: 4,
        completed: 4,
        success: 0,
        partial: 4,
        failed: 0,
        running: 0,
        queued: 0,
        per_row_status: [],
        offset: 0,
        limit: 100,
        has_more: false,
      };

      window.dispatchEvent(
        new CustomEvent('import-job-complete', { detail: partialOnlyStatus })
      );

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Import Complete - Data Needed',
          description: '4 listings imported with partial data. Please complete the missing information.',
          variant: 'default',
        });
      });
    });

    it('should show mixed results toast with failures', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const mixedStatus: BulkImportStatus = {
        bulk_job_id: bulkJobId,
        status: 'partial',
        total_urls: 15,
        completed: 15,
        success: 10,
        partial: 3,
        failed: 2,
        running: 0,
        queued: 0,
        per_row_status: [],
        offset: 0,
        limit: 100,
        has_more: false,
      };

      window.dispatchEvent(
        new CustomEvent('import-job-complete', { detail: mixedStatus })
      );

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Import Complete',
          description: 'Successfully imported 10 listings, 3 need more data, 2 failed.',
          variant: 'default',
        });
      });
    });

    it('should handle singular vs plural grammar correctly', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const singleSuccess: BulkImportStatus = {
        bulk_job_id: bulkJobId,
        status: 'complete',
        total_urls: 1,
        completed: 1,
        success: 1,
        partial: 0,
        failed: 0,
        running: 0,
        queued: 0,
        per_row_status: [],
        offset: 0,
        limit: 100,
        has_more: false,
      };

      window.dispatchEvent(
        new CustomEvent('import-job-complete', { detail: singleSuccess })
      );

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Import Complete',
          description: 'Successfully imported 1 listing.',
          variant: 'default',
        });
      });
    });
  });

  describe('Event Listener Cleanup', () => {
    it('should clean up event listeners on unmount', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = render(<ImportNotifications bulkJobId={bulkJobId} />);

      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'import-partial-found',
        expect.any(Function)
      );
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'import-job-complete',
        expect.any(Function)
      );

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'import-partial-found',
        expect.any(Function)
      );
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'import-job-complete',
        expect.any(Function)
      );

      addEventListenerSpy.mockRestore();
      removeEventListenerSpy.mockRestore();
    });
  });

  describe('Component Rendering', () => {
    it('should render nothing (null)', () => {
      const { container } = render(<ImportNotifications bulkJobId={bulkJobId} />);
      expect(container.firstChild).toBeNull();
    });

    it('should not cause re-renders on event emission', () => {
      const { rerender } = render(<ImportNotifications bulkJobId={bulkJobId} />);
      const initialRenderCount = mockToast.mock.calls.length;

      // Emit event
      window.dispatchEvent(
        new CustomEvent('import-partial-found', {
          detail: {
            url: 'https://example.com/listing/1',
            status: 'complete',
            listing_id: 1,
            quality: 'partial',
            error: null,
          } as PerRowImportStatus,
        })
      );

      // Component should not re-render
      rerender(<ImportNotifications bulkJobId={bulkJobId} />);
      expect(mockToast.mock.calls.length).toBeGreaterThan(initialRenderCount);
    });
  });

  describe('TypeScript Type Safety', () => {
    it('should handle custom event detail types correctly', async () => {
      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const partialData: PerRowImportStatus = {
        url: 'https://example.com/listing/123',
        status: 'complete',
        listing_id: 456,
        quality: 'partial',
        error: null,
      };

      // Type-safe event creation
      const event = new CustomEvent<PerRowImportStatus>('import-partial-found', {
        detail: partialData,
      });

      window.dispatchEvent(event);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalled();
      });
    });
  });

  describe('Console Logging', () => {
    it('should log partial import detection for debugging', async () => {
      const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();

      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const partialData: PerRowImportStatus = {
        url: 'https://example.com/listing/123',
        status: 'complete',
        listing_id: 456,
        quality: 'partial',
        error: null,
      };

      window.dispatchEvent(
        new CustomEvent('import-partial-found', { detail: partialData })
      );

      await waitFor(() => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          '[ImportNotifications] Partial import detected:',
          {
            bulkJobId,
            listingId: 456,
            url: 'https://example.com/listing/123',
          }
        );
      });

      consoleLogSpy.mockRestore();
    });

    it('should log job completion for debugging', async () => {
      const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();

      render(<ImportNotifications bulkJobId={bulkJobId} />);

      const completeStatus: BulkImportStatus = {
        bulk_job_id: bulkJobId,
        status: 'complete',
        total_urls: 5,
        completed: 5,
        success: 5,
        partial: 0,
        failed: 0,
        running: 0,
        queued: 0,
        per_row_status: [],
        offset: 0,
        limit: 100,
        has_more: false,
      };

      window.dispatchEvent(
        new CustomEvent('import-job-complete', { detail: completeStatus })
      );

      await waitFor(() => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          '[ImportNotifications] Import job complete:',
          {
            bulkJobId,
            status: 'complete',
            total: 5,
            success: 5,
            partial: 0,
            failed: 0,
          }
        );
      });

      consoleLogSpy.mockRestore();
    });
  });
});
