from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from accounting_sim.canonical import (
    EVENT_COLUMNS,
    TAX_ANALYSIS_PARAMETER_COLUMNS,
    TAX_PARAMETER_COLUMNS,
    TAX_SCENARIO_COLUMNS,
    SchemaValidationError,
)
from accounting_sim.tax_context import TaxContext, validate_tax_parameters
from accounting_sim.tax_simples_2027 import (
    SIMPLES_2027_COMPARISON_COLUMNS,
    SIMPLES_2027_SCENARIO_RESULT_COLUMNS,
    run_simples_2027_counterfactual_report,
    select_effective_simples_2027_rules,
    select_simples_2027_analysis_assumptions,
    validate_simples_2027_admissibility,
    validate_tax_analysis_parameters,
)


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "examples" / "simples_2027"


def load_case() -> tuple[pd.DataFrame, TaxContext, pd.DataFrame]:
    events = pd.read_csv(FIXTURE_DIR / "events.csv", dtype=str, keep_default_na=False)
    events["DT_EVENTO"] = pd.to_datetime(events["DT_EVENTO"]).dt.date
    events["VL_EVENTO_CENTS"] = events["VL_EVENTO_CENTS"].astype(int)
    events["VL_CUSTO_CENTS"] = events["VL_CUSTO_CENTS"].replace("", pd.NA)
    mask = events["VL_CUSTO_CENTS"].notna()
    events.loc[mask, "VL_CUSTO_CENTS"] = events.loc[mask, "VL_CUSTO_CENTS"].astype(int)
    for column in ("MEIO_FINANCEIRO", "CATEGORIA_DESPESA", "COD_PART", "DOC_REF"):
        events[column] = events[column].replace("", pd.NA)
    scenarios = pd.read_csv(FIXTURE_DIR / "tax_scenarios.csv", dtype=str, keep_default_na=False)
    scenarios["DT_REFERENCIA_NORMATIVA"] = pd.to_datetime(scenarios["DT_REFERENCIA_NORMATIVA"]).dt.date
    scenarios["E_BASELINE"] = scenarios["E_BASELINE"].map(lambda value: str(value).lower() == "true")
    scenarios["ATIVO"] = scenarios["ATIVO"].map(lambda value: str(value).lower() == "true")
    parameters = pd.read_csv(FIXTURE_DIR / "tax_parameters.csv", dtype=str, keep_default_na=False)
    for column in ("VIG_INI", "DATA_CONSULTA"):
        parameters[column] = pd.to_datetime(parameters[column]).dt.date
    parameters["VIG_FIM"] = parameters["VIG_FIM"].map(
        lambda value: None if str(value).strip() == "" else pd.to_datetime(value).date()
    )
    tax_context = TaxContext(
        entity_profile=pd.read_csv(FIXTURE_DIR / "entity_profile.csv", dtype=str, keep_default_na=False),
        fiscal_event_attributes=pd.read_csv(FIXTURE_DIR / "fiscal_event_attributes.csv", dtype=str, keep_default_na=False),
        tax_scenarios=scenarios.loc[:, list(TAX_SCENARIO_COLUMNS)],
        tax_parameters=parameters.loc[:, list(TAX_PARAMETER_COLUMNS)],
    )
    analysis = pd.read_csv(FIXTURE_DIR / "analysis_parameters.csv", dtype=str, keep_default_na=False)
    return events.loc[:, list(EVENT_COLUMNS)], tax_context, analysis.loc[:, list(TAX_ANALYSIS_PARAMETER_COLUMNS)]


