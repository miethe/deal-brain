"use client";

import * as React from "react";
import { Check, Copy, Loader2, Search, Send } from "lucide-react";
import { useDebounce } from "use-debounce";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useShareListing } from "@/hooks/use-share-listing";
import { useShareWithUser } from "@/hooks/use-share-with-user";
import { useUserSearch, type User } from "@/hooks/use-user-search";
import { cn } from "@/lib/utils";

interface ShareModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  listingId: number;
  listingName: string;
}

/**
 * Modal for sharing listings via public link or with specific users
 */
export function ShareModal({
  open,
  onOpenChange,
  listingId,
  listingName,
}: ShareModalProps) {
  const [activeTab, setActiveTab] = React.useState<"link" | "user">("link");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Share Listing</DialogTitle>
          <DialogDescription>
            Share &quot;{listingName}&quot; via public link or send to a specific user.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "link" | "user")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="link">Copy Link</TabsTrigger>
            <TabsTrigger value="user">Share with User</TabsTrigger>
          </TabsList>

          <TabsContent value="link" className="mt-4">
            <CopyLinkTab listingId={listingId} />
          </TabsContent>

          <TabsContent value="user" className="mt-4">
            <ShareWithUserTab
              listingId={listingId}
              onSuccess={() => onOpenChange(false)}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Copy Link Tab - Generate and copy public share link
 */
function CopyLinkTab({ listingId }: { listingId: number }) {
  const [copied, setCopied] = React.useState(false);
  const shareListing = useShareListing();
  const linkInputRef = React.useRef<HTMLInputElement>(null);

  // Generate link on mount
  React.useEffect(() => {
    if (!shareListing.data && !shareListing.isPending) {
      shareListing.mutate({ listing_id: listingId });
    }
    // Only depend on listingId - shareListing.data and isPending are checked in the condition
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  // Auto-focus input when link is generated
  React.useEffect(() => {
    if (shareListing.data && linkInputRef.current) {
      linkInputRef.current.focus();
      linkInputRef.current.select();
    }
  }, [shareListing.data]);

  const handleCopy = async () => {
    if (!shareListing.data?.share_url) return;

    try {
      await navigator.clipboard.writeText(shareListing.data.share_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
    }
  };

  const formatExpiryDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const daysUntilExpiry = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (daysUntilExpiry <= 0) return "Expired";
    if (daysUntilExpiry === 1) return "Expires in 1 day";
    if (daysUntilExpiry <= 30) return `Expires in ${daysUntilExpiry} days`;

    const monthsUntilExpiry = Math.floor(daysUntilExpiry / 30);
    return `Expires in ${monthsUntilExpiry} month${monthsUntilExpiry > 1 ? "s" : ""}`;
  };

  if (shareListing.isPending) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Generating share link...</span>
      </div>
    );
  }

  if (shareListing.isError) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-destructive">Failed to generate share link. Please try again.</p>
        <Button
          onClick={() => shareListing.mutate({ listing_id: listingId })}
          variant="outline"
          className="w-full"
        >
          Retry
        </Button>
      </div>
    );
  }

  if (!shareListing.data) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="share-link">Share Link</Label>
        <div className="flex gap-2">
          <Input
            id="share-link"
            ref={linkInputRef}
            value={shareListing.data.share_url}
            readOnly
            className="font-mono text-xs"
          />
          <Button
            onClick={handleCopy}
            variant="outline"
            size="icon"
            className="shrink-0"
            aria-label="Copy to clipboard"
          >
            {copied ? (
              <Check className="h-4 w-4 text-green-600" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          {formatExpiryDate(shareListing.data.expires_at)}
        </p>
      </div>

      <div className="rounded-md bg-muted p-3">
        <p className="text-xs text-muted-foreground">
          Anyone with this link can view this listing. The link will expire automatically
          after the specified time period.
        </p>
      </div>
    </div>
  );
}

/**
 * Share with User Tab - Send listing to specific user
 */
