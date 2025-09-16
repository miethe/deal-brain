"""Shared enumerations for Deal Brain domain objects."""

from __future__ import annotations

from enum import Enum


class Condition(str, Enum):
    NEW = "new"
    REFURB = "refurb"
    USED = "used"


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


__all__ = [
    "Condition",
    "ComponentType",
    "ComponentMetric",
    "ListingStatus",
    "PortType",
]

