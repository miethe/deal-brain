---
title: "Export & Import User Guide"
description: "Step-by-step guide for exporting and importing listings and collections in Deal Brain, including best practices and common workflows."
audience: [users, developers]
tags: [export, import, guide, how-to, listings, collections, workflow]
created: 2025-11-19
updated: 2025-11-19
category: "guide"
status: published
related:
  - /docs/api/export-import-api.md
  - /docs/schemas/export-format-reference.md
  - /docs/guides/export-import-troubleshooting.md
---

# Export & Import User Guide

## Overview

Deal Brain allows you to export listings and collections as portable JSON files that can be imported into other Deal Brain instances. This guide covers how to use these features.

### Common Use Cases

- **Backup Data**: Export your listings and collections for backup
- **Share Data**: Export and share specific deals or curated collections with others
- **Transfer Between Systems**: Move data between different Deal Brain instances
- **Data Analysis**: Export for offline analysis or reporting
- **Bulk Migrate**: Transfer large collections between accounts

---

## Exporting Listings

### Single Listing Export

**To export a single listing:**

1. Browse to your listings or search for a specific deal
2. Click the **Export** button on the listing card or detail page
3. Your listing downloads as `deal-brain-listing-{id}-{date}.json`
4. File is ready to share or import

**What's Included:**
- Listing title, price, seller, condition, and status
- All component specifications (CPU, GPU, RAM, storage, ports)
- Performance metrics and valuation analysis
- Custom fields and additional notes
- Timestamps and metadata

**File Size**: Typical listing export is 5-20 KB

**Example Export:**
```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-19T12:34:56.789Z",
    "type": "deal"
  },
  "data": {
    "listing": {
      "id": 42,
      "title": "Intel Core i7 Gaming PC",
      "price_usd": 799.99,
      ...
    }
  }
}
```

### Tips for Exporting

- **Verify Data Before Exporting**: Check that listing details are complete and accurate
- **Name Your File**: Rename downloaded file to something descriptive like `gaming-pc-deal.json`
- **Create Backups**: Export regularly to back up important deals
- **Share with Context**: When sharing, include a note about why this deal is interesting

---

## Exporting Collections

### Collection Export

**To export a collection:**

1. Go to **Collections** in the sidebar
2. Find your collection and click **Export**
3. Entire collection downloads as `deal-brain-collection-{id}-{date}.json`
4. This includes all items in the collection

**What's Included:**
- Collection name, description, and visibility setting
- All items in the collection with complete listing data
- Position/order of items
- Notes on each item
- All component and performance data

**File Size**: Depends on collection size
- 10 items: 50-150 KB
- 100 items: 500 KB - 1.5 MB
- Large collections may take longer to export

**Tips for Exporting Collections**

- **Well-Organized Collections Export Better**: Name collections clearly, write descriptions
- **Use Descriptions**: Add collection description explaining the deal category
- **Position Items**: Reorder items before exporting so they import in desired order
- **Set Visibility**: Mark collection as public/private before sharing
- **Archive Large Collections**: Consider splitting very large collections (1000+ items) before exporting

---

## Importing Data

### Preview & Duplicate Detection

**To import a listing or collection:**

1. Go to **Import** → **From JSON**
2. Choose whether importing listing or collection
3. Upload JSON file or paste JSON data
4. System shows **Import Preview** with:
   - Parsed data from file
   - Potential duplicates found
   - 30-minute expiration timer

**Duplicate Detection** works by matching on:
- **Exact Title & Seller**: Same title + same seller = high confidence match
- **URL Match**: Same listing URL = confirmed duplicate
- **Fuzzy Matching**: Similar title + similar price = possible match

### Reviewing the Preview

**What You See in Preview:**

```
Preview ID: 550e8400-e29b-41d4-a716-446655440000
Expires at: 2025-11-19T13:04:56.789Z

Found 1 potential duplicate:
- Listing #41: "Gaming PC - Intel i7" ($799.99)
  Match Score: 95%
  Match Reason: Similar title and price
```

