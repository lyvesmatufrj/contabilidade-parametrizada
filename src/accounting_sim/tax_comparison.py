"""Comparação auditável de resultados contrafactuais CBS 2026."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral

import pandas as pd

from accounting_sim.canonical import (
    COUNTERFACTUAL_COMPARISON_COLUMNS,
    TAX_ASSESSMENT_RESULT_COLUMNS,
    TAX_OPERATION_RESULT_COLUMNS,
    SchemaValidationError,
)
from accounting_sim.tax_context import TaxContext
from accounting_sim.tax_counterfactual import (
    Cbs2026CounterfactualResult,
    run_cbs_2026_counterfactual_experiment,
)


CBS_2026_COUNTERFACTUAL_REPORT_SPEC_VERSION = (
    "spec_11_counterfactual_tax_comparison_report_v1"
)

_MONETARY_COLUMNS = (
    "S_APUR_CENTS",
    "T_RECOLHER_CENTS",
    "P_CASH_CENTS",
    "E_DRE_CENTS",
    "C_SALDO_CENTS",
)
_DELTA_COLUMNS = (
    "DELTA_S_APUR_CENTS",
    "DELTA_T_RECOLHER_CENTS",
    "DELTA_P_CASH_CENTS",
    "DELTA_E_DRE_CENTS",
    "DELTA_C_SALDO_CENTS",
)


@dataclass(frozen=True)
class Cbs2026CounterfactualReport:
    baseline_scenario_id: str
    scenario_ids: tuple[str, ...]
    operation_results: pd.DataFrame
    assessment_results: pd.DataFrame
    comparison_results: pd.DataFrame


def compare_cbs_2026_counterfactual_result(
    counterfactual_result: Cbs2026CounterfactualResult,
) -> pd.DataFrame:
    operation_results = counterfactual_result.operation_results.copy(deep=True)
    assessment_results = counterfactual_result.assessment_results.copy(deep=True)
    scenario_ids = tuple(counterfactual_result.scenario_ids)
    baseline_id = counterfactual_result.baseline_scenario_id

    _validate_counterfactual_structure(
        baseline_id,
        scenario_ids,
        operation_results,
        assessment_results,
    )

    baseline_rows = (
        assessment_results.loc[assessment_results["ID_CENARIO"] == baseline_id]
        .set_index("TRIBUTO", drop=False)
        .sort_index()
    )
    baseline_tributes = tuple(sorted(str(value) for value in baseline_rows.index))
    rows: list[dict[str, object]] = []

    for scenario_id in scenario_ids[1:]:
        scenario_rows = (
            assessment_results.loc[assessment_results["ID_CENARIO"] == scenario_id]
            .set_index("TRIBUTO", drop=False)
            .sort_index()
        )
        for tribute in baseline_tributes:
            baseline = baseline_rows.loc[tribute]
            alternative = scenario_rows.loc[tribute]
            row = {
                "ID_CENARIO_BASE": baseline_id,
                "ID_CENARIO": scenario_id,
                "TRIBUTO": tribute,
            }
            for source_column, delta_column in zip(_MONETARY_COLUMNS, _DELTA_COLUMNS, strict=True):
                row[delta_column] = _nullable_delta(
                    _normalize_nullable_int(alternative[source_column], source_column),
                    _normalize_nullable_int(baseline[source_column], source_column),
                )
            rows.append(row)

    return pd.DataFrame(rows, columns=COUNTERFACTUAL_COMPARISON_COLUMNS, dtype=object)


def run_cbs_2026_counterfactual_report(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> Cbs2026CounterfactualReport:
    counterfactual_result = run_cbs_2026_counterfactual_experiment(events, tax_context)
    comparison_results = compare_cbs_2026_counterfactual_result(counterfactual_result)
    return Cbs2026CounterfactualReport(
        baseline_scenario_id=counterfactual_result.baseline_scenario_id,
        scenario_ids=tuple(counterfactual_result.scenario_ids),
        operation_results=counterfactual_result.operation_results.copy(deep=True),
        assessment_results=counterfactual_result.assessment_results.copy(deep=True),
        comparison_results=comparison_results.copy(deep=True),
    )


def _validate_counterfactual_structure(
    baseline_id: str,
    scenario_ids: tuple[str, ...],
    operation_results: pd.DataFrame,
    assessment_results: pd.DataFrame,
) -> None:
    if tuple(operation_results.columns) != TAX_OPERATION_RESULT_COLUMNS:
        raise SchemaValidationError("operation_results não usa TAX_OPERATION_RESULT_COLUMNS.")
    if tuple(assessment_results.columns) != TAX_ASSESSMENT_RESULT_COLUMNS:
        raise SchemaValidationError("assessment_results não usa TAX_ASSESSMENT_RESULT_COLUMNS.")
    if baseline_id not in scenario_ids:
        raise SchemaValidationError("baseline_scenario_id deve pertencer a scenario_ids.")
    if not scenario_ids or scenario_ids[0] != baseline_id:
        raise SchemaValidationError("baseline_scenario_id deve ser o primeiro scenario_id.")
    if len(set(scenario_ids)) != len(scenario_ids):
        raise SchemaValidationError("scenario_ids não pode conter duplicatas.")

    duplicated = assessment_results.duplicated(["ID_CENARIO", "TRIBUTO"], keep=False)
    if duplicated.any():
        raise SchemaValidationError("assessment_results contém apuração duplicada por cenário e tributo.")

    expected_scenarios = set(scenario_ids)
    actual_scenarios = set(assessment_results["ID_CENARIO"].astype(str))
    missing_scenarios = expected_scenarios - actual_scenarios
    extra_scenarios = actual_scenarios - expected_scenarios
    if missing_scenarios:
        raise SchemaValidationError(f"assessment_results sem apuração para cenários: {sorted(missing_scenarios)}.")
    if extra_scenarios:
        raise SchemaValidationError(f"assessment_results contém cenários não esperados: {sorted(extra_scenarios)}.")

    baseline_tributes = _tributes_for_scenario(assessment_results, baseline_id)
    for scenario_id in scenario_ids[1:]:
        scenario_tributes = _tributes_for_scenario(assessment_results, scenario_id)
        if scenario_tributes != baseline_tributes:
            raise SchemaValidationError(
                f"Conjunto de tributos divergente no cenário {scenario_id}."
            )

    for column in _MONETARY_COLUMNS:
        for value in assessment_results[column]:
            _normalize_nullable_int(value, column)


def _tributes_for_scenario(assessment_results: pd.DataFrame, scenario_id: str) -> set[str]:
    rows = assessment_results.loc[assessment_results["ID_CENARIO"] == scenario_id]
    return set(rows["TRIBUTO"].astype(str))


def _nullable_delta(alternative: int | None, baseline: int | None) -> int | None:
    if alternative is None or baseline is None:
        return None
    return alternative - baseline


def _normalize_nullable_int(value: object, column: str) -> int | None:
    if _is_missing(value):
        return None
    if isinstance(value, bool) or isinstance(value, float):
        raise SchemaValidationError(f"{column} deve ser int ou ausente; float/bool não é aceito.")
    if not isinstance(value, Integral):
        raise SchemaValidationError(f"{column} deve ser int ou ausente.")
    return int(value)


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False
