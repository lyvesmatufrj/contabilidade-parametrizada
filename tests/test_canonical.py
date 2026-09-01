from datetime import date
from decimal import Decimal

import pytest

import accounting_sim.canonical as canonical
from accounting_sim.canonical import (
    AccountNature,
    AccountType,
    CHART_OF_ACCOUNTS_COLUMNS,
    DebitCredit,
    Origin,
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
