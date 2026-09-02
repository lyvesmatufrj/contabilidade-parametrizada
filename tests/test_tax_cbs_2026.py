from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from accounting_sim.canonical import (
    ENTITY_PROFILE_COLUMNS,
    EVENT_COLUMNS,
    FISCAL_EVENT_ATTRIBUTE_COLUMNS,
    TAX_ASSESSMENT_RESULT_COLUMNS,
    TAX_OPERATION_RESULT_COLUMNS,
    TAX_PARAMETER_COLUMNS,
    TAX_SCENARIO_COLUMNS,
    EventClass,
    EventDirection,
    EventNature,
    Origin,
    PaymentTerm,
    SchemaValidationError,
)
from accounting_sim.tax_cbs_2026 import (
    CBS_2026_REQUIRED_PARAMETER_KEYS,
    Cbs2026Result,
    EffectiveCbs2026Rules,
    assess_cbs_2026,
    calculate_cbs_2026_operations,
    run_cbs_2026,
    select_effective_cbs_2026_rules,
    validate_cbs_2026_admissibility,
)
from accounting_sim.tax_context import TaxContext, build_empty_tax_context, validate_tax_context
from accounting_sim.events import EVENT_SPEC_VERSION


SCENARIO_ID = "CBS_2026_BASE"
ENTITY_ID = "ENT_CBS_2026"
NORMATIVE_VERSION = "CBS_2026_08_31_V1"
RULE_VERSION = "cbs_2026_regular_nfe55_v1"


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID_EVENTO": "E001",
                "DT_EVENTO": date(2026, 8, 3),
                "CLASSE_EVENTO": EventClass.TRANSACTION.value,
                "TIPO_EVENTO": "compra_mercadoria_a_vista",
                "DIRECAO": EventDirection.IN.value,
                "NATUREZA": EventNature.GOOD.value,
                "DESCRICAO": "Compra para revenda com base fiscal distinta",
                "VL_EVENTO_CENTS": 101000,
                "VL_CUSTO_CENTS": pd.NA,
                "MEIO_FINANCEIRO": "caixa",
                "CATEGORIA_DESPESA": pd.NA,
                "COD_PART": "FORN001",
                "COND_PAGTO": PaymentTerm.CASH.value,
                "DOC_REF": "NFe-001",
                "HIST": "Compra para revenda",
                "ORIGEM": Origin.SYNTHETIC.value,
                "SPEC_VERSION": EVENT_SPEC_VERSION,
            },
            {
                "ID_EVENTO": "E002",
                "DT_EVENTO": date(2026, 8, 10),
                "CLASSE_EVENTO": EventClass.TRANSACTION.value,
                "TIPO_EVENTO": "venda_a_prazo",
                "DIRECAO": EventDirection.OUT.value,
                "NATUREZA": EventNature.GOOD.value,
                "DESCRICAO": "Venda tributada integralmente",
                "VL_EVENTO_CENTS": 200000,
                "VL_CUSTO_CENTS": 100000,
                "MEIO_FINANCEIRO": "clientes",
                "CATEGORIA_DESPESA": pd.NA,
                "COD_PART": "CLI001",
                "COND_PAGTO": PaymentTerm.CREDIT.value,
                "DOC_REF": "NFe-002",
                "HIST": "Venda tributada integralmente",
                "ORIGEM": Origin.SYNTHETIC.value,
                "SPEC_VERSION": EVENT_SPEC_VERSION,
            },
            {
                "ID_EVENTO": "E003",
                "DT_EVENTO": date(2026, 8, 12),
                "CLASSE_EVENTO": EventClass.TRANSACTION.value,
                "TIPO_EVENTO": "aporte_capital",
                "DIRECAO": EventDirection.IN.value,
                "NATUREZA": EventNature.FINANCIAL.value,
                "DESCRICAO": "Evento contábil sem operação CBS no recorte",
                "VL_EVENTO_CENTS": 500000,
                "VL_CUSTO_CENTS": pd.NA,
                "MEIO_FINANCEIRO": "caixa",
                "CATEGORIA_DESPESA": pd.NA,
                "COD_PART": pd.NA,
                "COND_PAGTO": PaymentTerm.NA.value,
                "DOC_REF": "CAP-001",
                "HIST": "Integralizacao de capital",
                "ORIGEM": Origin.SYNTHETIC.value,
                "SPEC_VERSION": EVENT_SPEC_VERSION,
            },
        ],
        columns=EVENT_COLUMNS,
    )


