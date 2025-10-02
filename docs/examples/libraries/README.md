# Deal Brain Reference Libraries

This directory contains production-ready reference data libraries for Deal Brain, including custom field definitions, valuation rules, rulesets, and scoring profiles.

## 📁 Directory Structure

```
libraries/
├── fields/           # Custom field definitions
├── rules/            # Valuation rule libraries
├── rulesets/         # Packaged ruleset bundles (.dbrs)
├── profiles/         # Scoring profile configurations
└── README.md         # This file
```

## 🚀 Quick Start

### Import All Libraries

```bash
# Import everything (fields, rules, profiles)
poetry run python scripts/import_libraries.py --all

# Import specific categories
poetry run python scripts/import_libraries.py --fields
poetry run python scripts/import_libraries.py --rules
poetry run python scripts/import_libraries.py --profiles

# Import specific ruleset
poetry run python scripts/import_libraries.py --ruleset gaming-pc-rules
```

### Using the CLI

```bash
# Import custom fields
poetry run dealbrain-cli fields import docs/examples/libraries/fields/listing-custom-fields.yaml

# Import rules
poetry run dealbrain-cli rules import docs/examples/libraries/rules/gaming-pc-rules.yaml

# Export rules to package
poetry run dealbrain-cli rules package "Gaming PC Valuation" --output gaming-pc.dbrs
```

## 📋 Custom Fields Library

### `fields/listing-custom-fields.yaml`

**42 custom field definitions** extending the base Listing model:

**Categories:**
- **Physical Condition** (3 fields): cosmetic_condition, has_original_packaging, warranty_months_remaining
- **Performance & Testing** (2 fields): benchmark_tested, stress_test_hours
- **Storage Details** (2 fields): secondary_storage_type, secondary_storage_capacity_gb
- **Networking** (2 fields): wifi_standard, ethernet_speed_gbps
- **Ports & Expansion** (3 fields): usb_c_count, thunderbolt_count, pcie_slots_available
- **Power & Cooling** (3 fields): psu_wattage, psu_efficiency_rating, cooling_solution
- **RGB & Aesthetics** (3 fields): has_rgb_lighting, case_form_factor, has_tempered_glass
- **Market & Sales** (5 fields): days_since_listing, seller_rating, number_of_reviews, shipping_cost_usd, local_pickup_available
- **Build Quality** (5 fields): is_prebuilt, manufacturer, has_custom_cables, bios_updated, supports_dual_gpu
- **Operating System** (2 fields): os_installed, os_license_type
- **Special Features** (3 fields): includes_peripherals, refurbishment_grade

**Use Cases:**
- Enhanced valuation accuracy
- Detailed filtering and search
- Trust and quality indicators
- Market competitiveness tracking

## 🎯 Valuation Rules Libraries

### `rules/gaming-pc-rules.yaml`

**Gaming PC Valuation Ruleset** - 6 rule groups, 30+ rules

**Rule Groups:**
1. **CPU Performance Tier** (weight: 0.25)
   - Flagship CPU Premium ($150): 45k+ CPU Mark or 16+ cores
   - High-End CPU Premium ($100): 30-45k CPU Mark, 8+ cores
   - Mid-Range CPU ($50): 20-30k CPU Mark
   - Budget CPU Penalty (-$75): <15k CPU Mark

2. **GPU Performance Tier** (weight: 0.35)
   - Enthusiast GPU Premium ($250): 30k+ GPU Mark
   - High-End GPU Premium ($150): 20-30k GPU Mark
   - Mid-Range GPU ($75): 12-20k GPU Mark
   - Entry-Level GPU Penalty (-$50): <8k GPU Mark
   - High VRAM Bonus ($75): 16GB+ VRAM

3. **RAM Capacity & Speed** (weight: 0.15)
   - High-Capacity RAM: $4.50/GB for 64GB+
   - Standard Gaming RAM ($80): 32GB optimal
   - Adequate RAM ($40): 16GB minimum
   - Insufficient RAM Penalty (-$60): <16GB

4. **Storage Performance** (weight: 0.10)
   - Gen4 NVMe Premium ($60)
   - NVMe SSD Standard ($40)
   - SATA SSD Penalty (-$20)
   - HDD Penalty (-$80)
   - Large Capacity Bonus ($50): 2TB+

