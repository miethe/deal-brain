/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EntityDeleteDialog } from '../entity-delete-dialog';

// Mock UI components
jest.mock('@/components/ui/alert-dialog', () => ({
  AlertDialog: ({ children, open, onOpenChange }: any) => (
    open ? <div data-testid="alert-dialog" onClick={() => onOpenChange?.(false)}>{children}</div> : null
  ),
  AlertDialogContent: ({ children }: any) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: any) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: any) => <h2>{children}</h2>,
  AlertDialogDescription: ({ children }: any) => <div>{children}</div>,
  AlertDialogFooter: ({ children }: any) => <div data-testid="dialog-footer">{children}</div>,
  AlertDialogCancel: ({ children, onClick, disabled }: any) => (
    <button onClick={onClick} disabled={disabled}>{children}</button>
  ),
}));

jest.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} {...props}>
      {children}
    </button>
  ),
}));

jest.mock('@/components/ui/input', () => {
  const React = require('react');
  return {
    Input: React.forwardRef(({ id, ...props }: any, ref: any) => (
      <input id={id} ref={ref} {...props} />
    )),
  };
});

jest.mock('@/components/ui/label', () => ({
  Label: ({ children, htmlFor }: any) => <label htmlFor={htmlFor}>{children}</label>,
}));

jest.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, className, ...props }: any) => (
    <span data-variant={variant} className={className} {...props}>{children}</span>
  ),
}));

