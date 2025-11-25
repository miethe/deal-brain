---
title: "Entity Management User Guide"
description: "Comprehensive guide for managing catalog entities with edit and delete operations"
audience: [users, administrators]
tags: [entities, crud, catalog, user-guide, global-fields]
created: 2025-11-14
updated: 2025-11-14
category: "user-documentation"
status: published
related:
  - /docs/api/catalog-crud-endpoints.md
---

# Entity Management User Guide

## 1. Introduction

Entity management is a core administrative function in Deal Brain, allowing you to maintain accurate, up-to-date information about the components and specifications used in your price-to-performance analysis.

### What is Entity Management?

Deal Brain organizes PC components and specifications into seven distinct entity types. These entities form the foundation of your catalog data and power the valuation and scoring systems. Entity management enables you to:

- **Create** new entities to expand your catalog coverage
- **Edit** existing entities to fix errors or update information
- **Delete** obsolete or duplicate entities
- **View** detailed information about each entity

### Who Should Use These Features?

Entity management tools are designed for:
- **System Administrators** - Managing catalog data and maintaining data quality
- **Data Managers** - Importing and organizing component specifications
- **Power Users** - Creating custom entities and tailoring the catalog to your needs

Regular users typically interact with entities through listings but do not need to manage them directly.

### Deal Brain Entity Types

Deal Brain manages seven core entity types across your catalog:

| Entity Type | Purpose | Examples |
|------------|---------|----------|
| **CPU** | Processor specifications and benchmarks | Intel Core i7-13700K, AMD Ryzen 9 5900X |
| **GPU** | Graphics processing unit data | NVIDIA RTX 4080, AMD RX 7900 XTX |
| **RAM Spec** | Memory configuration profiles | DDR4 32GB 3200MHz, DDR5 16GB 6000MHz |
| **Storage Profile** | Storage device specifications | NVMe 1TB, SSD 512GB, HDD 2TB |
| **Ports Profile** | Connectivity configuration | USB 3.0, HDMI 2.1, DisplayPort 1.4 |
| **Scoring Profile** | Valuation weighting rules | Gaming, Productivity, Value |
| **Listing** | Individual PC entries | Used listings with component associations |

---

## 2. Accessing Entity Management

Deal Brain provides two primary methods for managing entities:

### Option A: Entity Detail Pages

**Direct entity management** - Access individual entities through their detail pages.

**How to access:**
1. Navigate to the **Catalog** section in the main menu
2. Select the entity type (CPU, GPU, RAM Spec, etc.)
3. Browse or search for the specific entity
4. Click on the entity name or "View Details" button
5. The entity detail page loads with all information and action buttons

**What you see on detail pages:**
- Complete entity information displayed in read-only format
- **Edit** button in the top-right header
- **Delete** button next to Edit
- "Used in X listings" badge (if applicable)
- Related information and associations
- Timestamps (created, last updated)

**Best for:**
- Focused edits to a single entity
- Reviewing all details about one entity
- Understanding entity relationships
- Performing deletion operations

### Option B: Global Fields Workspace

**Bulk entity management** - View and manage all entities of a specific type in one place.

**How to access:**
1. Navigate to **Global Fields** from the main menu
2. Select an entity type from the left sidebar
3. A data grid appears showing all entities of that type
4. Use search and filter controls to find specific entities
5. Click "View Details" for full entity details or edit inline

**What you see in Global Fields:**
- Data grid with all entities of selected type
- Column headers with sort controls
- Search bar for quick filtering
- Pagination for large datasets
- "Add Entry" button to create new entities
- "View Details" button on each row
- Quick edit options (in supported entity types)

**Best for:**
- Browsing all entities of a type
- Creating new entities
- Finding duplicates or similar entries
- Bulk operations and searches

---

## 3. Editing Entities

Editing allows you to update entity information, correct errors, and add or modify specifications.

### Step-by-Step Editing Guide

**From Detail Page:**

1. **Navigate** to the entity detail page (see "Accessing Entity Management" above)
2. **Click** the **Edit** button in the top-right corner
3. **Edit modal opens** with all current data pre-filled in form fields
4. **Modify** the fields you need to update:
   - Required fields (marked with `*`) cannot be left empty
   - Update text fields by clicking and typing
   - Select dropdown values for categorical fields
   - Add or remove custom attributes as needed
5. **Review** your changes before saving
6. **Click** "Save Changes" button at the bottom of the modal
7. **Success notification** appears confirming the update
8. **Modal closes** and detail view refreshes with new data

**From Global Fields:**

1. Navigate to Global Fields and select your entity type
2. Locate the entity in the data grid
3. Click the **Edit** icon on that row, or click "View Details" then use the Edit button
4. Follow steps 3-8 above

### Common Editing Scenarios

#### Scenario 1: Fix a Typo in Entity Name

1. Open entity detail page for "Intl Core i7-13700K" (typo: "Intl" instead of "Intel")
2. Click Edit
3. Find the "Name" field: "Intl Core i7-13700K"
4. Correct to: "Intel Core i7-13700K"
5. Click "Save Changes"
6. Confirmation: "Entity updated successfully"

#### Scenario 2: Update CPU Specifications

1. Open CPU detail page for an older processor
2. Click Edit
3. Update fields:
   - **Cores**: 8 → 10
   - **Threads**: 16 → 20
   - **TDP**: 65W → 125W
4. Add benchmark scores if available:
   - **CPU Mark**: 45000 (multi-threaded)
   - **Single Thread**: 4500
5. Click "Save Changes"

#### Scenario 3: Add Custom Attributes

1. Open any entity detail page
2. Click Edit
3. Scroll to **Attributes** section (if entity type supports it)
4. Click "Add Attribute"
5. Enter key-value pair:
   - **Key**: "Architecture"
   - **Value**: "Zen 4"
