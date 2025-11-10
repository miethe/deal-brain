/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { CPUCard } from '@/app/cpus/_components/grid-view/cpu-card';
import type { CPURecord } from '@/types/cpus';

// Mock the Zustand store
const mockOpenDetailsDialog = jest.fn();
jest.mock('@/stores/cpu-catalog-store', () => ({
  useCPUCatalogStore: (selector: any) => {
    const state = {
      openDetailsDialog: mockOpenDetailsDialog,
    };
    return selector(state);
  },
}));

// Mock child components
jest.mock('@/app/cpus/_components/grid-view/performance-badge', () => ({
  PerformanceBadge: ({ label, value }: any) => (
    <div data-testid={`performance-badge-${label}`}>{label}: {value}</div>
  ),
}));

jest.mock('@/app/cpus/_components/price-targets', () => ({
  PriceTargets: ({ priceTargetGood, confidence, variant }: any) => (
    <div data-testid="price-targets">
      Price: ${priceTargetGood || 'N/A'} ({confidence}) [{variant}]
    </div>
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

describe('CPUCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders CPU name', () => {
      const cpu = createMockCPU();
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('AMD Ryzen 5 5600X')).toBeInTheDocument();
    });

    it('renders manufacturer badge', () => {
      const cpu = createMockCPU();
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('AMD')).toBeInTheDocument();
    });

    it('renders CPU icon', () => {
      const cpu = createMockCPU();
      const { container } = render(<CPUCard cpu={cpu} />);

      // Check for Cpu icon from lucide-react
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Specifications Grid', () => {
    it('displays socket information', () => {
      const cpu = createMockCPU({ socket: 'AM4' });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('Socket:')).toBeInTheDocument();
      expect(screen.getByText('AM4')).toBeInTheDocument();
    });

    it('displays cores and threads', () => {
      const cpu = createMockCPU({ cores: 6, threads: 12 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('Cores/Threads:')).toBeInTheDocument();
      expect(screen.getByText('6C/12T')).toBeInTheDocument();
    });

    it('displays TDP', () => {
      const cpu = createMockCPU({ tdp_w: 65 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('TDP:')).toBeInTheDocument();
      expect(screen.getByText('65W')).toBeInTheDocument();
    });

    it('displays release year', () => {
      const cpu = createMockCPU({ release_year: 2020 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('Release:')).toBeInTheDocument();
      expect(screen.getByText('2020')).toBeInTheDocument();
    });

    it('displays N/A for missing socket', () => {
      const cpu = createMockCPU({ socket: null });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('Socket:')).toBeInTheDocument();
      const specs = screen.getAllByText('N/A');
      expect(specs.length).toBeGreaterThan(0);
    });

    it('displays N/A for missing cores/threads', () => {
      const cpu = createMockCPU({ cores: null, threads: null });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('Cores/Threads:')).toBeInTheDocument();
      expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
    });

    it('displays N/A for missing TDP', () => {
      const cpu = createMockCPU({ tdp_w: null });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('TDP:')).toBeInTheDocument();
      expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
    });

    it('displays N/A for missing release year', () => {
      const cpu = createMockCPU({ release_year: null });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('Release:')).toBeInTheDocument();
      expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
    });
  });

  describe('Performance Badges', () => {
    it('renders single-thread performance badge when available', () => {
      const cpu = createMockCPU({ cpu_mark_single: 3500 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByTestId('performance-badge-ST')).toBeInTheDocument();
      expect(screen.getByText(/ST: 3500/)).toBeInTheDocument();
    });

    it('renders multi-thread performance badge when available', () => {
      const cpu = createMockCPU({ cpu_mark_multi: 22000 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByTestId('performance-badge-MT')).toBeInTheDocument();
      expect(screen.getByText(/MT: 22000/)).toBeInTheDocument();
    });

    it('renders iGPU badge when available', () => {
      const cpu = createMockCPU({ igpu_mark: 2500 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByTestId('performance-badge-iGPU')).toBeInTheDocument();
      expect(screen.getByText(/iGPU: 2500/)).toBeInTheDocument();
    });

    it('does not render performance badges section when no marks available', () => {
      const cpu = createMockCPU({
        cpu_mark_single: null,
        cpu_mark_multi: null,
        igpu_mark: null,
      });
      render(<CPUCard cpu={cpu} />);

      expect(screen.queryByTestId('performance-badge-ST')).not.toBeInTheDocument();
      expect(screen.queryByTestId('performance-badge-MT')).not.toBeInTheDocument();
      expect(screen.queryByTestId('performance-badge-iGPU')).not.toBeInTheDocument();
    });
  });

  describe('Price Targets Integration', () => {
    it('renders PriceTargets component with correct props', () => {
      const cpu = createMockCPU({
        price_target_great: 180,
        price_target_good: 200,
        price_target_fair: 220,
        price_target_confidence: 'high',
        price_target_sample_size: 12,
      });
      render(<CPUCard cpu={cpu} />);

      const priceTargets = screen.getByTestId('price-targets');
      expect(priceTargets).toBeInTheDocument();
      expect(priceTargets).toHaveTextContent('Price: $200');
      expect(priceTargets).toHaveTextContent('high');
      expect(priceTargets).toHaveTextContent('[compact]');
    });

    it('passes compact variant to PriceTargets', () => {
      const cpu = createMockCPU();
      render(<CPUCard cpu={cpu} />);

      const priceTargets = screen.getByTestId('price-targets');
      expect(priceTargets).toHaveTextContent('[compact]');
    });
  });

  describe('Performance Value Metrics', () => {
    it('displays dollar per ST mark when available', () => {
      const cpu = createMockCPU({ dollar_per_mark_single: 0.0571 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('$/ST Mark:')).toBeInTheDocument();
      expect(screen.getByText('$0.0571')).toBeInTheDocument();
    });

    it('displays dollar per MT mark when available', () => {
      const cpu = createMockCPU({ dollar_per_mark_multi: 0.0091 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('$/MT Mark:')).toBeInTheDocument();
      expect(screen.getByText('$0.0091')).toBeInTheDocument();
    });

    it('does not display value metrics section when both are null', () => {
      const cpu = createMockCPU({
        dollar_per_mark_single: null,
        dollar_per_mark_multi: null,
      });
      render(<CPUCard cpu={cpu} />);

      expect(screen.queryByText('Value Metrics:')).not.toBeInTheDocument();
    });

    it('displays only available value metrics', () => {
      const cpu = createMockCPU({
        dollar_per_mark_single: 0.0571,
        dollar_per_mark_multi: null,
      });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('$/ST Mark:')).toBeInTheDocument();
      expect(screen.queryByText('$/MT Mark:')).not.toBeInTheDocument();
    });
  });

  describe('Footer Information', () => {
    it('displays iGPU model when available', () => {
      const cpu = createMockCPU({ igpu_model: 'Radeon Graphics' });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText(/iGPU:.*Radeon Graphics/)).toBeInTheDocument();
    });

    it('displays listings count badge', () => {
      const cpu = createMockCPU({ listings_count: 15 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('15 listings')).toBeInTheDocument();
    });

    it('uses singular form for 1 listing', () => {
      const cpu = createMockCPU({ listings_count: 1 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('1 listing')).toBeInTheDocument();
    });

    it('does not display listings badge when count is 0', () => {
      const cpu = createMockCPU({ listings_count: 0 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.queryByText(/listing/)).not.toBeInTheDocument();
    });

    it('does not display iGPU when model is null', () => {
      const cpu = createMockCPU({ igpu_model: null });
      render(<CPUCard cpu={cpu} />);

      expect(screen.queryByText(/iGPU:/)).not.toBeInTheDocument();
    });
  });

  describe('Card Interactions', () => {
    it('has hover styling classes', () => {
      const cpu = createMockCPU();
      const { container } = render(<CPUCard cpu={cpu} />);

      const card = container.querySelector('.hover\\:shadow-lg');
      expect(card).toBeInTheDocument();
    });

    it('has cursor pointer class', () => {
      const cpu = createMockCPU();
      const { container } = render(<CPUCard cpu={cpu} />);

      const card = container.querySelector('.cursor-pointer');
      expect(card).toBeInTheDocument();
    });

    it('calls openDetailsDialog when card is clicked', () => {
      const cpu = createMockCPU({ id: 42 });
      const { container } = render(<CPUCard cpu={cpu} />);

      const card = container.querySelector('[class*="cursor-pointer"]');
      expect(card).toBeInTheDocument();

      if (card) {
        fireEvent.click(card);
        expect(mockOpenDetailsDialog).toHaveBeenCalledWith(42);
      }
    });

    it('opens correct CPU detail when clicked', () => {
      const cpu1 = createMockCPU({ id: 1, name: 'CPU 1' });
      const cpu2 = createMockCPU({ id: 2, name: 'CPU 2' });

      const { rerender, container } = render(<CPUCard cpu={cpu1} />);

      let card = container.querySelector('[class*="cursor-pointer"]');
      if (card) fireEvent.click(card);
      expect(mockOpenDetailsDialog).toHaveBeenCalledWith(1);

      mockOpenDetailsDialog.mockClear();

      rerender(<CPUCard cpu={cpu2} />);
      card = container.querySelector('[class*="cursor-pointer"]');
      if (card) fireEvent.click(card);
      expect(mockOpenDetailsDialog).toHaveBeenCalledWith(2);
    });
  });

  describe('Layout and Structure', () => {
    it('uses card component structure', () => {
      const cpu = createMockCPU();
      const { container } = render(<CPUCard cpu={cpu} />);

      // Should have card structure (checking for common card classes)
      const card = container.querySelector('[class*="group"]');
      expect(card).toBeInTheDocument();
    });

    it('has flex column layout for full height', () => {
      const cpu = createMockCPU();
      const { container } = render(<CPUCard cpu={cpu} />);

      const card = container.querySelector('.flex-col');
      expect(card).toBeInTheDocument();
    });

    it('has proper content spacing', () => {
      const cpu = createMockCPU();
      render(<CPUCard cpu={cpu} />);

      // Check that major sections are present
      expect(screen.getByText('AMD Ryzen 5 5600X')).toBeInTheDocument(); // Header
      expect(screen.getByText('Socket:')).toBeInTheDocument(); // Content
      expect(screen.getByTestId('price-targets')).toBeInTheDocument(); // Content
    });
  });

  describe('Edge Cases', () => {
    it('handles CPU with all null optional fields', () => {
      const cpu = createMockCPU({
        socket: null,
        cores: null,
        threads: null,
        tdp_w: null,
        igpu_model: null,
        release_year: null,
        cpu_mark_single: null,
        cpu_mark_multi: null,
        igpu_mark: null,
        dollar_per_mark_single: null,
        dollar_per_mark_multi: null,
        listings_count: 0,
      });
      render(<CPUCard cpu={cpu} />);

      // Should still render basic info
      expect(screen.getByText('AMD Ryzen 5 5600X')).toBeInTheDocument();
      expect(screen.getByText('AMD')).toBeInTheDocument();
    });

    it('handles very long CPU names', () => {
      const cpu = createMockCPU({
        name: 'Intel Core i9-13900KS Special Edition Processor with Extended Name',
      });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText(/Intel Core i9-13900KS/)).toBeInTheDocument();
    });

    it('handles high listing counts', () => {
      const cpu = createMockCPU({ listings_count: 9999 });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('9999 listings')).toBeInTheDocument();
    });

    it('handles zero TDP', () => {
      const cpu = createMockCPU({ tdp_w: 0 });
      render(<CPUCard cpu={cpu} />);

      // 0 is falsy but valid - should display as 0W or N/A
      expect(screen.getByText('TDP:')).toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('renders with expected card structure', () => {
      const cpu = createMockCPU();
      const { container } = render(<CPUCard cpu={cpu} />);

      // Component uses Card structure with group class
      const card = container.querySelector('[class*="group"]');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Intel CPUs', () => {
    it('renders Intel CPU correctly', () => {
      const cpu = createMockCPU({
        name: 'Intel Core i7-12700K',
        manufacturer: 'Intel',
        socket: 'LGA1700',
      });
      render(<CPUCard cpu={cpu} />);

      expect(screen.getByText('Intel Core i7-12700K')).toBeInTheDocument();
      expect(screen.getByText('Intel')).toBeInTheDocument();
      expect(screen.getByText('LGA1700')).toBeInTheDocument();
    });
  });
});
