from __future__ import annotations

from datetime import date
from decimal import Decimal
import importlib.util

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries
from pandas.testing import assert_frame_equal

from accounting_sim.account_mapping import DEFAULT_ACCOUNT_ROLE_MAP, build_default_account_role_mapping
from accounting_sim.canonical import (
    ACCOUNT_ROLE_MAPPING_COLUMNS,
    CHART_OF_ACCOUNTS_COLUMNS,
    EVENT_COLUMNS,
    STATEMENT_MAPPING_COLUMNS,
    AccountingPeriod,
    DebitCredit,
    EventClass,
    EventDirection,
    EventNature,
    EventType,
    Origin,
    PaymentTerm,
    SimulationConfig,
    SchemaValidationError,
)
from accounting_sim.chart_of_accounts import build_default_commercial_chart, validate_chart_of_accounts
from accounting_sim.events import EVENT_SPEC_VERSION
from accounting_sim.posting import post_events
from accounting_sim.statements import (
    FINANCIAL_STATEMENT_SPEC_VERSION,
    build_default_statement_mapping,
    validate_statement_mapping,
)
from accounting_sim.workbook import (
    EVENT_WORKBOOK_COLUMNS,
    TABLE_NAMES,
    WORKBOOK_SHEETS,
    WORKBOOK_SPEC_VERSION,
    WorkbookInputs,
    build_workbook,
    load_workbook_inputs,
    regenerate_workbook,
)


PERIOD = AccountingPeriod(date(2026, 1, 1), date(2026, 1, 31))
CONFIG = SimulationConfig(
    simulation_id="SIM_WORKBOOK",
    start_date=PERIOD.start_date,
    end_date=PERIOD.end_date,
    currency="BRL",
    seed=0,
    scenario_name="workbook",
    spec_version=WORKBOOK_SPEC_VERSION,
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
        "CLASSE_EVENTO": EventClass.TRANSACTION.value,
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
        columns=EVENT_COLUMNS,
        dtype=object,
    )


def workbook_inputs(
    chart_of_accounts: pd.DataFrame | None = None,
    account_role_mapping: pd.DataFrame | None = None,
    events: pd.DataFrame | None = None,
    statement_mapping: pd.DataFrame | None = None,
) -> WorkbookInputs:
    chart_df = chart() if chart_of_accounts is None else chart_of_accounts
    return WorkbookInputs(
        simulation_config=CONFIG,
        chart_of_accounts=chart_df,
        account_role_mapping=build_default_account_role_mapping() if account_role_mapping is None else account_role_mapping,
        events=canonical_events() if events is None else events,
        statement_mapping=build_default_statement_mapping(chart_df) if statement_mapping is None else statement_mapping,
    )


def build_case(tmp_path, inputs: WorkbookInputs | None = None):
    path = tmp_path / "case.xlsx"
    build_workbook(inputs or workbook_inputs(), path)
    return path, load_workbook(path, data_only=True)


def sheet_frame(path, sheet_name: str) -> pd.DataFrame:
    wb = load_workbook(path, data_only=True)
    ws = wb[sheet_name]
    table = ws.tables[TABLE_NAMES[sheet_name]]
    min_col, min_row, max_col, max_row = range_boundaries(table.ref)
    rows = list(ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col, values_only=True))
    return pd.DataFrame(rows[1:], columns=rows[0], dtype=object)


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.00"))


def row_by_code(frame: pd.DataFrame, code: str) -> pd.Series:
    return frame[frame["COD_CTA"] == code].iloc[0]


def row_by_line(frame: pd.DataFrame, code: str) -> pd.Series:
    return frame[frame["COD_LINHA"] == code].iloc[0]


def test_openpyxl_is_available_as_dependency():
    assert importlib.util.find_spec("openpyxl") is not None


def test_build_workbook_creates_xlsx_and_can_be_reopened(tmp_path):
    path, wb = build_case(tmp_path)
    assert path.exists()
    assert path.suffix == ".xlsx"
    assert "README" in wb.sheetnames


