from __future__ import annotations

from datetime import date

import pandas as pd
from pandas.testing import assert_frame_equal

from accounting_sim.account_mapping import build_default_account_role_mapping
from accounting_sim.canonical import (
    BALANCE_SHEET_COLUMNS,
    INCOME_STATEMENT_COLUMNS,
    STATEMENT_MAPPING_COLUMNS,
    TRIAL_BALANCE_COLUMNS,
    AccountingPeriod,
    DebitCredit,
    EventClass,
    EventDirection,
    EventNature,
    EventType,
    Origin,
    PaymentTerm,
    SimulationConfig,
)
from accounting_sim.chart_of_accounts import build_default_commercial_chart
from accounting_sim.events import EVENT_SPEC_VERSION
from accounting_sim.ledger import build_ledger, build_trial_balance
from accounting_sim.posting import post_events
from accounting_sim.statements import (
    BALANCE_SHEET_CATALOG,
    FINANCIAL_STATEMENT_SPEC_VERSION,
    INCOME_STATEMENT_CATALOG,
    FinancialStatements,
    build_balance_sheet,
    build_default_statement_mapping,
    build_financial_statements,
    build_income_statement,
    synchronize_chart_statement_codes,
    validate_financial_statements,
    validate_statement_mapping,
)


PERIOD = AccountingPeriod(date(2026, 1, 1), date(2026, 1, 31))
CONFIG = SimulationConfig(
    simulation_id="SIM_STATEMENTS",
    start_date=PERIOD.start_date,
    end_date=PERIOD.end_date,
    currency="BRL",
    seed=0,
    scenario_name="statements",
    spec_version=FINANCIAL_STATEMENT_SPEC_VERSION,
)


def chart() -> pd.DataFrame:
    return build_default_commercial_chart(PERIOD.start_date)


def canonical_events() -> pd.DataFrame:
    rows = [
        event_row("E001", date(2026, 1, 1), EventType.CAPITAL_CONTRIBUTION, 10000000),
        event_row("E002", date(2026, 1, 2), EventType.PURCHASE_CASH, 3000000),
        event_row("E003", date(2026, 1, 3), EventType.SALE_CREDIT, 5000000, 2000000),
        event_row("E004", date(2026, 1, 4), EventType.CUSTOMER_RECEIPT, 3000000),
    ]
    return pd.DataFrame(rows, dtype=object)


def event_row(
    event_id: str,
    event_date: date,
    event_type: EventType,
    amount: int,
    cost: int | None = None,
    medium: str | None = "caixa",
) -> dict[str, object]:
    direction = {
        EventType.CAPITAL_CONTRIBUTION: EventDirection.IN.value,
        EventType.PURCHASE_CASH: EventDirection.IN.value,
        EventType.SALE_CREDIT: EventDirection.OUT.value,
        EventType.CUSTOMER_RECEIPT: EventDirection.IN.value,
    }[event_type]
    nature = {
        EventType.PURCHASE_CASH: EventNature.GOOD.value,
        EventType.SALE_CREDIT: EventNature.GOOD.value,
    }.get(event_type, EventNature.FINANCIAL.value)
    payment_term = {
        EventType.PURCHASE_CASH: PaymentTerm.CASH.value,
        EventType.SALE_CREDIT: PaymentTerm.CREDIT.value,
    }.get(event_type, PaymentTerm.NA.value)
    if event_type is EventType.SALE_CREDIT:
        medium = None
    return {
        "ID_EVENTO": event_id,
        "DT_EVENTO": event_date,
        "CLASSE_EVENTO": EventClass.TRANSACTION.value,
        "TIPO_EVENTO": event_type.value,
        "DIRECAO": direction,
        "NATUREZA": nature,
        "VL_EVENTO_CENTS": amount,
        "VL_CUSTO_CENTS": cost,
        "MEIO_FINANCEIRO": medium,
        "CATEGORIA_DESPESA": None,
        "COD_PART": "PART001",
        "COND_PAGTO": payment_term,
        "DOC_REF": f"DOC-{event_id}",
        "HIST": event_type.value,
        "ORIGEM": Origin.SYNTHETIC.value,
        "SPEC_VERSION": EVENT_SPEC_VERSION,
    }


