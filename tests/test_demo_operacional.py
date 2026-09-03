from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from accounting_sim.canonical import SchemaValidationError
from accounting_sim.demo_operacional import (
    ALT_SCENARIO_ID,
    ANALYSIS_INPUT_COLUMNS,
    BASE_SCENARIO_ID,
    DEMO_INTERFACE_VERSION,
    ENTITY_INPUT_COLUMNS,
    MEMORY_COLUMNS,
    OPERATIONS_INPUT_COLUMNS,
    RUN_REQUEST_COLUMNS,
    DemoConfigurationError,
    DemoInputError,
    build_demo_canonical_objects,
    load_demo_inputs,
    run_demo,
)
from accounting_sim.tax_simples_2027 import (
    SIMPLES_2027_COMPARISON_COLUMNS,
    SIMPLES_2027_SCENARIO_RESULT_COLUMNS,
    run_simples_2027_counterfactual_report,
)
from scripts import run_demo_operacional
from scripts.run_demo_operacional import (
    EXIT_CONFIGURATION_ERROR,
    EXIT_INPUT_ERROR,
    EXIT_INTERNAL_ERROR,
    EXIT_SUCCESS,
    RUN_STATUS_COLUMNS,
    execute,
)


UTF8_BOM = b"\xef\xbb\xbf"


def _canonical_operations() -> list[dict[str, str]]:
    return [
        {
            "ID_OPERACAO": "OP001",
            "DATA": "2027-01-10",
            "TIPO_OPERACAO": "compra_revenda",
            "VALOR": "85000",
            "REGIME_CONTRAPARTE": "ibs_cbs_regime_regular",
            "OBSERVACAO": "compra mercadoria",
        },
        {
            "ID_OPERACAO": "OP002",
            "DATA": "2027-01-15",
            "TIPO_OPERACAO": "venda_b2b",
            "VALOR": "70000",
            "REGIME_CONTRAPARTE": "ibs_cbs_regime_regular",
            "OBSERVACAO": "cliente empresa",
        },
        {
            "ID_OPERACAO": "OP003",
            "DATA": "2027-01-20",
            "TIPO_OPERACAO": "venda_b2c",
            "VALOR": "30000",
            "REGIME_CONTRAPARTE": "consumidor_final",
            "OBSERVACAO": "consumidor final",
        },
    ]


def _write_frame(path: Path, rows: list[dict[str, object]], columns: tuple[str, ...]) -> None:
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def _write_valid_inputs(
    base: Path,
    *,
    operations: list[dict[str, str]] | None = None,
    rbt12: str = "1200000",
    cbs: str = "0.09",
    alpha: str = "1",
    interface_version: str = DEMO_INTERFACE_VERSION,
    run_id: str = "TEST_RUN_001",
) -> None:
    _write_frame(base / "entity_input.csv", [{"CHAVE": "RBT12", "VALOR": rbt12}], ENTITY_INPUT_COLUMNS)
    _write_frame(base / "operations_input.csv", operations or _canonical_operations(), OPERATIONS_INPUT_COLUMNS)
    _write_frame(
        base / "analysis_input.csv",
        [
            {"CHAVE_PARAM": "CBS_2027_ANALYSIS_RATE_FRACTION", "VALOR": cbs},
            {"CHAVE_PARAM": "REGULAR_CREDIT_REALIZATION_FRACTION", "VALOR": alpha},
        ],
        ANALYSIS_INPUT_COLUMNS,
    )
    _write_frame(
        base / "run_request.csv",
        [{"RUN_ID": run_id, "INTERFACE_VERSION": interface_version}],
        RUN_REQUEST_COLUMNS,
    )


def _read_output(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=object, keep_default_na=False, encoding="utf-8-sig")


def _scenario_row(frame: pd.DataFrame, scenario_id: str) -> pd.Series:
    return frame.loc[frame["ID_CENARIO"] == scenario_id].iloc[0]