def test_workbook_sheets_are_exactly_in_canonical_order(tmp_path):
    _, wb = build_case(tmp_path)
    assert tuple(wb.sheetnames) == WORKBOOK_SHEETS


def test_future_sheets_are_not_anticipated(tmp_path):
    _, wb = build_case(tmp_path)
    forbidden = {"ENTIDADE", "CENTROS_CUSTO", "PARTICIPANTES", "HISTORICOS", "DFC", "DVA", "CENARIOS"}
    assert forbidden.isdisjoint(set(wb.sheetnames))
    assert not any(name.startswith("FISCAL_") for name in wb.sheetnames)


def test_named_tables_exist_and_cover_expected_row_counts(tmp_path):
    path, wb = build_case(tmp_path)
    expected_rows = {
        "CONFIG": 7,
        "PLANO_CONTAS": len(chart()),
        "MAPEAMENTO_CONTAS": len(build_default_account_role_mapping()),
        "EVENTOS": len(canonical_events()),
        "LANCAMENTOS": 5,
        "PARTIDAS": 10,
        "VINCULO_EVENTO_LCTO": 5,
        "DIARIO": 10,
        "RAZAO": 10,
        "BALANCETE": len(chart()[chart()["IND_CTA"] == "A"]),
        "MAPEAMENTO_DF": len(build_default_statement_mapping(chart())),
        "BP": 22,
        "DRE": 11,
        "VALIDACOES": 7,
        "PROVENIENCIA": 10,
    }
    for sheet_name, table_name in TABLE_NAMES.items():
        assert table_name in wb[sheet_name].tables
        frame = sheet_frame(path, sheet_name)
        assert len(frame) == expected_rows[sheet_name]


def test_tabular_sheets_have_freeze_panes_and_filters(tmp_path):
    _, wb = build_case(tmp_path)
    for sheet_name, table_name in TABLE_NAMES.items():
        ws = wb[sheet_name]
        assert ws.freeze_panes == "A2"
        assert ws.tables[table_name].autoFilter is not None


def test_config_round_trip_preserves_types(tmp_path):
    path, _ = build_case(tmp_path)
    reloaded = load_workbook_inputs(path)
    assert reloaded.simulation_config == CONFIG
    assert isinstance(reloaded.simulation_config.start_date, date)
    assert isinstance(reloaded.simulation_config.seed, int)


def test_chart_round_trip_preserves_keys_dates_bools_and_hierarchy(tmp_path):
    path, _ = build_case(tmp_path)
    reloaded = load_workbook_inputs(path)
    assert tuple(reloaded.chart_of_accounts.columns) == CHART_OF_ACCOUNTS_COLUMNS
    assert list(reloaded.chart_of_accounts["COD_CTA"]) == list(chart()["COD_CTA"])
    assert reloaded.chart_of_accounts["DT_ALT"].map(type).eq(date).all()
    assert reloaded.chart_of_accounts["ATIVA"].map(type).eq(bool).all()
    assert validate_chart_of_accounts(reloaded.chart_of_accounts).ok is True


def test_mapping_round_trip_preserves_roles_and_codes(tmp_path):
    path, _ = build_case(tmp_path)
    reloaded = load_workbook_inputs(path)
    assert tuple(reloaded.account_role_mapping.columns) == ACCOUNT_ROLE_MAPPING_COLUMNS
    assert_frame_equal(reloaded.account_role_mapping, build_default_account_role_mapping(), check_dtype=False)


def test_statement_mapping_round_trip_preserves_accounts_and_lines(tmp_path):
    path, _ = build_case(tmp_path)
    reloaded = load_workbook_inputs(path)
    expected = build_default_statement_mapping(chart())
    assert tuple(reloaded.statement_mapping.columns) == STATEMENT_MAPPING_COLUMNS
    assert_frame_equal(reloaded.statement_mapping, expected, check_dtype=False)
    assert validate_statement_mapping(reloaded.statement_mapping, reloaded.chart_of_accounts).ok is True


