from __future__ import annotations

import math
from typing import List, Optional

from xbrlval.core.models import ValidationIssue, ValidationReport, Instance, Fact
from xbrlval.core.parser import XbrlInstanceParser
from xbrlval.taxonomy.linkbase import CalculationLinkbase


class ValidationEngine:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir

    def validate(self, source: str, run_calculation: bool = True, run_all: bool = True) -> ValidationReport:
        issues: List[ValidationIssue] = []

        try:
            parser = XbrlInstanceParser(base_uri=str(source))
            instance: Instance = parser.parse(source)
        except Exception as ex:  # noqa: BLE001
            issues.append(
                ValidationIssue(
                    code="XBRL-PARSE-ERROR",
                    message=f"Failed to parse instance: {ex}",
                    severity="error",
                    location=str(source),
                )
            )
            return ValidationReport(issues=issues)

        # Basic context checks
        seen_ctx_ids = set()
        for ctx_id, ctx in instance.contexts.items():
            if ctx_id in seen_ctx_ids:
                issues.append(ValidationIssue(code="CTX-DUPLICATE-ID", message=f"Duplicate context id '{ctx_id}'", severity="error"))
            seen_ctx_ids.add(ctx_id)
            if not ctx.entity.identifier or not ctx.entity.scheme:
                issues.append(ValidationIssue(code="CTX-ENTITY-MISSING", message=f"Context '{ctx_id}' missing entity identifier/scheme", severity="error"))
            if ctx.period.type == "duration":
                if not ctx.period.start_date or not ctx.period.end_date:
                    issues.append(ValidationIssue(code="CTX-PERIOD-MALFORMED", message=f"Context '{ctx_id}' duration missing start/end", severity="error"))
            if ctx.period.type == "instant":
                if not ctx.period.instant:
                    issues.append(ValidationIssue(code="CTX-PERIOD-MALFORMED", message=f"Context '{ctx_id}' instant missing value", severity="error"))

        # Basic unit checks
        seen_unit_ids = set()
        for unit_id, unit in instance.units.items():
            if unit_id in seen_unit_ids:
                issues.append(ValidationIssue(code="UNIT-DUPLICATE-ID", message=f"Duplicate unit id '{unit_id}'", severity="error"))
            seen_unit_ids.add(unit_id)
            if not unit.measures and not (unit.numerator_measures and unit.denominator_measures):
                issues.append(ValidationIssue(code="UNIT-EMPTY", message=f"Unit '{unit_id}' has no measures", severity="error"))

        # Facts checks
        ctx_ids = set(instance.contexts.keys())
        unit_ids = set(instance.units.keys())
        fact_key_to_value = {}
        for fact in instance.facts:
            if fact.context_ref and fact.context_ref not in ctx_ids:
                issues.append(ValidationIssue(code="FACT-CONTEXT-REF-UNKNOWN", message=f"Fact '{fact.concept}' references unknown context '{fact.context_ref}'", severity="error"))
            if fact.is_numeric and (not fact.unit_ref or fact.unit_ref not in unit_ids):
                issues.append(ValidationIssue(code="FACT-UNIT-REF-UNKNOWN", message=f"Numeric fact '{fact.concept}' references unknown unit '{fact.unit_ref}'", severity="error"))
            # Duplicate facts with differing values
            key = (fact.concept, fact.context_ref, fact.unit_ref)
            if key in fact_key_to_value:
                if fact.value != fact_key_to_value[key]:
                    issues.append(ValidationIssue(code="FACT-DUPLICATE-INCONSISTENT", message=f"Duplicate fact for {key} has different value", severity="error"))
            else:
                fact_key_to_value[key] = fact.value

            # Numeric value validity
            if fact.is_numeric and fact.value is not None:
                try:
                    float(fact.value)
                except Exception:  # noqa: BLE001
                    issues.append(ValidationIssue(code="FACT-NONNUMERIC", message=f"Numeric fact '{fact.concept}' has non-numeric value '{fact.value}'", severity="error"))

        # Calculation linkbase checks (if available)
        if run_calculation and (instance.linkbase_locations or instance.schema_locations):
            try:
                calc = CalculationLinkbase()
                calc.load_from_instance(instance)
                calc_issues = self._check_calculation_consistency(instance, calc)
                issues.extend(calc_issues)
            except Exception as ex:  # noqa: BLE001
                issues.append(ValidationIssue(code="CALC-LOAD-ERROR", message=f"Failed to load calculation linkbase: {ex}", severity="warning"))

        return ValidationReport(issues=issues)

    def _check_calculation_consistency(self, instance: Instance, calc: CalculationLinkbase) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        # Build index of facts by concept and context and unit
        by_key: dict[tuple[str, Optional[str], Optional[str]], Fact] = {}
        for f in instance.facts:
            key = (f.concept, f.context_ref, f.unit_ref)
            by_key[key] = f

        for role, trees in calc.trees_by_role.items():
            for root_concept, children in trees.items():
                # Evaluate only if parent fact exists
                for key, parent_fact in list(by_key.items()):
                    concept, ctx, unit = key
                    if concept != root_concept:
                        continue
                    parent_val = self._to_float(parent_fact.value)
                    if parent_val is None:
                        continue
                    total = 0.0
                    missing_child = False
                    for child_concept, weight in children:
                        child = by_key.get((child_concept, ctx, unit))
                        if child is None:
                            missing_child = True
                            continue
                        child_val = self._to_float(child.value)
                        if child_val is None:
                            missing_child = True
                            continue
                        total += weight * child_val
                    if missing_child:
                        # Cannot assert inconsistency if inputs missing
                        continue
                    if not self._values_equal_with_decimals(parent_fact, total):
                        issues.append(ValidationIssue(
                            code="CALC-INCONSISTENT",
                            message=f"[{role}] {root_concept} != sum(children). Expected {total} but got {parent_val} for context {ctx} unit {unit}",
                            severity="error",
                        ))
        return issues

    def _to_float(self, val: Optional[str]) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except Exception:  # noqa: BLE001
            return None

    def _values_equal_with_decimals(self, parent: Fact, computed: float) -> bool:
        # Simplified decimals handling: if decimals is an integer d, compare rounded values at that scale
        d = None
        if parent.decimals is not None and parent.decimals.lower() != "inf":
            try:
                d = int(parent.decimals)
            except Exception:  # noqa: BLE001
                d = None
        try:
            parent_val = float(parent.value) if parent.value is not None else math.nan
        except Exception:  # noqa: BLE001
            return False
        if d is None:
            return math.isclose(parent_val, computed, rel_tol=1e-9, abs_tol=0.0)
        scale = 10 ** (-d) if d < 0 else 10 ** d
        # Round to 'd' decimals as per XBRL 'decimals': number of decimal places
        return round(parent_val, d) == round(computed, d)