def _entity_profile() -> pd.DataFrame:
    rows = [
        ("TIPO_PESSOA", "pj", "str"),
        ("ATIVIDADE", "comercio_revenda_mercadorias", "str"),
        ("CONTRIBUINTE_ICMS", "true", "bool"),
        ("CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026", "true", "bool"),
    ]
    return pd.DataFrame(
        [
            {
                "ID_ENTIDADE": ENTITY_ID,
                "ATRIBUTO": attribute,
                "VALOR": value,
                "TIPO_VALOR": value_type,
                "ORIGEM": Origin.SYNTHETIC.value,
            }
            for attribute, value, value_type in rows
        ],
        columns=ENTITY_PROFILE_COLUMNS,
    )


def _tax_scenarios() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID_CENARIO": SCENARIO_ID,
                "ID_ENTIDADE": ENTITY_ID,
                "DESCRICAO": "CBS 2026 regular NF-e 55",
                "E_BASELINE": True,
                "DT_REFERENCIA_NORMATIVA": date(2026, 8, 31),
                "REGIME_ENTIDADE": "nao_optante_simples_mei",
                "REGIME_IR": "",
                "REGIME_CONSUMO": "cbs_regime_regular",
                "REGIME_ESPECIAL": "",
                "ID_VERSAO_NORMATIVA": NORMATIVE_VERSION,
                "ATIVO": True,
            }
        ],
        columns=TAX_SCENARIO_COLUMNS,
    )


def _parameter(
    key: str,
    value: str,
    value_type: str,
    source_type: str,
    title: str,
    url: str,
    device: str,
    vig_ini: str = "2026-01-01",
    vig_fim: str = "",
) -> dict[str, object]:
    return {
        "ID_PARAM": f"PARAM_{key}",
        "ID_VERSAO_NORMATIVA": NORMATIVE_VERSION,
        "ID_REGRA": "CBS_REGULAR_2026_NFE55",
        "TRIBUTO": "CBS",
        "CHAVE_PARAM": key,
        "VALOR": value,
        "TIPO_VALOR": value_type,
        "TIPO_FONTE": source_type,
        "FONTE_TITULO": title,
        "FONTE_URL": url,
        "DISPOSITIVO": device,
        "VERSAO_NORMA": "snapshot_2026_08_31",
        "VIG_INI": vig_ini,
        "VIG_FIM": vig_fim,
        "DATA_CONSULTA": "2026-09-02",
        "VERSAO_REGRA": RULE_VERSION,
    }


def _tax_parameters() -> pd.DataFrame:
    rows = [
        _parameter(
            "CBS_RATE_FRACTION",
            "0.009",
            "decimal",
            "norm",
            "LC 214/2025 compilada",
            "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm",
            "art. 346",
            "2026-01-01",
            "2026-12-31",
        ),
        _parameter(
            "CBS_ASSESSMENT_PERIOD",
            "monthly",
            "str",
            "reg",
            "Decreto 12.955/2026",
            "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12955.htm",
            "art. 43",
        ),
        _parameter(
            "CBS_NFE_MODEL",
            "55",
            "str",
            "oper",
            "Ato Conjunto RFB/CGIBS 01/2025",
            "https://www.in.gov.br/",
            "art. 2, par. 1, I",
        ),
        _parameter(
            "CBS_NFE_MANDATORY_FROM",
            "2026-08-03",
            "date",
            "oper",
            "Ato Conjunto RFB/CGIBS 04/2026",
            "https://www.in.gov.br/",
            "art. 1, I e par. 4",
        ),
        _parameter(
            "CBS_CST_INTEGRAL",
            "000",
            "str",
            "tec",
            "Tabela CST IBS/CBS 2026-06-23",
            "https://www.gov.br/",
            "linha CST 000",
        ),
        _parameter(
            "CBS_CCLASSTRIB_INTEGRAL",
            "000001",
            "str",
            "tec",
            "Tabela cClassTrib IBS/CBS 2026-06-23",
            "https://www.gov.br/",
            "linha cClassTrib 000001",
        ),
        _parameter(
            "CBS_VCBS_TOLERANCE_CENTS",
            "1",
            "decimal",
            "tec",
            "NF-e Nota Tecnica 2025.002 v1.51",
            "https://www.nfe.fazenda.gov.br/",
            "regra UB67-10",
        ),
        _parameter(
            "CBS_CREDIT_WAIVER_IF_MODALITIES_ABSENT",
            "true",
            "bool",
            "norm",
            "LC 214/2025 compilada",
            "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm",
            "art. 48",
        ),
        _parameter(
            "CBS_SPLIT_PAYMENT_IMPLEMENTED",
            "false",
            "bool",
            "oper",
            "NF-e Nota Tecnica 2026.006 v1.00",
            "https://www.nfe.fazenda.gov.br/",
            "implantacao futura de grupo split",
            "2026-01-01",
            "2026-08-31",
        ),
        _parameter(
            "CBS_BUYER_COLLECTION_IMPLEMENTED",
            "false",
            "bool",
            "oper",
            "Documentacao tecnica RTC 2026",
            "https://www.gov.br/",
            "sem recolhimento pelo adquirente no recorte",
            "2026-01-01",
            "2026-08-31",
        ),
        _parameter(
            "CBS_2026_COLLECTION_WAIVER_IF_ACCESSORY_COMPLIANT",
            "true",
            "bool",
            "reg",
            "Decreto 12.955/2026",
            "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12955.htm",
            "art. 464",
            "2026-01-01",
            "2026-12-31",
        ),
    ]
    return pd.DataFrame(rows, columns=TAX_PARAMETER_COLUMNS)


