'use client';

import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  XCircle,
} from 'lucide-react';
import { BulkImportStatus, PerRowImportStatus } from '@/hooks/useImportPolling';
import { cn } from '@/lib/utils';

interface BulkImportProgressProps {
  status: BulkImportStatus;
  isLoading?: boolean;
}

export function BulkImportProgress({
  status,
  isLoading = false,
}: BulkImportProgressProps) {
  const progressPercent = Math.round(
    (status.completed / (status.total_urls || 1)) * 100
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Bulk Import Progress</CardTitle>
        <CardDescription>
          {status.total_urls} URLs - {status.completed} completed
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex justify-between items-baseline">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-sm text-gray-600">{progressPercent}%</span>
          </div>
          <Progress value={progressPercent} className="h-3" />
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <StatusCard
            label="Total"
            value={status.total_urls}
            icon={<Clock className="w-4 h-4" />}
            className="bg-blue-50"
          />

          <StatusCard
            label="Complete"
            value={status.success}
            icon={<CheckCircle className="w-4 h-4 text-green-600" />}
            className="bg-green-50"
          />

          <StatusCard
            label="Partial"
            value={status.partial}
            icon={<AlertCircle className="w-4 h-4 text-yellow-600" />}
            className="bg-yellow-50"
          />

          <StatusCard
            label="Running"
            value={status.running}
            icon={<Zap className="w-4 h-4 text-blue-600 animate-pulse" />}
            className="bg-blue-50"
          />

          <StatusCard
            label="Failed"
            value={status.failed}
            icon={<XCircle className="w-4 h-4 text-red-600" />}
            className="bg-red-50"
          />
        </div>

        {/* Per-URL Status (if showing details) */}
        {status.per_row_status.length > 0 && (
          <div className="space-y-2 mt-6">
            <h4 className="text-sm font-semibold">Recent Imports</h4>

            <div className="space-y-2 max-h-48 overflow-y-auto">
              {status.per_row_status.slice(0, 5).map((row) => (
                <PerRowStatusItem key={row.url} row={row} />
              ))}

              {status.per_row_status.length > 5 && (
                <p className="text-xs text-gray-500 text-center py-2">
                  ... and {status.per_row_status.length - 5} more
                </p>
              )}
            </div>
          </div>
        )}

        {/* Completion Message */}
        {status.status === 'complete' && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800 font-medium">
              Import completed! {status.partial} listing(s) need data completion.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface StatusCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  className?: string;
}

function StatusCard({ label, value, icon, className }: StatusCardProps) {
  return (
    <div
      className={cn(
        'p-3 rounded-lg text-center',
        className || 'bg-gray-50'
      )}
    >
      <div className="flex justify-center mb-2">{icon}</div>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs text-gray-600">{label}</div>
    </div>
  );
}

interface PerRowStatusItemProps {
  row: PerRowImportStatus;
}

function PerRowStatusItem({ row }: PerRowStatusItemProps) {
  const getQualityBadge = (quality: 'full' | 'partial' | null) => {
    switch (quality) {
      case 'full':
        return (
          <Badge variant="default" className="bg-green-600 text-white">
            Complete
          </Badge>
        );
      case 'partial':
        return (
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            Needs Data
          </Badge>
        );
      default:
        return <Badge variant="outline">Pending</Badge>;
    }
  };

  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
      <div className="flex-1 truncate">
        <p className="text-gray-700 truncate" title={row.url}>
          {row.url}
        </p>
      </div>

      <div className="flex items-center gap-2 ml-2">
        <span
          className={cn(
            'px-2 py-1 rounded text-xs font-medium',
            getStatusColor(row.status)
          )}
        >
          {row.status}
        </span>

        {row.listing_id && getQualityBadge(row.quality)}
      </div>
    </div>
  );
}

function getStatusColor(
  status: 'queued' | 'running' | 'complete' | 'failed'
) {
  switch (status) {
    case 'complete':
      return 'bg-green-100 text-green-800';
    case 'running':
      return 'bg-blue-100 text-blue-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'queued':
      return 'bg-gray-100 text-gray-800';
  }
}