def test_events_round_trip_preserves_ids_dates_and_cents(tmp_path):
    path, _ = build_case(tmp_path)
    reloaded = load_workbook_inputs(path)
    assert tuple(reloaded.events.columns) == EVENT_COLUMNS
    assert list(reloaded.events["ID_EVENTO"]) == list(canonical_events()["ID_EVENTO"])
    assert list(reloaded.events["DT_EVENTO"]) == list(canonical_events()["DT_EVENTO"])
    assert list(reloaded.events["VL_EVENTO_CENTS"]) == list(canonical_events()["VL_EVENTO_CENTS"])
    assert list(reloaded.events["VL_CUSTO_CENTS"]) == list(canonical_events()["VL_CUSTO_CENTS"])


def test_events_sheet_uses_reais_columns_not_cents(tmp_path):
    path, _ = build_case(tmp_path)
    events = sheet_frame(path, "EVENTOS")
    assert tuple(events.columns) == EVENT_WORKBOOK_COLUMNS
    assert "VL_EVENTO_CENTS" not in events.columns
    assert decimal_value(events.loc[events["ID_EVENTO"] == "E001", "VL_EVENTO"].iloc[0]) == Decimal("100000.00")


def test_money_reader_rejects_more_than_two_decimal_places(tmp_path):
    path, _ = build_case(tmp_path)
    wb = load_workbook(path)
    ws = wb["EVENTOS"]
    headers = [cell.value for cell in ws[1]]
    ws.cell(row=2, column=headers.index("VL_EVENTO") + 1, value="100000.001")
    wb.save(path)
    try:
        load_workbook_inputs(path)
    except SchemaValidationError as exc:
        assert "duas casas" in str(exc)
    else:
        raise AssertionError("Valor monetário com mais de duas casas deveria ser rejeitado.")


def test_canonical_workbook_materializes_five_entries_and_ten_postings(tmp_path):
    path, _ = build_case(tmp_path)
    assert len(sheet_frame(path, "LANCAMENTOS")) == 5
    assert len(sheet_frame(path, "PARTIDAS")) == 10


def test_canonical_workbook_debit_and_credit_totals_are_brl(tmp_path):
    path, _ = build_case(tmp_path)
    postings = sheet_frame(path, "PARTIDAS")
    debit_total = sum(decimal_value(value) for value in postings.loc[postings["IND_DC"] == "D", "VL_DC"])
    credit_total = sum(decimal_value(value) for value in postings.loc[postings["IND_DC"] == "C", "VL_DC"])
    assert debit_total == Decimal("230000.00")
    assert credit_total == Decimal("230000.00")


def test_ledger_sheet_presents_expected_canonical_balances(tmp_path):
    path, _ = build_case(tmp_path)
    ledger = sheet_frame(path, "RAZAO")
    last_by_account = ledger.groupby("COD_CTA", sort=False).tail(1).set_index("COD_CTA")
    assert decimal_value(last_by_account.loc["1.1.01.01", "SALDO_ABS"]) == Decimal("100000.00")
    assert decimal_value(last_by_account.loc["1.1.02.01", "SALDO_ABS"]) == Decimal("20000.00")
    assert decimal_value(last_by_account.loc["1.1.03.01", "SALDO_ABS"]) == Decimal("10000.00")
    assert decimal_value(last_by_account.loc["3.1.01.01", "SALDO_ABS"]) == Decimal("100000.00")
    assert decimal_value(last_by_account.loc["4.1.01.01", "SALDO_ABS"]) == Decimal("50000.00")
    assert decimal_value(last_by_account.loc["4.2.01.01", "SALDO_ABS"]) == Decimal("20000.00")
    assert last_by_account.loc["3.1.01.01", "IND_DC_SALDO"] == DebitCredit.CREDIT.value