def _fiscal_event_attributes() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(event_id: str, attribute: str, value: str, value_type: str) -> None:
        rows.append(
            {
                "ID_EVENTO": event_id,
                "ATRIBUTO_FISCAL": attribute,
                "VALOR": value,
                "TIPO_VALOR": value_type,
                "ORIGEM": Origin.SYNTHETIC.value,
            }
        )

    for event_id, nfe_number, supply_date, base_cents, cbs_cents in (
        ("E001", "1" * 44, "2026-08-03", "100000", "900"),
        ("E002", "2" * 44, "2026-08-10", "200000", "1800"),
    ):
        add(event_id, "MODELO_DFE", "55", "str")
        add(event_id, "CHAVE_NFE", nfe_number, "str")
        add(event_id, "PROTOCOLO_AUTORIZACAO", f"13526000000000{event_id[-1]}", "str")
        add(event_id, "STATUS_DFE", "autorizado_nao_cancelado", "str")
        add(event_id, "DT_FORNECIMENTO", supply_date, "date")
        add(event_id, "QTD_ITENS_DFE", "1", "int")
        add(event_id, "CST_IBS_CBS", "000", "str")
        add(event_id, "CCLASSTRIB", "000001", "str")
        add(event_id, "VBC_CENTS", base_cents, "int")
        add(event_id, "PCBS_PERCENT", "0.9", "decimal")
        add(event_id, "VCBS_CENTS", cbs_cents, "int")
    add("E001", "DESTINACAO_AQUISICAO", "revenda", "str")

    return pd.DataFrame(rows, columns=FISCAL_EVENT_ATTRIBUTE_COLUMNS)


def _tax_context(
    *,
    entity_profile: pd.DataFrame | None = None,
    fiscal_event_attributes: pd.DataFrame | None = None,
    tax_scenarios: pd.DataFrame | None = None,
    tax_parameters: pd.DataFrame | None = None,
) -> TaxContext:
    return TaxContext(
        entity_profile=_entity_profile() if entity_profile is None else entity_profile,
        fiscal_event_attributes=(
            _fiscal_event_attributes()
            if fiscal_event_attributes is None
            else fiscal_event_attributes
        ),
        tax_scenarios=_tax_scenarios() if tax_scenarios is None else tax_scenarios,
        tax_parameters=_tax_parameters() if tax_parameters is None else tax_parameters,
    )


def _replace_entity_attr(context: TaxContext, attribute: str, value: str) -> TaxContext:
    frame = context.entity_profile.copy(deep=True)
    frame.loc[frame["ATRIBUTO"] == attribute, "VALOR"] = value
    return _tax_context(
        entity_profile=frame,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=context.tax_scenarios,
        tax_parameters=context.tax_parameters,
    )


def _replace_scenario(context: TaxContext, column: str, value: object) -> TaxContext:
    frame = context.tax_scenarios.copy(deep=True)
    frame.loc[frame["ID_CENARIO"] == SCENARIO_ID, column] = value
    return _tax_context(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=frame,
        tax_parameters=context.tax_parameters,
    )


def _replace_parameter(
    context: TaxContext, key: str, column: str, value: object
) -> TaxContext:
    frame = context.tax_parameters.copy(deep=True)
    frame.loc[frame["CHAVE_PARAM"] == key, column] = value
    return _tax_context(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=context.tax_scenarios,
        tax_parameters=frame,
    )


