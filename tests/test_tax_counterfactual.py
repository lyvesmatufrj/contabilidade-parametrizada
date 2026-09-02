from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from accounting_sim.canonical import (
    COUNTERFACTUAL_COMPARISON_COLUMNS,
    FISCAL_EVENT_ATTRIBUTE_COLUMNS,
    TAX_ASSESSMENT_RESULT_COLUMNS,
    TAX_OPERATION_RESULT_COLUMNS,
    SchemaValidationError,
)
from accounting_sim.tax_context import TaxContext
from accounting_sim.tax_counterfactual import (
    Cbs2026CounterfactualResult,
    run_cbs_2026_counterfactual_experiment,
    validate_cbs_2026_counterfactual_experiment,
)


BASE_SCENARIO_ID = "CBS_2026_BASE"
CONTROL_SCENARIO_ID = "CBS_2026_CONTROLE"


def _fixture_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data/examples/cbs_2026"


def _events() -> pd.DataFrame:
    events = pd.read_csv(_fixture_dir() / "events.csv", dtype=str, keep_default_na=False)
    events["DT_EVENTO"] = pd.to_datetime(events["DT_EVENTO"]).dt.date
    events["VL_EVENTO_CENTS"] = events["VL_EVENTO_CENTS"].astype(int)
    events["VL_CUSTO_CENTS"] = events["VL_CUSTO_CENTS"].replace("", pd.NA)
    mask = events["VL_CUSTO_CENTS"].notna()
    events.loc[mask, "VL_CUSTO_CENTS"] = events.loc[mask, "VL_CUSTO_CENTS"].astype(int)
    return events


def _tax_context() -> TaxContext:
    return TaxContext(
        entity_profile=pd.read_csv(
            _fixture_dir() / "entity_profile.csv", dtype=str, keep_default_na=False
        ),
        fiscal_event_attributes=pd.read_csv(
            _fixture_dir() / "fiscal_event_attributes.csv",
            dtype=str,
            keep_default_na=False,
        ),
        tax_scenarios=_tax_scenarios_csv(),
        tax_parameters=pd.read_csv(
            _fixture_dir() / "tax_parameters.csv", dtype=str, keep_default_na=False
        ),
    )


def _tax_scenarios_csv() -> pd.DataFrame:
    scenarios = pd.read_csv(
        _fixture_dir() / "tax_scenarios.csv", dtype=str, keep_default_na=False
    )
    scenarios["DT_REFERENCIA_NORMATIVA"] = pd.to_datetime(
        scenarios["DT_REFERENCIA_NORMATIVA"]
    ).dt.date
    scenarios["E_BASELINE"] = scenarios["E_BASELINE"].map(
        lambda value: str(value).lower() == "true"
    )
    scenarios["ATIVO"] = scenarios["ATIVO"].map(
        lambda value: str(value).lower() == "true"
    )
    return scenarios


def _with_control_scenario(
    context: TaxContext,
    *,
    scenario_id: str = CONTROL_SCENARIO_ID,
    active: bool = True,
    baseline: bool = False,
    regime_entity: str | None = None,
) -> TaxContext:
    scenarios = context.tax_scenarios.copy(deep=True)
    control = scenarios.loc[scenarios["ID_CENARIO"] == BASE_SCENARIO_ID].iloc[0].copy()
    control["ID_CENARIO"] = scenario_id
    control["DESCRICAO"] = "controle de orquestracao"
    control["E_BASELINE"] = baseline
    control["ATIVO"] = active
    if regime_entity is not None:
        control["REGIME_ENTIDADE"] = regime_entity
    scenarios = pd.concat([scenarios, pd.DataFrame([control])], ignore_index=True)
    return TaxContext(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=scenarios,
        tax_parameters=context.tax_parameters,
    )


def _valid_context() -> TaxContext:
    return _with_control_scenario(_tax_context())


def _replace_scenario_value(
    context: TaxContext,
    scenario_id: str,
    column: str,
    value: object,
) -> TaxContext:
    scenarios = context.tax_scenarios.copy(deep=True)
    scenarios.loc[scenarios["ID_CENARIO"] == scenario_id, column] = value
    return TaxContext(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=scenarios,
        tax_parameters=context.tax_parameters,
    )


def test_baseline_plus_structural_control_is_valid() -> None:
    report = validate_cbs_2026_counterfactual_experiment(_events(), _valid_context())

    assert report.ok