6. Optionally add more attributes
7. Click "Save Changes"

#### Scenario 4: Modify Ports Profile

1. Open Ports Profile detail page
2. Click Edit
3. Update **Name** and **Description**
4. Modify nested **Ports**:
   - Click "Add Port" to add connectivity
   - Select port type (USB-A, USB-C, HDMI, DisplayPort, etc.)
   - Enter port count and optional notes
5. Click "Save Changes"

### Validation and Error Handling

When editing, the system enforces validation rules to ensure data quality:

**Required Fields**
- Fields marked with `*` cannot be empty
- Error message: "Name field is required"
- Action: Fill in the required field before saving

**Numeric Ranges**
- Some numeric fields have minimum/maximum limits
- Example: CPU cores must be 1-128
- Error message: "Cores must be between 1 and 128"
- Action: Adjust value to valid range

**Duplicate Names**
- Most entity types do not allow duplicate names
- Error message: "A CPU with name 'Intel Core i7-13700K' already exists"
- Action: Choose a unique name or edit the existing entity instead

**Type-Specific Validation**
- RAM Speed must be numeric (e.g., 3200, not "3200MHz")
- Storage capacity must use valid format
- Error message explains what format is expected
- Action: Follow the format specified in error message

**Example Error Scenario:**

```
You attempt to edit a CPU:
- Name: "Intel Core i7-13700K"
- Cores: "sixteen" (should be numeric)
- Submit

Error message: "Cores field must be a number between 1 and 128"

Fix: Change "sixteen" to "16" and submit again
```

---

## 4. Deleting Entities

Deletion removes entities from your catalog. This action is **permanent and cannot be undone**, so use caution.

### When to Delete Entities

Delete entities when they are:
- **Duplicates** - Multiple entries for the same component (e.g., two entries for "Intel Core i7-13700K")
- **Obsolete** - Outdated specifications no longer relevant (e.g., very old CPU models from 2005)
- **Incorrect** - Erroneous entries that should never have been created
- **Unused** - Entities not associated with any listings

**Do NOT delete:**
- Entities used in active listings (system prevents this)
- Entities you're unsure about
- Default profiles that may be system-critical

### Step-by-Step Deletion Guide

1. **Navigate** to the entity detail page
2. **Check** the "Used in X listings" badge:
   - If badge shows "0 listings" or is absent: Entity is safe to delete
   - If badge shows "5 listings" or more: Entity is in use (see safety warning below)
3. **Click** the **Delete** button in the top-right corner
4. **Confirmation dialog** appears with entity information

**If entity is NOT in use:**
```
Dialog title: "Delete Entity?"
Message: "Are you sure? This action cannot be undone."
Options: [Cancel] [Delete]
```
- Review the entity name and details one final time
- Click **Delete** to confirm permanent deletion
- You are redirected to the entity list page
- Confirmation message: "Entity deleted successfully"

**If entity IS in use:**
```
Dialog title: "Cannot Delete Entity"
Message: "This entity is used in 15 listings.
To delete it, you must first reassign or remove those listings."
Name confirmation: [text field: "Type entity name to confirm"]
Options: [Cancel] [Delete]
```
- You must **type the exact entity name** in the confirmation field
- This prevents accidental deletion of in-use entities
- After typing the name correctly, the **Delete** button becomes active
- Click **Delete** to confirm
- You are redirected to the entity list page

### Safety Features Explained

#### "Used in X Listings" Badge

This badge appears on entity detail pages when the entity is associated with listings.

**What it means:**
- **"0 listings"** - Entity is not used anywhere; safe to delete
- **"5 listings"** - Entity appears in 5 listings; cannot delete without confirmation
- **"125 listings"** - Entity appears in 125 listings; high impact deletion (use extreme caution)

**Why it matters:**
- Deleting an in-use entity would break listings that reference it
- The system prevents unintended data loss
- You can see the impact before attempting deletion

#### Name Confirmation Requirement

When deleting an in-use entity, the system requires you to type the entity name.

**Why this exists:**
- Prevents accidental deletion of high-impact entities
- Confirms you understand what you're deleting
- Acts as a second confirmation barrier

**Example:**
```
Entity: "Intel Core i7-13700K" (used in 42 listings)

Confirmation prompt: "Type entity name to confirm deletion"
User types: "Intel Core i7-13700K"
Delete button becomes active → Click to confirm deletion
```

### Deletion Error Messages

#### Error: Cannot Delete (Entity in Use)

```
❌ Error: Cannot delete entity
   This entity is used in 15 listings.
   To delete it, reassign or remove those listings first.
```

**What this means:**
- The entity is referenced by 15 active listings
- Deleting it would leave those listings incomplete

**How to resolve:**
1. **Option A: Keep the entity** - Most common choice
2. **Option B: Edit the entity** - Update incorrect data instead of deleting
3. **Option C: Reassign listings** - Change those 15 listings to reference different entities
4. **Option D: Delete the listings** - Remove obsolete listings first, then delete entity

#### Error: Validation Failed

```
❌ Error: Cannot complete deletion
   Please refresh the page and try again.
```

**What this means:**
- System encountered an issue during deletion process
- Likely due to network connection or session timeout

**How to resolve:**
- Refresh the page (F5 or Cmd+R)
- Navigate back to the entity detail page
- Attempt deletion again
- If error persists, contact your system administrator

### Delete Confirmation Checklist

Before deleting an entity, use this checklist:

- [ ] Is this a duplicate or truly unwanted entity?
- [ ] Have I checked the "Used in" badge?
- [ ] Am I certain about this deletion?
- [ ] Have I made any recent backups?
- [ ] Have I notified relevant team members (if applicable)?

**If you answer "no" to any question, do NOT delete the entity.**

---

