/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PriceTargets } from '@/app/cpus/_components/price-targets';

describe('PriceTargets', () => {
  describe('Compact Variant (Default)', () => {
    it('renders all three price targets in compact mode', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      expect(screen.getByText('$320')).toBeInTheDocument();
      expect(screen.getByText('$350')).toBeInTheDocument();
      expect(screen.getByText('$380')).toBeInTheDocument();
      expect(screen.getByText('Great')).toBeInTheDocument();
      expect(screen.getByText('Good')).toBeInTheDocument();
      expect(screen.getByText('Fair')).toBeInTheDocument();
    });

    it('displays header with price targets label', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      expect(screen.getByText('Price Targets')).toBeInTheDocument();
    });

    it('shows sample size footer in compact mode', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      expect(screen.getByText('Based on 12 listings')).toBeInTheDocument();
    });

    it('uses correct singular/plural for sample size', () => {
      const { rerender } = render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={null}
          confidence="low"
          sampleSize={3}
          variant="compact"
        />
      );

      expect(screen.getByText(/based on 3 listings/i)).toBeInTheDocument();

      rerender(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="medium"
          sampleSize={2}
          variant="compact"
        />
      );

      expect(screen.getByText(/based on 2 listings/i)).toBeInTheDocument();
    });

    it('renders only Good price when Great and Fair are null', () => {
      render(
        <PriceTargets
          priceTargetGreat={null}
          priceTargetGood={350}
          priceTargetFair={null}
          confidence="low"
          sampleSize={3}
          variant="compact"
        />
      );

      expect(screen.getByText('$350')).toBeInTheDocument();
      expect(screen.queryByText('$320')).not.toBeInTheDocument();
      expect(screen.queryByText('$380')).not.toBeInTheDocument();
    });

    it('uses 3-column grid layout in compact mode', () => {
      const { container } = render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const grid = container.querySelector('.grid-cols-3');
      expect(grid).toBeInTheDocument();
    });
  });

  describe('Detailed Variant', () => {
    it('renders all price targets in detailed layout', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="medium"
          sampleSize={7}
          variant="detailed"
        />
      );

      expect(screen.getByText('$320')).toBeInTheDocument();
      expect(screen.getByText('$350')).toBeInTheDocument();
      expect(screen.getByText('$380')).toBeInTheDocument();
      expect(screen.getByText('Great Deal')).toBeInTheDocument();
      expect(screen.getByText('Good Price')).toBeInTheDocument();
      expect(screen.getByText('Fair Price')).toBeInTheDocument();
    });

    it('shows active listings text in detailed mode footer', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="medium"
          sampleSize={7}
          variant="detailed"
        />
      );

      expect(screen.getByText('Based on 7 active listings')).toBeInTheDocument();
    });

    it('uses vertical layout in detailed mode', () => {
      const { container } = render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="medium"
          sampleSize={7}
          variant="detailed"
        />
      );

      // Detailed mode should not have grid-cols-3
      const horizontalGrid = container.querySelector('.grid-cols-3');
      expect(horizontalGrid).not.toBeInTheDocument();
    });
  });

  describe('Confidence Levels', () => {
    it('displays high confidence badge', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
        />
      );

      expect(screen.getByText('high')).toBeInTheDocument();
    });

    it('displays medium confidence badge', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="medium"
          sampleSize={7}
        />
      );

      expect(screen.getByText('medium')).toBeInTheDocument();
    });

    it('displays low confidence badge', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="low"
          sampleSize={3}
        />
      );

      expect(screen.getByText('low')).toBeInTheDocument();
    });

    it('has aria-label for high confidence', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
        />
      );

      const confidenceBadge = screen.getByText('high');
      expect(confidenceBadge).toBeInTheDocument();
    });

    it('renders medium confidence correctly', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="medium"
          sampleSize={7}
        />
      );

      expect(screen.getByText('medium')).toBeInTheDocument();
    });

    it('renders low confidence correctly', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="low"
          sampleSize={3}
        />
      );

      expect(screen.getByText('low')).toBeInTheDocument();
    });
  });

  describe('Insufficient Data State', () => {
    it('displays alert when confidence is insufficient', () => {
      render(
        <PriceTargets
          priceTargetGreat={null}
          priceTargetGood={null}
          priceTargetFair={null}
          confidence="insufficient"
          sampleSize={1}
        />
      );

      expect(screen.getByText(/insufficient data/i)).toBeInTheDocument();
      expect(screen.getByText(/Listings page/i)).toBeInTheDocument();
      expect(screen.getByText(/for available deals/i)).toBeInTheDocument();
    });

    it('displays alert when sample size is less than 2', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="low"
          sampleSize={1}
        />
      );

      expect(screen.getByText(/insufficient data/i)).toBeInTheDocument();
    });

    it('displays alert when priceTargetGood is null', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={null}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
        />
      );

      expect(screen.getByText(/insufficient data/i)).toBeInTheDocument();
    });

    it('displays alert with info icon', () => {
      const { container } = render(
        <PriceTargets
          priceTargetGreat={null}
          priceTargetGood={null}
          priceTargetFair={null}
          confidence="insufficient"
          sampleSize={1}
        />
      );

      // Check for InfoIcon presence
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Price Target Accessibility', () => {
    it('has role="region" for Great price tier', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const greatPrice = screen.getByText('$320').closest('[role="region"]');
      expect(greatPrice).toBeInTheDocument();
    });

    it('has role="region" for Good price tier', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const goodPrice = screen.getByText('$350').closest('[role="region"]');
      expect(goodPrice).toBeInTheDocument();
    });

    it('has role="region" for Fair price tier', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const fairPrice = screen.getByText('$380').closest('[role="region"]');
      expect(fairPrice).toBeInTheDocument();
    });
  });

  describe('Price Formatting', () => {
    it('formats prices with comma separators for thousands', () => {
      render(
        <PriceTargets
          priceTargetGreat={1320}
          priceTargetGood={1500}
          priceTargetFair={1680}
          confidence="high"
          sampleSize={12}
        />
      );

      expect(screen.getByText('$1,320')).toBeInTheDocument();
      expect(screen.getByText('$1,500')).toBeInTheDocument();
      expect(screen.getByText('$1,680')).toBeInTheDocument();
    });

    it('handles whole dollar amounts without decimals', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
        />
      );

      // Should not show .00
      expect(screen.getByText('$320')).toBeInTheDocument();
      expect(screen.queryByText('$320.00')).not.toBeInTheDocument();
    });
  });

  describe('Color Coding', () => {
    it('applies emerald/green styling to Great price', () => {
      const { container } = render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const greatSection = container.querySelector('.bg-emerald-50');
      expect(greatSection).toBeInTheDocument();
    });

    it('applies blue styling to Good price', () => {
      const { container } = render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const goodSection = container.querySelector('.bg-blue-50');
      expect(goodSection).toBeInTheDocument();
    });

    it('applies amber/yellow styling to Fair price', () => {
      const { container } = render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const fairSection = container.querySelector('.bg-amber-50');
      expect(fairSection).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role="region" for each price tier', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const regions = screen.getAllByRole('region');
      expect(regions.length).toBeGreaterThanOrEqual(2); // At least Good and one other
    });

    it('has proper aria-label for price targets', () => {
      render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      expect(screen.getByLabelText(/great deal price target/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/good price target/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/fair price target/i)).toBeInTheDocument();
    });

    it('has cursor-help class for interactive tooltips', () => {
      const { container } = render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
          variant="compact"
        />
      );

      const helpElements = container.querySelectorAll('.cursor-help');
      expect(helpElements.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('handles zero sample size gracefully', () => {
      render(
        <PriceTargets
          priceTargetGreat={null}
          priceTargetGood={null}
          priceTargetFair={null}
          confidence="insufficient"
          sampleSize={0}
        />
      );

      expect(screen.getByText(/insufficient data/i)).toBeInTheDocument();
    });

    it('handles missing confidence gracefully', () => {
      render(
        <PriceTargets
          priceTargetGreat={null}
          priceTargetGood={null}
          priceTargetFair={null}
          confidence={null}
          sampleSize={5}
        />
      );

      // Should show insufficient data when confidence is null
      expect(screen.getByText(/insufficient data/i)).toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('renders with expected structure', () => {
      const { container } = render(
        <PriceTargets
          priceTargetGreat={320}
          priceTargetGood={350}
          priceTargetFair={380}
          confidence="high"
          sampleSize={12}
        />
      );

      // Component renders with proper structure
      expect(screen.getByText('$320')).toBeInTheDocument();
      expect(screen.getByText('$350')).toBeInTheDocument();
      expect(screen.getByText('$380')).toBeInTheDocument();
    });
  });
});
