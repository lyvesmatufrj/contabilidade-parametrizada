"""Vocabulário canônico e helpers primitivos das specs 00-02."""

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


class AccountingSimError(Exception):
    """Erro-base do MVP contábil."""


class SchemaValidationError(AccountingSimError):
    """Erro de schema ou tipo tabular."""


class ReferentialIntegrityError(AccountingSimError):
    """Erro de chave ou relacionamento entre objetos."""


class AccountingInvariantError(AccountingSimError):
    """Erro de invariante contábil."""


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
