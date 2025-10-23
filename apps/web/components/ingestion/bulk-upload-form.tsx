'use client';

import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import type { BulkUploadFormProps, BulkImportMode, ParsedUrls } from './bulk-import-types';

/**
 * Parse pasted URLs text into array
 * One URL per line, supports various formats
 */
function parseUrlsFromText(text: string): ParsedUrls {
  const lines = text.split('\n').map((line) => line.trim()).filter(Boolean);
  const urls: string[] = [];
  const errors: string[] = [];
  const warnings: string[] = [];

  lines.forEach((line, index) => {
    // Skip CSV header if present
    if (line.toLowerCase() === 'url' && index === 0) {
      return;
    }

    // Basic URL validation
    if (line.startsWith('http://') || line.startsWith('https://')) {
      urls.push(line);
    } else {
      errors.push(`Line ${index + 1}: Invalid URL format "${line}"`);
    }
  });

  if (urls.length === 0 && lines.length > 0) {
    errors.push('No valid URLs found. Each line must start with http:// or https://');
  }

  if (urls.length > 1000) {
    errors.push(`Too many URLs: ${urls.length}. Maximum is 1000 per batch.`);
  }

  return { urls, errors, warnings };
}

/**
 * Validate file before upload
 */
function validateFile(file: File): { valid: boolean; error?: string } {
  // Check file size (max 1MB)
  if (file.size > 1024 * 1024) {
    return { valid: false, error: 'File size exceeds 1MB limit' };
  }

  // Check file type
  const validTypes = ['text/csv', 'application/json'];
  const validExtensions = ['.csv', '.json'];
  const hasValidType = validTypes.includes(file.type);
  const hasValidExtension = validExtensions.some((ext) => file.name.endsWith(ext));

  if (!hasValidType && !hasValidExtension) {
    return { valid: false, error: 'Invalid file type. Please upload CSV or JSON file.' };
  }

  return { valid: true };
}

export function BulkUploadForm({ onSubmit, disabled, error }: BulkUploadFormProps) {
  const [mode, setMode] = useState<BulkImportMode>('file');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [urlsText, setUrlsText] = useState('');
  const [parseError, setParseError] = useState<string | null>(null);
  const [urlCount, setUrlCount] = useState<number>(0);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const validation = validateFile(file);

      if (validation.valid) {
        setSelectedFile(file);
        setFileError(null);
      } else {
        setFileError(validation.error || 'Invalid file');
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validation = validateFile(file);

      if (validation.valid) {
        setSelectedFile(file);
        setFileError(null);
      } else {
        setFileError(validation.error || 'Invalid file');
      }
    }
  };

  const handleUrlsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setUrlsText(text);

    // Parse and validate in real-time
    if (text.trim()) {
      const parsed = parseUrlsFromText(text);
      if (parsed.errors.length > 0) {
        setParseError(parsed.errors[0]);
        setUrlCount(0);
      } else {
        setParseError(null);
        setUrlCount(parsed.urls.length);
      }
    } else {
      setParseError(null);
      setUrlCount(0);
    }
  };

  const handleSubmit = () => {
    if (mode === 'file' && selectedFile) {
      const formData = new FormData();
      formData.append('file', selectedFile);
      onSubmit(formData);
    } else if (mode === 'paste' && urlsText) {
      const parsed = parseUrlsFromText(urlsText);
      if (parsed.errors.length === 0 && parsed.urls.length > 0) {
        onSubmit(parsed.urls);
      }
    }
  };

  const isValid = mode === 'file'
    ? selectedFile && !fileError
    : urlsText.trim() && !parseError && urlCount > 0;

  return (
    <div className="space-y-4">
      {/* Mode Toggle */}
      <div className="flex gap-2 p-1 bg-muted rounded-lg">
        <button
          type="button"
          onClick={() => setMode('file')}
          disabled={disabled}
          className={cn(
            'flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors',
            mode === 'file'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          <Upload className="inline-block h-4 w-4 mr-2" />
          Upload File
        </button>
        <button
          type="button"
          onClick={() => setMode('paste')}
          disabled={disabled}
          className={cn(
            'flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors',
            mode === 'paste'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          <FileText className="inline-block h-4 w-4 mr-2" />
          Paste URLs
        </button>
      </div>

      {/* File Upload Mode */}
      {mode === 'file' && (
        <div className="space-y-3">
          <Label htmlFor="file-upload">Upload CSV or JSON file</Label>
          <div
            className={cn(
              'relative border-2 border-dashed rounded-lg p-8 transition-colors',
              dragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-muted-foreground/50',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              id="file-upload"
              type="file"
              accept=".csv,.json"
              onChange={handleFileChange}
              disabled={disabled}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              aria-label="Upload file"
            />
            <div className="text-center space-y-2">
              <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
              <div className="text-sm">
                {selectedFile ? (
                  <p className="font-medium text-foreground">{selectedFile.name}</p>
                ) : (
                  <>
                    <p className="font-medium">
                      Drop file here or <span className="text-primary">browse</span>
                    </p>
                    <p className="text-muted-foreground">CSV or JSON, max 1MB, up to 1000 URLs</p>
                  </>
                )}
              </div>
            </div>
          </div>
          {fileError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{fileError}</AlertDescription>
            </Alert>
          )}
        </div>
      )}

      {/* Paste URLs Mode */}
      {mode === 'paste' && (
        <div className="space-y-3">
          <Label htmlFor="urls-textarea">
            Paste URLs (one per line)
            {urlCount > 0 && (
              <span className="ml-2 text-xs text-muted-foreground">
                ({urlCount} URL{urlCount !== 1 ? 's' : ''})
              </span>
            )}
          </Label>
          <Textarea
            id="urls-textarea"
            placeholder="https://www.ebay.com/itm/123456789&#10;https://www.amazon.com/dp/B08N5WRWNW&#10;https://..."
            value={urlsText}
            onChange={handleUrlsChange}
            disabled={disabled}
            rows={10}
            className={cn('font-mono text-xs', parseError && 'border-destructive')}
            aria-describedby={parseError ? 'urls-error' : 'urls-help'}
          />
          {parseError ? (
            <Alert variant="destructive" id="urls-error">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{parseError}</AlertDescription>
            </Alert>
          ) : (
            <p id="urls-help" className="text-xs text-muted-foreground">
              Enter one URL per line. Maximum 1000 URLs per batch.
            </p>
          )}
        </div>
      )}

      {/* Global Error */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {/* Submit Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSubmit}
          disabled={!isValid || disabled}
          size="lg"
        >
          Import {mode === 'file' ? 'File' : `${urlCount} URL${urlCount !== 1 ? 's' : ''}`}
        </Button>
      </div>
    </div>
  );
}
