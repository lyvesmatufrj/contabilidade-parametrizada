"""Materialização Excel do núcleo contábil validado pela spec 06."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

from accounting_sim.account_mapping import validate_account_role_mapping
from accounting_sim.canonical import (
    ACCOUNT_ROLE_MAPPING_COLUMNS,
    CHART_OF_ACCOUNTS_COLUMNS,
    EVENT_COLUMNS,
    EVENT_ENTRY_LINK_COLUMNS,
    JOURNAL_ENTRY_HEADER_COLUMNS,
    JOURNAL_VIEW_COLUMNS,
    LEDGER_VIEW_COLUMNS,
    POSTING_COLUMNS,
    TRIAL_BALANCE_COLUMNS,
    AccountingInvariantError,
    AccountingPeriod,
    DebitCredit,
    EventClass,
    EventDirection,
    EventNature,
    EventType,
    Origin,
    PaymentTerm,
    SchemaValidationError,
    SimulationConfig,
    ValidationIssue,
    ValidationReport,
    parse_iso_date,
)
from accounting_sim.chart_of_accounts import validate_chart_of_accounts
from accounting_sim.events import normalize_events, sort_events, validate_events
from accounting_sim.ledger import (
    build_journal,
    build_ledger,
    build_trial_balance,
    validate_ledger_trial_balance,
)
from accounting_sim.posting import post_events, validate_posting_result


WORKBOOK_SPEC_VERSION = "spec_06_excel_workbook_v1"

WORKBOOK_SHEETS: tuple[str, ...] = (
    "README",
    "CONFIG",
    "PLANO_CONTAS",
    "MAPEAMENTO_CONTAS",
    "EVENTOS",
    "LANCAMENTOS",
    "PARTIDAS",
    "VINCULO_EVENTO_LCTO",
    "DIARIO",
    "RAZAO",
    "BALANCETE",
    "VALIDACOES",
    "PROVENIENCIA",
)

EDITABLE_SHEETS = frozenset({"CONFIG", "PLANO_CONTAS", "MAPEAMENTO_CONTAS", "EVENTOS"})

CONFIG_COLUMNS: tuple[str, ...] = ("CHAVE", "VALOR")
VALIDATION_COLUMNS: tuple[str, ...] = (
    "ETAPA",
    "OK",
    "ISSUE_CODE",
    "MENSAGEM",
    "ACCOUNT_CODE",
    "EVENT_ID",
    "ENTRY_ID",
    "POSTING_ID",
)
PROVENANCE_COLUMNS: tuple[str, ...] = ("CHAVE", "VALOR")

EVENT_WORKBOOK_COLUMNS: tuple[str, ...] = (
    "ID_EVENTO",
    "DT_EVENTO",
    "CLASSE_EVENTO",
    "TIPO_EVENTO",
    "DIRECAO",
    "NATUREZA",
    "VL_EVENTO",
    "VL_CUSTO",
    "MEIO_FINANCEIRO",
    "CATEGORIA_DESPESA",
    "COD_PART",
    "COND_PAGTO",
    "DOC_REF",
    "HIST",
    "ORIGEM",
    "SPEC_VERSION",
)
JOURNAL_ENTRY_WORKBOOK_COLUMNS: tuple[str, ...] = (
    "NUM_LCTO",
    "DT_LCTO",
    "VL_LCTO",
    "IND_LCTO",
    "DT_LCTO_EXT",
    "ID_GERACAO",
    "VERSAO_REGRA",
)
POSTING_WORKBOOK_COLUMNS: tuple[str, ...] = (
    "ID_PARTIDA",
    "NUM_LCTO",
    "COD_CTA",
    "COD_CCUS",
    "VL_DC",
    "IND_DC",
    "NUM_ARQ",
    "COD_HIST_PAD",
    "HIST",
    "COD_PART",
    "ID_ORIGEM",
)
JOURNAL_VIEW_WORKBOOK_COLUMNS: tuple[str, ...] = (
    "DT_LCTO",
    "NUM_LCTO",
    "ID_PARTIDA",
    "COD_CTA",
    "CTA",
    "IND_DC",
    "VL_DC",
    "HIST",
    "COD_PART",
    "ID_ORIGEM",
)
LEDGER_VIEW_WORKBOOK_COLUMNS: tuple[str, ...] = (
    "COD_CTA",
    "CTA",
    "DT_LCTO",
    "NUM_LCTO",
    "ID_PARTIDA",
    "DEBITO",
    "CREDITO",
    "MOVIMENTO_ASSINADO",
    "SALDO_ASSINADO",
    "SALDO_ABS",
    "IND_DC_SALDO",
    "HIST",
    "ID_ORIGEM",
)
TRIAL_BALANCE_WORKBOOK_COLUMNS: tuple[str, ...] = (
    "DT_INI",
    "DT_FIN",
    "COD_CTA",
    "COD_CCUS",
    "VL_SLD_INI",
    "IND_DC_INI",
    "VL_DEB",
    "VL_CRED",
    "VL_SLD_FIN",
    "IND_DC_FIN",
)

TABLE_NAMES: Mapping[str, str] = {
    "CONFIG": "tbl_CONFIG",
    "PLANO_CONTAS": "tbl_PLANO_CONTAS",
    "MAPEAMENTO_CONTAS": "tbl_MAPEAMENTO_CONTAS",
    "EVENTOS": "tbl_EVENTOS",
    "LANCAMENTOS": "tbl_LANCAMENTOS",
    "PARTIDAS": "tbl_PARTIDAS",
    "VINCULO_EVENTO_LCTO": "tbl_VINCULO_EVENTO_LCTO",
    "DIARIO": "tbl_DIARIO",
    "RAZAO": "tbl_RAZAO",
    "BALANCETE": "tbl_BALANCETE",
    "VALIDACOES": "tbl_VALIDACOES",
    "PROVENIENCIA": "tbl_PROVENIENCIA",
}


@dataclass(frozen=True)
class WorkbookInputs:
    simulation_config: SimulationConfig
    chart_of_accounts: pd.DataFrame
    account_role_mapping: pd.DataFrame
    events: pd.DataFrame


def build_workbook(
    inputs: WorkbookInputs,
    path: str | Path,
    *,
    rule_version: str = "posting_rules_v1",
) -> Path:
    simulation_config = inputs.simulation_config
    period = AccountingPeriod(simulation_config.start_date, simulation_config.end_date)
    chart_of_accounts = inputs.chart_of_accounts.copy(deep=True)
    account_role_mapping = inputs.account_role_mapping.copy(deep=True)
    events = sort_events(normalize_events(inputs.events.copy(deep=True)))

    chart_report = validate_chart_of_accounts(chart_of_accounts)
    mapping_report = validate_account_role_mapping(account_role_mapping, chart_of_accounts)
    event_report = validate_events(events, period)
    _raise_if_invalid("PLANO_CONTAS", chart_report)
    _raise_if_invalid("MAPEAMENTO_CONTAS", mapping_report)
    _raise_if_invalid("EVENTOS", event_report)

    posting_result = post_events(
        events,
        chart_of_accounts,
        simulation_config,
        account_role_mapping=account_role_mapping,
        rule_version=rule_version,
    )
    posting_report = validate_posting_result(posting_result, events, chart_of_accounts)
    _raise_if_invalid("LANCAMENTOS_PARTIDAS", posting_report)

    journal = build_journal(posting_result.journal_entry_headers, posting_result.postings, chart_of_accounts)
    ledger = build_ledger(posting_result.journal_entry_headers, posting_result.postings, chart_of_accounts)
    trial_balance = build_trial_balance(ledger, chart_of_accounts, period)
    ledger_report = validate_ledger_trial_balance(posting_result.postings, ledger, trial_balance, chart_of_accounts, period)
    _raise_if_invalid("RAZAO_BALANCETE", ledger_report)

    validations = _build_validations(
        {
            "PLANO_CONTAS": chart_report,
            "MAPEAMENTO_CONTAS": mapping_report,
            "EVENTOS": event_report,
            "LANCAMENTOS_PARTIDAS": posting_report,
            "RAZAO_BALANCETE": ledger_report,
        }
    )
    provenance = _build_provenance(simulation_config, events, rule_version)

    wb = Workbook()
    wb.remove(wb.active)
    _write_readme(wb)
    _write_table(wb, "CONFIG", _config_to_frame(simulation_config))
    _write_table(wb, "PLANO_CONTAS", _serialize_frame(chart_of_accounts, CHART_OF_ACCOUNTS_COLUMNS))
    _write_table(wb, "MAPEAMENTO_CONTAS", _serialize_frame(account_role_mapping, ACCOUNT_ROLE_MAPPING_COLUMNS))
    _write_table(wb, "EVENTOS", _events_to_workbook(events))
    _write_table(wb, "LANCAMENTOS", _journal_entries_to_workbook(posting_result.journal_entry_headers))
    _write_table(wb, "PARTIDAS", _postings_to_workbook(posting_result.postings))
    _write_table(wb, "VINCULO_EVENTO_LCTO", _serialize_frame(posting_result.event_entry_links, EVENT_ENTRY_LINK_COLUMNS))
    _write_table(wb, "DIARIO", _journal_to_workbook(journal))
    _write_table(wb, "RAZAO", _ledger_to_workbook(ledger))
    _write_table(wb, "BALANCETE", _trial_balance_to_workbook(trial_balance))
    _write_table(wb, "VALIDACOES", validations)
    _write_table(wb, "PROVENIENCIA", provenance)
    _apply_editable_validations(wb)

    if tuple(wb.sheetnames) != WORKBOOK_SHEETS:
        raise AccountingInvariantError("Workbook gerado com abas fora da ordem canônica.")

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path


def load_workbook_inputs(path: str | Path) -> WorkbookInputs:
    wb = load_workbook(path, data_only=True)
    for sheet_name in EDITABLE_SHEETS:
        if sheet_name not in wb.sheetnames:
            raise SchemaValidationError(f"Aba de entrada ausente: {sheet_name}.")

    config = _frame_to_config(_read_table_frame(wb["CONFIG"], CONFIG_COLUMNS))
    chart_of_accounts = _frame_to_chart(_read_table_frame(wb["PLANO_CONTAS"], CHART_OF_ACCOUNTS_COLUMNS))
    account_role_mapping = _read_table_frame(wb["MAPEAMENTO_CONTAS"], ACCOUNT_ROLE_MAPPING_COLUMNS)
    events = _frame_to_events(_read_table_frame(wb["EVENTOS"], EVENT_WORKBOOK_COLUMNS))
    return WorkbookInputs(config, chart_of_accounts, account_role_mapping, events)


def regenerate_workbook(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    rule_version: str = "posting_rules_v1",
) -> Path:
    source_path = Path(input_path)
    inputs = load_workbook_inputs(source_path)
    destination = source_path if output_path is None else Path(output_path)
    return build_workbook(inputs, destination, rule_version=rule_version)


def _config_to_frame(config: SimulationConfig) -> pd.DataFrame:
    rows = [
        ("simulation_id", config.simulation_id),
        ("start_date", config.start_date),
        ("end_date", config.end_date),
        ("currency", config.currency),
        ("seed", config.seed),
        ("scenario_name", config.scenario_name),
        ("spec_version", config.spec_version),
    ]
    return pd.DataFrame(rows, columns=CONFIG_COLUMNS, dtype=object)


def _frame_to_config(frame: pd.DataFrame) -> SimulationConfig:
    values = {str(row["CHAVE"]).strip(): row["VALOR"] for _, row in frame.iterrows()}
    required = {"simulation_id", "start_date", "end_date", "currency", "seed", "scenario_name", "spec_version"}
    missing = required - set(values)
    if missing:
        raise SchemaValidationError(f"CONFIG sem chaves obrigatórias: {sorted(missing)}.")
    return SimulationConfig(
        simulation_id=str(values["simulation_id"]).strip(),
        start_date=_coerce_excel_date(values["start_date"]),
        end_date=_coerce_excel_date(values["end_date"]),
        currency=str(values["currency"]).strip(),
        seed=_coerce_int(values["seed"], "seed"),
        scenario_name=str(values["scenario_name"]).strip(),
        spec_version=str(values["spec_version"]).strip(),
    )


def _frame_to_chart(frame: pd.DataFrame) -> pd.DataFrame:
    chart = frame.copy()
    chart["DT_ALT"] = chart["DT_ALT"].map(_coerce_excel_date)
    chart["NIVEL"] = chart["NIVEL"].map(lambda value: _coerce_int(value, "NIVEL"))
    chart["ATIVA"] = chart["ATIVA"].map(_coerce_bool)
    for column in ("COD_CTA_SUP", "COD_DF"):
        chart[column] = chart[column].map(_blank_to_none)
    return chart.loc[:, list(CHART_OF_ACCOUNTS_COLUMNS)]


def _frame_to_events(frame: pd.DataFrame) -> pd.DataFrame:
    events = frame.copy()
    events["DT_EVENTO"] = events["DT_EVENTO"].map(_coerce_excel_date)
    events["VL_EVENTO_CENTS"] = pd.Series(
        [_excel_money_to_cents(value, optional=False) for value in events["VL_EVENTO"]],
        index=events.index,
        dtype=object,
    )
    events["VL_CUSTO_CENTS"] = pd.Series(
        [_excel_money_to_cents(value, optional=True) for value in events["VL_CUSTO"]],
        index=events.index,
        dtype=object,
    )
    events = events.drop(columns=["VL_EVENTO", "VL_CUSTO"])
    for column in ("MEIO_FINANCEIRO", "CATEGORIA_DESPESA", "COD_PART", "DOC_REF"):
        events[column] = events[column].map(_blank_to_none)
    return events.loc[:, list(EVENT_COLUMNS)]


def _build_validations(reports_by_stage: Mapping[str, ValidationReport]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for stage, report in reports_by_stage.items():
        if report.ok:
            rows.append(
                {
                    "ETAPA": stage,
                    "OK": True,
                    "ISSUE_CODE": None,
                    "MENSAGEM": "ok",
                    "ACCOUNT_CODE": None,
                    "EVENT_ID": None,
                    "ENTRY_ID": None,
                    "POSTING_ID": None,
                }
            )
            continue
        for issue in report.issues:
            rows.append(_validation_issue_to_row(stage, issue))
    return pd.DataFrame(rows, columns=VALIDATION_COLUMNS, dtype=object)


def _validation_issue_to_row(stage: str, issue: ValidationIssue) -> dict[str, object]:
    return {
        "ETAPA": stage,
        "OK": False,
        "ISSUE_CODE": issue.code,
        "MENSAGEM": issue.message,
        "ACCOUNT_CODE": issue.account_code,
        "EVENT_ID": issue.event_id,
        "ENTRY_ID": issue.entry_id,
        "POSTING_ID": issue.posting_id,
    }


def _build_provenance(config: SimulationConfig, events: pd.DataFrame, rule_version: str) -> pd.DataFrame:
    event_versions = sorted({str(value) for value in events["SPEC_VERSION"].dropna()})
    rows = [
        ("workbook_spec_version", WORKBOOK_SPEC_VERSION),
        ("simulation_id", config.simulation_id),
        ("scenario_name", config.scenario_name),
        ("simulation_spec_version", config.spec_version),
        ("posting_rule_version", rule_version),
        ("currency", config.currency),
        ("chart_source", "template_or_input_PLANO_CONTAS"),
        ("event_spec_versions", ",".join(event_versions)),
    ]
    return pd.DataFrame(rows, columns=PROVENANCE_COLUMNS, dtype=object)


def _events_to_workbook(events: pd.DataFrame) -> pd.DataFrame:
    workbook_events = events.copy()
    workbook_events.insert(6, "VL_EVENTO", workbook_events.pop("VL_EVENTO_CENTS").map(_cents_to_excel_money))
    workbook_events.insert(7, "VL_CUSTO", workbook_events.pop("VL_CUSTO_CENTS").map(_optional_cents_to_excel_money))
    return workbook_events.loc[:, list(EVENT_WORKBOOK_COLUMNS)]


def _journal_entries_to_workbook(journal_entries: pd.DataFrame) -> pd.DataFrame:
    return _replace_money_columns(journal_entries, {"VL_LCTO_CENTS": "VL_LCTO"}, JOURNAL_ENTRY_WORKBOOK_COLUMNS)


def _postings_to_workbook(postings: pd.DataFrame) -> pd.DataFrame:
    return _replace_money_columns(postings, {"VL_DC_CENTS": "VL_DC"}, POSTING_WORKBOOK_COLUMNS)


def _journal_to_workbook(journal: pd.DataFrame) -> pd.DataFrame:
    return _replace_money_columns(journal, {"VL_DC_CENTS": "VL_DC"}, JOURNAL_VIEW_WORKBOOK_COLUMNS)


def _ledger_to_workbook(ledger: pd.DataFrame) -> pd.DataFrame:
    return _replace_money_columns(
        ledger,
        {
            "DEBITO_CENTS": "DEBITO",
            "CREDITO_CENTS": "CREDITO",
            "MOVIMENTO_ASSINADO_CENTS": "MOVIMENTO_ASSINADO",
            "SALDO_ASSINADO_CENTS": "SALDO_ASSINADO",
            "SALDO_ABS_CENTS": "SALDO_ABS",
        },
        LEDGER_VIEW_WORKBOOK_COLUMNS,
    )


def _trial_balance_to_workbook(trial_balance: pd.DataFrame) -> pd.DataFrame:
    return _replace_money_columns(
        trial_balance,
        {
            "VL_SLD_INI_CENTS": "VL_SLD_INI",
            "VL_DEB_CENTS": "VL_DEB",
            "VL_CRED_CENTS": "VL_CRED",
            "VL_SLD_FIN_CENTS": "VL_SLD_FIN",
        },
        TRIAL_BALANCE_WORKBOOK_COLUMNS,
    )


def _replace_money_columns(
    frame: pd.DataFrame,
    replacements: Mapping[str, str],
    output_columns: tuple[str, ...],
) -> pd.DataFrame:
    workbook_frame = frame.copy()
    for cents_column, workbook_column in replacements.items():
        position = list(workbook_frame.columns).index(cents_column)
        workbook_frame.insert(position, workbook_column, workbook_frame.pop(cents_column).map(_cents_to_excel_money))
    return workbook_frame.loc[:, list(output_columns)]


def _serialize_frame(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    serialized = frame.copy()
    for column in columns:
        if column not in serialized.columns:
            serialized[column] = None
    return serialized.loc[:, list(columns)]


def _write_readme(wb: Workbook) -> None:
    ws = wb.create_sheet("README")
    rows = [
        ("Workbook contábil parametrizado", None),
        ("Versão", WORKBOOK_SPEC_VERSION),
        ("Regra operacional", "Editar somente CONFIG, PLANO_CONTAS, MAPEAMENTO_CONTAS e EVENTOS; regenerar pelo Python."),
        ("Derivadas", "LANCAMENTOS, PARTIDAS, VINCULO_EVENTO_LCTO, DIARIO, RAZAO, BALANCETE, VALIDACOES e PROVENIENCIA."),
        ("Fonte de verdade", "Objetos derivados são reconstruídos a partir das abas de entrada."),
    ]
    for row_number, values in enumerate(rows, start=1):
        ws.cell(row=row_number, column=1, value=values[0])
        ws.cell(row=row_number, column=2, value=values[1])
    ws["A1"].font = Font(bold=True, size=14)
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 96


def _write_table(wb: Workbook, sheet_name: str, frame: pd.DataFrame) -> None:
    ws = wb.create_sheet(sheet_name)
    materialized = frame.where(pd.notna(frame), None)
    columns = list(materialized.columns)
    ws.append(columns)
    for row in materialized.itertuples(index=False, name=None):
        ws.append(list(row))

    ws.freeze_panes = "A2"
    _style_header(ws, sheet_name)
    _format_columns(ws, columns)
    _set_column_widths(ws, columns)

    table_ref = f"A1:{get_column_letter(len(columns))}{max(ws.max_row, 1)}"
    table = Table(displayName=TABLE_NAMES[sheet_name], ref=table_ref)
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=False)
    ws.add_table(table)


def _style_header(ws, sheet_name: str) -> None:
    fill_color = "D9EAF7" if sheet_name in EDITABLE_SHEETS else "E7E6E6"
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor=fill_color)


def _format_columns(ws, columns: list[str]) -> None:
    money_columns = {
        "VL_EVENTO",
        "VL_CUSTO",
        "VL_LCTO",
        "VL_DC",
        "DEBITO",
        "CREDITO",
        "MOVIMENTO_ASSINADO",
        "SALDO_ASSINADO",
        "SALDO_ABS",
        "VL_SLD_INI",
        "VL_DEB",
        "VL_CRED",
        "VL_SLD_FIN",
    }
    date_columns = {"DT_ALT", "DT_EVENTO", "DT_LCTO", "DT_LCTO_EXT", "DT_INI", "DT_FIN"}
    for column_index, column_name in enumerate(columns, start=1):
        number_format = None
        if column_name in money_columns:
            number_format = '#,##0.00'
        elif column_name in date_columns:
            number_format = "yyyy-mm-dd"
        if number_format is None:
            continue
        for cell in ws.iter_cols(min_col=column_index, max_col=column_index, min_row=2, max_row=ws.max_row):
            for item in cell:
                item.number_format = number_format


def _set_column_widths(ws, columns: list[str]) -> None:
    for index, column_name in enumerate(columns, start=1):
        width = min(max(len(column_name) + 2, 12), 34)
        if column_name in {"HIST", "MENSAGEM"}:
            width = 42
        if column_name in {"COD_CTA", "COD_CTA_SUP", "PAPEL_CONTABIL"}:
            width = 22
        ws.column_dimensions[get_column_letter(index)].width = width


def _apply_editable_validations(wb: Workbook) -> None:
    _add_list_validation(wb["CONFIG"], "B", '"BRL"', 5, 5)
    _add_list_validation(wb["PLANO_CONTAS"], "B", '"01,02,03,04,05,09"', 2, 1000)
    _add_list_validation(wb["PLANO_CONTAS"], "C", '"S,A"', 2, 1000)
    _add_list_validation(wb["PLANO_CONTAS"], "H", '"D,C"', 2, 1000)
    _add_list_validation(wb["PLANO_CONTAS"], "J", '"TRUE,FALSE"', 2, 1000)
    _add_list_validation(wb["PLANO_CONTAS"], "K", '"observada,sintética,template,ajustada"', 2, 1000)
    _add_list_validation(wb["EVENTOS"], "C", f'"{",".join(item.value for item in EventClass)}"', 2, 1000)
    _add_list_validation(wb["EVENTOS"], "D", f'"{",".join(item.value for item in EventType)}"', 2, 1000)
    _add_list_validation(wb["EVENTOS"], "E", f'"{",".join(item.value for item in EventDirection)}"', 2, 1000)
    _add_list_validation(wb["EVENTOS"], "F", f'"{",".join(item.value for item in EventNature)}"', 2, 1000)
    _add_list_validation(wb["EVENTOS"], "I", '"caixa,banco"', 2, 1000)
    _add_list_validation(wb["EVENTOS"], "J", '"salarios,aluguel,utilidades,juros"', 2, 1000)
    _add_list_validation(wb["EVENTOS"], "L", f'"{",".join(item.value for item in PaymentTerm)}"', 2, 1000)
    _add_list_validation(wb["EVENTOS"], "O", f'"{",".join(item.value for item in Origin)}"', 2, 1000)


def _add_list_validation(ws, column: str, formula: str, first_row: int, last_row: int) -> None:
    validation = DataValidation(type="list", formula1=formula, allow_blank=True)
    ws.add_data_validation(validation)
    validation.add(f"{column}{first_row}:{column}{last_row}")


def _read_table_frame(ws, expected_columns: tuple[str, ...]) -> pd.DataFrame:
    if not ws.tables:
        raise SchemaValidationError(f"Aba {ws.title} não contém tabela nomeada.")
    table = next(iter(ws.tables.values()))
    min_col, min_row, max_col, max_row = range_boundaries(table.ref)
    rows = list(ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col, values_only=True))
    if not rows:
        raise SchemaValidationError(f"Tabela vazia em {ws.title}.")
    headers = tuple(str(value).strip() for value in rows[0])
    if headers != expected_columns:
        raise SchemaValidationError(f"Schema físico inválido em {ws.title}: {headers}.")
    data_rows = [row for row in rows[1:] if any(value is not None for value in row)]
    return pd.DataFrame(data_rows, columns=expected_columns, dtype=object)


def _coerce_excel_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    return parse_iso_date(value)  # type: ignore[arg-type]


def _coerce_int(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise SchemaValidationError(f"{field_name} deve ser inteiro, não bool.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(f"{field_name} inválido: {value!r}.") from exc


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "sim", "s"}:
            return True
        if lowered in {"false", "0", "nao", "não", "n"}:
            return False
    raise SchemaValidationError(f"Valor booleano inválido: {value!r}.")


def _blank_to_none(value: object) -> object | None:
    if pd.isna(value):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _cents_to_excel_money(value: int) -> Decimal:
    return Decimal(int(value)) / Decimal("100")


def _optional_cents_to_excel_money(value: object) -> Decimal | None:
    if pd.isna(value) or value is None:
        return None
    return _cents_to_excel_money(int(value))


def _excel_money_to_cents(value: object, *, optional: bool) -> int | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        if optional:
            return None
        raise SchemaValidationError("Valor monetário obrigatório ausente.")
    try:
        decimal_value = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise SchemaValidationError(f"Valor monetário inválido: {value!r}.") from exc
    cents = decimal_value * Decimal("100")
    if cents != cents.to_integral_value():
        raise SchemaValidationError("Valor monetário deve ter no máximo duas casas decimais.")
    return int(cents)


def _raise_if_invalid(stage: str, report: ValidationReport) -> None:
    if report.ok:
        return
    details = "; ".join(issue.code for issue in report.issues[:5])
    raise AccountingInvariantError(f"{stage} inválido: {details}")
