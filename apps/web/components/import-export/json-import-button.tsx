"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, FileJson, Loader2, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_URL } from "@/lib/utils";
import { ImportPreviewModal, ImportPreviewData } from "./import-preview-modal";
import { cn } from "@/lib/utils";

interface JsonImportButtonProps {
  importType: "listing" | "collection";
  onSuccess?: () => void;
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm" | "lg";
  className?: string;
}

/**
 * JSON Import Button with Drag & Drop
 *
 * Features:
 * - File upload via button click (file picker)
 * - Drag and drop support
 * - JSON validation
 * - Preview modal with duplicate detection
 * - Confirm/cancel flow
 */
export function JsonImportButton({
  importType,
  onSuccess,
  variant = "default",
  size = "default",
  className,
}: JsonImportButtonProps) {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [previewData, setPreviewData] = useState<ImportPreviewData | null>(null);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Upload mutation (preview step)
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const endpoint =
        importType === "listing"
          ? `${API_URL}/v1/listings/import`
          : `${API_URL}/v1/collections/import`;

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Upload failed",
        }));
        throw new Error(error.detail || "Upload failed");
      }

      return response.json();
    },
    onSuccess: (data: ImportPreviewData) => {
      setPreviewData(data);
      setPreviewModalOpen(true);
    },
    onError: (error: Error) => {
      toast({
        title: "Upload failed",
        description: error.message,
        variant: "destructive",
      });
      setSelectedFile(null);
    },
  });

  // Confirm mutation (actual import)
  const confirmMutation = useMutation({
    mutationFn: async (confirmData: {
      importData: Record<string, unknown>;
      duplicateAction: "skip" | "merge" | "create_new";
      selectedDuplicateId?: number;
    }) => {
      if (!previewData) throw new Error("No preview data");

      const endpoint =
        importType === "listing"
          ? `${API_URL}/v1/listings/import/confirm`
          : `${API_URL}/v1/collections/import/confirm`;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(confirmData),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Import failed",
        }));
        throw new Error(error.detail || "Import failed");
      }

      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Import successful",
        description: `${importType === "listing" ? "Listing" : "Collection"} imported successfully`,
      });
      setPreviewModalOpen(false);
      setPreviewData(null);
      setSelectedFile(null);
      onSuccess?.();
    },
    onError: (error: Error) => {
      toast({
        title: "Import failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const validateJsonFile = (file: File): boolean => {
    // Check file type
    if (!file.name.endsWith(".json") && file.type !== "application/json") {
      toast({
        title: "Invalid file type",
        description: "Please select a JSON file",
        variant: "destructive",
      });
      return false;
    }

    // Check file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast({
        title: "File too large",
        description: "File size must be less than 10MB",
        variant: "destructive",
      });
      return false;
    }

    return true;
  };

  const handleFileSelect = async (file: File) => {
    if (!validateJsonFile(file)) {
      return;
    }

    setSelectedFile(file);
    uploadMutation.mutate(file);
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <>
      <div className="relative">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,application/json"
          onChange={handleFileInputChange}
          className="hidden"
          aria-label={`Import ${importType} from JSON`}
        />

        {/* Upload button */}
        <Button
          variant={variant}
          size={size}
          onClick={handleButtonClick}
          disabled={uploadMutation.isPending}
          className={className}
        >
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4 mr-2" />
              Import from JSON
            </>
          )}
        </Button>

        {/* Selected file indicator */}
        {selectedFile && uploadMutation.isPending && (
          <div className="absolute top-full mt-2 left-0 right-0">
            <Alert className="bg-background">
              <FileJson className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                <span className="text-sm truncate">{selectedFile.name}</span>
                <Loader2 className="h-4 w-4 animate-spin ml-2" />
              </AlertDescription>
            </Alert>
          </div>
        )}
      </div>

      {/* Import Preview Modal */}
      <ImportPreviewModal
        open={previewModalOpen}
        onOpenChange={setPreviewModalOpen}
        previewData={previewData}
        onConfirm={confirmMutation.mutateAsync}
        isConfirming={confirmMutation.isPending}
      />
    </>
  );
}