def test_canonical_adapter_builds_canonical_objects(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)
    inputs = load_demo_inputs(tmp_path)
    canonical = build_demo_canonical_objects(inputs)

    assert list(canonical.events["ID_EVENTO"]) == ["D13_OP001", "D13_OP002", "D13_OP003"]
    assert list(canonical.events["VL_EVENTO_CENTS"]) == [8_500_000, 7_000_000, 3_000_000]
    assert list(canonical.events["NATUREZA"]) == ["bem", "bem", "bem"]
    assert "ID_CENARIO" not in canonical.events.columns
    assert "ID_CENARIO" not in canonical.fiscal_event_attributes.columns
    fiscal = canonical.fiscal_event_attributes
    assert fiscal.loc[
        (fiscal["ID_EVENTO"] == "D13_OP002") & (fiscal["ATRIBUTO_FISCAL"] == "REGIME_ADQUIRENTE"),
        "VALOR",
    ].iloc[0] == "ibs_cbs_regime_regular"
    assert canonical.entity_profile.loc[canonical.entity_profile["ATRIBUTO"] == "RBT12_CENTS", "VALOR"].iloc[0] == "120000000"


def test_canonical_case_reproduces_spec_12_regression(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)
    result = run_demo(tmp_path)
    scenarios = result.report.scenario_results
    comparison = result.report.comparison_results
    puro = _scenario_row(scenarios, BASE_SCENARIO_ID)
    hibrido = _scenario_row(scenarios, ALT_SCENARIO_ID)
    delta = comparison.loc[comparison["METRICA"] == "ENCARGO_TRIBUTARIO_COMPARAVEL"].iloc[0]
    assert puro["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"] == 882_500
    assert hibrido["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"] == 882_213
    assert delta["DELTA_CENTS"] == -287
    assert result.report.cbs_break_even_rate_fraction == Decimal("0.09019166666666666666666666667")


def test_wrong_b2b_counterpart_is_rejected_before_engine(tmp_path: Path) -> None:
    operations = _canonical_operations()
    operations[1]["REGIME_CONTRAPARTE"] = "consumidor_final"
    _write_valid_inputs(tmp_path, operations=operations)
    with pytest.raises(DemoInputError, match="REGIME_CONTRAPARTE"):
        load_demo_inputs(tmp_path)


def test_wrong_b2c_counterpart_is_rejected_before_engine(tmp_path: Path) -> None:
    operations = _canonical_operations()
    operations[2]["REGIME_CONTRAPARTE"] = "ibs_cbs_regime_regular"
    _write_valid_inputs(tmp_path, operations=operations)
    with pytest.raises(DemoInputError, match="REGIME_CONTRAPARTE"):
        load_demo_inputs(tmp_path)


@pytest.mark.parametrize("value", ["0", "-1"])
def test_zero_or_negative_operation_value_is_rejected(tmp_path: Path, value: str) -> None:
    operations = _canonical_operations()
    operations[0]["VALOR"] = value
    _write_valid_inputs(tmp_path, operations=operations)
    with pytest.raises(DemoInputError, match="VALOR deve ser maior que zero"):
        load_demo_inputs(tmp_path)


@pytest.mark.parametrize("rbt12", ["0", "-1", "3600000.01"])
def test_invalid_rbt12_is_rejected(tmp_path: Path, rbt12: str) -> None:
    _write_valid_inputs(tmp_path, rbt12=rbt12)
    with pytest.raises((DemoInputError, SchemaValidationError)):
        run_demo(tmp_path)


def test_missing_cbs_analysis_rate_is_rejected(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)
    analysis = _read_output(tmp_path / "analysis_input.csv")
    analysis = analysis.loc[analysis["CHAVE_PARAM"] != "CBS_2027_ANALYSIS_RATE_FRACTION"]
    analysis.to_csv(tmp_path / "analysis_input.csv", index=False, encoding="utf-8-sig")
    with pytest.raises(DemoInputError, match="obrigatórias ausentes"):
        load_demo_inputs(tmp_path)


