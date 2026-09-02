"""Motor tributário mínimo CBS 2026 para o recorte da spec 09."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from accounting_sim.canonical import (
    EVENT_COLUMNS,
    TAX_ASSESSMENT_RESULT_COLUMNS,
    TAX_OPERATION_RESULT_COLUMNS,
    EventType,
    ScalarValueType,
    SchemaValidationError,
    ValidationIssue,
    ValidationReport,
    parse_iso_date,
)
from accounting_sim.tax_context import TaxContext, validate_tax_context, validate_tax_parameters


CBS_2026_RULE_SPEC_VERSION = "spec_09_cbs_2026_regular_nfe55_v1"

CBS_2026_REQUIRED_PARAMETER_KEYS: tuple[str, ...] = (
    "CBS_RATE_FRACTION",
    "CBS_ASSESSMENT_PERIOD",
    "CBS_NFE_MODEL",
    "CBS_NFE_MANDATORY_FROM",
    "CBS_CST_INTEGRAL",
    "CBS_CCLASSTRIB_INTEGRAL",
    "CBS_VCBS_TOLERANCE_CENTS",
    "CBS_CREDIT_WAIVER_IF_MODALITIES_ABSENT",
    "CBS_SPLIT_PAYMENT_IMPLEMENTED",
    "CBS_BUYER_COLLECTION_IMPLEMENTED",
    "CBS_2026_COLLECTION_WAIVER_IF_ACCESSORY_COMPLIANT",
)

_TRIBUTE = "CBS"
_SUPPORTED_PURCHASE_TYPES = frozenset({EventType.PURCHASE_CASH.value, EventType.PURCHASE_CREDIT.value})
_SUPPORTED_SALE_TYPES = frozenset({EventType.SALE_CASH.value, EventType.SALE_CREDIT.value})
_SUPPORTED_EVENT_TYPES = _SUPPORTED_PURCHASE_TYPES | _SUPPORTED_SALE_TYPES
_SNAPSHOT_REFERENCE_DATE = date(2026, 8, 31)
_ASSESSMENT_END_DATE = date(2026, 8, 31)
_SUPPORTED_ENTITY_REGIME = "nao_optante_simples_mei"
_SUPPORTED_CONSUMPTION_REGIME = "cbs_regime_regular"
_SUPPORTED_ENTITY_TYPE = "pj"
_SUPPORTED_ACTIVITY = "comercio_revenda_mercadorias"
_SUPPORTED_DOCUMENT_STATUS = "autorizado_nao_cancelado"
_SUPPORTED_PURCHASE_DESTINATION = "revenda"
_SUPPORTED_ITEM_COUNT = 1
_SUPPORTED_ASSESSMENT_PERIOD = "monthly"

_REQUIRED_ENTITY_ATTRIBUTES = (
    "TIPO_PESSOA",
    "ATIVIDADE",
    "CONTRIBUINTE_ICMS",
    "CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026",
)

_COMMON_FISCAL_ATTRIBUTES = (
    "MODELO_DFE",
    "CHAVE_NFE",
    "PROTOCOLO_AUTORIZACAO",
    "STATUS_DFE",
    "DT_FORNECIMENTO",
    "QTD_ITENS_DFE",
    "CST_IBS_CBS",
    "CCLASSTRIB",
    "VBC_CENTS",
    "PCBS_PERCENT",
    "VCBS_CENTS",
)

_PURCHASE_ONLY_FISCAL_ATTRIBUTES = ("DESTINACAO_AQUISICAO",)


@dataclass(frozen=True)
class EffectiveCbs2026Rules:
    normative_version_id: str
    rule_version: str
    rate_fraction: Decimal
    assessment_period: str
    nfe_model: str
    nfe_mandatory_from: date
    cst_integral: str
    cclasstrib_integral: str
    vcbs_tolerance_cents: Decimal
    credit_waiver_if_modalities_absent: bool
    split_payment_implemented: bool
    buyer_collection_implemented: bool
    collection_waiver_if_accessory_compliant: bool

    @property
    def credit_extinction_waived(self) -> bool:
        return (
            self.credit_waiver_if_modalities_absent
            and not self.split_payment_implemented
            and not self.buyer_collection_implemented
        )


@dataclass(frozen=True)
class Cbs2026Result:
    operation_results: pd.DataFrame
    assessment_results: pd.DataFrame


def validate_cbs_2026_admissibility(
    events: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    issues.extend(_missing_event_columns(events))
    context_report = validate_tax_context(tax_context, events if not issues else pd.DataFrame(columns=EVENT_COLUMNS))
    if not context_report.ok:
        issues.extend(context_report.issues)
    if issues:
        return ValidationReport(ok=False, issues=tuple(_deduplicate_issues(issues)))

    scenarios = tax_context.tax_scenarios.copy()
    selected = scenarios[scenarios["ID_CENARIO"].astype(str) == str(scenario_id)]
    if len(selected) != 1:
        issues.append(ValidationIssue("cbs_scenario_not_found", "Cenário CBS 2026 deve existir uma única vez.", scenario_id=scenario_id))
        return ValidationReport(ok=False, issues=tuple(issues))

    scenario = selected.iloc[0]
    scenario_issues, entity_id = _validate_cbs_scenario_row(scenario, scenario_id)
    issues.extend(scenario_issues)

    entity = _entity_attribute_map(tax_context.entity_profile, entity_id)
    issues.extend(_validate_cbs_entity(entity, entity_id, scenario_id))

    try:
        rules = select_effective_cbs_2026_rules(tax_context, scenario_id)
    except SchemaValidationError as exc:
        issues.append(ValidationIssue("cbs_effective_rules_invalid", str(exc), scenario_id=scenario_id))
        return ValidationReport(ok=False, issues=tuple(_deduplicate_issues(issues)))

    fiscal_by_event = _fiscal_attribute_map(tax_context.fiscal_event_attributes)
    normalized_events = _normalize_events_for_tax(events)
    fiscal_event_ids = set()
    for _, event in normalized_events.iterrows():
        if event["TIPO_EVENTO"] not in _SUPPORTED_EVENT_TYPES:
            continue
        event_id = str(event["ID_EVENTO"])
        attrs = fiscal_by_event.get(event_id, {})
        fiscal_event_ids.add(event_id)
        issues.extend(_validate_supported_fiscal_event(event, attrs, rules, scenario_id))

    issues.extend(_validate_unique_nfe_keys(fiscal_by_event, fiscal_event_ids, scenario_id))
    return ValidationReport(ok=not issues, issues=tuple(_deduplicate_issues(issues)))


def select_effective_cbs_2026_rules(
    tax_context: TaxContext,
    scenario_id: str,
) -> EffectiveCbs2026Rules:
    parameter_report = validate_tax_parameters(tax_context.tax_parameters)
    if not parameter_report.ok:
        _raise_report("FISCAL_PARAM inválido para CBS 2026", parameter_report)

    scenario = _get_scenario(tax_context, scenario_id)
    reference_date = _coerce_date(scenario["DT_REFERENCIA_NORMATIVA"], "DT_REFERENCIA_NORMATIVA")
    normative_version_id = _clean_string(scenario["ID_VERSAO_NORMATIVA"])
    if normative_version_id == "":
        raise SchemaValidationError("Cenário CBS 2026 sem ID_VERSAO_NORMATIVA.")

    effective_rows: dict[str, pd.Series] = {}
    parameters = tax_context.tax_parameters.copy()
    for _, row in parameters.iterrows():
        if _clean_string(row["ID_VERSAO_NORMATIVA"]) != normative_version_id:
            continue
        if _clean_string(row["TRIBUTO"]) != _TRIBUTE:
            continue
        if not _is_effective_on(row, reference_date):
            continue
        key = _clean_string(row["CHAVE_PARAM"])
        if key not in CBS_2026_REQUIRED_PARAMETER_KEYS:
            continue
        if key in effective_rows:
            raise SchemaValidationError(f"Parâmetro CBS duplicado vigente: {key}.")
        effective_rows[key] = row

    missing = [key for key in CBS_2026_REQUIRED_PARAMETER_KEYS if key not in effective_rows]
    if missing:
        raise SchemaValidationError(f"Parâmetros CBS ausentes ou fora da vigência: {missing}.")

    rule_versions = {_clean_string(row["VERSAO_REGRA"]) for row in effective_rows.values()}
    if len(rule_versions) != 1:
        raise SchemaValidationError("Parâmetros CBS efetivos devem compartilhar uma única VERSAO_REGRA.")

    values = {key: _parse_parameter_value(row) for key, row in effective_rows.items()}
    rules = EffectiveCbs2026Rules(
        normative_version_id=normative_version_id,
        rule_version=next(iter(rule_versions)),
        rate_fraction=_require_decimal(values["CBS_RATE_FRACTION"], "CBS_RATE_FRACTION"),
        assessment_period=_require_str(values["CBS_ASSESSMENT_PERIOD"], "CBS_ASSESSMENT_PERIOD"),
        nfe_model=_require_str(values["CBS_NFE_MODEL"], "CBS_NFE_MODEL"),
        nfe_mandatory_from=_require_date(values["CBS_NFE_MANDATORY_FROM"], "CBS_NFE_MANDATORY_FROM"),
        cst_integral=_require_str(values["CBS_CST_INTEGRAL"], "CBS_CST_INTEGRAL"),
        cclasstrib_integral=_require_str(values["CBS_CCLASSTRIB_INTEGRAL"], "CBS_CCLASSTRIB_INTEGRAL"),
        vcbs_tolerance_cents=_require_decimal(values["CBS_VCBS_TOLERANCE_CENTS"], "CBS_VCBS_TOLERANCE_CENTS"),
        credit_waiver_if_modalities_absent=_require_bool(values["CBS_CREDIT_WAIVER_IF_MODALITIES_ABSENT"], "CBS_CREDIT_WAIVER_IF_MODALITIES_ABSENT"),
        split_payment_implemented=_require_bool(values["CBS_SPLIT_PAYMENT_IMPLEMENTED"], "CBS_SPLIT_PAYMENT_IMPLEMENTED"),
        buyer_collection_implemented=_require_bool(values["CBS_BUYER_COLLECTION_IMPLEMENTED"], "CBS_BUYER_COLLECTION_IMPLEMENTED"),
        collection_waiver_if_accessory_compliant=_require_bool(
            values["CBS_2026_COLLECTION_WAIVER_IF_ACCESSORY_COMPLIANT"],
            "CBS_2026_COLLECTION_WAIVER_IF_ACCESSORY_COMPLIANT",
        ),
    )
    if rules.assessment_period != _SUPPORTED_ASSESSMENT_PERIOD:
        raise SchemaValidationError("CBS_ASSESSMENT_PERIOD fora do recorte mensal da Spec 09.")
    if not rules.credit_extinction_waived:
        raise SchemaValidationError("Modalidades do art. 48 exigem rastreamento fora do recorte da Spec 09.")
    if not rules.collection_waiver_if_accessory_compliant:
        raise SchemaValidationError("Dispensa transitória de recolhimento 2026 ausente no recorte da Spec 09.")
    return rules


def calculate_cbs_2026_operations(
    events: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> pd.DataFrame:
    _ensure_report_ok("CBS 2026 admissibilidade", validate_cbs_2026_admissibility(events, tax_context, scenario_id))
    rules = select_effective_cbs_2026_rules(tax_context, scenario_id)
    fiscal_by_event = _fiscal_attribute_map(tax_context.fiscal_event_attributes)
    rows: list[dict[str, object]] = []
    for _, event in _normalize_events_for_tax(events).iterrows():
        event_type = event["TIPO_EVENTO"]
        if event_type not in _SUPPORTED_EVENT_TYPES:
            continue
        event_id = str(event["ID_EVENTO"])
        attrs = fiscal_by_event[event_id]
        vcbs_cents = _require_int(attrs["VCBS_CENTS"], "VCBS_CENTS")
        vbc_cents = _require_int(attrs["VBC_CENTS"], "VBC_CENTS")
        is_purchase = event_type in _SUPPORTED_PURCHASE_TYPES
        rows.append(
            {
                "ID_CENARIO": scenario_id,
                "ID_EVENTO": event_id,
                "TRIBUTO": _TRIBUTE,
                "INCIDE": True,
                "BASE_CENTS": vbc_cents,
                "ALIQUOTA": rules.rate_fraction,
                "CREDITO_CENTS": vcbs_cents if is_purchase else 0,
                "DEBITO_CENTS": 0 if is_purchase else vcbs_cents,
                "VERSAO_REGRA": rules.rule_version,
            }
        )
    return pd.DataFrame(sorted(rows, key=lambda row: row["ID_EVENTO"]), columns=TAX_OPERATION_RESULT_COLUMNS, dtype=object)


def assess_cbs_2026(
    operation_results: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> pd.DataFrame:
    rules = select_effective_cbs_2026_rules(tax_context, scenario_id)
    scenario = _get_scenario(tax_context, scenario_id)
    entity = _entity_attribute_map(tax_context.entity_profile, _clean_string(scenario["ID_ENTIDADE"]))
    compliance = _require_bool(entity.get("CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026"), "CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026")
    if not compliance:
        raise SchemaValidationError("Compliance acessório CBS 2026 ausente ou falso está fora do recorte.")
    _ensure_operation_result_schema(operation_results)

    results = operation_results.copy()
    total_debits = sum(_require_int(value, "DEBITO_CENTS") for value in results["DEBITO_CENTS"])
    total_credits = sum(_require_int(value, "CREDITO_CENTS") for value in results["CREDITO_CENTS"])
    assessment_balance = total_debits - total_credits
    nominal_due = max(assessment_balance, 0)
    credit_balance = max(-assessment_balance, 0)
    amount_due = 0 if rules.collection_waiver_if_accessory_compliant and compliance else nominal_due
    row = {
        "ID_CENARIO": scenario_id,
        "TRIBUTO": _TRIBUTE,
        "S_APUR_CENTS": assessment_balance,
        "T_RECOLHER_CENTS": amount_due,
        "P_CASH_CENTS": None,
        "E_DRE_CENTS": None,
        "C_SALDO_CENTS": credit_balance,
        "VERSAO_REGRA": rules.rule_version,
    }
    return pd.DataFrame([row], columns=TAX_ASSESSMENT_RESULT_COLUMNS, dtype=object)


def run_cbs_2026(
    events: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> Cbs2026Result:
    context_report = validate_tax_context(tax_context, events)
    _ensure_report_ok("TaxContext", context_report)
    admissibility_report = validate_cbs_2026_admissibility(events, tax_context, scenario_id)
    _ensure_report_ok("CBS 2026 admissibilidade", admissibility_report)
    operation_results = calculate_cbs_2026_operations(events, tax_context, scenario_id)
    assessment_results = assess_cbs_2026(operation_results, tax_context, scenario_id)
    return Cbs2026Result(
        operation_results=operation_results.copy(deep=True),
        assessment_results=assessment_results.copy(deep=True),
    )


def _validate_cbs_scenario_row(scenario: pd.Series, scenario_id: str) -> tuple[list[ValidationIssue], str]:
    issues: list[ValidationIssue] = []
    entity_id = _clean_string(scenario["ID_ENTIDADE"])
    if _parse_bool(scenario["ATIVO"]) is not True:
        issues.append(ValidationIssue("cbs_scenario_inactive", "Cenário CBS 2026 deve estar ativo.", scenario_id=scenario_id))
    if _clean_string(scenario["REGIME_ENTIDADE"]) != _SUPPORTED_ENTITY_REGIME:
        issues.append(ValidationIssue("cbs_entity_regime_out_of_scope", "REGIME_ENTIDADE fora do recorte CBS 2026.", scenario_id=scenario_id))
    if _clean_string(scenario["REGIME_CONSUMO"]) != _SUPPORTED_CONSUMPTION_REGIME:
        issues.append(ValidationIssue("cbs_consumption_regime_out_of_scope", "REGIME_CONSUMO fora do recorte CBS regular.", scenario_id=scenario_id))
    if _clean_string(scenario["REGIME_ESPECIAL"]) != "":
        issues.append(ValidationIssue("cbs_special_regime_out_of_scope", "REGIME_ESPECIAL deve ser vazio no recorte CBS 2026.", scenario_id=scenario_id))
    if _coerce_date_or_none(scenario["DT_REFERENCIA_NORMATIVA"]) != _SNAPSHOT_REFERENCE_DATE:
        issues.append(ValidationIssue("cbs_snapshot_date_out_of_scope", "DT_REFERENCIA_NORMATIVA deve ser 2026-08-31.", scenario_id=scenario_id))
    if _clean_string(scenario["ID_VERSAO_NORMATIVA"]) == "":
        issues.append(ValidationIssue("cbs_missing_normative_version", "ID_VERSAO_NORMATIVA é obrigatório no recorte CBS 2026.", scenario_id=scenario_id))
    return issues, entity_id


def _validate_cbs_entity(entity: dict[str, object], entity_id: str, scenario_id: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for attribute in _REQUIRED_ENTITY_ATTRIBUTES:
        if attribute not in entity:
            issues.append(ValidationIssue("cbs_entity_attribute_missing", f"ENTIDADE sem atributo obrigatório: {attribute}.", entity_id=entity_id, scenario_id=scenario_id))
    if issues:
        return issues
    if _clean_string(entity["TIPO_PESSOA"]) != _SUPPORTED_ENTITY_TYPE:
        issues.append(ValidationIssue("cbs_entity_attribute_out_of_scope", "TIPO_PESSOA deve ser pj.", entity_id=entity_id, scenario_id=scenario_id))
    if _clean_string(entity["ATIVIDADE"]) != _SUPPORTED_ACTIVITY:
        issues.append(ValidationIssue("cbs_entity_attribute_out_of_scope", "ATIVIDADE fora do recorte de comércio/revenda.", entity_id=entity_id, scenario_id=scenario_id))
    if entity["CONTRIBUINTE_ICMS"] is not True:
        issues.append(ValidationIssue("cbs_entity_attribute_out_of_scope", "CONTRIBUINTE_ICMS deve ser true para agosto de 2026.", entity_id=entity_id, scenario_id=scenario_id))
    if entity["CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026"] is not True:
        issues.append(ValidationIssue("cbs_entity_attribute_out_of_scope", "Cumprimento acessório CBS 2026 deve ser true.", entity_id=entity_id, scenario_id=scenario_id))
    return issues


def _validate_supported_fiscal_event(
    event: pd.Series,
    attrs: dict[str, object],
    rules: EffectiveCbs2026Rules,
    scenario_id: str,
) -> list[ValidationIssue]:
    event_id = str(event["ID_EVENTO"])
    event_type = str(event["TIPO_EVENTO"])
    issues: list[ValidationIssue] = []
    required = list(_COMMON_FISCAL_ATTRIBUTES)
    if event_type in _SUPPORTED_PURCHASE_TYPES:
        required.extend(_PURCHASE_ONLY_FISCAL_ATTRIBUTES)
    for attribute in required:
        if attribute not in attrs:
            issues.append(ValidationIssue("cbs_fiscal_attribute_missing", f"EVENTOS_FISCAIS sem atributo obrigatório: {attribute}.", event_id=event_id, scenario_id=scenario_id))
    if issues:
        return issues

    if _clean_string(attrs["MODELO_DFE"]) != rules.nfe_model:
        issues.append(ValidationIssue("cbs_nfe_model_invalid", "MODELO_DFE fora da regra efetiva CBS.", event_id=event_id, scenario_id=scenario_id))
    key = _clean_string(attrs["CHAVE_NFE"])
    if len(key) != 44 or not key.isdigit():
        issues.append(ValidationIssue("cbs_nfe_key_invalid", "CHAVE_NFE deve conter exatamente 44 dígitos.", event_id=event_id, scenario_id=scenario_id))
    if _clean_string(attrs["PROTOCOLO_AUTORIZACAO"]) == "":
        issues.append(ValidationIssue("cbs_protocol_missing", "PROTOCOLO_AUTORIZACAO não pode ser vazio.", event_id=event_id, scenario_id=scenario_id))
    if _clean_string(attrs["STATUS_DFE"]) != _SUPPORTED_DOCUMENT_STATUS:
        issues.append(ValidationIssue("cbs_document_not_authorized", "STATUS_DFE deve representar documento autorizado e não cancelado.", event_id=event_id, scenario_id=scenario_id))

    supply_date = _coerce_date_or_none(attrs["DT_FORNECIMENTO"])
    if supply_date is None or not (rules.nfe_mandatory_from <= supply_date <= _ASSESSMENT_END_DATE):
        issues.append(ValidationIssue("cbs_supply_date_out_of_scope", "DT_FORNECIMENTO fora do período fiscal CBS suportado.", event_id=event_id, scenario_id=scenario_id))
    if _coerce_date_or_none(event["DT_EVENTO"]) is None:
        issues.append(ValidationIssue("cbs_invalid_event_date", "DT_EVENTO deve ser data válida.", event_id=event_id, scenario_id=scenario_id))

    if _safe_int(attrs["QTD_ITENS_DFE"]) != _SUPPORTED_ITEM_COUNT:
        issues.append(ValidationIssue("cbs_item_count_out_of_scope", "QTD_ITENS_DFE deve ser 1 no recorte CBS 2026.", event_id=event_id, scenario_id=scenario_id))
    if _clean_string(attrs["CST_IBS_CBS"]) != rules.cst_integral:
        issues.append(ValidationIssue("cbs_cst_invalid", "CST_IBS_CBS diverge da regra efetiva.", event_id=event_id, scenario_id=scenario_id))
    if _clean_string(attrs["CCLASSTRIB"]) != rules.cclasstrib_integral:
        issues.append(ValidationIssue("cbs_cclass_invalid", "CCLASSTRIB diverge da regra efetiva.", event_id=event_id, scenario_id=scenario_id))

    vbc_cents = _safe_int(attrs["VBC_CENTS"])
    if vbc_cents is None or vbc_cents <= 0:
        issues.append(ValidationIssue("cbs_base_invalid", "VBC_CENTS deve ser inteiro estritamente positivo.", event_id=event_id, scenario_id=scenario_id))
    vcbs_cents = _safe_int(attrs["VCBS_CENTS"])
    if vcbs_cents is None or vcbs_cents < 0:
        issues.append(ValidationIssue("cbs_vcbs_invalid", "VCBS_CENTS deve ser inteiro não negativo.", event_id=event_id, scenario_id=scenario_id))

    pcbs_percent = _safe_decimal(attrs["PCBS_PERCENT"])
    if pcbs_percent is None or pcbs_percent / Decimal("100") != rules.rate_fraction:
        issues.append(ValidationIssue("cbs_pcbs_invalid", "PCBS_PERCENT diverge da alíquota efetiva CBS.", event_id=event_id, scenario_id=scenario_id))
    if vbc_cents is not None and vcbs_cents is not None:
        expected_vcbs = Decimal(vbc_cents) * rules.rate_fraction
        if abs(Decimal(vcbs_cents) - expected_vcbs) > rules.vcbs_tolerance_cents:
            issues.append(ValidationIssue("cbs_vcbs_inconsistent", "VCBS_CENTS diverge do cálculo documental além da tolerância.", event_id=event_id, scenario_id=scenario_id))

    if event_type in _SUPPORTED_PURCHASE_TYPES and _clean_string(attrs["DESTINACAO_AQUISICAO"]) != _SUPPORTED_PURCHASE_DESTINATION:
        issues.append(ValidationIssue("cbs_purchase_destination_invalid", "Compra CBS deve ter DESTINACAO_AQUISICAO=revenda.", event_id=event_id, scenario_id=scenario_id))
    return issues


def _validate_unique_nfe_keys(
    fiscal_by_event: dict[str, dict[str, object]],
    fiscal_event_ids: set[str],
    scenario_id: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: dict[str, str] = {}
    for event_id in sorted(fiscal_event_ids):
        key = _clean_string(fiscal_by_event.get(event_id, {}).get("CHAVE_NFE"))
        if key == "":
            continue
        if key in seen:
            issues.append(ValidationIssue("cbs_nfe_key_duplicated", "CHAVE_NFE deve ser única no recorte CBS.", event_id=event_id, scenario_id=scenario_id))
            issues.append(ValidationIssue("cbs_nfe_key_duplicated", "CHAVE_NFE deve ser única no recorte CBS.", event_id=seen[key], scenario_id=scenario_id))
        seen[key] = event_id
    return issues


def _get_scenario(tax_context: TaxContext, scenario_id: str) -> pd.Series:
    scenarios = tax_context.tax_scenarios
    selected = scenarios[scenarios["ID_CENARIO"].astype(str) == str(scenario_id)]
    if len(selected) != 1:
        raise SchemaValidationError(f"Cenário tributário ausente ou duplicado: {scenario_id}.")
    return selected.iloc[0]


def _entity_attribute_map(entity_profile: pd.DataFrame, entity_id: str) -> dict[str, object]:
    entity_rows = entity_profile[entity_profile["ID_ENTIDADE"].astype(str) == str(entity_id)]
    return {str(row["ATRIBUTO"]).strip(): _parse_generic_value(row["VALOR"], row["TIPO_VALOR"]) for _, row in entity_rows.iterrows()}


def _fiscal_attribute_map(fiscal_event_attributes: pd.DataFrame) -> dict[str, dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for _, row in fiscal_event_attributes.iterrows():
        event_id = str(row["ID_EVENTO"]).strip()
        grouped.setdefault(event_id, {})[str(row["ATRIBUTO_FISCAL"]).strip()] = _parse_generic_value(row["VALOR"], row["TIPO_VALOR"])
    return grouped


def _parse_parameter_value(row: pd.Series) -> object:
    return _parse_generic_value(row["VALOR"], row["TIPO_VALOR"])


def _parse_generic_value(value: object, value_type: object) -> object:
    value_kind = _clean_string(value_type)
    if value_kind == ScalarValueType.STRING.value:
        return _clean_string(value)
    if value_kind == ScalarValueType.INTEGER.value:
        return _parse_int(value)
    if value_kind == ScalarValueType.DECIMAL.value:
        return _parse_decimal(value)
    if value_kind == ScalarValueType.BOOLEAN.value:
        return _parse_bool(value)
    if value_kind == ScalarValueType.DATE.value:
        return _coerce_date(value, "VALOR")
    raise SchemaValidationError(f"TIPO_VALOR não suportado na CBS 2026: {value_type!r}.")


def _is_effective_on(row: pd.Series, reference_date: date) -> bool:
    start = _coerce_date(row["VIG_INI"], "VIG_INI")
    end_raw = row["VIG_FIM"]
    end = None if _clean_string(end_raw) == "" else _coerce_date(end_raw, "VIG_FIM")
    return start <= reference_date and (end is None or reference_date <= end)


def _normalize_events_for_tax(events: pd.DataFrame) -> pd.DataFrame:
    normalized = events.copy()
    normalized = normalized.loc[:, list(EVENT_COLUMNS)]
    for column in ("ID_EVENTO", "TIPO_EVENTO"):
        normalized[column] = normalized[column].map(_clean_string)
    return normalized


def _ensure_operation_result_schema(operation_results: pd.DataFrame) -> None:
    if tuple(operation_results.columns) != TAX_OPERATION_RESULT_COLUMNS:
        raise SchemaValidationError("Schema de TAX_OPERATION_RESULT inválido.")


def _missing_event_columns(events: pd.DataFrame) -> tuple[ValidationIssue, ...]:
    return tuple(ValidationIssue("missing_event_column", f"Coluna obrigatória ausente: {column}.") for column in EVENT_COLUMNS if column not in events.columns)


def _ensure_report_ok(stage: str, report: ValidationReport) -> None:
    if report.ok:
        return
    _raise_report(stage, report)


def _raise_report(stage: str, report: ValidationReport) -> None:
    details = "; ".join(f"{issue.code}: {issue.message}" for issue in report.issues[:5])
    raise SchemaValidationError(f"{stage}: {details}")


def _deduplicate_issues(issues: list[ValidationIssue]) -> tuple[ValidationIssue, ...]:
    unique: dict[tuple[object, ...], ValidationIssue] = {}
    for issue in issues:
        unique.setdefault((issue.code, issue.event_id, issue.entity_id, issue.scenario_id, issue.tax_param_id), issue)
    return tuple(unique.values())


def _clean_string(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _coerce_date(value: object, field_name: str) -> date:
    result = _coerce_date_or_none(value)
    if result is None:
        raise SchemaValidationError(f"{field_name} deve ser datetime.date ou ISO date.")
    return result


def _coerce_date_or_none(value: object) -> date | None:
    if value is None or pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return parse_iso_date(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _parse_int(value: object) -> int:
    if isinstance(value, bool) or isinstance(value, float):
        raise SchemaValidationError(f"Valor inteiro inválido: {value!r}.")
    try:
        return int(_clean_string(value))
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(f"Valor inteiro inválido: {value!r}.") from exc


def _safe_int(value: object) -> int | None:
    try:
        return _parse_int(value)
    except SchemaValidationError:
        return None


def _parse_decimal(value: object) -> Decimal:
    if isinstance(value, float):
        raise SchemaValidationError("Decimal normativo/documental não deve usar float.")
    try:
        return Decimal(_clean_string(value))
    except (InvalidOperation, ValueError) as exc:
        raise SchemaValidationError(f"Decimal inválido: {value!r}.") from exc


def _safe_decimal(value: object) -> Decimal | None:
    try:
        return _parse_decimal(value)
    except SchemaValidationError:
        return None


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    lowered = _clean_string(value).lower()
    if lowered in {"true", "1", "sim", "s"}:
        return True
    if lowered in {"false", "0", "nao", "não", "n"}:
        return False
    raise SchemaValidationError(f"Booleano inválido: {value!r}.")


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or value == "":
        raise SchemaValidationError(f"{field_name} deve ser string não vazia.")
    return value


def _require_decimal(value: object, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise SchemaValidationError(f"{field_name} deve ser Decimal.")
    return value


def _require_date(value: object, field_name: str) -> date:
    if not isinstance(value, date):
        raise SchemaValidationError(f"{field_name} deve ser date.")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise SchemaValidationError(f"{field_name} deve ser bool.")
    return value


def _require_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SchemaValidationError(f"{field_name} deve ser int.")
    return value