def test_demo_outputs_exact_numbers() -> None:
    events, tax_context, analysis = load_case()

    report = run_simples_2027_counterfactual_report(events, tax_context, analysis)

    assert report.baseline_scenario_id == "SIMPLES_2027_PURO"
    assert report.alternative_scenario_id == "SIMPLES_2027_HIBRIDO"
    assert tuple(report.scenario_results.columns) == SIMPLES_2027_SCENARIO_RESULT_COLUMNS
    assert tuple(report.comparison_results.columns) == SIMPLES_2027_COMPARISON_COLUMNS
    puro = report.scenario_results.loc[report.scenario_results["ID_CENARIO"] == "SIMPLES_2027_PURO"].iloc[0]
    hibrido = report.scenario_results.loc[report.scenario_results["ID_CENARIO"] == "SIMPLES_2027_HIBRIDO"].iloc[0]
    assert puro["DAS_TOTAL_CENTS"] == 882500
    assert puro["DAS_CBS_CENTS"] == 135287
    assert puro["DAS_IBS_CENTS"] == 1500
    assert puro["DAS_OUTROS_CENTS"] == 745713
    assert hibrido["CBS_DEBITO_REGULAR_CENTS"] == 900000
    assert hibrido["CBS_CREDITO_EMPRESA_POTENCIAL_CENTS"] == 765000
    assert hibrido["CBS_CREDITO_EMPRESA_MODELADO_CENTS"] == 765000
    assert hibrido["CBS_VALOR_LIQUIDO_MODELADO_CENTS"] == 135000
    assert hibrido["IBS_DEBITO_REGULAR_CENTS"] == 10000
    assert hibrido["IBS_CREDITO_EMPRESA_POTENCIAL_CENTS"] == 8500
    assert hibrido["IBS_CREDITO_EMPRESA_MODELADO_CENTS"] == 8500
    assert hibrido["IBS_VALOR_LIQUIDO_MODELADO_CENTS"] == 1500
    assert puro["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"] == 882500
    assert hibrido["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"] == 882213
    assert puro["CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS"] == 94701
    assert puro["CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS"] == 1050
    assert hibrido["CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS"] == 630000
    assert hibrido["CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS"] == 7000
    encargo = report.comparison_results.loc[report.comparison_results["METRICA"] == "ENCARGO_TRIBUTARIO_COMPARAVEL"].iloc[0]
    assert encargo["DELTA_CENTS"] == -287
    assert report.cbs_rate_source == "analysis"
    assert report.cbs_break_even_rate_fraction == Decimal("0.09019166666666666666666666667")


def test_analysis_parameters_are_separate_from_tax_context_and_validated() -> None:
    _, tax_context, analysis = load_case()
    assert not hasattr(tax_context, "tax_analysis_parameters")
    assert validate_tax_analysis_parameters(analysis).ok

    invalid = analysis.copy()
    invalid["FONTE_URL"] = "https://example.invalid"
    assert not validate_tax_analysis_parameters(invalid).ok

    forbidden = analysis.copy()
    forbidden.loc[0, "CHAVE_PARAM"] = "CBS_2027_REGULAR_RATE_FRACTION"
    report = validate_tax_analysis_parameters(forbidden)
    assert not report.ok
    assert any(issue.code == "forbidden_tax_analysis_parameter_key" for issue in report.issues)


def test_fiscal_param_still_requires_provenance() -> None:
    _, tax_context, _ = load_case()
    invalid = tax_context.tax_parameters.copy()
    invalid.loc[0, "FONTE_URL"] = ""
    report = validate_tax_parameters(invalid)
    assert not report.ok
    assert any(issue.code == "missing_tax_parameter_provenance" for issue in report.issues)


def test_fixture_normative_provenance_patch_is_preserved() -> None:
    _, tax_context, _ = load_case()
    params = tax_context.tax_parameters
    cgsn_190 = params.loc[params["FONTE_TITULO"] == "Resolução CGSN 190/2026"]
    assert set(cgsn_190["FONTE_URL"]) == {
        "https://www.in.gov.br/web/dou/-/resolucao-cgsn-n-190-de-4-de-agosto-de-2026-724454118"
    }
    anexo_i = cgsn_190.loc[cgsn_190["DISPOSITIVO"].astype(str).str.contains("Anexo I", regex=False)]
    assert set(anexo_i["VIG_FIM"]) == {date(2028, 12, 31)}

    ibs = params.loc[params["CHAVE_PARAM"] == "IBS_2027_REGULAR_RATE_FRACTION"].iloc[0]
    assert ibs["DISPOSITIVO"] == "art. 344"
    revenue = params.loc[params["CHAVE_PARAM"] == "SIMPLES_2027_REVENUE_RECOGNITION"].iloc[0]
    assert revenue["VIG_FIM"] == date(2027, 6, 30)


def test_analysis_rate_key_is_not_normative_parameter() -> None:
    _, tax_context, _ = load_case()
    invalid = tax_context.tax_parameters.copy()
    row = invalid.iloc[0].copy()
    row["ID_PARAM"] = "PARAM_FORBIDDEN_ANALYSIS_RATE"
    row["CHAVE_PARAM"] = "CBS_2027_ANALYSIS_RATE_FRACTION"
    invalid = pd.concat([invalid, pd.DataFrame([row])], ignore_index=True)
    bad_context = TaxContext(tax_context.entity_profile, tax_context.fiscal_event_attributes, tax_context.tax_scenarios, invalid)
    with pytest.raises(SchemaValidationError):
        select_effective_simples_2027_rules(bad_context, "SIMPLES_2027_PURO")


