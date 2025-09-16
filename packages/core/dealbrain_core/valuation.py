"""Valuation engine for computing adjusted listing prices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition


@dataclass
class ValuationRuleData:
    component_type: ComponentType
    metric: ComponentMetric
    unit_value_usd: float
    condition_new: float = 1.0
    condition_refurb: float = 0.75
    condition_used: float = 0.6

    def multiplier_for(self, condition: Condition) -> float:
        match condition:
            case Condition.NEW:
                return self.condition_new
            case Condition.REFURB:
                return self.condition_refurb
            case _:
                return self.condition_used


@dataclass
class ComponentValuationInput:
    component_type: ComponentType
    quantity: float
    label: str


@dataclass
class ValuationLine:
    label: str
    component_type: ComponentType
    quantity: float
    unit_value: float
    condition_multiplier: float
    deduction_usd: float


@dataclass
class ValuationResult:
    listing_price_usd: float
    adjusted_price_usd: float
    lines: list[ValuationLine]

    @property
    def total_deductions(self) -> float:
        return sum(line.deduction_usd for line in self.lines)


def compute_adjusted_price(
    listing_price_usd: float,
    condition: Condition,
    rules: Iterable[ValuationRuleData],
    components: Iterable[ComponentValuationInput],
) -> ValuationResult:
    lookup = {rule.component_type: rule for rule in rules}
    lines: list[ValuationLine] = []

    for component in components:
        rule = lookup.get(component.component_type)
        if not rule:
            continue
        quantity = component.quantity
        if quantity <= 0:
            continue
        unit_value = rule.unit_value_usd
        if rule.metric == ComponentMetric.PER_TB:
            quantity = quantity / 1024
        deduction = quantity * unit_value * rule.multiplier_for(condition)
        lines.append(
            ValuationLine(
                label=component.label,
                component_type=component.component_type,
                quantity=quantity,
                unit_value=unit_value,
                condition_multiplier=rule.multiplier_for(condition),
                deduction_usd=float(round(deduction, 2)),
            )
        )

    adjusted_price = float(round(listing_price_usd - sum(line.deduction_usd for line in lines), 2))
    return ValuationResult(
        listing_price_usd=listing_price_usd,
        adjusted_price_usd=max(adjusted_price, 0.0),
        lines=lines,
    )


__all__ = [
    "ValuationRuleData",
    "ComponentValuationInput",
    "ValuationLine",
    "ValuationResult",
    "compute_adjusted_price",
]
