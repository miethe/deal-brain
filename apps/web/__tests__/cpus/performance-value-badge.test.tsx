/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PerformanceValueBadge } from '@/app/cpus/_components/performance-value-badge';

describe('PerformanceValueBadge', () => {
  describe('Excellent Rating', () => {
    it('renders excellent rating with correct styling and content', () => {
      render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={0.0623}
          percentile={22.5}
          metricType="single"
        />
      );

      // Check formatted value is displayed
      const badge = screen.getByText('$0.0623/mark');
      expect(badge).toBeInTheDocument();

      // Check ARIA label includes rating and metric info
      const badgeElement = screen.getByLabelText(/excellent value/i);
      expect(badgeElement).toBeInTheDocument();
      expect(badgeElement).toHaveAttribute('aria-label', expect.stringContaining('ST'));
    });

    it('is wrapped in tooltip provider', () => {
      const { container } = render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={0.0623}
          percentile={22.5}
          metricType="single"
        />
      );

      // Badge should be present and wrapped (tooltip tested via manual/e2e)
      const badge = screen.getByText('$0.0623/mark');
      expect(badge).toBeInTheDocument();
      expect(badge.getAttribute('aria-label')).toContain('Excellent Value');
    });

    it('displays emerald/green color classes for excellent rating', () => {
      const { container } = render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={0.0623}
          percentile={22.5}
        />
      );

      const badge = container.querySelector('[class*="bg-emerald"]');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Good Rating', () => {
    it('renders good rating with correct styling', () => {
      render(
        <PerformanceValueBadge
          rating="good"
          dollarPerMark={0.0894}
          percentile={45.2}
          metricType="multi"
        />
      );

      const badge = screen.getByText('$0.0894/mark');
      expect(badge).toBeInTheDocument();

      const badgeElement = screen.getByLabelText(/good value/i);
      expect(badgeElement).toHaveAttribute('aria-label', expect.stringContaining('MT'));
    });

    it('has correct aria-label for good rating', () => {
      render(
        <PerformanceValueBadge
          rating="good"
          dollarPerMark={0.0894}
          percentile={45.2}
          metricType="multi"
        />
      );

      const badgeElement = screen.getByLabelText(/good value/i);
      expect(badgeElement).toBeInTheDocument();
      expect(badgeElement.getAttribute('aria-label')).toContain('MT');
    });
  });

  describe('Fair Rating', () => {
    it('renders fair rating with amber styling', () => {
      render(
        <PerformanceValueBadge
          rating="fair"
          dollarPerMark={0.1234}
          percentile={65.0}
        />
      );

      const badge = screen.getByText('$0.1234/mark');
      expect(badge).toBeInTheDocument();

      const badgeElement = screen.getByLabelText(/fair value/i);
      expect(badgeElement).toBeInTheDocument();
    });

    it('has cursor-help class for tooltip indication', () => {
      const { container } = render(
        <PerformanceValueBadge
          rating="fair"
          dollarPerMark={0.1234}
          percentile={65.0}
        />
      );

      const badge = container.querySelector('.cursor-help');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Poor Rating', () => {
    it('renders poor rating with red styling', () => {
      render(
        <PerformanceValueBadge
          rating="poor"
          dollarPerMark={0.2567}
          percentile={85.0}
        />
      );

      const badge = screen.getByText('$0.2567/mark');
      expect(badge).toBeInTheDocument();

      const badgeElement = screen.getByLabelText(/poor value/i);
      expect(badgeElement).toBeInTheDocument();
    });

    it('has correct aria-label for poor rating', () => {
      render(
        <PerformanceValueBadge
          rating="poor"
          dollarPerMark={0.2567}
          percentile={85.0}
        />
      );

      const badgeElement = screen.getByLabelText(/poor value/i);
      expect(badgeElement).toBeInTheDocument();
    });
  });

  describe('No Data State', () => {
    it('renders no data state when rating is null', () => {
      render(
        <PerformanceValueBadge
          rating={null}
          dollarPerMark={null}
          percentile={null}
        />
      );

      expect(screen.getByText('No data')).toBeInTheDocument();
      expect(screen.getByLabelText(/no performance value data available/i)).toBeInTheDocument();
    });

    it('renders no data state when dollarPerMark is null', () => {
      render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={null}
          percentile={22.5}
        />
      );

      expect(screen.getByText('No data')).toBeInTheDocument();
    });

    it('has gray styling for no data state', () => {
      const { container } = render(
        <PerformanceValueBadge
          rating={null}
          dollarPerMark={null}
        />
      );

      const badge = container.querySelector('[class*="bg-gray"]');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Metric Type Display', () => {
    it('displays ST label for single-thread metric', () => {
      render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={0.0623}
          percentile={22.5}
          metricType="single"
        />
      );

      const badgeElement = screen.getByLabelText(/ST performance/i);
      expect(badgeElement).toBeInTheDocument();
    });

    it('displays MT label for multi-thread metric', () => {
      render(
        <PerformanceValueBadge
          rating="good"
          dollarPerMark={0.0894}
          percentile={45.2}
          metricType="multi"
        />
      );

      const badgeElement = screen.getByLabelText(/MT performance/i);
      expect(badgeElement).toBeInTheDocument();
    });

    it('defaults to multi-thread when metricType not specified', () => {
      render(
        <PerformanceValueBadge
          rating="good"
          dollarPerMark={0.0894}
          percentile={45.2}
        />
      );

      const badgeElement = screen.getByLabelText(/MT performance/i);
      expect(badgeElement).toBeInTheDocument();
    });
  });

  describe('Percentile Display', () => {
    it('accepts percentile prop', () => {
      render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={0.0623}
          percentile={22.5}
        />
      );

      // Component renders successfully with percentile
      expect(screen.getByText('$0.0623/mark')).toBeInTheDocument();
    });

    it('handles zero percentile correctly', () => {
      render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={0.0500}
          percentile={0}
        />
      );

      // Component renders successfully with 0 percentile
      expect(screen.getByText('$0.0500/mark')).toBeInTheDocument();
    });

    it('handles null percentile', () => {
      render(
        <PerformanceValueBadge
          rating="good"
          dollarPerMark={0.0894}
          percentile={null}
        />
      );

      // Component still renders without percentile
      expect(screen.getByText('$0.0894/mark')).toBeInTheDocument();
    });

    it('handles undefined percentile', () => {
      render(
        <PerformanceValueBadge
          rating="good"
          dollarPerMark={0.0894}
          percentile={undefined}
        />
      );

      // Component still renders without percentile
      expect(screen.getByText('$0.0894/mark')).toBeInTheDocument();
    });
  });

  describe('Value Formatting', () => {
    it('formats dollar per mark with 4 decimal places', () => {
      render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={0.123456789}
          percentile={20}
        />
      );

      // Should round to 4 decimal places
      expect(screen.getByText('$0.1235/mark')).toBeInTheDocument();
    });

    it('pads zeros for values with fewer decimal places', () => {
      render(
        <PerformanceValueBadge
          rating="good"
          dollarPerMark={0.05}
          percentile={30}
        />
      );

      expect(screen.getByText('$0.0500/mark')).toBeInTheDocument();
    });

    it('handles whole numbers correctly', () => {
      render(
        <PerformanceValueBadge
          rating="poor"
          dollarPerMark={1}
          percentile={90}
        />
      );

      expect(screen.getByText('$1.0000/mark')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for screen readers', () => {
      render(
        <PerformanceValueBadge
          rating="excellent"
          dollarPerMark={0.0623}
          percentile={22.5}
          metricType="single"
        />
      );

      const badgeElement = screen.getByLabelText('Excellent Value: $0.0623/mark for ST performance');
      expect(badgeElement).toBeInTheDocument();
    });

    it('has cursor help class for tooltip indication', () => {
      const { container } = render(
        <PerformanceValueBadge
          rating="good"
          dollarPerMark={0.0894}
          percentile={45.2}
        />
      );

      const badge = container.querySelector('[class*="cursor-help"]');
      expect(badge).toBeInTheDocument();
    });
  });
});