def test_normative_cbs_rate_takes_precedence_when_present() -> None:
    events, tax_context, analysis = load_case()
    params = tax_context.tax_parameters.copy()
    row = params.iloc[0].copy()
    row["ID_PARAM"] = "PARAM_CBS_2027_REGULAR_RATE"
    row["TRIBUTO"] = "CBS"
    row["CHAVE_PARAM"] = "CBS_2027_REGULAR_RATE_FRACTION"
    row["VALOR"] = "0.08"
    row["TIPO_VALOR"] = "decimal"
    params = pd.concat([params, pd.DataFrame([row])], ignore_index=True)
    context = TaxContext(tax_context.entity_profile, tax_context.fiscal_event_attributes, tax_context.tax_scenarios, params)

    report = run_simples_2027_counterfactual_report(events, context, analysis)

    hibrido = report.scenario_results.loc[report.scenario_results["ID_CENARIO"] == "SIMPLES_2027_HIBRIDO"].iloc[0]
    assert report.cbs_rate_source == "normative"
    assert hibrido["CBS_REGULAR_RATE_FRACTION"] == Decimal("0.08")
    assert hibrido["STATUS_RESULTADO"] == "analitico"


def test_admissibility_requires_acquirer_regime_for_supported_sales() -> None:
    events, tax_context, analysis = load_case()

    b2b_wrong = tax_context.fiscal_event_attributes.copy()
    b2b_wrong.loc[
        (b2b_wrong["ID_EVENTO"] == "S2027_E003") & (b2b_wrong["ATRIBUTO_FISCAL"] == "REGIME_ADQUIRENTE"),
        "VALOR",
    ] = "simples_nacional"
    report = validate_simples_2027_admissibility(
        events,
        TaxContext(tax_context.entity_profile, b2b_wrong, tax_context.tax_scenarios, tax_context.tax_parameters),
        analysis,
    )
    assert any(issue.code == "simples_2027_b2b_acquirer_regime_out_of_scope" for issue in report.issues)

    b2c_wrong = tax_context.fiscal_event_attributes.copy()
    b2c_wrong.loc[
        (b2c_wrong["ID_EVENTO"] == "S2027_E004") & (b2c_wrong["ATRIBUTO_FISCAL"] == "REGIME_ADQUIRENTE"),
        "VALOR",
    ] = "ibs_cbs_regime_regular"
    report = validate_simples_2027_admissibility(
        events,
        TaxContext(tax_context.entity_profile, b2c_wrong, tax_context.tax_scenarios, tax_context.tax_parameters),
        analysis,
    )
    assert any(issue.code == "simples_2027_b2c_acquirer_regime_out_of_scope" for issue in report.issues)

    missing = tax_context.fiscal_event_attributes.loc[
        ~(
            (tax_context.fiscal_event_attributes["ID_EVENTO"] == "S2027_E003")
            & (tax_context.fiscal_event_attributes["ATRIBUTO_FISCAL"] == "REGIME_ADQUIRENTE")
        )
    ].copy()
    report = validate_simples_2027_admissibility(
        events,
        TaxContext(tax_context.entity_profile, missing, tax_context.tax_scenarios, tax_context.tax_parameters),
        analysis,
    )
    assert any(issue.code == "simples_2027_missing_acquirer_regime" for issue in report.issues)


def test_b2b_chain_credit_requires_regular_acquirer_regime() -> None:
    events, tax_context, analysis = load_case()
    attrs = tax_context.fiscal_event_attributes.copy()
    attrs.loc[
        (attrs["ID_EVENTO"] == "S2027_E003") & (attrs["ATRIBUTO_FISCAL"] == "TIPO_CLIENTE"),
        "VALOR",
    ] = "b2c"
    attrs.loc[
        (attrs["ID_EVENTO"] == "S2027_E003") & (attrs["ATRIBUTO_FISCAL"] == "REGIME_ADQUIRENTE"),
        "VALOR",
    ] = "consumidor_final"
    attrs.loc[
        (attrs["ID_EVENTO"] == "S2027_E004") & (attrs["ATRIBUTO_FISCAL"] == "TIPO_CLIENTE"),
        "VALOR",
    ] = "b2b"
    attrs.loc[
        (attrs["ID_EVENTO"] == "S2027_E004") & (attrs["ATRIBUTO_FISCAL"] == "REGIME_ADQUIRENTE"),
        "VALOR",
    ] = "ibs_cbs_regime_regular"
    context = TaxContext(tax_context.entity_profile, attrs, tax_context.tax_scenarios, tax_context.tax_parameters)

    report = run_simples_2027_counterfactual_report(events, context, analysis)

    puro = report.scenario_results.loc[report.scenario_results["ID_CENARIO"] == "SIMPLES_2027_PURO"].iloc[0]
    hibrido = report.scenario_results.loc[report.scenario_results["ID_CENARIO"] == "SIMPLES_2027_HIBRIDO"].iloc[0]
    assert puro["CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS"] == 40586
    assert puro["CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS"] == 450
    assert hibrido["CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS"] == 270000
    assert hibrido["CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS"] == 3000


