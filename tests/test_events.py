from datetime import date

import pandas as pd
import pytest

from accounting_sim.canonical import (
    EVENT_COLUMNS,
    AccountingPeriod,
    EventClass,
    EventDirection,
    EventType,
    SchemaValidationError,
)
from accounting_sim.events import (
    build_demo_events,
    load_events,
    save_events,
    validate_events,
)


PERIOD = AccountingPeriod(date(2026, 1, 1), date(2026, 1, 31))


def issue_codes(df: pd.DataFrame) -> set[str]:
    return {issue.code for issue in validate_events(df, PERIOD).issues}


def test_demo_events_have_canonical_columns_in_order():
    df = build_demo_events(PERIOD)
    assert tuple(df.columns) == EVENT_COLUMNS


def test_event_ids_are_unique():
    df = build_demo_events(PERIOD)
    assert df["ID_EVENTO"].is_unique


def test_event_dates_are_converted_to_date():
    df = load_events("data/examples/events_mvp.csv")
    assert df["DT_EVENTO"].map(type).eq(date).all()


def test_money_values_are_int_cents_without_float():
    df = build_demo_events(PERIOD)
    assert df["VL_EVENTO_CENTS"].map(type).eq(int).all()
    with pytest.raises(SchemaValidationError):
        validate_events(df.assign(VL_EVENTO_CENTS=100.10), PERIOD)


def test_non_positive_event_amount_is_rejected():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E001", "VL_EVENTO_CENTS"] = 0
    assert "non_positive_event_amount" in issue_codes(df)


def test_event_outside_period_is_rejected():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E001", "DT_EVENTO"] = date(2026, 2, 1)
    assert "event_outside_period" in issue_codes(df)


def test_event_class_is_validated():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E001", "CLASSE_EVENTO"] = "BAD"
    assert "invalid_event_class" in issue_codes(df)


def test_event_direction_by_type_is_validated():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E001", "DIRECAO"] = EventDirection.OUT.value
    assert "invalid_direction_for_type" in issue_codes(df)


def test_payment_term_by_type_is_validated():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E002", "COND_PAGTO"] = "vista"
    assert "invalid_payment_term_for_type" in issue_codes(df)


def test_financial_medium_required_when_applicable():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E001", "MEIO_FINANCEIRO"] = None
    assert "missing_financial_medium" in issue_codes(df)


def test_expense_category_required_when_applicable():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E007", "CATEGORIA_DESPESA"] = None
    assert "missing_expense_category" in issue_codes(df)


def test_sale_cost_is_required():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E005", "VL_CUSTO_CENTS"] = None
    assert "missing_sale_cost" in issue_codes(df)


def test_demo_scenario_is_complete_and_valid():
    df = build_demo_events(PERIOD)
    report = validate_events(df, PERIOD)
    assert report.ok is True
    assert report.issues == ()
    assert {
        EventType.CAPITAL_CONTRIBUTION.value,
        EventType.PURCHASE_CREDIT.value,
        EventType.SUPPLIER_PAYMENT.value,
        EventType.SALE_CASH.value,
        EventType.SALE_CREDIT.value,
        EventType.CUSTOMER_RECEIPT.value,
        EventType.OPERATING_EXPENSE_CASH.value,
        EventType.DEPRECIATION.value,
    }.issubset(set(df["TIPO_EVENTO"]))
    assert df.loc[df["TIPO_EVENTO"] == EventType.DEPRECIATION.value, "CLASSE_EVENTO"].iloc[0] == EventClass.ADJUSTMENT.value


def test_save_and_reload_csv_preserves_ids_dates_and_values(tmp_path):
    df = build_demo_events(PERIOD)
    path = tmp_path / "events.csv"
    save_events(df, path)
    reloaded = load_events(path)
    assert list(reloaded["ID_EVENTO"]) == list(df["ID_EVENTO"])
    assert list(reloaded["DT_EVENTO"]) == list(df["DT_EVENTO"])
    assert list(reloaded["VL_EVENTO_CENTS"]) == list(df["VL_EVENTO_CENTS"])
    assert list(reloaded["VL_CUSTO_CENTS"]) == list(df["VL_CUSTO_CENTS"])


def test_events_are_sorted_deterministically_by_date_and_id():
    df = build_demo_events(PERIOD).iloc[::-1].reset_index(drop=True)
    path_sorted = build_demo_events(PERIOD)
    saved = validate_events(df, PERIOD)
    assert saved.ok is True
    assert list(load_events("data/examples/events_mvp.csv")["ID_EVENTO"]) == list(path_sorted["ID_EVENTO"])


def test_unknown_event_type_is_rejected():
    df = build_demo_events(PERIOD)
    df.loc[df["ID_EVENTO"] == "E001", "TIPO_EVENTO"] = "tipo_desconhecido"
    assert "invalid_event_type" in issue_codes(df)