**Next Steps:**
- If no duplicates: Proceed with import
- If duplicates found: Choose how to handle them (see merge strategies below)

### Merge Strategies

When importing, you choose what to do if duplicates are found:

#### Create New (Default)

**Use When**: You want separate copies or don't care about duplicates

- Creates new listing/collection regardless of duplicates
- Original data is not affected
- Good for: Comparing versions, keeping history

**Example**:
```
Duplicate found: Gaming PC #41 already exists
Merge strategy: Create New
Result: New listing created as #42 (separate from #41)
```

#### Update Existing (Listing Only)

**Use When**: Replacing old data with new version

- Replaces existing listing with imported data
- Requires selecting which listing to update
- Overwrites all fields with import data
- Good for: Fixing stale data, updating with new info

**Example**:
```
Duplicate found: Gaming PC #41
Merge strategy: Update Existing (target: #41)
Result: Listing #41 updated with new data (old data replaced)
```

#### Merge Items (Collection Only)

**Use When**: Combining collections together

- Adds imported items to existing collection
- Creates new listings for imported items (doesn't update existing)
- Preserves all existing collection items
- Good for: Merging curated lists

**Example**:
```
Collection "Gaming Deals" has 5 items
Import "Gaming Deals" with 3 items
Merge strategy: Merge Items (target: existing collection)
Result: Collection now has 8 items (5 original + 3 imported)
```

#### Skip (Cancel)

**Use When**: You change your mind

- Cancels the import
- No data is changed
- Returns an error message
- Good for: Re-evaluating the import

---

## Step-by-Step Workflow Examples

### Example 1: Backup Your Favorite Deals

**Goal**: Export best deals found this month

**Steps**:
1. Search for your favorite listings
2. For each deal:
   - Click **Export**
   - File downloads
   - Rename to something descriptive: `budget-gaming-pc-nov.json`
3. Store files in backup folder or cloud storage
4. Later: Can import if needed

**Time**: 2 minutes per listing

---

### Example 2: Share a Deal with Friend

**Goal**: Send a specific deal to a friend for feedback

**Steps**:
1. Find the listing you want to share
2. Click **Export** (downloads JSON file)
3. Email or message the JSON file to friend
4. Friend:
   - Goes to their Deal Brain instance
   - Imports the JSON file
   - Reviews duplicate detection (if applicable)
   - Chooses merge strategy (usually "Create New")
   - Confirms import
5. Friend now has listing in their database

**Time**: 3 minutes total

---

### Example 3: Merge Collections from Two Users

**Goal**: Combine "Best Deals" from two friends

**Your Friend Exports:**
1. Goes to Collections → "Best Deals"
2. Clicks Export
3. Sends you file: `best-deals-nov.json`

**You Import:**
1. Go to Import → From JSON
2. Upload friend's file
3. System detects duplicate: Your collection "Best Deals" also exists
4. Review preview (1 potential match)
5. Choose "Merge Items" strategy
6. Select target collection: Your "Best Deals"
7. Confirm import
8. Your collection now has both your items + friend's items

**Result**:
- Your "Best Deals" collection merged with friend's
- Duplicate detection prevented importing the same deals twice
- All unique deals now in one collection

**Time**: 5 minutes

---

### Example 4: Back Up Your Collections

**Goal**: Monthly backup of all collections

**Steps**:
1. Go to Collections page
2. For each collection:
   - Click Export
   - Organize downloads: `collections-backup-november-2025/`
   - Files save as: `deal-brain-collection-{id}-{date}.json`
3. Store folder in backup location (Google Drive, Dropbox, etc.)

**Advantages**:
- Can restore if data is lost
- Can import into new Deal Brain instance
- Can share entire collections with others
- Offline reference copies

**Frequency**: Monthly recommended

**Time**: 5-10 minutes depending on number of collections

---

## Best Practices

### For Exporting

1. **Verify Data Quality**
   - Check that listings have all important data filled in
   - Fix any obvious errors before exporting
   - Complete custom fields where relevant

2. **Use Meaningful Names**
   - Rename files descriptively: `gaming-pcs-budget-deals.json`
   - Include date if versioning: `deals-november-2025.json`
   - Don't use generic names like `export.json`

3. **Document Context**
   - When sharing, include note about deal category
   - Explain why deal is interesting or valuable
   - Provide search criteria used to find deals

4. **Regular Backups**
   - Back up collections monthly
   - Back up favorite deals weekly
   - Keep offline copies in cloud storage

### For Importing

1. **Review Duplicates Carefully**
   - Check duplicate detection results
   - Understand why matches were found
   - Choose appropriate merge strategy

2. **Test First**
   - Import one test file first to understand workflow
   - Practice with small collections before big imports
   - Verify imported data looks correct

3. **Organize After Import**
   - Review imported listings/collections
   - Delete duplicates if needed
   - Reorganize items into appropriate collections

4. **Keep Original Files**
   - Don't delete source files after import
   - Keep numbered versions: `deals-v1.json`, `deals-v2.json`
   - Use version control system for organization

---

## Troubleshooting Quick Links

**See the troubleshooting guide for help with:**

- "Invalid JSON format" errors
- "Schema validation failed" messages
- Expired preview sessions
- File transfer issues
- Large file handling
- Understanding duplicate detection

👉 **[Export/Import Troubleshooting Guide](export-import-troubleshooting.md)**

---

## Technical Details

For developers and advanced users:

**Schema Details**: See [Export Format Reference](../schemas/export-format-reference.md)
- Complete field specifications
- Validation rules
- Optional vs required fields
- Future version migration path

**API Reference**: See [Export/Import API](../api/export-import-api.md)
- Complete endpoint documentation
- Request/response formats
- Error codes and meanings
- Integration examples

**JSON Schema Validation**: See `/docs/schemas/deal-brain-export-schema-v1.0.0.json`
- JSON Schema v7 format
- Can validate exports independently
- Useful for tooling and testing

---

## FAQ

**Q: Can I edit the JSON file before importing?**
A: Yes, you can modify listing prices, titles, or custom fields. Don't modify IDs or timestamps. Invalid JSON will fail import.

**Q: What if my export is very large?**
A: Collections with 1000+ items may take time to export. Consider splitting into multiple collections for better performance.

**Q: Can I import the same export multiple times?**
A: Yes, duplicate detection will alert you. Choose "Create New" to import again, or "Update Existing" to replace data.

**Q: How long are preview sessions valid?**
A: Previews expire after 30 minutes. Re-import to get a new preview if needed.

**Q: Can I delete duplicates automatically?**
A: No, you must review and choose what to do. This prevents accidental data loss.

**Q: Is exported data secure?**
A: Export files are JSON format with no encryption. Don't share exports containing sensitive information.

**Q: Can I import from different Deal Brain versions?**
A: Only v1.0.0 exports are currently supported. Contact support for legacy data migration.

**Q: What about custom fields - are they preserved?**
A: Yes, all custom fields are preserved during export/import.

**Q: Can I schedule automatic exports?**
A: Not yet, but you can export manually. Feature planned for future release.

---

## Related Documentation

- **API Reference**: Complete technical API documentation - [Export/Import API](../api/export-import-api.md)
- **Schema Reference**: Field specifications and validation - [Export Format Reference](../schemas/export-format-reference.md)
- **Troubleshooting**: Common issues and solutions - [Troubleshooting Guide](export-import-troubleshooting.md)
- **Collections Guide**: Managing collections - `/docs/guides/collections-sharing-user-guide.md`
- **Import Guide**: Importing from Excel/URLs - `/docs/guides/import-guide.md`
