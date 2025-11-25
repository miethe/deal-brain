"""
Integration tests for RulesService.

Tests CRUD operations for rulesets, rule groups, and rules with database persistence.
"""

from datetime import datetime
from typing import Any
import sys
import types
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

if "celery" not in sys.modules:

    class _DummyTask:
        def __init__(self, func):
            self._func = func

        def __call__(self, *args, **kwargs):
            return self._func(*args, **kwargs)

        def delay(self, *args, **kwargs):
            return self._func(*args, **kwargs)

    class _StubCelery:
        def __init__(self, *args, **kwargs):
            pass

        def config_from_object(self, *args, **kwargs):
            return None

        def task(self, *decorator_args, **decorator_kwargs):
            def _decorator(func):
                return _DummyTask(func)

            return _decorator

    celery_stub = types.ModuleType("celery")
    celery_stub.Celery = _StubCelery
    sys.modules["celery"] = celery_stub

from dealbrain_api.models.core import ValuationRuleset, ValuationRuleGroup, ValuationRuleV2
from dealbrain_api.services.rules import RulesService
from dealbrain_api.schemas.rules import (
    RulesetCreate,
    RulesetUpdate,
    RuleGroupCreate,
    RuleCreate,
    ConditionCreate,
    ActionCreate,
    ConditionOperator,
    ActionType,
    LogicalOperator,
)


@pytest.fixture
async def rules_service():
    """Create RulesService instance."""
    return RulesService()


@pytest.fixture
async def sample_ruleset_data() -> RulesetCreate:
    """Sample ruleset creation data."""
    return RulesetCreate(
        name="Test Gaming Ruleset",
        version="1.0.0",
        description="Test ruleset for gaming PCs",
        is_active=True,
        metadata={"author": "Test Suite", "tags": ["gaming", "test"]},
    )


@pytest.fixture
async def sample_rule_group_data() -> RuleGroupCreate:
    """Sample rule group creation data."""
    return RuleGroupCreate(
        name="CPU Valuation",
        category="cpu",
        description="CPU-based valuation rules",
        weight=0.30,
        display_order=1,
    )


@pytest.fixture
async def sample_rule_data() -> RuleCreate:
    """Sample rule creation data."""
    return RuleCreate(
        name="High-End CPU Premium",
        description="Premium for high-end CPUs",
        category="cpu",
        evaluation_order=100,
        is_active=True,
        conditions=ConditionCreate(
            field_name="cpu.cpu_mark_multi",
            field_type="integer",
            operator=ConditionOperator.GREATER_THAN,
            value=30000,
        ),
        actions=[
            ActionCreate(
                action_type=ActionType.FIXED_VALUE,
                value_usd=100.00,
                description="Add $100 for high-end CPU",
            )
        ],
    )


@pytest.fixture(autouse=True)
def _disable_recalculation(monkeypatch):
    """Prevent Celery enqueues during tests unless explicitly observed."""
    monkeypatch.setattr(
        "dealbrain_api.services.rules.enqueue_listing_recalculation",
        lambda **_: None,
    )


@pytest.fixture
def recalculation_spy(monkeypatch):
    """Capture recalculation enqueue invocations."""
    calls: list[dict[str, Any]] = []

    def _capture(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        "dealbrain_api.services.rules.enqueue_listing_recalculation",
        _capture,
    )
    return calls


