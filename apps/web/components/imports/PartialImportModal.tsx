"use client";

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { ListingRecord } from '@/types/listings';
import { API_URL } from '@/lib/utils';

interface PartialImportModalProps {
  listing: ListingRecord;
  onComplete: () => void;
  onSkip: () => void;
}

export function PartialImportModal({
  listing,
  onComplete,
  onSkip,
}: PartialImportModalProps) {
  const [price, setPrice] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    // Validate price
    const priceNum = parseFloat(price);
    if (!price.trim()) {
      setError('Price is required');
      return;
    }
    if (isNaN(priceNum) || priceNum <= 0) {
      setError('Price must be a positive number');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/v1/listings/${listing.id}/complete`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price: priceNum }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save listing');
      }

      onComplete();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save listing. Please try again.';
      setError(message);
      console.error('Error completing import:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading && price.trim()) {
      handleSubmit();
    }
  };

  return (
    <Dialog open={true} onOpenChange={onSkip}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Complete Listing Import</DialogTitle>
          <DialogDescription>
            We extracted most data for this listing, but need your help with one field to complete it
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Extracted Data (Read-Only) */}
          <div className="border-l-4 border-green-500 bg-green-50 p-4 rounded-r-md">
            <h3 className="font-semibold text-sm flex items-center gap-2 text-green-900 mb-3">
              <CheckCircle className="w-4 h-4" />
              Extracted Data (Read-Only)
            </h3>

            <div className="text-sm space-y-2 text-green-800">
              <div className="flex justify-between">
                <span className="font-medium">Title:</span>
                <span>{listing.title}</span>
              </div>

              {listing.cpu?.name && (
                <div className="flex justify-between">
                  <span className="font-medium">CPU:</span>
                  <span>{listing.cpu.name}</span>
                </div>
              )}

              {listing.ram_gb && (
                <div className="flex justify-between">
                  <span className="font-medium">RAM:</span>
                  <span>{listing.ram_gb}GB</span>
                </div>
              )}

              {listing.primary_storage_gb && (
                <div className="flex justify-between">
                  <span className="font-medium">Storage:</span>
                  <span>
                    {listing.primary_storage_gb}GB {listing.primary_storage_type || 'SSD'}
                  </span>
                </div>
              )}

              {listing.condition && (
                <div className="flex justify-between">
                  <span className="font-medium">Condition:</span>
                  <span className="capitalize">{listing.condition}</span>
                </div>
              )}

              {listing.gpu?.name && (
                <div className="flex justify-between">
                  <span className="font-medium">GPU:</span>
                  <span>{listing.gpu.name}</span>
                </div>
              )}
            </div>
          </div>

          {/* Missing Fields (Editable) */}
          <div className="border-l-4 border-yellow-400 bg-yellow-50 p-4 rounded-r-md">
            <h3 className="font-semibold text-sm flex items-center gap-2 text-yellow-900 mb-3">
              <AlertCircle className="w-4 h-4" />
              Complete These Fields
            </h3>

            <div className="space-y-3">
              <div>
                <Label htmlFor="price" className="text-yellow-900 font-medium">
                  Price (USD)
                  <span className="text-red-500 ml-1" aria-label="required">
                    *
                  </span>
                </Label>
                <Input
                  id="price"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="299.99"
                  value={price}
                  onChange={(e) => {
                    setPrice(e.target.value);
                    if (error) setError('');
                  }}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                  className={`mt-1 ${error ? 'border-red-500 focus:border-red-500' : ''}`}
                  autoFocus
                  aria-label="Listing price in USD"
                  aria-required="true"
                  aria-invalid={!!error}
                  aria-describedby={error ? 'price-error' : undefined}
                />
                {error && (
                  <p
                    id="price-error"
                    className="text-xs text-red-600 mt-1"
                    role="alert"
                  >
                    {error}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Info Message */}
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800 text-sm">
              After you complete these fields, we'll calculate the deal rating and metrics for this listing.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter className="flex gap-2">
          <Button
            variant="outline"
            onClick={onSkip}
            disabled={isLoading}
            className="flex-1 sm:flex-initial"
          >
            Skip for Now
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isLoading || !price.trim()}
            className="flex-1 sm:flex-initial"
          >
            {isLoading ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save & Complete'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