5. **Condition & Warranty** (weight: 0.08)
   - New Condition: 20% multiplier
   - Like-New: 10% multiplier
   - Fair Condition: 15% penalty
   - Warranty: $3/month remaining

6. **Gaming Features** (weight: 0.07)
   - WiFi 6E Premium ($40)
   - Thunderbolt Support ($30/port)
   - RGB Lighting Bonus ($25)
   - Tempered Glass ($15)

**Target Market:** Gaming enthusiasts, high FPS gamers, streamers
**Price Range:** $800 - $3,000+

---

### `rules/workstation-rules.yaml`

**Workstation Valuation Ruleset** - 6 rule groups, 25+ rules

**Rule Groups:**
1. **CPU Multi-Core Performance** (weight: 0.30)
   - HEDT CPU Premium ($300): 32+ cores, 60k+ CPU Mark
   - High Core Count ($200): 24-31 cores, 50k+ CPU Mark
   - Professional CPU ($120): 16-23 cores, 35k+ CPU Mark
   - Insufficient Cores (-$80): <12 cores

2. **Professional GPU** (weight: 0.25)
   - Quadro/Radeon Pro Premium ($200)
   - High VRAM Premium ($150): 24GB+
   - Adequate VRAM ($80): 16-23GB
   - Dual GPU Support ($100)

3. **RAM Capacity & Type** (weight: 0.20)
   - Massive RAM: $5/GB for 128GB+
   - High-Capacity: $4/GB for 64-127GB
   - Standard Workstation ($100): 32-64GB
   - Insufficient RAM (-$120): <32GB

4. **Storage Performance & Capacity** (weight: 0.12)
   - Dual NVMe Configuration ($120)
   - Large Primary Storage ($100): 4TB+
   - NVMe Primary Standard ($60): 1TB+
   - Secondary Storage Bonus ($50): 2TB+

5. **Reliability Features** (weight: 0.08)
   - Manufacturer Certified: 15% multiplier
   - Extended Warranty: $4/month for 24+ months
   - Stress Tested ($75): 48+ hours
   - BIOS Updated ($25)

6. **Professional Features** (weight: 0.05)
   - 10GbE Network ($80)
   - 2.5GbE Network ($30)
   - Thunderbolt Professional ($60): 2+ ports
   - PCIe Expansion: $15/slot for 3+ slots
   - High Wattage PSU ($50): 1000W+
   - Platinum/Titanium PSU ($40)

**Target Market:** Content creators, 3D artists, video editors, CAD professionals
**Price Range:** $1,500 - $8,000+

---

### `rules/budget-value-rules.yaml`

**Budget Value Optimization Ruleset** - 7 rule groups, 30+ rules

**Rule Groups:**
1. **Essential Performance** (weight: 0.20)
   - Modern CPU Bonus ($40): 2020+ release
   - Quad Core Minimum ($20): 4+ cores
   - Dual Core Penalty (-$50): <4 cores

2. **Graphics Value** (weight: 0.18)
   - Dedicated GPU Bonus ($60): 3k+ GPU Mark
   - Entry Gaming GPU ($35): 6-10k GPU Mark
   - Integrated Graphics ($0): <3k GPU Mark

3. **RAM Value** (weight: 0.15)
   - Ideal Budget RAM ($50): 16GB sweet spot
   - Minimum Viable RAM ($15): 8GB
   - Insufficient RAM (-$40): <8GB
   - Overkill RAM Penalty (-$30): >32GB

4. **Storage Value** (weight: 0.20)
   - SSD Boot Drive ($45): Any SSD type
   - NVMe Bonus ($20)
   - HDD Penalty (-$60)
   - Adequate Capacity ($15): 500GB+
   - Small Storage Penalty (-$25): <256GB

5. **Essential Connectivity** (weight: 0.10)
   - WiFi Included ($20)
   - Modern WiFi Bonus ($15): WiFi 5+
   - Bluetooth Bonus ($10)
   - USB-C Port Bonus ($15)

6. **Condition & Seller Trust** (weight: 0.12)
   - Like-New Budget: 15% premium
   - Good Condition: baseline
   - Fair Condition: 20% penalty
   - High Seller Rating ($30): 4.5+ stars, 50+ reviews
   - Benchmark Tested ($25)