## 5. Managing Entities from Global Fields

The Global Fields workspace provides a centralized hub for bulk entity management across all seven entity types.

### Benefits of Global Fields

- **Unified view** - See all entities of one type in a single data grid
- **Efficient search** - Find specific entities quickly with search and filter
- **Bulk browsing** - Review multiple entities side-by-side
- **Quick creation** - Create new entities without leaving the view
- **Easy navigation** - Jump to detail pages for deep dives
- **Pagination support** - Handle large datasets (100s or 1000s of entities)

### Step-by-Step: Using Global Fields

#### Step 1: Navigate to Global Fields

1. Click **Global Fields** in the main navigation menu
2. Global Fields page loads with a sidebar on the left

#### Step 2: Select Entity Type

1. Look at the **left sidebar** showing all 7 entity types:
   - CPU
   - GPU
   - RAM Spec
   - Storage Profile
   - Ports Profile
   - Scoring Profile
   - Listing
2. **Click** the entity type you want to manage
3. A data grid appears showing all entities of that type

#### Step 3: View Entities

The data grid displays:

| Column | Information |
|--------|-------------|
| Name | Entity name or identifier |
| Type/Category | Entity classification |
| Status | Active, deprecated, or other status |
| Used In | Number of listings using this entity |
| Actions | View Details, Edit, Delete buttons |

#### Step 4: Find Specific Entities

**Using Search:**
1. Look for the **search bar** above the data grid
2. Type your search term: "Intel Core i7"
3. Grid filters to show matching entities
4. Results update in real-time as you type

**Using Filter:**
1. Click the **Filter** button (funnel icon) above the grid
2. Select filter criteria:
   - By manufacturer: "Intel", "AMD", etc.
   - By type: "High-end", "Budget", etc.
   - By status: "Active", "Deprecated"
3. Grid updates to show filtered results
4. Click **Clear Filters** to reset

**Using Sort:**
1. Click **column headers** to sort by that column
2. First click: Sort ascending (A-Z or low-high)
3. Second click: Sort descending (Z-A or high-low)
4. Arrow indicator shows current sort order

#### Step 5: View Entity Details

1. Locate the entity in the data grid
2. Click **View Details** button on that row
3. Full entity detail page opens in a new tab
4. Review complete information including:
   - All specifications and attributes
   - Usage count ("Used in X listings")
   - Edit/Delete buttons
   - Related entities
5. Make changes if needed using the Edit button
6. Return to Global Fields tab to manage other entities

#### Step 6: Create New Entities

1. In Global Fields for your selected entity type
2. Click **Add Entry** button (top-right of grid)
3. Create modal opens with empty form fields
4. Fill in required fields (marked with `*`):
   - Name
   - Type/Category
   - Specifications (CPU cores, GPU memory, etc.)
5. Add optional information:
   - Description
   - Attributes
   - Notes
6. Click **Create Entity** button
7. New entity appears in the data grid
8. Success notification: "Entity created successfully"

#### Step 7: Edit from Global Fields

1. Locate the entity in the data grid
2. Click **Edit** button on that row (if available)
3. Edit modal opens with current data pre-filled
4. Modify fields as needed
5. Click **Save Changes**
6. Entity in grid updates immediately

#### Step 8: Handle Pagination

For entity types with large datasets:

1. **Page indicator** shows current page: "Page 1 of 12"
2. **Entries per page** selector: "Show 25 entries" or "Show 50 entries"
3. **Navigation arrows** at bottom: "< Previous | Next >"
4. Click arrows to move between pages
5. Or change entries-per-page to see more/fewer items at once

### Global Fields Best Practices

- **Search first** - Before creating a new entity, search to ensure it doesn't already exist
- **Review columns** - Check the "Used In" column to understand entity relationships
- **Use filters** - Narrow down to relevant entities for your task
- **Make bulk changes** - When possible, manage multiple entities in one Global Fields session
- **Verify before deleting** - Check usage count and "View Details" before deletion

---

## 6. Entity-Specific Guidance

### CPU Management

**Purpose:** Store processor specifications including cores, threads, benchmarks, and performance metrics.

**Key Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| Name | Processor model name | Intel Core i7-13700K |
| Manufacturer | CPU brand | Intel, AMD |
| Socket | CPU socket type | LGA1700, AM5 |
| Cores | Number of cores | 16 |
| Threads | Number of threads | 24 |
| TDP | Thermal Design Power | 125W |
| Base Clock | Base frequency | 3.4 GHz |
| Boost Clock | Max frequency | 5.4 GHz |

**Benchmark Scores:**

| Metric | Purpose | Source |
|--------|---------|--------|
| CPU Mark (Multi) | Multi-threaded performance score | PassMark benchmark |
| CPU Mark (Single) | Single-threaded performance score | PassMark benchmark |
| iGPU Mark | Integrated GPU performance (if available) | PassMark benchmark |

**Common Attributes:**
- Architecture (Zen 4, Raptor Lake, etc.)
- Process node (7nm, 5nm, etc.)
- Release date
- Market segment (Entry-level, High-end, etc.)

**Editing Tips:**
- Update benchmark scores when new data becomes available
- Keep names consistent with manufacturer's official naming
- Add architecture information for easier categorization
- Include TDP for power consumption analysis

**Deletion Considerations:**
- CPUs are frequently used in listings
- Check "Used in X listings" before deletion
- Consider editing duplicates instead of deleting

### GPU Management

**Purpose:** Maintain discrete and integrated GPU data including performance metrics.

**Key Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| Name | GPU model name | NVIDIA RTX 4080 |
| Manufacturer | GPU brand | NVIDIA, AMD, Intel |
| VRAM | Video memory capacity | 12GB |
| Memory Type | GDDR6, GDDR6X, HBM, etc. | GDDR6X |
| Memory Bus | Memory interface width | 192-bit |
| Base Clock | Base GPU frequency | 2.4 GHz |
| Boost Clock | Max frequency | 2.7 GHz |
| TDP | Power consumption | 320W |

