from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from accounting_sim.canonical import (
    COUNTERFACTUAL_COMPARISON_COLUMNS,
    TAX_ASSESSMENT_RESULT_COLUMNS,
    TAX_OPERATION_RESULT_COLUMNS,
    SchemaValidationError,
)
from accounting_sim.tax_comparison import (
    Cbs2026CounterfactualReport,
    compare_cbs_2026_counterfactual_result,
    run_cbs_2026_counterfactual_report,
)
from accounting_sim.tax_context import TaxContext
from accounting_sim.tax_counterfactual import (
    Cbs2026CounterfactualResult,
    run_cbs_2026_counterfactual_experiment,
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


def _tax_scenarios_csv() -> pd.DataFrame:
    scenarios = pd.read_csv(_fixture_dir() / "tax_scenarios.csv", dtype=str, keep_default_na=False)
    scenarios["DT_REFERENCIA_NORMATIVA"] = pd.to_datetime(scenarios["DT_REFERENCIA_NORMATIVA"]).dt.date
    scenarios["E_BASELINE"] = scenarios["E_BASELINE"].map(lambda value: str(value).lower() == "true")
    scenarios["ATIVO"] = scenarios["ATIVO"].map(lambda value: str(value).lower() == "true")
    return scenarios


def _tax_context() -> TaxContext:
    return TaxContext(
        entity_profile=pd.read_csv(_fixture_dir() / "entity_profile.csv", dtype=str, keep_default_na=False),
        fiscal_event_attributes=pd.read_csv(_fixture_dir() / "fiscal_event_attributes.csv", dtype=str, keep_default_na=False),
        tax_scenarios=_tax_scenarios_csv(),
        tax_parameters=pd.read_csv(_fixture_dir() / "tax_parameters.csv", dtype=str, keep_default_na=False),
    )


def _with_control_scenario(context: TaxContext) -> TaxContext:
    scenarios = context.tax_scenarios.copy(deep=True)
    control = scenarios.loc[scenarios["ID_CENARIO"] == BASE_SCENARIO_ID].iloc[0].copy()
    control["ID_CENARIO"] = CONTROL_SCENARIO_ID
    control["DESCRICAO"] = "controle de orquestracao"
    control["E_BASELINE"] = False
    control["ATIVO"] = True
    return TaxContext(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=pd.concat([scenarios, pd.DataFrame([control])], ignore_index=True),
        tax_parameters=context.tax_parameters,
    )


def _operation_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID_CENARIO": "S0",
                "ID_EVENTO": "E001",
                "TRIBUTO": "TRIBUTO_TESTE",
                "INCIDE": True,
                "BASE_CENTS": 1000,
                "ALIQUOTA": "0.01",
                "CREDITO_CENTS": 0,
                "DEBITO_CENTS": 10,
                "VERSAO_REGRA": "REGRA_TESTE",
            }
        ],
        columns=TAX_OPERATION_RESULT_COLUMNS,
        dtype=object,
    )


def _assessment_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=TAX_ASSESSMENT_RESULT_COLUMNS, dtype=object)


def _assessment_row(
    scenario_id: str,
    tribute: str = "TRIBUTO_TESTE",
    *,
    s_apur: object = 900,
    t_recolher: object = 0,
    p_cash: object = None,
    e_dre: object = None,
    c_saldo: object = 0,
) -> dict[str, object]:
    return {
        "ID_CENARIO": scenario_id,
        "TRIBUTO": tribute,
        "S_APUR_CENTS": s_apur,
        "T_RECOLHER_CENTS": t_recolher,
        "P_CASH_CENTS": p_cash,
        "E_DRE_CENTS": e_dre,
        "C_SALDO_CENTS": c_saldo,
        "VERSAO_REGRA": "REGRA_TESTE",
    }


def _result(
    *,
    baseline: str = "S0",
    scenario_ids: tuple[str, ...] = ("S0", "S1"),
    assessment_rows: list[dict[str, object]] | None = None,
) -> Cbs2026CounterfactualResult:
    return Cbs2026CounterfactualResult(
        baseline_scenario_id=baseline,
        scenario_ids=scenario_ids,
        operation_results=_operation_frame(),
        assessment_results=_assessment_frame(
            assessment_rows
            or [
                _assessment_row("S0"),
                _assessment_row("S1"),
            ]
        ),
    )


