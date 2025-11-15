"""Backward compatibility shim for models.core module.

This module has been refactored into domain-focused modules for better organization.
All models are re-exported here to maintain backward compatibility with existing code.

New structure:
- base.py: TimestampMixin and base utilities
- catalog.py: CPU, GPU, RAM, and Storage catalog models
- listings.py: Listing, Component, Score, and Profile models
- rules.py: Valuation rules system
- ports.py: Ports and connectivity profile models
- imports.py: Import job and session tracking models
- settings.py: Application settings and custom field definitions
- metrics.py: Ingestion metrics and raw payload storage

Deprecated: Import directly from dealbrain_api.models instead of models.core
"""

# Re-export all models for backward compatibility
from .base import TimestampMixin
from .builds import SavedBuild
from .catalog import Cpu, Gpu, RamSpec, StorageProfile
from .imports import ImportJob, ImportSession, ImportSessionAudit, TaskRun
from .listings import Listing, ListingComponent, ListingScoreSnapshot, Profile
from .metrics import IngestionMetric, RawPayload
from .ports import Port, PortsProfile
from .rules import (
    ValuationRuleAction,
    ValuationRuleAudit,
    ValuationRuleCondition,
    ValuationRuleGroup,
    ValuationRuleset,
    ValuationRuleV2,
    ValuationRuleVersion,
)
from .settings import (
    ApplicationSettings,
    CustomFieldAttributeHistory,
    CustomFieldAuditLog,
    CustomFieldDefinition,
)

__all__ = [
    # Base
    "TimestampMixin",
    # Catalog
    "Cpu",
    "Gpu",
    "RamSpec",
    "StorageProfile",
    # Ports
    "Port",
    "PortsProfile",
    # Rules
    "ValuationRuleAction",
    "ValuationRuleAudit",
    "ValuationRuleCondition",
    "ValuationRuleGroup",
    "ValuationRuleset",
    "ValuationRuleV2",
    "ValuationRuleVersion",
    # Listings
    "Listing",
    "ListingComponent",
    "ListingScoreSnapshot",
    "Profile",
    # Imports
    "ImportJob",
    "ImportSession",
    "ImportSessionAudit",
    "TaskRun",
    # Settings
    "ApplicationSettings",
    "CustomFieldAttributeHistory",
    "CustomFieldAuditLog",
    "CustomFieldDefinition",
    # Metrics
    "IngestionMetric",
    "RawPayload",
    # Builds
    "SavedBuild",
]
