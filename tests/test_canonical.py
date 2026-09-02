from datetime import date
from decimal import Decimal

import pytest

import accounting_sim.canonical as canonical
from accounting_sim.canonical import (
    AccountNature,
    AccountType,
    COUNTERFACTUAL_COMPARISON_COLUMNS,
    CHART_OF_ACCOUNTS_COLUMNS,
    DebitCredit,
    ENTITY_PROFILE_COLUMNS,
    Origin,
    FISCAL_EVENT_ATTRIBUTE_COLUMNS,
    ScalarValueType,
    TAX_ASSESSMENT_RESULT_COLUMNS,
    TAX_OPERATION_RESULT_COLUMNS,
    TAX_PARAMETER_COLUMNS,
    TAX_SCENARIO_COLUMNS,
    TaxSourceType,
    ValidationIssue,
    amount_reais_to_cents,
    parse_iso_date,
)


def test_enums_have_canonical_values():
    assert DebitCredit.DEBIT == "D"
    assert DebitCredit.CREDIT == "C"
    assert AccountType.SYNTHETIC == "S"
    assert AccountType.ANALYTIC == "A"
    assert AccountNature.ASSET == "01"
    assert AccountNature.LIABILITY == "02"
    assert AccountNature.EQUITY == "03"
    assert AccountNature.RESULT == "04"
    assert AccountNature.COMPENSATION == "05"
    assert AccountNature.OTHER == "09"
    assert Origin.OBSERVED == "observada"
    assert Origin.SYNTHETIC == "sintética"
    assert Origin.TEMPLATE == "template"
    assert Origin.ADJUSTED == "ajustada"
    assert ScalarValueType.STRING == "str"
    assert ScalarValueType.INTEGER == "int"
    assert ScalarValueType.DECIMAL == "decimal"
    assert ScalarValueType.BOOLEAN == "bool"
    assert ScalarValueType.DATE == "date"
    assert TaxSourceType.NORMATIVE == "norm"
    assert TaxSourceType.REGULATORY == "reg"
    assert TaxSourceType.TECHNICAL == "tec"
    assert TaxSourceType.OPERATIONAL == "oper"


def test_money_conversion_is_deterministic():
    assert amount_reais_to_cents("100.00") == 10000
    assert amount_reais_to_cents("100.10") == 10010
    assert amount_reais_to_cents(Decimal("0.01")) == 1


def test_money_conversion_rejects_float_source():
    with pytest.raises(TypeError):
        amount_reais_to_cents(100.10)  # type: ignore[arg-type]


def test_money_conversion_rejects_more_than_two_decimals():
    with pytest.raises(ValueError):
        amount_reais_to_cents("100.101")


def test_parse_iso_date():
    assert parse_iso_date("2026-01-31") == date(2026, 1, 31)
    assert parse_iso_date(date(2026, 1, 31)) == date(2026, 1, 31)


def test_chart_columns_are_immutable_and_canonical():
    assert isinstance(CHART_OF_ACCOUNTS_COLUMNS, tuple)
    assert CHART_OF_ACCOUNTS_COLUMNS == (
        "DT_ALT",
        "COD_NAT",
        "IND_CTA",
        "NIVEL",
        "COD_CTA",
        "COD_CTA_SUP",
        "CTA",
        "NAT_SALDO_NORMAL",
        "COD_DF",
        "ATIVA",
        "ORIGEM",
    )


def test_forbidden_public_aliases_are_not_introduced():
    forbidden_aliases = {"L_t", "R_t", "ledger", "r_t", "E_j", "z_t"}
    assert forbidden_aliases.isdisjoint(set(dir(canonical)))


def test_tax_interface_schemas_are_tuples_and_canonical():
    assert isinstance(ENTITY_PROFILE_COLUMNS, tuple)
    assert ENTITY_PROFILE_COLUMNS == ("ID_ENTIDADE", "ATRIBUTO", "VALOR", "TIPO_VALOR", "ORIGEM")
    assert FISCAL_EVENT_ATTRIBUTE_COLUMNS == ("ID_EVENTO", "ATRIBUTO_FISCAL", "VALOR", "TIPO_VALOR", "ORIGEM")
    assert TAX_SCENARIO_COLUMNS == (
        "ID_CENARIO",
        "ID_ENTIDADE",
        "DESCRICAO",
        "E_BASELINE",
        "DT_REFERENCIA_NORMATIVA",
        "REGIME_ENTIDADE",
        "REGIME_IR",
        "REGIME_CONSUMO",
        "REGIME_ESPECIAL",
        "ID_VERSAO_NORMATIVA",
        "ATIVO",
    )
    assert TAX_PARAMETER_COLUMNS == (
        "ID_PARAM",
        "ID_VERSAO_NORMATIVA",
        "ID_REGRA",
        "TRIBUTO",
        "CHAVE_PARAM",
        "VALOR",
        "TIPO_VALOR",
        "TIPO_FONTE",
        "FONTE_TITULO",
        "FONTE_URL",
        "DISPOSITIVO",
        "VERSAO_NORMA",
        "VIG_INI",
        "VIG_FIM",
        "DATA_CONSULTA",
        "VERSAO_REGRA",
    )


def test_reserved_tax_result_schemas_are_canonical_but_not_public_aliases():
    assert TAX_OPERATION_RESULT_COLUMNS == (
        "ID_CENARIO",
        "ID_EVENTO",
        "TRIBUTO",
        "INCIDE",
        "BASE_CENTS",
        "ALIQUOTA",
        "CREDITO_CENTS",
        "DEBITO_CENTS",
        "VERSAO_REGRA",
    )
    assert TAX_ASSESSMENT_RESULT_COLUMNS == (
        "ID_CENARIO",
        "TRIBUTO",
        "S_APUR_CENTS",
        "T_RECOLHER_CENTS",
        "P_CASH_CENTS",
        "E_DRE_CENTS",
        "C_SALDO_CENTS",
        "VERSAO_REGRA",
    )
    assert COUNTERFACTUAL_COMPARISON_COLUMNS == (
        "ID_CENARIO_BASE",
        "ID_CENARIO",
        "TRIBUTO",
        "DELTA_S_APUR_CENTS",
        "DELTA_T_RECOLHER_CENTS",
        "DELTA_P_CASH_CENTS",
        "DELTA_E_DRE_CENTS",
        "DELTA_C_SALDO_CENTS",
    )


def test_validation_issue_preserves_existing_fields_and_adds_tax_traceability():
    issue = ValidationIssue("code", "msg")
    assert issue.account_code is None
    assert issue.event_id is None
    assert issue.entry_id is None
    assert issue.posting_id is None
    assert issue.entity_id is None
    assert issue.scenario_id is None
    assert issue.tax_param_id is None
