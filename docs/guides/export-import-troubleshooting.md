---
title: "Export/Import Troubleshooting Guide"
description: "Common issues with export/import functionality, error messages, solutions, and debugging tips for users and developers."
audience: [users, developers, support]
tags: [troubleshooting, export, import, debugging, faq, errors, solutions]
created: 2025-11-19
updated: 2025-11-19
category: "guide"
status: published
related:
  - /docs/api/export-import-api.md
  - /docs/schemas/export-format-reference.md
  - /docs/guides/export-import-user-guide.md
---

# Export/Import Troubleshooting Guide

## Quick Diagnostics

### Is the export file valid?

```bash
# Validate against JSON Schema
npm install -g ajv-cli

ajv validate \
  -s docs/schemas/deal-brain-export-schema-v1.0.0.json \
  -d listing-export.json
```

**If valid**: File is correct format, issue is likely in import process

**If invalid**: File is corrupted or not a valid v1.0.0 export

---

## Common Export Issues

### "Export failed: Listing not found"

**Status Code**: 404

**Cause**: Listing ID doesn't exist or you don't have permission to access it.

**Solutions**:
1. Verify listing ID is correct
2. Check that you own the listing (or it's public)
3. Ensure listing wasn't deleted
4. In multi-tenant system, verify you're using correct account

**Example**:
```bash
# Wrong ID - check your listing first
curl https://api.dealbrain.io/api/v1/listings/9999/export
# Error: Listing 9999 not found

# Correct ID
curl https://api.dealbrain.io/api/v1/listings/42/export
# Success
```

---

### "Export failed: User does not have access"

**Status Code**: 403

**Cause**: You don't own this listing and it's not marked as public.

**Solutions**:
1. Make sure you're logged in with the right account
2. Check listing visibility settings
3. Ask listing owner for permission
4. For API access, verify authentication token is valid

**Example**:
```bash
# Without auth
curl https://api.dealbrain.io/api/v1/listings/42/export
# Error: 403 Forbidden

# With auth (must be owner or public listing)
curl -H "Authorization: Bearer token" \
  https://api.dealbrain.io/api/v1/listings/42/export
# Success (if you own it)
```

---

### "Export failed: Invalid format parameter"

**Status Code**: 400

**Cause**: Requested an unsupported export format.

**Solutions**:
1. Only `"json"` format is currently supported
2. Remove the format parameter (defaults to JSON)
3. Don't use other formats like `"csv"`, `"xml"`, etc.

**Example**:
```bash
# Wrong - CSV not supported
curl https://api.dealbrain.io/api/v1/listings/42/export?format=csv
# Error: Invalid format

# Correct - JSON is default
curl https://api.dealbrain.io/api/v1/listings/42/export
# Success
```

---

## Common Import Issues

### "Invalid JSON format" Error

**Status Code**: 400

**Cause**: File contains malformed JSON.

**Solutions**:
1. Validate JSON syntax: Use online JSON validator or `jq`
2. Check file encoding is UTF-8
3. Ensure file wasn't corrupted during transfer
4. Try downloading export again and re-importing

**Diagnostics**:
```bash
# Validate JSON syntax
jq empty listing-export.json
# If no error, JSON is valid

# Check file encoding
file listing-export.json
# Should show: UTF-8 Unicode

# If file seems corrupt, try pretty-printing
jq . malformed.json
# Will show exact location of syntax error
```

**Example Error**:
```json
{
  "detail": "Invalid JSON format: Expecting value: line 5 column 2 (char 128)"
}
```

This points to line 5, column 2 - missing comma or quote in that area.

---

### "Schema validation failed" Error

**Status Code**: 422

**Cause**: JSON is valid but doesn't match v1.0.0 schema.

**Common Causes**:

#### Missing Required Field

**Error Message**:
```
Invalid export schema: 1 validation error for PortableDealExport
data -> listing -> title
  ensure this value has at least 1 characters (type=value_error.any_str.min_length)
```

**Solution**: Check that all required fields are present and have valid values.

**Required Fields for Deal Export**:
- `deal_brain_export` object with:
  - `version` (must be "1.0.0")
  - `exported_at` (ISO 8601 datetime)
  - `type` (must be "deal")
- `data` object with:
  - `listing` object with:
    - `id` (integer)
    - `title` (string, 1-255 chars)
    - `price_usd` (number, ≥ 0)
    - `condition` (enum: new, like_new, good, fair, poor)
    - `status` (enum: active, sold, removed, draft)
    - `created_at` (ISO 8601 datetime)
    - `updated_at` (ISO 8601 datetime)

#### Wrong Enum Value

**Error Message**:
```
Invalid export schema: value is not a valid enumeration member (type=type_error.enum)
```

**Solution**: Check enum fields use exact case-sensitive values.

**Valid Values**:
- `condition`: `"new"`, `"like_new"`, `"good"`, `"fair"`, `"poor"`
- `status`: `"active"`, `"sold"`, `"removed"`, `"draft"`
- `type`: `"deal"`, `"collection"`
- `visibility`: `"private"`, `"unlisted"`, `"public"`
- `component_type`: `"psu"`, `"cooler"`, `"case"`, etc.
- `port_type`: `"usb_a"`, `"usb_c"`, `"hdmi"`, `"displayport"`, etc.

**Example**: ❌ `"condition": "Like New"` → ✅ `"condition": "like_new"`

#### Wrong Version

**Error Message**:
```
Invalid export schema: Incompatible schema version: 0.9.0. Only v1.0.0 is currently supported.
```

**Solution**: Export was created with different version.

**What to do**:
1. If you have access to original listing, re-export it (will use v1.0.0)
2. If it's an old export, check if manual migration is possible
3. Contact support if you need to import legacy data

---

### "Preview expired" Error

**Status Code**: 404

**Cause**: Preview has expired (30 minute TTL).

**Solutions**:
1. Re-import the file (creates new preview)
2. Complete import confirmation within 30 minutes
3. Don't wait too long between preview and confirmation

**Timing**:
```bash
# 1. Import at 12:00 PM
curl -X POST ... /api/v1/listings/import
# Response includes: "expires_at": "2025-11-19T12:30:00Z"

# 2. Confirm anytime before 12:30 PM ✓
curl -X POST ... /api/v1/listings/import/confirm
# Works: 12:15 PM

# 3. Confirm after 12:30 PM ✗
curl -X POST ... /api/v1/listings/import/confirm
# Error: Preview not found or expired (404)

# Solution: Re-import to get new preview
curl -X POST ... /api/v1/listings/import
```

---

### "target_listing_id required" Error

**Status Code**: 400

**Cause**: Using `"update_existing"` merge strategy without specifying which listing to update.

**Solutions**:
1. Include `target_listing_id` in confirmation request
2. OR use `"create_new"` merge strategy instead

**Example**:
```bash
# Wrong - missing target_listing_id
curl -X POST \
  -d '{
    "preview_id": "abc123",
    "merge_strategy": "update_existing"
  }' \
  https://api.dealbrain.io/api/v1/listings/import/confirm
# Error: target_listing_id required

# Correct - include target_listing_id
curl -X POST \
  -d '{
    "preview_id": "abc123",
    "merge_strategy": "update_existing",
    "target_listing_id": 41
  }' \
  https://api.dealbrain.io/api/v1/listings/import/confirm
# Success
```

---

### "Preview is not for a listing import" Error

**Status Code**: 400

**Cause**: You're trying to confirm a collection import with a listing endpoint (or vice versa).

**Solutions**:
1. For listing imports: Use `/api/v1/listings/import/confirm`
2. For collection imports: Use `/api/v1/collections/import/confirm`
3. Check preview_id is from the correct import

**Example**:
```bash
# Create collection import preview
curl -X POST -F "file=@collection.json" \
  https://api.dealbrain.io/api/v1/collections/import
# Response: preview_id = "xyz789"

# Try to confirm as listing (WRONG)
curl -X POST \
  -d '{"preview_id": "xyz789", "merge_strategy": "create_new"}' \
  https://api.dealbrain.io/api/v1/listings/import/confirm
# Error: Preview is not for a listing import

# Correct endpoint
curl -X POST \
  -d '{"preview_id": "xyz789", "merge_strategy": "create_new"}' \
  https://api.dealbrain.io/api/v1/collections/import/confirm
# Success
```

---

## Common Duplicate Detection Issues

### "I see a duplicate but want to create anyway"

**Situation**: System detects potential duplicate, but you want to import as separate listing.

**Solution**: Use `"create_new"` merge strategy to create new listing despite duplicates.

```bash
curl -X POST \
  -d '{
    "preview_id": "abc123",
    "merge_strategy": "create_new"
  }' \
  https://api.dealbrain.io/api/v1/listings/import/confirm
```

Duplicates detected are informational - they don't block import.

---

### "Duplicate detection is too strict/loose"

**Duplicate Detection Algorithm**:
- Exact matches (score 1.0): Title + seller match, or URL match
- Fuzzy matches (score 0.7-1.0): Title similarity (70%) + price similarity (30%)
- Only shows duplicates with score > 0.7

**If too many false positives** (false duplicates):
- System is being conservative - intentional to inform users
- Use `"create_new"` to create duplicate if needed
- Consider merging manually to keep data clean

**If missing duplicates**:
- Different titles but same listing - no match (as intended)
- Different sellers or prices - might not meet threshold
- If you spot missing duplicate, report to support

---

### "How does merge strategy work?"

**Strategy**: `"create_new"`
- Always creates new listing/collection
- Ignores duplicate warnings
- Original data not affected
- Best for: Different copies, temporary data

**Strategy**: `"update_existing"`
- For listings: Replaces all fields with import data
- Requires `target_listing_id`
- Original listing replaced completely
- Best for: Updating stale data, correcting info

**Strategy**: `"merge_items"` (collections only)
- Adds imported collection items to existing collection
- Creates new listings for items (doesn't update existing)
- Existing items in collection not removed
- Best for: Combining collections

**Strategy**: `"skip"`
- Cancels import (error response)
- Data not changed
- Best for: Changing your mind

---

## File Transfer Issues

### "File corrupted during upload/download"

**Cause**: Network transfer interrupted or file encoding changed.

**Solutions**:
1. Verify file integrity with checksum:
   ```bash
   # Create checksum
   sha256sum listing.json > listing.json.sha256

   # Verify after transfer
   sha256sum -c listing.json.sha256
   ```

2. Re-download or re-export
3. Try again with stable network
4. Use file transfer tool (scp, rsync) instead of browser

---

### "File size too large"

**Cause**: Exporting collection with 1000+ items creates large file.

**Solutions**:
1. Export collection items in smaller batches
2. Use pagination if available
3. Contact support if legitimate large export

**Performance Tips**:
- Collections with < 100 items: Fast
- Collections with 100-1000 items: 1-10 seconds
- Collections with 1000+ items: > 10 seconds (consider splitting)

---

## Authorization & Authentication Issues

### "401 Unauthorized" Error

**Cause**: Missing or invalid authentication token.

**Solutions**:
1. Ensure you're logged in
2. Include Authorization header with Bearer token
3. Check token hasn't expired
4. Verify token format: `Authorization: Bearer {token}`

**Example**:
```bash
# Wrong - no auth
curl https://api.dealbrain.io/api/v1/listings/42/export
# Error: 401 Unauthorized

# Correct - with auth
curl -H "Authorization: Bearer eyJhbGc..." \
  https://api.dealbrain.io/api/v1/listings/42/export
# Success
```

---

### "403 Forbidden - Access Denied"

**Cause**: You're authenticated but don't have permission.

**Solutions**:
1. Verify you own the listing/collection
2. Check if item is public/shared with you
3. Ask owner for access
4. Try with different account if you have multiple

---

## Advanced Debugging

### Enable Verbose Logging

**JavaScript/Node.js**:
```javascript
// Add debug flag
process.env.DEBUG = 'deal-brain:*';
```

**Python**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Curl**:
```bash
# See request/response details
curl -v https://api.dealbrain.io/api/v1/listings/42/export

# Even more verbose
curl -vvv https://api.dealbrain.io/api/v1/listings/42/export
```

---

### Check Network & API

```bash
# Test API connectivity
curl https://api.dealbrain.io/api/v1/listings/1/export

# Check HTTP status code
curl -w "HTTP Status: %{http_code}\n" \
  https://api.dealbrain.io/api/v1/listings/42/export

# Test with specific headers
curl -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  https://api.dealbrain.io/api/v1/listings/42/export
```

---

### Validate Against Schema

**Using jq**:
```bash
# Check structure
jq '.deal_brain_export' listing.json
jq '.data.listing' listing.json

# Validate against schema
jq -r 'if .deal_brain_export.version == "1.0.0" then "Version OK" else "Version Error" end' listing.json

# Check all required fields exist
jq 'if (.deal_brain_export and .data and .data.listing) then "Structure OK" else "Structure Error" end' listing.json
```

**Using Python**:
```python
import json
from jsonschema import validate, ValidationError

with open('deal-brain-export-schema-v1.0.0.json') as f:
    schema = json.load(f)

with open('listing.json') as f:
    data = json.load(f)

try:
    validate(instance=data, schema=schema)
    print("Valid!")
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Path: {list(e.path)}")
```

---

## Performance Issues

### Export is slow

**Cause**: Large listing with many relationships, or database slow.

**Solutions**:
1. Check network latency: `ping api.dealbrain.io`
2. Try again during off-peak hours
3. Check server status
4. Export simpler listings first

**Expected Times**:
- Single listing: < 1 second
- Collection with 10 items: 1-2 seconds
- Collection with 100 items: 5-10 seconds
- Collection with 1000+ items: > 30 seconds

---

### Import is slow

**Cause**: Large preview generation with many duplicates, or database slow.

**Solutions**:
1. Use smaller files (< 50 items per import)
2. Try again during off-peak hours
3. Check duplicate detection is completing
4. Contact support if consistently slow

**Typical Performance**:
- Create preview: 1-5 seconds
- Confirm import: 2-10 seconds
- Total time: < 15 seconds for typical import

---

## Getting Help

### Gather Information

Before contacting support, collect:
1. Error message (exact text)
2. HTTP status code
3. Request details (endpoint, method)
4. Export/import file (if not sensitive)
5. Steps to reproduce
6. Browser console logs or server logs

**How to get logs**:

Browser:
1. Open Developer Tools (F12)
2. Go to Console tab
3. Reproduce error
4. Screenshot/copy error messages

Terminal:
```bash
# Verbose curl output
curl -vvv ... > debug.log 2>&1

# Python logs
import logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG)
```

### Contact Support

Provide:
- Error message
- HTTP status code
- Request (without sensitive data)
- Response
- Steps to reproduce
- Browser/client version

---

## Related Documentation

- **API Reference**: `/docs/api/export-import-api.md`
- **Schema Reference**: `/docs/schemas/export-format-reference.md`
- **User Guide**: `/docs/guides/export-import-user-guide.md`
