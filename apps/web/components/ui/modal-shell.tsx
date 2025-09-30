"use client";

import { ReactNode } from "react";

import { DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "./dialog";

interface ModalShellProps {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export function ModalShell({ title, description, children, footer, className }: ModalShellProps) {
  return (
    <DialogContent className={className ?? "max-w-3xl gap-6 p-6 shadow-2xl sm:px-8"}>
      <DialogHeader className="space-y-1 text-left">
        <DialogTitle className="text-xl font-semibold tracking-tight">{title}</DialogTitle>
        {description ? <DialogDescription>{description}</DialogDescription> : null}
      </DialogHeader>
      <div className="max-h-[60vh] overflow-y-auto pr-1">{children}</div>
      {footer ? <DialogFooter className="sticky bottom-0 flex justify-between gap-3 border-t bg-background/95 px-0 pt-4">{footer}</DialogFooter> : null}
    </DialogContent>
  );
}
