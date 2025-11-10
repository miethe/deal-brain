/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DetailPanel } from '@/app/cpus/_components/master-detail-view/detail-panel';
import type { CPURecord, CPUDetail, ListingPreview } from '@/types/cpus';

// Mock Zustand store
const mockToggleCompare = jest.fn();
let mockCompareSelections: number[] = [];

jest.mock('@/stores/cpu-catalog-store', () => ({
  useCPUCatalogStore: jest.fn((selector) => {
    const state = {
      toggleCompare: mockToggleCompare,
      compareSelections: mockCompareSelections,
    };
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

// Mock child components
jest.mock('@/app/cpus/_components/grid-view/performance-badge', () => ({
  PerformanceBadge: ({ label, value }: any) => (
    <div data-testid={`performance-badge-${label}`}>{label}: {value}</div>
  ),
}));

jest.mock('@/app/cpus/_components/price-targets', () => ({
  PriceTargets: ({ priceTargetGood, variant }: any) => (
    <div data-testid="price-targets">Price: ${priceTargetGood} [{variant}]</div>
  ),
}));

jest.mock('@/app/cpus/_components/performance-value-badge', () => ({
  PerformanceValueBadge: ({ rating, metricType }: any) => (
    <div data-testid={`perf-value-badge-${metricType}`}>Rating: {rating}</div>
  ),
}));

jest.mock('@/app/cpus/_components/master-detail-view/kpi-metric', () => ({
  KpiMetric: ({ label, value }: any) => (
    <div data-testid={`kpi-${label}`}>{label}: {value}</div>
  ),
}));

jest.mock('@/app/cpus/_components/master-detail-view/key-value', () => ({
  KeyValue: ({ label, value }: any) => (
    <div data-testid={`key-value-${label}`}>{label}: {value}</div>
  ),
}));

const createMockCPU = (overrides?: Partial<CPURecord>): CPURecord => ({
  id: 1,
  name: 'AMD Ryzen 5 5600X',
  manufacturer: 'AMD',
  socket: 'AM4',
  cores: 6,
  threads: 12,
  tdp_w: 65,
  igpu_model: null,
  release_year: 2020,
  cpu_mark_single: 3500,
  cpu_mark_multi: 22000,
  igpu_mark: null,
  passmark_slug: 'amd-ryzen-5-5600x',
  passmark_category: 'Desktop',
  passmark_id: '4236',
  notes: null,
  attributes_json: {},
  price_target_good: 200,
  price_target_great: 180,
  price_target_fair: 220,
  price_target_sample_size: 12,
  price_target_confidence: 'high',
  price_target_stddev: 20,
  price_target_updated_at: '2025-11-01T00:00:00Z',
  dollar_per_mark_single: 0.0571,
  dollar_per_mark_multi: 0.0091,
  performance_value_percentile: 25,
  performance_value_rating: 'good',
  performance_metrics_updated_at: '2025-11-01T00:00:00Z',
  listings_count: 15,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2025-11-01T00:00:00Z',
  ...overrides,
});

const createMockListing = (overrides?: Partial<ListingPreview>): ListingPreview => ({
  id: 1,
  title: 'Test Listing',
  base_price_usd: 250,
  adjusted_price_usd: 230,
  marketplace: 'eBay',
  condition: 'used',
  url: 'https://example.com',
  status: 'active',
  ...overrides,
});

const createMockCPUDetail = (cpu: CPURecord, overrides?: Partial<CPUDetail>): CPUDetail => ({
  ...cpu,
  associated_listings: [
    createMockListing({ id: 1, title: 'Listing 1', adjusted_price_usd: 180 }),
    createMockListing({ id: 2, title: 'Listing 2', adjusted_price_usd: 200 }),
  ],
  market_data: {
    price_distribution: [180, 190, 200, 210, 220],
  },
  ...overrides,
});

describe('DetailPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Empty State', () => {
    it('shows empty state when no CPU selected', () => {
      render(
        <DetailPanel
          cpu={undefined}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Select a CPU to view details')).toBeInTheDocument();
    });
  });

  describe('Basic CPU Information', () => {
    it('renders CPU name', () => {
      const cpu = createMockCPU();
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('AMD Ryzen 5 5600X')).toBeInTheDocument();
    });

    it('renders manufacturer badge', () => {
      const cpu = createMockCPU({ manufacturer: 'Intel' });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Intel')).toBeInTheDocument();
    });

    it('renders socket badge', () => {
      const cpu = createMockCPU({ socket: 'LGA1700' });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('LGA1700')).toBeInTheDocument();
    });

    it('renders release year badge', () => {
      const cpu = createMockCPU({ release_year: 2023 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('2023')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading alert when analytics are loading', () => {
      const cpu = createMockCPU();
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={true}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText(/loading market analytics/i)).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows error alert when analytics fail to load', () => {
      const cpu = createMockCPU();
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={true}
        />
      );

      expect(screen.getByText(/failed to load market analytics/i)).toBeInTheDocument();
      expect(screen.getByText(/basic cpu information shown/i)).toBeInTheDocument();
    });

    it('does not show loading alert when error occurs', () => {
      const cpu = createMockCPU();
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={true}
        />
      );

      expect(screen.queryByText(/loading market analytics/i)).not.toBeInTheDocument();
    });
  });

  describe('KPI Metrics Grid', () => {
    it('renders Good Price KPI', () => {
      const cpu = createMockCPU({ price_target_good: 200 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('kpi-Good Price')).toBeInTheDocument();
      expect(screen.getByText(/Good Price:.*\$200/)).toBeInTheDocument();
    });

    it('renders Great Price KPI', () => {
      const cpu = createMockCPU({ price_target_great: 180 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('kpi-Great Price')).toBeInTheDocument();
      expect(screen.getByText(/Great Price:.*\$180/)).toBeInTheDocument();
    });

    it('renders dollar per ST mark KPI', () => {
      const cpu = createMockCPU({ dollar_per_mark_single: 0.0571 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('kpi-$/ST Mark')).toBeInTheDocument();
    });

    it('renders dollar per MT mark KPI', () => {
      const cpu = createMockCPU({ dollar_per_mark_multi: 0.0091 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('kpi-$/MT Mark')).toBeInTheDocument();
    });
  });

  describe('Price Targets', () => {
    it('renders price targets with detailed variant', () => {
      const cpu = createMockCPU({ price_target_good: 200 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      const priceTargets = screen.getByTestId('price-targets');
      expect(priceTargets).toHaveTextContent('[detailed]');
    });
  });

  describe('Performance Metrics', () => {
    it('renders Performance Metrics heading', () => {
      const cpu = createMockCPU();
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });

    it('renders single-thread performance badge', () => {
      const cpu = createMockCPU({ cpu_mark_single: 3500 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('performance-badge-ST')).toBeInTheDocument();
    });

    it('renders multi-thread performance badge', () => {
      const cpu = createMockCPU({ cpu_mark_multi: 22000 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('performance-badge-MT')).toBeInTheDocument();
    });

    it('renders iGPU badge when available', () => {
      const cpu = createMockCPU({ igpu_mark: 2500 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('performance-badge-iGPU')).toBeInTheDocument();
    });

    it('renders performance value badges', () => {
      const cpu = createMockCPU({
        dollar_per_mark_single: 0.0571,
        dollar_per_mark_multi: 0.0091,
      });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('perf-value-badge-single')).toBeInTheDocument();
      expect(screen.getByTestId('perf-value-badge-multi')).toBeInTheDocument();
    });
  });

  describe('Market Analytics Section', () => {
    it('renders Market Analytics heading when detail data available', () => {
      const cpu = createMockCPU();
      const cpuDetail = createMockCPUDetail(cpu);
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Market Analytics')).toBeInTheDocument();
    });

    it('does not render Market Analytics section without detail data', () => {
      const cpu = createMockCPU();
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.queryByText('Market Analytics')).not.toBeInTheDocument();
    });
  });

  describe('Associated Listings', () => {
    it('renders Top Listings section when listings available', () => {
      const cpu = createMockCPU();
      const cpuDetail = createMockCPUDetail(cpu);
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText(/top listings.*2/i)).toBeInTheDocument();
    });

    it('renders listing titles', () => {
      const cpu = createMockCPU();
      const cpuDetail = createMockCPUDetail(cpu);
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Listing 1')).toBeInTheDocument();
      expect(screen.getByText('Listing 2')).toBeInTheDocument();
    });

    it('renders listing marketplace and condition', () => {
      const cpu = createMockCPU();
      const listings = [
        createMockListing({ id: 1, title: 'Test', marketplace: 'Amazon', condition: 'new' }),
      ];
      const cpuDetail = createMockCPUDetail(cpu, { associated_listings: listings });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText(/amazon.*new/i)).toBeInTheDocument();
    });

    it('shows strikethrough base price when different from adjusted', () => {
      const cpu = createMockCPU();
      const listings = [
        createMockListing({
          id: 1,
          title: 'Test',
          base_price_usd: 250,
          adjusted_price_usd: 230,
        }),
      ];
      const cpuDetail = createMockCPUDetail(cpu, { associated_listings: listings });
      const { container } = render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      // Check for strikethrough styling
      const strikethrough = container.querySelector('.line-through');
      expect(strikethrough).toBeInTheDocument();
    });

    it('limits listings to first 5', () => {
      const cpu = createMockCPU();
      const listings = Array.from({ length: 10 }, (_, i) =>
        createMockListing({ id: i + 1, title: `Listing ${i + 1}` })
      );
      const cpuDetail = createMockCPUDetail(cpu, { associated_listings: listings });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Listing 1')).toBeInTheDocument();
      expect(screen.getByText('Listing 5')).toBeInTheDocument();
      expect(screen.queryByText('Listing 6')).not.toBeInTheDocument();
    });
  });

  describe('CPU Specifications Section', () => {
    it('renders Specifications heading', () => {
      const cpu = createMockCPU();
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Specifications')).toBeInTheDocument();
    });

    it('renders cores and threads specification', () => {
      const cpu = createMockCPU({ cores: 8, threads: 16 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('key-value-Cores / Threads')).toBeInTheDocument();
      expect(screen.getByText(/8 cores.*16 threads/i)).toBeInTheDocument();
    });

    it('renders TDP specification', () => {
      const cpu = createMockCPU({ tdp_w: 125 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('key-value-TDP')).toBeInTheDocument();
      expect(screen.getByText(/125W/)).toBeInTheDocument();
    });

    it('renders socket specification', () => {
      const cpu = createMockCPU({ socket: 'AM5' });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('key-value-Socket')).toBeInTheDocument();
    });

    it('renders iGPU specification when available', () => {
      const cpu = createMockCPU({ igpu_model: 'UHD Graphics 770' });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByTestId('key-value-Integrated GPU')).toBeInTheDocument();
      expect(screen.getByText(/UHD Graphics 770/)).toBeInTheDocument();
    });
  });

  describe('Performance Value Details Section', () => {
    it('renders Performance Value section when rating available', () => {
      const cpu = createMockCPU({ performance_value_rating: 'excellent' });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Performance Value')).toBeInTheDocument();
    });

    it('does not render section when rating is null', () => {
      const cpu = createMockCPU({ performance_value_rating: null });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.queryByText('Performance Value')).not.toBeInTheDocument();
    });
  });

  describe('Notes Section', () => {
    it('renders notes when available', () => {
      const cpu = createMockCPU({ notes: 'This is a test note' });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Notes')).toBeInTheDocument();
      expect(screen.getByText('This is a test note')).toBeInTheDocument();
    });

    it('does not render notes section when null', () => {
      const cpu = createMockCPU({ notes: null });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.queryByText('Notes')).not.toBeInTheDocument();
    });
  });

  describe('PassMark Link', () => {
    it('renders PassMark link when slug available', () => {
      const cpu = createMockCPU({ passmark_slug: 'amd-ryzen-5-5600x' });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      const link = screen.getByText('View on PassMark').closest('a');
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute(
        'href',
        'https://www.cpubenchmark.net/cpu.php?cpu=amd-ryzen-5-5600x'
      );
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('does not render PassMark link when slug is null', () => {
      const cpu = createMockCPU({ passmark_slug: null });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.queryByText('View on PassMark')).not.toBeInTheDocument();
    });
  });

  describe('Compare Button', () => {
    it('renders Compare button', () => {
      const cpu = createMockCPU();
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByRole('button', { name: /compare/i })).toBeInTheDocument();
    });

    it('calls toggleCompare when clicked', () => {
      const cpu = createMockCPU({ id: 42 });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      const compareButton = screen.getByRole('button', { name: /compare/i });
      fireEvent.click(compareButton);

      expect(mockToggleCompare).toHaveBeenCalledWith(42);
    });

    it('shows "Compare" text when not in compare list', () => {
      const cpu = createMockCPU({ id: 1 });
      // mockCompareSelections is empty
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      expect(screen.getByText('Compare')).toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('renders with card container', () => {
      const cpu = createMockCPU();
      const { container } = render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      // Component renders inside a Card
      expect(container.querySelector('[class*="overflow-auto"]')).toBeInTheDocument();
    });
  });

  describe('Charts Rendering', () => {
    it('renders benchmark chart when performance data available', () => {
      const cpu = createMockCPU({
        cpu_mark_single: 3500,
        cpu_mark_multi: 22000,
      });
      const { container } = render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      // Check for chart figure element
      const chartFigure = container.querySelector('figure[role="img"]');
      expect(chartFigure).toBeInTheDocument();
    });

    it('renders price distribution histogram when detail data available', () => {
      const cpu = createMockCPU();
      const cpuDetail = createMockCPUDetail(cpu);
      const { container } = render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      // Check for histogram figure
      const histogramFigure = Array.from(
        container.querySelectorAll('figure[role="img"]')
      ).find((fig) => fig.getAttribute('aria-label')?.includes('distribution'));
      expect(histogramFigure).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles CPU with all null specifications', () => {
      const cpu = createMockCPU({
        socket: null,
        cores: null,
        threads: null,
        tdp_w: null,
        igpu_model: null,
        release_year: null,
      });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={undefined}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      // Should still render basic structure
      expect(screen.getByText('AMD Ryzen 5 5600X')).toBeInTheDocument();
      expect(screen.getByText('Specifications')).toBeInTheDocument();
    });

    it('handles empty price distribution', () => {
      const cpu = createMockCPU();
      const cpuDetail = createMockCPUDetail(cpu, {
        market_data: { price_distribution: [] },
      });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      // Should not crash, Market Analytics should still render
      expect(screen.getByText('Market Analytics')).toBeInTheDocument();
    });

    it('handles empty associated listings', () => {
      const cpu = createMockCPU();
      const cpuDetail = createMockCPUDetail(cpu, { associated_listings: [] });
      render(
        <DetailPanel
          cpu={cpu}
          cpuDetail={cpuDetail}
          isLoadingDetail={false}
          isErrorDetail={false}
        />
      );

      // Top Listings section should not render
      expect(screen.queryByText(/top listings/i)).not.toBeInTheDocument();
    });
  });
});
