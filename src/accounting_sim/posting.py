"""Operador determinístico de escrituração da spec 04."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from accounting_sim.canonical import (
    EVENT_ENTRY_LINK_COLUMNS,
    JOURNAL_ENTRY_HEADER_COLUMNS,
    POSTING_COLUMNS,
    AccountingInvariantError,
    AccountingPeriod,
    DebitCredit,
    EventType,
    JournalEntryType,
    PaymentTerm,
    SimulationConfig,
    ValidationIssue,
    ValidationReport,
)
from accounting_sim.account_mapping import (
    DEFAULT_ACCOUNT_ROLE_MAP,
    account_role_map_as_dict,
    build_default_account_role_mapping,
)
from accounting_sim.chart_of_accounts import get_analytic_accounts, validate_chart_of_accounts
from accounting_sim.events import normalize_events, sort_events, validate_events


ACCOUNT_CODE_MAP = DEFAULT_ACCOUNT_ROLE_MAP

EXPENSE_CATEGORY_ACCOUNT_KEYS: dict[str, str] = {
    "salarios": "despesa_salarios",
    "aluguel": "despesa_aluguel",
    "utilidades": "despesa_utilidades",
    "juros": "despesa_juros",
}


@dataclass(frozen=True)
class PostingResult:
    journal_entry_headers: pd.DataFrame
    postings: pd.DataFrame
    event_entry_links: pd.DataFrame


@dataclass
class _PostingBuilder:
    simulation_id: str
    rule_version: str
    account_codes: dict[str, str]
    entry_counter: int = 0
    posting_counter: int = 0

    def add_entry(
        self,
        headers: list[dict[str, object]],
        postings: list[dict[str, object]],
        links: list[dict[str, object]],
        event: pd.Series,
        lines: tuple[tuple[str, str, int], ...],
        order_within_event: int,
        history: str,
    ) -> None:
        self.entry_counter += 1
        num_lcto = f"L{self.entry_counter:06d}"
        debit_total = sum(amount for _, side, amount in lines if side == DebitCredit.DEBIT.value)

        headers.append(
            {
                "NUM_LCTO": num_lcto,
                "DT_LCTO": event["DT_EVENTO"],
                "VL_LCTO_CENTS": debit_total,
                "IND_LCTO": JournalEntryType.NORMAL.value,
                "DT_LCTO_EXT": None,
                "ID_GERACAO": self.simulation_id,
                "VERSAO_REGRA": self.rule_version,
            }
        )
        links.append(
            {
                "ID_EVENTO": event["ID_EVENTO"],
                "NUM_LCTO": num_lcto,
                "ORDEM_LCTO_EVENTO": order_within_event,
            }
        )

        for account_code, side, amount_cents in lines:
            self.posting_counter += 1
            postings.append(
                {
                    "ID_PARTIDA": f"P{self.posting_counter:06d}",
                    "NUM_LCTO": num_lcto,
                    "COD_CTA": account_code,
                    "COD_CCUS": None,
                    "VL_DC_CENTS": amount_cents,
                    "IND_DC": side,
                    "NUM_ARQ": event["DOC_REF"],
                    "COD_HIST_PAD": None,
                    "HIST": history,
                    "COD_PART": event["COD_PART"],
                    "ID_ORIGEM": event["ID_EVENTO"],
                }
            )

    def account(self, role: str) -> str:
        return self.account_codes[role]


def post_events(
    events: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    simulation_config: SimulationConfig,
    *,
    account_role_mapping: pd.DataFrame | None = None,
    rule_version: str = "posting_rules_v1",
) -> PostingResult:
    period = AccountingPeriod(simulation_config.start_date, simulation_config.end_date)
    event_report = validate_events(events, period)
    if not event_report.ok:
        raise AccountingInvariantError(_format_issues("Eventos inválidos", event_report))
    chart_report = validate_chart_of_accounts(chart_of_accounts)
    if not chart_report.ok:
        raise AccountingInvariantError(_format_issues("Plano de contas inválido", chart_report))

    normalized_events = sort_events(normalize_events(events))
    effective_mapping = account_role_mapping if account_role_mapping is not None else build_default_account_role_mapping()
    account_codes = account_role_map_as_dict(effective_mapping, chart_of_accounts)

    headers: list[dict[str, object]] = []
    postings: list[dict[str, object]] = []
    links: list[dict[str, object]] = []
    builder = _PostingBuilder(simulation_config.simulation_id, rule_version, account_codes)

    dispatch: dict[str, Callable[[pd.Series, _PostingBuilder, list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]], None]] = {
        EventType.CAPITAL_CONTRIBUTION.value: _post_capital_contribution,
        EventType.PURCHASE_CASH.value: _post_purchase_cash,
        EventType.PURCHASE_CREDIT.value: _post_purchase_credit,
        EventType.SUPPLIER_PAYMENT.value: _post_supplier_payment,
        EventType.SALE_CASH.value: _post_sale_cash,
        EventType.SALE_CREDIT.value: _post_sale_credit,
        EventType.CUSTOMER_RECEIPT.value: _post_customer_receipt,
        EventType.OPERATING_EXPENSE_CASH.value: _post_operating_expense_cash,
        EventType.DEPRECIATION.value: _post_depreciation,
    }

    for _, event in normalized_events.iterrows():
        dispatch[event["TIPO_EVENTO"]](event, builder, headers, postings, links)

    result = PostingResult(
        journal_entry_headers=pd.DataFrame(headers, columns=JOURNAL_ENTRY_HEADER_COLUMNS, dtype=object),
        postings=pd.DataFrame(postings, columns=POSTING_COLUMNS, dtype=object),
        event_entry_links=pd.DataFrame(links, columns=EVENT_ENTRY_LINK_COLUMNS, dtype=object),
    )
    report = validate_posting_result(result, normalized_events, chart_of_accounts)
    if not report.ok:
        raise AccountingInvariantError(_format_issues("Resultado de escrituração inválido", report))
    return result


def validate_posting_result(
    result: PostingResult,
    events: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    headers = result.journal_entry_headers.copy()
    postings = result.postings.copy()
    links = result.event_entry_links.copy()
    normalized_events = sort_events(normalize_events(events))

    issues.extend(_validate_columns(headers, JOURNAL_ENTRY_HEADER_COLUMNS, "missing_journal_entry_column"))
    issues.extend(_validate_columns(postings, POSTING_COLUMNS, "missing_posting_column"))
    issues.extend(_validate_columns(links, EVENT_ENTRY_LINK_COLUMNS, "missing_event_entry_link_column"))
    if issues:
        return ValidationReport(ok=False, issues=tuple(issues))

    event_ids = set(normalized_events["ID_EVENTO"])
    entry_ids = set(headers["NUM_LCTO"])
    analytic_codes = set(get_analytic_accounts(chart_of_accounts, active_only=True)["COD_CTA"])

    if not headers["NUM_LCTO"].is_unique:
        issues.append(ValidationIssue("duplicate_journal_entry_id", "NUM_LCTO deve ser único."))
    if not postings["ID_PARTIDA"].is_unique:
        issues.append(ValidationIssue("duplicate_posting_id", "ID_PARTIDA deve ser único."))

    for _, posting in postings.iterrows():
        entry_id = posting["NUM_LCTO"]
        posting_id = posting["ID_PARTIDA"]
        account_code = posting["COD_CTA"]
        amount = posting["VL_DC_CENTS"]
        if entry_id not in entry_ids:
            issues.append(ValidationIssue("missing_journal_entry_for_posting", "PARTIDAS.NUM_LCTO sem cabeçalho.", entry_id=entry_id, posting_id=posting_id))
        if account_code not in analytic_codes:
            issues.append(ValidationIssue("invalid_posting_account", "COD_CTA deve ser conta analítica ativa.", account_code=account_code, posting_id=posting_id))
        if not isinstance(amount, int) or amount <= 0:
            issues.append(ValidationIssue("non_positive_posting_amount", "VL_DC_CENTS deve ser int > 0.", posting_id=posting_id))
        if posting["IND_DC"] not in {DebitCredit.DEBIT.value, DebitCredit.CREDIT.value}:
            issues.append(ValidationIssue("invalid_debit_credit_indicator", "IND_DC deve ser D ou C.", posting_id=posting_id))
        if posting["ID_ORIGEM"] not in event_ids:
            issues.append(ValidationIssue("missing_origin_event", "ID_ORIGEM deve referenciar EVENTOS.", event_id=posting["ID_ORIGEM"], posting_id=posting_id))

    for _, link in links.iterrows():
        if link["ID_EVENTO"] not in event_ids:
            issues.append(ValidationIssue("link_missing_event", "Vínculo referencia evento inexistente.", event_id=link["ID_EVENTO"]))
        if link["NUM_LCTO"] not in entry_ids:
            issues.append(ValidationIssue("link_missing_entry", "Vínculo referencia lançamento inexistente.", entry_id=link["NUM_LCTO"]))

    linked_entries = set(links["NUM_LCTO"])
    for entry_id in entry_ids:
        if entry_id not in linked_entries:
            issues.append(ValidationIssue("journal_entry_without_event_link", "Lançamento sem vínculo com evento.", entry_id=entry_id))

    event_dates = normalized_events.set_index("ID_EVENTO")["DT_EVENTO"].to_dict()
    link_by_entry = links.drop_duplicates("NUM_LCTO").set_index("NUM_LCTO")["ID_EVENTO"].to_dict()
    for _, header in headers.iterrows():
        entry_id = header["NUM_LCTO"]
        entry_postings = postings[postings["NUM_LCTO"] == entry_id]
        debit_total = int(entry_postings.loc[entry_postings["IND_DC"] == DebitCredit.DEBIT.value, "VL_DC_CENTS"].sum())
        credit_total = int(entry_postings.loc[entry_postings["IND_DC"] == DebitCredit.CREDIT.value, "VL_DC_CENTS"].sum())
        if debit_total != credit_total:
            issues.append(ValidationIssue("unbalanced_journal_entry", "Débitos e créditos do lançamento devem ser iguais.", entry_id=entry_id))
        if header["VL_LCTO_CENTS"] != debit_total or header["VL_LCTO_CENTS"] != credit_total:
            issues.append(ValidationIssue("invalid_journal_entry_amount", "VL_LCTO_CENTS deve ser a soma de um lado.", entry_id=entry_id))
        if header["IND_LCTO"] != JournalEntryType.NORMAL.value:
            issues.append(ValidationIssue("invalid_journal_entry_type", "IND_LCTO deve ser N no MVP.", entry_id=entry_id))
        if header["DT_LCTO_EXT"] is not None:
            issues.append(ValidationIssue("unexpected_extemporaneous_date", "DT_LCTO_EXT deve ser None no MVP.", entry_id=entry_id))
        origin_event_id = link_by_entry.get(entry_id)
        if origin_event_id in event_dates and header["DT_LCTO"] != event_dates[origin_event_id]:
            issues.append(ValidationIssue("journal_entry_date_mismatch", "DT_LCTO deve preservar DT_EVENTO.", event_id=origin_event_id, entry_id=entry_id))

    return ValidationReport(ok=not issues, issues=tuple(issues))


def _post_capital_contribution(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    amount = event["VL_EVENTO_CENTS"]
    builder.add_entry(headers, postings, links, event, ((_financial_account(event, builder), "D", amount), (builder.account("capital_social"), "C", amount)), 1, event["HIST"])


def _post_purchase_cash(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    amount = event["VL_EVENTO_CENTS"]
    builder.add_entry(headers, postings, links, event, ((builder.account("estoques"), "D", amount), (_financial_account(event, builder), "C", amount)), 1, event["HIST"])


def _post_purchase_credit(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    amount = event["VL_EVENTO_CENTS"]
    builder.add_entry(headers, postings, links, event, ((builder.account("estoques"), "D", amount), (builder.account("fornecedores"), "C", amount)), 1, event["HIST"])


def _post_supplier_payment(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    amount = event["VL_EVENTO_CENTS"]
    builder.add_entry(headers, postings, links, event, ((builder.account("fornecedores"), "D", amount), (_financial_account(event, builder), "C", amount)), 1, event["HIST"])


def _post_sale_cash(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    _post_sale(event, builder, headers, postings, links, _financial_account(event, builder))


def _post_sale_credit(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    _post_sale(event, builder, headers, postings, links, builder.account("clientes"))


def _post_sale(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]], debit_account: str) -> None:
    amount = event["VL_EVENTO_CENTS"]
    cost = event["VL_CUSTO_CENTS"]
    if cost is None or cost <= 0:
        raise AccountingInvariantError("Venda deve gerar lançamento de CMV com VL_CUSTO_CENTS > 0 na spec 04.")
    builder.add_entry(headers, postings, links, event, ((debit_account, "D", amount), (builder.account("receita_vendas"), "C", amount)), 1, event["HIST"])
    builder.add_entry(headers, postings, links, event, ((builder.account("cmv"), "D", cost), (builder.account("estoques"), "C", cost)), 2, f"CMV - {event['HIST']}")


def _post_customer_receipt(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    amount = event["VL_EVENTO_CENTS"]
    builder.add_entry(headers, postings, links, event, ((_financial_account(event, builder), "D", amount), (builder.account("clientes"), "C", amount)), 1, event["HIST"])


def _post_operating_expense_cash(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    amount = event["VL_EVENTO_CENTS"]
    expense_key = EXPENSE_CATEGORY_ACCOUNT_KEYS[event["CATEGORIA_DESPESA"]]
    builder.add_entry(headers, postings, links, event, ((builder.account(expense_key), "D", amount), (_financial_account(event, builder), "C", amount)), 1, event["HIST"])


def _post_depreciation(event: pd.Series, builder: _PostingBuilder, headers: list[dict[str, object]], postings: list[dict[str, object]], links: list[dict[str, object]]) -> None:
    amount = event["VL_EVENTO_CENTS"]
    builder.add_entry(headers, postings, links, event, ((builder.account("despesa_depreciacao"), "D", amount), (builder.account("depreciacao_acumulada"), "C", amount)), 1, event["HIST"])


def _financial_account(event: pd.Series, builder: _PostingBuilder) -> str:
    return builder.account(event["MEIO_FINANCEIRO"])


def _validate_columns(df: pd.DataFrame, columns: tuple[str, ...], issue_code: str) -> tuple[ValidationIssue, ...]:
    return tuple(
        ValidationIssue(issue_code, f"Coluna obrigatória ausente: {column}.")
        for column in columns
        if column not in df.columns
    )


def _format_issues(prefix: str, report: ValidationReport) -> str:
    details = "; ".join(issue.code for issue in report.issues[:5])
    return f"{prefix}: {details}"
