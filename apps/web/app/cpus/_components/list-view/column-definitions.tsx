/**
 * Column definitions for CPU table
 *
 * Defines table columns with sortability, width, alignment, and formatting.
 */

import type { CPURecord } from '@/types/cpus'

export type SortableColumn =
  | 'name'
  | 'manufacturer'
  | 'socket'
  | 'cores'
  | 'tdp_w'
  | 'cpu_mark_single'
  | 'cpu_mark_multi'

export interface ColumnDefinition {
  key: string
  label: string
  sortable: boolean
  sortKey?: SortableColumn
  width: string
  align: 'left' | 'center' | 'right'
  formatter?: (cpu: CPURecord) => React.ReactNode | string
}

export const columns: ColumnDefinition[] = [
  {
    key: 'name',
    label: 'Name',
    sortable: true,
    sortKey: 'name',
    width: 'flex-1 min-w-[250px]',
    align: 'left'
  },
  {
    key: 'manufacturer',
    label: 'Manufacturer',
    sortable: true,
    sortKey: 'manufacturer',
    width: 'w-[140px]',
    align: 'left'
  },
  {
    key: 'socket',
    label: 'Socket',
    sortable: true,
    sortKey: 'socket',
    width: 'w-[120px]',
    align: 'left'
  },
  {
    key: 'cores',
    label: 'Cores/Threads',
    sortable: true,
    sortKey: 'cores',
    width: 'w-[120px]',
    align: 'center',
    formatter: (cpu) => {
      if (cpu.cores && cpu.threads) {
        return `${cpu.cores}C/${cpu.threads}T`
      }
      return '-'
    }
  },
  {
    key: 'tdp',
    label: 'TDP',
    sortable: true,
    sortKey: 'tdp_w',
    width: 'w-[80px]',
    align: 'right',
    formatter: (cpu) => {
      if (cpu.tdp_w) {
        return `${cpu.tdp_w}W`
      }
      return '-'
    }
  },
  {
    key: 'cpu_mark_single',
    label: 'ST Mark',
    sortable: true,
    sortKey: 'cpu_mark_single',
    width: 'w-[100px]',
    align: 'right',
    formatter: (cpu) => {
      if (cpu.cpu_mark_single) {
        return cpu.cpu_mark_single.toLocaleString()
      }
      return '-'
    }
  },
  {
    key: 'cpu_mark_multi',
    label: 'MT Mark',
    sortable: true,
    sortKey: 'cpu_mark_multi',
    width: 'w-[100px]',
    align: 'right',
    formatter: (cpu) => {
      if (cpu.cpu_mark_multi) {
        return cpu.cpu_mark_multi.toLocaleString()
      }
      return '-'
    }
  },
  {
    key: 'igpu_mark',
    label: 'iGPU',
    sortable: false,
    width: 'w-[100px]',
    align: 'right',
    formatter: (cpu) => {
      if (cpu.igpu_mark) {
        return cpu.igpu_mark.toLocaleString()
      }
      return '-'
    }
  },
  {
    key: 'actions',
    label: 'Actions',
    sortable: false,
    width: 'w-[120px]',
    align: 'center'
  }
]

/**
 * Get cell value for sorting
 */
export function getSortValue(cpu: CPURecord, key: SortableColumn): any {
  switch (key) {
    case 'name':
      return cpu.name?.toLowerCase() ?? ''
    case 'manufacturer':
      return cpu.manufacturer?.toLowerCase() ?? ''
    case 'socket':
      return cpu.socket?.toLowerCase() ?? ''
    case 'cores':
      return cpu.cores ?? -Infinity
    case 'tdp_w':
      return cpu.tdp_w ?? -Infinity
    case 'cpu_mark_single':
      return cpu.cpu_mark_single ?? -Infinity
    case 'cpu_mark_multi':
      return cpu.cpu_mark_multi ?? -Infinity
    default:
      return ''
  }
}