def test_structural_control_generates_one_comparison_line() -> None:
    comparison = compare_cbs_2026_counterfactual_result(_result())

    assert len(comparison) == 1
    assert tuple(comparison.columns) == COUNTERFACTUAL_COMPARISON_COLUMNS
    assert comparison.iloc[0]["ID_CENARIO_BASE"] == "S0"
    assert comparison.iloc[0]["ID_CENARIO"] == "S1"


def test_baseline_is_not_compared_against_itself() -> None:
    comparison = compare_cbs_2026_counterfactual_result(_result())

    assert "S0" not in set(comparison["ID_CENARIO"])


def test_alternative_scenario_order_is_preserved_and_tributes_are_sorted() -> None:
    comparison = compare_cbs_2026_counterfactual_result(
        _result(
            scenario_ids=("S0", "S2", "S1"),
            assessment_rows=[
                _assessment_row("S0", "Z_TRIBUTO"),
                _assessment_row("S0", "A_TRIBUTO"),
                _assessment_row("S2", "Z_TRIBUTO"),
                _assessment_row("S2", "A_TRIBUTO"),
                _assessment_row("S1", "Z_TRIBUTO"),
                _assessment_row("S1", "A_TRIBUTO"),
            ],
        )
    )

    assert list(comparison[["ID_CENARIO", "TRIBUTO"]].itertuples(index=False, name=None)) == [
        ("S2", "A_TRIBUTO"),
        ("S2", "Z_TRIBUTO"),
        ("S1", "A_TRIBUTO"),
        ("S1", "Z_TRIBUTO"),
    ]


def test_delta_sign_is_alternative_minus_baseline_with_positive_negative_and_zero() -> None:
    comparison = compare_cbs_2026_counterfactual_result(
        _result(
            assessment_rows=[
                _assessment_row("S0", s_apur=900, t_recolher=10, c_saldo=500),
                _assessment_row("S1", s_apur=1200, t_recolher=10, c_saldo=200),
            ],
        )
    )
    row = comparison.iloc[0]

    assert row["DELTA_S_APUR_CENTS"] == 300
    assert row["DELTA_T_RECOLHER_CENTS"] == 0
    assert row["DELTA_C_SALDO_CENTS"] == -300


def test_none_cash_and_income_statement_components_remain_none() -> None:
    comparison = compare_cbs_2026_counterfactual_result(
        _result(
            assessment_rows=[
                _assessment_row("S0", p_cash=None, e_dre=10),
                _assessment_row("S1", p_cash=20, e_dre=None),
            ],
        )
    )
    row = comparison.iloc[0]

    assert row["DELTA_P_CASH_CENTS"] is None
    assert row["DELTA_E_DRE_CENTS"] is None


def test_absent_values_are_not_interpreted_as_zero_even_when_both_sides_are_absent() -> None:
    comparison = compare_cbs_2026_counterfactual_result(
        _result(
            assessment_rows=[
                _assessment_row("S0", p_cash=pd.NA, e_dre=None),
                _assessment_row("S1", p_cash=None, e_dre=pd.NA),
            ],
        )
    )
    row = comparison.iloc[0]

    assert row["DELTA_P_CASH_CENTS"] is None
    assert row["DELTA_E_DRE_CENTS"] is None


def test_invalid_operation_schema_is_rejected() -> None:
    result = _result()
    invalid = Cbs2026CounterfactualResult(
        baseline_scenario_id=result.baseline_scenario_id,
        scenario_ids=result.scenario_ids,
        operation_results=result.operation_results.drop(columns=["INCIDE"]),
        assessment_results=result.assessment_results,
    )

    with pytest.raises(SchemaValidationError, match="operation_results"):
        compare_cbs_2026_counterfactual_result(invalid)


def test_invalid_assessment_schema_is_rejected() -> None:
    result = _result()
    invalid = Cbs2026CounterfactualResult(
        baseline_scenario_id=result.baseline_scenario_id,
        scenario_ids=result.scenario_ids,
        operation_results=result.operation_results,
        assessment_results=result.assessment_results.drop(columns=["VERSAO_REGRA"]),
    )

    with pytest.raises(SchemaValidationError, match="assessment_results"):
        compare_cbs_2026_counterfactual_result(invalid)


def test_duplicate_scenario_ids_are_rejected() -> None:
    with pytest.raises(SchemaValidationError, match="duplicatas"):
        compare_cbs_2026_counterfactual_result(_result(scenario_ids=("S0", "S1", "S1")))