**Benchmark Scores:**

| Metric | Purpose |
|--------|---------|
| GPU Mark | Overall GPU performance score |
| 3D Graphics Mark | 3D rendering performance |
| Metal Score | Metal API performance (macOS) |

**Common Attributes:**
- Architecture (Ada, RDNA 3, etc.)
- Ray tracing support (Yes/No)
- Tensor cores/Stream processors count
- Release date

**Editing Tips:**
- Include VRAM amount (critical for performance analysis)
- Update GPU Mark scores for newer drivers/benchmarks
- Add ray tracing support info for gaming profile assessment
- Specify memory type for technical accuracy

**Deletion Considerations:**
- Discrete GPUs are less commonly used than CPUs
- Integrated GPUs may be referenced in CPU configurations
- Verify usage count before deletion

### RAM Spec Management

**Purpose:** Define memory configurations including DDR generation, speed, capacity, and module count.

**Key Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| Name | Memory specification identifier | DDR4 32GB 3200MHz |
| DDR Generation | Memory standard | DDR4, DDR5, DDR3 |
| Speed | Memory frequency | 3200 MHz |
| Capacity | Total memory size | 32GB |
| Module Count | Number of RAM modules | 2 (2x16GB) |
| Timings | Memory timings | 16-20-20-40 |
| Voltage | Operating voltage | 1.35V |

**Important Constraints:**
- **Unique constraint**: Cannot create duplicate RAM specs
- System prevents: "A RAM spec with DDR4 32GB 3200MHz already exists"

**Common Attributes:**
- Rank (1R, 2R, etc.)
- Error-correcting code (ECC support)
- Form factor (DIMM type)
- Brand/model recommendations

**Editing Tips:**
- Name format should be clear: "DDR4 32GB 3200MHz" not "mem32"
- Always include DDR generation and speed (essential for compatibility)
- Verify capacity before saving
- Note the unique constraint - duplicate specs are not allowed

**Deletion Considerations:**
- RAM specs are fundamental to listing configurations
- Often used in multiple listings
- Check usage before deletion; consider editing instead
- Cannot delete if referenced by active listings

### Storage Profile Management

**Purpose:** Define storage device specifications including medium type, capacity, form factor, and performance tier.

**Key Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| Name | Storage identifier | NVMe 1TB PCIe 4.0 |
| Medium | Storage type | NVMe, SSD, HDD |
| Interface | Connection type | PCIe 4.0, PCIe 3.0, SATA |
| Form Factor | Physical size | M.2, 2.5", 3.5" |
| Capacity | Storage size | 1TB |
| RPM | Rotation speed (HDD only) | 7200, 5400 |
| Performance Tier | Speed classification | Budget, Mainstream, Performance, Enthusiast |

**Performance Tiers:**

| Tier | Type | Speed Class | Example |
|------|------|-------------|---------|
| Budget | HDD or slow SSD | SATA SSD | 2.5" SATA SSD 500GB |
| Mainstream | Standard performance | NVMe Gen 3 | M.2 NVMe PCIe 3.0 1TB |
| Performance | High performance | NVMe Gen 4 | M.2 NVMe PCIe 4.0 1TB |
| Enthusiast | Maximum performance | NVMe Gen 5 | M.2 NVMe PCIe 5.0 4TB |

**Common Attributes:**
- Cache capacity (for HDDs)
- MTBF (Mean Time Between Failures)
- Sequential read/write speeds
- Warranty period

**Editing Tips:**
- Clearly specify medium type (NVMe vs SSD vs HDD)
- Include interface for compatibility information
- Assign appropriate performance tier based on specs
- HDD profiles should include RPM

**Deletion Considerations:**
- Storage profiles are essential to every listing
- Very high usage across listings
- Avoid deletion; consider editing or renaming instead
- Almost certainly will hit "Cannot delete: in use" error

### Ports Profile Management

**Purpose:** Define connectivity configurations including port types, counts, and availability.

**Key Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| Name | Profile name | High Connectivity |
| Description | Profile description | USB 3.1 + HDMI 2.1 |

**Nested Ports (Sub-fields):**

| Sub-field | Description | Example |
|-----------|-------------|---------|
| Port Type | Connectivity standard | USB-A, USB-C, HDMI, DisplayPort |
| Count | Number of ports | 4 (for 4x USB-A) |
| Version | Port standard version | 3.0, 3.1, 2.0, 2.1 |
| Notes | Optional notes | Thunderbolt 3 capable |

**Common Port Types:**
- **USB-A 2.0** - Standard USB, lower speed
- **USB-A 3.0** - Fast USB, common on PCs
- **USB-A 3.1** - Very fast USB
- **USB-C 2.0** - Newer connector, standard speed
- **USB-C 3.1** - Fast USB with modern connector
- **USB-C Thunderbolt 3** - Premium high-speed
- **HDMI 2.0** - Standard display output
- **HDMI 2.1** - High-speed display output
- **DisplayPort 1.4** - Professional display standard
- **Audio Jack** - Analog audio connector
- **SD Card Reader** - Memory card slot

**Editing Tips:**
- Create descriptive profile names: "High Connectivity" vs "Minimal"
- Specify port versions (e.g., USB 3.0 vs 3.1) for accuracy
- Add multiple port entries for each type:
  - "USB-A 3.0" with count "4"
  - "USB-C 3.1" with count "2"
  - "HDMI 2.1" with count "2"
- Use Notes field for special capabilities (Thunderbolt, eGPU capable, etc.)