def test_trial_balance_presents_expected_debit_and_credit_balances_in_brl(tmp_path):
    path, _ = build_case(tmp_path)
    trial_balance = sheet_frame(path, "BALANCETE")
    debit_total = sum(decimal_value(value) for value in trial_balance.loc[trial_balance["IND_DC_FIN"] == "D", "VL_SLD_FIN"])
    credit_total = sum(decimal_value(value) for value in trial_balance.loc[trial_balance["IND_DC_FIN"] == "C", "VL_SLD_FIN"])
    assert debit_total == Decimal("150000.00")
    assert credit_total == Decimal("150000.00")


def test_income_statement_sheet_presents_canonical_result_in_brl(tmp_path):
    path, _ = build_case(tmp_path)
    dre = sheet_frame(path, "DRE")
    assert decimal_value(row_by_line(dre, "DRE_RECEITA_VENDAS")["VL"]) == Decimal("50000.00")
    assert decimal_value(row_by_line(dre, "DRE_CMV")["VL"]) == Decimal("-20000.00")
    assert decimal_value(row_by_line(dre, "DRE_RESULTADO_BRUTO")["VL"]) == Decimal("30000.00")
    assert decimal_value(row_by_line(dre, "DRE_RESULTADO_PERIODO")["VL"]) == Decimal("30000.00")


def test_balance_sheet_sheet_presents_canonical_totals_in_brl(tmp_path):
    path, _ = build_case(tmp_path)
    bp = sheet_frame(path, "BP")
    assert decimal_value(row_by_line(bp, "BP_ATIVO")["VL"]) == Decimal("130000.00")
    assert decimal_value(row_by_line(bp, "BP_CAPITAL")["VL"]) == Decimal("100000.00")
    assert decimal_value(row_by_line(bp, "BP_RESULTADO_PERIODO")["VL"]) == Decimal("30000.00")
    assert decimal_value(row_by_line(bp, "BP_PATRIMONIO_LIQUIDO")["VL"]) == Decimal("130000.00")
    assert decimal_value(row_by_line(bp, "BP_TOTAL_PASSIVO_PL")["VL"]) == Decimal("130000.00")


def test_workbook_preserves_previous_core_invariants_after_adding_statements(tmp_path):
    path, _ = build_case(tmp_path)
    postings = sheet_frame(path, "PARTIDAS")
    trial_balance = sheet_frame(path, "BALANCETE")
    assert len(sheet_frame(path, "LANCAMENTOS")) == 5
    assert len(postings) == 10
    assert sum(decimal_value(value) for value in postings.loc[postings["IND_DC"] == "D", "VL_DC"]) == Decimal("230000.00")
    assert sum(decimal_value(value) for value in postings.loc[postings["IND_DC"] == "C", "VL_DC"]) == Decimal("230000.00")
    assert sum(decimal_value(value) for value in trial_balance.loc[trial_balance["IND_DC_FIN"] == "D", "VL_SLD_FIN"]) == Decimal("150000.00")
    assert sum(decimal_value(value) for value in trial_balance.loc[trial_balance["IND_DC_FIN"] == "C", "VL_SLD_FIN"]) == Decimal("150000.00")


def test_validations_sheet_has_no_failures_for_canonical_case(tmp_path):
    path, _ = build_case(tmp_path)
    validations = sheet_frame(path, "VALIDACOES")
    assert set(validations["OK"]) == {True}
    assert set(validations["MENSAGEM"]) == {"ok"}


def test_provenance_contains_spec_and_rule_versions(tmp_path):
    path, _ = build_case(tmp_path)
    provenance = sheet_frame(path, "PROVENIENCIA").set_index("CHAVE")["VALOR"].to_dict()
    assert provenance["workbook_spec_version"] == WORKBOOK_SPEC_VERSION
    assert provenance["financial_statement_spec_version"] == FINANCIAL_STATEMENT_SPEC_VERSION
    assert provenance["posting_rule_version"] == "posting_rules_v1"
    assert provenance["statement_mapping_source"] == "MAPEAMENTO_DF"
    assert provenance["simulation_id"] == CONFIG.simulation_id


