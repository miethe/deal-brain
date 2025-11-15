"""SQLAlchemy models for Deal Brain.

This module provides backward-compatible imports after refactoring the monolithic
core.py into domain-focused modules. All models can be imported from this module
exactly as before the refactoring.

Module Structure:
- base.py: TimestampMixin and base utilities
- catalog.py: CPU, GPU, RAM, and Storage catalog models
- listings.py: Listing, Component, Score, and Profile models
- rules.py: Valuation rules system (Ruleset, RuleGroup, Rule, Condition, Action, etc.)
- ports.py: Ports and connectivity profile models
- imports.py: Import job and session tracking models
- settings.py: Application settings and custom field definitions
- metrics.py: Ingestion metrics and raw payload storage
"""

# Base utilities
from .base import TimestampMixin

# Catalog models
from .catalog import Cpu, Gpu, RamSpec, StorageProfile

# Ports models
from .ports import Port, PortsProfile

# Rules models
from .rules import (
    ValuationRuleAction,
    ValuationRuleAudit,
    ValuationRuleCondition,
    ValuationRuleGroup,
    ValuationRuleset,
    ValuationRuleV2,
    ValuationRuleVersion,
)

# Listing models
from .listings import Listing, ListingComponent, ListingScoreSnapshot, Profile

# Import models
from .imports import ImportJob, ImportSession, ImportSessionAudit, TaskRun

# Settings models
from .settings import (
    ApplicationSettings,
    CustomFieldAttributeHistory,
    CustomFieldAuditLog,
    CustomFieldDefinition,
)

# Metrics models
from .metrics import IngestionMetric, RawPayload

# Build models
from .builds import SavedBuild

# Legacy models (kept in separate files)
from .baseline_audit import BaselineAuditLog

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
    # Legacy
    "BaselineAuditLog",
]
