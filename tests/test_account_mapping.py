from datetime import date

import pandas as pd
from pandas.testing import assert_frame_equal

from accounting_sim.account_mapping import (
    DEFAULT_ACCOUNT_ROLE_MAP,
    REQUIRED_ACCOUNT_ROLES,
    build_default_account_role_mapping,
    validate_account_role_mapping,
)
from accounting_sim.canonical import (
    ACCOUNT_ROLE_MAPPING_COLUMNS,
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
from accounting_sim.posting import post_events


PERIOD = AccountingPeriod(date(2026, 1, 1), date(2026, 1, 31))
CONFIG = SimulationConfig(
    simulation_id="SIM_MAPPING",
    start_date=PERIOD.start_date,
    end_date=PERIOD.end_date,
    currency="BRL",
    seed=0,
    scenario_name="mapping",
    spec_version="spec_06_excel_workbook_v1",
)


def chart() -> pd.DataFrame:
    return build_default_commercial_chart(PERIOD.start_date)


def mapping() -> pd.DataFrame:
    return build_default_account_role_mapping()


def issue_codes(account_mapping: pd.DataFrame, chart_of_accounts: pd.DataFrame | None = None) -> set[str]:
    return {issue.code for issue in validate_account_role_mapping(account_mapping, chart() if chart_of_accounts is None else chart_of_accounts).issues}


def one_event(
    event_type: EventType,
    *,
    amount: int = 100000,
    cost: int | None = None,
    medium: str | None = "caixa",
) -> pd.DataFrame:
    class_value = EventClass.ADJUSTMENT.value if event_type is EventType.DEPRECIATION else EventClass.TRANSACTION.value
    direction = {
        EventType.CAPITAL_CONTRIBUTION: EventDirection.IN.value,
        EventType.PURCHASE_CASH: EventDirection.IN.value,
        EventType.SALE_CREDIT: EventDirection.OUT.value,
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
    if event_type is EventType.SALE_CREDIT and cost is None:
        cost = amount // 2

    return pd.DataFrame(
        [
            {
                "ID_EVENTO": "E001",
                "DT_EVENTO": PERIOD.start_date,
                "CLASSE_EVENTO": class_value,
                "TIPO_EVENTO": event_type.value,
                "DIRECAO": direction,
                "NATUREZA": nature,
                "VL_EVENTO_CENTS": amount,
                "VL_CUSTO_CENTS": cost,
                "MEIO_FINANCEIRO": medium,
                "CATEGORIA_DESPESA": None,
                "COD_PART": "PART001",
                "COND_PAGTO": payment_term,
                "DOC_REF": "DOC001",
                "HIST": f"Evento {event_type.value}",
                "ORIGEM": Origin.SYNTHETIC.value,
                "SPEC_VERSION": EVENT_SPEC_VERSION,
            }
        ],
        dtype=object,
    )


def recode_analytic_account(chart_of_accounts: pd.DataFrame, old_code: str, new_code: str) -> pd.DataFrame:
    recoded = chart_of_accounts.copy()
    recoded.loc[recoded["COD_CTA"] == old_code, "COD_CTA"] = new_code
    return recoded


def remap_role(account_mapping: pd.DataFrame, role: str, new_code: str) -> pd.DataFrame:
    remapped = account_mapping.copy()
    remapped.loc[remapped["PAPEL_CONTABIL"] == role, "COD_CTA"] = new_code
    return remapped


def test_account_role_mapping_columns_are_canonical():
    assert tuple(mapping().columns) == ACCOUNT_ROLE_MAPPING_COLUMNS


def test_default_mapping_contains_all_required_roles():
    assert set(REQUIRED_ACCOUNT_ROLES).issubset(set(mapping()["PAPEL_CONTABIL"]))


def test_account_role_must_be_unique():
    duplicated = pd.concat([mapping(), mapping().iloc[[0]]], ignore_index=True)
    assert "duplicate_account_role" in issue_codes(duplicated)


def test_missing_required_role_is_rejected():
    missing = mapping()[mapping()["PAPEL_CONTABIL"] != "caixa"]
    assert "missing_account_role" in issue_codes(missing)


def test_missing_mapped_account_is_rejected():
    bad = remap_role(mapping(), "caixa", "9.9.99")
    assert "mapped_account_missing" in issue_codes(bad)


def test_synthetic_mapped_account_is_rejected():
    bad = remap_role(mapping(), "caixa", "1.1.01")
    assert "mapped_account_not_analytic" in issue_codes(bad)


def test_inactive_mapped_account_is_rejected():
    chart_df = chart()
    chart_df.loc[chart_df["COD_CTA"] == DEFAULT_ACCOUNT_ROLE_MAP["caixa"], "ATIVA"] = False
    assert "mapped_account_inactive" in issue_codes(mapping(), chart_df)


def test_nature_mismatch_is_rejected():
    bad = remap_role(mapping(), "caixa", DEFAULT_ACCOUNT_ROLE_MAP["capital_social"])
    assert "account_role_nature_mismatch" in issue_codes(bad)


def test_normal_balance_mismatch_is_rejected():
    bad = remap_role(mapping(), "caixa", DEFAULT_ACCOUNT_ROLE_MAP["depreciacao_acumulada"])
    assert "account_role_balance_nature_mismatch" in issue_codes(bad)


def test_duplicate_cod_cta_between_compatible_roles_is_allowed():
    compatible = remap_role(mapping(), "despesa_utilidades", DEFAULT_ACCOUNT_ROLE_MAP["despesa_aluguel"])
    report = validate_account_role_mapping(compatible, chart())
    assert report.ok is True


def test_default_mapping_reproduces_default_posting_behavior():
    events = one_event(EventType.CAPITAL_CONTRIBUTION)
    default_result = post_events(events, chart(), CONFIG)
    explicit_result = post_events(events, chart(), CONFIG, account_role_mapping=mapping())
    assert_frame_equal(default_result.journal_entry_headers, explicit_result.journal_entry_headers)
    assert_frame_equal(default_result.postings, explicit_result.postings)
    assert_frame_equal(default_result.event_entry_links, explicit_result.event_entry_links)


def test_cash_recoding_changes_physical_account_without_changing_economic_rule():
    chart_df = recode_analytic_account(chart(), DEFAULT_ACCOUNT_ROLE_MAP["caixa"], "1.01.001.0001")
    account_mapping = remap_role(mapping(), "caixa", "1.01.001.0001")
    result = post_events(one_event(EventType.CAPITAL_CONTRIBUTION), chart_df, CONFIG, account_role_mapping=account_mapping)
    assert list(result.postings[["COD_CTA", "IND_DC"]].itertuples(index=False, name=None)) == [
        ("1.01.001.0001", DebitCredit.DEBIT.value),
        (DEFAULT_ACCOUNT_ROLE_MAP["capital_social"], DebitCredit.CREDIT.value),
    ]


def test_inventory_recoding_flows_through_purchase_and_sale():
    chart_df = recode_analytic_account(chart(), DEFAULT_ACCOUNT_ROLE_MAP["estoques"], "1.01.003.0001")
    account_mapping = remap_role(mapping(), "estoques", "1.01.003.0001")
    purchase = post_events(one_event(EventType.PURCHASE_CASH), chart_df, CONFIG, account_role_mapping=account_mapping)
    sale = post_events(one_event(EventType.SALE_CREDIT, amount=500000, cost=200000), chart_df, CONFIG, account_role_mapping=account_mapping)

    assert ("1.01.003.0001", DebitCredit.DEBIT.value) in list(purchase.postings[["COD_CTA", "IND_DC"]].itertuples(index=False, name=None))
    assert ("1.01.003.0001", DebitCredit.CREDIT.value) in list(sale.postings[["COD_CTA", "IND_DC"]].itertuples(index=False, name=None))


def test_posting_engine_consumes_supplied_mapping():
    chart_df = recode_analytic_account(chart(), DEFAULT_ACCOUNT_ROLE_MAP["caixa"], "1.01.001.0001")
    account_mapping = remap_role(mapping(), "caixa", "1.01.001.0001")
    result = post_events(one_event(EventType.CAPITAL_CONTRIBUTION), chart_df, CONFIG, account_role_mapping=account_mapping)
    assert result.postings.loc[result.postings["IND_DC"] == DebitCredit.DEBIT.value, "COD_CTA"].iloc[0] == "1.01.001.0001"
