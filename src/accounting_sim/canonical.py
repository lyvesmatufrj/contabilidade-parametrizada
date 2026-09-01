"""Vocabulário canônico e helpers primitivos do MVP contábil."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class DebitCredit(StrEnum):
    DEBIT = "D"
    CREDIT = "C"


class AccountType(StrEnum):
    SYNTHETIC = "S"
    ANALYTIC = "A"


class AccountNature(StrEnum):
    ASSET = "01"
    LIABILITY = "02"
    EQUITY = "03"
    RESULT = "04"
    COMPENSATION = "05"
    OTHER = "09"


class Origin(StrEnum):
    OBSERVED = "observada"
    SYNTHETIC = "sintética"
    TEMPLATE = "template"
    ADJUSTED = "ajustada"


class EventClass(StrEnum):
    TRANSACTION = "TR"
    ADJUSTMENT = "ADJ"


class EventDirection(StrEnum):
    IN = "in"
    OUT = "out"
    NA = "na"


class EventNature(StrEnum):
    GOOD = "bem"
    SERVICE = "servico"
    FINANCIAL = "financeiro"
    ADJUSTMENT = "ajuste"


class PaymentTerm(StrEnum):
    CASH = "vista"
    CREDIT = "prazo"
    NA = "na"


class EventType(StrEnum):
    CAPITAL_CONTRIBUTION = "aporte_capital"
    PURCHASE_CASH = "compra_mercadoria_a_vista"
    PURCHASE_CREDIT = "compra_mercadoria_a_prazo"
    SUPPLIER_PAYMENT = "pagamento_fornecedor"
    SALE_CASH = "venda_a_vista"
    SALE_CREDIT = "venda_a_prazo"
    CUSTOMER_RECEIPT = "recebimento_cliente"
    OPERATING_EXPENSE_CASH = "despesa_operacional_a_vista"
    DEPRECIATION = "depreciacao"


class JournalEntryType(StrEnum):
    NORMAL = "N"
    CLOSING = "E"
    EXTEMPORANEOUS = "X"


class AccountingSimError(Exception):
    """Erro-base do MVP contábil."""


class SchemaValidationError(AccountingSimError):
    """Erro de schema ou tipo tabular."""


class ReferentialIntegrityError(AccountingSimError):
    """Erro de chave ou relacionamento entre objetos."""


class AccountingInvariantError(AccountingSimError):
    """Erro de invariante contábil."""


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    account_code: str | None = None
    event_id: str | None = None
    entry_id: str | None = None
    posting_id: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    issues: tuple[ValidationIssue, ...]


CHART_OF_ACCOUNTS_COLUMNS: tuple[str, ...] = (
    "DT_ALT",
    "COD_NAT",
    "IND_CTA",
    "NIVEL",
    "COD_CTA",
    "COD_CTA_SUP",
    "CTA",
    "NAT_SALDO_NORMAL",
    "COD_DF",
    "ATIVA",
    "ORIGEM",
)

EVENT_COLUMNS: tuple[str, ...] = (
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

ACCOUNT_ROLE_MAPPING_COLUMNS: tuple[str, ...] = (
    "PAPEL_CONTABIL",
    "COD_CTA",
)

STATEMENT_MAPPING_COLUMNS: tuple[str, ...] = (
    "COD_CTA",
    "DEMONSTRACAO",
    "COD_LINHA",
)

JOURNAL_ENTRY_HEADER_COLUMNS: tuple[str, ...] = (
    "NUM_LCTO",
    "DT_LCTO",
    "VL_LCTO_CENTS",
    "IND_LCTO",
    "DT_LCTO_EXT",
    "ID_GERACAO",
    "VERSAO_REGRA",
)

POSTING_COLUMNS: tuple[str, ...] = (
    "ID_PARTIDA",
    "NUM_LCTO",
    "COD_CTA",
    "COD_CCUS",
    "VL_DC_CENTS",
    "IND_DC",
    "NUM_ARQ",
    "COD_HIST_PAD",
    "HIST",
    "COD_PART",
    "ID_ORIGEM",
)

EVENT_ENTRY_LINK_COLUMNS: tuple[str, ...] = (
    "ID_EVENTO",
    "NUM_LCTO",
    "ORDEM_LCTO_EVENTO",
)

JOURNAL_VIEW_COLUMNS: tuple[str, ...] = (
    "DT_LCTO",
    "NUM_LCTO",
    "ID_PARTIDA",
    "COD_CTA",
    "CTA",
    "IND_DC",
    "VL_DC_CENTS",
    "HIST",
    "COD_PART",
    "ID_ORIGEM",
)

LEDGER_VIEW_COLUMNS: tuple[str, ...] = (
    "COD_CTA",
    "CTA",
    "DT_LCTO",
    "NUM_LCTO",
    "ID_PARTIDA",
    "DEBITO_CENTS",
    "CREDITO_CENTS",
    "MOVIMENTO_ASSINADO_CENTS",
    "SALDO_ASSINADO_CENTS",
    "SALDO_ABS_CENTS",
    "IND_DC_SALDO",
    "HIST",
    "ID_ORIGEM",
)

TRIAL_BALANCE_COLUMNS: tuple[str, ...] = (
    "DT_INI",
    "DT_FIN",
    "COD_CTA",
    "COD_CCUS",
    "VL_SLD_INI_CENTS",
    "IND_DC_INI",
    "VL_DEB_CENTS",
    "VL_CRED_CENTS",
    "VL_SLD_FIN_CENTS",
    "IND_DC_FIN",
)

BALANCE_SHEET_COLUMNS: tuple[str, ...] = (
    "DT_REF",
    "ORDEM",
    "COD_LINHA",
    "NIVEL",
    "TIPO_LINHA",
    "LINHA",
    "VL_CENTS",
)

INCOME_STATEMENT_COLUMNS: tuple[str, ...] = (
    "DT_INI",
    "DT_FIN",
    "ORDEM",
    "COD_LINHA",
    "NIVEL",
    "TIPO_LINHA",
    "LINHA",
    "VL_CENTS",
)

ACCOUNT_NATURE_LABELS: Mapping[str, str] = MappingProxyType(
    {
        AccountNature.ASSET.value: "Ativo",
        AccountNature.LIABILITY.value: "Passivo",
        AccountNature.EQUITY.value: "Patrimônio Líquido",
        AccountNature.RESULT.value: "Contas de Resultado",
        AccountNature.COMPENSATION.value: "Contas de Compensação",
        AccountNature.OTHER.value: "Outras",
    }
)


@dataclass(frozen=True)
class AccountingPeriod:
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise SchemaValidationError("end_date deve ser maior ou igual a start_date.")


@dataclass(frozen=True)
class SimulationConfig:
    simulation_id: str
    start_date: date
    end_date: date
    currency: str
    seed: int
    scenario_name: str
    spec_version: str

    def __post_init__(self) -> None:
        if self.currency != "BRL":
            raise SchemaValidationError("currency deve ser BRL no MVP.")
        AccountingPeriod(self.start_date, self.end_date)


def parse_iso_date(value: str | date) -> date:
    """Converte data ISO 8601 para datetime.date, preservando date já válido."""

    if isinstance(value, datetime):
        raise TypeError("Use datetime.date, não datetime.datetime.")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise TypeError("Data deve ser string ISO 8601 ou datetime.date.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Data ISO inválida: {value!r}.") from exc


def amount_reais_to_cents(amount: str | int | Decimal) -> int:
    """Converte valor em BRL para centavos inteiros sem aceitar float."""

    if isinstance(amount, bool) or isinstance(amount, float):
        raise TypeError("Valores monetários não devem usar float como fonte de verdade.")

    try:
        decimal_amount = Decimal(amount)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Valor monetário inválido: {amount!r}.") from exc

    cents = decimal_amount * Decimal("100")
    if cents != cents.to_integral_value():
        raise ValueError("Valor monetário deve ter no máximo duas casas decimais.")
    return int(cents)
