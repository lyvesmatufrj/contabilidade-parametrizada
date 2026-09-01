"""Diário, Livro Razão e balancete derivados da spec 05."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from accounting_sim.canonical import (
    JOURNAL_VIEW_COLUMNS,
    LEDGER_VIEW_COLUMNS,
    TRIAL_BALANCE_COLUMNS,
    AccountingPeriod,
    DebitCredit,
    ValidationIssue,
    ValidationReport,
)
from accounting_sim.chart_of_accounts import account_code_sort_key, get_analytic_accounts, validate_chart_of_accounts


@dataclass(frozen=True)
class LedgerResult:
    journal_view: pd.DataFrame
    ledger_view: pd.DataFrame
    trial_balance: pd.DataFrame


def build_journal(
    journal_entry_headers: pd.DataFrame,
    postings: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> pd.DataFrame:
    headers = journal_entry_headers.copy()
    posting_rows = postings.copy()
    accounts = chart_of_accounts[["COD_CTA", "CTA"]].copy()

    journal = posting_rows.merge(headers[["NUM_LCTO", "DT_LCTO"]], on="NUM_LCTO", how="left")
    journal = journal.merge(accounts, on="COD_CTA", how="left")
    journal = journal.loc[:, list(JOURNAL_VIEW_COLUMNS)]
    return journal.sort_values(["DT_LCTO", "NUM_LCTO", "ID_PARTIDA"], kind="mergesort").reset_index(drop=True)


def build_ledger(
    journal_entry_headers: pd.DataFrame,
    postings: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> pd.DataFrame:
    journal = build_journal(journal_entry_headers, postings, chart_of_accounts)
    ledger = journal.copy()
    ledger["DEBITO_CENTS"] = ledger.apply(
        lambda row: row["VL_DC_CENTS"] if row["IND_DC"] == DebitCredit.DEBIT.value else 0,
        axis=1,
    )
    ledger["CREDITO_CENTS"] = ledger.apply(
        lambda row: row["VL_DC_CENTS"] if row["IND_DC"] == DebitCredit.CREDIT.value else 0,
        axis=1,
    )
    ledger["MOVIMENTO_ASSINADO_CENTS"] = ledger["DEBITO_CENTS"] - ledger["CREDITO_CENTS"]
    ledger["_account_sort_key"] = ledger["COD_CTA"].map(account_code_sort_key)
    ledger = ledger.sort_values(["_account_sort_key", "DT_LCTO", "NUM_LCTO", "ID_PARTIDA"], kind="mergesort")
    ledger["SALDO_ASSINADO_CENTS"] = ledger.groupby("COD_CTA", sort=False)["MOVIMENTO_ASSINADO_CENTS"].cumsum()
    encoded = ledger["SALDO_ASSINADO_CENTS"].map(_encode_signed_balance)
    ledger["SALDO_ABS_CENTS"] = encoded.map(lambda item: item[0])
    ledger["IND_DC_SALDO"] = encoded.map(lambda item: item[1])
    ledger = ledger.loc[:, list(LEDGER_VIEW_COLUMNS)]
    return ledger.reset_index(drop=True)


def build_trial_balance(
    ledger: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    period: AccountingPeriod,
) -> pd.DataFrame:
    ledger_rows = ledger.copy()
    analytic_accounts = get_analytic_accounts(chart_of_accounts, active_only=True)
    rows: list[dict[str, object]] = []

    for _, account in analytic_accounts.iterrows():
        account_code = account["COD_CTA"]
        account_ledger = ledger_rows[ledger_rows["COD_CTA"] == account_code]
        debit_total = int(account_ledger["DEBITO_CENTS"].sum()) if not account_ledger.empty else 0
        credit_total = int(account_ledger["CREDITO_CENTS"].sum()) if not account_ledger.empty else 0
        signed_final = debit_total - credit_total
        final_abs, final_side = _encode_signed_balance(signed_final)
        rows.append(
            {
                "DT_INI": period.start_date,
                "DT_FIN": period.end_date,
                "COD_CTA": account_code,
                "COD_CCUS": None,
                "VL_SLD_INI_CENTS": 0,
                "IND_DC_INI": DebitCredit.DEBIT.value,
                "VL_DEB_CENTS": debit_total,
                "VL_CRED_CENTS": credit_total,
                "VL_SLD_FIN_CENTS": final_abs,
                "IND_DC_FIN": final_side,
            }
        )

    return pd.DataFrame(rows, columns=TRIAL_BALANCE_COLUMNS, dtype=object)


def validate_ledger_trial_balance(
    postings: pd.DataFrame,
    ledger: pd.DataFrame,
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    period: AccountingPeriod,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    issues.extend(_validate_columns(ledger, LEDGER_VIEW_COLUMNS, "missing_ledger_column"))
    issues.extend(_validate_columns(trial_balance, TRIAL_BALANCE_COLUMNS, "missing_trial_balance_column"))
    if issues:
        return ValidationReport(ok=False, issues=tuple(issues))

    chart_report = validate_chart_of_accounts(chart_of_accounts)
    if not chart_report.ok:
        issues.extend(chart_report.issues)
        return ValidationReport(ok=False, issues=tuple(issues))

    analytic_codes = set(get_analytic_accounts(chart_of_accounts, active_only=True)["COD_CTA"])
    for _, row in ledger.iterrows():
        if row["COD_CTA"] not in analytic_codes:
            issues.append(ValidationIssue("ledger_account_not_analytic", "Conta do Razão deve ser analítica ativa.", account_code=row["COD_CTA"]))
        if not (period.start_date <= row["DT_LCTO"] <= period.end_date):
            issues.append(ValidationIssue("ledger_entry_outside_period", "Lançamento no Razão fora do período.", entry_id=row["NUM_LCTO"], posting_id=row["ID_PARTIDA"]))
        if row["MOVIMENTO_ASSINADO_CENTS"] != row["DEBITO_CENTS"] - row["CREDITO_CENTS"]:
            issues.append(ValidationIssue("invalid_signed_movement", "Movimento assinado deve ser débito menos crédito.", posting_id=row["ID_PARTIDA"]))
        expected_abs, expected_side = _encode_signed_balance(row["SALDO_ASSINADO_CENTS"])
        if row["SALDO_ABS_CENTS"] != expected_abs or row["IND_DC_SALDO"] != expected_side:
            issues.append(ValidationIssue("invalid_balance_encoding", "Encoding do saldo assinado inválido.", posting_id=row["ID_PARTIDA"]))

    for account_code, group in ledger.groupby("COD_CTA", sort=False):
        expected = list(group["MOVIMENTO_ASSINADO_CENTS"].cumsum())
        if list(group["SALDO_ASSINADO_CENTS"]) != expected:
            issues.append(ValidationIssue("invalid_running_balance", "Saldo corrido inválido por conta.", account_code=account_code))

    trial_codes = set(trial_balance["COD_CTA"])
    for code in trial_codes:
        if code not in analytic_codes:
            issues.append(ValidationIssue("trial_balance_account_not_analytic", "Balancete deve conter apenas contas analíticas ativas.", account_code=code))
    missing_codes = analytic_codes - trial_codes
    for code in missing_codes:
        issues.append(ValidationIssue("missing_trial_balance_account", "Conta analítica ativa ausente no balancete.", account_code=code))

    ledger_totals = ledger.groupby("COD_CTA", as_index=True)[["DEBITO_CENTS", "CREDITO_CENTS"]].sum()
    for _, row in trial_balance.iterrows():
        code = row["COD_CTA"]
        deb = int(ledger_totals.loc[code, "DEBITO_CENTS"]) if code in ledger_totals.index else 0
        cred = int(ledger_totals.loc[code, "CREDITO_CENTS"]) if code in ledger_totals.index else 0
        if row["VL_DEB_CENTS"] != deb or row["VL_CRED_CENTS"] != cred:
            issues.append(ValidationIssue("trial_balance_movement_mismatch", "Movimentos do balancete divergem do Razão.", account_code=code))
        expected_abs, expected_side = _encode_signed_balance(row["VL_DEB_CENTS"] - row["VL_CRED_CENTS"])
        if row["VL_SLD_INI_CENTS"] != 0 or row["IND_DC_INI"] != DebitCredit.DEBIT.value:
            issues.append(ValidationIssue("invalid_initial_balance", "Saldo inicial do MVP deve ser 0 D.", account_code=code))
        if row["VL_SLD_FIN_CENTS"] != expected_abs or row["IND_DC_FIN"] != expected_side:
            issues.append(ValidationIssue("invalid_trial_balance_final_balance", "Saldo final do balancete inválido.", account_code=code))

    posting_debits = int(postings.loc[postings["IND_DC"] == DebitCredit.DEBIT.value, "VL_DC_CENTS"].sum())
    posting_credits = int(postings.loc[postings["IND_DC"] == DebitCredit.CREDIT.value, "VL_DC_CENTS"].sum())
    trial_debits = int(trial_balance["VL_DEB_CENTS"].sum())
    trial_credits = int(trial_balance["VL_CRED_CENTS"].sum())
    if trial_debits != trial_credits:
        issues.append(ValidationIssue("unbalanced_trial_balance", "Débitos e créditos globais do balancete devem ser iguais."))
    if trial_debits != posting_debits or trial_credits != posting_credits:
        issues.append(ValidationIssue("trial_balance_postings_mismatch", "Totais do balancete divergem de PARTIDAS."))

    return ValidationReport(ok=not issues, issues=tuple(issues))


def _encode_signed_balance(signed_balance_cents: int) -> tuple[int, str]:
    if signed_balance_cents >= 0:
        return abs(signed_balance_cents), DebitCredit.DEBIT.value
    return abs(signed_balance_cents), DebitCredit.CREDIT.value


def _validate_columns(df: pd.DataFrame, columns: tuple[str, ...], issue_code: str) -> tuple[ValidationIssue, ...]:
    return tuple(
        ValidationIssue(issue_code, f"Coluna obrigatória ausente: {column}.")
        for column in columns
        if column not in df.columns
    )
