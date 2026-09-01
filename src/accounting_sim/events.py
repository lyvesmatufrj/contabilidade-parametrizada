"""Eventos econômicos canônicos da spec 03."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from accounting_sim.canonical import (
    EVENT_COLUMNS,
    AccountingPeriod,
    EventClass,
    EventDirection,
    EventNature,
    EventType,
    Origin,
    PaymentTerm,
    SchemaValidationError,
    ValidationIssue,
    ValidationReport,
    parse_iso_date,
)


DEFAULT_DEMO_EVENTS_PATH = Path(__file__).resolve().parents[2] / "data" / "examples" / "events_mvp.csv"
EVENT_SPEC_VERSION = "spec_03_events_v1"

FINANCIAL_MEDIA = frozenset({"caixa", "banco"})
EXPENSE_CATEGORIES = frozenset({"salarios", "aluguel", "utilidades", "juros"})

IMMEDIATE_FINANCIAL_EVENT_TYPES = frozenset(
    {
        EventType.CAPITAL_CONTRIBUTION.value,
        EventType.PURCHASE_CASH.value,
        EventType.SUPPLIER_PAYMENT.value,
        EventType.SALE_CASH.value,
        EventType.CUSTOMER_RECEIPT.value,
        EventType.OPERATING_EXPENSE_CASH.value,
    }
)

EXPECTED_EVENT_CLASS = {
    EventType.DEPRECIATION.value: EventClass.ADJUSTMENT.value,
}

EXPECTED_DIRECTION = {
    EventType.CAPITAL_CONTRIBUTION.value: EventDirection.IN.value,
    EventType.PURCHASE_CASH.value: EventDirection.IN.value,
    EventType.PURCHASE_CREDIT.value: EventDirection.IN.value,
    EventType.SUPPLIER_PAYMENT.value: EventDirection.OUT.value,
    EventType.SALE_CASH.value: EventDirection.OUT.value,
    EventType.SALE_CREDIT.value: EventDirection.OUT.value,
    EventType.CUSTOMER_RECEIPT.value: EventDirection.IN.value,
    EventType.OPERATING_EXPENSE_CASH.value: EventDirection.OUT.value,
    EventType.DEPRECIATION.value: EventDirection.NA.value,
}

EXPECTED_PAYMENT_TERM = {
    EventType.PURCHASE_CASH.value: PaymentTerm.CASH.value,
    EventType.PURCHASE_CREDIT.value: PaymentTerm.CREDIT.value,
    EventType.SALE_CASH.value: PaymentTerm.CASH.value,
    EventType.SALE_CREDIT.value: PaymentTerm.CREDIT.value,
    EventType.CAPITAL_CONTRIBUTION.value: PaymentTerm.NA.value,
    EventType.SUPPLIER_PAYMENT.value: PaymentTerm.NA.value,
    EventType.CUSTOMER_RECEIPT.value: PaymentTerm.NA.value,
    EventType.OPERATING_EXPENSE_CASH.value: PaymentTerm.NA.value,
    EventType.DEPRECIATION.value: PaymentTerm.NA.value,
}


def load_events(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return sort_events(normalize_events(df))


def save_events(df: pd.DataFrame, path: str | Path) -> Path:
    normalized = sort_events(normalize_events(df))
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    serialized = normalized.copy()
    serialized["DT_EVENTO"] = serialized["DT_EVENTO"].map(lambda value: value.isoformat())
    for column in ("VL_CUSTO_CENTS", "MEIO_FINANCEIRO", "CATEGORIA_DESPESA", "COD_PART", "DOC_REF"):
        serialized[column] = serialized[column].map(lambda value: "" if pd.isna(value) else value)
    serialized.to_csv(output_path, index=False)
    return output_path


def validate_events(df: pd.DataFrame, period: AccountingPeriod) -> ValidationReport:
    issues: list[ValidationIssue] = []
    missing_columns = [column for column in EVENT_COLUMNS if column not in df.columns]
    for column in missing_columns:
        issues.append(ValidationIssue("missing_column", f"Coluna obrigatória ausente: {column}."))
    if missing_columns:
        return ValidationReport(ok=False, issues=tuple(issues))

    events = normalize_events(df)
    ids = events["ID_EVENTO"].astype(str)

    for _, row in events[ids.str.strip() == ""].iterrows():
        issues.append(ValidationIssue("empty_event_id", "ID_EVENTO não pode ser vazio."))

    for _, row in events[ids.duplicated(keep=False)].iterrows():
        issues.append(
            ValidationIssue(
                "duplicate_event_id",
                f"ID_EVENTO duplicado: {row['ID_EVENTO']}.",
                event_id=row["ID_EVENTO"],
            )
        )

    issues.extend(_validate_event_rows(events, period))
    return ValidationReport(ok=not issues, issues=tuple(issues))


def build_demo_events(period: AccountingPeriod) -> pd.DataFrame:
    rows = [
        _event("E001", _date_at_offset(period, 0), EventType.CAPITAL_CONTRIBUTION, 10000000, None, "caixa", None, "Integralização de capital em caixa"),
        _event("E002", _date_at_offset(period, 1), EventType.PURCHASE_CREDIT, 3000000, None, None, None, "Compra de mercadorias a prazo"),
        _event("E003", _date_at_offset(period, 2), EventType.SUPPLIER_PAYMENT, 1000000, None, "caixa", None, "Pagamento parcial de fornecedor"),
        _event("E004", _date_at_offset(period, 3), EventType.SALE_CASH, 4000000, 1600000, "caixa", None, "Venda à vista de mercadorias"),
        _event("E005", _date_at_offset(period, 4), EventType.SALE_CREDIT, 5000000, 2000000, None, None, "Venda a prazo de mercadorias"),
        _event("E006", _date_at_offset(period, 5), EventType.CUSTOMER_RECEIPT, 3000000, None, "caixa", None, "Recebimento de cliente"),
        _event("E007", _date_at_offset(period, 6), EventType.OPERATING_EXPENSE_CASH, 500000, None, "caixa", "aluguel", "Pagamento de aluguel"),
        _event("E008", _date_at_offset(period, 7), EventType.DEPRECIATION, 20000, None, None, None, "Depreciação do período"),
    ]
    return sort_events(normalize_events(pd.DataFrame(rows, columns=EVENT_COLUMNS, dtype=object)))


def normalize_events(df: pd.DataFrame) -> pd.DataFrame:
    return _normalize_events(df)


def sort_events(df: pd.DataFrame) -> pd.DataFrame:
    return _sort_events(df)


def _event(
    event_id: str,
    event_date: date,
    event_type: EventType,
    amount_cents: int,
    cost_cents: int | None,
    financial_medium: str | None,
    expense_category: str | None,
    history: str,
) -> list[object]:
    event_type_value = event_type.value
    event_class = EXPECTED_EVENT_CLASS.get(event_type_value, EventClass.TRANSACTION.value)
    return [
        event_id,
        event_date,
        event_class,
        event_type_value,
        EXPECTED_DIRECTION[event_type_value],
        _default_nature(event_type),
        amount_cents,
        cost_cents,
        financial_medium,
        expense_category,
        None,
        EXPECTED_PAYMENT_TERM[event_type_value],
        None,
        history,
        Origin.SYNTHETIC.value,
        EVENT_SPEC_VERSION,
    ]


def _default_nature(event_type: EventType) -> str:
    if event_type in {EventType.PURCHASE_CASH, EventType.PURCHASE_CREDIT, EventType.SALE_CASH, EventType.SALE_CREDIT}:
        return EventNature.GOOD.value
    if event_type is EventType.OPERATING_EXPENSE_CASH:
        return EventNature.SERVICE.value
    if event_type is EventType.DEPRECIATION:
        return EventNature.ADJUSTMENT.value
    return EventNature.FINANCIAL.value


def _date_at_offset(period: AccountingPeriod, days: int) -> date:
    candidate = period.start_date + timedelta(days=days)
    return min(candidate, period.end_date)


def _normalize_events(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    if set(EVENT_COLUMNS).issubset(normalized.columns):
        normalized = normalized.loc[:, list(EVENT_COLUMNS)]

    for column in (
        "ID_EVENTO",
        "CLASSE_EVENTO",
        "TIPO_EVENTO",
        "DIRECAO",
        "NATUREZA",
        "MEIO_FINANCEIRO",
        "CATEGORIA_DESPESA",
        "COD_PART",
        "COND_PAGTO",
        "DOC_REF",
        "HIST",
        "ORIGEM",
        "SPEC_VERSION",
    ):
        if column in normalized.columns:
            required = column not in {"MEIO_FINANCEIRO", "CATEGORIA_DESPESA", "COD_PART", "DOC_REF"}
            normalized[column] = normalized[column].map(_clean_required_string if required else _clean_optional_string)

    if "DT_EVENTO" in normalized.columns:
        normalized["DT_EVENTO"] = normalized["DT_EVENTO"].map(parse_iso_date)
    if "VL_EVENTO_CENTS" in normalized.columns:
        normalized["VL_EVENTO_CENTS"] = pd.Series(
            [_parse_int(value) for value in normalized["VL_EVENTO_CENTS"]],
            index=normalized.index,
            dtype=object,
        )
    if "VL_CUSTO_CENTS" in normalized.columns:
        normalized["VL_CUSTO_CENTS"] = pd.Series(
            [_parse_optional_int(value) for value in normalized["VL_CUSTO_CENTS"]],
            index=normalized.index,
            dtype=object,
        )

    return normalized


def _validate_event_rows(events: pd.DataFrame, period: AccountingPeriod) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    valid_classes = {item.value for item in EventClass}
    valid_types = {item.value for item in EventType}
    valid_directions = {item.value for item in EventDirection}
    valid_natures = {item.value for item in EventNature}
    valid_payment_terms = {item.value for item in PaymentTerm}
    valid_origins = {item.value for item in Origin}

    for _, row in events.iterrows():
        event_id = row["ID_EVENTO"]
        event_type = row["TIPO_EVENTO"]

        if not (period.start_date <= row["DT_EVENTO"] <= period.end_date):
            issues.append(ValidationIssue("event_outside_period", "DT_EVENTO fora do período contábil.", event_id=event_id))
        if event_type not in valid_types:
            issues.append(ValidationIssue("invalid_event_type", "TIPO_EVENTO fora do enum do MVP.", event_id=event_id))
        if row["CLASSE_EVENTO"] not in valid_classes:
            issues.append(ValidationIssue("invalid_event_class", "CLASSE_EVENTO deve ser TR ou ADJ.", event_id=event_id))
        if row["DIRECAO"] not in valid_directions:
            issues.append(ValidationIssue("invalid_event_direction", "DIRECAO inválida.", event_id=event_id))
        if row["NATUREZA"] not in valid_natures:
            issues.append(ValidationIssue("invalid_event_nature", "NATUREZA inválida.", event_id=event_id))
        if row["COND_PAGTO"] not in valid_payment_terms:
            issues.append(ValidationIssue("invalid_payment_term", "COND_PAGTO inválida.", event_id=event_id))
        if row["ORIGEM"] not in valid_origins:
            issues.append(ValidationIssue("invalid_origin", "ORIGEM fora do enum canônico.", event_id=event_id))
        if row["HIST"] == "":
            issues.append(ValidationIssue("empty_history", "HIST não pode ser vazio.", event_id=event_id))
        if not isinstance(row["VL_EVENTO_CENTS"], int) or row["VL_EVENTO_CENTS"] <= 0:
            issues.append(ValidationIssue("non_positive_event_amount", "VL_EVENTO_CENTS deve ser int > 0.", event_id=event_id))
        cost = row["VL_CUSTO_CENTS"]
        if cost is not None and (not isinstance(cost, int) or cost < 0):
            issues.append(ValidationIssue("invalid_cost_amount", "VL_CUSTO_CENTS deve ser int >= 0 quando preenchido.", event_id=event_id))
        if event_type in valid_types:
            issues.extend(_validate_event_semantics(row))

    return tuple(issues)


def _validate_event_semantics(row: pd.Series) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    event_id = row["ID_EVENTO"]
    event_type = row["TIPO_EVENTO"]

    expected_class = EXPECTED_EVENT_CLASS.get(event_type, EventClass.TRANSACTION.value)
    if row["CLASSE_EVENTO"] != expected_class:
        issues.append(ValidationIssue("invalid_event_class_for_type", "CLASSE_EVENTO incompatível com TIPO_EVENTO.", event_id=event_id))
    if row["DIRECAO"] != EXPECTED_DIRECTION[event_type]:
        issues.append(ValidationIssue("invalid_direction_for_type", "DIRECAO incompatível com TIPO_EVENTO.", event_id=event_id))
    if row["COND_PAGTO"] != EXPECTED_PAYMENT_TERM[event_type]:
        issues.append(ValidationIssue("invalid_payment_term_for_type", "COND_PAGTO incompatível com TIPO_EVENTO.", event_id=event_id))

    financial_medium = row["MEIO_FINANCEIRO"]
    if event_type in IMMEDIATE_FINANCIAL_EVENT_TYPES and financial_medium is None:
        issues.append(ValidationIssue("missing_financial_medium", "MEIO_FINANCEIRO obrigatório para evento com liquidação imediata.", event_id=event_id))
    if financial_medium is not None and financial_medium not in FINANCIAL_MEDIA:
        issues.append(ValidationIssue("invalid_financial_medium", "MEIO_FINANCEIRO deve ser caixa ou banco.", event_id=event_id))
    if event_type == EventType.DEPRECIATION.value and financial_medium is not None:
        issues.append(ValidationIssue("unexpected_financial_medium", "Depreciação não deve ter MEIO_FINANCEIRO.", event_id=event_id))

    expense_category = row["CATEGORIA_DESPESA"]
    if event_type == EventType.OPERATING_EXPENSE_CASH.value and expense_category is None:
        issues.append(ValidationIssue("missing_expense_category", "CATEGORIA_DESPESA obrigatória para despesa operacional.", event_id=event_id))
    if expense_category is not None and expense_category not in EXPENSE_CATEGORIES:
        issues.append(ValidationIssue("invalid_expense_category", "CATEGORIA_DESPESA fora do MVP.", event_id=event_id))

    if event_type in {EventType.SALE_CASH.value, EventType.SALE_CREDIT.value}:
        cost = row["VL_CUSTO_CENTS"]
        if cost is None:
            issues.append(ValidationIssue("missing_sale_cost", "Venda deve informar VL_CUSTO_CENTS.", event_id=event_id))
        elif cost <= 0:
            issues.append(ValidationIssue("non_positive_sale_cost", "VL_CUSTO_CENTS deve ser > 0 para vendas no MVP.", event_id=event_id))
        elif cost > row["VL_EVENTO_CENTS"]:
            issues.append(ValidationIssue("sale_cost_exceeds_amount", "VL_CUSTO_CENTS não pode exceder VL_EVENTO_CENTS no MVP.", event_id=event_id))

    return tuple(issues)


def _sort_events(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["DT_EVENTO", "ID_EVENTO"], kind="mergesort").reset_index(drop=True)


def _clean_required_string(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _clean_optional_string(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def _parse_int(value: object) -> int:
    if isinstance(value, bool) or isinstance(value, float):
        raise SchemaValidationError("Valores em centavos devem ser inteiros, sem float.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(f"Valor inteiro inválido: {value!r}.") from exc


def _parse_optional_int(value: object) -> int | None:
    if pd.isna(value):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return _parse_int(value)
