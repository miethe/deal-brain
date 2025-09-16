"""Schemas used for spreadsheet import/export."""

from __future__ import annotations

from typing import List

from pydantic import Field

from .base import DealBrainModel
from .catalog import CpuCreate, GpuCreate, PortsProfileCreate, ProfileCreate, ValuationRuleCreate
from .listing import ListingCreate


class SpreadsheetSeed(DealBrainModel):
    cpus: List[CpuCreate] = Field(default_factory=list)
    gpus: List[GpuCreate] = Field(default_factory=list)
    valuation_rules: List[ValuationRuleCreate] = Field(default_factory=list)
    profiles: List[ProfileCreate] = Field(default_factory=list)
    ports_profiles: List[PortsProfileCreate] = Field(default_factory=list)
    listings: List[ListingCreate] = Field(default_factory=list)


__all__ = ["SpreadsheetSeed"]