def test_manual_trial_balance_edit_is_ignored_by_regeneration(tmp_path):
    path, _ = build_case(tmp_path)
    wb = load_workbook(path)
    ws = wb["BALANCETE"]
    headers = [cell.value for cell in ws[1]]
    value_col = headers.index("VL_SLD_FIN") + 1
    code_col = headers.index("COD_CTA") + 1
    for row in range(2, ws.max_row + 1):
        if ws.cell(row=row, column=code_col).value == "1.1.01.01":
            ws.cell(row=row, column=value_col, value=999999.99)
            break
    wb.save(path)

    regenerated = tmp_path / "regenerated_trial.xlsx"
    regenerate_workbook(path, regenerated)
    trial_balance = sheet_frame(regenerated, "BALANCETE")
    assert decimal_value(row_by_code(trial_balance, "1.1.01.01")["VL_SLD_FIN"]) == Decimal("100000.00")


def test_manual_ledger_edit_is_ignored_by_regeneration(tmp_path):
    path, _ = build_case(tmp_path)
    wb = load_workbook(path)
    ws = wb["RAZAO"]
    headers = [cell.value for cell in ws[1]]
    value_col = headers.index("SALDO_ABS") + 1
    code_col = headers.index("COD_CTA") + 1
    for row in range(2, ws.max_row + 1):
        if ws.cell(row=row, column=code_col).value == "1.1.01.01":
            ws.cell(row=row, column=value_col, value=999999.99)
    wb.save(path)

    regenerated = tmp_path / "regenerated_ledger.xlsx"
    regenerate_workbook(path, regenerated)
    ledger = sheet_frame(regenerated, "RAZAO")
    caixa_final = ledger[ledger["COD_CTA"] == "1.1.01.01"].tail(1).iloc[0]
    assert decimal_value(caixa_final["SALDO_ABS"]) == Decimal("100000.00")


def test_manual_balance_sheet_edit_is_ignored_by_regeneration(tmp_path):
    path, _ = build_case(tmp_path)
    wb = load_workbook(path)
    ws = wb["BP"]
    headers = [cell.value for cell in ws[1]]
    value_col = headers.index("VL") + 1
    line_col = headers.index("COD_LINHA") + 1
    for row in range(2, ws.max_row + 1):
        if ws.cell(row=row, column=line_col).value == "BP_ATIVO":
            ws.cell(row=row, column=value_col, value=999999.99)
            break
    wb.save(path)

    regenerated = tmp_path / "regenerated_bp.xlsx"
    regenerate_workbook(path, regenerated)
    bp = sheet_frame(regenerated, "BP")
    assert decimal_value(row_by_line(bp, "BP_ATIVO")["VL"]) == Decimal("130000.00")


def test_manual_income_statement_edit_is_ignored_by_regeneration(tmp_path):
    path, _ = build_case(tmp_path)
    wb = load_workbook(path)
    ws = wb["DRE"]
    headers = [cell.value for cell in ws[1]]
    value_col = headers.index("VL") + 1
    line_col = headers.index("COD_LINHA") + 1
    for row in range(2, ws.max_row + 1):
        if ws.cell(row=row, column=line_col).value == "DRE_RESULTADO_PERIODO":
            ws.cell(row=row, column=value_col, value=999999.99)
            break
    wb.save(path)

    regenerated = tmp_path / "regenerated_dre.xlsx"
    regenerate_workbook(path, regenerated)
    dre = sheet_frame(regenerated, "DRE")
    assert decimal_value(row_by_line(dre, "DRE_RESULTADO_PERIODO")["VL"]) == Decimal("30000.00")