def _drop_parameter(context: TaxContext, key: str) -> TaxContext:
    frame = context.tax_parameters.loc[
        context.tax_parameters["CHAVE_PARAM"] != key
    ].copy()
    return _tax_context(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=context.tax_scenarios,
        tax_parameters=frame,
    )


def _duplicate_parameter(context: TaxContext, key: str) -> TaxContext:
    frame = context.tax_parameters.copy(deep=True)
    duplicate = frame.loc[frame["CHAVE_PARAM"] == key].copy()
    duplicate.loc[:, "ID_PARAM"] = duplicate["ID_PARAM"] + "_DUP"
    return _tax_context(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=context.tax_scenarios,
        tax_parameters=pd.concat([frame, duplicate], ignore_index=True),
    )


def _replace_fiscal_attr(
    context: TaxContext, event_id: str, attribute: str, value: str
) -> TaxContext:
    frame = context.fiscal_event_attributes.copy(deep=True)
    mask = (frame["ID_EVENTO"] == event_id) & (frame["ATRIBUTO_FISCAL"] == attribute)
    frame.loc[mask, "VALOR"] = value
    return _tax_context(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=frame,
        tax_scenarios=context.tax_scenarios,
        tax_parameters=context.tax_parameters,
    )


def _drop_fiscal_attr(context: TaxContext, event_id: str, attribute: str) -> TaxContext:
    frame = context.fiscal_event_attributes.loc[
        ~(
            (context.fiscal_event_attributes["ID_EVENTO"] == event_id)
            & (context.fiscal_event_attributes["ATRIBUTO_FISCAL"] == attribute)
        )
    ].copy()
    return _tax_context(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=frame,
        tax_scenarios=context.tax_scenarios,
        tax_parameters=context.tax_parameters,
    )


def _assert_invalid(context: TaxContext, expected_code: str) -> None:
    report = validate_cbs_2026_admissibility(_events(), context, SCENARIO_ID)
    assert not report.ok
    assert expected_code in {issue.code for issue in report.issues}


def test_empty_spec08_tax_context_remains_valid() -> None:
    report = validate_tax_context(build_empty_tax_context(), _events())

    assert report.ok


def test_select_effective_rules_from_versioned_fiscal_param() -> None:
    rules = select_effective_cbs_2026_rules(_tax_context(), SCENARIO_ID)

    assert isinstance(rules, EffectiveCbs2026Rules)
    assert rules.rate_fraction == Decimal("0.009")
    assert rules.cst_integral == "000"
    assert rules.cclasstrib_integral == "000001"
    assert rules.credit_extinction_waived is True


def test_exact_vcbs_document_is_accepted() -> None:
    report = validate_cbs_2026_admissibility(_events(), _tax_context(), SCENARIO_ID)

    assert report.ok


def test_parameters_of_other_normative_version_do_not_leak() -> None:
    context = _tax_context()
    extra = context.tax_parameters.copy(deep=True)
    extra.loc[:, "ID_PARAM"] = extra["ID_PARAM"] + "_OTHER"
    extra.loc[:, "ID_VERSAO_NORMATIVA"] = "CBS_OTHER_VERSION"
    extra.loc[extra["CHAVE_PARAM"] == "CBS_RATE_FRACTION", "VALOR"] = "0.123"
    context = _tax_context(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=context.tax_scenarios,
        tax_parameters=pd.concat([context.tax_parameters, extra], ignore_index=True),
    )

    rules = select_effective_cbs_2026_rules(context, SCENARIO_ID)

    assert rules.rate_fraction == Decimal("0.009")


@pytest.mark.parametrize(
    ("column", "value", "issue_code"),
    [
        ("ATIVO", False, "cbs_scenario_inactive"),
        ("REGIME_ENTIDADE", "simples_nacional", "cbs_entity_regime_out_of_scope"),
        ("REGIME_CONSUMO", "ibs_cbs_outro", "cbs_consumption_regime_out_of_scope"),
        ("REGIME_ESPECIAL", "regime_especial_teste", "cbs_special_regime_out_of_scope"),
        ("DT_REFERENCIA_NORMATIVA", date(2026, 8, 30), "cbs_snapshot_date_out_of_scope"),
    ],
)
def test_chi_t_rejects_scenario_outside_scope(
    column: str, value: object, issue_code: str
) -> None:
    _assert_invalid(_replace_scenario(_tax_context(), column, value), issue_code)