/**
 * JSON Import Dropzone Component
 *
 * Full dropzone UI for drag and drop import
 */
interface JsonImportDropzoneProps {
  importType: "listing" | "collection";
  onSuccess?: () => void;
  className?: string;
}

export function JsonImportDropzone({
  importType,
  onSuccess,
  className,
}: JsonImportDropzoneProps) {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [previewData, setPreviewData] = useState<ImportPreviewData | null>(null);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Upload mutation (preview step)
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const endpoint =
        importType === "listing"
          ? `${API_URL}/v1/listings/import`
          : `${API_URL}/v1/collections/import`;

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Upload failed",
        }));
        throw new Error(error.detail || "Upload failed");
      }

      return response.json();
    },
    onSuccess: (data: ImportPreviewData) => {
      setPreviewData(data);
      setPreviewModalOpen(true);
    },
    onError: (error: Error) => {
      toast({
        title: "Upload failed",
        description: error.message,
        variant: "destructive",
      });
      setSelectedFile(null);
    },
  });

  // Confirm mutation (actual import)
  const confirmMutation = useMutation({
    mutationFn: async (confirmData: {
      importData: Record<string, unknown>;
      duplicateAction: "skip" | "merge" | "create_new";
      selectedDuplicateId?: number;
    }) => {
      if (!previewData) throw new Error("No preview data");

      const endpoint =
        importType === "listing"
          ? `${API_URL}/v1/listings/import/confirm`
          : `${API_URL}/v1/collections/import/confirm`;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(confirmData),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Import failed",
        }));
        throw new Error(error.detail || "Import failed");
      }

      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Import successful",
        description: `${importType === "listing" ? "Listing" : "Collection"} imported successfully`,
      });
      setPreviewModalOpen(false);
      setPreviewData(null);
      setSelectedFile(null);
      onSuccess?.();
    },
    onError: (error: Error) => {
      toast({
        title: "Import failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const validateJsonFile = (file: File): boolean => {
    if (!file.name.endsWith(".json") && file.type !== "application/json") {
      toast({
        title: "Invalid file type",
        description: "Please select a JSON file",
        variant: "destructive",
      });
      return false;
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast({
        title: "File too large",
        description: "File size must be less than 10MB",
        variant: "destructive",
      });
      return false;
    }

    return true;
  };

  const handleFileSelect = async (file: File) => {
    if (!validateJsonFile(file)) {
      return;
    }

    setSelectedFile(file);
    uploadMutation.mutate(file);
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  return (
    <>
      <div
        className={cn(
          "relative border-2 border-dashed rounded-lg p-8 transition-colors",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50",
          uploadMutation.isPending && "opacity-50 pointer-events-none",
          className
        )}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,application/json"
          onChange={handleFileInputChange}
          className="hidden"
          aria-label={`Import ${importType} from JSON`}
        />

        <div className="flex flex-col items-center justify-center gap-4 text-center">
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div className="space-y-2">
                <p className="text-sm font-medium">Uploading...</p>
                {selectedFile && (
                  <p className="text-xs text-muted-foreground">{selectedFile.name}</p>
                )}
              </div>
            </>
          ) : (
            <>
              <FileJson className="h-12 w-12 text-muted-foreground" />
              <div className="space-y-2">
                <p className="text-sm font-medium">
                  Drag and drop a JSON file here, or click to browse
                </p>
                <p className="text-xs text-muted-foreground">
                  Accepts .json files up to 10MB
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="h-4 w-4 mr-2" />
                Select File
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Import Preview Modal */}
      <ImportPreviewModal
        open={previewModalOpen}
        onOpenChange={setPreviewModalOpen}
        previewData={previewData}
        onConfirm={confirmMutation.mutateAsync}
        isConfirming={confirmMutation.isPending}
      />
    </>
  );
}
