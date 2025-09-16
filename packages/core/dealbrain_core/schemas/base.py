"""Shared base schema definitions."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DealBrainModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


__all__ = ["DealBrainModel"]
