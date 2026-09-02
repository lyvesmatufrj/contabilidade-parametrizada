from __future__ import annotations

from datetime import date

import pandas as pd

from accounting_sim.canonical import (
    ENTITY_PROFILE_COLUMNS,
    EVENT_COLUMNS,
    FISCAL_EVENT_ATTRIBUTE_COLUMNS,
    TAX_PARAMETER_COLUMNS,
    TAX_SCENARIO_COLUMNS,
    Origin,
    ScalarValueType,
    TaxSourceType,
)
from accounting_sim.events import EVENT_SPEC_VERSION
from accounting_sim.tax_context import (
    TaxContext,
    build_empty_tax_context,
    validate_entity_profile,
    validate_fiscal_event_attributes,
    validate_tax_context,
    validate_tax_parameters,
    validate_tax_scenarios,
)


def events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID_EVENTO": "E001",
                "DT_EVENTO": date(2026, 1, 1),
                "CLASSE_EVENTO": "TR",
                "TIPO_EVENTO": "aporte_capital",
                "DIRECAO": "in",
                "NATUREZA": "financeiro",
                "VL_EVENTO_CENTS": 100000,
                "VL_CUSTO_CENTS": None,
                "MEIO_FINANCEIRO": "caixa",
                "CATEGORIA_DESPESA": None,
                "COD_PART": None,
                "COND_PAGTO": "na",
                "DOC_REF": "DOC001",
                "HIST": "Evento de teste",
                "ORIGEM": Origin.SYNTHETIC.value,
                "SPEC_VERSION": EVENT_SPEC_VERSION,
            }
        ],
        columns=EVENT_COLUMNS,
        dtype=object,
    )


def entity_profile() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID_ENTIDADE": "ENT_TESTE",
                "ATRIBUTO": "porte_teste",
                "VALOR": "pequeno",
                "TIPO_VALOR": ScalarValueType.STRING.value,
                "ORIGEM": Origin.SYNTHETIC.value,
            }
        ],
        columns=ENTITY_PROFILE_COLUMNS,
        dtype=object,
    )


def fiscal_event_attributes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID_EVENTO": "E001",
                "ATRIBUTO_FISCAL": "atributo_teste",
                "VALOR": "valor_teste",
                "TIPO_VALOR": ScalarValueType.STRING.value,
                "ORIGEM": Origin.SYNTHETIC.value,
            }
        ],
        columns=FISCAL_EVENT_ATTRIBUTE_COLUMNS,
        dtype=object,
    )


def tax_parameters() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID_PARAM": "PARAM_TESTE",
                "ID_VERSAO_NORMATIVA": "VERSAO_TESTE",
                "ID_REGRA": "REGRA_TESTE",
                "TRIBUTO": "TRIBUTO_TESTE",
                "CHAVE_PARAM": "parametro_teste",
                "VALOR": "0.1234",
                "TIPO_VALOR": ScalarValueType.DECIMAL.value,
                "TIPO_FONTE": TaxSourceType.NORMATIVE.value,
                "FONTE_TITULO": "Fonte oficial de teste",
                "FONTE_URL": "https://example.invalid/fonte-teste",
                "DISPOSITIVO": "Artigo de teste",
                "VERSAO_NORMA": "VERSAO_NORMA_TESTE",
                "VIG_INI": date(2026, 1, 1),
                "VIG_FIM": None,
                "DATA_CONSULTA": date(2026, 1, 2),
                "VERSAO_REGRA": "REGRA_TESTE_V1",
            }
        ],
        columns=TAX_PARAMETER_COLUMNS,
        dtype=object,
    )


def tax_scenarios() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID_CENARIO": "S0",
                "ID_ENTIDADE": "ENT_TESTE",
                "DESCRICAO": "Baseline artificial",
                "E_BASELINE": True,
                "DT_REFERENCIA_NORMATIVA": date(2026, 1, 1),
                "REGIME_ENTIDADE": "REGIME_TESTE",
                "REGIME_IR": "",
                "REGIME_CONSUMO": "",
                "REGIME_ESPECIAL": "",
                "ID_VERSAO_NORMATIVA": "VERSAO_TESTE",
                "ATIVO": True,
            },
            {
                "ID_CENARIO": "S1",
                "ID_ENTIDADE": "ENT_TESTE",
                "DESCRICAO": "Cenário artificial",
                "E_BASELINE": False,
                "DT_REFERENCIA_NORMATIVA": date(2026, 1, 1),
                "REGIME_ENTIDADE": "REGIME_TESTE_ALTERNATIVO",
                "REGIME_IR": "",
                "REGIME_CONSUMO": "",
                "REGIME_ESPECIAL": "",
                "ID_VERSAO_NORMATIVA": "VERSAO_TESTE",
                "ATIVO": True,
            },
        ],
        columns=TAX_SCENARIO_COLUMNS,
        dtype=object,
    )