def core():
    chart_df = chart()
    events = canonical_events()
    posting_result = post_events(events, chart_df, CONFIG, account_role_mapping=build_default_account_role_mapping())
    ledger = build_ledger(posting_result.journal_entry_headers, posting_result.postings, chart_df)
    trial_balance = build_trial_balance(ledger, chart_df, PERIOD)
    return chart_df, events, posting_result, ledger, trial_balance


def mapping() -> pd.DataFrame:
    return build_default_statement_mapping(chart())


def issue_codes(statement_mapping: pd.DataFrame, chart_of_accounts: pd.DataFrame | None = None) -> set[str]:
    report = validate_statement_mapping(statement_mapping, chart() if chart_of_accounts is None else chart_of_accounts)
    return {issue.code for issue in report.issues}


def line_value(statement: pd.DataFrame, code: str) -> int:
    return int(statement.loc[statement["COD_LINHA"] == code, "VL_CENTS"].iloc[0])


def account_row(trial_balance: pd.DataFrame, account_code: str) -> pd.Series:
    return trial_balance.loc[trial_balance["COD_CTA"] == account_code].iloc[0]


def test_statement_mapping_columns_are_canonical():
    assert STATEMENT_MAPPING_COLUMNS == ("COD_CTA", "DEMONSTRACAO", "COD_LINHA")
    assert tuple(mapping().columns) == STATEMENT_MAPPING_COLUMNS


def test_statement_catalogs_have_expected_shapes_and_result_version():
    assert len(BALANCE_SHEET_CATALOG) == 22
    assert len(INCOME_STATEMENT_CATALOG) == 11
    assert FINANCIAL_STATEMENT_SPEC_VERSION == "spec_07_financial_statements_v1"


def test_default_statement_mapping_is_built_from_cod_df_fallback():
    chart_df = chart()
    default = build_default_statement_mapping(chart_df)
    assert default.loc[default["COD_CTA"] == "1.1.01.01", ["DEMONSTRACAO", "COD_LINHA"]].iloc[0].tolist() == ["BP", "BP_CAIXA"]
    assert default.loc[default["COD_CTA"] == "4.1.01.01", ["DEMONSTRACAO", "COD_LINHA"]].iloc[0].tolist() == ["DRE", "DRE_RECEITA_VENDAS"]
    assert validate_statement_mapping(default, chart_df).ok is True


def test_statement_mapping_must_have_unique_cod_cta():
    duplicated = pd.concat([mapping(), mapping().iloc[[0]]], ignore_index=True)
    assert "duplicate_statement_mapping_account" in issue_codes(duplicated)


def test_statement_mapping_must_cover_every_active_analytic_account():
    missing = mapping()[mapping()["COD_CTA"] != "1.1.01.01"]
    assert "missing_statement_mapping_account" in issue_codes(missing)


def test_statement_mapping_rejects_missing_account():
    bad = mapping()
    bad.loc[bad["COD_CTA"] == "1.1.01.01", "COD_CTA"] = "9.9.99"
    assert "mapped_statement_account_missing" in issue_codes(bad)


def test_statement_mapping_rejects_synthetic_account():
    bad = mapping()
    bad.loc[bad["COD_CTA"] == "1.1.01.01", "COD_CTA"] = "1.1.01"
    assert "mapped_statement_account_not_analytic" in issue_codes(bad)


def test_statement_mapping_rejects_inactive_account():
    chart_df = chart()
    chart_df.loc[chart_df["COD_CTA"] == "1.1.01.01", "ATIVA"] = False
    assert "mapped_statement_account_inactive" in issue_codes(mapping(), chart_df)


