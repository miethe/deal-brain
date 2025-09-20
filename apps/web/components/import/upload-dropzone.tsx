"use client";

import { useCallback, useRef, useState } from "react";

import { cn } from "../../lib/utils";
import { Button } from "../ui/button";
import { UploadCloud } from "lucide-react";

interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

export function UploadDropzone({ onUpload, isUploading }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const [file] = Array.from(files);
      if (!file) return;
      await onUpload(file);
    },
    [onUpload]
  );

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-12 text-center transition", 
        isDragging ? "border-primary bg-primary/5" : "border-muted"
      )}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={async (event) => {
        event.preventDefault();
        setIsDragging(false);
        await handleFiles(event.dataTransfer?.files ?? null);
      }}
    >
      <UploadCloud className="mb-4 h-10 w-10 text-muted-foreground" />
      <p className="text-lg font-medium">Drag and drop your workbook</p>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        Supports .xlsx, .csv, and .tsv files. We will analyze the sheets, suggest mappings, and highlight anything that needs your attention before committing the import.
      </p>
      <div className="mt-6 flex gap-3">
        <Button
          type="button"
          disabled={isUploading}
          onClick={() => inputRef.current?.click()}
        >
          {isUploading ? "Uploading…" : "Select a file"}
        </Button>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv,.tsv"
        className="hidden"
        onChange={async (event) => {
          await handleFiles(event.target.files);
          event.target.value = "";
        }}
      />
    </div>
  );
}