class TestRulesetCRUD:
    """Test ruleset CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_ruleset(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        recalculation_spy,
    ):
        """Test creating a new ruleset."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)

        assert ruleset.id is not None
        assert ruleset.name == sample_ruleset_data.name
        assert ruleset.version == sample_ruleset_data.version
        assert ruleset.description == sample_ruleset_data.description
        assert ruleset.is_active == sample_ruleset_data.is_active
        assert ruleset.metadata == sample_ruleset_data.metadata
        assert isinstance(ruleset.created_at, datetime)
        assert recalculation_spy[-1]["ruleset_id"] == ruleset.id
        assert recalculation_spy[-1]["reason"] == "ruleset_created"

    @pytest.mark.asyncio
    async def test_get_ruleset(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
    ):
        """Test retrieving a ruleset by ID."""
        created = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        retrieved = await rules_service.get_ruleset(db_session, created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    @pytest.mark.asyncio
    async def test_get_ruleset_not_found(
        self, db_session: AsyncSession, rules_service: RulesService
    ):
        """Test retrieving non-existent ruleset returns None."""
        result = await rules_service.get_ruleset(db_session, 99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_rulesets(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
    ):
        """Test listing all rulesets."""
        # Create multiple rulesets
        await rules_service.create_ruleset(db_session, sample_ruleset_data)

        second_data = sample_ruleset_data.model_copy()
        second_data.name = "Test Workstation Ruleset"
        await rules_service.create_ruleset(db_session, second_data)

        rulesets = await rules_service.list_rulesets(db_session)
        assert len(rulesets) >= 2

    @pytest.mark.asyncio
    async def test_list_rulesets_active_only(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
    ):
        """Test filtering rulesets by active status."""
        # Create active ruleset
        await rules_service.create_ruleset(db_session, sample_ruleset_data)

        # Create inactive ruleset
        inactive_data = sample_ruleset_data.model_copy()
        inactive_data.name = "Inactive Ruleset"
        inactive_data.is_active = False
        await rules_service.create_ruleset(db_session, inactive_data)

        active_rulesets = await rules_service.list_rulesets(db_session, active_only=True)
        assert all(rs.is_active for rs in active_rulesets)

    @pytest.mark.asyncio
    async def test_update_ruleset(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        recalculation_spy,
    ):
        """Test updating a ruleset."""
        created = await rules_service.create_ruleset(db_session, sample_ruleset_data)

        update_data = RulesetUpdate(
            name="Updated Gaming Ruleset",
            version="1.1.0",
            description="Updated description",
            is_active=False,
        )

        updated = await rules_service.update_ruleset(db_session, created.id, update_data)

        assert updated.name == update_data.name
        assert updated.version == update_data.version
        assert updated.description == update_data.description
        assert updated.is_active == update_data.is_active
        assert recalculation_spy[-1]["reason"] == "ruleset_updated"
        assert recalculation_spy[-1]["ruleset_id"] == created.id

    @pytest.mark.asyncio
    async def test_delete_ruleset(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        recalculation_spy,
    ):
        """Test deleting a ruleset."""
        created = await rules_service.create_ruleset(db_session, sample_ruleset_data)

        result = await rules_service.delete_ruleset(db_session, created.id)
        assert result is True

        # Verify it's deleted
        retrieved = await rules_service.get_ruleset(db_session, created.id)
        assert retrieved is None
        assert recalculation_spy[-1]["reason"] == "ruleset_deleted"
        assert recalculation_spy[-1]["ruleset_id"] == created.id


class TestRuleGroupCRUD:
    """Test rule group CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_rule_group(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
        recalculation_spy,
    ):
        """Test creating a rule group."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)

        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )

        assert group.id is not None
        assert group.ruleset_id == ruleset.id
        assert group.name == sample_rule_group_data.name
        assert group.category == sample_rule_group_data.category
        assert group.weight == sample_rule_group_data.weight
        assert recalculation_spy[-1]["reason"] == "rule_group_created"
        assert recalculation_spy[-1]["ruleset_id"] == ruleset.id

    @pytest.mark.asyncio
    async def test_list_rule_groups(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
    ):
        """Test listing rule groups for a ruleset."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)

        # Create multiple groups
        await rules_service.create_rule_group(db_session, ruleset.id, sample_rule_group_data)

        gpu_group = sample_rule_group_data.model_copy()
        gpu_group.name = "GPU Valuation"
        gpu_group.category = "gpu"
        await rules_service.create_rule_group(db_session, ruleset.id, gpu_group)

        groups = await rules_service.list_rule_groups(db_session, ruleset.id)
        assert len(groups) == 2

    @pytest.mark.asyncio
    async def test_delete_rule_group(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
    ):
        """Test deleting a rule group."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )

        result = await rules_service.delete_rule_group(db_session, group.id)
        assert result is True


class TestRuleCRUD:
    """Test rule CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_rule(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
        sample_rule_data: RuleCreate,
        recalculation_spy,
    ):
        """Test creating a rule."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )

        rule = await rules_service.create_rule(db_session, group.id, sample_rule_data)

        assert rule.id is not None
        assert rule.group_id == group.id
        assert rule.name == sample_rule_data.name
        assert rule.category == sample_rule_data.category
        assert rule.is_active == sample_rule_data.is_active
        assert len(rule.conditions) > 0
        assert len(rule.actions) > 0
        assert recalculation_spy[-1]["reason"] == "rule_created"
        assert recalculation_spy[-1]["ruleset_id"] == ruleset.id

    @pytest.mark.asyncio
    async def test_create_per_unit_rule_requires_metric(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
    ):
        """Per-unit actions without metrics should be rejected."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )

        with pytest.raises(ValueError, match="Per-unit actions must include a metric"):
            await rules_service.create_rule(
                db_session,
                group.id,
                name="Invalid Per Unit Rule",
                category="ram",
                evaluation_order=10,
                actions=[
                    {
                        "action_type": "per_unit",
                        "value_usd": 5.0,
                    }
                ],
            )

    @pytest.mark.asyncio
    async def test_create_rule_with_nested_conditions(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
    ):
        """Test creating a rule with nested AND/OR conditions."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )

        # (cores >= 8 AND ram >= 16) OR cpu_mark > 30000
        rule_data = RuleCreate(
            name="High-Performance PC",
            description="Premium for high-performance PCs",
            category="cpu",
            evaluation_order=100,
            is_active=True,
            conditions=ConditionCreate(
                logical_operator=LogicalOperator.OR,
                conditions=[
                    ConditionCreate(
                        logical_operator=LogicalOperator.AND,
                        conditions=[
                            ConditionCreate(
                                field_name="cpu.cores",
                                operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                                value=8,
                            ),
                            ConditionCreate(
                                field_name="ram_gb",
                                operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                                value=16,
                            ),
                        ],
                    ),
                    ConditionCreate(
                        field_name="cpu.cpu_mark_multi",
                        operator=ConditionOperator.GREATER_THAN,
                        value=30000,
                    ),
                ],
            ),
            actions=[
                ActionCreate(
                    action_type=ActionType.FIXED_VALUE,
                    value_usd=150.00,
                    description="Premium for high-performance configuration",
                )
            ],
        )

        rule = await rules_service.create_rule(db_session, group.id, rule_data)

        assert rule.id is not None
        assert len(rule.conditions) > 0
        # Verify nested structure persisted correctly
        assert rule.conditions[0].logical_operator in [LogicalOperator.AND, LogicalOperator.OR]

    @pytest.mark.asyncio
    async def test_list_rules(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
        sample_rule_data: RuleCreate,
    ):
        """Test listing rules in a group."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )

        # Create multiple rules
        await rules_service.create_rule(db_session, group.id, sample_rule_data)

        second_rule = sample_rule_data.model_copy()
        second_rule.name = "Mid-Range CPU"
        await rules_service.create_rule(db_session, group.id, second_rule)

        rules = await rules_service.list_rules(db_session, group.id)
        assert len(rules) == 2

    @pytest.mark.asyncio
    async def test_update_rule(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
        sample_rule_data: RuleCreate,
        recalculation_spy,
    ):
        """Test updating a rule."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )
        rule = await rules_service.create_rule(db_session, group.id, sample_rule_data)

        from dealbrain_api.schemas.rules import RuleUpdate

        update_data = RuleUpdate(
            name="Updated High-End CPU Premium",
            description="Updated description",
            is_active=False,
        )

        updated = await rules_service.update_rule(db_session, rule.id, update_data)

        assert updated.name == update_data.name
        assert updated.description == update_data.description
        assert updated.is_active == update_data.is_active
        assert recalculation_spy[-1]["reason"] == "rule_updated"
        assert recalculation_spy[-1]["ruleset_id"] == ruleset.id

    @pytest.mark.asyncio
    async def test_delete_rule(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
        sample_rule_data: RuleCreate,
        recalculation_spy,
    ):
        """Test deleting a rule."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )
        rule = await rules_service.create_rule(db_session, group.id, sample_rule_data)

        result = await rules_service.delete_rule(db_session, rule.id)
        assert result is True
        assert recalculation_spy[-1]["reason"] == "rule_deleted"
        assert recalculation_spy[-1]["ruleset_id"] == ruleset.id

    @pytest.mark.asyncio
    async def test_delete_ruleset_cascades(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        sample_ruleset_data: RulesetCreate,
        sample_rule_group_data: RuleGroupCreate,
        sample_rule_data: RuleCreate,
    ):
        """Test that deleting a ruleset cascades to groups and rules."""
        ruleset = await rules_service.create_ruleset(db_session, sample_ruleset_data)
        group = await rules_service.create_rule_group(
            db_session, ruleset.id, sample_rule_group_data
        )
        rule = await rules_service.create_rule(db_session, group.id, sample_rule_data)

        # Delete ruleset
        await rules_service.delete_ruleset(db_session, ruleset.id)

        # Verify group and rule are also deleted
        retrieved_group = await db_session.get(ValuationRuleGroup, group.id)
        assert retrieved_group is None

        retrieved_rule = await db_session.get(ValuationRuleV2, rule.id)
        assert retrieved_rule is None