def test_statement_mapping_rejects_invalid_statement_name():
    bad = mapping()
    bad.loc[bad["COD_CTA"] == "1.1.01.01", "DEMONSTRACAO"] = "DFC"
    assert "invalid_statement" in issue_codes(bad)


def test_statement_mapping_rejects_nature_mismatch_between_account_and_statement():
    bad = mapping()
    bad.loc[bad["COD_CTA"] == "1.1.01.01", ["DEMONSTRACAO", "COD_LINHA"]] = ["DRE", "DRE_RECEITA_VENDAS"]
    assert "statement_nature_mismatch" in issue_codes(bad)


def test_statement_mapping_rejects_subtotal_total_and_result_period_lines():
    subtotal = mapping()
    subtotal.loc[subtotal["COD_CTA"] == "1.1.01.01", "COD_LINHA"] = "BP_ATIVO_CIRCULANTE"
    total = mapping()
    total.loc[total["COD_CTA"] == "1.1.01.01", "COD_LINHA"] = "BP_ATIVO"
    derived = mapping()
    derived.loc[derived["COD_CTA"] == "1.1.01.01", "COD_LINHA"] = "BP_RESULTADO_PERIODO"
    assert "statement_line_not_detail" in issue_codes(subtotal)
    assert "statement_line_not_detail" in issue_codes(total)
    assert "statement_result_period_line_mapped" in issue_codes(derived)


def test_statement_mapping_rejects_line_nature_and_normal_balance_mismatch():
    nature_bad = mapping()
    nature_bad.loc[nature_bad["COD_CTA"] == "1.1.01.01", "COD_LINHA"] = "BP_FORNECEDORES"
    balance_bad = mapping()
    balance_bad.loc[balance_bad["COD_CTA"] == "1.2.01.02", "COD_LINHA"] = "BP_IMOBILIZADO"
    assert "statement_line_nature_mismatch" in issue_codes(nature_bad)
    assert "statement_line_balance_nature_mismatch" in issue_codes(balance_bad)


def test_multiple_accounts_can_map_to_same_detail_line():
    compatible = mapping()
    compatible.loc[compatible["COD_CTA"] == "1.1.01.02", "COD_LINHA"] = "BP_CAIXA"
    assert validate_statement_mapping(compatible, chart()).ok is True


def test_synchronize_chart_statement_codes_overwrites_cod_df_mirror():
    chart_df = chart()
    chart_df.loc[chart_df["COD_CTA"] == "1.1.01.01", "COD_DF"] = "BP_BANCOS"
    synchronized = synchronize_chart_statement_codes(chart_df, mapping())
    assert synchronized.loc[synchronized["COD_CTA"] == "1.1.01.01", "COD_DF"].iloc[0] == "BP_CAIXA"


def test_income_statement_columns_are_canonical():
    chart_df, _, _, _, trial_balance = core()
    dre = build_income_statement(trial_balance, chart_df, mapping(), PERIOD)
    assert tuple(dre.columns) == INCOME_STATEMENT_COLUMNS


def test_canonical_income_statement_values():
    chart_df, _, _, _, trial_balance = core()
    dre = build_income_statement(trial_balance, chart_df, mapping(), PERIOD)
    assert line_value(dre, "DRE_RECEITA_VENDAS") == 5000000
    assert line_value(dre, "DRE_CMV") == -2000000
    assert line_value(dre, "DRE_RESULTADO_BRUTO") == 3000000
    assert line_value(dre, "DRE_RESULTADO_PERIODO") == 3000000


def test_income_statement_uses_period_movements_not_final_balance():
    chart_df, _, _, _, trial_balance = core()
    changed = trial_balance.copy()
    changed.loc[changed["COD_CTA"] == "4.1.01.01", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]] = [999999, DebitCredit.DEBIT.value]
    dre = build_income_statement(changed, chart_df, mapping(), PERIOD)
    assert line_value(dre, "DRE_RECEITA_VENDAS") == 5000000


