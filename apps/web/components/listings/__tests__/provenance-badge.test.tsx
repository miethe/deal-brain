/**
 * Provenance Badge Component Tests
 *
 * Tests for the provenance badge components ensuring:
 * - Correct rendering for all source types
 * - Proper accessibility attributes
 * - Color-coded styling
 * - Icon display
 */

import { render, screen } from '@testing-library/react';
import { ProvenanceBadge } from '../provenance-badge';
import { QualityIndicator } from '../quality-indicator';
import { LastSeenTimestamp } from '../last-seen-timestamp';
import { ListingProvenanceDisplay } from '../listing-provenance-display';

describe('ProvenanceBadge', () => {
  it('renders eBay API badge with correct label and icon', () => {
    render(<ProvenanceBadge provenance="ebay_api" />);
    expect(screen.getByLabelText(/Data from eBay API/i)).toBeInTheDocument();
    expect(screen.getByText('eBay API')).toBeInTheDocument();
  });

  it('renders JSON-LD badge', () => {
    render(<ProvenanceBadge provenance="jsonld" />);
    expect(screen.getByLabelText(/Data from JSON-LD/i)).toBeInTheDocument();
    expect(screen.getByText('Structured Data')).toBeInTheDocument();
  });

  it('renders scraper badge', () => {
    render(<ProvenanceBadge provenance="scraper" />);
    expect(screen.getByLabelText(/Data from web scraper/i)).toBeInTheDocument();
    expect(screen.getByText('Web Scraper')).toBeInTheDocument();
  });

  it('renders excel badge', () => {
    render(<ProvenanceBadge provenance="excel" />);
    expect(screen.getByLabelText(/Data from Excel/i)).toBeInTheDocument();
    expect(screen.getByText('Excel Import')).toBeInTheDocument();
  });

  it('hides label when showLabel is false', () => {
    render(<ProvenanceBadge provenance="ebay_api" showLabel={false} />);
    expect(screen.queryByText('eBay API')).not.toBeInTheDocument();
  });
});

describe('QualityIndicator', () => {
  it('renders full quality badge', () => {
    render(<QualityIndicator quality="full" />);
    expect(
      screen.getByLabelText(/Data quality: Full - all required fields present/i)
    ).toBeInTheDocument();
    expect(screen.getByText('Full')).toBeInTheDocument();
  });

  it('renders partial quality badge', () => {
    render(<QualityIndicator quality="partial" missingFields={['RAM Size']} />);
    expect(screen.getByLabelText(/Data quality: Partial/i)).toBeInTheDocument();
    expect(screen.getByText('Partial')).toBeInTheDocument();
  });

  it('shows missing fields in tooltip for partial quality', async () => {
    const { user } = render(
      <QualityIndicator
        quality="partial"
        missingFields={['RAM Size', 'Storage Type']}
      />
    );

    const badge = screen.getByLabelText(/Data quality: Partial/i);
    await user.hover(badge);

    expect(await screen.findByText('Missing Fields:')).toBeInTheDocument();
    expect(screen.getByText('RAM Size')).toBeInTheDocument();
    expect(screen.getByText('Storage Type')).toBeInTheDocument();
  });

  it('hides label when showLabel is false', () => {
    render(<QualityIndicator quality="full" showLabel={false} />);
    expect(screen.queryByText('Full')).not.toBeInTheDocument();
  });
});

describe('LastSeenTimestamp', () => {
  it('renders relative timestamp', () => {
    const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString();
    render(<LastSeenTimestamp lastSeenAt={twoDaysAgo} />);

    expect(screen.getByText(/Last seen/i)).toBeInTheDocument();
    expect(screen.getByText(/2 days ago/i)).toBeInTheDocument();
  });

  it('shows exact datetime in tooltip', async () => {
    const testDate = new Date('2025-04-27T10:30:00Z').toISOString();
    const { user } = render(<LastSeenTimestamp lastSeenAt={testDate} />);

    const timestamp = screen.getByText(/Last seen/i);
    await user.hover(timestamp);

    expect(await screen.findByText('Last Seen')).toBeInTheDocument();
  });

  it('hides icon when showIcon is false', () => {
    const testDate = new Date().toISOString();
    const { container } = render(
      <LastSeenTimestamp lastSeenAt={testDate} showIcon={false} />
    );

    // Check that no clock icon is rendered
    expect(container.querySelector('svg[class*="lucide-clock"]')).not.toBeInTheDocument();
  });

  it('uses semantic time element', () => {
    const testDate = new Date('2025-04-27T10:30:00Z').toISOString();
    render(<LastSeenTimestamp lastSeenAt={testDate} />);

    const timeElement = screen.getByRole('time');
    expect(timeElement).toBeInTheDocument();
    expect(timeElement).toHaveAttribute('datetime', testDate);
  });
});

describe('ListingProvenanceDisplay', () => {
  const testDate = new Date('2025-04-27T10:30:00Z').toISOString();

  it('renders all components in horizontal layout', () => {
    render(
      <ListingProvenanceDisplay
        provenance="ebay_api"
        quality="full"
        lastSeenAt={testDate}
      />
    );

    expect(screen.getByText('eBay API')).toBeInTheDocument();
    expect(screen.getByText('Full')).toBeInTheDocument();
    expect(screen.getByText(/Last seen/i)).toBeInTheDocument();
  });

  it('renders in vertical layout', () => {
    const { container } = render(
      <ListingProvenanceDisplay
        provenance="jsonld"
        quality="full"
        lastSeenAt={testDate}
        layout="vertical"
      />
    );

    const wrapper = container.querySelector('[role="group"]');
    expect(wrapper).toHaveClass('flex-col');
  });

  it('renders in compact mode', () => {
    render(
      <ListingProvenanceDisplay
        provenance="scraper"
        quality="full"
        lastSeenAt={testDate}
        compact
      />
    );

    // Labels should be hidden in compact mode
    expect(screen.queryByText('Web Scraper')).not.toBeInTheDocument();
    expect(screen.queryByText('Full')).not.toBeInTheDocument();
  });

  it('respects showSource prop', () => {
    render(
      <ListingProvenanceDisplay
        provenance="ebay_api"
        quality="full"
        lastSeenAt={testDate}
        showSource={false}
      />
    );

    expect(screen.queryByText('eBay API')).not.toBeInTheDocument();
    expect(screen.getByText('Full')).toBeInTheDocument();
  });

  it('respects showQuality prop', () => {
    render(
      <ListingProvenanceDisplay
        provenance="excel"
        lastSeenAt={testDate}
        showQuality={false}
      />
    );

    expect(screen.getByText('Excel Import')).toBeInTheDocument();
    expect(screen.queryByText('Full')).not.toBeInTheDocument();
    expect(screen.queryByText('Partial')).not.toBeInTheDocument();
  });

  it('respects showTimestamp prop', () => {
    render(
      <ListingProvenanceDisplay
        provenance="jsonld"
        quality="full"
        lastSeenAt={testDate}
        showTimestamp={false}
      />
    );

    expect(screen.queryByText(/Last seen/i)).not.toBeInTheDocument();
  });

  it('has proper accessibility group label', () => {
    render(
      <ListingProvenanceDisplay
        provenance="ebay_api"
        quality="full"
        lastSeenAt={testDate}
      />
    );

    const group = screen.getByRole('group');
    expect(group).toHaveAttribute('aria-label');
    expect(group.getAttribute('aria-label')).toContain('ebay api');
  });
});