def test_supported_events_must_be_goods() -> None:
    events, tax_context, analysis = load_case()
    invalid = events.copy()
    invalid.loc[invalid["ID_EVENTO"] == "S2027_E002", "NATUREZA"] = "financeiro"

    report = validate_simples_2027_admissibility(invalid, tax_context, analysis)

    assert any(issue.code == "simples_2027_event_nature_out_of_scope" for issue in report.issues)


def test_admissibility_requires_analysis_hypotheses_only_when_needed() -> None:
    events, tax_context, analysis = load_case()
    empty = analysis.iloc[0:0].copy()
    report = validate_simples_2027_admissibility(events, tax_context, empty)
    assert any(issue.code == "missing_simples_2027_analysis_parameter_key" for issue in report.issues)

    no_alpha = analysis.loc[analysis["CHAVE_PARAM"] != "REGULAR_CREDIT_REALIZATION_FRACTION"].copy()
    report = validate_simples_2027_admissibility(events, tax_context, no_alpha)
    assert any(
        issue.code == "missing_simples_2027_analysis_parameter_key"
        and "REGULAR_CREDIT_REALIZATION_FRACTION" in issue.message
        for issue in report.issues
    )

    no_cbs = analysis.loc[analysis["CHAVE_PARAM"] != "CBS_2027_ANALYSIS_RATE_FRACTION"].copy()
    report = validate_simples_2027_admissibility(events, tax_context, no_cbs)
    assert any(
        issue.code == "missing_simples_2027_analysis_parameter_key"
        and "CBS_2027_ANALYSIS_RATE_FRACTION" in issue.message
        for issue in report.issues
    )

    params = tax_context.tax_parameters.copy()
    row = params.iloc[0].copy()
    row["ID_PARAM"] = "PARAM_CBS_2027_REGULAR_RATE"
    row["TRIBUTO"] = "CBS"
    row["CHAVE_PARAM"] = "CBS_2027_REGULAR_RATE_FRACTION"
    row["VALOR"] = "0.08"
    row["TIPO_VALOR"] = "decimal"
    context_with_normative_cbs = TaxContext(
        tax_context.entity_profile,
        tax_context.fiscal_event_attributes,
        tax_context.tax_scenarios,
        pd.concat([params, pd.DataFrame([row])], ignore_index=True),
    )
    report = validate_simples_2027_admissibility(events, context_with_normative_cbs, no_cbs)
    assert report.ok


def test_admissibility_rejects_invalid_scope_and_scenario_shape() -> None:
    events, tax_context, analysis = load_case()
    no_b2b_attrs = tax_context.fiscal_event_attributes.copy()
    no_b2b_attrs.loc[no_b2b_attrs["ATRIBUTO_FISCAL"] == "TIPO_CLIENTE", "VALOR"] = "b2c"
    bad_context = TaxContext(tax_context.entity_profile, no_b2b_attrs, tax_context.tax_scenarios, tax_context.tax_parameters)
    report = validate_simples_2027_admissibility(events, bad_context, analysis)
    assert any(issue.code == "simples_2027_missing_b2b_sale" for issue in report.issues)

    one_scenario = tax_context.tax_scenarios.iloc[[0]].copy()
    bad_context = TaxContext(tax_context.entity_profile, tax_context.fiscal_event_attributes, one_scenario, tax_context.tax_parameters)
    report = validate_simples_2027_admissibility(events, bad_context, analysis)
    assert any(issue.code == "simples_2027_requires_two_active_scenarios" for issue in report.issues)


