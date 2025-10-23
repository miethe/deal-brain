export const ERROR_MESSAGES: Record<string, string> = {
  TIMEOUT: 'Import timed out. The marketplace may be slow to respond.',
  INVALID_SCHEMA: 'Could not extract listing data. The page format may not be supported.',
  ADAPTER_DISABLED: 'This marketplace integration is currently disabled.',
  ITEM_NOT_FOUND: 'Listing not found. The URL may be invalid or the item may have been removed.',
  RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  SUBMIT_ERROR: 'Failed to create import job. Please try again.',
  POLLING_ERROR: 'Failed to check import status. The job may still be running.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
};

export function getErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] || ERROR_MESSAGES.UNKNOWN_ERROR;
}
