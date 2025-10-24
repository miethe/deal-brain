import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import type { ListingDetail } from "@/types/listing-detail";
import { format } from "date-fns";

interface HistoryTabProps {
  listing: ListingDetail;
}

/**
 * History tab component displaying listing timestamps
 *
 * Currently shows:
 * - Created timestamp
 * - Last updated timestamp
 *
 * Future enhancements will include:
 * - Audit log entries table
 * - Field-level change history
 * - User attribution for changes
 * - Filter/search functionality
 *
 * @example
 * ```tsx
 * <HistoryTab listing={listing} />
 * ```
 */
export function HistoryTab({ listing }: HistoryTabProps) {
  const formatDateTime = (date: string | Date) => {
    try {
      return format(new Date(date), "PPP 'at' p");
    } catch (error) {
      return "—";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>History & Updates</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label className="text-xs uppercase tracking-wide text-muted-foreground">
            Created
          </Label>
          <div className="text-sm font-medium mt-1">
            {formatDateTime(listing.created_at)}
          </div>
        </div>

        <div>
          <Label className="text-xs uppercase tracking-wide text-muted-foreground">
            Last Updated
          </Label>
          <div className="text-sm font-medium mt-1">
            {formatDateTime(listing.updated_at)}
          </div>
        </div>

        <div className="mt-6 rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
          <p>Audit log coming soon</p>
          <p className="text-xs mt-1">Track all changes made to this listing</p>
        </div>
      </CardContent>
    </Card>
  );
}