def test_single_active_scenario_is_rejected() -> None:
    report = validate_cbs_2026_counterfactual_experiment(_events(), _tax_context())

    assert not report.ok
    assert "counterfactual_requires_two_active_scenarios" in {
        issue.code for issue in report.issues
    }


def test_zero_active_scenarios_are_rejected() -> None:
    context = _replace_scenario_value(_tax_context(), BASE_SCENARIO_ID, "ATIVO", False)

    report = validate_cbs_2026_counterfactual_experiment(_events(), context)

    assert not report.ok
    assert "counterfactual_requires_two_active_scenarios" in {
        issue.code for issue in report.issues
    }


def test_exactly_one_active_baseline_is_preserved() -> None:
    context = _with_control_scenario(_tax_context(), baseline=True)

    report = validate_cbs_2026_counterfactual_experiment(_events(), context)

    assert not report.ok
    assert "counterfactual_invalid_active_baseline_count" in {
        issue.code for issue in report.issues
    }


def test_active_scenario_outside_cbs_scope_invalidates_whole_experiment() -> None:
    context = _with_control_scenario(
        _tax_context(), regime_entity="simples_nacional"
    )

    report = validate_cbs_2026_counterfactual_experiment(_events(), context)

    assert not report.ok
    assert any(
        issue.scenario_id == CONTROL_SCENARIO_ID
        and issue.code == "cbs_entity_regime_out_of_scope"
        for issue in report.issues
    )
    with pytest.raises(SchemaValidationError, match=CONTROL_SCENARIO_ID):
        run_cbs_2026_counterfactual_experiment(_events(), context)


def test_inactive_scenario_outside_cbs_scope_is_not_executed() -> None:
    context = _with_control_scenario(_tax_context())
    context = _with_control_scenario(
        context,
        scenario_id="CBS_2026_INATIVO_FORA_RECORTE",
        active=False,
        regime_entity="simples_nacional",
    )

    result = run_cbs_2026_counterfactual_experiment(_events(), context)

    assert "CBS_2026_INATIVO_FORA_RECORTE" not in result.scenario_ids
    assert "CBS_2026_INATIVO_FORA_RECORTE" not in set(
        result.operation_results["ID_CENARIO"]
    )
    assert "CBS_2026_INATIVO_FORA_RECORTE" not in set(
        result.assessment_results["ID_CENARIO"]
    )


def test_inputs_are_not_mutated() -> None:
    events = _events()
    context = _valid_context()
    events_before = events.copy(deep=True)
    entity_before = context.entity_profile.copy(deep=True)
    fiscal_before = context.fiscal_event_attributes.copy(deep=True)
    scenarios_before = context.tax_scenarios.copy(deep=True)
    parameters_before = context.tax_parameters.copy(deep=True)

    run_cbs_2026_counterfactual_experiment(events, context)

    pd.testing.assert_frame_equal(events, events_before)
    pd.testing.assert_frame_equal(context.entity_profile, entity_before)
    pd.testing.assert_frame_equal(context.fiscal_event_attributes, fiscal_before)
    pd.testing.assert_frame_equal(context.tax_scenarios, scenarios_before)
    pd.testing.assert_frame_equal(context.tax_parameters, parameters_before)


def test_factual_tables_do_not_receive_scenario_id() -> None:
    context = _valid_context()

    assert "ID_CENARIO" not in _events().columns
    assert "ID_CENARIO" not in context.entity_profile.columns
    assert "ID_CENARIO" not in context.fiscal_event_attributes.columns
    assert FISCAL_EVENT_ATTRIBUTE_COLUMNS == (
        "ID_EVENTO",
        "ATRIBUTO_FISCAL",
        "VALOR",
        "TIPO_VALOR",
        "ORIGEM",
    )


def test_result_identifies_baseline_and_returns_dataclass() -> None:
    result = run_cbs_2026_counterfactual_experiment(_events(), _valid_context())

    assert isinstance(result, Cbs2026CounterfactualResult)
    assert result.baseline_scenario_id == BASE_SCENARIO_ID


def test_scenario_ids_have_baseline_first_and_other_ids_sorted() -> None:
    context = _with_control_scenario(_tax_context(), scenario_id="ZZZ_CONTROLE")
    context = _with_control_scenario(context, scenario_id="AAA_CONTROLE")

    result = run_cbs_2026_counterfactual_experiment(_events(), context)

    assert result.scenario_ids == (BASE_SCENARIO_ID, "AAA_CONTROLE", "ZZZ_CONTROLE")