**Deletion Considerations:**
- Ports profiles are referenced by listings
- Check usage count; may be in 50+ listings
- Consider editing existing profiles instead of creating new ones
- Consolidate similar profiles to reduce duplication

### Scoring Profile Management

**Purpose:** Define valuation weights and metrics used to score and rank listings.

**Key Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| Name | Profile name | Gaming Profile |
| Description | Profile purpose | Optimized for gaming performance |
| Default | Whether this is the default | Yes/No |
| Weights | Metric weights | CPU: 0.3, GPU: 0.4, RAM: 0.2 |

**Common Profiles:**

| Profile | Focus | Typical Weights |
|---------|-------|-----------------|
| Gaming | Gaming performance | GPU: 40%, CPU: 30%, RAM: 30% |
| Productivity | Workload performance | CPU: 50%, RAM: 30%, Storage: 20% |
| Value | Price-to-performance | Value Score: 100% |
| Balanced | General purpose | CPU: 30%, GPU: 30%, RAM: 25%, Storage: 15% |

**Default Profile Requirement:**
- **At least one** scoring profile must be marked as "Default"
- The default profile is used for listings when no specific profile is selected
- Cannot delete the only default profile
- Error message: "Cannot delete: this is the only default profile"

**Common Attributes:**
- Target market (gaming, business, etc.)
- Benchmark data sources
- Component weighting rationale
- Applicable listing types

**Editing Tips:**
- Create descriptive names: "Gaming Profile" vs "profile1"
- Include clear description of profile purpose
- Ensure weights sum to 100% (or appropriate total)
- Mark one profile as default for system stability
- Document weighting rationale in notes

**Deletion Considerations:**
- Cannot delete the only default profile
- If you have multiple profiles, you can delete non-default ones
- If you need to delete the default profile:
  1. Create or mark another profile as default first
  2. Then delete the old default profile
- Verify no listings explicitly reference the profile

---

## 7. Best Practices

### Data Quality Standards

#### Naming Conventions
- **Be descriptive** - Entity names should clearly identify the component
  - ✅ Good: "Intel Core i7-13700K"
  - ❌ Bad: "i7 cool cpu"
- **Match official names** - Use manufacturer's official product names when possible
  - ✅ Good: "AMD Ryzen 9 7950X3D"
  - ❌ Bad: "AMD super processor"
- **Avoid special characters** - Stick to alphanumeric and standard punctuation
  - ✅ Good: "NVIDIA RTX 4080 Super"
  - ❌ Bad: "NVIDIA RTX 4080 $uper!!!"
- **Consistent formatting** - Use consistent capitalization and spacing
  - ✅ Good: "DDR4 32GB 3200MHz" (consistent across entries)
  - ❌ Bad: Mix of "DDR4 32gb 3200mhz", "ddr4 32GB 3200MHz"

#### Field Completeness
- **Fill required fields** - All fields marked with `*` must have values
- **Add specifications** - Include relevant specs for your use case:
  - For CPUs: cores, threads, TDP, benchmark scores
  - For GPUs: VRAM, memory type, TDP, benchmark scores
  - For RAM: DDR generation, speed, capacity, timings
- **Use descriptions** - Add descriptions for complex or custom entities
- **Organize attributes** - If using custom attributes, keep them organized and consistent

#### Documentation and Notes
- **Add context** - Use notes/description fields to explain unusual values
  - Example: "Integrated GPU only, no discrete graphics"
- **Link related entities** - Add cross-references in notes when applicable
  - Example: "Pairs well with LGA1700 socket CPUs"
- **Document assumptions** - Explain any estimates or incomplete data
  - Example: "Benchmark scores interpolated from similar models"

### Before Deleting Entities

#### Pre-Deletion Checklist

1. **Verify it's a duplicate**
   - [ ] Search for similar entities in Global Fields
   - [ ] Compare specifications side-by-side
   - [ ] Confirm both entities describe the same component
   - [ ] If unsure, edit one instead of deleting

2. **Check usage count**
   - [ ] View entity detail page
   - [ ] Note the "Used in X listings" badge
   - [ ] If count > 0, see "When Entity is In Use" section below

3. **Verify correctness**
   - [ ] Is this entity truly unwanted?
   - [ ] Could editing be a better solution?
   - [ ] Have I checked for recent changes or updates?

4. **Notify stakeholders** (if applicable)
   - [ ] Inform team members before deleting widely-used entities
   - [ ] Check with any dependents of this data
   - [ ] Document the reason for deletion

#### When Entity is In Use

If the "Used in X listings" badge shows any count > 0:

**Option 1: Keep the Entity** (Recommended)
- Safest choice - maintains data integrity
- Entity continues to work with existing listings
- Consider editing if data is incorrect instead

**Option 2: Edit the Entity**
- Correct errors in the entity definition
- Rename if necessary (still maintains relationships)
- Better than deletion for active entities

**Option 3: Reassign Listings**
- For each listing using this entity
  1. Open the listing
  2. Change the component reference to a different entity
  3. Save the listing
- Once no listings reference this entity, deletion becomes possible
- Time-consuming but necessary for deleting heavily-used entities

**Option 4: Delete the Listings**
- Remove the dependent listings entirely
- Use only if listings are truly obsolete
- Permanent action - use extreme caution
- Verify no one else needs these listings

**Example Scenario:**

```
You want to delete "Intel Core i5-11400" (used in 23 listings)

Option A (Recommended):
- Keep the entity
- It continues to work with those 23 listings
- Deletion is unnecessary

Option B:
- Edit the entity name to be more specific
- Merge with a similar entity by editing

Option C:
- Go to each of the 23 listings
- Change CPU reference to "Intel Core i5-12400"
- Save each listing
- Then delete the old entity

Option D:
- Delete all 23 listings
- Then delete the entity
- Only if listings are truly obsolete
```

### Performance Optimization

