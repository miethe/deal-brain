"""Shared enumerations for Deal Brain domain objects."""

from __future__ import annotations

from enum import Enum


class Condition(str, Enum):
    NEW = "new"
    REFURB = "refurb"
    USED = "used"


class RamGeneration(str, Enum):
    DDR3 = "ddr3"
    DDR4 = "ddr4"
    DDR5 = "ddr5"
    LPDDR4 = "lpddr4"
    LPDDR4X = "lpddr4x"
    LPDDR5 = "lpddr5"
    LPDDR5X = "lpddr5x"
    HBM2 = "hbm2"
    HBM3 = "hbm3"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    RAM = "ram"
    SSD = "ssd"
    HDD = "hdd"
    OS_LICENSE = "os_license"
    WIFI = "wifi"
    GPU = "gpu"
    MISC = "misc"


class ComponentMetric(str, Enum):
    PER_GB = "per_gb"
    PER_TB = "per_tb"
    FLAT = "flat"
    PER_RAM_SPEC_GB = "per_ram_spec_gb"
    PER_RAM_SPEED = "per_ram_speed"
    PER_PRIMARY_STORAGE_GB = "per_primary_storage_gb"
    PER_SECONDARY_STORAGE_GB = "per_secondary_storage_gb"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING = "pending"


class PortType(str, Enum):
    USB_A = "usb_a"
    USB_C = "usb_c"
    THUNDERBOLT = "thunderbolt"
    HDMI = "hdmi"
    DISPLAYPORT = "displayport"
    RJ45_1G = "rj45_1g"
    RJ45_2_5G = "rj45_2_5g"
    RJ45_10G = "rj45_10g"
    AUDIO = "audio"
    SDXC = "sdxc"
    PCIE_X16 = "pcie_x16"
    PCIE_X8 = "pcie_x8"
    M2_SLOT = "m2_slot"
    SATA_BAY = "sata_bay"
    OTHER = "other"


class StorageMedium(str, Enum):
    NVME = "nvme"
    SATA_SSD = "sata_ssd"
    HDD = "hdd"
    HYBRID = "hybrid"
    EMMC = "emmc"
    UFS = "ufs"
    UNKNOWN = "unknown"


class Marketplace(str, Enum):
    """Source marketplace for URL-ingested listings."""
    EBAY = "ebay"
    AMAZON = "amazon"
    OTHER = "other"


class SourceType(str, Enum):
    """Type of import source for ImportSession."""
    EXCEL = "excel"
    URL_SINGLE = "url_single"
    URL_BULK = "url_bulk"


class SourceDataType(str, Enum):
    """Type of raw payload data stored."""
    JSON = "json"
    HTML = "html"


__all__ = [
    "Condition",
    "RamGeneration",
    "ComponentType",
    "ComponentMetric",
    "ListingStatus",
    "PortType",
    "StorageMedium",
    "Marketplace",
    "SourceType",
    "SourceDataType",
]
