/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ListingValuationTab } from "../components/listings/listing-valuation-tab";
import type { ListingRecord } from "../types/listings";

const invalidateQueries = jest.fn();
const mutateMock = jest.fn();

jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn().mockReturnValue({
    data: [
      { id: 1, name: "Primary Ruleset", priority: 1, is_active: true },
      { id: 2, name: "Secondary Ruleset", priority: 2, is_active: true },
    ],
    isLoading: false,
  }),
  useMutation: jest.fn().mockImplementation((options) => {
    mutateMock.mockImplementation((payload) => {
      options?.onSuccess?.({
        mode: payload.mode,
        ruleset_id: payload.ruleset_id ?? null,
        disabled_rulesets: payload.disabled_rulesets ?? [],
      });
    });
    return { mutate: mutateMock, isPending: false };
  }),
  useQueryClient: () => ({
    invalidateQueries,
  }),
}));

jest.mock("../components/listings/valuation-cell", () => ({
  ValuationCell: () => <div data-testid="valuation-cell" />,
}));

jest.mock("../components/listings/valuation-breakdown-modal", () => ({
  ValuationBreakdownModal: () => null,
}));

jest.mock("../components/ui/use-toast", () => ({
  useToast: () => ({ toast: jest.fn() }),
}));

jest.mock("@/hooks/use-valuation-thresholds", () => ({
  useValuationThresholds: () => ({ data: null }),
}));

beforeEach(() => {
  jest.clearAllMocks();
});

const baseListing: ListingRecord = {
  id: 101,
  title: "Sample Listing",
  listing_url: null,
  other_urls: [],
  seller: "Test Seller",
  price_usd: 950,
  adjusted_price_usd: 950,
  score_composite: null,
  score_cpu_multi: null,
  score_cpu_single: null,
  score_gpu: null,
  dollar_per_cpu_mark: null,
  dollar_per_single_mark: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  status: "active",
  condition: "used",
  thumbnail_url: null,
  ruleset_id: null,
  valuation_breakdown: {
    listing_price: 950,
    adjusted_price: 950,
    total_adjustment: 0,
    total_deductions: 0,
    matched_rules_count: 0,
    matched_rules: [],
    adjustments: [],
    lines: [],
    ruleset: { id: null, name: null },
  },
  attributes: {},
};

describe("ListingValuationTab override workflow", () => {
  it("disables the save button after successful override persist", async () => {
    const user = userEvent.setup();

    render(<ListingValuationTab listing={baseListing} />);

    const saveButton = screen.getByRole("button", { name: /save overrides/i });
    expect(saveButton).toBeDisabled();

    await user.click(screen.getByRole("button", { name: /static override/i }));
    expect(saveButton).toBeEnabled();

    await user.click(saveButton);
    expect(mutateMock).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(saveButton).toBeDisabled();
    });
  });
});