def test_purchase_supplier_regular_required_and_alpha_changes_only_modelled_credit() -> None:
    events, tax_context, analysis = load_case()
    bad_attrs = tax_context.fiscal_event_attributes.copy()
    bad_attrs.loc[bad_attrs["ATRIBUTO_FISCAL"] == "REGIME_FORNECEDOR", "VALOR"] = "simples_ibs_cbs_das"
    bad_context = TaxContext(tax_context.entity_profile, bad_attrs, tax_context.tax_scenarios, tax_context.tax_parameters)
    report = validate_simples_2027_admissibility(events, bad_context, analysis)
    assert any(issue.code == "simples_2027_purchase_supplier_out_of_scope" for issue in report.issues)

    half_alpha = analysis.copy()
    half_alpha.loc[half_alpha["CHAVE_PARAM"] == "REGULAR_CREDIT_REALIZATION_FRACTION", "VALOR"] = "0.5"
    result = run_simples_2027_counterfactual_report(events, tax_context, half_alpha)
    hibrido = result.scenario_results.loc[result.scenario_results["ID_CENARIO"] == "SIMPLES_2027_HIBRIDO"].iloc[0]
    assert hibrido["CBS_CREDITO_EMPRESA_POTENCIAL_CENTS"] == 765000
    assert hibrido["CBS_CREDITO_EMPRESA_MODELADO_CENTS"] == 382500
    assert hibrido["IBS_CREDITO_EMPRESA_POTENCIAL_CENTS"] == 8500
    assert hibrido["IBS_CREDITO_EMPRESA_MODELADO_CENTS"] == 4250


def test_band_selection_rbt12_limits_and_effective_rate() -> None:
    events, tax_context, analysis = load_case()
    expected = {
        18000000: Decimal("0.04"),
        36000000: Decimal("0.0565"),
        72000000: Decimal("0.07575"),
        120000000: Decimal("0.08825"),
        360000000: Decimal("0.11875"),
    }
    for rbt12, effective_rate in expected.items():
        entity = tax_context.entity_profile.copy()
        entity.loc[entity["ATRIBUTO"] == "RBT12_CENTS", "VALOR"] = str(rbt12)
        context = TaxContext(entity, tax_context.fiscal_event_attributes, tax_context.tax_scenarios, tax_context.tax_parameters)
        report = run_simples_2027_counterfactual_report(events, context, analysis)
        assert report.scenario_results.iloc[0]["ALIQUOTA_EFETIVA_SIMPLES"] == effective_rate

    for rbt12 in (0, 360000001):
        entity = tax_context.entity_profile.copy()
        entity.loc[entity["ATRIBUTO"] == "RBT12_CENTS", "VALOR"] = str(rbt12)
        context = TaxContext(entity, tax_context.fiscal_event_attributes, tax_context.tax_scenarios, tax_context.tax_parameters)
        report = validate_simples_2027_admissibility(events, context, analysis)
        assert any(issue.code == "simples_2027_rbt12_out_of_scope" for issue in report.issues)


def test_break_even_none_when_denominator_nonpositive_and_inputs_not_mutated() -> None:
    events, tax_context, analysis = load_case()
    events_before = events.copy(deep=True)
    context_before = deepcopy(tax_context)
    high_alpha = analysis.copy()
    high_alpha.loc[high_alpha["CHAVE_PARAM"] == "REGULAR_CREDIT_REALIZATION_FRACTION", "VALOR"] = "1.0"
    large_purchase = events.copy()
    large_purchase.loc[large_purchase["TIPO_EVENTO"] == "compra_mercadoria_a_vista", "VL_EVENTO_CENTS"] = 10000000

    report = run_simples_2027_counterfactual_report(large_purchase, tax_context, high_alpha)

    assert report.cbs_break_even_rate_fraction is None
    pd.testing.assert_frame_equal(events, events_before)
    pd.testing.assert_frame_equal(tax_context.entity_profile, context_before.entity_profile)
    pd.testing.assert_frame_equal(tax_context.fiscal_event_attributes, context_before.fiscal_event_attributes)
    pd.testing.assert_frame_equal(tax_context.tax_scenarios, context_before.tax_scenarios)
    pd.testing.assert_frame_equal(tax_context.tax_parameters, context_before.tax_parameters)
    assert "ID_CENARIO" not in events.columns
    assert "ID_CENARIO" not in tax_context.fiscal_event_attributes.columns
    assert "ID_CENARIO" not in tax_context.entity_profile.columns


def test_no_demo_cbs_analysis_rate_hardcoded_as_normative_source() -> None:
    source = (Path(__file__).resolve().parents[1] / "src" / "accounting_sim" / "tax_simples_2027.py").read_text(encoding="utf-8")
    assert "CBS_2027_ANALYSIS_RATE_FRACTION" in source
    assert 'Decimal("0.09")' not in source
    assert "CBS_RATE = " not in source
