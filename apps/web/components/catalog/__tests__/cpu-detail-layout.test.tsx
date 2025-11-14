/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CPUDetailLayout } from '../cpu-detail-layout';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: any) => <a href={href}>{children}</a>;
});

// Mock hooks
const mockUpdateCpuMutate = jest.fn();
const mockDeleteCpuMutate = jest.fn();

jest.mock('@/hooks/use-entity-mutations', () => ({
  useUpdateCpu: jest.fn(() => ({
    mutateAsync: mockUpdateCpuMutate,
  })),
  useDeleteCpu: jest.fn((cpuId: number, options: any) => ({
    mutateAsync: async () => {
      await mockDeleteCpuMutate();
      options?.onSuccess?.();
    },
  })),
}));

// Mock toast
const mockToast = jest.fn();
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock EntityEditModal
jest.mock('@/components/entity/entity-edit-modal', () => ({
  EntityEditModal: ({ isOpen, onClose, onSubmit, initialValues }: any) => (
    isOpen ? (
      <div data-testid="edit-modal">
        <h2>Edit CPU</h2>
        <button onClick={async () => {
          await onSubmit(initialValues);
        }}>
          Save Changes
        </button>
        <button onClick={onClose}>Cancel</button>
      </div>
    ) : null
  ),
}));

// Mock EntityDeleteDialog
jest.mock('@/components/entity/entity-delete-dialog', () => ({
  EntityDeleteDialog: ({ isOpen, onCancel, onConfirm, entityName, usedInCount }: any) => (
    isOpen ? (
      <div data-testid="delete-dialog">
        <h2>Delete CPU</h2>
        <p>Entity: {entityName}</p>
        <p>Used in {usedInCount} listings</p>
        <button onClick={onConfirm}>Confirm Delete</button>
        <button onClick={onCancel}>Cancel</button>
      </div>
    ) : null
  ),
}));

// Mock UI components
jest.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
}));

jest.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: any) => <span>{children}</span>,
}));

jest.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>{children}</button>
  ),
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  ChevronRight: () => <span>→</span>,
  Cpu: () => <span>CPU</span>,
  TrendingUp: () => <span>↑</span>,
  Zap: () => <span>⚡</span>,
  Pencil: () => <span>✏️</span>,
  Trash2: () => <span>🗑️</span>,
}));

