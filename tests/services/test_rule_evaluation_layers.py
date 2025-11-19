"""
Unit tests for multi-layer rule evaluation logic.

Tests the RuleEvaluationService's ability to evaluate multiple rulesets
in priority order without requiring database access.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from dealbrain_api.services.rule_evaluation import RuleEvaluationService
from dealbrain_api.models.core import ValuationRuleset, Listing


class TestLayerTypeDetection:
    """Test layer type detection based on ruleset metadata and priority."""

    def test_detects_baseline_via_metadata(self):
        """Test that system_baseline metadata flag identifies baseline layer."""
        service = RuleEvaluationService()

        ruleset = ValuationRuleset(
            name="System: Baseline v1.0",
            priority=10,  # Higher priority but metadata marks it as baseline
            metadata_json={"system_baseline": True},
        )

        assert service._get_layer_type(ruleset) == "baseline"

    def test_detects_baseline_via_priority(self):
        """Test that priority <= 5 identifies baseline layer."""
        service = RuleEvaluationService()

        ruleset = ValuationRuleset(
            name="Low Priority Ruleset",
            priority=5,
            metadata_json={},
        )

        assert service._get_layer_type(ruleset) == "baseline"

    def test_detects_basic_layer(self):
        """Test that priority 6-10 identifies basic layer."""
        service = RuleEvaluationService()

        ruleset = ValuationRuleset(
            name="Standard Ruleset",
            priority=10,
            metadata_json={},
        )

        assert service._get_layer_type(ruleset) == "basic"

    def test_detects_advanced_layer(self):
        """Test that priority > 10 identifies advanced layer."""
        service = RuleEvaluationService()

        ruleset = ValuationRuleset(
            name="Advanced Ruleset",
            priority=20,
            metadata_json={},
        )

        assert service._get_layer_type(ruleset) == "advanced"


class TestMatchedRulesFlattening:
    """Test the flattening of matched rules for backward compatibility."""

    def test_flattens_rules_with_layer_attribution(self):
        """Test that matched rules are properly flattened with layer info."""
        service = RuleEvaluationService()

        matched_by_layer = {
            "baseline": {
                "ruleset_id": 1,
                "ruleset_name": "System: Baseline v1.0",
                "priority": 5,
                "adjustment": 50.0,
                "matched_rules": [
                    {
                        "rule_id": 101,
                        "rule_name": "Baseline RAM",
                        "adjustment": 50.0,
                        "breakdown": [],
                    }
                ],
            },
            "basic": {
                "ruleset_id": 2,
                "ruleset_name": "Standard Valuation",
                "priority": 10,
                "adjustment": 25.0,
                "matched_rules": [
                    {
                        "rule_id": 201,
                        "rule_name": "Standard RAM",
                        "adjustment": 25.0,
                        "breakdown": [],
                    }
                ],
            },
        }

        flattened = service._flatten_matched_rules(matched_by_layer)

        assert len(flattened) == 2

        # Check first rule (baseline)
        assert flattened[0]["rule_id"] == 101
        assert flattened[0]["layer"] == "baseline"
        assert flattened[0]["ruleset_id"] == 1
        assert flattened[0]["ruleset_name"] == "System: Baseline v1.0"

        # Check second rule (basic)
        assert flattened[1]["rule_id"] == 201
        assert flattened[1]["layer"] == "basic"
        assert flattened[1]["ruleset_id"] == 2
        assert flattened[1]["ruleset_name"] == "Standard Valuation"

    def test_handles_empty_layers(self):
        """Test that empty layers are handled correctly."""
        service = RuleEvaluationService()

        matched_by_layer = {}
        flattened = service._flatten_matched_rules(matched_by_layer)

        assert flattened == []


class TestMultiRulesetEvaluation:
    """Test multi-ruleset evaluation logic with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_get_rulesets_for_evaluation_ordering(self):
        """Test that rulesets are returned in priority order."""
        service = RuleEvaluationService()

        # Mock rulesets with different priorities
        baseline = MagicMock(spec=ValuationRuleset)
        baseline.id = 1
        baseline.priority = 5
        baseline.is_active = True
        baseline.conditions_json = None
        baseline.created_at = datetime.now()

        standard = MagicMock(spec=ValuationRuleset)
        standard.id = 2
        standard.priority = 10
        standard.is_active = True
        standard.conditions_json = None
        standard.created_at = datetime.now()

        advanced = MagicMock(spec=ValuationRuleset)
        advanced.id = 3
        advanced.priority = 20
        advanced.is_active = True
        advanced.conditions_json = None
        advanced.created_at = datetime.now()

        # Mock database query - note: ORDER BY happens at SQL level,
        # so mock should return already-ordered results
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            baseline,
            standard,
            advanced,
        ]  # Correct order from SQL
        mock_session.execute.return_value = mock_result

        # Call the method
        rulesets = await service._get_rulesets_for_evaluation(mock_session, {}, set())

        # Verify rulesets are returned in the order from SQL
        assert len(rulesets) == 3
        assert rulesets[0].priority == 5  # Baseline first
        assert rulesets[1].priority == 10  # Standard second
        assert rulesets[2].priority == 20  # Advanced third

    @pytest.mark.asyncio
    async def test_excludes_disabled_rulesets(self):
        """Test that excluded rulesets are filtered out."""
        service = RuleEvaluationService()

        # Mock rulesets
        ruleset1 = MagicMock(spec=ValuationRuleset)
        ruleset1.id = 1
        ruleset1.priority = 5
        ruleset1.is_active = True
        ruleset1.conditions_json = None

        ruleset2 = MagicMock(spec=ValuationRuleset)
        ruleset2.id = 2
        ruleset2.priority = 10
        ruleset2.is_active = True
        ruleset2.conditions_json = None

        # Mock database query
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [ruleset1, ruleset2]
        mock_session.execute.return_value = mock_result

        # Call with ruleset2 excluded
        rulesets = await service._get_rulesets_for_evaluation(
            mock_session, {}, {2}  # Exclude ruleset 2
        )

        # Verify only ruleset1 is returned
        assert len(rulesets) == 1
        assert rulesets[0].id == 1

    @pytest.mark.asyncio
    async def test_filters_conditional_rulesets(self):
        """Test that conditional rulesets are filtered based on context."""
        service = RuleEvaluationService()

        # Mock ruleset with conditions
        conditional_ruleset = MagicMock(spec=ValuationRuleset)
        conditional_ruleset.id = 1
        conditional_ruleset.priority = 10
        conditional_ruleset.is_active = True
        conditional_ruleset.conditions_json = {
            "field_name": "ram_gb",
            "operator": ">=",
            "value": 64,
        }

        # Mock database query
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [conditional_ruleset]
        mock_session.execute.return_value = mock_result

        # Test with context that doesn't match (32GB RAM)
        with patch.object(service, "_ruleset_matches_context", return_value=False):
            rulesets = await service._get_rulesets_for_evaluation(
                mock_session, {"ram_gb": 32}, set()
            )
            assert len(rulesets) == 0

        # Test with context that matches (64GB RAM)
        with patch.object(service, "_ruleset_matches_context", return_value=True):
            rulesets = await service._get_rulesets_for_evaluation(
                mock_session, {"ram_gb": 64}, set()
            )
            assert len(rulesets) == 1
            assert rulesets[0].id == 1