@pytest.mark.parametrize("alpha", ["-0.1", "1.1"])
def test_alpha_outside_closed_interval_is_rejected(tmp_path: Path, alpha: str) -> None:
    _write_valid_inputs(tmp_path, alpha=alpha)
    with pytest.raises(DemoInputError, match="REGULAR_CREDIT_REALIZATION_FRACTION"):
        load_demo_inputs(tmp_path)


def test_decimal_comma_is_rejected_in_inputs(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path, cbs="0,09")
    with pytest.raises(DemoInputError, match="ponto como separador decimal"):
        load_demo_inputs(tmp_path)


def test_interface_mismatch_is_rejected(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path, interface_version="spec_13_incompatível")
    with pytest.raises(DemoInputError, match="INTERFACE_VERSION incompatível"):
        load_demo_inputs(tmp_path)


def test_duplicate_operation_id_is_rejected(tmp_path: Path) -> None:
    operations = _canonical_operations()
    operations[1]["ID_OPERACAO"] = "OP001"
    _write_valid_inputs(tmp_path, operations=operations)
    with pytest.raises(DemoInputError, match="ID_OPERACAO deve ser único"):
        load_demo_inputs(tmp_path)


def test_invalid_date_is_rejected(tmp_path: Path) -> None:
    operations = _canonical_operations()
    operations[0]["DATA"] = "2027-99-99"
    _write_valid_inputs(tmp_path, operations=operations)
    with pytest.raises(DemoInputError, match="YYYY-MM-DD"):
        load_demo_inputs(tmp_path)


def test_out_of_scope_date_is_rejected(tmp_path: Path) -> None:
    operations = _canonical_operations()
    operations[0]["DATA"] = "2027-07-01"
    _write_valid_inputs(tmp_path, operations=operations)
    with pytest.raises(DemoInputError, match="H1/2027"):
        load_demo_inputs(tmp_path)


def test_invalid_input_schema_and_partial_rows_are_rejected(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)
    operations = _read_output(tmp_path / "operations_input.csv").drop(columns=["OBSERVACAO"])
    operations.to_csv(tmp_path / "operations_input.csv", index=False, encoding="utf-8-sig")
    with pytest.raises(DemoInputError, match="Schema inválido"):
        load_demo_inputs(tmp_path)

    _write_valid_inputs(tmp_path)
    partial = _read_output(tmp_path / "operations_input.csv")
    partial.loc[len(partial)] = ["OP004", "", "venda_b2b", "10", "ibs_cbs_regime_regular", ""]
    partial.to_csv(tmp_path / "operations_input.csv", index=False, encoding="utf-8-sig")
    with pytest.raises(DemoInputError, match="linha parcialmente preenchida"):
        load_demo_inputs(tmp_path)


def test_exact_output_schemas_and_exit_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    _write_valid_inputs(input_dir)

    assert execute(input_dir, output_dir) == EXIT_SUCCESS
    assert tuple(_read_output(output_dir / "run_status.csv").columns) == RUN_STATUS_COLUMNS
    assert tuple(_read_output(output_dir / "scenario_results.csv").columns) == SIMPLES_2027_SCENARIO_RESULT_COLUMNS
    assert tuple(_read_output(output_dir / "comparison_results.csv").columns) == SIMPLES_2027_COMPARISON_COLUMNS
    assert tuple(_read_output(output_dir / "memory_results.csv").columns) == MEMORY_COLUMNS

    operations = _read_output(input_dir / "operations_input.csv")
    operations.loc[0, "VALOR"] = "-1"
    operations.to_csv(input_dir / "operations_input.csv", index=False, encoding="utf-8-sig")
    assert execute(input_dir, tmp_path / "out_input_error") == EXIT_INPUT_ERROR

    def raise_config(*_args, **_kwargs):
        raise DemoConfigurationError("config inválida")

    def raise_internal(*_args, **_kwargs):
        raise RuntimeError("falha inesperada")

    monkeypatch.setattr(run_demo_operacional, "run_demo", raise_config)
    assert execute(input_dir, tmp_path / "out_config_error") == EXIT_CONFIGURATION_ERROR
    monkeypatch.setattr(run_demo_operacional, "run_demo", raise_internal)
    assert execute(input_dir, tmp_path / "out_internal_error") == EXIT_INTERNAL_ERROR


