"""Comparação Simples Nacional 2027 puro vs híbrido da spec 12."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd

from accounting_sim.canonical import (
    EVENT_COLUMNS,
    TAX_ANALYSIS_PARAMETER_COLUMNS,
    TAX_PARAMETER_COLUMNS,
    TAX_SCENARIO_COLUMNS,
    EventNature,
    EventType,
    ScalarValueType,
    SchemaValidationError,
    ValidationIssue,
    ValidationReport,
    parse_iso_date,
)
from accounting_sim.tax_context import TaxContext, validate_tax_context, validate_tax_parameters


SIMPLES_2027_RULE_SPEC_VERSION = "spec_12_simples_2027_puro_hibrido_v1"

SIMPLES_2027_SCENARIO_RESULT_COLUMNS = (
    "ID_CENARIO",
    "REGIME_CONSUMO",
    "RECEITA_MES_CENTS",
    "RBT12_CENTS",
    "ALIQUOTA_EFETIVA_SIMPLES",
    "DAS_TOTAL_CENTS",
    "DAS_CBS_CENTS",
    "DAS_IBS_CENTS",
    "DAS_OUTROS_CENTS",
    "CBS_REGULAR_RATE_FRACTION",
    "CBS_RATE_SOURCE",
    "CBS_DEBITO_REGULAR_CENTS",
    "CBS_CREDITO_EMPRESA_POTENCIAL_CENTS",
    "CBS_CREDITO_EMPRESA_MODELADO_CENTS",
    "CBS_VALOR_LIQUIDO_MODELADO_CENTS",
    "CBS_SALDO_CREDOR_MODELADO_CENTS",
    "IBS_REGULAR_RATE_FRACTION",
    "IBS_DEBITO_REGULAR_CENTS",
    "IBS_CREDITO_EMPRESA_POTENCIAL_CENTS",
    "IBS_CREDITO_EMPRESA_MODELADO_CENTS",
    "IBS_VALOR_LIQUIDO_MODELADO_CENTS",
    "IBS_SALDO_CREDOR_MODELADO_CENTS",
    "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS",
    "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS",
    "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS",
    "STATUS_RESULTADO",
    "VERSAO_REGRA",
)

SIMPLES_2027_COMPARISON_COLUMNS = (
    "ID_CENARIO_BASE",
    "ID_CENARIO",
    "METRICA",
    "BASELINE_CENTS",
    "ALTERNATIVO_CENTS",
    "DELTA_CENTS",
    "STATUS_BASELINE",
    "STATUS_ALTERNATIVO",
)

_REQUIRED_ANALYSIS_KEYS = (
    "CBS_2027_ANALYSIS_RATE_FRACTION",
    "REGULAR_CREDIT_REALIZATION_FRACTION",
)
_FORBIDDEN_ANALYSIS_KEYS = frozenset({"CBS_2027_REGULAR_RATE_FRACTION"})
_OPTIONAL_CBS_RATE_KEY = "CBS_2027_REGULAR_RATE_FRACTION"
_REQUIRED_PARAMETER_KEYS = tuple(
    key
    for band in range(1, 6)
    for key in (
        f"SIMPLES_ANNEX_I_F{band}_RBT12_MAX_CENTS",
        f"SIMPLES_ANNEX_I_F{band}_NOMINAL_RATE_FRACTION",
        f"SIMPLES_ANNEX_I_F{band}_DEDUCTION_CENTS",
    )
) + (
    "SIMPLES_ANNEX_I_CBS_SHARE_FRACTION",
    "SIMPLES_ANNEX_I_IBS_SHARE_FRACTION",
    "SIMPLES_2027_REVENUE_RECOGNITION",
    "IBS_2027_REGULAR_RATE_FRACTION",
)

_SUPPORTED_ENTITY_REGIME = "simples_nacional"
_BASELINE_REGIME = "simples_ibs_cbs_das"
_HYBRID_REGIME = "ibs_cbs_regime_regular"
_SUPPORTED_ENTITY_TYPE = "pj"
_SUPPORTED_ACTIVITY = "comercio_revenda_mercadorias"
_SUPPORTED_ANNEX = "I"
_SUPPORTED_SCOPE = "domestica"
_SUPPORTED_SUPPLIER_REGIME = "ibs_cbs_regime_regular"
_SUPPORTED_B2B_ACQUIRER_REGIME = "ibs_cbs_regime_regular"
_SUPPORTED_B2C_ACQUIRER_REGIME = "consumidor_final"
_SUPPORTED_PURCHASE_DESTINATION = "revenda"
_SUPPORTED_PURCHASE_TYPES = frozenset({EventType.PURCHASE_CASH.value, EventType.PURCHASE_CREDIT.value})
_SUPPORTED_SALE_TYPES = frozenset({EventType.SALE_CASH.value, EventType.SALE_CREDIT.value})
_SUPPORTED_EVENT_TYPES = _SUPPORTED_PURCHASE_TYPES | _SUPPORTED_SALE_TYPES
_FIRST_SEMESTER_START = date(2027, 1, 1)
_FIRST_SEMESTER_END = date(2027, 6, 30)
_STATUS_NORMATIVE = "normativo"
_STATUS_ANALYTICAL = "analitico"


@dataclass(frozen=True)
class SimplesAnnexBand:
    max_rbt12_cents: int
    nominal_rate_fraction: Decimal
    deduction_cents: int


@dataclass(frozen=True)
class EffectiveSimples2027Rules:
    normative_version_id: str
    rule_version: str
    annex_i_bands: tuple[SimplesAnnexBand, ...]
    cbs_share_fraction: Decimal
    ibs_share_fraction: Decimal
    ibs_regular_rate_fraction: Decimal
    cbs_regular_rate_fraction: Decimal | None
    revenue_recognition: str


@dataclass(frozen=True)
class Simples2027AnalysisAssumptions:
    analysis_id: str
    cbs_analysis_rate_fraction: Decimal
    regular_credit_realization_fraction: Decimal


@dataclass(frozen=True)
class Simples2027CounterfactualReport:
    baseline_scenario_id: str
    alternative_scenario_id: str
    scenario_results: pd.DataFrame
    comparison_results: pd.DataFrame
    cbs_rate_used_fraction: Decimal
    cbs_rate_source: str
    cbs_break_even_rate_fraction: Decimal | None


@dataclass(frozen=True)
class _MeasuredFacts:
    revenue_cents: int
    eligible_purchase_cents: int
    b2b_revenue_cents: int
    b2c_revenue_cents: int


def validate_tax_analysis_parameters(
    analysis_parameters: pd.DataFrame,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    if tuple(analysis_parameters.columns) != TAX_ANALYSIS_PARAMETER_COLUMNS:
        missing = [column for column in TAX_ANALYSIS_PARAMETER_COLUMNS if column not in analysis_parameters.columns]
        extra = [column for column in analysis_parameters.columns if column not in TAX_ANALYSIS_PARAMETER_COLUMNS]
        for column in missing:
            issues.append(ValidationIssue("missing_tax_analysis_parameter_column", f"Coluna obrigatória ausente em ANALISE_PARAM: {column}."))
        for column in extra:
            issues.append(ValidationIssue("forbidden_tax_analysis_parameter_column", f"Coluna não prevista em ANALISE_PARAM: {column}."))
        return ValidationReport(ok=False, issues=tuple(issues))

    if analysis_parameters.empty:
        return ValidationReport(ok=True, issues=())

    raw_values = analysis_parameters["VALOR"].copy()
    params = _normalize_analysis_parameters(analysis_parameters)
    if params["ID_ANALISE"].nunique() != 1:
        issues.append(ValidationIssue("tax_analysis_requires_single_id", "ANALISE_PARAM requer uma única ID_ANALISE."))

    duplicated = params.duplicated(["CHAVE_PARAM"], keep=False)
    for _, row in params[duplicated].iterrows():
        issues.append(ValidationIssue("duplicate_tax_analysis_parameter_key", "CHAVE_PARAM deve ser única em ANALISE_PARAM."))

    for _, row in params.iterrows():
        key = row["CHAVE_PARAM"]
        raw_value = raw_values.loc[row.name] if row.name in raw_values.index else None
        if isinstance(raw_value, float):
            issues.append(ValidationIssue("float_tax_analysis_parameter_value", "ANALISE_PARAM.VALOR deve ser texto; float binário é rejeitado."))
        if key in _FORBIDDEN_ANALYSIS_KEYS:
            issues.append(ValidationIssue("forbidden_tax_analysis_parameter_key", f"{key} pertence a FISCAL_PARAM, não a ANALISE_PARAM."))
        if row["ID_ANALISE"] == "" or key == "" or row["VALOR"] == "":
            issues.append(ValidationIssue("empty_tax_analysis_parameter_required_field", "ID_ANALISE, CHAVE_PARAM e VALOR são obrigatórios."))
        if row["TIPO_VALOR"] not in {item.value for item in ScalarValueType}:
            issues.append(ValidationIssue("invalid_tax_analysis_parameter_type", "TIPO_VALOR inválido em ANALISE_PARAM."))

    values = _analysis_value_map(params)
    cbs_rate = _safe_decimal(values.get("CBS_2027_ANALYSIS_RATE_FRACTION"))
    if cbs_rate is not None and not (Decimal(0) < cbs_rate < Decimal(1)):
        issues.append(ValidationIssue("invalid_tax_analysis_cbs_rate", "CBS_2027_ANALYSIS_RATE_FRACTION deve pertencer a (0,1)."))
    alpha = _safe_decimal(values.get("REGULAR_CREDIT_REALIZATION_FRACTION"))
    if alpha is not None and not (Decimal(0) <= alpha <= Decimal(1)):
        issues.append(ValidationIssue("invalid_tax_analysis_credit_realization", "REGULAR_CREDIT_REALIZATION_FRACTION deve pertencer a [0,1]."))

    return ValidationReport(ok=not issues, issues=tuple(_deduplicate_issues(issues)))


def validate_simples_2027_admissibility(
    events: pd.DataFrame,
    tax_context: TaxContext,
    analysis_parameters: pd.DataFrame,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    if not set(EVENT_COLUMNS).issubset(events.columns):
        issues.extend(ValidationIssue("missing_event_column", f"Coluna obrigatória ausente: {column}.") for column in EVENT_COLUMNS if column not in events.columns)
        return ValidationReport(ok=False, issues=tuple(issues))

    context_report = validate_tax_context(tax_context, events)
    issues.extend(context_report.issues)
    analysis_report = validate_tax_analysis_parameters(analysis_parameters)
    if not analysis_report.ok:
        issues.append(ValidationIssue("simples_2027_analysis_parameters_invalid", "ANALISE_PARAM inválido para Spec 12."))
        issues.extend(analysis_report.issues)

    if not set(TAX_SCENARIO_COLUMNS).issubset(tax_context.tax_scenarios.columns):
        return ValidationReport(ok=False, issues=tuple(_deduplicate_issues(issues)))

    active = _active_scenarios(tax_context.tax_scenarios)
    baseline_rows = active.loc[active["E_BASELINE"].map(_parse_bool_or_none) == True]  # noqa: E712
    if len(active) != 2:
        issues.append(ValidationIssue("simples_2027_requires_two_active_scenarios", "Spec 12 requer exatamente dois cenários ativos."))
    if len(baseline_rows) != 1:
        issues.append(ValidationIssue("simples_2027_invalid_baseline", "Spec 12 requer exatamente um baseline ativo."))
    if len(active) == 2 and len(baseline_rows) == 1:
        baseline = baseline_rows.iloc[0]
        alternatives = active.loc[active["ID_CENARIO"] != baseline["ID_CENARIO"]]
        alternative = alternatives.iloc[0]
        issues.extend(_validate_scenario_pair(baseline, alternative))
        rules_by_scenario: dict[str, EffectiveSimples2027Rules] = {}
        for scenario_id in (str(baseline["ID_CENARIO"]), str(alternative["ID_CENARIO"])):
            try:
                rules_by_scenario[scenario_id] = select_effective_simples_2027_rules(tax_context, scenario_id)
            except SchemaValidationError as exc:
                issues.append(ValidationIssue("simples_2027_normative_parameters_invalid", str(exc), scenario_id=scenario_id))
        reference_rules = rules_by_scenario.get(str(baseline["ID_CENARIO"]))
        require_cbs_analysis_rate = reference_rules is None or reference_rules.cbs_regular_rate_fraction is None
        issues.extend(_validate_required_analysis_parameters(analysis_parameters, require_cbs_analysis_rate=require_cbs_analysis_rate))

    entity_id = str(active.iloc[0]["ID_ENTIDADE"]).strip() if not active.empty and "ID_ENTIDADE" in active.columns else ""
    entity = _entity_attribute_map(tax_context.entity_profile, entity_id)
    rules_for_entity: EffectiveSimples2027Rules | None = None
    if not active.empty:
        try:
            rules_for_entity = select_effective_simples_2027_rules(tax_context, str(active.iloc[0]["ID_CENARIO"]))
        except SchemaValidationError:
            rules_for_entity = None
    issues.extend(_validate_entity(entity, entity_id, rules_for_entity))
    issues.extend(_validate_facts(events, tax_context.fiscal_event_attributes))

    return ValidationReport(ok=not issues, issues=tuple(_deduplicate_issues(issues)))


def select_effective_simples_2027_rules(
    tax_context: TaxContext,
    scenario_id: str,
) -> EffectiveSimples2027Rules:
    parameter_report = validate_tax_parameters(tax_context.tax_parameters)
    if not parameter_report.ok:
        _raise_report("FISCAL_PARAM inválido para Simples 2027", parameter_report)

    scenario = _get_scenario(tax_context, scenario_id)
    reference_date = _require_date(scenario["DT_REFERENCIA_NORMATIVA"], "DT_REFERENCIA_NORMATIVA")
    normative_version_id = _clean_string(scenario["ID_VERSAO_NORMATIVA"])
    if not normative_version_id:
        raise SchemaValidationError("Cenário Simples 2027 sem ID_VERSAO_NORMATIVA.")

    effective_rows: dict[str, pd.Series] = {}
    optional_cbs_rows: list[pd.Series] = []
    for _, row in tax_context.tax_parameters.iterrows():
        if _clean_string(row["ID_VERSAO_NORMATIVA"]) != normative_version_id:
            continue
        if not _is_effective_on(row, reference_date):
            continue
        key = _clean_string(row["CHAVE_PARAM"])
        if key == "CBS_2027_ANALYSIS_RATE_FRACTION":
            raise SchemaValidationError("CBS_2027_ANALYSIS_RATE_FRACTION não é chave normativa usada pela engine.")
        if key == _OPTIONAL_CBS_RATE_KEY:
            optional_cbs_rows.append(row)
            continue
        if key not in _REQUIRED_PARAMETER_KEYS:
            continue
        if key in effective_rows:
            raise SchemaValidationError(f"Parâmetro Simples 2027 duplicado vigente: {key}.")
        effective_rows[key] = row

    missing = [key for key in _REQUIRED_PARAMETER_KEYS if key not in effective_rows]
    if missing:
        raise SchemaValidationError(f"Parâmetros Simples 2027 ausentes ou fora da vigência: {missing}.")
    if len(optional_cbs_rows) > 1:
        raise SchemaValidationError("CBS_2027_REGULAR_RATE_FRACTION duplicado vigente.")

    rule_versions = {_clean_string(row["VERSAO_REGRA"]) for row in (*effective_rows.values(), *optional_cbs_rows)}
    if len(rule_versions) != 1:
        raise SchemaValidationError("Parâmetros Simples 2027 efetivos devem compartilhar uma única VERSAO_REGRA.")

    values = {key: _parse_parameter_value(row) for key, row in effective_rows.items()}
    bands = tuple(
        SimplesAnnexBand(
            max_rbt12_cents=_require_int(values[f"SIMPLES_ANNEX_I_F{band}_RBT12_MAX_CENTS"], f"SIMPLES_ANNEX_I_F{band}_RBT12_MAX_CENTS"),
            nominal_rate_fraction=_require_decimal(values[f"SIMPLES_ANNEX_I_F{band}_NOMINAL_RATE_FRACTION"], f"SIMPLES_ANNEX_I_F{band}_NOMINAL_RATE_FRACTION"),
            deduction_cents=_require_int(values[f"SIMPLES_ANNEX_I_F{band}_DEDUCTION_CENTS"], f"SIMPLES_ANNEX_I_F{band}_DEDUCTION_CENTS"),
        )
        for band in range(1, 6)
    )
    cbs_regular_rate = None
    if optional_cbs_rows:
        cbs_regular_rate = _require_decimal(_parse_parameter_value(optional_cbs_rows[0]), _OPTIONAL_CBS_RATE_KEY)
    return EffectiveSimples2027Rules(
        normative_version_id=normative_version_id,
        rule_version=next(iter(rule_versions)),
        annex_i_bands=tuple(sorted(bands, key=lambda band: band.max_rbt12_cents)),
        cbs_share_fraction=_require_decimal(values["SIMPLES_ANNEX_I_CBS_SHARE_FRACTION"], "SIMPLES_ANNEX_I_CBS_SHARE_FRACTION"),
        ibs_share_fraction=_require_decimal(values["SIMPLES_ANNEX_I_IBS_SHARE_FRACTION"], "SIMPLES_ANNEX_I_IBS_SHARE_FRACTION"),
        ibs_regular_rate_fraction=_require_decimal(values["IBS_2027_REGULAR_RATE_FRACTION"], "IBS_2027_REGULAR_RATE_FRACTION"),
        cbs_regular_rate_fraction=cbs_regular_rate,
        revenue_recognition=_require_str(values["SIMPLES_2027_REVENUE_RECOGNITION"], "SIMPLES_2027_REVENUE_RECOGNITION"),
    )


def select_simples_2027_analysis_assumptions(
    analysis_parameters: pd.DataFrame,
) -> Simples2027AnalysisAssumptions:
    return _select_simples_2027_analysis_assumptions(analysis_parameters, require_cbs_analysis_rate=True)


def _select_simples_2027_analysis_assumptions(
    analysis_parameters: pd.DataFrame,
    *,
    require_cbs_analysis_rate: bool,
) -> Simples2027AnalysisAssumptions:
    report = validate_tax_analysis_parameters(analysis_parameters)
    if not report.ok:
        _raise_report("ANALISE_PARAM inválido para Simples 2027", report)
    params = _normalize_analysis_parameters(analysis_parameters)
    values = _analysis_value_map(params)
    required_keys = _required_analysis_keys(require_cbs_analysis_rate=require_cbs_analysis_rate)
    missing = [key for key in required_keys if key not in values]
    if missing:
        raise SchemaValidationError(f"ANALISE_PARAM sem chaves obrigatórias para Spec 12: {missing}.")
    return Simples2027AnalysisAssumptions(
        analysis_id=str(params["ID_ANALISE"].iloc[0]).strip(),
        cbs_analysis_rate_fraction=(
            _require_decimal(_parse_generic_value(values["CBS_2027_ANALYSIS_RATE_FRACTION"], ScalarValueType.DECIMAL.value), "CBS_2027_ANALYSIS_RATE_FRACTION")
            if "CBS_2027_ANALYSIS_RATE_FRACTION" in values
            else Decimal(0)
        ),
        regular_credit_realization_fraction=_require_decimal(_parse_generic_value(values["REGULAR_CREDIT_REALIZATION_FRACTION"], ScalarValueType.DECIMAL.value), "REGULAR_CREDIT_REALIZATION_FRACTION"),
    )


def run_simples_2027_counterfactual_report(
    events: pd.DataFrame,
    tax_context: TaxContext,
    analysis_parameters: pd.DataFrame,
) -> Simples2027CounterfactualReport:
    report = validate_simples_2027_admissibility(events, tax_context, analysis_parameters)
    if not report.ok:
        _raise_report("Experimento Simples 2027 inválido", report)

    active = _active_scenarios(tax_context.tax_scenarios)
    baseline = active.loc[active["E_BASELINE"].map(_parse_bool_or_none) == True].iloc[0]  # noqa: E712
    alternative = active.loc[active["ID_CENARIO"] != baseline["ID_CENARIO"]].iloc[0]
    baseline_id = _clean_string(baseline["ID_CENARIO"])
    alternative_id = _clean_string(alternative["ID_CENARIO"])
    rules = select_effective_simples_2027_rules(tax_context, baseline_id)
    analysis = _select_simples_2027_analysis_assumptions(
        analysis_parameters,
        require_cbs_analysis_rate=rules.cbs_regular_rate_fraction is None,
    )
    cbs_rate, cbs_rate_source = _resolve_cbs_2027_rate(rules, analysis)
    entity = _entity_attribute_map(tax_context.entity_profile, _clean_string(baseline["ID_ENTIDADE"]))
    rbt12_cents = _require_int(entity["RBT12_CENTS"], "RBT12_CENTS")
    band = _select_annex_band(rules, rbt12_cents)
    effective_rate = _effective_rate(rbt12_cents, band)
    facts = _measure_facts(events, tax_context.fiscal_event_attributes)

    das_total = _round_cents(Decimal(facts.revenue_cents) * effective_rate)
    das_cbs = _round_cents(Decimal(facts.revenue_cents) * effective_rate * rules.cbs_share_fraction)
    das_ibs = _round_cents(Decimal(facts.revenue_cents) * effective_rate * rules.ibs_share_fraction)
    das_outros = das_total - das_cbs - das_ibs

    b2b_cbs_puro = _round_cents(Decimal(facts.b2b_revenue_cents) * effective_rate * rules.cbs_share_fraction)
    b2b_ibs_puro = _round_cents(Decimal(facts.b2b_revenue_cents) * effective_rate * rules.ibs_share_fraction)
    cbs_debit = _round_cents(Decimal(facts.revenue_cents) * cbs_rate)
    cbs_credit_potential = _round_cents(Decimal(facts.eligible_purchase_cents) * cbs_rate)
    cbs_credit_modelled = _round_cents(Decimal(cbs_credit_potential) * analysis.regular_credit_realization_fraction)
    cbs_net = max(cbs_debit - cbs_credit_modelled, 0)
    cbs_credit_balance = max(cbs_credit_modelled - cbs_debit, 0)
    ibs_debit = _round_cents(Decimal(facts.revenue_cents) * rules.ibs_regular_rate_fraction)
    ibs_credit_potential = _round_cents(Decimal(facts.eligible_purchase_cents) * rules.ibs_regular_rate_fraction)
    ibs_credit_modelled = _round_cents(Decimal(ibs_credit_potential) * analysis.regular_credit_realization_fraction)
    ibs_net = max(ibs_debit - ibs_credit_modelled, 0)
    ibs_credit_balance = max(ibs_credit_modelled - ibs_debit, 0)
    b2b_cbs_hybrid = _round_cents(Decimal(facts.b2b_revenue_cents) * cbs_rate)
    b2b_ibs_hybrid = _round_cents(Decimal(facts.b2b_revenue_cents) * rules.ibs_regular_rate_fraction)
    hybrid_charge = das_outros + cbs_net + ibs_net

    scenario_rows = [
        {
            "ID_CENARIO": baseline_id,
            "REGIME_CONSUMO": _BASELINE_REGIME,
            "RECEITA_MES_CENTS": facts.revenue_cents,
            "RBT12_CENTS": rbt12_cents,
            "ALIQUOTA_EFETIVA_SIMPLES": effective_rate,
            "DAS_TOTAL_CENTS": das_total,
            "DAS_CBS_CENTS": das_cbs,
            "DAS_IBS_CENTS": das_ibs,
            "DAS_OUTROS_CENTS": das_outros,
            "CBS_REGULAR_RATE_FRACTION": None,
            "CBS_RATE_SOURCE": None,
            "CBS_DEBITO_REGULAR_CENTS": None,
            "CBS_CREDITO_EMPRESA_POTENCIAL_CENTS": 0,
            "CBS_CREDITO_EMPRESA_MODELADO_CENTS": None,
            "CBS_VALOR_LIQUIDO_MODELADO_CENTS": None,
            "CBS_SALDO_CREDOR_MODELADO_CENTS": None,
            "IBS_REGULAR_RATE_FRACTION": None,
            "IBS_DEBITO_REGULAR_CENTS": None,
            "IBS_CREDITO_EMPRESA_POTENCIAL_CENTS": 0,
            "IBS_CREDITO_EMPRESA_MODELADO_CENTS": None,
            "IBS_VALOR_LIQUIDO_MODELADO_CENTS": None,
            "IBS_SALDO_CREDOR_MODELADO_CENTS": None,
            "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS": das_total,
            "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS": b2b_cbs_puro,
            "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS": b2b_ibs_puro,
            "STATUS_RESULTADO": _STATUS_NORMATIVE,
            "VERSAO_REGRA": rules.rule_version,
        },
        {
            "ID_CENARIO": alternative_id,
            "REGIME_CONSUMO": _HYBRID_REGIME,
            "RECEITA_MES_CENTS": facts.revenue_cents,
            "RBT12_CENTS": rbt12_cents,
            "ALIQUOTA_EFETIVA_SIMPLES": effective_rate,
            "DAS_TOTAL_CENTS": None,
            "DAS_CBS_CENTS": None,
            "DAS_IBS_CENTS": None,
            "DAS_OUTROS_CENTS": das_outros,
            "CBS_REGULAR_RATE_FRACTION": cbs_rate,
            "CBS_RATE_SOURCE": cbs_rate_source,
            "CBS_DEBITO_REGULAR_CENTS": cbs_debit,
            "CBS_CREDITO_EMPRESA_POTENCIAL_CENTS": cbs_credit_potential,
            "CBS_CREDITO_EMPRESA_MODELADO_CENTS": cbs_credit_modelled,
            "CBS_VALOR_LIQUIDO_MODELADO_CENTS": cbs_net,
            "CBS_SALDO_CREDOR_MODELADO_CENTS": cbs_credit_balance,
            "IBS_REGULAR_RATE_FRACTION": rules.ibs_regular_rate_fraction,
            "IBS_DEBITO_REGULAR_CENTS": ibs_debit,
            "IBS_CREDITO_EMPRESA_POTENCIAL_CENTS": ibs_credit_potential,
            "IBS_CREDITO_EMPRESA_MODELADO_CENTS": ibs_credit_modelled,
            "IBS_VALOR_LIQUIDO_MODELADO_CENTS": ibs_net,
            "IBS_SALDO_CREDOR_MODELADO_CENTS": ibs_credit_balance,
            "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS": hybrid_charge,
            "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS": b2b_cbs_hybrid,
            "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS": b2b_ibs_hybrid,
            "STATUS_RESULTADO": _STATUS_ANALYTICAL,
            "VERSAO_REGRA": rules.rule_version,
        },
    ]
    scenario_results = pd.DataFrame(scenario_rows, columns=SIMPLES_2027_SCENARIO_RESULT_COLUMNS, dtype=object)
    comparison_results = _build_comparison(scenario_results, baseline_id, alternative_id)
    return Simples2027CounterfactualReport(
        baseline_scenario_id=baseline_id,
        alternative_scenario_id=alternative_id,
        scenario_results=scenario_results.copy(deep=True),
        comparison_results=comparison_results.copy(deep=True),
        cbs_rate_used_fraction=cbs_rate,
        cbs_rate_source=cbs_rate_source,
        cbs_break_even_rate_fraction=_break_even_cbs_rate(facts, das_total, rules, analysis),
    )


def _resolve_cbs_2027_rate(
    rules: EffectiveSimples2027Rules,
    analysis: Simples2027AnalysisAssumptions,
) -> tuple[Decimal, str]:
    if rules.cbs_regular_rate_fraction is not None:
        return rules.cbs_regular_rate_fraction, "normative"
    return analysis.cbs_analysis_rate_fraction, "analysis"


def _required_analysis_keys(*, require_cbs_analysis_rate: bool) -> tuple[str, ...]:
    if require_cbs_analysis_rate:
        return _REQUIRED_ANALYSIS_KEYS
    return ("REGULAR_CREDIT_REALIZATION_FRACTION",)


def _validate_required_analysis_parameters(
    analysis_parameters: pd.DataFrame,
    *,
    require_cbs_analysis_rate: bool,
) -> list[ValidationIssue]:
    if tuple(analysis_parameters.columns) != TAX_ANALYSIS_PARAMETER_COLUMNS:
        return []
    params = _normalize_analysis_parameters(analysis_parameters)
    values = _analysis_value_map(params)
    issues: list[ValidationIssue] = []
    for key in _required_analysis_keys(require_cbs_analysis_rate=require_cbs_analysis_rate):
        if key not in values:
            issues.append(ValidationIssue("missing_simples_2027_analysis_parameter_key", f"Chave analítica necessária ao recorte Simples 2027 ausente: {key}."))
    return issues


def _validate_scenario_pair(baseline: pd.Series, alternative: pd.Series) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    baseline_id = _clean_string(baseline["ID_CENARIO"])
    alternative_id = _clean_string(alternative["ID_CENARIO"])
    if _clean_string(baseline["REGIME_ENTIDADE"]) != _SUPPORTED_ENTITY_REGIME or _clean_string(alternative["REGIME_ENTIDADE"]) != _SUPPORTED_ENTITY_REGIME:
        issues.append(ValidationIssue("simples_2027_entity_out_of_scope", "Ambos os cenários devem ter REGIME_ENTIDADE=simples_nacional."))
    if _clean_string(baseline["REGIME_CONSUMO"]) != _BASELINE_REGIME:
        issues.append(ValidationIssue("simples_2027_invalid_baseline", "Baseline deve ter REGIME_CONSUMO=simples_ibs_cbs_das.", scenario_id=baseline_id))
    if _clean_string(alternative["REGIME_CONSUMO"]) != _HYBRID_REGIME:
        issues.append(ValidationIssue("simples_2027_invalid_alternative", "Alternativo deve ter REGIME_CONSUMO=ibs_cbs_regime_regular.", scenario_id=alternative_id))
    if _clean_string(baseline["ID_ENTIDADE"]) != _clean_string(alternative["ID_ENTIDADE"]):
        issues.append(ValidationIssue("simples_2027_entity_out_of_scope", "Cenários ativos devem apontar para a mesma entidade."))
    if _clean_string(baseline["ID_VERSAO_NORMATIVA"]) != _clean_string(alternative["ID_VERSAO_NORMATIVA"]):
        issues.append(ValidationIssue("simples_2027_normative_parameters_invalid", "Cenários ativos devem usar a mesma versão normativa."))
    for row, scenario_id in ((baseline, baseline_id), (alternative, alternative_id)):
        reference_date = _coerce_date_or_none(row["DT_REFERENCIA_NORMATIVA"])
        if reference_date is None or not (_FIRST_SEMESTER_START <= reference_date <= _FIRST_SEMESTER_END):
            issues.append(ValidationIssue("simples_2027_invalid_reference_date", "Referência normativa deve estar no primeiro semestre de 2027.", scenario_id=scenario_id))
    return issues


def _validate_entity(entity: dict[str, object], entity_id: str, rules: EffectiveSimples2027Rules | None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required = ("TIPO_PESSOA", "ATIVIDADE", "OPTANTE_SIMPLES", "ANEXO_SIMPLES", "RBT12_CENTS")
    for attribute in required:
        if attribute not in entity:
            issues.append(ValidationIssue("simples_2027_entity_out_of_scope", f"ENTIDADE sem atributo obrigatório: {attribute}.", entity_id=entity_id))
    if issues:
        return issues
    if _clean_string(entity["TIPO_PESSOA"]) != _SUPPORTED_ENTITY_TYPE:
        issues.append(ValidationIssue("simples_2027_entity_out_of_scope", "TIPO_PESSOA deve ser pj.", entity_id=entity_id))
    if _clean_string(entity["ATIVIDADE"]) != _SUPPORTED_ACTIVITY:
        issues.append(ValidationIssue("simples_2027_entity_out_of_scope", "ATIVIDADE fora do recorte de comércio.", entity_id=entity_id))
    if entity["OPTANTE_SIMPLES"] is not True:
        issues.append(ValidationIssue("simples_2027_entity_out_of_scope", "OPTANTE_SIMPLES deve ser true.", entity_id=entity_id))
    if _clean_string(entity["ANEXO_SIMPLES"]) != _SUPPORTED_ANNEX:
        issues.append(ValidationIssue("simples_2027_entity_out_of_scope", "ANEXO_SIMPLES deve ser I.", entity_id=entity_id))
    rbt12 = _safe_int(entity["RBT12_CENTS"])
    max_rbt12 = max((band.max_rbt12_cents for band in rules.annex_i_bands), default=None) if rules is not None else None
    if rbt12 is None or rbt12 <= 0 or (max_rbt12 is not None and rbt12 > max_rbt12):
        issues.append(ValidationIssue("simples_2027_rbt12_out_of_scope", "RBT12_CENTS fora do recorte do Anexo I carregado.", entity_id=entity_id))
    return issues


def _validate_facts(events: pd.DataFrame, fiscal_event_attributes: pd.DataFrame) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    fiscal_by_event = _fiscal_attribute_map(fiscal_event_attributes)
    has_purchase = False
    has_b2b = False
    has_b2c = False
    normalized = _normalize_events_for_tax(events)
    for _, event in normalized.iterrows():
        event_type = _clean_string(event["TIPO_EVENTO"])
        if event_type not in _SUPPORTED_EVENT_TYPES:
            continue
        event_id = _clean_string(event["ID_EVENTO"])
        attrs = fiscal_by_event.get(event_id, {})
        if _clean_string(event["NATUREZA"]) != EventNature.GOOD.value:
            issues.append(ValidationIssue("simples_2027_event_nature_out_of_scope", "EVENTOS.NATUREZA deve ser bem.", event_id=event_id))
        if _clean_string(attrs.get("AMBITO_OPERACAO")) != _SUPPORTED_SCOPE:
            issues.append(ValidationIssue("simples_2027_operation_scope_out_of_scope", "AMBITO_OPERACAO deve ser domestica.", event_id=event_id))
        if event_type in _SUPPORTED_PURCHASE_TYPES:
            supplier_regime = _clean_string(attrs.get("REGIME_FORNECEDOR"))
            destination = _clean_string(attrs.get("DESTINACAO_AQUISICAO"))
            if supplier_regime != _SUPPORTED_SUPPLIER_REGIME:
                issues.append(ValidationIssue("simples_2027_purchase_supplier_out_of_scope", "Compra elegível requer fornecedor no regime regular.", event_id=event_id))
            if destination != _SUPPORTED_PURCHASE_DESTINATION:
                issues.append(ValidationIssue("simples_2027_purchase_destination_out_of_scope", "Compra elegível requer DESTINACAO_AQUISICAO=revenda.", event_id=event_id))
            if supplier_regime == _SUPPORTED_SUPPLIER_REGIME and destination == _SUPPORTED_PURCHASE_DESTINATION:
                has_purchase = True
        if event_type in _SUPPORTED_SALE_TYPES:
            customer_type = _clean_string(attrs.get("TIPO_CLIENTE"))
            acquirer_regime = _clean_string(attrs.get("REGIME_ADQUIRENTE"))
            if not acquirer_regime:
                issues.append(ValidationIssue("simples_2027_missing_acquirer_regime", "Venda suportada requer REGIME_ADQUIRENTE.", event_id=event_id))
            if customer_type == "b2b":
                if acquirer_regime != _SUPPORTED_B2B_ACQUIRER_REGIME:
                    issues.append(ValidationIssue("simples_2027_b2b_acquirer_regime_out_of_scope", "Venda B2B requer adquirente no regime regular de IBS/CBS.", event_id=event_id))
                elif _clean_string(event["NATUREZA"]) == EventNature.GOOD.value and _clean_string(attrs.get("AMBITO_OPERACAO")) == _SUPPORTED_SCOPE:
                    has_b2b = True
            elif customer_type == "b2c":
                if acquirer_regime != _SUPPORTED_B2C_ACQUIRER_REGIME:
                    issues.append(ValidationIssue("simples_2027_b2c_acquirer_regime_out_of_scope", "Venda B2C requer REGIME_ADQUIRENTE=consumidor_final.", event_id=event_id))
                elif _clean_string(event["NATUREZA"]) == EventNature.GOOD.value and _clean_string(attrs.get("AMBITO_OPERACAO")) == _SUPPORTED_SCOPE:
                    has_b2c = True
            else:
                issues.append(ValidationIssue("simples_2027_sale_customer_type_out_of_scope", "Venda suportada requer TIPO_CLIENTE=b2b ou b2c.", event_id=event_id))
    if not has_purchase:
        issues.append(ValidationIssue("simples_2027_missing_eligible_purchase", "Fixture demonstrativo requer ao menos uma compra elegível."))
    if not has_b2b:
        issues.append(ValidationIssue("simples_2027_missing_b2b_sale", "Fixture demonstrativo requer ao menos uma venda B2B."))
    if not has_b2c:
        issues.append(ValidationIssue("simples_2027_missing_b2c_sale", "Fixture demonstrativo requer ao menos uma venda B2C."))
    return issues


def _measure_facts(events: pd.DataFrame, fiscal_event_attributes: pd.DataFrame) -> _MeasuredFacts:
    fiscal_by_event = _fiscal_attribute_map(fiscal_event_attributes)
    revenue = 0
    purchases = 0
    b2b = 0
    b2c = 0
    for _, event in _normalize_events_for_tax(events).iterrows():
        event_type = _clean_string(event["TIPO_EVENTO"])
        event_id = _clean_string(event["ID_EVENTO"])
        value = _require_int(event["VL_EVENTO_CENTS"], "VL_EVENTO_CENTS")
        attrs = fiscal_by_event.get(event_id, {})
        if event_type in _SUPPORTED_PURCHASE_TYPES:
            if _clean_string(attrs.get("AMBITO_OPERACAO")) == _SUPPORTED_SCOPE and _clean_string(attrs.get("REGIME_FORNECEDOR")) == _SUPPORTED_SUPPLIER_REGIME and _clean_string(attrs.get("DESTINACAO_AQUISICAO")) == _SUPPORTED_PURCHASE_DESTINATION:
                purchases += value
        elif event_type in _SUPPORTED_SALE_TYPES:
            revenue += value
            customer_type = _clean_string(attrs.get("TIPO_CLIENTE"))
            acquirer_regime = _clean_string(attrs.get("REGIME_ADQUIRENTE"))
            if customer_type == "b2b" and acquirer_regime == _SUPPORTED_B2B_ACQUIRER_REGIME:
                b2b += value
            elif customer_type == "b2c" and acquirer_regime == _SUPPORTED_B2C_ACQUIRER_REGIME:
                b2c += value
    return _MeasuredFacts(revenue, purchases, b2b, b2c)


def _select_annex_band(rules: EffectiveSimples2027Rules, rbt12_cents: int) -> SimplesAnnexBand:
    for band in rules.annex_i_bands:
        if rbt12_cents <= band.max_rbt12_cents:
            return band
    raise SchemaValidationError("RBT12_CENTS acima das faixas carregadas.")


def _effective_rate(rbt12_cents: int, band: SimplesAnnexBand) -> Decimal:
    return (Decimal(rbt12_cents) * band.nominal_rate_fraction - Decimal(band.deduction_cents)) / Decimal(rbt12_cents)


def _build_comparison(scenario_results: pd.DataFrame, baseline_id: str, alternative_id: str) -> pd.DataFrame:
    baseline = scenario_results.loc[scenario_results["ID_CENARIO"] == baseline_id].iloc[0]
    alternative = scenario_results.loc[scenario_results["ID_CENARIO"] == alternative_id].iloc[0]
    metrics = (
        ("ENCARGO_TRIBUTARIO_COMPARAVEL", "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"),
        ("CREDITO_EMPRESA_CBS_POTENCIAL", "CBS_CREDITO_EMPRESA_POTENCIAL_CENTS"),
        ("CREDITO_EMPRESA_IBS_POTENCIAL", "IBS_CREDITO_EMPRESA_POTENCIAL_CENTS"),
        ("CLIENTE_B2B_CREDITO_CBS_POTENCIAL", "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS"),
        ("CLIENTE_B2B_CREDITO_IBS_POTENCIAL", "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS"),
    )
    rows = []
    for metric, column in metrics:
        baseline_value = _optional_int(baseline[column])
        alternative_value = _optional_int(alternative[column])
        rows.append(
            {
                "ID_CENARIO_BASE": baseline_id,
                "ID_CENARIO": alternative_id,
                "METRICA": metric,
                "BASELINE_CENTS": baseline_value,
                "ALTERNATIVO_CENTS": alternative_value,
                "DELTA_CENTS": None if baseline_value is None or alternative_value is None else alternative_value - baseline_value,
                "STATUS_BASELINE": baseline["STATUS_RESULTADO"],
                "STATUS_ALTERNATIVO": alternative["STATUS_RESULTADO"],
            }
        )
    return pd.DataFrame(rows, columns=SIMPLES_2027_COMPARISON_COLUMNS, dtype=object)


def _break_even_cbs_rate(
    facts: _MeasuredFacts,
    das_total_cents: int,
    rules: EffectiveSimples2027Rules,
    analysis: Simples2027AnalysisAssumptions,
) -> Decimal | None:
    denominator = Decimal(facts.revenue_cents) - analysis.regular_credit_realization_fraction * Decimal(facts.eligible_purchase_cents)
    if denominator <= 0:
        return None
    numerator = Decimal(das_total_cents) * (rules.cbs_share_fraction + rules.ibs_share_fraction)
    return numerator / denominator - rules.ibs_regular_rate_fraction


def _active_scenarios(tax_scenarios: pd.DataFrame) -> pd.DataFrame:
    scenarios = tax_scenarios.copy(deep=True)
    scenarios = scenarios.loc[:, list(TAX_SCENARIO_COLUMNS)]
    return scenarios.loc[scenarios["ATIVO"].map(_parse_bool_or_none) == True].copy(deep=True)  # noqa: E712


def _get_scenario(tax_context: TaxContext, scenario_id: str) -> pd.Series:
    selected = tax_context.tax_scenarios.loc[tax_context.tax_scenarios["ID_CENARIO"].astype(str) == str(scenario_id)]
    if len(selected) != 1:
        raise SchemaValidationError(f"Cenário tributário ausente ou duplicado: {scenario_id}.")
    return selected.iloc[0]


def _entity_attribute_map(entity_profile: pd.DataFrame, entity_id: str) -> dict[str, object]:
    if not {"ID_ENTIDADE", "ATRIBUTO", "VALOR", "TIPO_VALOR"}.issubset(entity_profile.columns):
        return {}
    entity_rows = entity_profile[entity_profile["ID_ENTIDADE"].astype(str) == str(entity_id)]
    return {str(row["ATRIBUTO"]).strip(): _parse_generic_value(row["VALOR"], row["TIPO_VALOR"]) for _, row in entity_rows.iterrows()}


def _fiscal_attribute_map(fiscal_event_attributes: pd.DataFrame) -> dict[str, dict[str, object]]:
    if not {"ID_EVENTO", "ATRIBUTO_FISCAL", "VALOR", "TIPO_VALOR"}.issubset(fiscal_event_attributes.columns):
        return {}
    grouped: dict[str, dict[str, object]] = {}
    for _, row in fiscal_event_attributes.iterrows():
        grouped.setdefault(_clean_string(row["ID_EVENTO"]), {})[_clean_string(row["ATRIBUTO_FISCAL"])] = _parse_generic_value(row["VALOR"], row["TIPO_VALOR"])
    return grouped


def _normalize_events_for_tax(events: pd.DataFrame) -> pd.DataFrame:
    normalized = events.loc[:, list(EVENT_COLUMNS)].copy()
    for column in ("ID_EVENTO", "TIPO_EVENTO", "NATUREZA"):
        normalized[column] = normalized[column].map(_clean_string)
    return normalized


def _normalize_analysis_parameters(analysis_parameters: pd.DataFrame) -> pd.DataFrame:
    params = analysis_parameters.copy()
    for column in TAX_ANALYSIS_PARAMETER_COLUMNS:
        params[column] = params[column].map(_clean_string)
    return params.loc[:, list(TAX_ANALYSIS_PARAMETER_COLUMNS)]


def _analysis_value_map(params: pd.DataFrame) -> dict[str, object]:
    return {row["CHAVE_PARAM"]: row["VALOR"] for _, row in params.iterrows() if row["CHAVE_PARAM"] != ""}


def _parse_parameter_value(row: pd.Series) -> object:
    return _parse_generic_value(row["VALOR"], row["TIPO_VALOR"])


def _parse_generic_value(value: object, value_type: object) -> object:
    kind = _clean_string(value_type)
    if kind == ScalarValueType.STRING.value:
        return _clean_string(value)
    if kind == ScalarValueType.INTEGER.value:
        return _parse_int(value)
    if kind == ScalarValueType.DECIMAL.value:
        return _parse_decimal(value)
    if kind == ScalarValueType.BOOLEAN.value:
        return _parse_bool(value)
    if kind == ScalarValueType.DATE.value:
        return _require_date(value, "VALOR")
    raise SchemaValidationError(f"TIPO_VALOR não suportado em Simples 2027: {value_type!r}.")


def _is_effective_on(row: pd.Series, reference_date: date) -> bool:
    start = _require_date(row["VIG_INI"], "VIG_INI")
    end_raw = row["VIG_FIM"]
    end = None if _clean_string(end_raw) == "" else _require_date(end_raw, "VIG_FIM")
    return start <= reference_date and (end is None or reference_date <= end)


def _round_cents(value: Decimal) -> int:
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _raise_report(stage: str, report: ValidationReport) -> None:
    details = "; ".join(f"{issue.scenario_id or issue.event_id or issue.entity_id or '-'}:{issue.code}: {issue.message}" for issue in report.issues[:5])
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


def _coerce_date_or_none(value: object) -> date | None:
    if value is None or pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return parse_iso_date(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _require_date(value: object, field_name: str) -> date:
    parsed = _coerce_date_or_none(value)
    if parsed is None:
        raise SchemaValidationError(f"{field_name} deve ser data.")
    return parsed


def _parse_bool_or_none(value: object) -> bool | None:
    try:
        return _parse_bool(value)
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


def _parse_int(value: object) -> int:
    if isinstance(value, bool) or isinstance(value, float):
        raise SchemaValidationError(f"Inteiro inválido: {value!r}.")
    try:
        return int(_clean_string(value))
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(f"Inteiro inválido: {value!r}.") from exc


def _safe_int(value: object) -> int | None:
    try:
        return _parse_int(value)
    except SchemaValidationError:
        return None


def _optional_int(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    return _parse_int(value)


def _parse_decimal(value: object) -> Decimal:
    if isinstance(value, float):
        raise SchemaValidationError("Decimal normativo/analítico não deve usar float.")
    try:
        return Decimal(_clean_string(value))
    except (InvalidOperation, ValueError) as exc:
        raise SchemaValidationError(f"Decimal inválido: {value!r}.") from exc


def _safe_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return _parse_decimal(value)
    except SchemaValidationError:
        return None


def _require_decimal(value: object, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise SchemaValidationError(f"{field_name} deve ser Decimal.")
    return value


def _require_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SchemaValidationError(f"{field_name} deve ser int.")
    return value


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaValidationError(f"{field_name} deve ser string não vazia.")
    return value