@pytest.mark.parametrize(
    ("attribute", "value", "issue_code"),
    [
        ("TIPO_PESSOA", "pf", "cbs_entity_attribute_out_of_scope"),
        ("ATIVIDADE", "servicos", "cbs_entity_attribute_out_of_scope"),
        ("CONTRIBUINTE_ICMS", "false", "cbs_entity_attribute_out_of_scope"),
        (
            "CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026",
            "false",
            "cbs_entity_attribute_out_of_scope",
        ),
    ],
)
def test_chi_t_rejects_entity_outside_scope(
    attribute: str, value: str, issue_code: str
) -> None:
    _assert_invalid(_replace_entity_attr(_tax_context(), attribute, value), issue_code)


def test_missing_required_entity_attribute_fails() -> None:
    context = _tax_context()
    frame = context.entity_profile.loc[
        context.entity_profile["ATRIBUTO"] != "CONTRIBUINTE_ICMS"
    ].copy()

    _assert_invalid(_tax_context(entity_profile=frame), "cbs_entity_attribute_missing")


def test_missing_parameter_fails() -> None:
    context = _drop_parameter(_tax_context(), "CBS_RATE_FRACTION")

    with pytest.raises(SchemaValidationError, match="CBS.*ausentes"):
        select_effective_cbs_2026_rules(context, SCENARIO_ID)


def test_duplicate_effective_parameter_fails() -> None:
    context = _duplicate_parameter(_tax_context(), "CBS_RATE_FRACTION")

    with pytest.raises(SchemaValidationError, match="CBS duplicado"):
        select_effective_cbs_2026_rules(context, SCENARIO_ID)


def test_expired_parameter_fails() -> None:
    context = _replace_parameter(
        _tax_context(), "CBS_RATE_FRACTION", "VIG_FIM", "2026-08-30"
    )

    with pytest.raises(SchemaValidationError, match="CBS.*ausentes"):
        select_effective_cbs_2026_rules(context, SCENARIO_ID)


def test_invalid_parameter_provenance_fails() -> None:
    context = _replace_parameter(_tax_context(), "CBS_RATE_FRACTION", "FONTE_TITULO", "")

    with pytest.raises(SchemaValidationError, match="FISCAL_PARAM"):
        select_effective_cbs_2026_rules(context, SCENARIO_ID)


@pytest.mark.parametrize(
    "key",
    ["CBS_SPLIT_PAYMENT_IMPLEMENTED", "CBS_BUYER_COLLECTION_IMPLEMENTED"],
)
def test_split_or_buyer_collection_implemented_invalidates_credit_branch(
    key: str,
) -> None:
    context = _replace_parameter(_tax_context(), key, "VALOR", "true")

    with pytest.raises(SchemaValidationError, match="Modalidades.*art. 48"):
        select_effective_cbs_2026_rules(context, SCENARIO_ID)


def test_collection_waiver_rule_false_is_out_of_scope() -> None:
    context = _replace_parameter(
        _tax_context(),
        "CBS_2026_COLLECTION_WAIVER_IF_ACCESSORY_COMPLIANT",
        "VALOR",
        "false",
    )

    with pytest.raises(SchemaValidationError, match="Dispensa"):
        select_effective_cbs_2026_rules(context, SCENARIO_ID)


@pytest.mark.parametrize(
    ("attribute", "value", "issue_code"),
    [
        ("STATUS_DFE", "cancelado", "cbs_document_not_authorized"),
        ("MODELO_DFE", "65", "cbs_nfe_model_invalid"),
        ("CST_IBS_CBS", "010", "cbs_cst_invalid"),
        ("CCLASSTRIB", "000002", "cbs_cclass_invalid"),
        ("PCBS_PERCENT", "1.0", "cbs_pcbs_invalid"),
        ("QTD_ITENS_DFE", "2", "cbs_item_count_out_of_scope"),
        ("DT_FORNECIMENTO", "2026-08-02", "cbs_supply_date_out_of_scope"),
        ("VBC_CENTS", "0", "cbs_base_invalid"),
        ("VCBS_CENTS", "-1", "cbs_vcbs_invalid"),
    ],
)
def test_fiscal_event_attribute_validation(
    attribute: str, value: str, issue_code: str
) -> None:
    _assert_invalid(_replace_fiscal_attr(_tax_context(), "E001", attribute, value), issue_code)


