from dealbrain_core.enums import ComponentMetric, ComponentType, Condition
from dealbrain_core.valuation import ComponentValuationInput, ValuationRuleData, compute_adjusted_price


def test_compute_adjusted_price_applies_rules():
    rules = [
        ValuationRuleData(
            component_type=ComponentType.RAM,
            metric=ComponentMetric.PER_GB,
            unit_value_usd=4.0,
            condition_new=1.0,
            condition_refurb=0.8,
            condition_used=0.6,
        ),
        ValuationRuleData(
            component_type=ComponentType.OS_LICENSE,
            metric=ComponentMetric.FLAT,
            unit_value_usd=35.0,
        ),
    ]
    components = [
        ComponentValuationInput(component_type=ComponentType.RAM, quantity=32, label="32GB DDR4"),
        ComponentValuationInput(component_type=ComponentType.OS_LICENSE, quantity=1, label="Windows 11 Pro"),
    ]

    result = compute_adjusted_price(500.0, Condition.USED, rules, components)

    assert result.adjusted_price_usd == 500.0 - (32 * 4.0 * 0.6) - (35.0 * 0.6)
    assert result.total_deductions == sum(line.deduction_usd for line in result.lines)

