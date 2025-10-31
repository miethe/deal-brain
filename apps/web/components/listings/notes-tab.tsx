import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

/**
 * Notes tab placeholder component
 *
 * Future enhancement will include:
 * - Rich text editor (TipTap or Quill)
 * - Auto-save functionality
 * - Attachment support
 * - Sharing/collaboration features
 *
 * @example
 * ```tsx
 * <NotesTab />
 * ```
 */
export function NotesTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Notes & Comments</CardTitle>
        <CardDescription>Add personal notes and observations</CardDescription>
      </CardHeader>
      <CardContent className="py-8 text-center">
        <div className="rounded-md border border-dashed p-8 text-muted-foreground">
          <p className="text-sm">Notes feature coming soon</p>
          <p className="text-xs mt-2">
            Add and manage personal notes for each listing with rich text formatting
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