def test_output_and_input_csvs_use_utf8_bom(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    _write_valid_inputs(input_dir)

    for filename in ("entity_input.csv", "operations_input.csv", "analysis_input.csv", "run_request.csv"):
        assert (input_dir / filename).read_bytes().startswith(UTF8_BOM)
    assert load_demo_inputs(input_dir).run_id == "TEST_RUN_001"
    assert execute(input_dir, output_dir) == EXIT_SUCCESS
    for filename in ("run_status.csv", "scenario_results.csv", "comparison_results.csv", "memory_results.csv"):
        assert (output_dir / filename).read_bytes().startswith(UTF8_BOM)


def test_unicode_comma_quote_and_newline_observation_round_trip(tmp_path: Path) -> None:
    operations = _canonical_operations()
    operations[0]["OBSERVACAO"] = 'compra com acento, "aspas"\ne nova linha'
    _write_valid_inputs(tmp_path, operations=operations)
    inputs = load_demo_inputs(tmp_path)
    canonical = build_demo_canonical_objects(inputs)
    assert canonical.events.loc[canonical.events["ID_EVENTO"] == "D13_OP001", "HIST"].iloc[0] == 'compra com acento, "aspas"\ne nova linha'
    assert run_demo(tmp_path).report.scenario_results.shape[0] == 2


def test_split_operations_preserve_same_totals_and_results(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)
    canonical = run_demo(tmp_path).report.scenario_results
    split_ops = [
        {**_canonical_operations()[0], "ID_OPERACAO": "OP001A", "VALOR": "40000"},
        {**_canonical_operations()[0], "ID_OPERACAO": "OP001B", "VALOR": "45000"},
        {**_canonical_operations()[1], "ID_OPERACAO": "OP002A", "VALOR": "35000"},
        {**_canonical_operations()[1], "ID_OPERACAO": "OP002B", "VALOR": "35000"},
        {**_canonical_operations()[2], "ID_OPERACAO": "OP003A", "VALOR": "10000"},
        {**_canonical_operations()[2], "ID_OPERACAO": "OP003B", "VALOR": "20000"},
    ]
    split_dir = tmp_path / "split"
    split_dir.mkdir()
    _write_valid_inputs(split_dir, operations=split_ops)
    split = run_demo(split_dir).report.scenario_results
    pd.testing.assert_frame_equal(canonical, split)


def test_cbs_10_percent_sensitivity(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path, cbs="0.10")
    result = run_demo(tmp_path)
    scenarios = result.report.scenario_results
    comparison = result.report.comparison_results
    puro = _scenario_row(scenarios, BASE_SCENARIO_ID)
    hibrido = _scenario_row(scenarios, ALT_SCENARIO_ID)
    delta = comparison.loc[comparison["METRICA"] == "ENCARGO_TRIBUTARIO_COMPARAVEL"].iloc[0]
    assert puro["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"] == 882_500
    assert hibrido["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"] == 897_213
    assert delta["DELTA_CENTS"] == 14_713


def test_spec_12_engine_regression_is_preserved(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)
    inputs = load_demo_inputs(tmp_path)
    canonical = build_demo_canonical_objects(inputs)
    adapter_result = run_demo(tmp_path).report
    direct_result = run_simples_2027_counterfactual_report(
        canonical.events,
        canonical.tax_context,
        canonical.analysis_parameters,
    )
    pd.testing.assert_frame_equal(adapter_result.scenario_results, direct_result.scenario_results)
    pd.testing.assert_frame_equal(adapter_result.comparison_results, direct_result.comparison_results)


def test_adapter_does_not_reimplement_tax_formula_constants() -> None:
    source = (Path(__file__).resolve().parents[1] / "src" / "accounting_sim" / "demo_operacional.py").read_text(encoding="utf-8")
    for forbidden in ("0.1533", "0.0017", "0.08825", "882500", "897213"):
        assert forbidden not in source