def test_balance_sheet_columns_are_canonical():
    chart_df, _, _, _, trial_balance = core()
    dre = build_income_statement(trial_balance, chart_df, mapping(), PERIOD)
    bp = build_balance_sheet(trial_balance, chart_df, mapping(), dre, PERIOD)
    assert tuple(bp.columns) == BALANCE_SHEET_COLUMNS


def test_balance_sheet_uses_final_balance_not_period_movements():
    chart_df, _, _, _, trial_balance = core()
    changed = trial_balance.copy()
    changed.loc[changed["COD_CTA"] == "1.1.01.01", ["VL_DEB_CENTS", "VL_CRED_CENTS", "VL_SLD_FIN_CENTS", "IND_DC_FIN"]] = [
        0,
        0,
        123456,
        DebitCredit.DEBIT.value,
    ]
    dre = build_income_statement(changed, chart_df, mapping(), PERIOD)
    bp = build_balance_sheet(changed, chart_df, mapping(), dre, PERIOD)
    assert line_value(bp, "BP_CAIXA") == 123456


def test_contra_asset_credit_balance_appears_negative():
    chart_df, _, _, _, trial_balance = core()
    changed = trial_balance.copy()
    changed.loc[changed["COD_CTA"] == "1.2.01.02", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]] = [250000, DebitCredit.CREDIT.value]
    dre = build_income_statement(changed, chart_df, mapping(), PERIOD)
    bp = build_balance_sheet(changed, chart_df, mapping(), dre, PERIOD)
    assert line_value(bp, "BP_DEPRECIACAO_ACUM") == -250000


def test_credit_liability_balance_appears_positive():
    chart_df, _, _, _, trial_balance = core()
    changed = trial_balance.copy()
    changed.loc[changed["COD_CTA"] == "2.1.01.01", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]] = [700000, DebitCredit.CREDIT.value]
    dre = build_income_statement(changed, chart_df, mapping(), PERIOD)
    bp = build_balance_sheet(changed, chart_df, mapping(), dre, PERIOD)
    assert line_value(bp, "BP_FORNECEDORES") == 700000


def test_period_loss_reduces_equity():
    chart_df, _, _, _, trial_balance = core()
    changed = trial_balance.copy()
    changed.loc[changed["COD_CTA"] == "4.1.01.01", ["VL_DEB_CENTS", "VL_CRED_CENTS", "VL_SLD_FIN_CENTS", "IND_DC_FIN"]] = [0, 0, 0, DebitCredit.DEBIT.value]
    changed.loc[changed["COD_CTA"] == "4.3.01.02", ["VL_DEB_CENTS", "VL_CRED_CENTS", "VL_SLD_FIN_CENTS", "IND_DC_FIN"]] = [12000000, 0, 12000000, DebitCredit.DEBIT.value]
    dre = build_income_statement(changed, chart_df, mapping(), PERIOD)
    bp = build_balance_sheet(changed, chart_df, mapping(), dre, PERIOD)
    assert line_value(dre, "DRE_RESULTADO_PERIODO") == -14000000
    assert line_value(bp, "BP_PATRIMONIO_LIQUIDO") == -4000000


def test_canonical_balance_sheet_values_and_identity():
    chart_df, _, _, _, trial_balance = core()
    statements = build_financial_statements(trial_balance, chart_df, mapping(), PERIOD)
    bp = statements.balance_sheet
    assert line_value(bp, "BP_ATIVO") == 13000000
    assert line_value(bp, "BP_CAPITAL") == 10000000
    assert line_value(bp, "BP_RESULTADO_PERIODO") == 3000000
    assert line_value(bp, "BP_PATRIMONIO_LIQUIDO") == 13000000
    assert line_value(bp, "BP_TOTAL_PASSIVO_PL") == 13000000
    assert line_value(bp, "BP_ATIVO") == line_value(bp, "BP_TOTAL_PASSIVO_PL")


