"use client";

import { type ReactNode, useEffect, useRef, useState } from 'react';
import { cn } from '../../lib/utils';

interface ResizablePaneProps {
  id: string;
  children: ReactNode;
  defaultHeight?: number;
  minHeight?: number;
  maxHeight?: number;
  className?: string;
}

export function ResizablePane({
  id,
  children,
  defaultHeight = 400,
  minHeight = 300,
  maxHeight = 800,
  className
}: ResizablePaneProps) {
  const storageKey = `pane-height-${id}`;
  const [height, setHeight] = useState(() => {
    if (typeof window === 'undefined') return defaultHeight;
    const saved = localStorage.getItem(storageKey);
    return saved ? Number(saved) : defaultHeight;
  });

  const paneRef = useRef<HTMLDivElement>(null);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    if (!isResizing) {
      localStorage.setItem(storageKey, String(height));
    }
  }, [height, isResizing, storageKey]);

  const handleMouseDown = () => {
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!paneRef.current) return;
      const rect = paneRef.current.getBoundingClientRect();
      const newHeight = e.clientY - rect.top;
      const constrained = Math.max(minHeight, Math.min(newHeight, maxHeight));
      setHeight(constrained);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, minHeight, maxHeight]);

  return (
    <div
      ref={paneRef}
      className={cn('relative overflow-hidden', className)}
      style={{ height: `${height}px` }}
      data-pane
    >
      <div className="h-full overflow-auto">
        {children}
      </div>

      {/* Resize handle */}
      <div
        className={cn(
          'absolute bottom-0 left-0 right-0 h-1 cursor-ns-resize bg-border hover:bg-primary/50 transition-colors',
          isResizing && 'bg-primary'
        )}
        onMouseDown={handleMouseDown}
      />
    </div>
  );
}
