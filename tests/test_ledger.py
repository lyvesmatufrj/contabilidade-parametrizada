from datetime import date

import pandas as pd
from pandas.testing import assert_frame_equal

from accounting_sim.canonical import (
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
from accounting_sim.chart_of_accounts import build_default_commercial_chart, get_analytic_accounts
from accounting_sim.events import EVENT_SPEC_VERSION
from accounting_sim.ledger import build_journal, build_ledger, build_trial_balance, validate_ledger_trial_balance
from accounting_sim.posting import post_events


PERIOD = AccountingPeriod(date(2026, 1, 1), date(2026, 1, 31))
CONFIG = SimulationConfig(
    simulation_id="SIM_LEDGER",
    start_date=PERIOD.start_date,
    end_date=PERIOD.end_date,
    currency="BRL",
    seed=0,
    scenario_name="ledger",
    spec_version="specs_03_05",
)


def chart() -> pd.DataFrame:
    return build_default_commercial_chart(PERIOD.start_date)


def event_row(
    event_id: str,
    event_date: date,
    event_type: EventType,
    amount: int,
    cost: int | None = None,
    medium: str | None = "caixa",
) -> dict[str, object]:
    event_class = EventClass.ADJUSTMENT.value if event_type is EventType.DEPRECIATION else EventClass.TRANSACTION.value
    direction = {
        EventType.CAPITAL_CONTRIBUTION: EventDirection.IN.value,
        EventType.PURCHASE_CASH: EventDirection.IN.value,
        EventType.SALE_CREDIT: EventDirection.OUT.value,
        EventType.CUSTOMER_RECEIPT: EventDirection.IN.value,
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
    return {
        "ID_EVENTO": event_id,
        "DT_EVENTO": event_date,
        "CLASSE_EVENTO": event_class,
        "TIPO_EVENTO": event_type.value,
        "DIRECAO": direction,
        "NATUREZA": nature,
        "VL_EVENTO_CENTS": amount,
        "VL_CUSTO_CENTS": cost,
        "MEIO_FINANCEIRO": medium,
        "CATEGORIA_DESPESA": None,
        "COD_PART": "PART001",
        "COND_PAGTO": payment_term,
        "DOC_REF": f"DOC-{event_id}",
        "HIST": event_type.value,
        "ORIGEM": Origin.SYNTHETIC.value,
        "SPEC_VERSION": EVENT_SPEC_VERSION,
    }


def canonical_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            event_row("E001", date(2026, 1, 1), EventType.CAPITAL_CONTRIBUTION, 10000000),
            event_row("E002", date(2026, 1, 2), EventType.PURCHASE_CASH, 3000000),
            event_row("E003", date(2026, 1, 3), EventType.SALE_CREDIT, 5000000, 2000000),
            event_row("E004", date(2026, 1, 4), EventType.CUSTOMER_RECEIPT, 3000000),
        ],
        dtype=object,
    )


def posted():
    return post_events(canonical_events(), chart(), CONFIG)


def built_views():
    result = posted()
    journal = build_journal(result.journal_entry_headers, result.postings, chart())
    ledger = build_ledger(result.journal_entry_headers, result.postings, chart())
    trial_balance = build_trial_balance(ledger, chart(), PERIOD)
    return result, journal, ledger, trial_balance


def test_journal_has_one_row_per_posting():
    result, journal, _, _ = built_views()
    assert len(journal) == len(result.postings)


def test_journal_is_sorted_by_date_entry_and_posting():
    _, journal, _, _ = built_views()
    sorted_journal = journal.sort_values(["DT_LCTO", "NUM_LCTO", "ID_PARTIDA"], kind="mergesort").reset_index(drop=True)
    assert_frame_equal(journal, sorted_journal)


def test_ledger_splits_debit_and_credit_correctly():
    _, _, ledger, _ = built_views()
    assert (ledger.loc[ledger["DEBITO_CENTS"] > 0, "CREDITO_CENTS"] == 0).all()
    assert (ledger.loc[ledger["CREDITO_CENTS"] > 0, "DEBITO_CENTS"] == 0).all()


def test_signed_movement_is_debit_minus_credit():
    _, _, ledger, _ = built_views()
    assert (ledger["MOVIMENTO_ASSINADO_CENTS"] == ledger["DEBITO_CENTS"] - ledger["CREDITO_CENTS"]).all()


def test_running_balance_is_correct_by_account():
    _, _, ledger, _ = built_views()
    for _, group in ledger.groupby("COD_CTA", sort=False):
        assert list(group["SALDO_ASSINADO_CENTS"]) == list(group["MOVIMENTO_ASSINADO_CENTS"].cumsum())


def test_ledger_final_balance_matches_trial_balance():
    _, _, ledger, trial_balance = built_views()
    last_balances = ledger.groupby("COD_CTA", as_index=True).tail(1).set_index("COD_CTA")
    for code, row in last_balances.iterrows():
        trial_row = trial_balance[trial_balance["COD_CTA"] == code].iloc[0]
        assert trial_row["VL_SLD_FIN_CENTS"] == row["SALDO_ABS_CENTS"]
        assert trial_row["IND_DC_FIN"] == row["IND_DC_SALDO"]