def test_income_statement_result_is_exactly_balance_sheet_period_result():
    chart_df, _, _, _, trial_balance = core()
    statements = build_financial_statements(trial_balance, chart_df, mapping(), PERIOD)
    assert line_value(statements.income_statement, "DRE_RESULTADO_PERIODO") == line_value(statements.balance_sheet, "BP_RESULTADO_PERIODO")


def test_build_financial_statements_accepts_default_cod_df_fallback():
    chart_df, _, _, _, trial_balance = core()
    statements = build_financial_statements(trial_balance, chart_df, None, PERIOD)
    assert line_value(statements.income_statement, "DRE_RESULTADO_PERIODO") == 3000000
    assert line_value(statements.balance_sheet, "BP_ATIVO") == 13000000


def test_building_statements_does_not_create_closing_entries_or_mutate_postings():
    chart_df, _, posting_result, _, trial_balance = core()
    postings_before = posting_result.postings.copy(deep=True)
    headers_before = posting_result.journal_entry_headers.copy(deep=True)
    _ = build_financial_statements(trial_balance, chart_df, mapping(), PERIOD)
    assert_frame_equal(posting_result.postings, postings_before)
    assert_frame_equal(posting_result.journal_entry_headers, headers_before)
    assert set(posting_result.journal_entry_headers["IND_LCTO"]) == {"N"}


def test_generating_statements_does_not_mutate_trial_balance():
    chart_df, _, _, _, trial_balance = core()
    before = trial_balance.copy(deep=True)
    _ = build_financial_statements(trial_balance, chart_df, mapping(), PERIOD)
    assert_frame_equal(trial_balance, before)


def test_validate_financial_statements_accepts_canonical_case():
    chart_df, _, _, _, trial_balance = core()
    statements = build_financial_statements(trial_balance, chart_df, mapping(), PERIOD)
    report = validate_financial_statements(statements, trial_balance, chart_df, mapping(), PERIOD)
    assert report.ok is True
    assert report.issues == ()


def test_validate_financial_statements_rejects_manual_dre_change():
    chart_df, _, _, _, trial_balance = core()
    statements = build_financial_statements(trial_balance, chart_df, mapping(), PERIOD)
    bad_dre = statements.income_statement.copy()
    bad_dre.loc[bad_dre["COD_LINHA"] == "DRE_RESULTADO_PERIODO", "VL_CENTS"] = 1
    report = validate_financial_statements(FinancialStatements(statements.balance_sheet, bad_dre), trial_balance, chart_df, mapping(), PERIOD)
    assert "income_statement_mismatch" in {issue.code for issue in report.issues}


def test_changing_statement_mapping_changes_presentation_not_posting():
    chart_df, events, _, _, trial_balance = core()
    remapped = mapping()
    remapped.loc[remapped["COD_CTA"] == "1.1.01.01", "COD_LINHA"] = "BP_BANCOS"
    statements = build_financial_statements(trial_balance, chart_df, remapped, PERIOD)
    posting_result = post_events(events, chart_df, CONFIG, account_role_mapping=build_default_account_role_mapping())
    assert line_value(statements.balance_sheet, "BP_CAIXA") == 0
    assert line_value(statements.balance_sheet, "BP_BANCOS") == 10000000
    assert "1.1.01.01" in set(posting_result.postings["COD_CTA"])


def test_statement_output_is_deterministic_for_same_inputs():
    chart_df, _, _, _, trial_balance = core()
    left = build_financial_statements(trial_balance, chart_df, mapping(), PERIOD)
    right = build_financial_statements(trial_balance, chart_df, mapping(), PERIOD)
    assert_frame_equal(left.balance_sheet, right.balance_sheet)
    assert_frame_equal(left.income_statement, right.income_statement)


def test_trial_balance_schema_is_preserved_by_statement_consumption():
    _, _, _, _, trial_balance = core()
    assert tuple(trial_balance.columns) == TRIAL_BALANCE_COLUMNS