#### Managing Large Datasets

- **Use pagination** - When working with 100+ entities, use the page navigation
- **Search strategically** - Don't browse all pages; use search to find specific entities
- **Filter before sorting** - Filter to a subset first, then sort
- **Create new entities carefully** - Verify it doesn't exist before creating (prevents duplicates)

#### Efficient Workflows

- **Batch similar changes** - When in Global Fields, complete all changes to one entity type before switching
- **Use detail pages for focused edits** - When editing a single entity, use the detail page for better UX
- **Leverage search** - In Global Fields, search is faster than browsing
- **Cache your choices** - Remember which entities are most commonly used/edited

#### Database Considerations

- **Save after each edit** - Don't make multiple changes without saving
- **Verify changes saved** - Check the success notification before navigating away
- **Refresh if needed** - If data looks stale, refresh the page (F5)
- **Report slowness** - If Global Fields is slow with large datasets, notify your administrator

---

## 8. Troubleshooting

### Problem: "Cannot Delete: Entity is Used in X Listings"

**Error Message:**
```
❌ Cannot delete entity
   This entity is used in 15 listings.
   To delete it, reassign or remove those listings first.
```

**What's happening:**
- The entity is associated with 15 active listings
- Deleting it would break those listings
- The system prevents this to protect data integrity

**Solutions:**

1. **Accept that entity must stay** (Most common)
   - The entity will remain in your system
   - It continues to work with the 15 listings
   - This is normal and expected

2. **Edit the entity instead**
   - Update incorrect or outdated information
   - Rename if necessary
   - Keep the entity but improve its data

3. **Reassign those 15 listings**
   - Find those 15 listings
   - Change their component references to different entities
   - Save each listing
   - Once all reassigned, entity has 0 usage → can be deleted

4. **Delete the 15 listings** (Use caution)
   - Only if listings are truly obsolete
   - Permanent action with no undo
   - Notify team members first

### Problem: "Validation Error: Name Already Exists"

**Error Message:**
```
❌ Validation error
   A CPU with name 'Intel Core i7-13700K' already exists.
```

**What's happening:**
- You're trying to create or edit an entity with a name that's already in use
- The system prevents duplicate names to maintain data integrity

**Solutions:**

1. **Use the existing entity**
   - Search for the existing entity in Global Fields
   - Use that entity in your listings instead
   - No need to create another

2. **Edit the existing entity**
   - If the existing entity has incorrect data
   - Open it and correct the information
   - Don't create a new one

3. **Give your entity a unique name**
   - Add a qualifier: "Intel Core i7-13700K (Tray)"
   - Add a number: "Intel Core i7-13700K #2"
   - Make the name clearly distinct

4. **Merge duplicates**
   - Decide which entry to keep
   - Reassign all listings from the unwanted entry
   - Delete the unwanted entry
   - Keep and use the main entry

### Problem: Edit Button Not Visible

**What you see:**
- You're on an entity detail page
- The Edit button is missing or grayed out

**Possible causes:**

1. **Permission restrictions**
   - Your user account may not have edit permissions
   - Contact your system administrator

2. **Entity is read-only**
   - System entities may not be editable
   - Try creating a new custom entity instead

3. **Browser issue**
   - Refresh the page (F5 or Cmd+R)
   - Clear browser cache (Ctrl+Shift+Delete)
   - Try a different browser

4. **Session expired**
   - You've been logged out
   - Log back in and navigate to the entity again

**Solutions:**

- [ ] Refresh the page and try again
- [ ] Clear browser cache and reload
- [ ] Try in an incognito/private window
- [ ] Check your user permissions
- [ ] Contact administrator if button still missing

### Problem: Changes Not Saving

**What happens:**
- You click "Save Changes"
- Modal stays open or notification doesn't appear
- Entity data doesn't update

**Possible causes:**

1. **Validation errors**
   - Required fields are empty
   - Numeric fields have invalid values
   - Names are duplicates

2. **Network issue**
   - Connection dropped during save
   - Server didn't receive the request
   - Network timeout occurred

3. **Session problem**
   - Session may have expired
   - May have been logged out
   - Authentication token invalid

**Solutions:**

1. **Check for validation errors**
   - Look for red error messages in the form
   - Ensure all `*` required fields are filled
   - Verify numeric fields contain valid numbers
   - Check for duplicate names

2. **Try saving again**
   - Click "Save Changes" again
   - Wait for the success notification

3. **Refresh and retry**
   - Refresh the page (F5)
   - Navigate back to entity detail page
   - Click Edit again
   - Make changes and save

4. **Check network connection**
   - Verify you're connected to the internet
   - Check if other websites load normally
   - Try from a different network

5. **Log out and log back in**
   - Click your profile menu
   - Select "Log Out"
   - Log back in
   - Return to entity and try again

### Problem: Global Fields Data Grid is Slow

**What's happening:**
- Global Fields is loading slowly
- Search/filter is lagging
- Scrolling is jerky

**Possible causes:**

1. **Large dataset**
   - Entity type has 1000+ entries
   - Browser struggling to render all rows

2. **Browser performance**
   - Too many other tabs open
   - Browser cache is full
   - System running low on memory

3. **Network issue**
   - Slow internet connection
   - Server is under load
   - API response time is high

**Solutions:**

1. **Use pagination**
   - Select "Show 25 entries" instead of "Show 100"
   - Navigate between pages instead of scrolling
   - Faster rendering with fewer visible rows

2. **Use search/filter**
   - Don't browse all pages
   - Search for specific entities
   - Filter to narrow results

3. **Clear browser cache**
   - Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
   - Select "Cached images and files"
   - Click "Clear"

4. **Close other tabs**
   - Each tab uses browser memory
   - Closing unnecessary tabs frees resources
   - Reload Global Fields in the remaining tab

