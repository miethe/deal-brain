'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CheckCircle2, XCircle, Loader2, Clock, ChevronLeft, ChevronRight, ExternalLink, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { BulkStatusTableProps } from './bulk-import-types';

/**
 * Get status badge variant and icon
 */
function getStatusBadge(status: string) {
  switch (status) {
    case 'complete':
      return {
        variant: 'default' as const,
        className: 'bg-green-600 hover:bg-green-700 text-white',
        icon: <CheckCircle2 className="h-3 w-3" />,
        label: 'Complete',
      };
    case 'partial':
      return {
        variant: 'default' as const,
        className: 'bg-yellow-600 hover:bg-yellow-700 text-white',
        icon: <AlertTriangle className="h-3 w-3" />,
        label: 'Partial',
      };
    case 'failed':
      return {
        variant: 'destructive' as const,
        className: '',
        icon: <XCircle className="h-3 w-3" />,
        label: 'Failed',
      };
    case 'running':
      return {
        variant: 'default' as const,
        className: 'bg-blue-600 hover:bg-blue-700 text-white',
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        label: 'Running',
      };
    case 'queued':
      return {
        variant: 'secondary' as const,
        className: '',
        icon: <Clock className="h-3 w-3" />,
        label: 'Queued',
      };
    default:
      return {
        variant: 'outline' as const,
        className: '',
        icon: null,
        label: status,
      };
  }
}

/**
 * Truncate URL for display
 */
function truncateUrl(url: string, maxLength: number = 50): string {
  if (url.length <= maxLength) return url;
  const start = url.substring(0, maxLength - 10);
  const end = url.substring(url.length - 10);
  return `${start}...${end}`;
}

export function BulkStatusTable({ bulkJobId, data, onRefresh }: BulkStatusTableProps) {
  const router = useRouter();
  const [currentPage, setCurrentPage] = useState(0);
  const rowsPerPage = 50;

  // Calculate pagination
  const totalRows = data.per_row_status.length;
  const totalPages = Math.ceil(data.total_urls / rowsPerPage);
  const startRow = currentPage * rowsPerPage + 1;
  const endRow = Math.min((currentPage + 1) * rowsPerPage, data.total_urls);

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
      onRefresh?.();
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
      onRefresh?.();
    }
  };

  const handleViewListing = (listingId: number) => {
    router.push(`/listings/${listingId}`);
  };

  return (
    <div className="space-y-4">
      {/* Table Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">
          Per-URL Status
          <span className="ml-2 text-muted-foreground">
            ({startRow}-{endRow} of {data.total_urls})
          </span>
        </h3>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePreviousPage}
            disabled={currentPage === 0}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-xs text-muted-foreground tabular-nums">
            Page {currentPage + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNextPage}
            disabled={currentPage >= totalPages - 1 || !data.has_more}
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40%]">URL</TableHead>
              <TableHead className="w-[15%]">Status</TableHead>
              <TableHead className="w-[15%]">Listing ID</TableHead>
              <TableHead className="w-[30%]">Result / Error</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.per_row_status.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                  No data available
                </TableCell>
              </TableRow>
            ) : (
              data.per_row_status.map((row, index) => {
                const statusBadge = getStatusBadge(row.status);

                return (
                  <TableRow key={`${row.url}-${index}`}>
                    {/* URL Column */}
                    <TableCell className="font-mono text-xs">
                      <a
                        href={row.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline inline-flex items-center gap-1"
                        title={row.url}
                      >
                        {truncateUrl(row.url)}
                        <ExternalLink className="h-3 w-3 flex-shrink-0" />
                      </a>
                    </TableCell>

                    {/* Status Column */}
                    <TableCell>
                      <Badge
                        variant={statusBadge.variant}
                        className={cn('gap-1', statusBadge.className)}
                      >
                        {statusBadge.icon}
                        {statusBadge.label}
                      </Badge>
                    </TableCell>

                    {/* Listing ID Column */}
                    <TableCell>
                      {row.listing_id ? (
                        <Button
                          variant="link"
                          size="sm"
                          onClick={() => handleViewListing(row.listing_id!)}
                          className="h-auto p-0 text-xs"
                        >
                          #{row.listing_id}
                        </Button>
                      ) : (
                        <span className="text-muted-foreground text-xs">-</span>
                      )}
                    </TableCell>

                    {/* Result / Error Column */}
                    <TableCell>
                      {row.error ? (
                        <span className="text-xs text-destructive">{row.error}</span>
                      ) : row.listing_id ? (
                        <span className="text-xs text-green-600 dark:text-green-400">
                          Imported successfully
                        </span>
                      ) : row.status === 'running' ? (
                        <span className="text-xs text-muted-foreground">Processing...</span>
                      ) : row.status === 'queued' ? (
                        <span className="text-xs text-muted-foreground">Waiting...</span>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Keyboard navigation hint */}
      <p className="text-xs text-muted-foreground text-center">
        Use arrow buttons or keyboard shortcuts to navigate pages
      </p>
    </div>
  );
}
