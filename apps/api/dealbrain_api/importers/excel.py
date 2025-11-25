"""Spreadsheet importer for Deal Brain seed data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition
from dealbrain_core.schemas import (
    CpuCreate,
    GpuCreate,
    ListingComponentCreate,
    ListingCreate,
    PortsProfileCreate,
    PortCreate,
    ProfileCreate,
    SpreadsheetSeed,
    ValuationRuleCreate,
)


@dataclass
class ImportSummary:
    cpus: int = 0
    gpus: int = 0
    valuation_rules: int = 0
    profiles: int = 0
    ports_profiles: int = 0
    listings: int = 0


class SpreadsheetImporter:
    """Parse the Excel workbook that backs the Deal Brain catalog."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> tuple[SpreadsheetSeed, ImportSummary]:
        if not self.path.exists():
            raise FileNotFoundError(self.path)

        workbook = pd.read_excel(self.path, sheet_name=None)

        seed = SpreadsheetSeed()

        if cpu_sheet := self._find_sheet(workbook, {"cpu", "cpus"}):
            seed.cpus = self._parse_cpus(workbook[cpu_sheet])

        if ref_sheet := self._find_sheet(workbook, {"reference", "valuation", "rules"}):
            rules, gpus = self._parse_reference(workbook[ref_sheet])
            seed.valuation_rules = rules
            seed.gpus.extend(gpus)

        if sff_sheet := self._find_sheet(workbook, {"sff pcs", "listings", "devices"}):
            listings = self._parse_listings(workbook[sff_sheet])
            seed.listings.extend(listings)

        if mac_sheet := self._find_sheet(workbook, {"macs", "macs 725"}):
            seed.listings.extend(self._parse_listings(workbook[mac_sheet], is_apple=True))

        seed.profiles = self._default_profiles()
        seed.ports_profiles = self._default_ports_profiles()

        summary = ImportSummary(
            cpus=len(seed.cpus),
            gpus=len(seed.gpus),
            valuation_rules=len(seed.valuation_rules),
            profiles=len(seed.profiles),
            ports_profiles=len(seed.ports_profiles),
            listings=len(seed.listings),
        )

        return seed, summary

    def _find_sheet(self, workbook: dict[str, pd.DataFrame], candidates: set[str]) -> str | None:
        lowered = {name.lower(): name for name in workbook.keys()}
        for candidate in candidates:
            if candidate in lowered:
                return lowered[candidate]
        return None

    def _parse_cpus(self, dataframe: pd.DataFrame) -> list[CpuCreate]:
        cpus: list[CpuCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = self._first_value(row, ["CPU", "Cpu", "Processor", "Name"])
            manufacturer = self._first_value(row, ["Manufacturer", "Maker", "Brand"]) or "Unknown"
            if not name:
                continue
            cpu = CpuCreate(
                name=str(name).strip(),
                manufacturer=str(manufacturer).strip(),
                socket=self._first_value(row, ["Socket"]),
                cores=self._to_int(self._first_value(row, ["Cores"])),
                threads=self._to_int(self._first_value(row, ["Threads"])),
                tdp_w=self._to_int(self._first_value(row, ["TDP", "TDP W", "TDP (W)"])),
                igpu_model=self._first_value(row, ["GPU", "iGPU", "Integrated GPU"]),
                cpu_mark_multi=self._to_int(
                    self._first_value(row, ["CPU Mark - Multi", "CPU Mark"])
                ),
                cpu_mark_single=self._to_int(
                    self._first_value(row, ["Single Thread", "CPU Mark - Single"])
                ),
                release_year=self._to_int(self._first_value(row, ["Release Year", "Year"])),
                notes=self._first_value(row, ["Notes"]),
            )
            cpus.append(cpu)
        return cpus

    def _parse_reference(
        self, dataframe: pd.DataFrame
    ) -> tuple[list[ValuationRuleCreate], list[GpuCreate]]:
        rules: list[ValuationRuleCreate] = []
        gpus: list[GpuCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            component_type = (
                (self._first_value(row, ["Component", "Component Type"]) or "").strip().lower()
            )
            if component_type in {"gpu", "graphics"}:
                gpu_name = self._first_value(row, ["GPU Model", "GPU"])
                if gpu_name:
                    gpus.append(
                        GpuCreate(
                            name=str(gpu_name).strip(),
                            manufacturer=self._infer_gpu_manufacturer(gpu_name),
                            gpu_mark=self._to_int(
                                self._first_value(row, ["GPU Mark Score", "GPU Mark"])
                            ),
                            metal_score=self._to_int(
                                self._first_value(row, ["Metal", "Metal Score"])
                            ),
                        )
                    )
                continue

            if not component_type:
                continue

            metric_value = (
                (self._first_value(row, ["Metric"]) or "per_gb")
                .replace("/", "_")
                .replace("-", "_")
                .lower()
            )
            metric = ComponentMetric.PER_GB if "gb" in metric_value else ComponentMetric.FLAT
            if "tb" in metric_value:
                metric = ComponentMetric.PER_TB

            rule = ValuationRuleCreate(
                name=self._first_value(row, ["Reference", "Name"]) or component_type.title(),
                component_type=(
                    ComponentType(component_type)
                    if component_type in ComponentType._value2member_map_
                    else ComponentType.MISC
                ),
                metric=metric,
                unit_value_usd=float(
                    self._first_value(
                        row, ["Unit cost (suggested)", "Adjustment Amount", "Unit Value"]
                    )
                    or 0.0
                ),
                condition_new=self._to_float(
                    self._first_value(row, ["Condition New", "Multiplier New"]) or 1.0
                )
                or 1.0,
                condition_refurb=self._to_float(
                    self._first_value(row, ["Condition Refurb", "Multiplier Refurb"]) or 0.75
                )
                or 0.75,
                condition_used=self._to_float(
                    self._first_value(row, ["Condition Used", "Multiplier Used"]) or 0.6
                )
                or 0.6,
                notes=self._first_value(row, ["Notes"]),
            )
            rules.append(rule)
        return rules, gpus

    def _parse_listings(
        self, dataframe: pd.DataFrame, *, is_apple: bool = False
    ) -> list[ListingCreate]:
        listings: list[ListingCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            title = self._first_value(row, ["Device", "Title", "Listing"])
            if not title:
                continue
            price_value = (
                self._to_float(self._first_value(row, ["Cost", "Price", "Listing Price"])) or 0.0
            )
            condition_value = (self._first_value(row, ["Condition"]) or "used").lower()
            condition = (
                Condition(condition_value)
                if condition_value in Condition._value2member_map_
                else Condition.USED
            )

            listing = ListingCreate(
                title=str(title).strip(),
                price_usd=price_value,
                condition=condition,
                cpu_id=None,
                gpu_id=None,
                ports_profile_id=None,
                ram_gb=self._to_int(self._first_value(row, ["Memory", "RAM"]) or 0) or 0,
                primary_storage_gb=self._normalize_storage(row),
                primary_storage_type=self._first_value(
                    row, ["Storage 1 Type", "Storage Type", "Primary Storage Type"]
                ),
                secondary_storage_gb=self._to_int(
                    self._first_value(row, ["Storage 2", "Storage Secondary"])
                ),
                secondary_storage_type=self._first_value(row, ["Storage 2 Type"]),
                os_license=self._first_value(row, ["OS", "OS License"]),
                notes=self._first_value(row, ["Notes"]),
            )

            components: list[ListingComponentCreate] = []
            gpu_name = self._first_value(row, ["GPU", "GPU Model"])
            if gpu_name:
                components.append(
                    ListingComponentCreate(
                        component_type=ComponentType.GPU,
                        name=gpu_name,
                        metadata_json={
                            "gpu_mark": self._to_int(self._first_value(row, ["GPU Mark"]))
                        },
                    )
                )

            listing.components = components or None
            listings.append(listing)
        return listings

    def _normalize_storage(self, row: dict[str, Any]) -> int:
        raw = self._first_value(row, ["Storage", "Storage 1", "SSD", "Primary Storage"])
        if not raw:
            return 0
        text = str(raw).lower().replace("tb", "000").replace("gb", "").split()[0]
        try:
            return int(float(text))
        except ValueError:
            return 0

    def _default_profiles(self) -> list[ProfileCreate]:
        return [
            ProfileCreate(
                name="Proxmox",
                description="Heavy virtualization workloads",
                weights_json={
                    "cpu_mark_multi": 0.5,
                    "ram_capacity": 0.2,
                    "expandability": 0.2,
                    "perf_per_watt": 0.1,
                },
                is_default=True,
            ),
            ProfileCreate(
                name="Plex",
                description="Media server and transcoding",
                weights_json={
                    "cpu_mark_single": 0.4,
                    "encoder_capability": 0.4,
                    "perf_per_watt": 0.2,
                },
            ),
        ]

    def _default_ports_profiles(self) -> list[PortsProfileCreate]:
        return [
            PortsProfileCreate(
                name="Baseline SFF",
                description="Default configuration with typical SFF connectivity",
                ports=[
                    PortCreate(type="usb_a", count=4),
                    PortCreate(type="usb_c", count=2),
                    PortCreate(type="rj45_2_5g", count=1),
                    PortCreate(type="hdmi", count=1),
                ],
            )
        ]

    def _first_value(self, row: dict[str, Any], keys: list[str]) -> Any:
        for key in keys:
            if key in row and row[key] not in ("", None):
                return row[key]
            alias = self._match_key(row, key)
            if alias and row[alias] not in ("", None):
                return row[alias]
        return None

    def _match_key(self, row: dict[str, Any], key: str) -> str | None:
        lowered = {k.lower(): k for k in row.keys()}
        return lowered.get(key.lower())

    def _to_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _to_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _infer_gpu_manufacturer(self, name: Any) -> str:
        text = str(name).lower()
        if any(keyword in text for keyword in ("nvidia", "rtx", "gtx", "quadro")):
            return "NVIDIA"
        if any(keyword in text for keyword in ("radeon", "rx", "vega")):
            return "AMD"
        if "apple" in text or text.startswith("m"):
            return "Apple"
        return "Unknown"


__all__ = ["SpreadsheetImporter", "ImportSummary"]
