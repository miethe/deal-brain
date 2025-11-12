"""
Rules API Router Aggregation

This module aggregates all rules-related routers into a single main router
to maintain backward compatibility with existing API paths.

Architecture Decision:
- Split large monolithic rules.py (1066 LOC) into focused modules by responsibility
- Each module handles a specific domain: rulesets, groups, rules, evaluation, packaging
- All routers are included in the main router with the same prefix (/api/v1)
- This preserves all existing endpoint paths for backward compatibility
- Reduces cognitive load and improves maintainability
"""

from fastapi import APIRouter

from . import rulesets, rule_groups, valuation_rules, evaluation, packaging


# Create main aggregated router with same prefix as original
router = APIRouter(prefix="/api/v1", tags=["rules"])

# Include all sub-routers
# Note: No additional prefix needed as each endpoint already has its full path
router.include_router(rulesets.router)
router.include_router(rule_groups.router)
router.include_router(valuation_rules.router)
router.include_router(evaluation.router)
router.include_router(packaging.router)

# Export the main router for use in the main API
__all__ = ["router"]