7. **Value Additions** (weight: 0.05)
   - OS Included ($40): Licensed OS
   - Free Shipping ($20)
   - Local Pickup ($15)
   - Peripherals Included ($35)
   - Original Packaging ($10)

**Target Market:** Students, first-time buyers, budget-conscious users
**Price Range:** $200 - $800

## ⚖️ Scoring Profiles Library

### `profiles/scoring-profiles.yaml`

**14 pre-configured scoring profiles** for different use cases:

### Gaming Profiles
- **Gaming Performance**: Balanced gaming (40% performance, 25% value)
- **Competitive Gaming**: High FPS focus (50% performance, 40% CPU weight)
- **Compact SFF Premium**: Small form factor gaming

### Content Creation Profiles
- **Video Editing Workstation**: 4K editing, rendering (45% performance)
- **3D Rendering Station**: Heavy rendering (50% performance, 40% CPU)

### General Purpose Profiles
- **Home Office Productivity**: Office work (35% value, 25% performance)
- **Student Budget Build**: Maximum value (45% value, 20% performance)
- **Home Theater PC**: Media streaming (25% storage, 25% graphics)

### Development Profiles
- **Software Development**: Programming, Docker, VMs
- **AI/ML Development**: Deep learning (40% GPU weight)

### Specialized Profiles
- **Ultimate Bargain Hunter**: Maximum value (55% value)
- **Home Server Build**: NAS, Plex, virtualization
- **All-Around Balanced**: Mixed use cases
- **Future-Proof Investment**: Longevity and upgrade path

Each profile includes:
- Metric weight distribution
- Rule group weight distribution
- Metadata (category, use cases, software)

## 📦 Using Libraries in Production

### Automated Deployment Import

Add to your deployment script:

```bash
#!/bin/bash
# deploy.sh

# Run migrations
poetry run alembic upgrade head

# Import reference libraries
poetry run python scripts/import_libraries.py --all

# Start services
docker-compose up -d
```

### Docker Entrypoint

Add to your Docker entrypoint:

```dockerfile
# Dockerfile
COPY docs/examples/libraries /app/libraries
COPY scripts/import_libraries.py /app/scripts/

# docker-entrypoint.sh
python scripts/import_libraries.py --all
exec "$@"
```

### Kubernetes Init Container

```yaml
initContainers:
  - name: import-libraries
    image: dealbrain-api:latest
    command: ["python", "scripts/import_libraries.py", "--all"]
```

## 🔄 Updating Libraries

### Modifying Existing Rules

1. Edit the YAML file
2. Delete old ruleset from database (or update version)
3. Re-import with import script

### Adding New Rules

1. Add rule to existing YAML file under appropriate group
2. Re-import (script will skip existing, add new)

### Versioning

Use semantic versioning in ruleset metadata:

```yaml
ruleset:
  name: Gaming PC Valuation
  version: 1.1.0  # Increment when changing rules
```

## 📖 Documentation References

- **User Guide**: [docs/user-guide/valuation-rules.md](../../user-guide/valuation-rules.md)
- **API Reference**: `/api/docs` (FastAPI Swagger UI)
- **CLI Reference**: `poetry run dealbrain-cli rules --help`

## 🎓 Best Practices

### Field Naming
- Use snake_case for field names
- Include units in name (e.g., `ram_gb`, `psu_wattage`)
- Prefix related fields (e.g., `secondary_storage_type`, `secondary_storage_capacity_gb`)

### Rule Organization
- Group related rules together
- Use consistent evaluation_order (100, 90, 80...)
- Higher evaluation_order = higher priority
- Document USD values in descriptions

### Weight Distribution
- Rule group weights should sum to 1.0
- Profile metric weights should sum to 1.0
- Higher weight = more impact on final score
- Test weight changes with real data

### Condition Logic
- Use AND for strict requirements
- Use OR for alternatives
- Keep conditions simple and readable
- Test edge cases (null, missing, invalid)

## 🤝 Contributing

When adding new library files:

1. Follow existing YAML structure
2. Include metadata (author, date, category)
3. Add comprehensive descriptions
4. Test import with sample data
5. Update this README
6. Add examples to user guide

## 📝 License

These reference libraries are part of Deal Brain and are provided as examples for customization.

---

**Last Updated:** 2025-10-02
**Maintainer:** Deal Brain Team