def test_cash_recoding_in_workbook_inputs_flows_to_postings(tmp_path):
    chart_df = chart().copy()
    chart_df.loc[chart_df["COD_CTA"] == DEFAULT_ACCOUNT_ROLE_MAP["caixa"], "COD_CTA"] = "1.01.001.0001"
    account_mapping = build_default_account_role_mapping()
    account_mapping.loc[account_mapping["PAPEL_CONTABIL"] == "caixa", "COD_CTA"] = "1.01.001.0001"
    path, _ = build_case(tmp_path, workbook_inputs(chart_of_accounts=chart_df, account_role_mapping=account_mapping))
    postings = sheet_frame(path, "PARTIDAS")
    assert "1.01.001.0001" in set(postings["COD_CTA"])


def test_changing_statement_mapping_changes_presentation_not_postings(tmp_path):
    statement_mapping = build_default_statement_mapping(chart())
    statement_mapping.loc[statement_mapping["COD_CTA"] == "1.1.01.01", "COD_LINHA"] = "BP_BANCOS"
    path, _ = build_case(tmp_path, workbook_inputs(statement_mapping=statement_mapping))
    bp = sheet_frame(path, "BP")
    postings = sheet_frame(path, "PARTIDAS")
    assert decimal_value(row_by_line(bp, "BP_CAIXA")["VL"]) == Decimal("0.00")
    assert decimal_value(row_by_line(bp, "BP_BANCOS")["VL"]) == Decimal("100000.00")
    assert "1.1.01.01" in set(postings["COD_CTA"])


def test_changing_only_cod_df_is_ignored_and_overwritten_by_statement_mapping(tmp_path):
    chart_df = chart()
    chart_df.loc[chart_df["COD_CTA"] == "1.1.01.01", "COD_DF"] = "BP_BANCOS"
    statement_mapping = build_default_statement_mapping(chart())
    path, _ = build_case(tmp_path, workbook_inputs(chart_of_accounts=chart_df, statement_mapping=statement_mapping))
    bp = sheet_frame(path, "BP")
    chart_sheet = sheet_frame(path, "PLANO_CONTAS")
    assert decimal_value(row_by_line(bp, "BP_CAIXA")["VL"]) == Decimal("100000.00")
    assert decimal_value(row_by_line(bp, "BP_BANCOS")["VL"]) == Decimal("0.00")
    assert row_by_code(chart_sheet, "1.1.01.01")["COD_DF"] == "BP_CAIXA"


def test_same_input_generates_same_values_after_two_materializations(tmp_path):
    first = tmp_path / "first.xlsx"
    second = tmp_path / "second.xlsx"
    inputs = workbook_inputs()
    build_workbook(inputs, first)
    build_workbook(inputs, second)
    for sheet_name in WORKBOOK_SHEETS:
        if sheet_name == "README":
            continue
        assert_frame_equal(sheet_frame(first, sheet_name), sheet_frame(second, sheet_name), check_dtype=False)


def test_build_workbook_does_not_mutate_input_dataframes(tmp_path):
    inputs = workbook_inputs()
    chart_copy = inputs.chart_of_accounts.copy(deep=True)
    mapping_copy = inputs.account_role_mapping.copy(deep=True)
    events_copy = inputs.events.copy(deep=True)
    build_workbook(inputs, tmp_path / "case.xlsx")
    assert_frame_equal(inputs.chart_of_accounts, chart_copy)
    assert_frame_equal(inputs.account_role_mapping, mapping_copy)
    assert_frame_equal(inputs.events, events_copy)


def test_workbook_does_not_need_formulas_to_close(tmp_path):
    path, _ = build_case(tmp_path)
    wb = load_workbook(path, data_only=False)
    formulas = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    formulas.append((ws.title, cell.coordinate, cell.value))
    assert formulas == []


def test_workbook_pipeline_matches_python_core_counts(tmp_path):
    inputs = workbook_inputs()
    path, _ = build_case(tmp_path, inputs)
    core = post_events(inputs.events, inputs.chart_of_accounts, inputs.simulation_config, account_role_mapping=inputs.account_role_mapping)
    assert len(sheet_frame(path, "LANCAMENTOS")) == len(core.journal_entry_headers)
    assert len(sheet_frame(path, "PARTIDAS")) == len(core.postings)
