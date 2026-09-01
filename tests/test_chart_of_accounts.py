from datetime import date

import pandas as pd
import pytest

from accounting_sim.canonical import (
    AccountNature,
    AccountType,
    CHART_OF_ACCOUNTS_COLUMNS,
    DebitCredit,
    ReferentialIntegrityError,
)
from accounting_sim.chart_of_accounts import (
    build_default_commercial_chart,
    get_account,
    get_analytic_accounts,
    load_chart_of_accounts,
    save_chart_of_accounts,
    validate_chart_of_accounts,
)


def issue_codes(df: pd.DataFrame) -> set[str]:
    return {issue.code for issue in validate_chart_of_accounts(df).issues}


def test_builder_produces_canonical_columns_in_order():
    df = build_default_commercial_chart(date(2026, 2, 1))
    assert tuple(df.columns) == CHART_OF_ACCOUNTS_COLUMNS
    assert set(df["DT_ALT"]) == {date(2026, 2, 1)}


def test_account_codes_are_unique():
    df = build_default_commercial_chart(date(2026, 1, 1))
    assert df["COD_CTA"].is_unique


def test_complete_template_is_valid():
    df = build_default_commercial_chart(date(2026, 1, 1))
    report = validate_chart_of_accounts(df)
    assert report.ok is True
    assert report.issues == ()


def test_all_template_analytic_accounts_are_level_4():
    df = build_default_commercial_chart(date(2026, 1, 1))
    analytic = get_analytic_accounts(df)
    assert set(analytic["NIVEL"]) == {4}


def test_all_parents_exist():
    df = build_default_commercial_chart(date(2026, 1, 1))
    parent_codes = set(df["COD_CTA_SUP"].dropna())
    assert parent_codes.issubset(set(df["COD_CTA"]))


def test_all_parents_are_synthetic():
    df = build_default_commercial_chart(date(2026, 1, 1))
    parent_codes = set(df["COD_CTA_SUP"].dropna())
    parents = df[df["COD_CTA"].isin(parent_codes)]
    assert set(parents["IND_CTA"]) == {AccountType.SYNTHETIC.value}


def test_no_analytic_account_has_children():
    df = build_default_commercial_chart(date(2026, 1, 1))
    parent_codes = set(df["COD_CTA_SUP"].dropna())
    analytic_codes = set(get_analytic_accounts(df, active_only=False)["COD_CTA"])
    assert parent_codes.isdisjoint(analytic_codes)


def test_absence_of_cycle():
    df = build_default_commercial_chart(date(2026, 1, 1))
    assert "hierarchy_cycle" not in issue_codes(df)


def test_level_transition_is_parent_plus_one():
    df = build_default_commercial_chart(date(2026, 1, 1))
    levels = df.set_index("COD_CTA")["NIVEL"].to_dict()
    for _, row in df.dropna(subset=["COD_CTA_SUP"]).iterrows():
        assert row["NIVEL"] == levels[row["COD_CTA_SUP"]] + 1


def test_cod_nat_belongs_to_enum():
    df = build_default_commercial_chart(date(2026, 1, 1))
    assert set(df["COD_NAT"]).issubset({item.value for item in AccountNature})


def test_balance_nature_belongs_to_debit_credit():
    df = build_default_commercial_chart(date(2026, 1, 1))
    assert set(df["NAT_SALDO_NORMAL"]).issubset({item.value for item in DebitCredit})


def test_active_analytic_accounts_have_statement_mapping():
    df = build_default_commercial_chart(date(2026, 1, 1))
    analytic = get_analytic_accounts(df)
    assert analytic["COD_DF"].notna().all()


def test_get_analytic_accounts_returns_only_analytic_accounts():
    df = build_default_commercial_chart(date(2026, 1, 1))
    analytic = get_analytic_accounts(df)
    assert set(analytic["IND_CTA"]) == {AccountType.ANALYTIC.value}
    assert analytic["ATIVA"].all()


def test_get_account_returns_expected_account():
    df = build_default_commercial_chart(date(2026, 1, 1))
    account = get_account(df, "1.1.01.01")
    assert account["CTA"] == "Caixa"
    assert account["COD_DF"] == "BP_CAIXA"


def test_get_account_missing_raises_clear_error():
    df = build_default_commercial_chart(date(2026, 1, 1))
    with pytest.raises(ReferentialIntegrityError, match="Conta inexistente"):
        get_account(df, "9.9")


def test_save_and_reload_csv_preserves_semantic_keys_and_types(tmp_path):
    df = build_default_commercial_chart(date(2026, 3, 15))
    path = tmp_path / "chart.csv"
    save_chart_of_accounts(df, path)
    reloaded = load_chart_of_accounts(path)

    assert list(reloaded["COD_CTA"]) == list(df["COD_CTA"])
    assert list(reloaded["COD_CTA_SUP"]) == list(df["COD_CTA_SUP"])
    assert set(reloaded["DT_ALT"]) == {date(2026, 3, 15)}
    assert reloaded["NIVEL"].map(type).eq(int).all()
    assert reloaded["ATIVA"].map(type).eq(bool).all()


def test_missing_parent_is_detected():
    df = build_default_commercial_chart(date(2026, 1, 1))
    df.loc[df["COD_CTA"] == "1.1.01.01", "COD_CTA_SUP"] = "1.1.99"
    assert "missing_parent" in issue_codes(df)


def test_analytic_parent_is_detected_with_required_issue_code():
    df = build_default_commercial_chart(date(2026, 1, 1))
    df.loc[df["COD_CTA"] == "1.1.01.02", "COD_CTA_SUP"] = "1.1.01.01"
    assert "analytic_account_has_children" in issue_codes(df)


def test_cycle_is_detected():
    df = build_default_commercial_chart(date(2026, 1, 1))
    df.loc[df["COD_CTA"] == "1.1", "COD_CTA_SUP"] = "1.1.01"
    df.loc[df["COD_CTA"] == "1.1", "NIVEL"] = 4
    assert "hierarchy_cycle" in issue_codes(df)


def test_invalid_level_transition_is_detected():
    df = build_default_commercial_chart(date(2026, 1, 1))
    df.loc[df["COD_CTA"] == "1.1.01.01", "NIVEL"] = 5
    assert "invalid_level_transition" in issue_codes(df)


def test_missing_statement_mapping_is_detected():
    df = build_default_commercial_chart(date(2026, 1, 1))
    df.loc[df["COD_CTA"] == "1.1.01.01", "COD_DF"] = None
    assert "missing_statement_mapping" in issue_codes(df)
