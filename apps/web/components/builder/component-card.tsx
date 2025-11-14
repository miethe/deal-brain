"use client";

import { Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Represents a selected component with minimal display info
 */
export interface SelectedComponent {
  id: number;
  name: string;
  price?: number;
  specs?: string;
}

export interface ComponentCardProps {
  title: string;
  componentType: string;
  selectedComponent: SelectedComponent | null;
  onSelect: () => void;
  onRemove: () => void;
  required?: boolean;
  disabled?: boolean;
}

/**
 * Card component for displaying and managing individual build components
 */
export function ComponentCard({
  title,
  componentType,
  selectedComponent,
  onSelect,
  onRemove,
  required = false,
  disabled = false,
}: ComponentCardProps) {
  return (
    <Card className="relative">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-lg">
          <span>{title}</span>
          {required && (
            <span className="text-xs font-normal text-red-500">Required</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {selectedComponent ? (
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{selectedComponent.name}</p>
              {selectedComponent.specs && (
                <p className="text-sm text-muted-foreground truncate">
                  {selectedComponent.specs}
                </p>
              )}
              {selectedComponent.price !== undefined && (
                <p className="text-sm text-muted-foreground mt-1">
                  ${selectedComponent.price.toFixed(2)}
                </p>
              )}
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={onSelect}
                disabled={disabled}
              >
                Change
              </Button>
              {!required && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={onRemove}
                  disabled={disabled}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        ) : (
          <Button
            variant="outline"
            className="w-full"
            onClick={onSelect}
            disabled={disabled}
          >
            <Plus className="mr-2 h-4 w-4" />
            Select {title}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