def configured_context() -> TaxContext:
    return TaxContext(
        entity_profile=entity_profile(),
        fiscal_event_attributes=fiscal_event_attributes(),
        tax_scenarios=tax_scenarios(),
        tax_parameters=tax_parameters(),
    )


def issue_codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


def test_empty_context_is_valid():
    context = build_empty_tax_context()
    report = validate_tax_context(context, events())
    assert report.ok is True
    assert report.issues == ()


def test_build_empty_tax_context_returns_exact_schemas():
    context = build_empty_tax_context()
    assert tuple(context.entity_profile.columns) == ENTITY_PROFILE_COLUMNS
    assert tuple(context.fiscal_event_attributes.columns) == FISCAL_EVENT_ATTRIBUTE_COLUMNS
    assert tuple(context.tax_scenarios.columns) == TAX_SCENARIO_COLUMNS
    assert tuple(context.tax_parameters.columns) == TAX_PARAMETER_COLUMNS


def test_entity_profile_accepts_long_format():
    assert validate_entity_profile(entity_profile()).ok is True


def test_duplicate_entity_attribute_is_rejected():
    duplicated = pd.concat([entity_profile(), entity_profile()], ignore_index=True)
    assert "duplicate_entity_attribute" in issue_codes(validate_entity_profile(duplicated))


def test_multiple_entities_are_rejected_in_mvp():
    profile = entity_profile()
    second = profile.copy()
    second.loc[0, "ID_ENTIDADE"] = "ENT_OUTRA"
    bad = pd.concat([profile, second], ignore_index=True)
    assert "multiple_entities_not_supported" in issue_codes(validate_entity_profile(bad))


def test_entity_value_type_and_origin_are_validated():
    bad_type = entity_profile()
    bad_type.loc[0, "TIPO_VALOR"] = "float"
    bad_origin = entity_profile()
    bad_origin.loc[0, "ORIGEM"] = "manual"
    assert "invalid_entity_value_type" in issue_codes(validate_entity_profile(bad_type))
    assert "invalid_entity_origin" in issue_codes(validate_entity_profile(bad_origin))


def test_fiscal_event_attributes_accept_empty_table():
    empty = pd.DataFrame(columns=FISCAL_EVENT_ATTRIBUTE_COLUMNS, dtype=object)
    assert validate_fiscal_event_attributes(empty, events()).ok is True


def test_fiscal_event_missing_event_is_rejected():
    attributes = fiscal_event_attributes()
    attributes.loc[0, "ID_EVENTO"] = "E999"
    assert "fiscal_event_missing_event" in issue_codes(validate_fiscal_event_attributes(attributes, events()))


def test_duplicate_fiscal_event_attribute_is_rejected():
    duplicated = pd.concat([fiscal_event_attributes(), fiscal_event_attributes()], ignore_index=True)
    assert "duplicate_fiscal_event_attribute" in issue_codes(validate_fiscal_event_attributes(duplicated, events()))


def test_fiscal_event_attribute_schema_has_no_scenario():
    assert "ID_CENARIO" not in FISCAL_EVENT_ATTRIBUTE_COLUMNS


def test_tax_scenario_id_must_be_unique():
    duplicated = tax_scenarios()
    duplicated.loc[1, "ID_CENARIO"] = "S0"
    assert "duplicate_tax_scenario_id" in issue_codes(validate_tax_scenarios(duplicated, entity_profile(), tax_parameters()))


def test_tax_scenario_without_valid_entity_is_rejected():
    scenarios = tax_scenarios()
    scenarios.loc[0, "ID_ENTIDADE"] = "ENT_INEXISTENTE"
    assert "tax_scenario_invalid_entity" in issue_codes(validate_tax_scenarios(scenarios, entity_profile(), tax_parameters()))


