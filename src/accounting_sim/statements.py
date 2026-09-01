"""BP e DRE mínimos derivados do balancete conforme a spec 07."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import pandas as pd
from pandas.testing import assert_frame_equal

from accounting_sim.canonical import (
    BALANCE_SHEET_COLUMNS,
    CHART_OF_ACCOUNTS_COLUMNS,
    INCOME_STATEMENT_COLUMNS,
    STATEMENT_MAPPING_COLUMNS,
    TRIAL_BALANCE_COLUMNS,
    AccountingInvariantError,
    AccountingPeriod,
    AccountNature,
    AccountType,
    DebitCredit,
    ValidationIssue,
    ValidationReport,
)
from accounting_sim.chart_of_accounts import get_account, get_analytic_accounts


FINANCIAL_STATEMENT_SPEC_VERSION = "spec_07_financial_statements_v1"

BALANCE_SHEET_CATALOG: tuple[dict[str, object], ...] = (
    {"ORDEM": 10, "COD_LINHA": "BP_ATIVO", "NIVEL": 1, "TIPO_LINHA": "TOTAL", "LINHA": "Ativo"},
    {"ORDEM": 20, "COD_LINHA": "BP_ATIVO_CIRCULANTE", "NIVEL": 2, "TIPO_LINHA": "SUBTOTAL", "LINHA": "Ativo Circulante"},
    {"ORDEM": 30, "COD_LINHA": "BP_CAIXA", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Caixa"},
    {"ORDEM": 40, "COD_LINHA": "BP_BANCOS", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Bancos Conta Movimento"},
    {"ORDEM": 50, "COD_LINHA": "BP_CLIENTES", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Clientes"},
    {"ORDEM": 60, "COD_LINHA": "BP_ESTOQUES", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Estoques"},
    {"ORDEM": 70, "COD_LINHA": "BP_TRIBUTOS_RECUPERAR", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Tributos a Recuperar"},
    {"ORDEM": 80, "COD_LINHA": "BP_ATIVO_NAO_CIRCULANTE", "NIVEL": 2, "TIPO_LINHA": "SUBTOTAL", "LINHA": "Ativo Não Circulante"},
    {"ORDEM": 90, "COD_LINHA": "BP_IMOBILIZADO", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Imobilizado"},
    {"ORDEM": 100, "COD_LINHA": "BP_DEPRECIACAO_ACUM", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "(-) Depreciação Acumulada"},
    {"ORDEM": 110, "COD_LINHA": "BP_PASSIVO", "NIVEL": 1, "TIPO_LINHA": "TOTAL", "LINHA": "Passivo"},
    {"ORDEM": 120, "COD_LINHA": "BP_PASSIVO_CIRCULANTE", "NIVEL": 2, "TIPO_LINHA": "SUBTOTAL", "LINHA": "Passivo Circulante"},
    {"ORDEM": 130, "COD_LINHA": "BP_FORNECEDORES", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Fornecedores"},
    {"ORDEM": 140, "COD_LINHA": "BP_OBRIG_TRAB", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Obrigações Trabalhistas"},
    {"ORDEM": 150, "COD_LINHA": "BP_OBRIG_TRIB", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Obrigações Tributárias"},
    {"ORDEM": 160, "COD_LINHA": "BP_PASSIVO_NAO_CIRCULANTE", "NIVEL": 2, "TIPO_LINHA": "SUBTOTAL", "LINHA": "Passivo Não Circulante"},
    {"ORDEM": 170, "COD_LINHA": "BP_EMPRESTIMOS", "NIVEL": 3, "TIPO_LINHA": "DETALHE", "LINHA": "Empréstimos e Financiamentos"},
    {"ORDEM": 180, "COD_LINHA": "BP_PATRIMONIO_LIQUIDO", "NIVEL": 1, "TIPO_LINHA": "SUBTOTAL", "LINHA": "Patrimônio Líquido"},
    {"ORDEM": 190, "COD_LINHA": "BP_CAPITAL", "NIVEL": 2, "TIPO_LINHA": "DETALHE", "LINHA": "Capital Social"},
    {"ORDEM": 200, "COD_LINHA": "BP_RESULTADOS_ACUM", "NIVEL": 2, "TIPO_LINHA": "DETALHE", "LINHA": "Resultados Acumulados"},
    {"ORDEM": 210, "COD_LINHA": "BP_RESULTADO_PERIODO", "NIVEL": 2, "TIPO_LINHA": "DERIVADA", "LINHA": "Resultado do Período"},
    {"ORDEM": 220, "COD_LINHA": "BP_TOTAL_PASSIVO_PL", "NIVEL": 1, "TIPO_LINHA": "TOTAL", "LINHA": "Total do Passivo e Patrimônio Líquido"},
)

INCOME_STATEMENT_CATALOG: tuple[dict[str, object], ...] = (
    {"ORDEM": 10, "COD_LINHA": "DRE_RECEITA_VENDAS", "NIVEL": 1, "TIPO_LINHA": "DETALHE", "LINHA": "Receita de Vendas"},
    {"ORDEM": 20, "COD_LINHA": "DRE_RECEITA_LIQUIDA", "NIVEL": 1, "TIPO_LINHA": "SUBTOTAL", "LINHA": "Receita Líquida"},
    {"ORDEM": 30, "COD_LINHA": "DRE_CMV", "NIVEL": 1, "TIPO_LINHA": "DETALHE", "LINHA": "(-) Custo das Mercadorias Vendidas"},
    {"ORDEM": 40, "COD_LINHA": "DRE_RESULTADO_BRUTO", "NIVEL": 1, "TIPO_LINHA": "SUBTOTAL", "LINHA": "Resultado Bruto"},
    {"ORDEM": 50, "COD_LINHA": "DRE_DESP_SALARIOS", "NIVEL": 2, "TIPO_LINHA": "DETALHE", "LINHA": "(-) Salários e Encargos"},
    {"ORDEM": 60, "COD_LINHA": "DRE_DESP_ALUGUEL", "NIVEL": 2, "TIPO_LINHA": "DETALHE", "LINHA": "(-) Aluguéis"},
    {"ORDEM": 70, "COD_LINHA": "DRE_DESP_UTILIDADES", "NIVEL": 2, "TIPO_LINHA": "DETALHE", "LINHA": "(-) Energia e Utilidades"},
    {"ORDEM": 80, "COD_LINHA": "DRE_DESP_DEPRECIACAO", "NIVEL": 2, "TIPO_LINHA": "DETALHE", "LINHA": "(-) Depreciação"},
    {"ORDEM": 90, "COD_LINHA": "DRE_DESP_OPERACIONAIS", "NIVEL": 1, "TIPO_LINHA": "SUBTOTAL", "LINHA": "Despesas Operacionais"},
    {"ORDEM": 100, "COD_LINHA": "DRE_DESP_FINANCEIRA", "NIVEL": 1, "TIPO_LINHA": "DETALHE", "LINHA": "(-) Despesas Financeiras"},
    {"ORDEM": 110, "COD_LINHA": "DRE_RESULTADO_PERIODO", "NIVEL": 1, "TIPO_LINHA": "TOTAL", "LINHA": "Resultado do Período"},
)

BALANCE_SHEET_DETAIL_EXPECTATIONS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "BP_CAIXA": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "BP_BANCOS": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "BP_CLIENTES": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "BP_ESTOQUES": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "BP_TRIBUTOS_RECUPERAR": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "BP_IMOBILIZADO": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "BP_DEPRECIACAO_ACUM": (AccountNature.ASSET.value, DebitCredit.CREDIT.value),
        "BP_FORNECEDORES": (AccountNature.LIABILITY.value, DebitCredit.CREDIT.value),
        "BP_OBRIG_TRAB": (AccountNature.LIABILITY.value, DebitCredit.CREDIT.value),
        "BP_OBRIG_TRIB": (AccountNature.LIABILITY.value, DebitCredit.CREDIT.value),
        "BP_EMPRESTIMOS": (AccountNature.LIABILITY.value, DebitCredit.CREDIT.value),
        "BP_CAPITAL": (AccountNature.EQUITY.value, DebitCredit.CREDIT.value),
        "BP_RESULTADOS_ACUM": (AccountNature.EQUITY.value, DebitCredit.CREDIT.value),
    }
)

INCOME_STATEMENT_DETAIL_EXPECTATIONS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "DRE_RECEITA_VENDAS": (AccountNature.RESULT.value, DebitCredit.CREDIT.value),
        "DRE_CMV": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "DRE_DESP_SALARIOS": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "DRE_DESP_ALUGUEL": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "DRE_DESP_UTILIDADES": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "DRE_DESP_DEPRECIACAO": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "DRE_DESP_FINANCEIRA": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
    }
)


@dataclass(frozen=True)
class FinancialStatements:
    balance_sheet: pd.DataFrame
    income_statement: pd.DataFrame


def build_default_statement_mapping(chart_of_accounts: pd.DataFrame) -> pd.DataFrame:
    analytic = get_analytic_accounts(chart_of_accounts, active_only=True)
    rows: list[dict[str, object]] = []
    for _, account in analytic.iterrows():
        line_code = account["COD_DF"]
        if pd.isna(line_code) or line_code is None or str(line_code).strip() == "":
            line_code = None
        rows.append(
            {
                "COD_CTA": account["COD_CTA"],
                "DEMONSTRACAO": _expected_statement_for_nature(account["COD_NAT"]),
                "COD_LINHA": line_code,
            }
        )
    return pd.DataFrame(rows, columns=STATEMENT_MAPPING_COLUMNS, dtype=object)


def validate_statement_mapping(
    statement_mapping: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    missing_columns = [column for column in STATEMENT_MAPPING_COLUMNS if column not in statement_mapping.columns]
    for column in missing_columns:
        issues.append(ValidationIssue("missing_statement_mapping_column", f"Coluna obrigatória ausente: {column}."))
    missing_chart_columns = [column for column in CHART_OF_ACCOUNTS_COLUMNS if column not in chart_of_accounts.columns]
    for column in missing_chart_columns:
        issues.append(ValidationIssue("missing_chart_column", f"Coluna obrigatória ausente no plano: {column}."))
    if missing_columns or missing_chart_columns:
        return ValidationReport(ok=False, issues=tuple(issues))

    mapping = _normalize_statement_mapping(statement_mapping)
    accounts = mapping["COD_CTA"]
    for _, row in mapping[accounts == ""].iterrows():
        issues.append(ValidationIssue("empty_statement_mapping_account", "COD_CTA não pode ser vazio em MAPEAMENTO_DF."))
    for _, row in mapping[accounts.duplicated(keep=False)].iterrows():
        issues.append(
            ValidationIssue(
                "duplicate_statement_mapping_account",
                f"COD_CTA duplicado em MAPEAMENTO_DF: {row['COD_CTA']}.",
                account_code=row["COD_CTA"],
            )
        )

    active_analytic_codes = set(get_analytic_accounts(chart_of_accounts, active_only=True)["COD_CTA"])
    mapped_codes = set(accounts)
    for code in sorted(active_analytic_codes - mapped_codes):
        issues.append(
            ValidationIssue(
                "missing_statement_mapping_account",
                "Toda conta analítica ativa deve aparecer em MAPEAMENTO_DF.",
                account_code=code,
            )
        )

    bp_catalog = _catalog_by_code(BALANCE_SHEET_CATALOG)
    dre_catalog = _catalog_by_code(INCOME_STATEMENT_CATALOG)
    for _, row in mapping.iterrows():
        account_code = row["COD_CTA"]
        statement = row["DEMONSTRACAO"]
        line_code = row["COD_LINHA"]
        if account_code == "":
            continue
        try:
            account = get_account(chart_of_accounts, account_code)
        except Exception:
            issues.append(ValidationIssue("mapped_statement_account_missing", f"COD_CTA inexistente no plano: {account_code}.", account_code=account_code))
            continue

        if account["IND_CTA"] != AccountType.ANALYTIC.value:
            issues.append(ValidationIssue("mapped_statement_account_not_analytic", "COD_CTA mapeado deve ser conta analítica.", account_code=account_code))
        if not bool(account["ATIVA"]):
            issues.append(ValidationIssue("mapped_statement_account_inactive", "COD_CTA mapeado deve estar ativo.", account_code=account_code))
        if statement not in {"BP", "DRE"}:
            issues.append(ValidationIssue("invalid_statement", "DEMONSTRACAO deve ser BP ou DRE.", account_code=account_code))
            continue

        expected_statement = _expected_statement_for_nature(account["COD_NAT"])
        if expected_statement is None or statement != expected_statement:
            issues.append(
                ValidationIssue(
                    "statement_nature_mismatch",
                    "COD_NAT 01/02/03 deve mapear para BP e COD_NAT 04 deve mapear para DRE.",
                    account_code=account_code,
                )
            )

        catalog = bp_catalog if statement == "BP" else dre_catalog
        if line_code not in catalog:
            issues.append(ValidationIssue("statement_line_missing", f"COD_LINHA inexistente no catálogo {statement}: {line_code}.", account_code=account_code))
            continue
        line = catalog[line_code]
        if line_code == "BP_RESULTADO_PERIODO":
            issues.append(ValidationIssue("statement_result_period_line_mapped", "BP_RESULTADO_PERIODO não pode receber contas.", account_code=account_code))
        if line["TIPO_LINHA"] != "DETALHE":
            issues.append(ValidationIssue("statement_line_not_detail", "COD_LINHA deve ser linha DETALHE.", account_code=account_code))
            continue

        expectations = BALANCE_SHEET_DETAIL_EXPECTATIONS if statement == "BP" else INCOME_STATEMENT_DETAIL_EXPECTATIONS
        expected = expectations.get(line_code)
        if expected is None:
            issues.append(ValidationIssue("statement_line_not_detail", "COD_LINHA deve ser linha DETALHE válida.", account_code=account_code))
            continue
        expected_nature, expected_balance = expected
        if account["COD_NAT"] != expected_nature:
            issues.append(ValidationIssue("statement_line_nature_mismatch", f"COD_LINHA exige COD_NAT {expected_nature}.", account_code=account_code))
        if account["NAT_SALDO_NORMAL"] != expected_balance:
            issues.append(ValidationIssue("statement_line_balance_nature_mismatch", f"COD_LINHA exige NAT_SALDO_NORMAL {expected_balance}.", account_code=account_code))

    return ValidationReport(ok=not issues, issues=tuple(issues))


def synchronize_chart_statement_codes(
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame,
) -> pd.DataFrame:
    report = validate_statement_mapping(statement_mapping, chart_of_accounts)
    if not report.ok:
        details = "; ".join(issue.code for issue in report.issues[:5])
        raise AccountingInvariantError(f"MAPEAMENTO_DF inválido: {details}")

    synchronized = chart_of_accounts.copy(deep=True)
    mapping = _normalize_statement_mapping(statement_mapping).set_index("COD_CTA")["COD_LINHA"].to_dict()
    analytic_codes = set(get_analytic_accounts(synchronized, active_only=True)["COD_CTA"])
    mask = synchronized["COD_CTA"].isin(analytic_codes)
    synchronized.loc[mask, "COD_DF"] = synchronized.loc[mask, "COD_CTA"].map(mapping)
    return synchronized.loc[:, list(CHART_OF_ACCOUNTS_COLUMNS)]


def build_income_statement(
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame | None,
    period: AccountingPeriod,
) -> pd.DataFrame:
    mapping = _validated_mapping_or_default(statement_mapping, chart_of_accounts)
    values = _zero_values(INCOME_STATEMENT_CATALOG)

    joined = _join_trial_chart_mapping(trial_balance, chart_of_accounts, mapping)
    result_rows = joined[joined["DEMONSTRACAO"] == "DRE"]
    for _, row in result_rows.iterrows():
        line_code = row["COD_LINHA"]
        values[line_code] += int(row["VL_CRED_CENTS"]) - int(row["VL_DEB_CENTS"])

    values["DRE_RECEITA_LIQUIDA"] = values["DRE_RECEITA_VENDAS"]
    values["DRE_RESULTADO_BRUTO"] = values["DRE_RECEITA_LIQUIDA"] + values["DRE_CMV"]
    values["DRE_DESP_OPERACIONAIS"] = (
        values["DRE_DESP_SALARIOS"]
        + values["DRE_DESP_ALUGUEL"]
        + values["DRE_DESP_UTILIDADES"]
        + values["DRE_DESP_DEPRECIACAO"]
    )
    values["DRE_RESULTADO_PERIODO"] = (
        values["DRE_RESULTADO_BRUTO"]
        + values["DRE_DESP_OPERACIONAIS"]
        + values["DRE_DESP_FINANCEIRA"]
    )

    return _statement_frame(INCOME_STATEMENT_CATALOG, values, INCOME_STATEMENT_COLUMNS, period=period)


def build_balance_sheet(
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame | None,
    income_statement: pd.DataFrame,
    period: AccountingPeriod,
) -> pd.DataFrame:
    mapping = _validated_mapping_or_default(statement_mapping, chart_of_accounts)
    values = _zero_values(BALANCE_SHEET_CATALOG)

    joined = _join_trial_chart_mapping(trial_balance, chart_of_accounts, mapping)
    patrimonial_rows = joined[joined["DEMONSTRACAO"] == "BP"]
    for _, row in patrimonial_rows.iterrows():
        signed_balance = int(row["VL_SLD_FIN_CENTS"]) if row["IND_DC_FIN"] == DebitCredit.DEBIT.value else -int(row["VL_SLD_FIN_CENTS"])
        contribution = signed_balance if row["COD_NAT"] == AccountNature.ASSET.value else -signed_balance
        values[row["COD_LINHA"]] += contribution

    dre_result = _line_value(income_statement, "DRE_RESULTADO_PERIODO")
    values["BP_RESULTADO_PERIODO"] = dre_result
    values["BP_ATIVO_CIRCULANTE"] = (
        values["BP_CAIXA"]
        + values["BP_BANCOS"]
        + values["BP_CLIENTES"]
        + values["BP_ESTOQUES"]
        + values["BP_TRIBUTOS_RECUPERAR"]
    )
    values["BP_ATIVO_NAO_CIRCULANTE"] = values["BP_IMOBILIZADO"] + values["BP_DEPRECIACAO_ACUM"]
    values["BP_ATIVO"] = values["BP_ATIVO_CIRCULANTE"] + values["BP_ATIVO_NAO_CIRCULANTE"]
    values["BP_PASSIVO_CIRCULANTE"] = values["BP_FORNECEDORES"] + values["BP_OBRIG_TRAB"] + values["BP_OBRIG_TRIB"]
    values["BP_PASSIVO_NAO_CIRCULANTE"] = values["BP_EMPRESTIMOS"]
    values["BP_PASSIVO"] = values["BP_PASSIVO_CIRCULANTE"] + values["BP_PASSIVO_NAO_CIRCULANTE"]
    values["BP_PATRIMONIO_LIQUIDO"] = values["BP_CAPITAL"] + values["BP_RESULTADOS_ACUM"] + values["BP_RESULTADO_PERIODO"]
    values["BP_TOTAL_PASSIVO_PL"] = values["BP_PASSIVO"] + values["BP_PATRIMONIO_LIQUIDO"]

    return _statement_frame(BALANCE_SHEET_CATALOG, values, BALANCE_SHEET_COLUMNS, period=period)


def build_financial_statements(
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame | None,
    period: AccountingPeriod,
) -> FinancialStatements:
    income_statement = build_income_statement(trial_balance, chart_of_accounts, statement_mapping, period)
    balance_sheet = build_balance_sheet(trial_balance, chart_of_accounts, statement_mapping, income_statement, period)
    return FinancialStatements(balance_sheet=balance_sheet, income_statement=income_statement)


def validate_financial_statements(
    financial_statements: FinancialStatements,
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame | None,
    period: AccountingPeriod,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    issues.extend(_validate_columns(financial_statements.balance_sheet, BALANCE_SHEET_COLUMNS, "missing_balance_sheet_column"))
    issues.extend(_validate_columns(financial_statements.income_statement, INCOME_STATEMENT_COLUMNS, "missing_income_statement_column"))
    issues.extend(_validate_columns(trial_balance, TRIAL_BALANCE_COLUMNS, "missing_trial_balance_column"))
    mapping = statement_mapping if statement_mapping is not None else build_default_statement_mapping(chart_of_accounts)
    mapping_report = validate_statement_mapping(mapping, chart_of_accounts)
    if not mapping_report.ok:
        issues.extend(mapping_report.issues)
    if issues:
        return ValidationReport(ok=False, issues=tuple(issues))

    expected_income = build_income_statement(trial_balance, chart_of_accounts, mapping, period)
    expected_balance = build_balance_sheet(trial_balance, chart_of_accounts, mapping, expected_income, period)
    try:
        assert_frame_equal(financial_statements.income_statement, expected_income, check_dtype=False)
    except AssertionError:
        issues.append(ValidationIssue("income_statement_mismatch", "DRE diverge dos movimentos do balancete."))
    try:
        assert_frame_equal(financial_statements.balance_sheet, expected_balance, check_dtype=False)
    except AssertionError:
        issues.append(ValidationIssue("balance_sheet_mismatch", "BP diverge dos saldos finais do balancete e do resultado do período."))

    bp_result = _line_value(financial_statements.balance_sheet, "BP_RESULTADO_PERIODO")
    dre_result = _line_value(financial_statements.income_statement, "DRE_RESULTADO_PERIODO")
    if bp_result != dre_result:
        issues.append(ValidationIssue("period_result_mismatch", "Resultado do período no BP deve coincidir com a DRE."))
    if _line_value(financial_statements.balance_sheet, "BP_ATIVO") != _line_value(financial_statements.balance_sheet, "BP_TOTAL_PASSIVO_PL"):
        issues.append(ValidationIssue("balance_sheet_identity_mismatch", "BP_ATIVO deve ser igual a BP_TOTAL_PASSIVO_PL em centavos."))

    return ValidationReport(ok=not issues, issues=tuple(issues))


def _validated_mapping_or_default(
    statement_mapping: pd.DataFrame | None,
    chart_of_accounts: pd.DataFrame,
) -> pd.DataFrame:
    mapping = build_default_statement_mapping(chart_of_accounts) if statement_mapping is None else statement_mapping
    report = validate_statement_mapping(mapping, chart_of_accounts)
    if not report.ok:
        details = "; ".join(issue.code for issue in report.issues[:5])
        raise AccountingInvariantError(f"MAPEAMENTO_DF inválido: {details}")
    return _normalize_statement_mapping(mapping)


def _join_trial_chart_mapping(
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame,
) -> pd.DataFrame:
    trial = trial_balance.copy()
    chart = chart_of_accounts[["COD_CTA", "COD_NAT", "NAT_SALDO_NORMAL"]].copy()
    mapping = _normalize_statement_mapping(statement_mapping)
    return trial.merge(chart, on="COD_CTA", how="left").merge(mapping, on="COD_CTA", how="left")


def _statement_frame(
    catalog: tuple[dict[str, object], ...],
    values: Mapping[str, int],
    columns: tuple[str, ...],
    *,
    period: AccountingPeriod,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for line in catalog:
        row = dict(line)
        row["VL_CENTS"] = int(values[row["COD_LINHA"]])
        if columns == BALANCE_SHEET_COLUMNS:
            row = {"DT_REF": period.end_date, **row}
        else:
            row = {"DT_INI": period.start_date, "DT_FIN": period.end_date, **row}
        rows.append(row)
    return pd.DataFrame(rows, columns=columns, dtype=object)


def _zero_values(catalog: tuple[dict[str, object], ...]) -> dict[str, int]:
    return {str(row["COD_LINHA"]): 0 for row in catalog}


def _line_value(statement: pd.DataFrame, line_code: str) -> int:
    matches = statement[statement["COD_LINHA"] == line_code]
    if matches.empty:
        raise AccountingInvariantError(f"Linha ausente na demonstração: {line_code}.")
    return int(matches.iloc[0]["VL_CENTS"])


def _catalog_by_code(catalog: tuple[dict[str, object], ...]) -> dict[str, dict[str, object]]:
    return {str(row["COD_LINHA"]): dict(row) for row in catalog}


def _expected_statement_for_nature(cod_nat: str) -> str | None:
    if cod_nat in {AccountNature.ASSET.value, AccountNature.LIABILITY.value, AccountNature.EQUITY.value}:
        return "BP"
    if cod_nat == AccountNature.RESULT.value:
        return "DRE"
    return None


def _normalize_statement_mapping(statement_mapping: pd.DataFrame) -> pd.DataFrame:
    normalized = statement_mapping.copy()
    if set(STATEMENT_MAPPING_COLUMNS).issubset(normalized.columns):
        normalized = normalized.loc[:, list(STATEMENT_MAPPING_COLUMNS)]
    for column in STATEMENT_MAPPING_COLUMNS:
        normalized[column] = normalized[column].map(_clean_required_string)
    return normalized


def _clean_required_string(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _validate_columns(df: pd.DataFrame, columns: tuple[str, ...], issue_code: str) -> tuple[ValidationIssue, ...]:
    return tuple(ValidationIssue(issue_code, f"Coluna obrigatória ausente: {column}.") for column in columns if column not in df.columns)
