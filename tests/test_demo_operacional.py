from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from accounting_sim.demo_operacional import (
    ALT_SCENARIO_ID,
    BASE_SCENARIO_ID,
    DEMO_INTERFACE_VERSION,
    DemoInputError,
    build_demo_canonical_objects,
    load_demo_inputs,
    run_demo,
)
from scripts.run_demo_operacional import (
    EXIT_INPUT_ERROR,
    EXIT_SUCCESS,
    execute,
)


def _write_valid_inputs(base: Path) -> None:
    pd.DataFrame(
        [{"CHAVE": "RBT12", "VALOR": "1200000"}]
    ).to_csv(base / "entity_input.csv", index=False)

    pd.DataFrame(
        [
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
    ).to_csv(base / "operations_input.csv", index=False)

    pd.DataFrame(
        [
            {
                "CHAVE_PARAM": "CBS_2027_ANALYSIS_RATE_FRACTION",
                "VALOR": "0.09",
            },
            {
                "CHAVE_PARAM": "REGULAR_CREDIT_REALIZATION_FRACTION",
                "VALOR": "1",
            },
        ]
    ).to_csv(base / "analysis_input.csv", index=False)

    pd.DataFrame(
        [
            {
                "RUN_ID": "TEST_RUN_001",
                "INTERFACE_VERSION": DEMO_INTERFACE_VERSION,
            }
        ]
    ).to_csv(base / "run_request.csv", index=False)


def test_operational_adapter_builds_canonical_objects(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)
    inputs = load_demo_inputs(tmp_path)
    canonical = build_demo_canonical_objects(inputs)

    assert list(canonical.events["ID_EVENTO"]) == [
        "D13_OP001",
        "D13_OP002",
        "D13_OP003",
    ]
    assert list(canonical.events["VL_EVENTO_CENTS"]) == [
        8_500_000,
        7_000_000,
        3_000_000,
    ]

    fiscal = canonical.fiscal_event_attributes
    assert (
        fiscal.loc[
            (fiscal["ID_EVENTO"] == "D13_OP002")
            & (fiscal["ATRIBUTO_FISCAL"] == "REGIME_ADQUIRENTE"),
            "VALOR",
        ].iloc[0]
        == "ibs_cbs_regime_regular"
    )

    rbt12 = canonical.entity_profile.loc[
        canonical.entity_profile["ATRIBUTO"] == "RBT12_CENTS",
        "VALOR",
    ].iloc[0]
    assert rbt12 == "120000000"


def test_canonical_case_reproduces_spec_12_regression(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)
    result = run_demo(tmp_path)

    scenarios = result.report.scenario_results
    comparison = result.report.comparison_results

    puro = scenarios.loc[
        scenarios["ID_CENARIO"] == BASE_SCENARIO_ID
    ].iloc[0]
    hibrido = scenarios.loc[
        scenarios["ID_CENARIO"] == ALT_SCENARIO_ID
    ].iloc[0]
    delta = comparison.loc[
        comparison["METRICA"] == "ENCARGO_TRIBUTARIO_COMPARAVEL"
    ].iloc[0]

    assert puro["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"] == 882_500
    assert hibrido["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"] == 882_213
    assert delta["DELTA_CENTS"] == -287


def test_wrong_b2b_counterpart_is_rejected_before_engine(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)

    operations = pd.read_csv(
        tmp_path / "operations_input.csv",
        dtype=str,
        keep_default_na=False,
    )
    operations.loc[
        operations["TIPO_OPERACAO"] == "venda_b2b",
        "REGIME_CONTRAPARTE",
    ] = "consumidor_final"
    operations.to_csv(tmp_path / "operations_input.csv", index=False)

    with pytest.raises(DemoInputError, match="REGIME_CONTRAPARTE"):
        load_demo_inputs(tmp_path)


def test_missing_analysis_key_is_rejected(tmp_path: Path) -> None:
    _write_valid_inputs(tmp_path)

    analysis = pd.read_csv(
        tmp_path / "analysis_input.csv",
        dtype=str,
        keep_default_na=False,
    )
    analysis = analysis.loc[
        analysis["CHAVE_PARAM"]
        != "CBS_2027_ANALYSIS_RATE_FRACTION"
    ]
    analysis.to_csv(tmp_path / "analysis_input.csv", index=False)

    with pytest.raises(DemoInputError, match="obrigatórias ausentes"):
        load_demo_inputs(tmp_path)


def test_cli_writes_expected_outputs(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    _write_valid_inputs(input_dir)

    code = execute(input_dir, output_dir)

    assert code == EXIT_SUCCESS
    for filename in (
        "run_status.csv",
        "scenario_results.csv",
        "comparison_results.csv",
        "memory_results.csv",
    ):
        assert (output_dir / filename).exists()

    status = pd.read_csv(output_dir / "run_status.csv")
    assert bool(status.iloc[0]["OK"]) is True
    assert int(status.iloc[0]["STATUS_CODE"]) == 0


def test_cli_returns_input_error_and_status_file(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    _write_valid_inputs(input_dir)

    operations = pd.read_csv(
        input_dir / "operations_input.csv",
        dtype=str,
        keep_default_na=False,
    )
    operations.loc[0, "VALOR"] = "-1"
    operations.to_csv(input_dir / "operations_input.csv", index=False)

    code = execute(input_dir, output_dir)

    assert code == EXIT_INPUT_ERROR
    status = pd.read_csv(output_dir / "run_status.csv")
    assert bool(status.iloc[0]["OK"]) is False
    assert int(status.iloc[0]["STATUS_CODE"]) == EXIT_INPUT_ERROR
    assert "VALOR deve ser maior que zero" in status.iloc[0]["MESSAGE"]
