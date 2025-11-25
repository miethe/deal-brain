/**
 * ValuationTooltip Component Tests
 *
 * Tests for accessibility, rendering, and interaction behavior
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ValuationTooltip } from "../valuation-tooltip";
import type { ValuationBreakdown } from "@/types/listings";

// Mock valuation breakdown data
const mockBreakdown: ValuationBreakdown = {
  listing_price: 999,
  adjusted_price: 849,
  total_adjustment: 150,
  matched_rules_count: 3,
  adjustments: [
    {
      rule_id: 1,
      rule_name: "RAM Deduction (8GB DDR4)",
      rule_description: "Deduct value of RAM",
      adjustment_amount: -80,
      actions: [],
    },
    {
      rule_id: 2,
      rule_name: "Storage Deduction (256GB SSD)",
      rule_description: "Deduct value of storage",
      adjustment_amount: -50,
      actions: [],
    },
    {
      rule_id: 3,
      rule_name: "Condition Adjustment (Good)",
      rule_description: "Adjust for condition",
      adjustment_amount: -20,
      actions: [],
    },
  ],
};

describe("ValuationTooltip", () => {
  it("renders default info icon trigger", () => {
    render(
      <ValuationTooltip
        listPrice={999}
        adjustedValue={849}
        valuationBreakdown={mockBreakdown}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    expect(trigger).toBeInTheDocument();
  });

  it("renders custom children as trigger", () => {
    render(
      <ValuationTooltip
        listPrice={999}
        adjustedValue={849}
        valuationBreakdown={mockBreakdown}
      >
        <button>Custom Trigger</button>
      </ValuationTooltip>
    );

    expect(screen.getByRole("button", { name: /custom trigger/i })).toBeInTheDocument();
  });

  it("displays calculation summary on hover", async () => {
    const user = userEvent.setup();

    render(
      <ValuationTooltip
        listPrice={999}
        adjustedValue={849}
        valuationBreakdown={mockBreakdown}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      expect(screen.getByText(/adjusted value calculation/i)).toBeInTheDocument();
      expect(screen.getByText("$999")).toBeInTheDocument();
      expect(screen.getByText("$849")).toBeInTheDocument();
      expect(screen.getByText(/-\$150/)).toBeInTheDocument();
    });
  });

  it("displays savings percentage correctly", async () => {
    const user = userEvent.setup();

    render(
      <ValuationTooltip
        listPrice={1000}
        adjustedValue={850}
        valuationBreakdown={mockBreakdown}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      expect(screen.getByText(/15\.0% savings/i)).toBeInTheDocument();
    });
  });

  it("displays premium percentage when adjusted value is higher", async () => {
    const user = userEvent.setup();

    render(
      <ValuationTooltip
        listPrice={1000}
        adjustedValue={1100}
        valuationBreakdown={{
          ...mockBreakdown,
          adjusted_price: 1100,
          total_adjustment: -100,
        }}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      expect(screen.getByText(/10\.0% premium/i)).toBeInTheDocument();
    });
  });

  it("displays top rules by impact", async () => {
    const user = userEvent.setup();

    render(
      <ValuationTooltip
        listPrice={999}
        adjustedValue={849}
        valuationBreakdown={mockBreakdown}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      expect(screen.getByText(/applied 3 valuation rules/i)).toBeInTheDocument();
      expect(screen.getByText(/RAM Deduction \(8GB DDR4\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Storage Deduction \(256GB SSD\)/i)).toBeInTheDocument();
    });
  });

  it("sorts rules by absolute impact (largest first)", async () => {
    const user = userEvent.setup();

    const breakdownWithMixedImpact: ValuationBreakdown = {
      ...mockBreakdown,
      adjustments: [
        { rule_id: 1, rule_name: "Small Rule", adjustment_amount: -20, actions: [] },
        { rule_id: 2, rule_name: "Large Rule", adjustment_amount: -100, actions: [] },
        { rule_id: 3, rule_name: "Medium Rule", adjustment_amount: -50, actions: [] },
      ],
    };

    render(
      <ValuationTooltip
        listPrice={999}
        adjustedValue={849}
        valuationBreakdown={breakdownWithMixedImpact}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      const rules = screen.getAllByText(/rule/i);
      // First rule should be "Large Rule" (highest impact)
      expect(rules[1]).toHaveTextContent("Large Rule");
    });
  });

  it("limits to top 5 rules", async () => {
    const user = userEvent.setup();

    const breakdownWithManyRules: ValuationBreakdown = {
      ...mockBreakdown,
      matched_rules_count: 10,
      adjustments: Array.from({ length: 10 }, (_, i) => ({
        rule_id: i + 1,
        rule_name: `Rule ${i + 1}`,
        adjustment_amount: -(10 + i * 5),
        actions: [],
      })),
    };

    render(
      <ValuationTooltip
        listPrice={999}
        adjustedValue={849}
        valuationBreakdown={breakdownWithManyRules}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      const ruleItems = screen.getAllByRole("listitem");
      expect(ruleItems).toHaveLength(5);
    });
  });

  it("calls onViewDetails when link is clicked", async () => {
    const user = userEvent.setup();
    const handleViewDetails = jest.fn();

    render(
      <ValuationTooltip
        listPrice={999}
        adjustedValue={849}
        valuationBreakdown={mockBreakdown}
        onViewDetails={handleViewDetails}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      const viewDetailsLink = screen.getByRole("button", {
        name: /open full valuation breakdown modal/i,
      });
      expect(viewDetailsLink).toBeInTheDocument();
    });

    const viewDetailsLink = screen.getByRole("button", {
      name: /open full valuation breakdown modal/i,
    });
    await user.click(viewDetailsLink);

    expect(handleViewDetails).toHaveBeenCalledTimes(1);
  });

  it("does not show link when onViewDetails is not provided", async () => {
    const user = userEvent.setup();

    render(
      <ValuationTooltip
        listPrice={999}
        adjustedValue={849}
        valuationBreakdown={mockBreakdown}
      />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      expect(screen.getByText(/adjusted value calculation/i)).toBeInTheDocument();
    });

    expect(
      screen.queryByRole("button", { name: /open full valuation breakdown modal/i })
    ).not.toBeInTheDocument();
  });

  it("handles missing valuation breakdown gracefully", async () => {
    const user = userEvent.setup();

    render(
      <ValuationTooltip listPrice={999} adjustedValue={849} valuationBreakdown={null} />
    );

    const trigger = screen.getByRole("button", { name: /view valuation details/i });
    await user.hover(trigger);

    await waitFor(() => {
      expect(screen.getByText(/adjusted value calculation/i)).toBeInTheDocument();
      expect(screen.getByText("$999")).toBeInTheDocument();
      expect(screen.getByText("$849")).toBeInTheDocument();
    });

    // Should not show rules section
    expect(screen.queryByText(/applied.*valuation rules/i)).not.toBeInTheDocument();
  });

  describe("Accessibility", () => {
    it("has proper ARIA labels", () => {
      render(
        <ValuationTooltip
          listPrice={999}
          adjustedValue={849}
          valuationBreakdown={mockBreakdown}
        />
      );

      const trigger = screen.getByRole("button", { name: /view valuation details/i });
      expect(trigger).toHaveAttribute("aria-label", "View valuation details");
    });

    it("is keyboard accessible (Tab to focus)", async () => {
      const user = userEvent.setup();

      render(
        <ValuationTooltip
          listPrice={999}
          adjustedValue={849}
          valuationBreakdown={mockBreakdown}
        />
      );

      // Tab to focus the trigger
      await user.tab();

      const trigger = screen.getByRole("button", { name: /view valuation details/i });
      expect(trigger).toHaveFocus();
    });

    it("shows tooltip on keyboard focus", async () => {
      const user = userEvent.setup();

      render(
        <ValuationTooltip
          listPrice={999}
          adjustedValue={849}
          valuationBreakdown={mockBreakdown}
        />
      );

      const trigger = screen.getByRole("button", { name: /view valuation details/i });
      trigger.focus();

      await waitFor(() => {
        expect(screen.getByText(/adjusted value calculation/i)).toBeInTheDocument();
      });
    });

    it("respects custom delay duration", async () => {
      const user = userEvent.setup();

      render(
        <ValuationTooltip
          listPrice={999}
          adjustedValue={849}
          valuationBreakdown={mockBreakdown}
          delayDuration={500}
        />
      );

      const trigger = screen.getByRole("button", { name: /view valuation details/i });
      await user.hover(trigger);

      // Should not appear immediately
      expect(screen.queryByText(/adjusted value calculation/i)).not.toBeInTheDocument();

      // Should appear after delay
      await waitFor(
        () => {
          expect(screen.getByText(/adjusted value calculation/i)).toBeInTheDocument();
        },
        { timeout: 600 }
      );
    });
  });
});
