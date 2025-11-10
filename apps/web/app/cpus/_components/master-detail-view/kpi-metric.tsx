'use client'

import React from 'react'

interface KpiMetricProps {
  label: string
  value: string | number
  accent?: 'good' | 'warn' | 'neutral'
  className?: string
}

export const KpiMetric = React.memo(function KpiMetric({
  label,
  value,
  accent = 'neutral',
  className = ''
}: KpiMetricProps) {
  const accentClasses = {
    good: 'border-emerald-500/20 bg-emerald-50/50 dark:bg-emerald-950/20',
    warn: 'border-amber-500/20 bg-amber-50/50 dark:bg-amber-950/20',
    neutral: 'border-border bg-muted/50'
  }

  const valueClasses = {
    good: 'text-emerald-700 dark:text-emerald-400',
    warn: 'text-amber-700 dark:text-amber-400',
    neutral: 'text-foreground'
  }

  return (
    <div
      className={`rounded-lg border p-4 ${accentClasses[accent]} ${className}`}
    >
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${valueClasses[accent]}`}>
        {value}
      </div>
    </div>
  )
})
