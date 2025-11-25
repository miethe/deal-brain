'use client';

/**
 * PERF-002: Visual Virtualization Test Page
 *
 * This page demonstrates table virtualization with configurable row counts.
 * Use this to verify performance and behavior with different dataset sizes.
 *
 * Access: http://localhost:3020/test-virtualization
 */

import { useState } from 'react';
import { DataGrid } from '@/components/ui/data-grid';
import { ColumnDef } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface TestRow {
  id: number;
  name: string;
  value: number;
  category: string;
  description: string;
}

function generateData(count: number): TestRow[] {
  const categories = ['A', 'B', 'C', 'D', 'E'];
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Row ${i + 1}`,
    value: Math.floor(Math.random() * 1000),
    category: categories[i % categories.length],
    description: `This is test data for row ${i + 1}`,
  }));
}

const columns: ColumnDef<TestRow>[] = [
  {
    header: 'ID',
    accessorKey: 'id',
    size: 80,
  },
  {
    header: 'Name',
    accessorKey: 'name',
    size: 150,
  },
  {
    header: 'Value',
    accessorKey: 'value',
    size: 100,
  },
  {
    header: 'Category',
    accessorKey: 'category',
    size: 100,
    meta: {
      filterType: 'multi-select',
      options: [
        { label: 'A', value: 'A' },
        { label: 'B', value: 'B' },
        { label: 'C', value: 'C' },
        { label: 'D', value: 'D' },
        { label: 'E', value: 'E' },
      ],
    },
  },
  {
    header: 'Description',
    accessorKey: 'description',
    size: 300,
  },
];

export default function VirtualizationTestPage() {
  const [rowCount, setRowCount] = useState(500);
  const [data, setData] = useState(() => generateData(500));
  const [perfStats, setPerfStats] = useState({ rendered: 0, total: 0 });

  const regenerate = (count: number) => {
    setRowCount(count);
    const newData = generateData(count);
    setData(newData);
    setPerfStats({ rendered: 0, total: count });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Table Virtualization Test</h1>
        <p className="text-muted-foreground mt-1">
          PERF-002: Verify virtualization behavior with different dataset sizes
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <div className="text-sm font-medium mb-2">Dataset Size</div>
              <div className="space-y-2">
                <Button
                  onClick={() => regenerate(50)}
                  variant={rowCount === 50 ? 'default' : 'outline'}
                  size="sm"
                  className="w-full"
                >
                  50 rows (No virtualization)
                </Button>
                <Button
                  onClick={() => regenerate(100)}
                  variant={rowCount === 100 ? 'default' : 'outline'}
                  size="sm"
                  className="w-full"
                >
                  100 rows (Threshold)
                </Button>
                <Button
                  onClick={() => regenerate(500)}
                  variant={rowCount === 500 ? 'default' : 'outline'}
                  size="sm"
                  className="w-full"
                >
                  500 rows (Virtualized)
                </Button>
                <Button
                  onClick={() => regenerate(1000)}
                  variant={rowCount === 1000 ? 'default' : 'outline'}
                  size="sm"
                  className="w-full"
                >
                  1,000 rows (Virtualized)
                </Button>
                <Button
                  onClick={() => regenerate(5000)}
                  variant={rowCount === 5000 ? 'default' : 'outline'}
                  size="sm"
                  className="w-full"
                >
                  5,000 rows (Virtualized)
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Virtualization Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Row Height:</span>
              <span className="font-mono">48px</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Overscan:</span>
              <span className="font-mono">10 rows</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Threshold:</span>
              <span className="font-mono">100 rows</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Status:</span>
              <span className={rowCount > 100 ? 'text-green-600 font-semibold' : 'text-amber-600'}>
                {rowCount > 100 ? '✅ Active' : '⚠️ Inactive'}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Rows:</span>
              <span className="font-mono">{data.length.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Expected Rendered:</span>
              <span className="font-mono">
                {rowCount > 100 ? '~20-30' : data.length.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Reduction:</span>
              <span className="font-mono">
                {rowCount > 100
                  ? `${Math.round((1 - 25 / data.length) * 100)}%`
                  : '0%'}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Test Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <strong>1. Verify Threshold Behavior:</strong>
            <ul className="list-disc list-inside ml-4 mt-1 space-y-1 text-muted-foreground">
              <li>Select "50 rows" - virtualization should be INACTIVE</li>
              <li>Select "100 rows" - virtualization at threshold (may activate)</li>
              <li>Select "500 rows" - virtualization should be ACTIVE</li>
            </ul>
          </div>
          <div>
            <strong>2. Test Performance:</strong>
            <ul className="list-disc list-inside ml-4 mt-1 space-y-1 text-muted-foreground">
              <li>Open Chrome DevTools → Performance tab</li>
              <li>Start recording</li>
              <li>Scroll rapidly through the table</li>
              <li>Stop recording and verify 60fps</li>
            </ul>
          </div>
          <div>
            <strong>3. Verify Features:</strong>
            <ul className="list-disc list-inside ml-4 mt-1 space-y-1 text-muted-foreground">
              <li>Try filtering by category (multi-select filter)</li>
              <li>Try sorting columns</li>
              <li>Verify smooth scrolling with no gaps</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      <div>
        <DataGrid
          data={data}
          columns={columns}
          enableFilters
          estimatedRowHeight={48}
          virtualizationThreshold={100}
          density="comfortable"
          className="border"
        />
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="text-xs text-muted-foreground space-y-1">
            <p><strong>Note:</strong> Open browser DevTools to inspect DOM nodes.</p>
            <p>
              With virtualization active, you should see ~20-30 table rows in the DOM
              instead of {data.length.toLocaleString()} rows.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
