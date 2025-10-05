/**
 * @jest-environment jsdom
 */

import { render, screen } from '@testing-library/react';
import { DualMetricCell } from '../components/listings/dual-metric-cell';

describe('DualMetricCell', () => {
  it('renders raw value when no adjusted value provided', () => {
    render(<DualMetricCell raw={0.15} adjusted={null} prefix="$" decimals={2} />);

    expect(screen.getByText('$0.15')).toBeInTheDocument();
  });

  it('displays improvement indicator when adjusted is lower', () => {
    render(<DualMetricCell raw={0.20} adjusted={0.16} prefix="$" decimals={2} />);

    expect(screen.getByText('$0.20')).toBeInTheDocument();
    expect(screen.getByText(/\$0\.16/)).toBeInTheDocument();
    expect(screen.getByText(/↓20%/)).toBeInTheDocument();
  });

  it('displays degradation indicator when adjusted is higher', () => {
    render(<DualMetricCell raw={0.15} adjusted={0.18} prefix="$" decimals={2} />);

    expect(screen.getByText('$0.15')).toBeInTheDocument();
    expect(screen.getByText(/\$0\.18/)).toBeInTheDocument();
    expect(screen.getByText(/↑20%/)).toBeInTheDocument();
  });

  it('handles null raw value gracefully', () => {
    render(<DualMetricCell raw={null} adjusted={null} prefix="$" decimals={2} />);

    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('handles undefined raw value gracefully', () => {
    render(<DualMetricCell raw={undefined} adjusted={undefined} prefix="$" decimals={2} />);

    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('handles zero raw value correctly', () => {
    render(<DualMetricCell raw={0} adjusted={0} prefix="$" decimals={2} />);

    expect(screen.getByText('$0.00')).toBeInTheDocument();
  });

  it('uses custom prefix and suffix', () => {
    render(<DualMetricCell raw={125} adjusted={null} prefix="" suffix="W" decimals={0} />);

    expect(screen.getByText('125W')).toBeInTheDocument();
  });

  it('respects decimal precision', () => {
    render(<DualMetricCell raw={0.12345} adjusted={null} prefix="$" decimals={3} />);

    expect(screen.getByText('$0.123')).toBeInTheDocument();
  });

  it('shows no change indicator when values are equal', () => {
    const { container } = render(<DualMetricCell raw={0.15} adjusted={0.15} prefix="$" decimals={2} />);

    expect(screen.getByText('$0.15')).toBeInTheDocument();
    // Should not show percentage change
    expect(container.textContent).not.toMatch(/↓/);
    expect(container.textContent).not.toMatch(/↑/);
  });
});
