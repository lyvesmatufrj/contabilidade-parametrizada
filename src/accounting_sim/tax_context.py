"""Contexto tributário contrafactual estrutural da spec 08."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

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
    ValidationIssue,
    ValidationReport,
    parse_iso_date,
)


TAX_INTERFACE_SPEC_VERSION = "spec_08_counterfactual_tax_interface_v1"

_SCALAR_VALUE_TYPES = frozenset(item.value for item in ScalarValueType)
_ORIGINS = frozenset(item.value for item in Origin)
_TAX_SOURCE_TYPES = frozenset(item.value for item in TaxSourceType)

_TAX_PARAMETER_REQUIRED_FIELDS = (
    "ID_PARAM",
    "ID_VERSAO_NORMATIVA",
    "ID_REGRA",
    "TRIBUTO",
    "CHAVE_PARAM",
    "VALOR",
    "TIPO_VALOR",
)

_TAX_PARAMETER_PROVENANCE_FIELDS = (
    "TIPO_FONTE",
    "FONTE_TITULO",
    "FONTE_URL",
    "DISPOSITIVO",
    "VERSAO_NORMA",
    "VIG_INI",
    "DATA_CONSULTA",
    "VERSAO_REGRA",
)


@dataclass(frozen=True)
class TaxContext:
    entity_profile: pd.DataFrame
    fiscal_event_attributes: pd.DataFrame
    tax_scenarios: pd.DataFrame
    tax_parameters: pd.DataFrame


def build_empty_tax_context() -> TaxContext:
    return TaxContext(
        entity_profile=pd.DataFrame(columns=ENTITY_PROFILE_COLUMNS, dtype=object),
        fiscal_event_attributes=pd.DataFrame(columns=FISCAL_EVENT_ATTRIBUTE_COLUMNS, dtype=object),
        tax_scenarios=pd.DataFrame(columns=TAX_SCENARIO_COLUMNS, dtype=object),
        tax_parameters=pd.DataFrame(columns=TAX_PARAMETER_COLUMNS, dtype=object),
    )


def validate_entity_profile(entity_profile: pd.DataFrame) -> ValidationReport:
    issues: list[ValidationIssue] = []
    issues.extend(_missing_columns(entity_profile, ENTITY_PROFILE_COLUMNS, "missing_entity_profile_column"))
    issues.extend(_forbidden_columns(entity_profile, frozenset({"ID_CENARIO", "REGIME_ENTIDADE", "REGIME_IR", "REGIME_CONSUMO", "REGIME_ESPECIAL"}), "forbidden_entity_profile_column"))
    if issues:
        return ValidationReport(ok=False, issues=tuple(issues))

    profile = _normalize_entity_profile(entity_profile)
    if profile.empty:
        return ValidationReport(ok=True, issues=())

    for _, row in profile.iterrows():
        entity_id = row["ID_ENTIDADE"]
        if entity_id == "":
            issues.append(ValidationIssue("empty_entity_id", "ID_ENTIDADE não pode ser vazio.", entity_id=entity_id))
        if row["ATRIBUTO"] == "":
            issues.append(ValidationIssue("empty_entity_attribute", "ATRIBUTO não pode ser vazio.", entity_id=entity_id))
        if row["VALOR"] == "":
            issues.append(ValidationIssue("empty_entity_value", "VALOR não pode ser vazio em ENTIDADE.", entity_id=entity_id))
        if row["TIPO_VALOR"] not in _SCALAR_VALUE_TYPES:
            issues.append(ValidationIssue("invalid_entity_value_type", "TIPO_VALOR deve pertencer a ScalarValueType.", entity_id=entity_id))
        if row["ORIGEM"] not in _ORIGINS:
            issues.append(ValidationIssue("invalid_entity_origin", "ORIGEM fora do enum canônico.", entity_id=entity_id))

    if profile["ID_ENTIDADE"].nunique() > 1:
        issues.append(ValidationIssue("multiple_entities_not_supported", "O MVP aceita no máximo uma entidade por workbook."))
    duplicated = profile.duplicated(["ID_ENTIDADE", "ATRIBUTO"], keep=False)
    for _, row in profile[duplicated].iterrows():
        issues.append(
            ValidationIssue(
                "duplicate_entity_attribute",
                "(ID_ENTIDADE, ATRIBUTO) deve ser único.",
                entity_id=row["ID_ENTIDADE"],
            )
        )

    return ValidationReport(ok=not issues, issues=tuple(_deduplicate_issues(issues)))


def validate_fiscal_event_attributes(
    fiscal_event_attributes: pd.DataFrame,
    events: pd.DataFrame,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    issues.extend(_missing_columns(fiscal_event_attributes, FISCAL_EVENT_ATTRIBUTE_COLUMNS, "missing_fiscal_event_attribute_column"))
    issues.extend(_missing_columns(events, EVENT_COLUMNS, "missing_event_column"))
    issues.extend(_forbidden_columns(fiscal_event_attributes, frozenset({"ID_CENARIO"}), "forbidden_fiscal_event_scenario_column"))
    if issues:
        return ValidationReport(ok=False, issues=tuple(issues))

    attributes = _normalize_fiscal_event_attributes(fiscal_event_attributes)
    if attributes.empty:
        return ValidationReport(ok=True, issues=())

    event_ids = set(events["ID_EVENTO"].astype(str))
    for _, row in attributes.iterrows():
        event_id = row["ID_EVENTO"]
        if event_id == "":
            issues.append(ValidationIssue("empty_fiscal_event_id", "ID_EVENTO não pode ser vazio em EVENTOS_FISCAIS.", event_id=event_id))
        elif event_id not in event_ids:
            issues.append(ValidationIssue("fiscal_event_missing_event", "ID_EVENTO deve referenciar EVENTOS.", event_id=event_id))
        if row["ATRIBUTO_FISCAL"] == "":
            issues.append(ValidationIssue("empty_fiscal_event_attribute", "ATRIBUTO_FISCAL não pode ser vazio.", event_id=event_id))
        if row["VALOR"] == "":
            issues.append(ValidationIssue("empty_fiscal_event_value", "VALOR não pode ser vazio em EVENTOS_FISCAIS.", event_id=event_id))
        if row["TIPO_VALOR"] not in _SCALAR_VALUE_TYPES:
            issues.append(ValidationIssue("invalid_fiscal_event_value_type", "TIPO_VALOR deve pertencer a ScalarValueType.", event_id=event_id))
        if row["ORIGEM"] not in _ORIGINS:
            issues.append(ValidationIssue("invalid_fiscal_event_origin", "ORIGEM fora do enum canônico.", event_id=event_id))

    duplicated = attributes.duplicated(["ID_EVENTO", "ATRIBUTO_FISCAL"], keep=False)
    for _, row in attributes[duplicated].iterrows():
        issues.append(
            ValidationIssue(
                "duplicate_fiscal_event_attribute",
                "(ID_EVENTO, ATRIBUTO_FISCAL) deve ser único.",
                event_id=row["ID_EVENTO"],
            )
        )

    return ValidationReport(ok=not issues, issues=tuple(_deduplicate_issues(issues)))


def validate_tax_parameters(tax_parameters: pd.DataFrame) -> ValidationReport:
    issues: list[ValidationIssue] = []
    issues.extend(_missing_columns(tax_parameters, TAX_PARAMETER_COLUMNS, "missing_tax_parameter_column"))
    if issues:
        return ValidationReport(ok=False, issues=tuple(issues))

    raw_values = tax_parameters["VALOR"].copy()
    parameters = _normalize_tax_parameters(tax_parameters)
    if parameters.empty:
        return ValidationReport(ok=True, issues=())

    ids = parameters["ID_PARAM"]
    for _, row in parameters[ids.duplicated(keep=False)].iterrows():
        issues.append(
            ValidationIssue(
                "duplicate_tax_parameter_id",
                "ID_PARAM deve ser único.",
                tax_param_id=row["ID_PARAM"],
            )
        )

    for _, row in parameters.iterrows():
        param_id = row["ID_PARAM"]
        raw_value = raw_values.loc[row.name] if row.name in raw_values.index else None
        if isinstance(raw_value, float):
            issues.append(
                ValidationIssue(
                    "float_tax_parameter_value",
                    "FISCAL_PARAM.VALOR deve ser texto; float binário não pode ser fonte de verdade normativa.",
                    tax_param_id=param_id,
                )
            )
        for field in _TAX_PARAMETER_REQUIRED_FIELDS:
            if row[field] == "":
                issues.append(ValidationIssue("empty_tax_parameter_required_field", f"{field} não pode ser vazio.", tax_param_id=param_id))
        for field in _TAX_PARAMETER_PROVENANCE_FIELDS:
            if row[field] in {"", None}:
                issues.append(ValidationIssue("missing_tax_parameter_provenance", f"{field} é obrigatório para Prov(p).", tax_param_id=param_id))
        if row["TIPO_VALOR"] not in _SCALAR_VALUE_TYPES:
            issues.append(ValidationIssue("invalid_tax_parameter_value_type", "TIPO_VALOR deve pertencer a ScalarValueType.", tax_param_id=param_id))
        if row["TIPO_FONTE"] not in _TAX_SOURCE_TYPES:
            issues.append(ValidationIssue("invalid_tax_source_type", "TIPO_FONTE deve pertencer a TaxSourceType.", tax_param_id=param_id))

        vig_ini = row["VIG_INI"]
        vig_fim = row["VIG_FIM"]
        if isinstance(vig_ini, date) and isinstance(vig_fim, date) and vig_fim < vig_ini:
            issues.append(ValidationIssue("invalid_tax_parameter_validity_range", "VIG_FIM deve ser maior ou igual a VIG_INI.", tax_param_id=param_id))

    return ValidationReport(ok=not issues, issues=tuple(_deduplicate_issues(issues)))


def validate_tax_scenarios(
    tax_scenarios: pd.DataFrame,
    entity_profile: pd.DataFrame,
    tax_parameters: pd.DataFrame,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    issues.extend(_missing_columns(tax_scenarios, TAX_SCENARIO_COLUMNS, "missing_tax_scenario_column"))
    if issues:
        return ValidationReport(ok=False, issues=tuple(issues))

    scenarios = _normalize_tax_scenarios(tax_scenarios)
    if scenarios.empty:
        return ValidationReport(ok=True, issues=())

    entity_report = validate_entity_profile(entity_profile)
    if not entity_report.ok:
        issues.extend(entity_report.issues)

    has_entity_schema = set(ENTITY_PROFILE_COLUMNS).issubset(entity_profile.columns)
    entity_ids = _normalize_entity_profile(entity_profile)["ID_ENTIDADE"].dropna().unique().tolist() if has_entity_schema and not entity_profile.empty else []
    if len(entity_ids) != 1:
        issues.append(ValidationIssue("tax_scenario_requires_single_entity", "CENARIOS_TRIBUTARIOS requer exatamente uma entidade em ENTIDADE."))
    expected_entity_id = entity_ids[0] if len(entity_ids) == 1 else None

    for _, row in scenarios.iterrows():
        scenario_id = row["ID_CENARIO"]
        if scenario_id == "":
            issues.append(ValidationIssue("empty_tax_scenario_id", "ID_CENARIO não pode ser vazio.", scenario_id=scenario_id))
        if expected_entity_id is not None and row["ID_ENTIDADE"] != expected_entity_id:
            issues.append(
                ValidationIssue(
                    "tax_scenario_invalid_entity",
                    "ID_ENTIDADE do cenário deve referenciar a entidade única.",
                    entity_id=row["ID_ENTIDADE"],
                    scenario_id=scenario_id,
                )
            )
        if not isinstance(row["DT_REFERENCIA_NORMATIVA"], date):
            issues.append(ValidationIssue("invalid_tax_scenario_reference_date", "DT_REFERENCIA_NORMATIVA deve ser datetime.date.", scenario_id=scenario_id))
        if not isinstance(row["E_BASELINE"], bool):
            issues.append(ValidationIssue("invalid_tax_scenario_baseline_flag", "E_BASELINE deve ser bool.", scenario_id=scenario_id))
        if not isinstance(row["ATIVO"], bool):
            issues.append(ValidationIssue("invalid_tax_scenario_active_flag", "ATIVO deve ser bool.", scenario_id=scenario_id))
        if row["ATIVO"] is True and row["REGIME_ENTIDADE"] == "":
            issues.append(ValidationIssue("active_tax_scenario_missing_regime", "Cenário ativo requer REGIME_ENTIDADE.", scenario_id=scenario_id))
        if row["ID_VERSAO_NORMATIVA"] == "":
            issues.append(ValidationIssue("tax_scenario_missing_normative_version", "Todo cenário requer ID_VERSAO_NORMATIVA.", scenario_id=scenario_id))

    ids = scenarios["ID_CENARIO"]
    for _, row in scenarios[ids.duplicated(keep=False)].iterrows():
        issues.append(ValidationIssue("duplicate_tax_scenario_id", "ID_CENARIO deve ser único.", scenario_id=row["ID_CENARIO"]))

    active = scenarios[scenarios["ATIVO"] == True]  # noqa: E712
    if not active.empty and int(active["E_BASELINE"].sum()) != 1:
        issues.append(ValidationIssue("invalid_active_baseline_count", "Deve existir exatamente um baseline entre cenários ativos."))

    tax_parameter_schema_issues = _missing_columns(tax_parameters, TAX_PARAMETER_COLUMNS, "missing_tax_parameter_column")
    issues.extend(tax_parameter_schema_issues)
    if not tax_parameter_schema_issues:
        version_ids = _normalize_tax_parameters(tax_parameters)["ID_VERSAO_NORMATIVA"].dropna()
        version_set = {value for value in version_ids if value != ""}
        for _, row in scenarios.iterrows():
            version = row["ID_VERSAO_NORMATIVA"]
            if version != "" and version not in version_set:
                issues.append(
                    ValidationIssue(
                        "tax_scenario_unknown_normative_version",
                        "ID_VERSAO_NORMATIVA deve existir em FISCAL_PARAM quando há cenários.",
                        scenario_id=row["ID_CENARIO"],
                    )
                )

    return ValidationReport(ok=not issues, issues=tuple(_deduplicate_issues(issues)))


def validate_tax_context(
    tax_context: TaxContext,
    events: pd.DataFrame,
) -> ValidationReport:
    reports = (
        validate_entity_profile(tax_context.entity_profile),
        validate_fiscal_event_attributes(tax_context.fiscal_event_attributes, events),
        validate_tax_parameters(tax_context.tax_parameters),
        validate_tax_scenarios(tax_context.tax_scenarios, tax_context.entity_profile, tax_context.tax_parameters),
    )
    issues = tuple(issue for report in reports for issue in report.issues)
    return ValidationReport(ok=not issues, issues=issues)


def _normalize_entity_profile(entity_profile: pd.DataFrame) -> pd.DataFrame:
    normalized = _with_columns(entity_profile, ENTITY_PROFILE_COLUMNS)
    for column in ENTITY_PROFILE_COLUMNS:
        normalized[column] = normalized[column].map(_clean_required_string)
    return normalized


def _normalize_fiscal_event_attributes(fiscal_event_attributes: pd.DataFrame) -> pd.DataFrame:
    normalized = _with_columns(fiscal_event_attributes, FISCAL_EVENT_ATTRIBUTE_COLUMNS)
    for column in FISCAL_EVENT_ATTRIBUTE_COLUMNS:
        normalized[column] = normalized[column].map(_clean_required_string)
    return normalized


def _normalize_tax_scenarios(tax_scenarios: pd.DataFrame) -> pd.DataFrame:
    normalized = _with_columns(tax_scenarios, TAX_SCENARIO_COLUMNS)
    for column in TAX_SCENARIO_COLUMNS:
        if column in {"DT_REFERENCIA_NORMATIVA"}:
            normalized[column] = normalized[column].map(_parse_required_date)
        elif column in {"E_BASELINE", "ATIVO"}:
            normalized[column] = normalized[column].map(_parse_bool)
        else:
            normalized[column] = normalized[column].map(_clean_required_string)
    return normalized


def _normalize_tax_parameters(tax_parameters: pd.DataFrame) -> pd.DataFrame:
    normalized = _with_columns(tax_parameters, TAX_PARAMETER_COLUMNS)
    for column in TAX_PARAMETER_COLUMNS:
        if column in {"VIG_INI", "DATA_CONSULTA"}:
            normalized[column] = normalized[column].map(_parse_required_date)
        elif column == "VIG_FIM":
            normalized[column] = normalized[column].map(_parse_optional_date)
        else:
            normalized[column] = normalized[column].map(_clean_required_string)
    return normalized


def _with_columns(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    normalized = frame.copy()
    if set(columns).issubset(normalized.columns):
        normalized = normalized.loc[:, list(columns)]
    return normalized


def _missing_columns(frame: pd.DataFrame, columns: tuple[str, ...], issue_code: str) -> tuple[ValidationIssue, ...]:
    return tuple(ValidationIssue(issue_code, f"Coluna obrigatória ausente: {column}.") for column in columns if column not in frame.columns)


def _forbidden_columns(frame: pd.DataFrame, columns: frozenset[str], issue_code: str) -> tuple[ValidationIssue, ...]:
    return tuple(ValidationIssue(issue_code, f"Coluna proibida nesta tabela: {column}.") for column in columns if column in frame.columns)


def _clean_required_string(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return str(value)
    return str(value).strip()


def _parse_required_date(value: object) -> date | None:
    if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return parse_iso_date(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _parse_optional_date(value: object) -> date | None:
    if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
        return None
    return _parse_required_date(value)


def _parse_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "sim", "s"}:
            return True
        if lowered in {"false", "0", "nao", "não", "n"}:
            return False
    return None


def _deduplicate_issues(issues: list[ValidationIssue]) -> tuple[ValidationIssue, ...]:
    unique: dict[tuple[str, str | None, str | None, str | None], ValidationIssue] = {}
    for issue in issues:
        unique.setdefault((issue.code, issue.entity_id, issue.event_id, issue.scenario_id or issue.tax_param_id), issue)
    return tuple(unique.values())