def test_active_tax_scenario_requires_regime_and_normative_version():
    no_regime = tax_scenarios()
    no_regime.loc[0, "REGIME_ENTIDADE"] = ""
    no_version = tax_scenarios()
    no_version.loc[0, "ID_VERSAO_NORMATIVA"] = ""
    assert "active_tax_scenario_missing_regime" in issue_codes(validate_tax_scenarios(no_regime, entity_profile(), tax_parameters()))
    assert "active_tax_scenario_missing_normative_version" in issue_codes(validate_tax_scenarios(no_version, entity_profile(), tax_parameters()))


def test_zero_and_multiple_active_baselines_are_rejected():
    zero = tax_scenarios()
    zero["E_BASELINE"] = False
    multiple = tax_scenarios()
    multiple["E_BASELINE"] = True
    assert "invalid_active_baseline_count" in issue_codes(validate_tax_scenarios(zero, entity_profile(), tax_parameters()))
    assert "invalid_active_baseline_count" in issue_codes(validate_tax_scenarios(multiple, entity_profile(), tax_parameters()))


def test_one_active_baseline_is_accepted():
    assert validate_tax_scenarios(tax_scenarios(), entity_profile(), tax_parameters()).ok is True


def test_missing_normative_version_is_rejected_when_scenarios_exist():
    params = tax_parameters()
    params.loc[0, "ID_VERSAO_NORMATIVA"] = "OUTRA_VERSAO"
    assert "tax_scenario_missing_normative_version" in issue_codes(validate_tax_scenarios(tax_scenarios(), entity_profile(), params))


def test_tax_parameter_id_must_be_unique():
    duplicated = pd.concat([tax_parameters(), tax_parameters()], ignore_index=True)
    assert "duplicate_tax_parameter_id" in issue_codes(validate_tax_parameters(duplicated))


def test_tax_parameter_requires_complete_provenance():
    for column in ("FONTE_TITULO", "FONTE_URL", "DISPOSITIVO", "VERSAO_NORMA", "VIG_INI", "DATA_CONSULTA", "VERSAO_REGRA"):
        params = tax_parameters()
        params.loc[0, column] = None
        assert "missing_tax_parameter_provenance" in issue_codes(validate_tax_parameters(params))


def test_tax_source_type_is_validated():
    params = tax_parameters()
    params.loc[0, "TIPO_FONTE"] = "fonte_invalida"
    assert "invalid_tax_source_type" in issue_codes(validate_tax_parameters(params))


def test_invalid_validity_range_is_rejected():
    params = tax_parameters()
    params.loc[0, "VIG_FIM"] = date(2025, 12, 31)
    assert "invalid_tax_parameter_validity_range" in issue_codes(validate_tax_parameters(params))


def test_null_validity_end_is_accepted():
    params = tax_parameters()
    params.loc[0, "VIG_FIM"] = None
    assert validate_tax_parameters(params).ok is True


def test_decimal_parameter_value_is_text_plus_type_not_float():
    params = tax_parameters()
    assert isinstance(params.loc[0, "VALOR"], str)
    assert params.loc[0, "TIPO_VALOR"] == ScalarValueType.DECIMAL.value
    assert validate_tax_parameters(params).ok is True


def test_float_tax_parameter_value_is_rejected():
    params = tax_parameters()
    params.loc[0, "VALOR"] = 0.1234
    assert "float_tax_parameter_value" in issue_codes(validate_tax_parameters(params))


def test_validate_tax_context_aggregates_component_failures():
    context = configured_context()
    bad_attributes = context.fiscal_event_attributes.copy()
    bad_attributes.loc[0, "ID_EVENTO"] = "E999"
    bad_context = TaxContext(context.entity_profile, bad_attributes, context.tax_scenarios, context.tax_parameters)
    report = validate_tax_context(bad_context, events())
    assert report.ok is False
    assert "fiscal_event_missing_event" in issue_codes(report)


def test_structurally_complete_test_context_is_accepted():
    report = validate_tax_context(configured_context(), events())
    assert report.ok is True
    assert report.issues == ()


def test_entity_profile_schema_forbids_regime_and_scenario_columns():
    bad = entity_profile().assign(ID_CENARIO="S0", REGIME_ENTIDADE="REGIME_TESTE")
    codes = issue_codes(validate_entity_profile(bad))
    assert "forbidden_entity_profile_column" in codes