5. **Try a different browser**
   - Test in Chrome, Firefox, Safari
   - Identifies if issue is browser-specific

6. **Contact IT support**
   - If slowness persists
   - May indicate server-side issue
   - Provide details about dataset size and browser

### Problem: "Confirmation Dialog Won't Accept My Input"

**What's happening:**
- You're trying to delete an in-use entity
- Confirmation dialog asks you to type the entity name
- Delete button remains disabled

**Possible causes:**

1. **Typo in name**
   - You typed a slightly different name
   - Capitalization or spacing is different
   - Extra/missing characters

2. **Copy-paste issue**
   - Pasted text includes extra spaces
   - Special characters not copied correctly

3. **Browser input lag**
   - Text not fully entered in field
   - Input field lost focus

**Solutions:**

1. **Type carefully**
   - Type the exact entity name as shown in the dialog
   - Match capitalization exactly
   - Don't add extra spaces before/after

2. **Copy name from dialog**
   - Select the entity name from the dialog text
   - Paste it into the input field
   - Avoids typing errors

3. **Clear and retype**
   - Click in the input field
   - Select all (Ctrl+A)
   - Delete
   - Type the name again carefully

4. **Browser refresh**
   - If still not working, refresh (F5)
   - Start deletion process again
   - Type the name fresh

---

## 9. Frequently Asked Questions

### Can I Undo a Deletion?

**Q: I deleted an entity by mistake. Can I undo it?**

**A:** Unfortunately, **deletions are permanent and cannot be undone**. However, you have a few options:

1. **Restore from backup** - If your organization maintains database backups, your administrator may be able to restore the deleted entity
2. **Recreate manually** - Create the entity again with the same specifications
3. **Check deletion logs** - Ask your administrator to check if deletion was logged with details

**Prevention tips:**
- Always verify before clicking Delete
- Use the "Used in" badge to understand impact
- When deleting in-use entities, carefully review the confirmation dialog

---

### What Happens If I Delete an Entity Used in Listings?

**Q: What happens to my listings if I delete an entity they reference?**

**A:** The system **prevents** deletion of in-use entities. You will see an error message: "Cannot delete: entity is used in X listings."

If somehow an in-use entity were deleted (should not be possible):
- Listings would lose the reference
- Associated component data would be incomplete
- Valuation and scoring might be affected
- Data integrity issues could occur

**This is why the system prevents deletion.** See "When Entity is In Use" in Section 7 for your options.

---

### How Do I Find Duplicate Entities?

**Q: How do I know which entities are duplicates? How can I find them?**

**A:** Use these techniques:

**Method 1: Global Fields Search**
1. Go to Global Fields
2. Select the entity type (e.g., CPU)
3. Search for the base name: "Intel Core i7"
4. Review results to find duplicates
5. Look for:
   - Different formatting: "Intel Core i7-13700K" vs "intel core i7 13700k"
   - Repeated entries: Two entries for the exact same component
   - Similar specs: Entries with nearly identical specifications

**Method 2: Manual Comparison**
1. Open entity detail pages for suspected duplicates
2. Compare specifications:
   - Cores, threads, TDP (for CPUs)
   - VRAM, memory type (for GPUs)
   - DDR generation, speed (for RAM)
3. If specs match exactly, they're likely duplicates

**Method 3: Ask Your Team**
- Communicate with other data managers
- Share suspected duplicates
- Get consensus before deleting

**Before deleting:**
- Decide which version to keep
- Reassign all listings from the unwanted version
- Delete the unwanted version

---

### Can I Bulk Edit Multiple Entities?

**Q: Can I edit multiple entities at once?**

**A:** Currently, **bulk editing is not available**. You must edit each entity individually.

**Workarounds:**

1. **Edit from Global Fields**
   - Switch to Global Fields for your entity type
   - Edit one entity at a time
   - Faster than navigating between detail pages

2. **Plan updates systematically**
   - Make a list of all updates needed
   - Work through them systematically
   - Groups similar updates together

3. **Request bulk editing feature**
   - Contact your product team
   - Provide use case for bulk operations
   - Help prioritize future enhancements

---

### What Are "Attributes"?

**Q: I see "Attributes" in the edit form. What are they? How do I use them?**

**A:** **Attributes** are custom key-value pairs that store additional information about entities.

**How they work:**
- Key: A name/label (e.g., "Architecture", "Color", "Warranty")
- Value: The actual data (e.g., "Zen 4", "Black", "3 years")
- You can add as many attributes as needed
- Each entity can have different attributes

**Common attributes:**

| Entity Type | Common Attributes |
|------------|-------------------|
| CPU | Architecture, Process node, Release date, Market segment |
| GPU | Architecture, VRAM, Ray tracing support |
| RAM Spec | Rank, ECC support, Brand, Timings |
| Storage | Cache capacity, MTBF, Warranty |
| Ports Profile | Certification level, Brand, Rated capacity |
| Scoring Profile | Target market, Data source, Update frequency |

**How to add attributes:**

1. In the Edit form, find **Attributes** section
2. Click **Add Attribute** button
3. Enter Key: "Architecture"
4. Enter Value: "Zen 4"
5. Click **+ Add more** to add another attribute
6. Or click **Save Changes** to finish

**Example:**
```
Attribute 1:
  Key: "Architecture"
  Value: "Zen 4"

Attribute 2:
  Key: "Process node"
  Value: "5nm"

Attribute 3:
  Key: "Release date"
  Value: "October 2022"
```

---

### Is There a Default Profile I Can't Delete?

**Q: Can I delete all scoring profiles? What if there's only one?**

**A:** No. **At least one scoring profile must exist and be marked as default.**

**Rule:**
- You must always have a default scoring profile
- The system uses the default profile for listings that don't have a specific profile assigned
- Cannot delete the only default profile

