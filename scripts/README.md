# Scripts Reference

Quick reference for Deal Brain utility scripts organized by category.

## Quick Reference

**Most Common Operations:**

```bash
# Initial data import
poetry run python scripts/setup/import_passmark_data.py data/passmark_cpus.csv
poetry run python scripts/setup/import_libraries.py --all

# Update CPU catalog from PassMark
poetry run python scripts/maintenance/update_cpus_from_passmark.py --cpu-json data/cpu.json --passmark-csv data/CPUModelSummary.csv

# Recalculate metrics after changes
poetry run python scripts/maintenance/recalculate_all_metrics.py
```

---

## Setup Scripts

**Initial data population and import operations.**

| Script | Purpose | Usage |
|--------|---------|-------|
| `import_entities.py` | Import hardware entities (CPUs, GPUs) from JSON/CSV | `poetry run python scripts/setup/import_entities.py cpu data/cpus.json` |
| `import_libraries.py` | Import reference libraries (custom fields, valuation rules, profiles) | `poetry run python scripts/setup/import_libraries.py --all` |
| `import_passmark_data.py` | Import PassMark benchmark data into CPU catalog | `poetry run python scripts/setup/import_passmark_data.py data/passmark_cpus.csv` |

---

## Maintenance Scripts

**Recurring operations for data updates and calculations.**

| Script | Purpose | Usage |
|--------|---------|-------|
| `update_cpus_from_passmark.py` | Update CPU catalog with latest PassMark CSV dumps | `poetry run python scripts/maintenance/update_cpus_from_passmark.py --cpu-json data/cpu.json --passmark-csv data/CPUModelSummary.csv` |
| `generate_formula_reference.py` | Generate JSON schema for baseline rule formulas | `poetry run python scripts/maintenance/generate_formula_reference.py` |
| `recalculate_adjusted_metrics.py` | Recalculate adjusted CPU metrics (delta-based, granular) | `poetry run python scripts/maintenance/recalculate_adjusted_metrics.py` |
| `recalculate_all_metrics.py` | Bulk recalculate dollar_per_cpu_mark for all listings | `poetry run python scripts/maintenance/recalculate_all_metrics.py` |
| `recalculate_cpu_marks.py` | Bulk recalculate CPU Mark metrics for all listings | `poetry run python scripts/maintenance/recalculate_cpu_marks.py` |

---

## Development Scripts

**Testing and sample data utilities.**

| Script | Purpose | Usage |
|--------|---------|-------|
| `seed_sample_listings.py` | Create sample listings with metadata and ports for testing | `poetry run python scripts/development/seed_sample_listings.py` |
| `test_cpu_analytics.py` | Test CPU analytics service methods | `poetry run python scripts/development/test_cpu_analytics.py` |

---

## Common Workflows

### Initial Setup
```bash
# 1. Import PassMark benchmarks
poetry run python scripts/setup/import_passmark_data.py data/passmark_cpus.csv

# 2. Import reference libraries
poetry run python scripts/setup/import_libraries.py --all

# 3. (Optional) Import additional entities
poetry run python scripts/setup/import_entities.py cpu data/cpus.json
```

### After Schema or Rule Changes
```bash
# Recalculate all metrics
poetry run python scripts/maintenance/recalculate_all_metrics.py

# Generate updated formula reference
poetry run python scripts/maintenance/generate_formula_reference.py
```

### Updating CPU Catalog
```bash
# Update from latest PassMark data
poetry run python scripts/maintenance/update_cpus_from_passmark.py \
  --cpu-json data/cpu.json \
  --passmark-csv data/CPUModelSummary.csv \
  --out data/cpu.updated.json
```

---

## Notes

- All scripts should be run from the project root using `poetry run`
- Scripts use async database operations and require the API database to be available
- For detailed usage and options, run any script with `--help`
- PassMark data must be obtained legally (licensed CSV dumps, not web scraping)