def test_result_schemas_are_canonical() -> None:
    result = run_cbs_2026_counterfactual_experiment(_events(), _valid_context())

    assert tuple(result.operation_results.columns) == TAX_OPERATION_RESULT_COLUMNS
    assert tuple(result.assessment_results.columns) == TAX_ASSESSMENT_RESULT_COLUMNS


def test_one_assessment_per_active_scenario() -> None:
    result = run_cbs_2026_counterfactual_experiment(_events(), _valid_context())

    assert len(result.assessment_results) == len(result.scenario_ids)
    assert list(result.assessment_results["ID_CENARIO"]) == list(result.scenario_ids)


def test_baseline_and_structural_control_have_same_values_except_scenario_id() -> None:
    result = run_cbs_2026_counterfactual_experiment(_events(), _valid_context())

    baseline_ops = result.operation_results[
        result.operation_results["ID_CENARIO"] == BASE_SCENARIO_ID
    ].reset_index(drop=True)
    control_ops = result.operation_results[
        result.operation_results["ID_CENARIO"] == CONTROL_SCENARIO_ID
    ].reset_index(drop=True)
    control_ops = control_ops.assign(ID_CENARIO=BASE_SCENARIO_ID)
    pd.testing.assert_frame_equal(baseline_ops, control_ops)

    baseline_assessment = result.assessment_results[
        result.assessment_results["ID_CENARIO"] == BASE_SCENARIO_ID
    ].reset_index(drop=True)
    control_assessment = result.assessment_results[
        result.assessment_results["ID_CENARIO"] == CONTROL_SCENARIO_ID
    ].reset_index(drop=True)
    control_assessment = control_assessment.assign(ID_CENARIO=BASE_SCENARIO_ID)
    pd.testing.assert_frame_equal(baseline_assessment, control_assessment)


def test_physical_scenario_row_order_does_not_change_output() -> None:
    context = _with_control_scenario(_tax_context(), scenario_id="ZZZ_CONTROLE")
    context = _with_control_scenario(context, scenario_id="AAA_CONTROLE")
    shuffled_context = TaxContext(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=context.tax_scenarios.sample(frac=1, random_state=10).reset_index(
            drop=True
        ),
        tax_parameters=context.tax_parameters,
    )

    expected = run_cbs_2026_counterfactual_experiment(_events(), context)
    actual = run_cbs_2026_counterfactual_experiment(_events(), shuffled_context)

    assert actual.baseline_scenario_id == expected.baseline_scenario_id
    assert actual.scenario_ids == expected.scenario_ids
    pd.testing.assert_frame_equal(actual.operation_results, expected.operation_results)
    pd.testing.assert_frame_equal(actual.assessment_results, expected.assessment_results)


def test_repeated_execution_is_deterministic() -> None:
    first = run_cbs_2026_counterfactual_experiment(_events(), _valid_context())
    second = run_cbs_2026_counterfactual_experiment(_events(), _valid_context())

    assert first.baseline_scenario_id == second.baseline_scenario_id
    assert first.scenario_ids == second.scenario_ids
    pd.testing.assert_frame_equal(first.operation_results, second.operation_results)
    pd.testing.assert_frame_equal(first.assessment_results, second.assessment_results)


def test_no_delta_or_counterfactual_comparison_is_produced() -> None:
    result = run_cbs_2026_counterfactual_experiment(_events(), _valid_context())

    assert not hasattr(result, "comparison_results")
    assert not any(column.startswith("DELTA_") for column in result.operation_results)
    assert not any(column.startswith("DELTA_") for column in result.assessment_results)
    assert not set(COUNTERFACTUAL_COMPARISON_COLUMNS).issubset(
        result.operation_results.columns
    )
    assert not set(COUNTERFACTUAL_COMPARISON_COLUMNS).issubset(
        result.assessment_results.columns
    )


def test_counterfactual_module_does_not_hard_code_new_tax_values() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src/accounting_sim/tax_counterfactual.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "CBS_RATE_FRACTION",
        "PCBS_PERCENT",
        "VCBS_CENTS",
        "VBC_CENTS",
        "CST_IBS_CBS",
        "CCLASSTRIB",
        "0.009",
        "000001",
    ):
        assert forbidden not in source


def test_workbook_materialization_is_not_implemented_in_counterfactual_executor() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src/accounting_sim/tax_counterfactual.py"
    ).read_text(encoding="utf-8")

    assert "FISCAL_RESULTADOS_OPERACAO" not in source
    assert "FISCAL_APURACAO" not in source
    assert "COMPARATIVO_CENARIOS" not in source
