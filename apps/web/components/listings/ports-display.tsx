import { memo } from "react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface PortsDisplayProps {
  ports: Array<{ port_type: string; quantity: number }>;
}

function PortsDisplayComponent({ ports }: PortsDisplayProps) {
  if (!ports || ports.length === 0) {
    return <span className="text-muted-foreground text-sm">—</span>;
  }

  const compactDisplay = ports
    .map((p) => `${p.quantity}× ${p.port_type}`)
    .join("  ");

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="text-left text-sm hover:underline cursor-pointer">
          {compactDisplay}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64">
        <div className="space-y-2">
          <h4 className="font-semibold text-sm">Ports</h4>
          <div className="space-y-1">
            {ports.map((port, i) => (
              <div key={i} className="flex justify-between text-sm">
                <span>{port.port_type}</span>
                <span className="text-muted-foreground">× {port.quantity}</span>
              </div>
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// Memoize to prevent re-renders when ports array hasn't changed
export const PortsDisplay = memo(
  PortsDisplayComponent,
  (prevProps, nextProps) => {
    // Deep equality check for ports array
    if (prevProps.ports.length !== nextProps.ports.length) return false;
    return prevProps.ports.every((prevPort, index) => {
      const nextPort = nextProps.ports[index];
      return (
        prevPort.port_type === nextPort.port_type &&
        prevPort.quantity === nextPort.quantity
      );
    });
  }
);