describe('CPUDetailLayout', () => {
  const mockCpu = {
    id: 1,
    model: 'Intel Core i7-13700K',
    manufacturer: 'Intel',
    generation: '13th Gen',
    cores: 16,
    threads: 24,
    base_clock_ghz: 3.4,
    boost_clock_ghz: 5.4,
    tdp_watts: 125,
    cpu_mark: 45000,
    single_thread_rating: 4200,
    igpu_mark: 1500,
    socket: 'LGA1700',
    igpu_model: 'Intel UHD Graphics 770',
    release_year: 2023,
    notes: 'High-performance CPU for gaming and productivity',
    passmark_slug: 'intel-core-i7-13700k',
    passmark_category: 'Desktop',
    passmark_id: '5120',
    attributes_json: {},
  };

  const mockListings = [
    {
      id: 101,
      title: 'Gaming PC - Intel i7-13700K',
      price_usd: 1200,
      adjusted_price_usd: 1150,
      manufacturer: 'Custom Build',
      model_number: 'GAMING-001',
      form_factor: 'Mid Tower',
      condition: 'new' as const,
      status: 'active' as const,
      cpu_name: 'Intel Core i7-13700K',
      ram_gb: 32,
      primary_storage_gb: 1000,
      primary_storage_type: 'NVMe SSD',
    },
    {
      id: 102,
      title: 'Workstation - Intel i7-13700K',
      price_usd: 1500,
      adjusted_price_usd: null,
      manufacturer: 'Dell',
      model_number: 'WS-500',
      form_factor: 'Tower',
      condition: 'refurbished' as const,
      status: 'active' as const,
      cpu_name: 'Intel Core i7-13700K',
      ram_gb: 64,
      primary_storage_gb: 2000,
      primary_storage_type: 'SSD',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('renders CPU details correctly', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      expect(screen.getByText('Intel Core i7-13700K')).toBeInTheDocument();
      expect(screen.getByText('Intel')).toBeInTheDocument();

      const genElements = screen.getAllByText('13th Gen');
      expect(genElements.length).toBeGreaterThan(0);

      const yearElements = screen.getAllByText('2023');
      expect(yearElements.length).toBeGreaterThan(0);
    });

    it('displays usage count badge', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      expect(screen.getByText(/Used in 2 listings/i)).toBeInTheDocument();
    });

    it('renders specifications section', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      expect(screen.getByText('Specifications')).toBeInTheDocument();
      expect(screen.getByText('16')).toBeInTheDocument(); // cores
      expect(screen.getByText('24')).toBeInTheDocument(); // threads
      expect(screen.getByText('125W')).toBeInTheDocument(); // TDP
      expect(screen.getByText('LGA1700')).toBeInTheDocument(); // socket
    });

    it('renders benchmark scores section', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      expect(screen.getByText('Benchmark Scores')).toBeInTheDocument();
      expect(screen.getByText('45,000')).toBeInTheDocument(); // cpu_mark
      expect(screen.getByText('4,200')).toBeInTheDocument(); // single_thread_rating
      expect(screen.getByText('1,500')).toBeInTheDocument(); // igpu_mark
    });

    it('renders listings using this CPU', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      expect(screen.getByText('Gaming PC - Intel i7-13700K')).toBeInTheDocument();
      expect(screen.getByText('Workstation - Intel i7-13700K')).toBeInTheDocument();
    });

    it('shows empty state when no listings use this CPU', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={[]} />);

      expect(screen.getByText(/No listings currently use this CPU/i)).toBeInTheDocument();
    });
  });

  describe('Edit Functionality', () => {
    it('renders edit button', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const editButton = screen.getByRole('button', { name: /Edit Intel Core i7-13700K/i });
      expect(editButton).toBeInTheDocument();
    });

    it('opens edit modal when edit button is clicked', async () => {
      const user = userEvent.setup();
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const editButton = screen.getByRole('button', { name: /Edit Intel Core i7-13700K/i });
      await user.click(editButton);

      expect(screen.getByTestId('edit-modal')).toBeInTheDocument();
      expect(screen.getByText('Edit CPU')).toBeInTheDocument();
    });

    it('closes edit modal when cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const editButton = screen.getByRole('button', { name: /Edit Intel Core i7-13700K/i });
      await user.click(editButton);

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByTestId('edit-modal')).not.toBeInTheDocument();
      });
    });

    it('submits edit form and closes modal on success', async () => {
      const user = userEvent.setup();
      mockUpdateCpuMutate.mockResolvedValue(undefined);

      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const editButton = screen.getByRole('button', { name: /Edit Intel Core i7-13700K/i });
      await user.click(editButton);

      const saveButton = screen.getByRole('button', { name: /Save Changes/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(mockUpdateCpuMutate).toHaveBeenCalled();
        expect(screen.queryByTestId('edit-modal')).not.toBeInTheDocument();
      });
    });
  });

  describe('Delete Functionality', () => {
    it('renders delete button', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const deleteButton = screen.getByRole('button', { name: /Delete Intel Core i7-13700K/i });
      expect(deleteButton).toBeInTheDocument();
    });

    it('opens delete dialog when delete button is clicked', async () => {
      const user = userEvent.setup();
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const deleteButton = screen.getByRole('button', { name: /Delete Intel Core i7-13700K/i });
      await user.click(deleteButton);

      expect(screen.getByTestId('delete-dialog')).toBeInTheDocument();
      expect(screen.getByText('Delete CPU')).toBeInTheDocument();
      expect(screen.getByText('Entity: Intel Core i7-13700K')).toBeInTheDocument();
    });

    it('passes correct usage count to delete dialog', async () => {
      const user = userEvent.setup();
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const deleteButton = screen.getByRole('button', { name: /Delete Intel Core i7-13700K/i });
      await user.click(deleteButton);

      const usageElements = screen.getAllByText(/Used in 2 listings/i);
      expect(usageElements.length).toBeGreaterThan(0);
    });

    it('closes delete dialog when cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const deleteButton = screen.getByRole('button', { name: /Delete Intel Core i7-13700K/i });
      await user.click(deleteButton);

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByTestId('delete-dialog')).not.toBeInTheDocument();
      });
    });

    it('deletes entity and redirects on confirmation', async () => {
      const user = userEvent.setup();
      mockDeleteCpuMutate.mockResolvedValue(undefined);

      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const deleteButton = screen.getByRole('button', { name: /Delete Intel Core i7-13700K/i });
      await user.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /Confirm Delete/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockDeleteCpuMutate).toHaveBeenCalled();
        expect(mockPush).toHaveBeenCalledWith('/catalog/cpus');
      });
    });
  });

  describe('Breadcrumb Navigation', () => {
    it('renders breadcrumb trail', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      expect(screen.getByText('Listings')).toBeInTheDocument();
      expect(screen.getByText('Catalog')).toBeInTheDocument();
      expect(screen.getByText('CPU Details')).toBeInTheDocument();
    });
  });

  describe('Listing Cards', () => {
    it('displays listing prices correctly', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      // First listing has adjusted price
      expect(screen.getByText('$1,150')).toBeInTheDocument();
      expect(screen.getByText('$1,200')).toBeInTheDocument(); // crossed out

      // Second listing has no adjusted price
      expect(screen.getByText('$1,500')).toBeInTheDocument();
    });

    it('displays listing metadata', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      expect(screen.getByText('Custom Build')).toBeInTheDocument();
      expect(screen.getByText('Mid Tower')).toBeInTheDocument();
      expect(screen.getByText('32GB RAM')).toBeInTheDocument();
      expect(screen.getByText('1000GB NVMe SSD')).toBeInTheDocument();
    });

    it('links to listing detail pages', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const links = screen.getAllByRole('link');
      const listingLinks = links.filter(link =>
        link.getAttribute('href')?.startsWith('/listings/')
      );

      expect(listingLinks.length).toBeGreaterThan(0);
      expect(listingLinks[0]).toHaveAttribute('href', '/listings/101');
    });
  });

  describe('Conditional Rendering', () => {
    it('hides specifications section when no specs are available', () => {
      const minimalCpu = {
        ...mockCpu,
        cores: null,
        threads: null,
        base_clock_ghz: null,
        boost_clock_ghz: null,
        tdp_watts: null,
        socket: null,
        generation: null,
        igpu_model: null,
        release_year: null,
      };

      render(<CPUDetailLayout cpu={minimalCpu} listings={mockListings} />);

      expect(screen.queryByText('Specifications')).not.toBeInTheDocument();
    });

    it('hides benchmark section when no benchmarks are available', () => {
      const noBenchmarksCpu = {
        ...mockCpu,
        cpu_mark: null,
        single_thread_rating: null,
        igpu_mark: null,
      };

      render(<CPUDetailLayout cpu={noBenchmarksCpu} listings={mockListings} />);

      expect(screen.queryByText('Benchmark Scores')).not.toBeInTheDocument();
    });

    it('displays notes when available', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      expect(screen.getByText('High-performance CPU for gaming and productivity')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper heading hierarchy', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const h1 = screen.getByRole('heading', { level: 1, name: 'Intel Core i7-13700K' });
      expect(h1).toBeInTheDocument();

      const h3s = screen.getAllByRole('heading', { level: 3 });
      expect(h3s.length).toBeGreaterThan(0);
    });

    it('provides aria-label for edit button', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const editButton = screen.getByLabelText(/Edit Intel Core i7-13700K/i);
      expect(editButton).toBeInTheDocument();
    });

    it('provides aria-label for delete button', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const deleteButton = screen.getByLabelText(/Delete Intel Core i7-13700K/i);
      expect(deleteButton).toBeInTheDocument();
    });

    it('has accessible breadcrumb navigation', () => {
      render(<CPUDetailLayout cpu={mockCpu} listings={mockListings} />);

      const breadcrumb = screen.getByLabelText('Breadcrumb');
      expect(breadcrumb).toBeInTheDocument();
    });
  });
});
