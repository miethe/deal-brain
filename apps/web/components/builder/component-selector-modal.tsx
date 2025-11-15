"use client";

import { useState, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

/**
 * Generic component item for selection
 */
export interface ComponentItem {
  id: number;
  name: string;
  price?: number;
  specs?: string;
  manufacturer?: string;
  metadata?: Record<string, unknown>;
}

export interface ComponentSelectorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  componentType: string;
  components: ComponentItem[];
  onSelect: (component: ComponentItem) => void;
  isLoading?: boolean;
}

/**
 * Modal for searching and selecting components from catalog
 */
export function ComponentSelectorModal({
  open,
  onOpenChange,
  title,
  componentType,
  components,
  onSelect,
  isLoading = false,
}: ComponentSelectorModalProps) {
  const [search, setSearch] = useState("");

  // Filter components based on search query
  const filteredComponents = useMemo(() => {
    if (!search.trim()) {
      return components;
    }

    const query = search.toLowerCase();
    return components.filter((component) => {
      const nameMatch = component.name.toLowerCase().includes(query);
      const specsMatch = component.specs?.toLowerCase().includes(query);
      const manufacturerMatch = component.manufacturer?.toLowerCase().includes(query);
      return nameMatch || specsMatch || manufacturerMatch;
    });
  }, [components, search]);

  const handleSelect = (component: ComponentItem) => {
    onSelect(component);
    onOpenChange(false);
    setSearch(""); // Reset search on selection
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 flex-1 flex flex-col min-h-0">
          <Input
            placeholder={`Search ${componentType}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />

          <ScrollArea className="flex-1">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">Loading components...</p>
              </div>
            ) : filteredComponents.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">
                  {search ? "No components found" : "No components available"}
                </p>
              </div>
            ) : (
              <div className="space-y-2 pr-4">
                {filteredComponents.map((component) => (
                  <div
                    key={component.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                    onClick={() => handleSelect(component)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium truncate">{component.name}</p>
                        {component.manufacturer && (
                          <Badge variant="outline" className="flex-shrink-0">
                            {component.manufacturer}
                          </Badge>
                        )}
                      </div>
                      {component.specs && (
                        <p className="text-sm text-muted-foreground truncate">
                          {component.specs}
                        </p>
                      )}
                    </div>
                    {component.price !== undefined && (
                      <p className="font-semibold flex-shrink-0 ml-4">
                        ${component.price.toFixed(2)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          {!isLoading && filteredComponents.length > 0 && (
            <div className="text-sm text-muted-foreground">
              Showing {filteredComponents.length} of {components.length} components
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
