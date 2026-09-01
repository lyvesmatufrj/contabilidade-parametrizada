from datetime import date

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from accounting_sim.canonical import (
    EVENT_ENTRY_LINK_COLUMNS,
    JOURNAL_ENTRY_HEADER_COLUMNS,
    POSTING_COLUMNS,
    AccountingInvariantError,
    AccountingPeriod,
    DebitCredit,
    EventClass,
    EventDirection,
    EventNature,
    EventType,
    JournalEntryType,
    Origin,
    PaymentTerm,
    ReferentialIntegrityError,
    SimulationConfig,
)
from accounting_sim.chart_of_accounts import build_default_commercial_chart
from accounting_sim.events import EVENT_SPEC_VERSION, build_demo_events
from accounting_sim.posting import ACCOUNT_CODE_MAP, post_events, validate_posting_result


PERIOD = AccountingPeriod(date(2026, 1, 1), date(2026, 1, 31))
CONFIG = SimulationConfig(
    simulation_id="SIM_TEST",
    start_date=PERIOD.start_date,
    end_date=PERIOD.end_date,
    currency="BRL",
    seed=0,
    scenario_name="tests",
    spec_version="specs_03_05",
)


def chart() -> pd.DataFrame:
    return build_default_commercial_chart(PERIOD.start_date)


def one_event(event_type: EventType, amount: int = 100000, cost: int | None = None, medium: str | None = "caixa", category: str | None = None) -> pd.DataFrame:
    event_type_value = event_type.value
    class_value = EventClass.ADJUSTMENT.value if event_type is EventType.DEPRECIATION else EventClass.TRANSACTION.value
    direction = {
        EventType.CAPITAL_CONTRIBUTION: EventDirection.IN.value,
        EventType.PURCHASE_CASH: EventDirection.IN.value,
        EventType.PURCHASE_CREDIT: EventDirection.IN.value,
        EventType.SUPPLIER_PAYMENT: EventDirection.OUT.value,
        EventType.SALE_CASH: EventDirection.OUT.value,
        EventType.SALE_CREDIT: EventDirection.OUT.value,
        EventType.CUSTOMER_RECEIPT: EventDirection.IN.value,
        EventType.OPERATING_EXPENSE_CASH: EventDirection.OUT.value,
        EventType.DEPRECIATION: EventDirection.NA.value,
    }[event_type]
    nature = {
        EventType.PURCHASE_CASH: EventNature.GOOD.value,
        EventType.PURCHASE_CREDIT: EventNature.GOOD.value,
        EventType.SALE_CASH: EventNature.GOOD.value,
        EventType.SALE_CREDIT: EventNature.GOOD.value,
        EventType.OPERATING_EXPENSE_CASH: EventNature.SERVICE.value,
        EventType.DEPRECIATION: EventNature.ADJUSTMENT.value,
    }.get(event_type, EventNature.FINANCIAL.value)
    payment_term = {
        EventType.PURCHASE_CASH: PaymentTerm.CASH.value,
        EventType.PURCHASE_CREDIT: PaymentTerm.CREDIT.value,
        EventType.SALE_CASH: PaymentTerm.CASH.value,
        EventType.SALE_CREDIT: PaymentTerm.CREDIT.value,
    }.get(event_type, PaymentTerm.NA.value)
    if event_type in {EventType.PURCHASE_CREDIT, EventType.SALE_CREDIT, EventType.DEPRECIATION}:
        medium = None
    if event_type is EventType.OPERATING_EXPENSE_CASH and category is None:
        category = "aluguel"
    if event_type in {EventType.SALE_CASH, EventType.SALE_CREDIT} and cost is None:
        cost = amount // 2

    return pd.DataFrame(
        [
            {
                "ID_EVENTO": "E001",
                "DT_EVENTO": PERIOD.start_date,
                "CLASSE_EVENTO": class_value,
                "TIPO_EVENTO": event_type_value,
                "DIRECAO": direction,
                "NATUREZA": nature,
                "VL_EVENTO_CENTS": amount,
                "VL_CUSTO_CENTS": cost,
                "MEIO_FINANCEIRO": medium,
                "CATEGORIA_DESPESA": category,
                "COD_PART": "PART001",
                "COND_PAGTO": payment_term,
                "DOC_REF": "DOC001",
                "HIST": f"Evento {event_type_value}",
                "ORIGEM": Origin.SYNTHETIC.value,
                "SPEC_VERSION": EVENT_SPEC_VERSION,
            }
        ],
        dtype=object,
    )


