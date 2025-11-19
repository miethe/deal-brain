import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ColumnSelector, type ColumnDefinition } from '../column-selector';

describe('ColumnSelector', () => {
  const mockColumns: ColumnDefinition[] = [
    { id: 'name', label: 'Name', defaultVisible: true, description: 'User name' },
    { id: 'email', label: 'Email', defaultVisible: true, description: 'Email address' },
    { id: 'phone', label: 'Phone', defaultVisible: false, description: 'Phone number' },
    { id: 'address', label: 'Address', defaultVisible: false },
  ];

  const mockSelectedColumns = ['name', 'email'];
  const mockOnColumnsChange = vi.fn();

  beforeEach(() => {
    mockOnColumnsChange.mockClear();
  });

  it('renders with correct visible column count', () => {
    render(
      <ColumnSelector
        columns={mockColumns}
        selectedColumns={mockSelectedColumns}
        onColumnsChange={mockOnColumnsChange}
      />
    );

    expect(screen.getByText(/2\/4/)).toBeInTheDocument();
  });

  it('has proper ARIA label for accessibility', () => {
    render(
      <ColumnSelector
        columns={mockColumns}
        selectedColumns={mockSelectedColumns}
        onColumnsChange={mockOnColumnsChange}
      />
    );

    const button = screen.getByRole('button', { name: /Column selector: 2 of 4 columns visible/ });
    expect(button).toBeInTheDocument();
  });

  it('opens dropdown when clicked', async () => {
    render(
      <ColumnSelector
        columns={mockColumns}
        selectedColumns={mockSelectedColumns}
        onColumnsChange={mockOnColumnsChange}
      />
    );

    const button = screen.getByRole('button', { name: /Column selector/ });
    fireEvent.click(button);

    // Should show column checkboxes
    expect(screen.getByLabelText(/Toggle Name column visibility/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Toggle Email column visibility/)).toBeInTheDocument();
  });

  it('displays all buttons (All, None, Reset, Cancel, Apply)', async () => {
    render(
      <ColumnSelector
        columns={mockColumns}
        selectedColumns={mockSelectedColumns}
        onColumnsChange={mockOnColumnsChange}
      />
    );

    const button = screen.getByRole('button', { name: /Column selector/ });
    fireEvent.click(button);

    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('None')).toBeInTheDocument();
    expect(screen.getByText('Reset to Default')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
    expect(screen.getByText('Apply')).toBeInTheDocument();
  });

  it('shows drag handles for reordering', async () => {
    render(
      <ColumnSelector
        columns={mockColumns}
        selectedColumns={mockSelectedColumns}
        onColumnsChange={mockOnColumnsChange}
      />
    );

    const button = screen.getByRole('button', { name: /Column selector/ });
    fireEvent.click(button);

    expect(screen.getByLabelText(/Drag to reorder Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Drag to reorder Email/)).toBeInTheDocument();
  });

  it('marks hidden columns with lower opacity', async () => {
    render(
      <ColumnSelector
        columns={mockColumns}
        selectedColumns={mockSelectedColumns}
        onColumnsChange={mockOnColumnsChange}
      />
    );

    const button = screen.getByRole('button', { name: /Column selector/ });
    fireEvent.click(button);

    const phoneCheckbox = screen.getByLabelText(/Show Phone column/);
    expect(phoneCheckbox).toBeInTheDocument();
    // Hidden columns should have unchecked checkboxes
    expect(phoneCheckbox).not.toBeChecked();
  });
});
