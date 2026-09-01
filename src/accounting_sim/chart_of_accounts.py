"""Plano de contas canônico das specs 00-02."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

from accounting_sim.canonical import (
    AccountNature,
    AccountType,
    CHART_OF_ACCOUNTS_COLUMNS,
    DebitCredit,
    Origin,
    ReferentialIntegrityError,
    SchemaValidationError,
    parse_iso_date,
)


DEFAULT_COMMERCIAL_CHART_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "templates"
    / "chart_of_accounts_commercial.csv"
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    account_code: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    issues: tuple[ValidationIssue, ...]


def load_chart_of_accounts(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return _normalize_chart_of_accounts(df)


def save_chart_of_accounts(df: pd.DataFrame, path: str | Path) -> Path:
    normalized = _normalize_chart_of_accounts(df)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = normalized.copy()
    for column in ("COD_CTA_SUP", "COD_DF"):
        serialized[column] = serialized[column].map(lambda value: "" if pd.isna(value) else value)
    serialized["DT_ALT"] = serialized["DT_ALT"].map(lambda value: value.isoformat())
    serialized["ATIVA"] = serialized["ATIVA"].map(lambda value: "true" if value else "false")
    serialized.to_csv(output_path, index=False)
    return output_path


def validate_chart_of_accounts(df: pd.DataFrame) -> ValidationReport:
    issues: list[ValidationIssue] = []
    missing_columns = [column for column in CHART_OF_ACCOUNTS_COLUMNS if column not in df.columns]
    for column in missing_columns:
        issues.append(ValidationIssue("missing_column", f"Coluna obrigatória ausente: {column}."))
    if missing_columns:
        return ValidationReport(ok=False, issues=tuple(issues))

    normalized = _normalize_chart_of_accounts(df)
    codes = normalized["COD_CTA"].astype(str)

    empty_codes = normalized[codes.str.strip() == ""]
    for _, row in empty_codes.iterrows():
        issues.append(ValidationIssue("empty_account_code", "COD_CTA não pode ser vazio."))

    duplicated = normalized[codes.duplicated(keep=False)]
    for _, row in duplicated.iterrows():
        issues.append(
            ValidationIssue(
                "duplicate_account_code",
                f"COD_CTA duplicado: {row['COD_CTA']}.",
                row["COD_CTA"],
            )
        )

    issues.extend(_validate_required_values(normalized))

    if empty_codes.empty and duplicated.empty:
        issues.extend(_validate_hierarchy(normalized))

    return ValidationReport(ok=not issues, issues=tuple(issues))


def build_default_commercial_chart(effective_date: date) -> pd.DataFrame:
    parsed_date = parse_iso_date(effective_date)
    df = load_chart_of_accounts(DEFAULT_COMMERCIAL_CHART_PATH)
    df["DT_ALT"] = parsed_date
    return _sort_chart(df)


def get_analytic_accounts(df: pd.DataFrame, active_only: bool = True) -> pd.DataFrame:
    normalized = _normalize_chart_of_accounts(df)
    mask = normalized["IND_CTA"] == AccountType.ANALYTIC.value
    if active_only:
        mask &= normalized["ATIVA"]
    return _sort_chart(normalized.loc[mask].copy())


def get_account(df: pd.DataFrame, code: str) -> pd.Series:
    normalized = _normalize_chart_of_accounts(df)
    matches = normalized[normalized["COD_CTA"] == code]
    if matches.empty:
        raise ReferentialIntegrityError(f"Conta inexistente no plano de contas: {code}.")
    if len(matches) > 1:
        raise ReferentialIntegrityError(f"Conta duplicada no plano de contas: {code}.")
    return matches.iloc[0]


def _normalize_chart_of_accounts(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    if set(CHART_OF_ACCOUNTS_COLUMNS).issubset(normalized.columns):
        normalized = normalized.loc[:, list(CHART_OF_ACCOUNTS_COLUMNS)]

    for column in ("COD_NAT", "IND_CTA", "COD_CTA", "CTA", "NAT_SALDO_NORMAL", "ORIGEM"):
        if column in normalized.columns:
            normalized[column] = normalized[column].map(_clean_required_string)

    for column in ("COD_CTA_SUP", "COD_DF"):
        if column in normalized.columns:
            normalized[column] = normalized[column].map(_clean_optional_string)

    if "DT_ALT" in normalized.columns:
        normalized["DT_ALT"] = normalized["DT_ALT"].map(parse_iso_date)
    if "NIVEL" in normalized.columns:
        normalized["NIVEL"] = normalized["NIVEL"].map(_parse_int)
    if "ATIVA" in normalized.columns:
        normalized["ATIVA"] = normalized["ATIVA"].map(_parse_bool)

    return normalized


def _validate_required_values(df: pd.DataFrame) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    valid_natures = {item.value for item in AccountNature}
    valid_account_types = {item.value for item in AccountType}
    valid_balance_natures = {item.value for item in DebitCredit}
    valid_origins = {item.value for item in Origin}

    for _, row in df.iterrows():
        code = row["COD_CTA"]
        if row["CTA"] == "":
            issues.append(ValidationIssue("empty_account_name", "CTA não pode ser vazio.", code))
        if row["COD_NAT"] not in valid_natures:
            issues.append(ValidationIssue("invalid_cod_nat", "COD_NAT fora do enum canônico.", code))
        if row["IND_CTA"] not in valid_account_types:
            issues.append(ValidationIssue("invalid_ind_cta", "IND_CTA deve ser S ou A.", code))
        if not isinstance(row["NIVEL"], int) or row["NIVEL"] < 1:
            issues.append(ValidationIssue("invalid_level", "NIVEL deve ser inteiro >= 1.", code))
        if row["NAT_SALDO_NORMAL"] not in valid_balance_natures:
            issues.append(
                ValidationIssue(
                    "invalid_balance_nature",
                    "NAT_SALDO_NORMAL deve ser D ou C.",
                    code,
                )
            )
        if not isinstance(row["ATIVA"], bool):
            issues.append(ValidationIssue("invalid_active_flag", "ATIVA deve ser bool.", code))
        if row["ORIGEM"] not in valid_origins:
            issues.append(ValidationIssue("invalid_origin", "ORIGEM fora do enum canônico.", code))
        if row["IND_CTA"] == AccountType.ANALYTIC.value and row["ATIVA"] and row["COD_DF"] is None:
            issues.append(
                ValidationIssue(
                    "missing_statement_mapping",
                    "Conta analítica ativa deve ter COD_DF preenchido no MVP.",
                    code,
                )
            )
    return tuple(issues)


def _validate_hierarchy(df: pd.DataFrame) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    by_code = {row["COD_CTA"]: row for _, row in df.iterrows()}
    parent_codes = {value for value in df["COD_CTA_SUP"] if value is not None}

    for _, row in df.iterrows():
        code = row["COD_CTA"]
        parent_code = row["COD_CTA_SUP"]

        if row["NIVEL"] == 1 and parent_code is not None:
            issues.append(ValidationIssue("invalid_root_parent", "Conta raiz não deve ter pai.", code))
        if row["NIVEL"] > 1 and parent_code is None:
            issues.append(
                ValidationIssue(
                    "missing_parent_for_non_root",
                    "Conta não raiz deve informar COD_CTA_SUP.",
                    code,
                )
            )
        if parent_code is None:
            continue
        if parent_code not in by_code:
            issues.append(ValidationIssue("missing_parent", "COD_CTA_SUP não existe em COD_CTA.", code))
            continue

        parent = by_code[parent_code]
        if parent["IND_CTA"] != AccountType.SYNTHETIC.value:
            issues.append(ValidationIssue("parent_not_synthetic", "Conta superior deve ser sintética.", code))
        if row["NIVEL"] != parent["NIVEL"] + 1:
            issues.append(
                ValidationIssue(
                    "invalid_level_transition",
                    "NIVEL do filho deve ser NIVEL do pai + 1.",
                    code,
                )
            )

    for _, row in df.iterrows():
        code = row["COD_CTA"]
        if row["IND_CTA"] == AccountType.ANALYTIC.value and code in parent_codes:
            issues.append(
                ValidationIssue(
                    "analytic_account_has_children",
                    "Conta analítica não pode ser pai de outra conta.",
                    code,
                )
            )

    for code in by_code:
        if _has_cycle(code, by_code):
            issues.append(ValidationIssue("hierarchy_cycle", "Ciclo detectado na hierarquia.", code))

    return tuple(_deduplicate_issues(issues))


def _has_cycle(code: str, by_code: dict[str, pd.Series]) -> bool:
    seen: set[str] = set()
    current: str | None = code
    while current is not None:
        if current in seen:
            return True
        seen.add(current)
        parent = by_code.get(current, {}).get("COD_CTA_SUP")  # type: ignore[union-attr]
        current = parent if isinstance(parent, str) else None
    return False


def _deduplicate_issues(issues: Iterable[ValidationIssue]) -> tuple[ValidationIssue, ...]:
    unique: dict[tuple[str, str | None], ValidationIssue] = {}
    for issue in issues:
        unique.setdefault((issue.code, issue.account_code), issue)
    return tuple(unique.values())


def _sort_chart(df: pd.DataFrame) -> pd.DataFrame:
    sorted_df = df.copy()
    sorted_df["_sort_key"] = sorted_df["COD_CTA"].map(_account_code_sort_key)
    sorted_df = sorted_df.sort_values("_sort_key", kind="mergesort").drop(columns="_sort_key")
    return sorted_df.reset_index(drop=True)


def _account_code_sort_key(code: str) -> tuple[tuple[int, int | str], ...]:
    parts: list[tuple[int, int | str]] = []
    for part in str(code).split("."):
        parts.append((0, int(part)) if part.isdigit() else (1, part))
    return tuple(parts)


def _clean_required_string(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _clean_optional_string(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def _parse_int(value: object) -> int:
    if isinstance(value, bool):
        raise SchemaValidationError("NIVEL deve ser inteiro, não bool.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(f"NIVEL inválido: {value!r}.") from exc


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "sim", "s"}:
            return True
        if lowered in {"false", "0", "nao", "não", "n"}:
            return False
    raise SchemaValidationError(f"ATIVA inválido: {value!r}.")
