"""Seed builders for converting spreadsheet data to domain schemas."""

from __future__ import annotations

import json
from typing import Any, Mapping

from pandas import DataFrame

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition
from dealbrain_core.schemas import (
    CpuCreate,
    GpuCreate,
    ListingComponentCreate,
    ListingCreate,
    PortCreate,
    PortsProfileCreate,
    ProfileCreate,
    SpreadsheetSeed,
    ValuationRuleCreate,
)

from .utils import normalize_text


class SeedBuilder:
    """Builds domain schema objects from mapped spreadsheet data."""

    @staticmethod
    def build_seed(
        workbook: Mapping[str, DataFrame],
        mappings: Mapping[str, Any],
        *,
        conflict_resolutions: Mapping[str, str],
        component_overrides: Mapping[int, dict[str, Any]],
        cpu_lookup: Mapping[str, int],
        gpu_lookup: Mapping[str, int],
    ) -> SpreadsheetSeed:
        """
        Build a complete SpreadsheetSeed from workbook data.

        Args:
            workbook: Dictionary of sheet DataFrames
            mappings: Field mapping configuration
            conflict_resolutions: User conflict resolutions
            component_overrides: Component assignment overrides
            cpu_lookup: CPU name -> ID lookup
            gpu_lookup: GPU name -> ID lookup

        Returns:
            Complete SpreadsheetSeed ready for import
        """
        seed = SpreadsheetSeed()

        # Build CPUs
        cpu_mapping = mappings.get("cpu") if mappings else None
        if cpu_mapping:
            dataframe = workbook.get(cpu_mapping.get("sheet"))
            if dataframe is not None:
                seed.cpus = SeedBuilder.build_cpus(dataframe, cpu_mapping.get("fields", {}), conflict_resolutions)

        # Build GPUs
        gpu_mapping = mappings.get("gpu") if mappings else None
        if gpu_mapping:
            dataframe = workbook.get(gpu_mapping.get("sheet"))
            if dataframe is not None:
                seed.gpus = SeedBuilder.build_gpus(dataframe, gpu_mapping.get("fields", {}))

        # Build valuation rules
        rules_mapping = mappings.get("valuation_rule") if mappings else None
        if rules_mapping:
            dataframe = workbook.get(rules_mapping.get("sheet"))
            if dataframe is not None:
                seed.valuation_rules = SeedBuilder.build_rules(dataframe, rules_mapping.get("fields", {}))

        # Build ports profiles
        ports_mapping = mappings.get("ports_profile") if mappings else None
        if ports_mapping:
            dataframe = workbook.get(ports_mapping.get("sheet"))
            if dataframe is not None:
                seed.ports_profiles = SeedBuilder.build_ports_profiles(dataframe, ports_mapping.get("fields", {}))

        # Build listings
        listing_mapping = mappings.get("listing") if mappings else None
        if listing_mapping:
            dataframe = workbook.get(listing_mapping.get("sheet"))
            if dataframe is not None:
                seed.listings = SeedBuilder.build_listings(
                    dataframe,
                    listing_mapping.get("fields", {}),
                    component_overrides=component_overrides,
                    cpu_lookup=cpu_lookup,
                    gpu_lookup=gpu_lookup,
                )

        # Add defaults if not present
        if not seed.profiles:
            seed.profiles = SeedBuilder.default_profiles()
        if not seed.ports_profiles:
            seed.ports_profiles = SeedBuilder.default_ports_profiles()

        return seed

    @staticmethod
    def build_cpus(
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
        conflict_resolutions: Mapping[str, str],
    ) -> list[CpuCreate]:
        """
        Build CPU schema objects from a DataFrame.

        Args:
            dataframe: Source DataFrame
            field_mappings: Field mapping configuration
            conflict_resolutions: User conflict resolutions

        Returns:
            List of CpuCreate schemas
        """
        name_column = field_mappings.get("name", {}).get("column")
        if not name_column or name_column not in dataframe.columns:
            return []

        cpus: list[CpuCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = ValueExtractor.to_str(row.get(name_column))
            if not name:
                continue

            action = conflict_resolutions.get(name)
            if action in {"skip", "keep"}:
                continue

            cpu = CpuCreate(
                name=name,
                manufacturer=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "manufacturer")) or "Unknown",
                socket=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "socket")),
                cores=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "cores")),
                threads=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "threads")),
                tdp_w=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "tdp_w")),
                igpu_model=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "igpu_model")),
                cpu_mark_multi=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "cpu_mark_multi")),
                cpu_mark_single=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "cpu_mark_single")),
                release_year=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "release_year")),
                notes=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "notes")),
            )
            cpus.append(cpu)

        return cpus

    @staticmethod
    def build_gpus(
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
    ) -> list[GpuCreate]:
        """
        Build GPU schema objects from a DataFrame.

        Args:
            dataframe: Source DataFrame
            field_mappings: Field mapping configuration

        Returns:
            List of GpuCreate schemas
        """
        name_column = field_mappings.get("name", {}).get("column")
        if not name_column or name_column not in dataframe.columns:
            return []

        gpus: list[GpuCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = ValueExtractor.to_str(row.get(name_column))
            if not name:
                continue

            gpu = GpuCreate(
                name=name,
                manufacturer=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "manufacturer")) or "Unknown",
                gpu_mark=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "gpu_mark")),
                metal_score=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "metal_score")),
                notes=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "notes")),
            )
            gpus.append(gpu)

        return gpus

    @staticmethod
    def build_rules(
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
    ) -> list[ValuationRuleCreate]:
        """
        Build valuation rule schema objects from a DataFrame.

        Args:
            dataframe: Source DataFrame
            field_mappings: Field mapping configuration

        Returns:
            List of ValuationRuleCreate schemas
        """
        name_column = field_mappings.get("name", {}).get("column")
        component_column = field_mappings.get("component_type", {}).get("column")
        unit_value_column = field_mappings.get("unit_value_usd", {}).get("column")

        if not name_column or not component_column or not unit_value_column:
            return []

        rules: list[ValuationRuleCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = ValueExtractor.to_str(row.get(name_column))
            component_value = ValueExtractor.to_str(row.get(component_column))
            unit_value = ValueExtractor.to_float(row.get(unit_value_column))

            if not name or not component_value or unit_value is None:
                continue

            rules.append(
                ValuationRuleCreate(
                    name=name,
                    component_type=ValueParser.parse_component_type(component_value),
                    metric=ValueParser.parse_metric(ValueExtractor.extract_value(row, field_mappings, "metric")),
                    unit_value_usd=unit_value,
                    condition_new=ValueExtractor.to_float(ValueExtractor.extract_value(row, field_mappings, "condition_new")) or 1.0,
                    condition_refurb=ValueExtractor.to_float(ValueExtractor.extract_value(row, field_mappings, "condition_refurb")) or 0.75,
                    condition_used=ValueExtractor.to_float(ValueExtractor.extract_value(row, field_mappings, "condition_used")) or 0.6,
                    notes=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "notes")),
                )
            )

        return rules

    @staticmethod
    def build_ports_profiles(
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
    ) -> list[PortsProfileCreate]:
        """
        Build ports profile schema objects from a DataFrame.

        Args:
            dataframe: Source DataFrame
            field_mappings: Field mapping configuration

        Returns:
            List of PortsProfileCreate schemas
        """
        name_column = field_mappings.get("name", {}).get("column")
        if not name_column or name_column not in dataframe.columns:
            return []

        profiles: list[PortsProfileCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = ValueExtractor.to_str(row.get(name_column))
            if not name:
                continue

            profiles.append(
                PortsProfileCreate(
                    name=name,
                    description=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "description")),
                    ports=ValueParser.parse_ports_blob(ValueExtractor.extract_value(row, field_mappings, "ports")) or None,
                )
            )

        return profiles

    @staticmethod
    def build_listings(
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
        *,
        component_overrides: Mapping[int, dict[str, Any]],
        cpu_lookup: Mapping[str, int],
        gpu_lookup: Mapping[str, int],
    ) -> list[ListingCreate]:
        """
        Build listing schema objects from a DataFrame.

        Args:
            dataframe: Source DataFrame
            field_mappings: Field mapping configuration
            component_overrides: Component assignment overrides
            cpu_lookup: CPU name -> ID lookup
            gpu_lookup: GPU name -> ID lookup

        Returns:
            List of ListingCreate schemas
        """
        from .cpu_matcher import CpuMatcher

        title_column = field_mappings.get("title", {}).get("column")
        price_column = field_mappings.get("price_usd", {}).get("column")
        if not title_column or title_column not in dataframe.columns:
            return []

        cpu_column = field_mappings.get("cpu_name", {}).get("column")
        match_lookup: dict[int, dict[str, Any]] = {}
        if cpu_column:
            matches = CpuMatcher.match_components(dataframe, cpu_column, list(cpu_lookup.keys()), limit=None)
            match_lookup = {match["row_index"]: match for match in matches}

        listings: list[ListingCreate] = []
        records = dataframe.fillna("").to_dict(orient="records")

        for index, row in enumerate(records):
            title = ValueExtractor.to_str(row.get(title_column))
            if not title:
                continue

            price_value = ValueExtractor.to_float(row.get(price_column)) or 0.0
            condition_value = ValueParser.parse_condition(ValueExtractor.extract_value(row, field_mappings, "condition"))

            override = component_overrides.get(index, {})
            match_data = match_lookup.get(index)
            cpu_assignment = CpuMatcher.resolve_cpu_assignment(override, match_data)
            cpu_id = cpu_lookup.get(normalize_text(cpu_assignment)) if cpu_assignment else None

            gpu_assignment = ValueExtractor.to_str(
                override.get("gpu_match") if override else ValueExtractor.extract_value(row, field_mappings, "gpu_name")
            )
            gpu_id = gpu_lookup.get(normalize_text(gpu_assignment)) if gpu_assignment else None

            listing = ListingCreate(
                title=title,
                price_usd=price_value,
                condition=condition_value,
                cpu_id=cpu_id,
                gpu_id=gpu_id,
                ports_profile_id=None,
                ram_gb=ValueExtractor.to_int(ValueExtractor.extract_value(row, field_mappings, "ram_gb")) or 0,
                ram_notes=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "ram_notes")),
                primary_storage_gb=ValueParser.parse_storage_capacity(ValueExtractor.extract_value(row, field_mappings, "primary_storage_gb")),
                primary_storage_type=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "primary_storage_type")),
                secondary_storage_gb=ValueParser.parse_storage_capacity(ValueExtractor.extract_value(row, field_mappings, "secondary_storage_gb")) or None,
                secondary_storage_type=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "secondary_storage_type")),
                os_license=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "os_license")),
                notes=ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "notes")),
                components=None,
            )

            components: list[ListingComponentCreate] = []
            gpu_name_raw = ValueExtractor.to_str(ValueExtractor.extract_value(row, field_mappings, "gpu_name"))
            if gpu_name_raw and not gpu_id:
                components.append(
                    ListingComponentCreate(
                        component_type=ComponentType.GPU,
                        name=gpu_name_raw,
                        metadata_json=None,
                    )
                )

            listing.components = components or None
            listings.append(listing)

        return listings

    @staticmethod
    def default_profiles() -> list[ProfileCreate]:
        """Generate default scoring profiles."""
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

    @staticmethod
    def default_ports_profiles() -> list[PortsProfileCreate]:
        """Generate default ports profiles."""
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


