/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CollectionSelectorModal } from "../collection-selector-modal";
import * as collectionsHooks from "@/hooks/use-collections";
import * as addToCollectionHook from "@/hooks/use-add-to-collection";

// Mock dependencies
jest.mock("@/hooks/use-collections");
jest.mock("@/hooks/use-add-to-collection");
jest.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock UI components
jest.mock("@/components/ui/dialog", () => ({
  Dialog: ({ children, open }: any) => (open ? <div>{children}</div> : null),
  DialogContent: ({ children }: any) => <div data-testid="dialog-content">{children}</div>,
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  DialogTitle: ({ children }: any) => <h2>{children}</h2>,
  DialogFooter: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, disabled, type }: any) => (
    <button onClick={onClick} disabled={disabled} type={type}>
      {children}
    </button>
  ),
}));

jest.mock("@/components/ui/input", () => {
  const React = require("react");
  return {
    Input: React.forwardRef(({ id, ...props }: any, ref: any) => (
      <input id={id} ref={ref} {...props} />
    )),
  };
});

jest.mock("@/components/ui/textarea", () => {
  const React = require("react");
  return {
    Textarea: React.forwardRef(({ id, ...props }: any, ref: any) => (
      <textarea id={id} ref={ref} {...props} />
    )),
  };
});

jest.mock("@/components/ui/label", () => ({
  Label: ({ children, htmlFor }: any) => <label htmlFor={htmlFor}>{children}</label>,
}));

jest.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: any) => <div>{children}</div>,
}));

