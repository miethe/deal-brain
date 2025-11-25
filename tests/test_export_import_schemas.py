"""Tests for portable export/import schemas.

Tests validation of the v1.0.0 export schema for Deal Brain listings and collections.
"""

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from dealbrain_api.schemas.export_import import (
    CPUExport,
    CollectionDataExport,
    CollectionExport,
    CollectionItemExport,
    ComponentExport,
    DealDataExport,
    ExportMetadata,
    ListingExport,
    ListingLinkExport,
    MetadataExport,
    PerformanceExport,
    PerformanceMetricsExport,
    PortableCollectionExport,
    PortableDealExport,
    PortableExport,
    PortExport,
    PortsExport,
    RAMExport,
    StorageExport,
    ValuationExport,
)
from dealbrain_core.enums import (
    CollectionItemStatus,
    CollectionVisibility,
    ComponentType,
    Condition,
    ListingStatus,
    PortType,
    RamGeneration,
    StorageMedium,
)


# ==================== Fixtures ====================


@pytest.fixture
def sample_export_metadata() -> dict:
    """Sample export metadata."""
    return {
        "version": "1.0.0",
        "exported_at": "2025-11-19T10:30:00Z",
        "exported_by": "550e8400-e29b-41d4-a716-446655440000",
        "type": "deal"
    }


@pytest.fixture
def sample_listing() -> dict:
    """Sample listing data."""
    return {
        "id": 42,
        "title": "Dell OptiPlex 7050 Micro",
        "listing_url": "https://example.com/listing",
        "other_urls": [{"url": "https://example.com/seller", "label": "Seller"}],
        "seller": "TechDeals Inc",
        "price_usd": 299.99,
        "price_date": "2025-11-18T15:00:00Z",
        "condition": "refurb",
        "status": "active",
        "device_model": "OptiPlex 7050 Micro",
        "notes": "Excellent condition",
        "custom_fields": {"warranty_months": 12},
        "created_at": "2025-11-15T08:00:00Z",
        "updated_at": "2025-11-18T15:00:00Z"
    }


@pytest.fixture
def sample_cpu() -> dict:
    """Sample CPU data."""
    return {
        "name": "Intel Core i7-7700T",
        "manufacturer": "Intel",
        "cores": 4,
        "threads": 8,
        "tdp_w": 35,
        "igpu_model": "Intel HD Graphics 630",
        "cpu_mark_multi": 8542,
        "cpu_mark_single": 2234,
        "igpu_mark": 1153,
        "release_year": 2017
    }


@pytest.fixture
def sample_ram() -> dict:
    """Sample RAM data."""
    return {
        "total_gb": 16,
        "ddr_generation": "ddr4",
        "speed_mhz": 2400,
        "module_count": 2,
        "capacity_per_module_gb": 8,
        "notes": "Dual channel"
    }


@pytest.fixture
def sample_storage() -> dict:
    """Sample storage data."""
    return {
        "capacity_gb": 512,
        "medium": "nvme",
        "interface": "PCIe 3.0 x4",
        "form_factor": "M.2 2280",
        "performance_tier": "Mid-range"
    }


@pytest.fixture
def sample_deal_export(sample_export_metadata: dict, sample_listing: dict) -> dict:
    """Sample complete deal export."""
    return {
        "deal_brain_export": sample_export_metadata,
        "data": {
            "listing": sample_listing,
            "valuation": {
                "base_price_usd": 299.99,
                "adjusted_price_usd": 289.99,
                "valuation_breakdown": {
                    "base_price": 299.99,
                    "adjustments": [{"rule_name": "RAM Bonus", "adjustment": -10.0}],
                    "final_price": 289.99
                },
                "ruleset_name": "Standard Rules"
            },
            "performance": None,
            "metadata": {
                "manufacturer": "Dell",
                "series": "OptiPlex",
                "model_number": "7050",
                "form_factor": "Micro"
            }
        }
    }


# ==================== Export Metadata Tests ====================


def test_export_metadata_valid(sample_export_metadata: dict):
    """Test valid export metadata."""
    metadata = ExportMetadata(**sample_export_metadata)
    assert metadata.version == "1.0.0"
    assert metadata.type == "deal"
    assert isinstance(metadata.exported_by, UUID)


def test_export_metadata_invalid_version():
    """Test export metadata with invalid version."""
    with pytest.raises(ValidationError) as exc_info:
        ExportMetadata(
            version="2.0.0",
            exported_at=datetime.now(),
            type="deal"
        )
    assert "Export schema version must be 1.0.0" in str(exc_info.value)


def test_export_metadata_missing_required_fields():
    """Test export metadata with missing required fields."""
    with pytest.raises(ValidationError):
        ExportMetadata(version="1.0.0")


# ==================== Component Schema Tests ====================


def test_listing_link_valid():
    """Test valid listing link."""
    link = ListingLinkExport(url="https://example.com", label="Example")
    assert link.url == "https://example.com"
    assert link.label == "Example"


