import { Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PortEntry {
  port_type: string;
  quantity: number;
}

interface PortsBuilderProps {
  value: PortEntry[];
  onChange: (ports: PortEntry[]) => void;
}

const PORT_TYPE_OPTIONS = [
  { value: "USB-A", label: "USB-A" },
  { value: "USB-C", label: "USB-C" },
  { value: "HDMI", label: "HDMI" },
  { value: "DisplayPort", label: "DisplayPort" },
  { value: "Ethernet", label: "Ethernet (RJ45)" },
  { value: "Thunderbolt", label: "Thunderbolt" },
  { value: "Audio", label: "3.5mm Audio" },
  { value: "SD Card", label: "SD Card Reader" },
  { value: "Other", label: "Other" },
];

export function PortsBuilder({ value, onChange }: PortsBuilderProps) {
  const addPort = () => {
    onChange([...value, { port_type: "", quantity: 1 }]);
  };

  const removePort = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const updatePort = (index: number, updates: Partial<PortEntry>) => {
    onChange(
      value.map((port, i) =>
        i === index ? { ...port, ...updates } : port
      )
    );
  };

  return (
    <div className="space-y-2">
      <div className="space-y-2">
        {value.map((port, index) => (
          <div key={index} className="flex gap-2 items-center">
            <select
              value={port.port_type}
              onChange={(e) => updatePort(index, { port_type: e.target.value })}
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Select type...</option>
              {PORT_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <input
              type="number"
              min="1"
              max="16"
              value={port.quantity}
              onChange={(e) =>
                updatePort(index, { quantity: parseInt(e.target.value) || 1 })
              }
              className="w-20 rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => removePort(index)}
              aria-label="Remove port"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={addPort}
      >
        <Plus className="h-4 w-4 mr-2" /> Add Port
      </Button>
    </div>
  );
}
