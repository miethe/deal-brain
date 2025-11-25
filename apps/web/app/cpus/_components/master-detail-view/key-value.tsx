'use client'

import React from 'react'

interface KeyValueProps {
  label: string
  value: string | number | React.ReactNode
  className?: string
}

export const KeyValue = React.memo(function KeyValue({
  label,
  value,
  className = ''
}: KeyValueProps) {
  return (
    <div className={`space-y-1 ${className}`}>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-medium">
        {value || '-'}
      </div>
    </div>
  )
})
