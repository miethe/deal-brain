# Import Guide

**Location:** `/dashboard/import`

Deal Brain provides a unified import interface with two complementary methods for getting your PC listings and data into the system. Choose the method that best fits your workflow.

---

## Overview

The Import page uses a **tabbed interface** to clearly separate two distinct import workflows:

1. **URL Import Tab** - Import individual listings from online marketplaces
2. **File Import Tab** - Batch import from Excel/CSV workbook files

Both methods are available simultaneously, allowing you to switch between them as needed.

---

## URL Import

### When to Use URL Import

URL import is ideal for:
- Importing individual PC listings from online marketplaces
- Real-time monitoring of specific marketplace listings
- Quick data entry when you find listings online
- Importing from eBay, Amazon, Mercari, and similar retailers

### Supported Sources

- eBay (full browse API support)
- Amazon product pages
- Mercari listings
- Most retailers with product schema (JSON-LD, microdata)

### Single URL Import

**Step 1: Enter the URL**
1. Paste the marketplace URL into the input field
2. The system validates the URL format automatically

**Step 2: Set Priority (Optional)**
1. Choose between **High** or **Normal** priority
2. Affects import queue processing order
3. Default: Normal

**Step 3: Submit**
1. Click **Import URL**
2. The system begins processing the URL asynchronously

**Step 4: Monitor Status**
1. Status updates appear in real-time
2. Watch for **Processing** → **Completed** or **Error**
3. On success, the listing ID appears with a link to the new listing
4. On error, detailed error message explains what went wrong

### Bulk URL Import

**When to Use:**
- Importing multiple URLs at once (up to 1000)
- Batch importing from a saved list
- Quick processing of multiple listings

**How to Access:**
1. In the URL Import tab, scroll to the "Need to import multiple URLs?" section
2. Click **Bulk Import URLs** button
3. This opens the bulk import dialog

**Bulk Import Dialog:**
1. **Choose Input Method:**
   - Upload CSV file with one URL per row
   - Paste up to 1000 URLs (one per line)

2. **CSV Format:**
   ```
   url,priority
   https://www.ebay.com/itm/123456,high
   https://www.amazon.com/dp/ASIN001,normal
   ```

3. **Submit:**
   - Click **Import URLs**
   - System creates a bulk job ID

4. **Track Progress:**
   - See real-time progress (3/100 imported)
   - View results in paginated table
   - Failed URLs marked with error reason
   - Export failed URLs to retry later

### Troubleshooting URL Import

**"Invalid URL"**
- Ensure the URL is a complete marketplace listing URL
- URL should point to a specific product, not a category or search results
- Check for typos

**"Marketplace not supported"**
- The URL's domain isn't recognized
- Verify the marketplace is in our supported list
- Contact support for new marketplace requests

**"Timeout or network error"**
- The marketplace site may be temporarily unavailable
- Wait a moment and retry
- Check your internet connection

**"No data found"**
- The listing may have been removed or is private
- Verify you can access the URL in your browser
- Try a different listing

---

## File Import

### When to Use File Import

File import is ideal for:
- Bulk importing multiple listings at once
- Setting up your catalog from an existing workbook
- Importing PC component catalogs (CPU, GPU specs)
- Importing valuation rules for pricing
- System configuration and bulk data migrations

### Supported File Formats

- **Excel:** `.xlsx`, `.xls` files
- **CSV:** `.csv` files (comma or tab-separated)
- **Max Size:** 10MB per file

### File Structure

Your workbook can contain multiple sheets, each representing different entity types:

1. **Listings Sheet** - Individual PC listings with specs
2. **CPUs Sheet** - CPU catalog with benchmark scores
3. **GPUs Sheet** - GPU specifications
4. **Valuation Rules Sheet** - Pricing adjustment rules
5. **Ports Profiles Sheet** - Connectivity specifications

### Step-by-Step Workflow

**Step 1: Upload File**
1. In the File Import tab, find the upload area
2. Drag and drop a `.xlsx` or `.csv` file, or click to browse
3. System stores the upload and extracts sheet information

**Step 2: Declare Entity Types**
1. For each sheet in your file, select the entity type
2. Options: Listings, CPUs, GPUs, Valuation Rules, Ports Profiles
3. Save declarations - the system will use these to guide mapping

**Step 3: Map Columns**
1. Switch between entity tabs (CPUs, Listings, etc.)
2. Review auto-detected column mappings
3. **Auto** mappings show confidence percentage
4. **Manually** adjust mappings by clicking the field select
5. Required fields are highlighted - ensure they're mapped
6. Click **Save mapping** before switching tabs

**Adding Custom Fields:**
1. If a column doesn't match any existing field
2. Click **Add field** button
3. Define in a popup:
   - Field name (e.g., "Warranty Period")
   - Data type (Text, Number, Date, Dropdown)
   - Validation rules
   - If dropdown: define options
4. New field appears in mapping immediately

**Step 4: Review Data & Resolve Conflicts**
1. **Preview tables** show sample rows from your file
2. For listings: See CPU component matching
   - **Auto** = High confidence match
   - **Needs review** = Lower confidence
   - **Unmatched** = No match found
3. **Adjust CPU matches** via dropdown if needed

**Conflicts Card:**
1. Shows fields that would update existing records
2. Examples: Existing CPU with different specs
3. For each conflict, choose:
   - **Update** - Replace with new data
   - **Skip** - Don't import this row
   - **Keep** - Keep existing, don't update

**Step 5: Commit Import**
1. Verify all conflicts have decisions
2. Verify all mappings are saved
3. Click **Commit import**
4. System processes the batch import

