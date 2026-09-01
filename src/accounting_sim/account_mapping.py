"""Mapeamento parametrizado de papéis contábeis para contas analíticas."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

import pandas as pd

from accounting_sim.canonical import (
    ACCOUNT_ROLE_MAPPING_COLUMNS,
    AccountingInvariantError,
    AccountNature,
    AccountType,
    DebitCredit,
    ReferentialIntegrityError,
    ValidationIssue,
    ValidationReport,
)
from accounting_sim.chart_of_accounts import validate_chart_of_accounts
from accounting_sim.chart_of_accounts import get_account


REQUIRED_ACCOUNT_ROLES: tuple[str, ...] = (
    "caixa",
    "banco",
    "clientes",
    "estoques",
    "depreciacao_acumulada",
    "fornecedores",
    "capital_social",
    "receita_vendas",
    "cmv",
    "despesa_salarios",
    "despesa_aluguel",
    "despesa_utilidades",
    "despesa_depreciacao",
    "despesa_juros",
)

OPTIONAL_ACCOUNT_ROLES: tuple[str, ...] = ("imobilizado",)

DEFAULT_ACCOUNT_ROLE_MAP: Mapping[str, str] = MappingProxyType(
    {
        "caixa": "1.1.01.01",
        "banco": "1.1.01.02",
        "clientes": "1.1.02.01",
        "estoques": "1.1.03.01",
        "imobilizado": "1.2.01.01",
        "depreciacao_acumulada": "1.2.01.02",
        "fornecedores": "2.1.01.01",
        "capital_social": "3.1.01.01",
        "receita_vendas": "4.1.01.01",
        "cmv": "4.2.01.01",
        "despesa_salarios": "4.3.01.01",
        "despesa_aluguel": "4.3.01.02",
        "despesa_utilidades": "4.3.01.03",
        "despesa_depreciacao": "4.3.01.04",
        "despesa_juros": "4.3.02.01",
    }
)

ACCOUNT_ROLE_EXPECTATIONS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "caixa": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "banco": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "clientes": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "estoques": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "imobilizado": (AccountNature.ASSET.value, DebitCredit.DEBIT.value),
        "depreciacao_acumulada": (AccountNature.ASSET.value, DebitCredit.CREDIT.value),
        "fornecedores": (AccountNature.LIABILITY.value, DebitCredit.CREDIT.value),
        "capital_social": (AccountNature.EQUITY.value, DebitCredit.CREDIT.value),
        "receita_vendas": (AccountNature.RESULT.value, DebitCredit.CREDIT.value),
        "cmv": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "despesa_salarios": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "despesa_aluguel": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "despesa_utilidades": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "despesa_depreciacao": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
        "despesa_juros": (AccountNature.RESULT.value, DebitCredit.DEBIT.value),
    }
)


def build_default_account_role_mapping() -> pd.DataFrame:
    rows = [
        {"PAPEL_CONTABIL": role, "COD_CTA": account_code}
        for role, account_code in DEFAULT_ACCOUNT_ROLE_MAP.items()
    ]
    return pd.DataFrame(rows, columns=ACCOUNT_ROLE_MAPPING_COLUMNS, dtype=object)


def validate_account_role_mapping(
    mapping: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    missing_columns = [column for column in ACCOUNT_ROLE_MAPPING_COLUMNS if column not in mapping.columns]
    for column in missing_columns:
        issues.append(ValidationIssue("missing_account_role_mapping_column", f"Coluna obrigatória ausente: {column}."))
    if missing_columns:
        return ValidationReport(ok=False, issues=tuple(issues))

    chart_report = validate_chart_of_accounts(chart_of_accounts)
    if not chart_report.ok:
        issues.extend(chart_report.issues)
        return ValidationReport(ok=False, issues=tuple(issues))

    normalized_mapping = _normalize_account_role_mapping(mapping)
    roles = normalized_mapping["PAPEL_CONTABIL"]
    for _, row in normalized_mapping[roles == ""].iterrows():
        issues.append(ValidationIssue("empty_account_role", "PAPEL_CONTABIL não pode ser vazio."))

    for _, row in normalized_mapping[roles.duplicated(keep=False)].iterrows():
        issues.append(
            ValidationIssue(
                "duplicate_account_role",
                f"PAPEL_CONTABIL duplicado: {row['PAPEL_CONTABIL']}.",
                account_code=row["COD_CTA"],
            )
        )

    present_roles = set(roles)
    for role in REQUIRED_ACCOUNT_ROLES:
        if role not in present_roles:
            issues.append(ValidationIssue("missing_account_role", f"PAPEL_CONTABIL obrigatório ausente: {role}."))

    allowed_roles = set(REQUIRED_ACCOUNT_ROLES) | set(OPTIONAL_ACCOUNT_ROLES)
    for _, row in normalized_mapping.iterrows():
        role = row["PAPEL_CONTABIL"]
        account_code = row["COD_CTA"]
        if role not in allowed_roles:
            issues.append(ValidationIssue("unknown_account_role", f"PAPEL_CONTABIL fora da política v1: {role}.", account_code=account_code))
            continue
        if account_code == "":
            issues.append(ValidationIssue("empty_mapped_account", "COD_CTA não pode ser vazio no mapeamento.", account_code=account_code))
            continue
        try:
            account = get_account(chart_of_accounts, account_code)
        except ReferentialIntegrityError:
            issues.append(ValidationIssue("mapped_account_missing", f"COD_CTA inexistente no plano: {account_code}.", account_code=account_code))
            continue
        if account["IND_CTA"] != AccountType.ANALYTIC.value:
            issues.append(ValidationIssue("mapped_account_not_analytic", "COD_CTA mapeado deve ser conta analítica.", account_code=account_code))
        if not bool(account["ATIVA"]):
            issues.append(ValidationIssue("mapped_account_inactive", "COD_CTA mapeado deve estar ativo.", account_code=account_code))

        expected_cod_nat, expected_balance = ACCOUNT_ROLE_EXPECTATIONS[role]
        if account["COD_NAT"] != expected_cod_nat:
            issues.append(
                ValidationIssue(
                    "account_role_nature_mismatch",
                    f"PAPEL_CONTABIL {role} exige COD_NAT {expected_cod_nat}.",
                    account_code=account_code,
                )
            )
        if account["NAT_SALDO_NORMAL"] != expected_balance:
            issues.append(
                ValidationIssue(
                    "account_role_balance_nature_mismatch",
                    f"PAPEL_CONTABIL {role} exige NAT_SALDO_NORMAL {expected_balance}.",
                    account_code=account_code,
                )
            )

    return ValidationReport(ok=not issues, issues=tuple(issues))


def account_role_map_as_dict(
    mapping: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> dict[str, str]:
    report = validate_account_role_mapping(mapping, chart_of_accounts)
    if not report.ok:
        detail = "; ".join(issue.code for issue in report.issues[:5])
        raise AccountingInvariantError(f"MAPEAMENTO_CONTAS inválido: {detail}")
    normalized = _normalize_account_role_mapping(mapping)
    return dict(zip(normalized["PAPEL_CONTABIL"], normalized["COD_CTA"], strict=True))


def _normalize_account_role_mapping(mapping: pd.DataFrame) -> pd.DataFrame:
    normalized = mapping.copy()
    if set(ACCOUNT_ROLE_MAPPING_COLUMNS).issubset(normalized.columns):
        normalized = normalized.loc[:, list(ACCOUNT_ROLE_MAPPING_COLUMNS)]
    for column in ACCOUNT_ROLE_MAPPING_COLUMNS:
        normalized[column] = normalized[column].map(_clean_required_string)
    return normalized


def _clean_required_string(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