def test_missing_baseline_is_rejected() -> None:
    with pytest.raises(SchemaValidationError, match="baseline_scenario_id"):
        compare_cbs_2026_counterfactual_result(_result(baseline="S9"))


def test_baseline_not_first_is_rejected() -> None:
    with pytest.raises(SchemaValidationError, match="primeiro"):
        compare_cbs_2026_counterfactual_result(_result(scenario_ids=("S1", "S0")))


def test_duplicate_assessment_per_scenario_and_tribute_is_rejected() -> None:
    with pytest.raises(SchemaValidationError, match="duplicada"):
        compare_cbs_2026_counterfactual_result(
            _result(
                assessment_rows=[
                    _assessment_row("S0"),
                    _assessment_row("S1"),
                    _assessment_row("S1"),
                ],
            )
        )


def test_scenario_without_assessment_is_rejected() -> None:
    with pytest.raises(SchemaValidationError, match="sem apuração"):
        compare_cbs_2026_counterfactual_result(
            _result(
                scenario_ids=("S0", "S1", "S2"),
                assessment_rows=[_assessment_row("S0"), _assessment_row("S1")],
            )
        )


def test_extra_scenario_in_assessment_is_rejected() -> None:
    with pytest.raises(SchemaValidationError, match="não esperados"):
        compare_cbs_2026_counterfactual_result(
            _result(
                assessment_rows=[
                    _assessment_row("S0"),
                    _assessment_row("S1"),
                    _assessment_row("S2"),
                ],
            )
        )


def test_divergent_tribute_set_is_rejected() -> None:
    with pytest.raises(SchemaValidationError, match="tributos divergente"):
        compare_cbs_2026_counterfactual_result(
            _result(
                assessment_rows=[
                    _assessment_row("S0", "TRIBUTO_A"),
                    _assessment_row("S1", "TRIBUTO_B"),
                ],
            )
        )


def test_float_in_monetary_field_is_rejected() -> None:
    with pytest.raises(SchemaValidationError, match="float"):
        compare_cbs_2026_counterfactual_result(
            _result(
                assessment_rows=[
                    _assessment_row("S0"),
                    _assessment_row("S1", s_apur=900.0),
                ],
            )
        )


def test_comparison_does_not_mutate_input() -> None:
    result = _result()
    operation_before = result.operation_results.copy(deep=True)
    assessment_before = result.assessment_results.copy(deep=True)

    compare_cbs_2026_counterfactual_result(result)

    assert_frame_equal(result.operation_results, operation_before)
    assert_frame_equal(result.assessment_results, assessment_before)


def test_comparison_is_deterministic() -> None:
    first = compare_cbs_2026_counterfactual_result(_result())
    second = compare_cbs_2026_counterfactual_result(_result())

    assert_frame_equal(first, second)


def test_runner_integrates_with_spec10_and_preserves_its_outputs() -> None:
    events = _events()
    context = _with_control_scenario(_tax_context())
    experiment = run_cbs_2026_counterfactual_experiment(events, context)

    report = run_cbs_2026_counterfactual_report(events, context)

    assert isinstance(report, Cbs2026CounterfactualReport)
    assert report.baseline_scenario_id == experiment.baseline_scenario_id
    assert report.scenario_ids == experiment.scenario_ids
    assert_frame_equal(report.operation_results, experiment.operation_results)
    assert_frame_equal(report.assessment_results, experiment.assessment_results)


def test_baseline_plus_structural_control_produces_zero_known_deltas() -> None:
    report = run_cbs_2026_counterfactual_report(_events(), _with_control_scenario(_tax_context()))
    row = report.comparison_results.iloc[0]

    assert len(report.comparison_results) == 1
    assert row["ID_CENARIO_BASE"] == BASE_SCENARIO_ID
    assert row["ID_CENARIO"] == CONTROL_SCENARIO_ID
    assert row["DELTA_S_APUR_CENTS"] == 0
    assert row["DELTA_T_RECOLHER_CENTS"] == 0
    assert row["DELTA_P_CASH_CENTS"] is None
    assert row["DELTA_E_DRE_CENTS"] is None
    assert row["DELTA_C_SALDO_CENTS"] == 0


def test_comparison_module_does_not_call_cbs_engine_directly() -> None:
    source = (Path(__file__).resolve().parents[1] / "src/accounting_sim/tax_comparison.py").read_text(encoding="utf-8")

    assert "from accounting_sim.tax_cbs_2026" not in source
    assert "run_cbs_2026(" not in source