def canonical_volume_iii_events() -> pd.DataFrame:
    rows = [
        one_event(EventType.CAPITAL_CONTRIBUTION, 10000000).iloc[0].to_dict(),
        one_event(EventType.PURCHASE_CASH, 3000000).assign(ID_EVENTO="E002", DT_EVENTO=date(2026, 1, 2)).iloc[0].to_dict(),
        one_event(EventType.SALE_CREDIT, 5000000, 2000000).assign(ID_EVENTO="E003", DT_EVENTO=date(2026, 1, 3)).iloc[0].to_dict(),
        one_event(EventType.CUSTOMER_RECEIPT, 3000000).assign(ID_EVENTO="E004", DT_EVENTO=date(2026, 1, 4)).iloc[0].to_dict(),
    ]
    return pd.DataFrame(rows, dtype=object)


def postings_for_event(event_type: EventType) -> pd.DataFrame:
    result = post_events(one_event(event_type), chart(), CONFIG)
    return result.postings


@pytest.mark.parametrize(
    ("event_type", "expected"),
    [
        (EventType.CAPITAL_CONTRIBUTION, [("1.1.01.01", "D"), ("3.1.01.01", "C")]),
        (EventType.PURCHASE_CASH, [("1.1.03.01", "D"), ("1.1.01.01", "C")]),
        (EventType.PURCHASE_CREDIT, [("1.1.03.01", "D"), ("2.1.01.01", "C")]),
        (EventType.SUPPLIER_PAYMENT, [("2.1.01.01", "D"), ("1.1.01.01", "C")]),
        (EventType.CUSTOMER_RECEIPT, [("1.1.01.01", "D"), ("1.1.02.01", "C")]),
        (EventType.OPERATING_EXPENSE_CASH, [("4.3.01.02", "D"), ("1.1.01.01", "C")]),
        (EventType.DEPRECIATION, [("4.3.01.04", "D"), ("1.2.01.02", "C")]),
    ],
)
def test_each_single_entry_event_posts_expected_accounts(event_type, expected):
    postings = postings_for_event(event_type)
    assert list(postings[["COD_CTA", "IND_DC"]].itertuples(index=False, name=None)) == expected


@pytest.mark.parametrize("event_type", [EventType.SALE_CASH, EventType.SALE_CREDIT])
def test_sales_produce_two_entries_in_stable_order(event_type):
    result = post_events(one_event(event_type, amount=500000, cost=200000), chart(), CONFIG)
    assert list(result.journal_entry_headers["NUM_LCTO"]) == ["L000001", "L000002"]
    assert list(result.event_entry_links["ORDEM_LCTO_EVENTO"]) == [1, 2]
    assert list(result.postings.groupby("NUM_LCTO")["COD_CTA"].agg(tuple)) == [
        ("1.1.01.01" if event_type is EventType.SALE_CASH else "1.1.02.01", "4.1.01.01"),
        ("4.2.01.01", "1.1.03.01"),
    ]


def test_output_columns_are_canonical():
    result = post_events(build_demo_events(PERIOD), chart(), CONFIG)
    assert tuple(result.journal_entry_headers.columns) == JOURNAL_ENTRY_HEADER_COLUMNS
    assert tuple(result.postings.columns) == POSTING_COLUMNS
    assert tuple(result.event_entry_links.columns) == EVENT_ENTRY_LINK_COLUMNS


def test_journal_entry_amount_is_one_side():
    result = post_events(one_event(EventType.PURCHASE_CASH, 100000), chart(), CONFIG)
    assert result.journal_entry_headers["VL_LCTO_CENTS"].iloc[0] == 100000
    assert result.postings["VL_DC_CENTS"].sum() == 200000