def test_document_without_authorization_protocol_fails() -> None:
    _assert_invalid(
        _replace_fiscal_attr(_tax_context(), "E001", "PROTOCOLO_AUTORIZACAO", ""),
        "empty_fiscal_event_value",
    )


def test_missing_required_fiscal_attribute_fails() -> None:
    _assert_invalid(
        _drop_fiscal_attr(_tax_context(), "E001", "VCBS_CENTS"),
        "cbs_fiscal_attribute_missing",
    )


def test_duplicate_nfe_key_fails() -> None:
    context = _replace_fiscal_attr(_tax_context(), "E002", "CHAVE_NFE", "1" * 44)

    _assert_invalid(context, "cbs_nfe_key_duplicated")


def test_invalid_nfe_key_fails() -> None:
    _assert_invalid(
        _replace_fiscal_attr(_tax_context(), "E001", "CHAVE_NFE", "123"),
        "cbs_nfe_key_invalid",
    )


@pytest.mark.parametrize("delta", [-1, 1])
def test_vcbs_tolerance_one_cent_is_accepted(delta: int) -> None:
    context = _replace_fiscal_attr(_tax_context(), "E001", "VCBS_CENTS", str(900 + delta))

    report = validate_cbs_2026_admissibility(_events(), context, SCENARIO_ID)

    assert report.ok


def test_vcbs_difference_above_tolerance_fails() -> None:
    _assert_invalid(
        _replace_fiscal_attr(_tax_context(), "E001", "VCBS_CENTS", "902"),
        "cbs_vcbs_inconsistent",
    )


def test_document_inside_tolerance_does_not_require_rounding_policy() -> None:
    context = _replace_fiscal_attr(_tax_context(), "E001", "VBC_CENTS", "100001")
    context = _replace_fiscal_attr(context, "E001", "VCBS_CENTS", "900")

    report = validate_cbs_2026_admissibility(_events(), context, SCENARIO_ID)

    assert report.ok


def test_purchase_destination_other_than_resale_fails() -> None:
    _assert_invalid(
        _replace_fiscal_attr(_tax_context(), "E001", "DESTINACAO_AQUISICAO", "uso_consumo"),
        "cbs_purchase_destination_invalid",
    )


def test_operation_uses_documental_base_not_event_amount() -> None:
    result = calculate_cbs_2026_operations(_events(), _tax_context(), SCENARIO_ID)
    purchase = result.loc[result["ID_EVENTO"] == "E001"].iloc[0]

    assert int(purchase["BASE_CENTS"]) == 100000
    assert int(_events().loc[_events()["ID_EVENTO"] == "E001", "VL_EVENTO_CENTS"].iloc[0]) == 101000


def test_operation_rate_and_rule_version_come_from_effective_rules() -> None:
    result = calculate_cbs_2026_operations(_events(), _tax_context(), SCENARIO_ID)

    assert set(result["ALIQUOTA"]) == {Decimal("0.009")}
    assert set(result["VERSAO_REGRA"]) == {RULE_VERSION}


def test_sale_generates_debit_and_purchase_generates_documental_credit() -> None:
    result = calculate_cbs_2026_operations(_events(), _tax_context(), SCENARIO_ID)

    purchase = result.loc[result["ID_EVENTO"] == "E001"].iloc[0]
    sale = result.loc[result["ID_EVENTO"] == "E002"].iloc[0]
    assert int(purchase["CREDITO_CENTS"]) == 900
    assert int(purchase["DEBITO_CENTS"]) == 0
    assert int(sale["DEBITO_CENTS"]) == 1800
    assert int(sale["CREDITO_CENTS"]) == 0


def test_assessment_positive_balance_has_zero_collection_when_compliant() -> None:
    operation_results = calculate_cbs_2026_operations(_events(), _tax_context(), SCENARIO_ID)
    assessment = assess_cbs_2026(operation_results, _tax_context(), SCENARIO_ID)
    row = assessment.iloc[0]

    assert int(operation_results["DEBITO_CENTS"].sum()) == 1800
    assert int(operation_results["CREDITO_CENTS"].sum()) == 900
    assert int(row["S_APUR_CENTS"]) == 900
    assert int(row["T_RECOLHER_CENTS"]) == 0
    assert row["P_CASH_CENTS"] is None
    assert row["E_DRE_CENTS"] is None


