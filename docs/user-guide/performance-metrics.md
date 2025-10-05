# Performance Metrics & Data Enrichment - User Guide

**Version:** 1.0
**Last Updated:** October 5, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Performance Metrics](#performance-metrics)
3. [Product Metadata](#product-metadata)
4. [Connectivity (Ports)](#connectivity-ports)
5. [CPU Information Panel](#cpu-information-panel)
6. [Using the Listing Form](#using-the-listing-form)
7. [Interpreting Metrics](#interpreting-metrics)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Performance Metrics & Data Enrichment feature provides comprehensive price-to-performance analysis for PC listings. It introduces:

- **Dual CPU Mark Metrics** - Separate single-thread and multi-thread efficiency calculations
- **Product Metadata** - Manufacturer, series, model number, and form factor classification
- **Ports Management** - Structured connectivity data for USB, HDMI, DisplayPort, etc.
- **Enhanced CPU Data** - PassMark benchmarks, TDP, release year, and iGPU information

---

## Performance Metrics

### Dual CPU Mark Columns

The Listings table now displays **two** CPU performance efficiency metrics:

#### $/CPU Mark (Single)

**What it measures:** Cost per PassMark single-thread point

**Best for:**
- Gaming workloads (most games favor single-thread performance)
- Single-core applications (web browsers, office apps)
- Responsiveness and snappiness

**How to read:** Lower is better. A listing with `$0.15` per single-thread point is better value than `$0.20`.

#### $/CPU Mark (Multi)

**What it measures:** Cost per PassMark multi-thread point

**Best for:**
- Video editing and rendering
- 3D modeling and CAD
- Compiling code
- Server workloads
- Virtualization

**How to read:** Lower is better. A listing with `$0.018` per multi-thread point is better value than `$0.025`.

### Dual Value Display

Each metric displays **two values** in a stacked layout:

```
┌─────────────────────┐
│  $0.20              │  ← Raw value (using list price)
│  $0.16 ↓20%        │  ← Adjusted value (after deductions) with improvement indicator
└─────────────────────┘
```

**Color coding:**
- **Green with ↓** - Improvement (better value after component deductions)
- **Red with ↑** - Degradation (worse value after deductions)
- **Gray with no arrow** - Neutral (no significant change)

**Example:**

A listing priced at $800 with a CPU valued at $150 in RAM has:
- **Raw $/CPU Mark:** $800 ÷ 4000 = `$0.20`
- **Adjusted $/CPU Mark:** $650 ÷ 4000 = `$0.16` ↓20%

The adjusted value shows **20% better price efficiency** after accounting for RAM value.

---

## Product Metadata

### Manufacturer

**Purpose:** Identify the PC brand or builder

**Options:**
- Dell
- HP
- Lenovo
- Apple
- ASUS
- Acer
- MSI
- Custom Build
- Other

**Usage:**
- Filter listings by preferred manufacturer
- Compare pricing across brands
- Identify warranty and support providers

### Series

**Purpose:** Product line identification

**Examples:**
- Dell: OptiPlex, Latitude, XPS
- Lenovo: ThinkCentre, ThinkPad, IdeaPad
- HP: EliteDesk, ProDesk, Pavilion
- Apple: Mac Studio, Mac Mini, MacBook Pro

**Usage:**
- Compare models within a product line
- Identify design/form factor families
- Track generational improvements

### Model Number

**Purpose:** Specific SKU or model identifier

**Examples:**
- Dell OptiPlex: 7090, 5090, 3090
- Lenovo ThinkCentre: M75q, M90a, M720q
- HP EliteDesk: 800 G9, 600 G6

**Usage:**
- Precise product identification
- Cross-reference with manufacturer specs
- Verify exact configuration

### Form Factor

**Purpose:** Hardware classification by size/type

**Options:**
- **Desktop** - Full tower or mid tower systems
- **Laptop** - Notebook or ultrabook form factor
- **Server** - Rack-mounted or tower servers
- **Mini-PC** - Compact systems (NUC, SFF)
- **All-in-One** - Display + computer integrated
- **Other** - Custom or specialized form factors

**Usage:**
- Filter by workspace constraints
- Compare power/performance by category
- Identify thermal and noise characteristics

---

## Connectivity (Ports)

### Ports Builder

The Ports Builder allows you to specify available connectivity options with precise quantities.

**Port Types:**
- **USB-A** - Standard USB Type-A ports
- **USB-C** - USB Type-C ports (may include Thunderbolt)
- **HDMI** - HDMI video output
- **DisplayPort** - DisplayPort video output
- **Ethernet** - RJ45 network port (typically 1Gbps or 2.5Gbps)
- **Thunderbolt** - Thunderbolt 3/4 ports
- **Audio** - 3.5mm audio jacks (headphone, microphone, line-in/out)
- **SD Card** - SD card reader
- **Other** - Specialized ports (serial, parallel, etc.)

### Adding Ports

1. Click **"Add Port"** button
2. Select port type from dropdown
3. Enter quantity (1-16)
4. Repeat for additional port types
5. Click **X** to remove a port entry

### Ports Display

In the listings table, ports display in a compact format:

**Example:** `3× USB-A  2× HDMI  1× Ethernet`

Click the port text to view a detailed breakdown in a popover.

**Use Cases:**
- **Multi-monitor setups** - Filter for listings with 2+ HDMI/DisplayPort
- **Peripheral compatibility** - Ensure sufficient USB-A ports
- **Network connectivity** - Verify Ethernet availability for servers
- **Docking requirements** - Check for Thunderbolt support

---

## CPU Information Panel

When you select a CPU in the listing form, an information panel automatically appears showing:

### Benchmark Scores

- **Single-Thread:** PassMark single-thread rating (e.g., 3,985)
- **Multi-Thread:** PassMark multi-thread rating (e.g., 35,864)

### Thermal & Timing

- **TDP:** Thermal Design Power in watts (e.g., 125W)
- **Year:** CPU release year (e.g., 2021)

### Integrated Graphics

- **iGPU Model:** Integrated GPU name (e.g., Intel UHD 770)
- **G3D Score:** PassMark 3D Graphics Mark (e.g., 1,850)

**Example Panel:**

```
┌─────────────────────────────────────┐
│ Intel Core i7-12700K                │
├─────────────────────────────────────┤
│ Single-Thread: 3,985    TDP: 125W  │
│ Multi-Thread:  35,864   Year: 2021 │
│ iGPU: Intel UHD 770 (G3D: 1,850)   │
└─────────────────────────────────────┘
```

**What this tells you:**
- **High single-thread (3,985)** - Excellent for gaming and responsiveness
- **Very high multi-thread (35,864)** - Great for productivity workloads
- **125W TDP** - Requires adequate cooling, not suitable for passively-cooled mini-PCs
- **2021 release** - Modern architecture with DDR5 support
- **iGPU included** - Can run without dedicated GPU for basic tasks

---

## Using the Listing Form

### Product Information Section

1. **Manufacturer** - Select from dropdown (required for filtering)
2. **Series** - Enter product line (e.g., "OptiPlex")
3. **Model Number** - Enter SKU (e.g., "7090")
4. **Form Factor** - Select category (Desktop, Laptop, etc.)

### Hardware Configuration Section

1. **CPU** - Select from dropdown
   - Info panel appears automatically
   - Shows benchmark scores, TDP, release year, iGPU
2. **RAM (GB)** - Enter memory capacity
3. **Primary Storage** - Capacity and type (NVMe SSD, SATA SSD, etc.)
4. **Secondary Storage** - Optional additional storage

### Connectivity Section

1. **Ports** - Use Ports Builder
   - Click "Add Port" for each port type
   - Enter quantities
   - Remove unwanted entries with X button

### Automatic Processing

After clicking **"Save listing"**, the system automatically:

1. ✅ Saves listing with all metadata
2. ✅ Creates ports profile (if ports specified)
3. ✅ Calculates performance metrics (if CPU assigned)
4. ✅ Returns to listings table with updated data

---

## Interpreting Metrics

### When to Use Single-Thread Metrics

✅ **Use for:**
- Gaming PCs (most games favor single-thread)
- Everyday desktop use (web browsing, office apps)
- Responsiveness comparisons
- Laptops for general productivity

❌ **Don't use for:**
- Workstations (rendering, CAD, video editing)
- Servers (multi-user, virtualization)
- Compiling large codebases

### When to Use Multi-Thread Metrics

✅ **Use for:**
- Video editing workstations
- 3D rendering machines
- Software compilation servers
- Virtualization hosts
- Scientific computing

❌ **Don't use for:**
- Gaming-focused builds (unless streaming)
- Basic office/web use
- Budget single-user desktops

### Comparing Across Listings

**Scenario:** Choosing between two listings

| Listing | Price | CPU | Single | Multi | Best For |
|---------|-------|-----|--------|-------|----------|
| A | $800 | i7-12700K | $0.20 | $0.022 | Gaming + productivity |
| B | $750 | Ryzen 9 5950X | $0.21 | $0.016 | Heavy multi-thread work |

**Analysis:**
- **Listing A:** Slightly better single-thread value (gaming)
- **Listing B:** Significantly better multi-thread value (rendering)

**Decision:**
- Choose **A** for gaming-first builds
- Choose **B** for video editing or server use

### Understanding Adjusted Values

**Raw metric:** Price ÷ CPU Mark (no deductions)
**Adjusted metric:** (Price - Component Values) ÷ CPU Mark

**Example:**

```
Listing: Dell OptiPlex 7090
Price: $800
RAM: 32GB (valued at $120)
Adjusted Price: $680

CPU: i7-12700K (Single-Thread: 4000)

Raw $/CPU Mark: $800 ÷ 4000 = $0.20
Adjusted $/CPU Mark: $680 ÷ 4000 = $0.17 ↓15%
```

The **adjusted metric** shows the true CPU value after excluding RAM cost.

---

## Best Practices

### Data Entry

✅ **Do:**
- Always select manufacturer and form factor for better filtering
- Add ports data for PCs with unique connectivity
- Use consistent naming (e.g., "OptiPlex" not "Optiplex")
- Enter series and model for popular brands (Dell, HP, Lenovo)

❌ **Don't:**
- Leave manufacturer blank (makes filtering harder)
- Guess port quantities (leave blank if unknown)
- Mix naming conventions (be consistent)

### Metric Usage

✅ **Do:**
- Compare metrics within the same form factor (Mini-PC vs Mini-PC)
- Consider both raw and adjusted values
- Use multi-thread for workstation builds
- Use single-thread for gaming builds

❌ **Don't:**
- Compare Desktop metrics to Laptop metrics (different TDP/cooling)
- Ignore adjusted values (they show true component value)
- Use only one metric (both provide insight)
- Compare across different use cases

### Filtering Tips

**Finding best gaming value:**
1. Filter: Form Factor = "Desktop" or "Mini-PC"
2. Sort by: $/CPU Mark (Single) - Adjusted
3. Filter: TDP ≥ 65W (adequate performance)

**Finding best workstation value:**
1. Filter: Form Factor = "Desktop"
2. Sort by: $/CPU Mark (Multi) - Adjusted
3. Filter: RAM ≥ 32GB, Multi-Thread ≥ 25,000

**Finding quiet mini-PCs:**
1. Filter: Form Factor = "Mini-PC"
2. Filter: TDP ≤ 65W
3. Sort by: $/CPU Mark (Single) - Adjusted

---

## Troubleshooting

### Metrics Show as Null/Empty

**Cause:** CPU not assigned or missing benchmark data

**Solution:**
1. Edit listing and select a CPU
2. If CPU selected but metrics still null, run:
   ```bash
   poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
   poetry run python scripts/recalculate_all_metrics.py
   ```

### CPU Info Panel Not Appearing

**Cause:** CPU not yet selected or data not loaded

**Solution:**
1. Select a CPU from the dropdown
2. Wait 1-2 seconds for data to load
3. If panel doesn't appear, check browser console for errors

### Ports Not Displaying in Table

**Cause:** Ports profile not created or orphaned

**Solution:**
1. Edit listing
2. Re-add ports using Ports Builder
3. Save listing

### Adjusted Metrics Same as Raw

**Cause:** No valuation rules applied (adjusted_price equals base price)

**Solution:**
1. This is normal if no component deductions apply
2. Create valuation rules for RAM/storage if desired
3. Recalculate metrics after rule application

### Performance Metrics Not Calculating

**Cause:** Missing CPU benchmark data

**Solution:**
1. Verify CPU has `cpu_mark_single` and `cpu_mark_multi` values
2. Import PassMark data if missing:
   ```bash
   poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
   ```
3. Recalculate all metrics:
   ```bash
   poetry run python scripts/recalculate_all_metrics.py
   ```

---

## Additional Resources

- **PRD:** `docs/project_plans/requests/prd-10-5-performance-metrics.md`
- **Implementation Plan:** `docs/project_plans/requests/implementation-plan-10-5.md`
- **QA Guide:** `docs/performance-metrics-qa.md`
- **API Documentation:** OpenAPI at `/docs` (when server running)

---

**Questions or Issues?**

File a GitHub issue or contact the development team.