**Step 6: Review Results**
1. Success message shows import counts
   - X listings imported
   - Y CPUs created/updated
   - Z conflicts resolved
2. Auto-created CPUs listed (created to satisfy listing references)
3. Link to view imported listings

### Tips for File Import

**Column Naming:**
- Use clear, descriptive headers
- "CPU Model", "RAM GB", "SSD Storage GB" work well
- Underscores or spaces both work (e.g., "cpu_model" or "CPU Model")

**Data Quality:**
- Keep consistent units (e.g., all GB for storage, not mixed GB/TB)
- Use recognized CPU names when possible (they match against catalog)
- Price values: numbers only, no currency symbols
- Condition: use standard values (New, Like New, Excellent, Good, Fair, Poor)

**Testing:**
- Start with a small test file (5-10 rows) to verify mappings
- Once confident, upload full batch

**Large Files:**
- Files under 5MB: Usually process in seconds
- Larger files may take longer
- Watch the progress indicator

### Troubleshooting File Import

**"File size too large"**
- Max size is 10MB
- Split into multiple files if needed

**"Column mapping required"**
- Ensure all required fields are mapped
- Required fields vary by entity type
- Red highlighting shows unmapped required fields

**"Conflict resolution required"**
- Address all conflicts before committing
- Choose Update, Skip, or Keep for each conflict

**"Data format error"**
- Check date formats are consistent
- Ensure numbers don't have text characters
- Verify enum values match allowed options
- Check first row is headers (not data)

---

## Comparison: When to Use Each Method

| Factor | URL Import | File Import |
|--------|-----------|------------|
| **Single items** | ✓ Best | Possible |
| **Multiple items (5+)** | Okay | ✓ Best |
| **Bulk imports (100+)** | Possible | ✓ Best |
| **New catalogs** | Not applicable | ✓ Best |
| **Configuration** | Not applicable | ✓ Best |
| **Real-time updates** | ✓ Best | N/A |
| **Setup complexity** | Very simple | Moderate |
| **Time per item** | ~10 seconds | <0.1 seconds |

---

## Import History & Audit

**Accessing Previous Imports:**

For file imports, the import session is stored with:
- Upload timestamp
- File name and checksum
- Entity counts (created, updated, skipped)
- Field mappings used
- Conflict resolutions made

For URL imports, each listing shows:
- Source marketplace (eBay, Amazon, etc.)
- Provenance badge with metadata
- Original URL and import date
- Data quality indicators

---

## Advanced Features

### CSV Format Variations

**Comma-separated** (default)
```
CPU Model,RAM GB,Price
Intel Core i7,16,599.99
AMD Ryzen 5,8,399.99
```

**Tab-separated**
```
CPU Model	RAM GB	Price
Intel Core i7	16	599.99
AMD Ryzen 5	8	399.99
```

Both formats are automatically detected and supported.

### Field Mapping Persistence

Custom field definitions created during file import:
- Persist to your global schema
- Available for future imports
- Visible in listing and catalog views
- Can be edited or deleted from Settings > Custom Fields

### Bulk URL CSV Structure

Columns supported:
- `url` - Required, the marketplace URL
- `priority` - Optional, "high" or "normal"
- `tags` - Optional, comma-separated tags

```csv
url,priority,tags
https://ebay.com/itm/123,high,"gaming,compact"
https://amazon.com/dp/ABC,normal,"budget"
```

---

## Performance Notes

### Single URL Import
- **Processing time:** 5-30 seconds per URL
- **Typical:** 10 seconds
- **Depends on:** Marketplace response time, data complexity

### Bulk URL Import
- **50 URLs:** ~5-10 minutes
- **100 URLs:** ~10-20 minutes
- **Processing happens asynchronously** - you can close the page

### File Import
- **Small file (< 5MB, < 500 rows):** 1-5 seconds
- **Larger files:** Up to 30 seconds
- **Processes synchronously** - wait for completion before leaving page

---

## Related Documentation

- **URL Ingestion Context:** `/mnt/containers/deal-brain/docs/project_plans/url-ingest/context/url-ingest-context.md`
- **Importer Workspace Details:** `/mnt/containers/deal-brain/docs/user-guide/guides/importer-usage-guide.md`
- **Import Page Design:** `/mnt/containers/deal-brain/docs/design/import-page-specification.md`
- **CLAUDE.md (For Developers):** `/mnt/containers/deal-brain/CLAUDE.md`

---

## FAQ

**Q: Can I import from multiple marketplaces?**
A: Yes! Both URL and file import support multi-marketplace data. Each listing retains its source marketplace information.

**Q: What happens to duplicate listings?**
A: For URL imports, deduplication checks prevent re-importing the same listing. For file imports, conflict resolution lets you decide how to handle duplicates.

**Q: Can I pause a bulk import?**
A: URL imports process asynchronously - you can close the browser. File imports process synchronously but are fast.

**Q: Are my data and files secure?**
A: Uploaded files are stored securely and processed on your server. Raw payloads are retained for 30 days for debugging, then auto-deleted.

**Q: How do I update existing listings?**
A: Use file import's conflict resolution to update existing CPUs/listings, or re-import via URL (system detects duplicates).

**Q: Can I import formulas or calculations?**
A: File import supports the values. Valuation rules are computed automatically based on your configured rules.

**Q: What if a URL stops working?**
A: Existing listings remain in the system. Re-importing the same listing simply updates its data (conflict resolution applies).

---

## Getting Help

- **Import failing?** Check the error message shown in the UI
- **Column mapping confused?** Hover over field names for descriptions
- **Need custom fields?** Create them inline during import
- **Still stuck?** See troubleshooting sections above for common issues

---

**Last Updated:** 2025-10-21