function ShareWithUserTab({
  listingId,
  onSuccess,
}: {
  listingId: number;
  onSuccess: () => void;
}) {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedUser, setSelectedUser] = React.useState<User | null>(null);
  const [message, setMessage] = React.useState("");
  const [showResults, setShowResults] = React.useState(false);

  const [debouncedQuery] = useDebounce(searchQuery, 200);
  const userSearch = useUserSearch(debouncedQuery, showResults);
  const shareWithUser = useShareWithUser();

  const searchInputRef = React.useRef<HTMLInputElement>(null);
  const messageInputRef = React.useRef<HTMLTextAreaElement>(null);

  // Auto-focus search input on mount
  React.useEffect(() => {
    searchInputRef.current?.focus();
  }, []);

  const handleUserSelect = (user: User) => {
    setSelectedUser(user);
    setSearchQuery(user.username);
    setShowResults(false);
    // Focus message input after selecting user
    setTimeout(() => messageInputRef.current?.focus(), 100);
  };

  const handleSend = async () => {
    if (!selectedUser) return;

    await shareWithUser.mutateAsync({
      recipient_id: selectedUser.id,
      listing_id: listingId,
      message: message.trim() || undefined,
    });

    // Reset form and close modal on success
    setSelectedUser(null);
    setSearchQuery("");
    setMessage("");
    onSuccess();
  };

  const users = userSearch.data?.users || [];
  const isLoading = userSearch.isLoading;
  const canSend = selectedUser && !shareWithUser.isPending;

  return (
    <div className="space-y-4">
      {/* User Search */}
      <div className="space-y-2">
        <Label htmlFor="user-search">Search User</Label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="user-search"
            ref={searchInputRef}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setSelectedUser(null);
              setShowResults(true);
            }}
            onFocus={() => setShowResults(true)}
            placeholder="Search by username or email..."
            className="pl-9"
            autoComplete="off"
          />
        </div>

        {/* Search Results Dropdown */}
        {showResults && searchQuery.trim() && (
          <div className="mt-1 max-h-[200px] overflow-y-auto rounded-md border border-border bg-background shadow-lg">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Searching...</span>
              </div>
            ) : users.length === 0 ? (
              <div className="py-4 text-center text-sm text-muted-foreground">
                No users found
              </div>
            ) : (
              <div className="py-1">
                {users.map((user) => (
                  <button
                    key={user.id}
                    onClick={() => handleUserSelect(user)}
                    className={cn(
                      "flex w-full flex-col gap-1 px-3 py-2 text-left transition-colors",
                      "hover:bg-accent hover:text-accent-foreground",
                      "focus:bg-accent focus:text-accent-foreground focus:outline-none"
                    )}
                  >
                    <span className="text-sm font-medium">{user.username}</span>
                    <span className="text-xs text-muted-foreground">{user.email}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {selectedUser && !showResults && (
          <div className="rounded-md bg-muted px-3 py-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">{selectedUser.username}</p>
                <p className="text-xs text-muted-foreground">{selectedUser.email}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedUser(null);
                  setSearchQuery("");
                  setShowResults(true);
                }}
              >
                Change
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Optional Message */}
      <div className="space-y-2">
        <Label htmlFor="share-message">Message (optional)</Label>
        <Textarea
          id="share-message"
          ref={messageInputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Add a personal message..."
          rows={3}
          className="resize-none"
        />
      </div>

      {/* Send Button */}
      <Button
        onClick={handleSend}
        disabled={!canSend}
        className="w-full"
      >
        {shareWithUser.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Sending...
          </>
        ) : (
          <>
            <Send className="mr-2 h-4 w-4" />
            Send
          </>
        )}
      </Button>

      <div className="rounded-md bg-muted p-3">
        <p className="text-xs text-muted-foreground">
          The user will receive a notification with a link to view this listing.
          You can share up to 10 listings per hour.
        </p>
      </div>
    </div>
  );
}