def test_credit_balance_generates_c_saldo() -> None:
    context = _replace_fiscal_attr(_tax_context(), "E001", "VBC_CENTS", "300000")
    context = _replace_fiscal_attr(context, "E001", "VCBS_CENTS", "2700")

    result = run_cbs_2026(_events(), context, SCENARIO_ID)
    assessment = result.assessment_results.iloc[0]

    assert int(assessment["S_APUR_CENTS"]) == -900
    assert int(assessment["T_RECOLHER_CENTS"]) == 0
    assert int(assessment["C_SALDO_CENTS"]) == 900


def test_run_cbs_2026_returns_result_dataclass_and_exact_schemas() -> None:
    result = run_cbs_2026(_events(), _tax_context(), SCENARIO_ID)

    assert isinstance(result, Cbs2026Result)
    assert tuple(result.operation_results.columns) == TAX_OPERATION_RESULT_COLUMNS
    assert tuple(result.assessment_results.columns) == TAX_ASSESSMENT_RESULT_COLUMNS
    assert len(result.operation_results) == 2
    assert len(result.assessment_results) == 1


def test_repeated_execution_with_same_inputs_produces_equivalent_frames() -> None:
    first = run_cbs_2026(_events(), _tax_context(), SCENARIO_ID)
    second = run_cbs_2026(_events(), _tax_context(), SCENARIO_ID)

    pd.testing.assert_frame_equal(first.operation_results, second.operation_results)
    pd.testing.assert_frame_equal(first.assessment_results, second.assessment_results)