class TestBackwardCompatibility:
    """Test that the enhanced evaluation maintains backward compatibility."""

    @pytest.mark.asyncio
    async def test_single_ruleset_mode_compatibility(self):
        """Test that specifying a ruleset_id evaluates only that ruleset."""
        service = RuleEvaluationService()

        # Mock listing
        mock_listing = MagicMock(spec=Listing)
        mock_listing.id = 1
        mock_listing.price_usd = Decimal("1000.00")
        mock_listing.attributes_json = {}
        mock_listing.cpu = None
        mock_listing.gpu = None
        mock_listing.ram_spec = None
        mock_listing.primary_storage_profile = None
        mock_listing.secondary_storage_profile = None

        # Mock session
        mock_session = AsyncMock()

        # Mock listing query
        listing_result = MagicMock()
        listing_result.scalar_one_or_none.return_value = mock_listing

        # Mock ruleset query
        mock_ruleset = MagicMock(spec=ValuationRuleset)
        mock_ruleset.id = 99
        mock_ruleset.name = "Specific Ruleset"
        mock_ruleset.priority = 10
        mock_ruleset.metadata_json = {}

        # Setup session execute to return different results based on query
        async def mock_execute(stmt):
            stmt_str = str(stmt)
            if "listing" in stmt_str.lower():
                return listing_result
            else:
                # Ruleset query
                result = MagicMock()
                result.scalar_one_or_none.return_value = mock_ruleset
                return result

        mock_session.execute = mock_execute

        # Mock rule fetching and evaluation
        with patch.object(service, "_get_rules_from_ruleset", return_value=[]):
            with patch.object(service.evaluator, "evaluate_ruleset", return_value=[]):
                with patch.object(
                    service.evaluator,
                    "calculate_total_adjustment",
                    return_value={"total_adjustment": 0, "matched_rules": []},
                ):

                    result = await service.evaluate_listing(
                        mock_session, listing_id=1, ruleset_id=99  # Specific ruleset
                    )

                    # Should only evaluate the specific ruleset
                    assert len(result["rulesets_evaluated"]) == 1
                    assert result["rulesets_evaluated"][0]["id"] == 99

    @pytest.mark.asyncio
    async def test_valuation_breakdown_structure(self):
        """Test that valuation breakdown maintains expected structure."""
        service = RuleEvaluationService()

        # Mock listing
        mock_listing = MagicMock(spec=Listing)
        mock_listing.id = 1
        mock_listing.price_usd = Decimal("1000.00")
        mock_listing.adjusted_price_usd = Decimal("1000.00")
        mock_listing.valuation_breakdown = {}

        # Mock session
        mock_session = AsyncMock()

        # Setup mock queries
        listing_query = MagicMock()
        listing_query.scalar_one_or_none.return_value = mock_listing

        async def mock_execute(stmt):
            return listing_query

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock evaluation to return sample results
        with patch.object(service, "evaluate_listing") as mock_eval:
            mock_eval.return_value = {
                "listing_id": 1,
                "original_price": 1000.0,
                "total_adjustment": 75.0,
                "adjusted_price": 1075.0,
                "matched_rules_count": 2,
                "layers": {
                    "baseline": {
                        "ruleset_id": 1,
                        "ruleset_name": "System: Baseline v1.0",
                        "priority": 5,
                        "adjustment": 50.0,
                        "matched_rules": [{"rule_id": 101, "adjustment": 50.0}],
                    },
                    "basic": {
                        "ruleset_id": 2,
                        "ruleset_name": "Standard",
                        "priority": 10,
                        "adjustment": 25.0,
                        "matched_rules": [{"rule_id": 201, "adjustment": 25.0}],
                    },
                },
                "matched_rules": [
                    {"rule_id": 101, "adjustment": 50.0, "layer": "baseline"},
                    {"rule_id": 201, "adjustment": 25.0, "layer": "basic"},
                ],
                "rulesets_evaluated": [
                    {"id": 1, "name": "System: Baseline v1.0", "priority": 5, "layer": "baseline"},
                    {"id": 2, "name": "Standard", "priority": 10, "layer": "basic"},
                ],
            }

            result = await service.apply_ruleset_to_listing(mock_session, 1)

            # Verify breakdown was set correctly
            assert mock_listing.adjusted_price_usd == 1075.0
            breakdown = mock_listing.valuation_breakdown
            assert breakdown["total_adjustment"] == 75.0
            assert "layers" in breakdown
            assert "matched_rules" in breakdown  # For backward compatibility
            assert "rulesets_evaluated" in breakdown
            assert "evaluated_at" in breakdown
