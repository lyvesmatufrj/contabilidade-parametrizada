"""Orquestração contrafactual multi-cenário para o motor CBS 2026."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd

from accounting_sim.canonical import (
    TAX_ASSESSMENT_RESULT_COLUMNS,
    TAX_OPERATION_RESULT_COLUMNS,
    TAX_SCENARIO_COLUMNS,
    SchemaValidationError,
    ValidationIssue,
    ValidationReport,
)
from accounting_sim.tax_cbs_2026 import (
    run_cbs_2026,
    validate_cbs_2026_admissibility,
)
from accounting_sim.tax_context import TaxContext, validate_tax_context


@dataclass(frozen=True)
class Cbs2026CounterfactualResult:
    baseline_scenario_id: str
    scenario_ids: tuple[str, ...]
    operation_results: pd.DataFrame
    assessment_results: pd.DataFrame


def validate_cbs_2026_counterfactual_experiment(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> ValidationReport:
    issues: list[ValidationIssue] = []

    context_report = validate_tax_context(tax_context, events)
    issues.extend(context_report.issues)

    if not set(TAX_SCENARIO_COLUMNS).issubset(tax_context.tax_scenarios.columns):
        return ValidationReport(ok=False, issues=tuple(_deduplicate_issues(issues)))

    active = _active_scenarios(tax_context)
    if len(active) < 2:
        issues.append(
            ValidationIssue(
                "counterfactual_requires_two_active_scenarios",
                "O experimento contrafactual CBS 2026 requer pelo menos dois cenários ativos.",
            )
        )

    baseline_ids = tuple(
        _clean_string(row["ID_CENARIO"])
        for _, row in active.iterrows()
        if _as_bool(row["E_BASELINE"]) is True
    )
    if len(baseline_ids) != 1:
        issues.append(
            ValidationIssue(
                "counterfactual_invalid_active_baseline_count",
                "O experimento contrafactual CBS 2026 requer exatamente um baseline ativo.",
            )
        )

    for scenario_id in _canonical_scenario_ids_from_active(active):
        scenario_report = validate_cbs_2026_admissibility(events, tax_context, scenario_id)
        if not scenario_report.ok:
            issues.extend(_issues_for_scenario(scenario_report.issues, scenario_id))

    return ValidationReport(ok=not issues, issues=tuple(_deduplicate_issues(issues)))


def run_cbs_2026_counterfactual_experiment(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> Cbs2026CounterfactualResult:
    report = validate_cbs_2026_counterfactual_experiment(events, tax_context)
    if not report.ok:
        _raise_report("Experimento contrafactual CBS 2026 inválido", report)

    scenario_ids = _canonical_scenario_ids(tax_context)
    baseline_scenario_id = scenario_ids[0]
    operation_frames: list[pd.DataFrame] = []
    assessment_frames: list[pd.DataFrame] = []

    for scenario_id in scenario_ids:
        result = run_cbs_2026(events, tax_context, scenario_id)
        operation_frames.append(result.operation_results.copy(deep=True))
        assessment_frames.append(result.assessment_results.copy(deep=True))

    operation_results = _concat_or_empty(operation_frames, TAX_OPERATION_RESULT_COLUMNS)
    assessment_results = _concat_or_empty(assessment_frames, TAX_ASSESSMENT_RESULT_COLUMNS)
    return Cbs2026CounterfactualResult(
        baseline_scenario_id=baseline_scenario_id,
        scenario_ids=tuple(scenario_ids),
        operation_results=operation_results.copy(deep=True),
        assessment_results=assessment_results.copy(deep=True),
    )


def _canonical_scenario_ids(tax_context: TaxContext) -> tuple[str, ...]:
    return _canonical_scenario_ids_from_active(_active_scenarios(tax_context))


def _canonical_scenario_ids_from_active(active_scenarios: pd.DataFrame) -> tuple[str, ...]:
    if active_scenarios.empty:
        return ()
    baseline_ids = [
        _clean_string(row["ID_CENARIO"])
        for _, row in active_scenarios.iterrows()
        if _as_bool(row["E_BASELINE"]) is True
    ]
    if len(baseline_ids) != 1:
        return tuple(sorted(_clean_string(value) for value in active_scenarios["ID_CENARIO"]))
    baseline_id = baseline_ids[0]
    other_ids = sorted(
        _clean_string(value)
        for value in active_scenarios["ID_CENARIO"]
        if _clean_string(value) != baseline_id
    )
    return (baseline_id, *other_ids)


def _active_scenarios(tax_context: TaxContext) -> pd.DataFrame:
    scenarios = tax_context.tax_scenarios.copy(deep=True)
    if not set(TAX_SCENARIO_COLUMNS).issubset(scenarios.columns):
        return pd.DataFrame(columns=TAX_SCENARIO_COLUMNS, dtype=object)
    scenarios = scenarios.loc[:, list(TAX_SCENARIO_COLUMNS)]
    active_mask = scenarios["ATIVO"].map(_as_bool) == True  # noqa: E712
    return scenarios.loc[active_mask].copy(deep=True)


def _as_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "sim", "s"}:
            return True
        if lowered in {"false", "0", "nao", "não", "n"}:
            return False
    return None


def _issues_for_scenario(
    issues: tuple[ValidationIssue, ...],
    scenario_id: str,
) -> tuple[ValidationIssue, ...]:
    return tuple(
        issue if issue.scenario_id is not None else replace(issue, scenario_id=scenario_id)
        for issue in issues
    )


def _concat_or_empty(
    frames: list[pd.DataFrame],
    columns: tuple[str, ...],
) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=columns, dtype=object)
    result = pd.concat(frames, ignore_index=True)
    return result.loc[:, list(columns)].copy(deep=True)


def _raise_report(stage: str, report: ValidationReport) -> None:
    details = "; ".join(
        f"{issue.scenario_id or '-'}:{issue.code}: {issue.message}"
        for issue in report.issues[:5]
    )
    raise SchemaValidationError(f"{stage}: {details}")


def _deduplicate_issues(issues: list[ValidationIssue]) -> tuple[ValidationIssue, ...]:
    unique: dict[tuple[object, ...], ValidationIssue] = {}
    for issue in issues:
        unique.setdefault(
            (
                issue.code,
                issue.event_id,
                issue.entity_id,
                issue.scenario_id,
                issue.tax_param_id,
            ),
            issue,
        )
    return tuple(unique.values())


def _clean_string(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()