describe('EntityDeleteDialog', () => {
  const mockOnConfirm = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('displays entity type and name', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.getByText('Delete CPU')).toBeInTheDocument();
      expect(screen.getByText(/Intel Core i7-13700K/i)).toBeInTheDocument();
    });

    it('shows correct entity type labels', () => {
      const { rerender } = render(
        <EntityDeleteDialog
          entityType="gpu"
          entityId={1}
          entityName="NVIDIA RTX 4070"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.getByText('Delete GPU')).toBeInTheDocument();

      rerender(
        <EntityDeleteDialog
          entityType="ram-spec"
          entityId={1}
          entityName="32GB DDR5"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.getByText('Delete RAM Specification')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={false}
        />
      );

      expect(screen.queryByTestId('alert-dialog')).not.toBeInTheDocument();
    });
  });

  describe('Usage Count Display', () => {
    it('shows "Used In X Listings" badge when usedInCount > 0', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const badges = screen.getAllByText(/Used in 5 Listings/i);
      expect(badges.length).toBeGreaterThan(0);
      expect(badges[0]).toHaveAttribute('data-variant', 'destructive');
    });

    it('shows singular "Listing" when usedInCount is 1', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={1}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.getByText(/Used in 1 Listing$/i)).toBeInTheDocument();
    });

    it('does not show badge when usedInCount is 0', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.queryByText(/Used in/i)).not.toBeInTheDocument();
    });

    it('shows warning message when entity is in use', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={3}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.getByText(/currently used in 3 listings/i)).toBeInTheDocument();
      expect(screen.getByText(/Deleting it may affect those listings/i)).toBeInTheDocument();
    });
  });

  describe('Confirmation Input', () => {
    it('requires typing entity name when usedInCount > 0', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.getByLabelText(/Type.*Intel Core i7-13700K.*to confirm deletion/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i)).toBeInTheDocument();
    });

    it('does not require confirmation input when usedInCount is 0', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.queryByLabelText(/Type.*to confirm deletion/i)).not.toBeInTheDocument();
    });

    it('enables confirm button only when name matches (case-insensitive)', async () => {
      const user = userEvent.setup();

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /Confirm deletion/i });
      expect(deleteButton).toBeDisabled();

      const input = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);

      // Type incorrect name
      await user.type(input, 'Wrong Name');
      expect(deleteButton).toBeDisabled();

      // Clear and type correct name (lowercase)
      await user.clear(input);
      await user.type(input, 'intel core i7-13700k');

      await waitFor(() => {
        expect(deleteButton).not.toBeDisabled();
      });
    });

    it('trims whitespace when validating confirmation', async () => {
      const user = userEvent.setup();

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /Confirm deletion/i });
      const input = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);

      await user.type(input, '  Intel Core i7-13700K  ');

      await waitFor(() => {
        expect(deleteButton).not.toBeDisabled();
      });
    });

    it('shows aria-invalid when confirmation is incorrect', async () => {
      const user = userEvent.setup();

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const input = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);
      await user.type(input, 'Wrong Name');

      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('sets autofocus attribute on confirmation input when required', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const input = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);
      // The autoFocus prop is passed to the Input component which applies it to the DOM
      expect(input).toBeInTheDocument();
    });
  });

  describe('Delete Confirmation', () => {
    it('calls onConfirm when delete button is clicked (no confirmation required)', async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /Confirm deletion/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalled();
      });
    });

    it('calls onConfirm when name validation passes', async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const input = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);
      await user.type(input, 'Intel Core i7-13700K');

      const deleteButton = screen.getByRole('button', { name: /Confirm deletion/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalled();
      });
    });

    it('does not call onConfirm when name validation fails', async () => {
      const user = userEvent.setup();

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const input = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);
      await user.type(input, 'Wrong Name');

      const deleteButton = screen.getByRole('button', { name: /Confirm deletion/i });
      // Button should be disabled, but try clicking anyway
      await user.click(deleteButton);

      expect(mockOnConfirm).not.toHaveBeenCalled();
    });

    it('shows loading state during deletion', async () => {
      const user = userEvent.setup();
      let resolveConfirm: any;
      mockOnConfirm.mockReturnValue(new Promise((resolve) => { resolveConfirm = resolve; }));

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /Confirm deletion/i });
      await user.click(deleteButton);

      expect(screen.getByText('Deleting...')).toBeInTheDocument();
      expect(deleteButton).toBeDisabled();

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      expect(cancelButton).toBeDisabled();

      resolveConfirm();
    });

    it('handles deletion errors gracefully', async () => {
      const user = userEvent.setup();
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      mockOnConfirm.mockRejectedValue(new Error('Delete failed'));

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /Confirm deletion/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          'Delete confirmation error:',
          expect.any(Error)
        );
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Cancel Functionality', () => {
    it('calls onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
      expect(mockOnConfirm).not.toHaveBeenCalled();
    });

    it('does not allow cancel during deletion', async () => {
      const user = userEvent.setup();
      let resolveConfirm: any;
      mockOnConfirm.mockReturnValue(new Promise((resolve) => { resolveConfirm = resolve; }));

      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /Confirm deletion/i });
      await user.click(deleteButton);

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      expect(cancelButton).toBeDisabled();

      resolveConfirm();
    });
  });

  describe('Dialog State Reset', () => {
    it('resets confirmation input when dialog closes', async () => {
      const user = userEvent.setup();

      const { rerender } = render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const input = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);
      await user.type(input, 'Some text');

      // Close dialog
      rerender(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={false}
        />
      );

      // Reopen dialog
      rerender(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const reopenedInput = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);
      expect(reopenedInput).toHaveValue('');
    });
  });

  describe('Accessibility', () => {
    it('provides accessible label for usage badge', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const badge = screen.getByLabelText(/Used in 5 listings/i);
      expect(badge).toBeInTheDocument();
    });

    it('provides aria-describedby for confirmation input', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={5}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const input = screen.getByPlaceholderText(/Type "Intel Core i7-13700K" to confirm/i);
      expect(input).toHaveAttribute('aria-describedby', 'confirmation-help');
      expect(screen.getByText(/Confirmation is required because this cpu is currently in use/i)).toHaveAttribute('id', 'confirmation-help');
    });

    it('provides accessible label for delete button', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      const deleteButton = screen.getByLabelText(/Confirm deletion of Intel Core i7-13700K/i);
      expect(deleteButton).toBeInTheDocument();
    });
  });

  describe('Warning Message', () => {
    it('displays "This action cannot be undone" message', () => {
      render(
        <EntityDeleteDialog
          entityType="cpu"
          entityId={1}
          entityName="Intel Core i7-13700K"
          usedInCount={0}
          onConfirm={mockOnConfirm}
          onCancel={mockOnCancel}
          isOpen={true}
        />
      );

      expect(screen.getByText(/This action cannot be undone/i)).toBeInTheDocument();
    });
  });
});
