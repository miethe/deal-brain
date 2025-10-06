"use client";

import * as React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Separator } from "../ui/separator";
import { CpuRecord } from "../../types/listings";

interface CpuDetailsModalProps {
  cpu: CpuRecord | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function CpuDetailsModalComponent({
  cpu,
  open,
  onOpenChange,
}: CpuDetailsModalProps) {
  if (!cpu) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{cpu.name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <Section title="Core Specifications">
            <SpecRow label="Manufacturer" value={cpu.manufacturer} />
            <SpecRow label="Socket" value={cpu.socket} />
            <SpecRow label="Cores" value={cpu.cores} />
            <SpecRow label="Threads" value={cpu.threads} />
          </Section>

          <Separator />

          <Section title="Performance Metrics">
            <SpecRow
              label="CPU Mark (Multi)"
              value={cpu.cpu_mark_multi?.toLocaleString()}
            />
            <SpecRow
              label="CPU Mark (Single)"
              value={cpu.cpu_mark_single?.toLocaleString()}
            />
            <SpecRow
              label="iGPU Mark"
              value={cpu.igpu_mark?.toLocaleString()}
            />
          </Section>

          <Separator />

          <Section title="Power & Thermal">
            <SpecRow
              label="TDP"
              value={cpu.tdp_w ? `${cpu.tdp_w}W` : null}
            />
            <SpecRow label="Release Year" value={cpu.release_year} />
          </Section>

          {cpu.igpu_model && (
            <>
              <Separator />
              <Section title="Graphics">
                <SpecRow label="Integrated GPU" value={cpu.igpu_model} />
              </Section>
            </>
          )}

          {cpu.notes && (
            <>
              <Separator />
              <Section title="Notes">
                <p className="text-sm">{cpu.notes}</p>
              </Section>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h4 className="text-sm font-semibold mb-2">{title}</h4>
      <div className="grid grid-cols-2 gap-3">{children}</div>
    </div>
  );
}

function SpecRow({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-muted-foreground">{label}:</span>
      <span className="font-medium">{value ?? "N/A"}</span>
    </div>
  );
}

export const CpuDetailsModal = React.memo(CpuDetailsModalComponent);