def test_input_row_order_does_not_change_output() -> None:
    events = _events().sample(frac=1, random_state=1).reset_index(drop=True)
    context = _tax_context()
    context = _tax_context(
        entity_profile=context.entity_profile,
        fiscal_event_attributes=context.fiscal_event_attributes.sample(
            frac=1, random_state=2
        ).reset_index(drop=True),
        tax_scenarios=context.tax_scenarios,
        tax_parameters=context.tax_parameters.sample(frac=1, random_state=3).reset_index(
            drop=True
        ),
    )

    shuffled = run_cbs_2026(events, context, SCENARIO_ID)
    ordered = run_cbs_2026(_events(), _tax_context(), SCENARIO_ID)

    pd.testing.assert_frame_equal(
        shuffled.operation_results.reset_index(drop=True),
        ordered.operation_results.reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(
        shuffled.assessment_results.reset_index(drop=True),
        ordered.assessment_results.reset_index(drop=True),
    )


def test_tax_context_with_no_supported_taxable_events_is_valid_and_empty() -> None:
    events = _events().loc[_events()["TIPO_EVENTO"] == "aporte_capital"].copy()
    context = _tax_context(
        fiscal_event_attributes=pd.DataFrame(
            columns=FISCAL_EVENT_ATTRIBUTE_COLUMNS, dtype=object
        )
    )

    result = run_cbs_2026(events, context, SCENARIO_ID)

    assert result.operation_results.empty
    assert int(result.assessment_results.iloc[0]["S_APUR_CENTS"]) == 0


def test_compliance_absent_or_false_rejects_before_assessment() -> None:
    context = _drop_entity_attr(_tax_context(), "CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026")

    _assert_invalid(context, "cbs_entity_attribute_missing")


def _drop_entity_attr(context: TaxContext, attribute: str) -> TaxContext:
    frame = context.entity_profile.loc[context.entity_profile["ATRIBUTO"] != attribute].copy()
    return _tax_context(
        entity_profile=frame,
        fiscal_event_attributes=context.fiscal_event_attributes,
        tax_scenarios=context.tax_scenarios,
        tax_parameters=context.tax_parameters,
    )


def test_spec08_schema_contracts_are_unchanged() -> None:
    assert EVENT_COLUMNS == (
        "ID_EVENTO",
        "DT_EVENTO",
        "CLASSE_EVENTO",
        "TIPO_EVENTO",
        "DIRECAO",
        "NATUREZA",
        "VL_EVENTO_CENTS",
        "VL_CUSTO_CENTS",
        "MEIO_FINANCEIRO",
        "CATEGORIA_DESPESA",
        "COD_PART",
        "COND_PAGTO",
        "DOC_REF",
        "HIST",
        "ORIGEM",
        "SPEC_VERSION",
    )
    assert ENTITY_PROFILE_COLUMNS == (
        "ID_ENTIDADE",
        "ATRIBUTO",
        "VALOR",
        "TIPO_VALOR",
        "ORIGEM",
    )
    assert FISCAL_EVENT_ATTRIBUTE_COLUMNS == (
        "ID_EVENTO",
        "ATRIBUTO_FISCAL",
        "VALOR",
        "TIPO_VALOR",
        "ORIGEM",
    )
    assert TAX_SCENARIO_COLUMNS == (
        "ID_CENARIO",
        "ID_ENTIDADE",
        "DESCRICAO",
        "E_BASELINE",
        "DT_REFERENCIA_NORMATIVA",
        "REGIME_ENTIDADE",
        "REGIME_IR",
        "REGIME_CONSUMO",
        "REGIME_ESPECIAL",
        "ID_VERSAO_NORMATIVA",
        "ATIVO",
    )
    assert TAX_PARAMETER_COLUMNS == (
        "ID_PARAM",
        "ID_VERSAO_NORMATIVA",
        "ID_REGRA",
        "TRIBUTO",
        "CHAVE_PARAM",
        "VALOR",
        "TIPO_VALOR",
        "TIPO_FONTE",
        "FONTE_TITULO",
        "FONTE_URL",
        "DISPOSITIVO",
        "VERSAO_NORMA",
        "VIG_INI",
        "VIG_FIM",
        "DATA_CONSULTA",
        "VERSAO_REGRA",
    )
    assert TAX_OPERATION_RESULT_COLUMNS == (
        "ID_CENARIO",
        "ID_EVENTO",
        "TRIBUTO",
        "INCIDE",
        "BASE_CENTS",
        "ALIQUOTA",
        "CREDITO_CENTS",
        "DEBITO_CENTS",
        "VERSAO_REGRA",
    )
    assert TAX_ASSESSMENT_RESULT_COLUMNS == (
        "ID_CENARIO",
        "TRIBUTO",
        "S_APUR_CENTS",
        "T_RECOLHER_CENTS",
        "P_CASH_CENTS",
        "E_DRE_CENTS",
        "C_SALDO_CENTS",
        "VERSAO_REGRA",
    )


def test_required_parameter_key_set_matches_spec09() -> None:
    assert set(CBS_2026_REQUIRED_PARAMETER_KEYS) == {
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
    }


def test_accounting_core_modules_do_not_import_cbs_engine() -> None:
    root = Path(__file__).resolve().parents[1]
    frozen_files = [
        root / "src/accounting_sim/events.py",
        root / "src/accounting_sim/posting.py",
        root / "src/accounting_sim/ledger.py",
        root / "src/accounting_sim/statements.py",
        root / "src/accounting_sim/account_mapping.py",
        root / "src/accounting_sim/chart_of_accounts.py",
    ]

    for path in frozen_files:
        text = path.read_text(encoding="utf-8")
        assert "tax_cbs_2026" not in text
        assert "CBS" not in text


def test_csv_fixtures_load_and_run() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "data/examples/cbs_2026"
    events = pd.read_csv(fixture_dir / "events.csv", keep_default_na=False)
    events["DT_EVENTO"] = pd.to_datetime(events["DT_EVENTO"]).dt.date
    events["VL_EVENTO_CENTS"] = events["VL_EVENTO_CENTS"].astype(int)
    events["VL_CUSTO_CENTS"] = events["VL_CUSTO_CENTS"].replace("", pd.NA)
    events.loc[events["VL_CUSTO_CENTS"].notna(), "VL_CUSTO_CENTS"] = events.loc[
        events["VL_CUSTO_CENTS"].notna(), "VL_CUSTO_CENTS"
    ].astype(int)
    tax_scenarios = pd.read_csv(fixture_dir / "tax_scenarios.csv", keep_default_na=False)
    tax_scenarios["E_BASELINE"] = tax_scenarios["E_BASELINE"].map(
        lambda value: str(value).lower() == "true"
    )
    tax_scenarios["ATIVO"] = tax_scenarios["ATIVO"].map(
        lambda value: str(value).lower() == "true"
    )
    context = TaxContext(
        entity_profile=pd.read_csv(
            fixture_dir / "entity_profile.csv", keep_default_na=False
        ),
        fiscal_event_attributes=pd.read_csv(
            fixture_dir / "fiscal_event_attributes.csv", keep_default_na=False
        ),
        tax_scenarios=tax_scenarios,
        tax_parameters=pd.read_csv(
            fixture_dir / "tax_parameters.csv", keep_default_na=False
        ),
    )

    result = run_cbs_2026(events, context, SCENARIO_ID)

    assert int(result.operation_results["DEBITO_CENTS"].sum()) == 1800
    assert int(result.operation_results["CREDITO_CENTS"].sum()) == 900