def test_listing_link_no_label():
    """Test listing link without label."""
    link = ListingLinkExport(url="https://example.com")
    assert link.url == "https://example.com"
    assert link.label is None


def test_cpu_export_valid(sample_cpu: dict):
    """Test valid CPU export."""
    cpu = CPUExport(**sample_cpu)
    assert cpu.name == "Intel Core i7-7700T"
    assert cpu.manufacturer == "Intel"
    assert cpu.cores == 4
    assert cpu.threads == 8


def test_ram_export_valid(sample_ram: dict):
    """Test valid RAM export."""
    ram = RAMExport(**sample_ram)
    assert ram.total_gb == 16
    assert ram.ddr_generation == RamGeneration.DDR4
    assert ram.speed_mhz == 2400


def test_storage_export_valid(sample_storage: dict):
    """Test valid storage export."""
    storage = StorageExport(**sample_storage)
    assert storage.capacity_gb == 512
    assert storage.medium == StorageMedium.NVME
    assert storage.interface == "PCIe 3.0 x4"


def test_port_export_valid():
    """Test valid port export."""
    port = PortExport(type=PortType.USB_A, count=4, spec_notes="USB 3.1")
    assert port.type == PortType.USB_A
    assert port.count == 4
    assert port.spec_notes == "USB 3.1"


def test_port_export_invalid_count():
    """Test port export with invalid count."""
    with pytest.raises(ValidationError):
        PortExport(type=PortType.USB_A, count=0)


def test_component_export_valid():
    """Test valid component export."""
    component = ComponentExport(
        component_type=ComponentType.WIFI,
        name="Intel AC 8265",
        quantity=1,
        metadata={"wifi_standard": "802.11ac"}
    )
    assert component.component_type == ComponentType.WIFI
    assert component.name == "Intel AC 8265"


# ==================== Listing Export Tests ====================


def test_listing_export_valid(sample_listing: dict):
    """Test valid listing export."""
    listing = ListingExport(**sample_listing)
    assert listing.id == 42
    assert listing.title == "Dell OptiPlex 7050 Micro"
    assert listing.price_usd == 299.99
    assert listing.condition == Condition.REFURB
    assert listing.status == ListingStatus.ACTIVE