**Error message:**
```
❌ Cannot delete
   This is the only default profile.
   Create or mark another profile as default before deleting this one.
```

**How to handle:**

If you have multiple profiles and want to delete one:
1. Ensure at least one other profile exists
2. Mark another profile as default (Edit it, check "Default" checkbox)
3. Save that profile
4. Now you can delete the old default profile

If you only have one profile:
- Create a new default profile first
- Mark the new one as default
- Then delete the old one if desired

---

### Where Do Benchmark Scores Come From?

**Q: How are CPU/GPU benchmark scores populated? Can I import them?**

**A:** Benchmark scores come from:

**PassMark CPU Benchmarks:**
- Multi-threaded CPU Mark score
- Single-threaded CPU Mark score
- Integrated GPU Mark (iGPU) score
- Source: PassMark Software data

**How to update:**
1. Obtain PassMark data (CSV export)
2. Contact your administrator
3. Administrator imports via:
   ```bash
   poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
   ```
4. Scores are updated in system

**GPU Benchmarks:**
- GPU Mark (NVIDIA/AMD discrete)
- Metal Score (macOS)
- Source: PassMark, developer specs

**Manually updating:**
1. Open CPU/GPU detail page
2. Click Edit
3. Enter benchmark scores in the form
4. Save Changes

---

### How Are Listings Updated When I Edit an Entity?

**Q: If I edit a CPU entity, do all listings using that CPU automatically update?**

**A:** Yes, **automatically**. Here's how it works:

**Entity Update Flow:**
1. You edit a CPU: Change cores from 8 to 10
2. You click "Save Changes"
3. Database updates the CPU entity
4. All listings referencing this CPU see the new specs immediately
5. Metrics and valuations may recalculate automatically

**Metrics recalculation:**
- Performance scores may update based on new specs
- Valuation may change (if CPU Mark changes)
- Price adjustments recalculated (if specifications impact pricing)

**Listings are NOT recreated:**
- Same listing IDs and URLs
- Same history and created dates
- Just updated data and re-calculated metrics

**Example:**
```
Scenario: Update CPU benchmark score

Before:
- CPU "Intel Core i7-13700K" has CPU Mark: 55000
- 50 listings use this CPU
- Listings show metrics based on 55000

You edit:
- Change CPU Mark to 56000 (new test results)
- Save Changes

After:
- CPU entity updated to 56000
- All 50 listings immediately see 56000
- Metrics recalculate for all 50 listings
- No manual action needed
```

---

### Can I See Who Last Edited an Entity?

**Q: Can I see who edited an entity and when?**

**A:** Yes, on each entity detail page you'll see:

- **Created** timestamp - When entity was originally created
- **Updated** timestamp - When entity was last modified
- **Created By** (if available) - User who created entity
- **Updated By** (if available) - User who last edited entity

This audit information helps you:
- Understand entity history
- Identify stale data (old "updated" date)
- Contact the responsible person for questions
- Track who made recent changes

---

### What If Two People Edit an Entity at the Same Time?

**Q: What happens if two admins try to edit the same entity simultaneously?**

**A:** The system handles concurrent edits with **last-write-wins** behavior:

1. **Admin A** opens entity and clicks Edit
2. **Admin B** opens the same entity and clicks Edit
3. **Admin A** makes changes and clicks "Save Changes"
4. **A's changes** are saved successfully
5. **Admin B** makes different changes and clicks "Save Changes"
6. **B's changes** overwrite A's changes

**Result:** Only B's changes persist. A's changes are lost.

**Best practice:**
- **Communicate** before editing high-impact entities
- **Take turns** editing shared entities
- **Verify** your changes were saved correctly
- **Check** the "Updated" timestamp to see when changes were last made
- **Refresh** the page if you suspect someone else edited the entity

---

### Where Do I Report Bugs or Request Features?

**Q: I found an issue with entity management. Who do I contact?**

**A:**

**For bugs:**
- Contact your system administrator with details:
  - What you were trying to do
  - What went wrong
  - Error messages you saw
  - Screenshots if possible
- Administrator escalates to development team

**For feature requests:**
- Suggest enhancements through your normal feedback channel
- Examples: Bulk editing, bulk deletion, audit logs, import/export
- Product team prioritizes based on user feedback

**Common enhancement requests:**
- Bulk edit multiple entities
- Export entities to CSV
- Import entities from CSV
- Advanced filtering and search
- Entity usage analytics
- Version history/rollback

---

## 10. Changelog

### Version 1.0 (November 2025)

**Initial Release:**
- Added comprehensive entity management guide
- Step-by-step instructions for CRUD operations
- Detailed safety features for deletions
- Global Fields workspace documentation
- Entity-specific guidance for all 7 types
- Best practices and troubleshooting
- FAQ section with common questions
- Validation error documentation
- Integration with Edit/Delete functionality

**Features Documented:**
- Entity detail pages with Edit/Delete buttons
- Global Fields workspace for bulk management
- Safe deletion with usage validation
- Name confirmation for in-use entity deletion
- Entity-specific fields and attributes
- Scoring profile default requirements
- Performance metrics and benchmarks

**Supported Entity Types:**
- CPU (processors with benchmarks)
- GPU (graphics cards)
- RAM Spec (memory configurations)
- Storage Profile (disk specifications)
- Ports Profile (connectivity)
- Scoring Profile (valuation weights)
- Listing (PC entries)

---

**Document Information:**

- **Created:** November 14, 2025
- **Last Updated:** November 14, 2025
- **Version:** 1.0
- **Status:** Published
- **Audience:** System administrators, data managers, power users
- **Related Documentation:**
  - API Catalog CRUD Endpoints
  - Global Fields Configuration
  - Entity Edit/Delete Endpoints
