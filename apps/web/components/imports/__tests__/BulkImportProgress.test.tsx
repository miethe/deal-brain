import { render, screen } from '@testing-library/react';
import { BulkImportProgress } from '../BulkImportProgress';
import { BulkImportStatus } from '@/hooks/useImportPolling';

describe('BulkImportProgress', () => {
  const mockStatus: BulkImportStatus = {
    bulk_job_id: 'test-123',
    status: 'running',
    total_urls: 10,
    completed: 5,
    success: 3,
    partial: 2,
    failed: 0,
    running: 5,
    queued: 0,
    per_row_status: [
      {
        url: 'https://example.com/1',
        status: 'complete',
        listing_id: 1,
        quality: 'full',
        error: null,
      },
      {
        url: 'https://example.com/2',
        status: 'complete',
        listing_id: 2,
        quality: 'partial',
        error: null,
      },
      {
        url: 'https://example.com/3',
        status: 'running',
        listing_id: null,
        quality: null,
        error: null,
      },
      {
        url: 'https://example.com/4',
        status: 'queued',
        listing_id: null,
        quality: null,
        error: null,
      },
      {
        url: 'https://example.com/5',
        status: 'failed',
        listing_id: null,
        quality: null,
        error: 'Invalid URL format',
      },
    ],
    offset: 0,
    limit: 20,
    has_more: false,
  };

  it('displays progress percentage correctly', () => {
    render(<BulkImportProgress status={mockStatus} />);

    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('displays status counts in grid', () => {
    render(<BulkImportProgress status={mockStatus} />);

    // Check labels
    expect(screen.getByText('Total')).toBeInTheDocument();
    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('Partial')).toBeInTheDocument();
    expect(screen.getByText('Running')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();

    // Check values
    expect(screen.getByText('10')).toBeInTheDocument(); // total_urls
    expect(screen.getByText('3')).toBeInTheDocument(); // success
    expect(screen.getByText('2')).toBeInTheDocument(); // partial
    expect(screen.getByText('5')).toBeInTheDocument(); // running
    expect(screen.getByText('0')).toBeInTheDocument(); // failed
  });

  it('displays header with total and completed counts', () => {
    render(<BulkImportProgress status={mockStatus} />);

    expect(screen.getByText('Bulk Import Progress')).toBeInTheDocument();
    expect(screen.getByText('10 URLs - 5 completed')).toBeInTheDocument();
  });

  it('shows per-row status for recent imports', () => {
    render(<BulkImportProgress status={mockStatus} />);

    expect(screen.getByText('Recent Imports')).toBeInTheDocument();
    expect(screen.getByText('https://example.com/1')).toBeInTheDocument();
    expect(screen.getByText('https://example.com/2')).toBeInTheDocument();
  });

  it('displays quality badges correctly', () => {
    render(<BulkImportProgress status={mockStatus} />);

    // Full quality badge
    expect(screen.getByText('Complete')).toBeInTheDocument();

    // Partial quality badge
    expect(screen.getByText('Needs Data')).toBeInTheDocument();
  });

  it('displays status badges for each row', () => {
    render(<BulkImportProgress status={mockStatus} />);

    // Check for status text (may appear multiple times)
    expect(screen.getAllByText('complete').length).toBeGreaterThan(0);
    expect(screen.getAllByText('running').length).toBeGreaterThan(0);
    expect(screen.getAllByText('queued').length).toBeGreaterThan(0);
    expect(screen.getAllByText('failed').length).toBeGreaterThan(0);
  });

  it('truncates long URLs and shows full URL in title attribute', () => {
    const longUrlStatus: BulkImportStatus = {
      ...mockStatus,
      per_row_status: [
        {
          url: 'https://example.com/very-long-url-that-should-be-truncated-for-display-purposes',
          status: 'complete',
          listing_id: 1,
          quality: 'full',
          error: null,
        },
      ],
    };

    render(<BulkImportProgress status={longUrlStatus} />);

    const urlElement = screen.getByTitle(
      'https://example.com/very-long-url-that-should-be-truncated-for-display-purposes'
    );
    expect(urlElement).toBeInTheDocument();
  });

  it('limits per-row display to first 5 items', () => {
    const manyRowsStatus: BulkImportStatus = {
      ...mockStatus,
      per_row_status: Array.from({ length: 10 }, (_, i) => ({
        url: `https://example.com/${i}`,
        status: 'complete' as const,
        listing_id: i,
        quality: 'full' as const,
        error: null,
      })),
    };

    render(<BulkImportProgress status={manyRowsStatus} />);

    // Should show "and 5 more" message
    expect(screen.getByText('... and 5 more')).toBeInTheDocument();
  });

  it('displays completion message when status is complete', () => {
    const completeStatus: BulkImportStatus = {
      ...mockStatus,
      status: 'complete',
      completed: 10,
      success: 8,
      partial: 2,
      running: 0,
    };

    render(<BulkImportProgress status={completeStatus} />);

    expect(
      screen.getByText(/Import completed! 2 listing\(s\) need data completion\./)
    ).toBeInTheDocument();
  });

  it('does not show completion message when still running', () => {
    render(<BulkImportProgress status={mockStatus} />);

    expect(
      screen.queryByText(/Import completed!/)
    ).not.toBeInTheDocument();
  });

  it('handles zero total URLs gracefully', () => {
    const emptyStatus: BulkImportStatus = {
      ...mockStatus,
      total_urls: 0,
      completed: 0,
      success: 0,
      partial: 0,
      failed: 0,
      running: 0,
      queued: 0,
      per_row_status: [],
    };

    render(<BulkImportProgress status={emptyStatus} />);

    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(screen.getByText('0 URLs - 0 completed')).toBeInTheDocument();
  });

  it('does not show recent imports section when no rows', () => {
    const noRowsStatus: BulkImportStatus = {
      ...mockStatus,
      per_row_status: [],
    };

    render(<BulkImportProgress status={noRowsStatus} />);

    expect(screen.queryByText('Recent Imports')).not.toBeInTheDocument();
  });

  it('renders with loading state', () => {
    const { container } = render(
      <BulkImportProgress status={mockStatus} isLoading={true} />
    );

    // Component should still render when loading
    expect(container).toBeTruthy();
    expect(screen.getByText('Bulk Import Progress')).toBeInTheDocument();
  });

  it('calculates progress percentage correctly for partial completion', () => {
    const partialStatus: BulkImportStatus = {
      ...mockStatus,
      total_urls: 100,
      completed: 37,
    };

    render(<BulkImportProgress status={partialStatus} />);

    expect(screen.getByText('37%')).toBeInTheDocument();
  });

  it('shows 100% when all URLs are completed', () => {
    const fullCompleteStatus: BulkImportStatus = {
      ...mockStatus,
      total_urls: 20,
      completed: 20,
      success: 18,
      partial: 2,
      running: 0,
      queued: 0,
      status: 'complete',
    };

    render(<BulkImportProgress status={fullCompleteStatus} />);

    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('applies accessible color classes for WCAG AA compliance', () => {
    const { container } = render(<BulkImportProgress status={mockStatus} />);

    // Check that status cards have background colors
    expect(container.querySelector('.bg-green-50')).toBeInTheDocument();
    expect(container.querySelector('.bg-yellow-50')).toBeInTheDocument();
    expect(container.querySelector('.bg-blue-50')).toBeInTheDocument();
    expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
  });

  it('displays pending badge when quality is null', () => {
    const pendingStatus: BulkImportStatus = {
      ...mockStatus,
      per_row_status: [
        {
          url: 'https://example.com/pending',
          status: 'queued',
          listing_id: null,
          quality: null,
          error: null,
        },
      ],
    };

    render(<BulkImportProgress status={pendingStatus} />);

    expect(screen.getByText('Pending')).toBeInTheDocument();
  });
});