describe("CollectionSelectorModal", () => {
  let queryClient: QueryClient;
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();

  const mockCollections = [
    {
      id: 1,
      name: "Gaming Builds",
      description: "High-performance gaming PCs",
      visibility: "private" as const,
      item_count: 12,
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    },
    {
      id: 2,
      name: "Budget Options",
      description: null,
      visibility: "private" as const,
      item_count: 5,
      created_at: "2025-01-02T00:00:00Z",
      updated_at: "2025-01-02T00:00:00Z",
    },
  ];

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  const renderModal = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <CollectionSelectorModal
          listingId={123}
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          {...props}
        />
      </QueryClientProvider>
    );
  };

  describe("Initial Rendering", () => {
    it("renders modal when isOpen is true", () => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: mockCollections, total: 2 },
        isLoading: false,
      });

      renderModal();

      expect(screen.getByText("Add to Collection")).toBeInTheDocument();
      expect(screen.getByTestId("dialog-content")).toBeInTheDocument();
    });

    it("does not render when isOpen is false", () => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: mockCollections, total: 2 },
        isLoading: false,
      });

      renderModal({ isOpen: false });

      expect(screen.queryByTestId("dialog-content")).not.toBeInTheDocument();
    });

    it("shows loading state while fetching collections", () => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
      });

      renderModal();

      expect(screen.getByText("Add to Collection")).toBeInTheDocument();
      // Loading spinner should be present (Loader2 icon)
      const loadingElement = screen.getByTestId("dialog-content");
      expect(loadingElement).toBeInTheDocument();
    });
  });

  describe("Collections List View", () => {
    beforeEach(() => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: mockCollections, total: 2 },
        isLoading: false,
      });
    });

    it("displays recent collections", () => {
      renderModal();

      expect(screen.getByText("Gaming Builds")).toBeInTheDocument();
      expect(screen.getByText("Budget Options")).toBeInTheDocument();
      expect(screen.getByText("(12)")).toBeInTheDocument();
      expect(screen.getByText("(5)")).toBeInTheDocument();
    });

    it("shows collection descriptions when available", () => {
      renderModal();

      expect(screen.getByText("High-performance gaming PCs")).toBeInTheDocument();
    });

    it("shows empty state when no collections exist", () => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: [], total: 0 },
        isLoading: false,
      });

      renderModal();

      expect(screen.getByText("No collections yet")).toBeInTheDocument();
      expect(screen.getByText("Create your first collection to get started")).toBeInTheDocument();
    });

    it("displays 'Create New Collection' button", () => {
      renderModal();

      expect(screen.getByRole("button", { name: /Create New Collection/i })).toBeInTheDocument();
    });

    it("displays cancel button", () => {
      renderModal();

      expect(screen.getByRole("button", { name: /Cancel/i })).toBeInTheDocument();
    });
  });

  describe("Adding to Existing Collection", () => {
    const mockAddMutation = {
      mutate: jest.fn(),
      isPending: false,
    };

    beforeEach(() => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: mockCollections, total: 2 },
        isLoading: false,
      });
      (addToCollectionHook.useAddToCollection as jest.Mock).mockReturnValue(mockAddMutation);
    });

    it("calls addMutation when collection is clicked", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      const gamingBuildsButton = screen.getByText("Gaming Builds").closest("button");
      await user.click(gamingBuildsButton!);

      // Fast-forward to trigger useEffect
      jest.runAllTimers();

      await waitFor(() => {
        expect(mockAddMutation.mutate).toHaveBeenCalledWith({
          listing_id: 123,
          status: "undecided",
        });
      });
    });

    it("shows loading state while adding", () => {
      (addToCollectionHook.useAddToCollection as jest.Mock).mockReturnValue({
        ...mockAddMutation,
        isPending: true,
      });

      renderModal();

      // Buttons should be disabled during add operation
      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      expect(createButton).toBeDisabled();
    });
  });

  describe("Create New Collection Mode", () => {
    beforeEach(() => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: mockCollections, total: 2 },
        isLoading: false,
      });
      (collectionsHooks.useCreateCollection as jest.Mock).mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });
      (addToCollectionHook.useAddToCollection as jest.Mock).mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });
    });

    it("switches to create mode when 'Create New Collection' is clicked", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      expect(screen.getByText("Create New Collection")).toBeInTheDocument();
      expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Create & Add/i })).toBeInTheDocument();
    });

    it("shows back button in create mode", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      const backButton = screen.getByLabelText("Back to collections list");
      expect(backButton).toBeInTheDocument();
    });

    it("returns to list view when back button is clicked", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      // Go to create mode
      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      // Click back
      const backButton = screen.getByLabelText("Back to collections list");
      await user.click(backButton);

      // Should be back to list view
      expect(screen.getByText("Add to Collection")).toBeInTheDocument();
      expect(screen.getByText("Gaming Builds")).toBeInTheDocument();
    });
  });

  describe("Creating New Collection and Adding", () => {
    const mockCreateMutation = {
      mutate: jest.fn(),
      isPending: false,
    };

    beforeEach(() => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: mockCollections, total: 2 },
        isLoading: false,
      });
      (collectionsHooks.useCreateCollection as jest.Mock).mockReturnValue(mockCreateMutation);
      (addToCollectionHook.useAddToCollection as jest.Mock).mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });
    });

    it("validates name field is required", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      // Go to create mode
      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      // Try to submit without name
      const submitButton = screen.getByRole("button", { name: /Create & Add/i });
      await user.click(submitButton);

      expect(screen.getByText("Name is required")).toBeInTheDocument();
      expect(mockCreateMutation.mutate).not.toHaveBeenCalled();
    });

    it("validates name length constraints", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      // Go to create mode
      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      // Type a name that's too long (> 100 characters)
      const nameInput = screen.getByLabelText(/Name/i);
      await user.type(nameInput, "a".repeat(101));

      const submitButton = screen.getByRole("button", { name: /Create & Add/i });
      await user.click(submitButton);

      expect(screen.getByText(/Name must be between 1 and 100 characters/i)).toBeInTheDocument();
    });

    it("creates collection with valid data", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      // Go to create mode
      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      // Fill in form
      const nameInput = screen.getByLabelText(/Name/i);
      await user.type(nameInput, "New Collection");

      const descInput = screen.getByLabelText(/Description/i);
      await user.type(descInput, "Test description");

      // Submit
      const submitButton = screen.getByRole("button", { name: /Create & Add/i });
      await user.click(submitButton);

      expect(mockCreateMutation.mutate).toHaveBeenCalledWith({
        name: "New Collection",
        description: "Test description",
        visibility: "private",
      });
    });

    it("shows loading state during creation", async () => {
      const user = userEvent.setup({ delay: null });

      (collectionsHooks.useCreateCollection as jest.Mock).mockReturnValue({
        ...mockCreateMutation,
        isPending: true,
      });

      renderModal();

      // Go to create mode
      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      const submitButton = screen.getByRole("button", { name: /Creating.../i });
      expect(submitButton).toBeDisabled();
    });
  });

  describe("Modal Closure", () => {
    beforeEach(() => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: mockCollections, total: 2 },
        isLoading: false,
      });
      (addToCollectionHook.useAddToCollection as jest.Mock).mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });
    });

    it("calls onClose when cancel button is clicked", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      const cancelButton = screen.getByRole("button", { name: /Cancel/i });
      await user.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it("resets form state when closed", async () => {
      const user = userEvent.setup({ delay: null });

      (collectionsHooks.useCreateCollection as jest.Mock).mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      const { rerender } = renderModal();

      // Go to create mode and fill form
      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      const nameInput = screen.getByLabelText(/Name/i);
      await user.type(nameInput, "Test Collection");

      // Close modal
      mockOnClose.mockClear();
      rerender(
        <QueryClientProvider client={queryClient}>
          <CollectionSelectorModal
            listingId={123}
            isOpen={false}
            onClose={mockOnClose}
            onSuccess={mockOnSuccess}
          />
        </QueryClientProvider>
      );

      // Reopen modal
      rerender(
        <QueryClientProvider client={queryClient}>
          <CollectionSelectorModal
            listingId={123}
            isOpen={true}
            onClose={mockOnClose}
            onSuccess={mockOnSuccess}
          />
        </QueryClientProvider>
      );

      // Should be back to list view (not create mode)
      expect(screen.getByText("Add to Collection")).toBeInTheDocument();
      expect(screen.getByText("Gaming Builds")).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    beforeEach(() => {
      (collectionsHooks.useCollections as jest.Mock).mockReturnValue({
        data: { collections: mockCollections, total: 2 },
        isLoading: false,
      });
      (addToCollectionHook.useAddToCollection as jest.Mock).mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });
    });

    it("has accessible labels for collection buttons", () => {
      renderModal();

      const gamingButton = screen.getByLabelText("Add to Gaming Builds");
      expect(gamingButton).toBeInTheDocument();

      const budgetButton = screen.getByLabelText("Add to Budget Options");
      expect(budgetButton).toBeInTheDocument();
    });

    it("has accessible back button label", async () => {
      const user = userEvent.setup({ delay: null });

      renderModal();

      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      const backButton = screen.getByLabelText("Back to collections list");
      expect(backButton).toBeInTheDocument();
    });

    it("shows validation errors with proper aria attributes", async () => {
      const user = userEvent.setup({ delay: null });

      (collectionsHooks.useCreateCollection as jest.Mock).mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderModal();

      // Go to create mode
      const createButton = screen.getByRole("button", { name: /Create New Collection/i });
      await user.click(createButton);

      // Try to submit without name
      const submitButton = screen.getByRole("button", { name: /Create & Add/i });
      await user.click(submitButton);

      const nameInput = screen.getByLabelText(/Name/i);
      expect(nameInput).toHaveAttribute("aria-invalid", "true");

      const errorMessage = screen.getByRole("alert");
      expect(errorMessage).toHaveTextContent("Name is required");
    });
  });
});