def test_credit_nature_account_encodes_credit_when_signed_balance_negative():
    _, _, ledger, _ = built_views()
    capital = ledger[ledger["COD_CTA"] == "3.1.01.01"].tail(1).iloc[0]
    assert capital["SALDO_ASSINADO_CENTS"] == -10000000
    assert capital["IND_DC_SALDO"] == DebitCredit.CREDIT.value


def test_zero_balance_is_encoded_as_zero_debit():
    _, _, _, trial_balance = built_views()
    zero_rows = trial_balance[trial_balance["VL_SLD_FIN_CENTS"] == 0]
    assert not zero_rows.empty
    assert set(zero_rows["IND_DC_FIN"]) == {DebitCredit.DEBIT.value}


def test_accounts_without_movement_appear_in_trial_balance():
    _, _, ledger, trial_balance = built_views()
    no_movement = set(get_analytic_accounts(chart())["COD_CTA"]) - set(ledger["COD_CTA"])
    assert no_movement
    assert no_movement.issubset(set(trial_balance["COD_CTA"]))
    assert (trial_balance[trial_balance["COD_CTA"].isin(no_movement)]["VL_DEB_CENTS"] == 0).all()


def test_synthetic_accounts_do_not_appear_in_trial_balance():
    _, _, _, trial_balance = built_views()
    synthetic_codes = set(chart().loc[chart()["IND_CTA"] == "S", "COD_CTA"])
    assert synthetic_codes.isdisjoint(set(trial_balance["COD_CTA"]))


def test_trial_balance_debits_equal_credits_and_match_postings():
    result, _, _, trial_balance = built_views()
    assert trial_balance["VL_DEB_CENTS"].sum() == trial_balance["VL_CRED_CENTS"].sum()
    assert trial_balance["VL_DEB_CENTS"].sum() == result.postings.loc[result.postings["IND_DC"] == "D", "VL_DC_CENTS"].sum()
    assert trial_balance["VL_CRED_CENTS"].sum() == result.postings.loc[result.postings["IND_DC"] == "C", "VL_DC_CENTS"].sum()


def test_outside_period_entries_are_rejected():
    result = posted()
    bad_headers = result.journal_entry_headers.copy()
    bad_headers.loc[bad_headers["NUM_LCTO"] == "L000001", "DT_LCTO"] = date(2026, 2, 1)
    ledger = build_ledger(bad_headers, result.postings, chart())
    trial_balance = build_trial_balance(ledger, chart(), PERIOD)
    report = validate_ledger_trial_balance(result.postings, ledger, trial_balance, chart(), PERIOD)
    assert "ledger_entry_outside_period" in {issue.code for issue in report.issues}


def test_canonical_case_produces_exact_nonzero_balances():
    _, _, _, trial_balance = built_views()
    nonzero = trial_balance[trial_balance["VL_SLD_FIN_CENTS"] > 0].set_index("COD_CTA")
    assert set(nonzero.index) == {"1.1.01.01", "1.1.02.01", "1.1.03.01", "3.1.01.01", "4.1.01.01", "4.2.01.01"}
    assert nonzero.loc["1.1.01.01", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]].tolist() == [10000000, "D"]
    assert nonzero.loc["1.1.02.01", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]].tolist() == [2000000, "D"]
    assert nonzero.loc["1.1.03.01", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]].tolist() == [1000000, "D"]
    assert nonzero.loc["3.1.01.01", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]].tolist() == [10000000, "C"]
    assert nonzero.loc["4.1.01.01", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]].tolist() == [5000000, "C"]
    assert nonzero.loc["4.2.01.01", ["VL_SLD_FIN_CENTS", "IND_DC_FIN"]].tolist() == [2000000, "D"]
    assert trial_balance.loc[trial_balance["IND_DC_FIN"] == "D", "VL_SLD_FIN_CENTS"].sum() == 15000000
    assert trial_balance.loc[trial_balance["IND_DC_FIN"] == "C", "VL_SLD_FIN_CENTS"].sum() == 15000000


def test_same_input_produces_identical_views():
    left = built_views()
    right = built_views()
    assert_frame_equal(left[1], right[1])
    assert_frame_equal(left[2], right[2])
    assert_frame_equal(left[3], right[3])


def test_functions_do_not_mutate_inputs_in_place():
    result = posted()
    headers = result.journal_entry_headers.copy(deep=True)
    postings = result.postings.copy(deep=True)
    chart_df = chart()
    chart_copy = chart_df.copy(deep=True)
    ledger = build_ledger(headers, postings, chart_df)
    _ = build_trial_balance(ledger, chart_df, PERIOD)
    assert_frame_equal(headers, result.journal_entry_headers)
    assert_frame_equal(postings, result.postings)
    assert_frame_equal(chart_df, chart_copy)


def test_ledger_trial_balance_validation_accepts_canonical_case():
    result, _, ledger, trial_balance = built_views()
    report = validate_ledger_trial_balance(result.postings, ledger, trial_balance, chart(), PERIOD)
    assert report.ok is True
    assert report.issues == ()