def test_listing_export_minimal():
    """Test listing export with minimal required fields."""
    listing = ListingExport(
        id=1,
        title="Test Listing",
        price_usd=100.0,
        condition=Condition.USED,
        status=ListingStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert listing.id == 1
    assert listing.title == "Test Listing"
    assert listing.seller is None


def test_listing_export_invalid_price():
    """Test listing export with invalid price."""
    with pytest.raises(ValidationError):
        ListingExport(
            id=1,
            title="Test",
            price_usd=-10.0,  # Negative price
            condition=Condition.USED,
            status=ListingStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


# ==================== Deal Export Tests ====================


def test_deal_data_export_valid(sample_listing: dict):
    """Test valid deal data export."""
    deal = DealDataExport(
        listing=ListingExport(**sample_listing),
        valuation=ValuationExport(
            base_price_usd=299.99,
            adjusted_price_usd=289.99
        ),
        metadata=MetadataExport(
            manufacturer="Dell",
            series="OptiPlex"
        )
    )
    assert deal.listing.id == 42
    assert deal.valuation.base_price_usd == 299.99
    assert deal.metadata.manufacturer == "Dell"


def test_portable_deal_export_valid(sample_deal_export: dict):
    """Test valid portable deal export."""
    export = PortableDealExport(**sample_deal_export)
    assert export.deal_brain_export.version == "1.0.0"
    assert export.deal_brain_export.type == "deal"
    assert export.data.listing.id == 42


def test_portable_deal_export_invalid_type(sample_deal_export: dict):
    """Test portable deal export with wrong type."""
    sample_deal_export["deal_brain_export"]["type"] = "collection"
    with pytest.raises(ValidationError) as exc_info:
        PortableDealExport(**sample_deal_export)
    assert "Export type must be 'deal'" in str(exc_info.value)


# ==================== Collection Export Tests ====================


def test_collection_export_valid():
    """Test valid collection export."""
    collection = CollectionExport(
        id=15,
        name="Best Budget Builds",
        description="Curated collection",
        visibility=CollectionVisibility.PUBLIC,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert collection.id == 15
    assert collection.name == "Best Budget Builds"
    assert collection.visibility == CollectionVisibility.PUBLIC


def test_collection_item_export_valid(sample_listing: dict):
    """Test valid collection item export."""
    item = CollectionItemExport(
        listing=DealDataExport(listing=ListingExport(**sample_listing)),
        status=CollectionItemStatus.SHORTLISTED,
        notes="Top pick",
        position=1,
        added_at=datetime.now()
    )
    assert item.status == CollectionItemStatus.SHORTLISTED
    assert item.notes == "Top pick"
    assert item.position == 1


def test_portable_collection_export_valid(sample_listing: dict):
    """Test valid portable collection export."""
    export = PortableCollectionExport(
        deal_brain_export=ExportMetadata(
            version="1.0.0",
            exported_at=datetime.now(),
            type="collection"
        ),
        data=CollectionDataExport(
            collection=CollectionExport(
                id=15,
                name="Test Collection",
                visibility=CollectionVisibility.PRIVATE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            items=[
                CollectionItemExport(
                    listing=DealDataExport(listing=ListingExport(**sample_listing)),
                    status=CollectionItemStatus.UNDECIDED,
                    added_at=datetime.now()
                )
            ]
        )
    )
    assert export.deal_brain_export.type == "collection"
    assert export.data.collection.name == "Test Collection"
    assert len(export.data.items) == 1


# ==================== Sample File Validation Tests ====================


def test_sample_deal_export_file_valid():
    """Test that sample deal export file is valid."""
    sample_file = Path(__file__).parent.parent / "docs" / "schemas" / "examples" / "sample-deal-export-v1.0.0.json"

    if not sample_file.exists():
        pytest.skip("Sample file not found")

    with open(sample_file) as f:
        data = json.load(f)

    export = PortableDealExport(**data)
    assert export.deal_brain_export.version == "1.0.0"
    assert export.data.listing.title is not None


def test_sample_collection_export_file_valid():
    """Test that sample collection export file is valid."""
    sample_file = Path(__file__).parent.parent / "docs" / "schemas" / "examples" / "sample-collection-export-v1.0.0.json"

    if not sample_file.exists():
        pytest.skip("Sample file not found")

    with open(sample_file) as f:
        data = json.load(f)

    export = PortableCollectionExport(**data)
    assert export.deal_brain_export.version == "1.0.0"
    assert export.data.collection.name is not None
    assert len(export.data.items) > 0


# ==================== Generic Export Wrapper Tests ====================


def test_portable_export_parse_deal(sample_deal_export: dict):
    """Test generic export wrapper can parse deal exports."""
    export = PortableExport(**sample_deal_export)
    assert export.deal_brain_export.type == "deal"
    assert isinstance(export.data, DealDataExport)


def test_portable_export_parse_collection(sample_listing: dict):
    """Test generic export wrapper can parse collection exports."""
    collection_export = {
        "deal_brain_export": {
            "version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "type": "collection"
        },
        "data": {
            "collection": {
                "id": 1,
                "name": "Test",
                "visibility": "private",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            "items": []
        }
    }

    export = PortableExport(**collection_export)
    assert export.deal_brain_export.type == "collection"


# ==================== Backward Compatibility Tests ====================


def test_export_schema_version_locked():
    """Test that export schema version is locked to 1.0.0."""
    # This test documents the schema lock requirement
    # Future versions must be 1.1.0, 1.2.0, etc. with backward compatibility
    metadata = ExportMetadata(
        version="1.0.0",
        exported_at=datetime.now(),
        type="deal"
    )
    assert metadata.version == "1.0.0"

    # Version 2.0.0 should fail
    with pytest.raises(ValidationError):
        ExportMetadata(
            version="2.0.0",
            exported_at=datetime.now(),
            type="deal"
        )


def test_optional_fields_for_forward_compatibility():
    """Test that optional fields support forward compatibility."""
    # Future versions can add new optional fields without breaking v1.0.0
    listing = ListingExport(
        id=1,
        title="Test",
        price_usd=100.0,
        condition=Condition.USED,
        status=ListingStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        # All other fields are optional
    )
    assert listing.seller is None
    assert listing.notes is None
    assert listing.custom_fields == {}


# ==================== Edge Cases ====================


def test_performance_export_all_null():
    """Test performance export with all null values."""
    perf = PerformanceExport()
    assert perf.cpu is None
    assert perf.gpu is None
    assert perf.ram is None
    assert perf.components == []


def test_valuation_export_no_breakdown():
    """Test valuation export without breakdown."""
    val = ValuationExport(base_price_usd=299.99)
    assert val.base_price_usd == 299.99
    assert val.adjusted_price_usd is None
    assert val.valuation_breakdown is None


def test_ports_export_empty():
    """Test ports export with no ports."""
    ports = PortsExport(profile_name="Empty Profile")
    assert ports.profile_name == "Empty Profile"
    assert ports.ports == []


def test_custom_fields_complex_data():
    """Test custom fields with complex nested data."""
    listing = ListingExport(
        id=1,
        title="Test",
        price_usd=100.0,
        condition=Condition.USED,
        status=ListingStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        custom_fields={
            "warranty": {
                "months": 12,
                "provider": "Manufacturer",
                "coverage": ["parts", "labor"]
            },
            "ratings": [4.5, 4.8, 5.0],
            "verified": True
        }
    )
    assert "warranty" in listing.custom_fields
    assert listing.custom_fields["warranty"]["months"] == 12
    assert listing.custom_fields["verified"] is True