class ValueExtractor:
    """Utilities for extracting and converting values from spreadsheet rows."""

    @staticmethod
    def extract_value(
        row: Mapping[str, Any],
        field_mappings: Mapping[str, Any],
        key: str,
    ) -> Any:
        """
        Extract a value from a row using field mappings.

        Args:
            row: DataFrame row dictionary
            field_mappings: Field mapping configuration
            key: Field key to extract

        Returns:
            Raw value from the row
        """
        mapping = field_mappings.get(key, {})
        column = mapping.get("column")
        if not column:
            return None
        value = row.get(column)
        if value == "":
            return None
        return value

    @staticmethod
    def to_str(value: Any) -> str | None:
        """Convert value to string or None."""
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def to_int(value: Any) -> int | None:
        """Convert value to integer or None."""
        float_value = ValueExtractor.to_float(value)
        if float_value is None:
            return None
        try:
            return int(round(float_value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def to_float(value: Any) -> float | None:
        """Convert value to float or None."""
        if value is None:
            return None
        text = str(value).strip().replace("$", "").replace(",", "")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None


class ValueParser:
    """Utilities for parsing domain-specific values."""

    @staticmethod
    def parse_condition(value: Any) -> Condition:
        """Parse condition enum from string value."""
        text = ValueExtractor.to_str(value)
        if not text:
            return Condition.USED
        normalized = text.lower().strip()
        if normalized in Condition._value2member_map_:
            return Condition(normalized)
        aliases = {
            "refurbished": Condition.REFURB,
            "refurb": Condition.REFURB,
            "new": Condition.NEW,
            "used": Condition.USED,
        }
        return aliases.get(normalized, Condition.USED)

    @staticmethod
    def parse_component_type(value: Any) -> ComponentType:
        """Parse component type enum from string value."""
        text = normalize_text(str(value))
        mapping = {
            "memory": ComponentType.RAM,
            "ram": ComponentType.RAM,
            "ssd": ComponentType.SSD,
            "hdd": ComponentType.HDD,
            "storage": ComponentType.SSD,
            "os": ComponentType.OS_LICENSE,
            "os license": ComponentType.OS_LICENSE,
            "wifi": ComponentType.WIFI,
            "gpu": ComponentType.GPU,
        }
        if text in mapping:
            return mapping[text]
        if text in ComponentType._value2member_map_:
            return ComponentType(text)
        return ComponentType.MISC

    @staticmethod
    def parse_metric(value: Any) -> ComponentMetric:
        """Parse component metric enum from string value."""
        text = ValueExtractor.to_str(value)
        if not text:
            return ComponentMetric.FLAT
        normalized = normalize_text(text)
        if "tb" in normalized:
            return ComponentMetric.PER_TB
        if "gb" in normalized:
            return ComponentMetric.PER_GB
        if normalized in ComponentMetric._value2member_map_:
            return ComponentMetric(normalized)
        return ComponentMetric.FLAT

    @staticmethod
    def parse_storage_capacity(value: Any) -> int:
        """Parse storage capacity from various string formats."""
        text = ValueExtractor.to_str(value)
        if not text:
            return 0
        lowered = text.lower().replace("tb", "000").replace("gb", "").strip()
        parts = lowered.split()
        candidate = parts[0] if parts else lowered
        try:
            return int(float(candidate))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def parse_ports_blob(value: Any) -> list[PortCreate]:
        """Parse JSON ports blob into PortCreate schemas."""
        text = ValueExtractor.to_str(value)
        if not text:
            return []
        try:
            data = json.loads(text)
            ports: list[PortCreate] = []
            if isinstance(data, list):
                for entry in data:
                    if not isinstance(entry, dict):
                        continue
                    port_type = entry.get("type")
                    if not port_type:
                        continue
                    ports.append(
                        PortCreate(
                            type=str(port_type),
                            count=int(entry.get("count") or 1),
                            spec_notes=ValueExtractor.to_str(entry.get("spec_notes")),
                        )
                    )
            return ports
        except (ValueError, TypeError):
            return []


__all__ = ["SeedBuilder", "ValueExtractor", "ValueParser"]