def test_double_entry_per_journal_entry_and_global_totals():
    result = post_events(build_demo_events(PERIOD), chart(), CONFIG)
    for _, group in result.postings.groupby("NUM_LCTO"):
        assert group.loc[group["IND_DC"] == "D", "VL_DC_CENTS"].sum() == group.loc[group["IND_DC"] == "C", "VL_DC_CENTS"].sum()
    assert result.postings.loc[result.postings["IND_DC"] == "D", "VL_DC_CENTS"].sum() == result.postings.loc[result.postings["IND_DC"] == "C", "VL_DC_CENTS"].sum()


def test_only_active_analytic_accounts_are_used():
    result = post_events(build_demo_events(PERIOD), chart(), CONFIG)
    analytic_codes = set(chart().loc[chart()["IND_CTA"] == "A", "COD_CTA"])
    assert set(result.postings["COD_CTA"]).issubset(analytic_codes)


def test_missing_mapped_account_raises_clear_error():
    bad_chart = chart()[chart()["COD_CTA"] != ACCOUNT_CODE_MAP["caixa"]]
    with pytest.raises(ReferentialIntegrityError, match="caixa"):
        post_events(one_event(EventType.CAPITAL_CONTRIBUTION), bad_chart, CONFIG)


def test_synthetic_account_in_mapping_raises_clear_error(monkeypatch):
    monkeypatch.setitem(ACCOUNT_CODE_MAP, "caixa", "1.1.01")
    with pytest.raises(ReferentialIntegrityError, match="caixa"):
        post_events(one_event(EventType.CAPITAL_CONTRIBUTION), chart(), CONFIG)


def test_ids_are_unique_and_deterministic():
    result = post_events(build_demo_events(PERIOD), chart(), CONFIG)
    assert result.journal_entry_headers["NUM_LCTO"].is_unique
    assert result.postings["ID_PARTIDA"].is_unique
    assert list(result.journal_entry_headers["NUM_LCTO"]) == [f"L{i:06d}" for i in range(1, len(result.journal_entry_headers) + 1)]
    assert list(result.postings["ID_PARTIDA"]) == [f"P{i:06d}" for i in range(1, len(result.postings) + 1)]


def test_event_entry_links_are_integral():
    events = build_demo_events(PERIOD)
    result = post_events(events, chart(), CONFIG)
    report = validate_posting_result(result, events, chart())
    assert report.ok is True


def test_dates_and_entry_type_are_preserved():
    events = build_demo_events(PERIOD)
    result = post_events(events, chart(), CONFIG)
    event_dates = events.set_index("ID_EVENTO")["DT_EVENTO"].to_dict()
    links = result.event_entry_links.set_index("NUM_LCTO")["ID_EVENTO"].to_dict()
    for _, header in result.journal_entry_headers.iterrows():
        assert header["DT_LCTO"] == event_dates[links[header["NUM_LCTO"]]]
    assert set(result.journal_entry_headers["IND_LCTO"]) == {JournalEntryType.NORMAL.value}
    assert result.journal_entry_headers["DT_LCTO_EXT"].isna().all()


def test_volume_iii_canonical_case_posts_expected_totals():
    result = post_events(canonical_volume_iii_events(), chart(), CONFIG)
    debit_total = result.postings.loc[result.postings["IND_DC"] == DebitCredit.DEBIT.value, "VL_DC_CENTS"].sum()
    credit_total = result.postings.loc[result.postings["IND_DC"] == DebitCredit.CREDIT.value, "VL_DC_CENTS"].sum()
    assert len(result.journal_entry_headers) == 5
    assert len(result.postings) == 10
    assert debit_total == 23000000
    assert credit_total == 23000000


def test_same_input_produces_same_dataframes():
    events = build_demo_events(PERIOD)
    left = post_events(events, chart(), CONFIG)
    right = post_events(events, chart(), CONFIG)
    assert_frame_equal(left.journal_entry_headers, right.journal_entry_headers)
    assert_frame_equal(left.postings, right.postings)
    assert_frame_equal(left.event_entry_links, right.event_entry_links)
