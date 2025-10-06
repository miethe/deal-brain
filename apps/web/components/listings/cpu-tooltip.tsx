"use client";

import * as React from "react";
import { Info } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Button } from "../ui/button";
import { CpuRecord } from "../../types/listings";

interface CpuTooltipProps {
  cpu: CpuRecord;
  onViewDetails: () => void;
}

function CpuTooltipComponent({ cpu, onViewDetails }: CpuTooltipProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-4 w-4 p-0 hover:bg-accent"
          aria-label="View CPU details"
        >
          <Info className="h-4 w-4 text-muted-foreground" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-2">
          <h4 className="font-semibold text-sm">{cpu.name}</h4>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Single-Thread:</span>
              <span className="ml-1">
                {cpu.cpu_mark_single?.toLocaleString() ?? "N/A"}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Multi-Thread:</span>
              <span className="ml-1">
                {cpu.cpu_mark_multi?.toLocaleString() ?? "N/A"}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">iGPU:</span>
              <span className="ml-1">{cpu.igpu_model ?? "No"}</span>
            </div>
            <div>
              <span className="text-muted-foreground">iGPU Mark:</span>
              <span className="ml-1">
                {cpu.igpu_mark?.toLocaleString() ?? "N/A"}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">TDP:</span>
              <span className="ml-1">
                {cpu.tdp_w ? `${cpu.tdp_w}W` : "N/A"}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Year:</span>
              <span className="ml-1">{cpu.release_year ?? "N/A"}</span>
            </div>
          </div>

          <Button
            onClick={onViewDetails}
            variant="outline"
            size="sm"
            className="w-full mt-2"
          >
            View Full CPU Details
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export const CpuTooltip = React.memo(CpuTooltipComponent);
