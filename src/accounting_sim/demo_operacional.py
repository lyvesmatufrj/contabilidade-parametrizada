"""Adaptador da Demo Operacional Excel ↔ Python da Spec 13.

Este módulo NÃO implementa lógica tributária. Ele:
1. lê/valida os CSVs simples exportados pelo Excel;
2. converte-os para os objetos canônicos do projeto;
3. reutiliza o motor congelado da Spec 12;
4. produz estruturas de saída para o frontend.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

from accounting_sim.canonical import (
    ENTITY_PROFILE_COLUMNS,
    EVENT_COLUMNS,
    FISCAL_EVENT_ATTRIBUTE_COLUMNS,
    TAX_ANALYSIS_PARAMETER_COLUMNS,
    TAX_PARAMETER_COLUMNS,
    TAX_SCENARIO_COLUMNS,
    EventType,
    SchemaValidationError,
)
from accounting_sim.tax_context import TaxContext
from accounting_sim.tax_simples_2027 import (
    SIMPLES_2027_RULE_SPEC_VERSION,
    Simples2027CounterfactualReport,
    run_simples_2027_counterfactual_report,
)


DEMO_INTERFACE_VERSION = "spec_13_demo_operacional_v0_1"
DEMO_ENGINE_VERSION = f"{DEMO_INTERFACE_VERSION}|{SIMPLES_2027_RULE_SPEC_VERSION}"

ENTITY_INPUT_COLUMNS = ("CHAVE", "VALOR")
OPERATIONS_INPUT_COLUMNS = (
    "ID_OPERACAO",
    "DATA",
    "TIPO_OPERACAO",
    "VALOR",
    "REGIME_CONTRAPARTE",
    "OBSERVACAO",
)
ANALYSIS_INPUT_COLUMNS = ("CHAVE_PARAM", "VALOR")
RUN_REQUEST_COLUMNS = ("RUN_ID", "INTERFACE_VERSION")

SUPPORTED_OPERATION_TYPES = frozenset(
    {"compra_revenda", "venda_b2b", "venda_b2c"}
)

EXPECTED_COUNTERPART_REGIME = {
    "compra_revenda": "ibs_cbs_regime_regular",
    "venda_b2b": "ibs_cbs_regime_regular",
    "venda_b2c": "consumidor_final",
}

REQUIRED_ANALYSIS_KEYS = frozenset(
    {
        "CBS_2027_ANALYSIS_RATE_FRACTION",
        "REGULAR_CREDIT_REALIZATION_FRACTION",
    }
)

ENTITY_ID = "ENT_SIMPL_2027"
BASE_SCENARIO_ID = "SIMPLES_2027_PURO"
ALT_SCENARIO_ID = "SIMPLES_2027_HIBRIDO"

MEMORY_COLUMNS = (
    "SECAO",
    "CHAVE",
    "VALOR",
    "UNIDADE",
    "STATUS",
    "FONTE",
)


class DemoOperationalError(Exception):
    """Erro-base da camada operacional da Spec 13."""


class DemoInputError(DemoOperationalError):
    """Entrada exportada pelo Excel inválida."""


class DemoConfigurationError(DemoOperationalError):
    """Ambiente/repositório sem recurso necessário para a demo."""


@dataclass(frozen=True)
class DemoOperationalInputs:
    run_id: str
    entity_input: pd.DataFrame
    operations_input: pd.DataFrame
    analysis_input: pd.DataFrame


@dataclass(frozen=True)
class DemoCanonicalObjects:
    events: pd.DataFrame
    entity_profile: pd.DataFrame
    fiscal_event_attributes: pd.DataFrame
    tax_scenarios: pd.DataFrame
    tax_parameters: pd.DataFrame
    analysis_parameters: pd.DataFrame

    @property
    def tax_context(self) -> TaxContext:
        return TaxContext(
            entity_profile=self.entity_profile,
            fiscal_event_attributes=self.fiscal_event_attributes,
            tax_scenarios=self.tax_scenarios,
            tax_parameters=self.tax_parameters,
        )


@dataclass(frozen=True)
class DemoRunResult:
    run_id: str
    report: Simples2027CounterfactualReport
    memory_results: pd.DataFrame


def project_root() -> Path:
    """Retorna a raiz do repositório a partir de src/accounting_sim/."""
    return Path(__file__).resolve().parents[2]


def fixture_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "examples" / "simples_2027"


def load_demo_inputs(input_dir: str | Path) -> DemoOperationalInputs:
    """Lê e valida os quatro arquivos de entrada da Spec 13."""
    base = Path(input_dir)

    entity = _read_required_csv(base / "entity_input.csv", ENTITY_INPUT_COLUMNS)
    operations = _read_required_csv(
        base / "operations_input.csv", OPERATIONS_INPUT_COLUMNS
    )
    analysis = _read_required_csv(
        base / "analysis_input.csv", ANALYSIS_INPUT_COLUMNS
    )
    request = _read_required_csv(
        base / "run_request.csv", RUN_REQUEST_COLUMNS
    )

    if len(request) != 1:
        raise DemoInputError("run_request.csv deve conter exatamente uma linha.")

    run_id = _clean(request.iloc[0]["RUN_ID"])
    interface_version = _clean(request.iloc[0]["INTERFACE_VERSION"])

    if not run_id:
        raise DemoInputError("RUN_ID não pode ser vazio.")
    if interface_version != DEMO_INTERFACE_VERSION:
        raise DemoInputError(
            "INTERFACE_VERSION incompatível. "
            f"Esperado={DEMO_INTERFACE_VERSION!r}; recebido={interface_version!r}."
        )

    _validate_entity_input(entity)
    _validate_operations_input(operations)
    _validate_analysis_input(analysis)

    return DemoOperationalInputs(
        run_id=run_id,
        entity_input=entity,
        operations_input=operations,
        analysis_input=analysis,
    )


def build_demo_entity(
    inputs: DemoOperationalInputs,
    *,
    root: Path | None = None,
) -> pd.DataFrame:
    """Reutiliza o perfil-base da Spec 12 e substitui apenas o RBT12 informado."""
    profile = _load_fixture_csv("entity_profile.csv", ENTITY_PROFILE_COLUMNS, root=root)

    rbt12_reais = _require_decimal(
        _value_from_key_table(inputs.entity_input, "CHAVE", "VALOR", "RBT12"),
        "RBT12",
    )
    rbt12_cents = _money_to_cents(rbt12_reais)

    mask = (
        (profile["ID_ENTIDADE"].astype(str) == ENTITY_ID)
        & (profile["ATRIBUTO"].astype(str) == "RBT12_CENTS")
    )
    if int(mask.sum()) != 1:
        raise DemoConfigurationError(
            "Fixture ENTIDADE deve conter exatamente um RBT12_CENTS para ENT_SIMPL_2027."
        )

    profile.loc[mask, "VALOR"] = str(rbt12_cents)
    profile.loc[mask, "TIPO_VALOR"] = "int"
    profile.loc[mask, "ORIGEM"] = "observada"

    return profile.loc[:, list(ENTITY_PROFILE_COLUMNS)].copy()


def build_demo_events(inputs: DemoOperationalInputs) -> pd.DataFrame:
    """Converte a tabela operacional do Excel em EVENTOS canônicos."""
    rows: list[dict[str, object]] = []

    for _, op in inputs.operations_input.iterrows():
        op_id = _clean(op["ID_OPERACAO"])
        op_type = _clean(op["TIPO_OPERACAO"])
        event_id = f"D13_{op_id}"
        event_date = _require_iso_date(_clean(op["DATA"]), f"{op_id}.DATA")
        value_cents = _money_to_cents(
            _require_decimal(op["VALOR"], f"{op_id}.VALOR")
        )
        observation = _clean(op["OBSERVACAO"])

        if op_type == "compra_revenda":
            event_type = EventType.PURCHASE_CASH.value
            direction = "in"
            payment_term = "vista"
            financial_medium = "caixa"
            partner = f"FORN_{op_id}"
        elif op_type == "venda_b2b":
            event_type = EventType.SALE_CREDIT.value
            direction = "out"
            payment_term = "prazo"
            financial_medium = None
            partner = f"CLI_B2B_{op_id}"
        elif op_type == "venda_b2c":
            event_type = EventType.SALE_CASH.value
            direction = "out"
            payment_term = "vista"
            financial_medium = "caixa"
            partner = f"CLI_B2C_{op_id}"
        else:  # defesa redundante após validação
            raise DemoInputError(f"TIPO_OPERACAO não suportado: {op_type!r}.")

        rows.append(
            {
                "ID_EVENTO": event_id,
                "DT_EVENTO": event_date,
                "CLASSE_EVENTO": "TR",
                "TIPO_EVENTO": event_type,
                "DIRECAO": direction,
                "NATUREZA": "bem",
                "VL_EVENTO_CENTS": value_cents,
                "VL_CUSTO_CENTS": None,
                "MEIO_FINANCEIRO": financial_medium,
                "CATEGORIA_DESPESA": None,
                "COD_PART": partner,
                "COND_PAGTO": payment_term,
                "DOC_REF": f"DEMO13-{op_id}",
                "HIST": observation or op_type,
                "ORIGEM": "observada",
                "SPEC_VERSION": DEMO_INTERFACE_VERSION,
            }
        )

    return pd.DataFrame(rows, columns=EVENT_COLUMNS, dtype=object)


def build_demo_fiscal_attributes(
    inputs: DemoOperationalInputs,
) -> pd.DataFrame:
    """Converte a classificação operacional em EVENTOS_FISCAIS factuais."""
    rows: list[dict[str, object]] = []

    def add(event_id: str, attribute: str, value: str) -> None:
        rows.append(
            {
                "ID_EVENTO": event_id,
                "ATRIBUTO_FISCAL": attribute,
                "VALOR": value,
                "TIPO_VALOR": "str",
                "ORIGEM": "observada",
            }
        )

    for _, op in inputs.operations_input.iterrows():
        op_id = _clean(op["ID_OPERACAO"])
        op_type = _clean(op["TIPO_OPERACAO"])
        counterpart = _clean(op["REGIME_CONTRAPARTE"])
        event_id = f"D13_{op_id}"

        add(event_id, "AMBITO_OPERACAO", "domestica")

        if op_type == "compra_revenda":
            add(event_id, "REGIME_FORNECEDOR", counterpart)
            add(event_id, "DESTINACAO_AQUISICAO", "revenda")
        elif op_type == "venda_b2b":
            add(event_id, "TIPO_CLIENTE", "b2b")
            add(event_id, "REGIME_ADQUIRENTE", counterpart)
        elif op_type == "venda_b2c":
            add(event_id, "TIPO_CLIENTE", "b2c")
            add(event_id, "REGIME_ADQUIRENTE", counterpart)

    return pd.DataFrame(
        rows,
        columns=FISCAL_EVENT_ATTRIBUTE_COLUMNS,
        dtype=object,
    )


def build_demo_analysis_parameters(
    inputs: DemoOperationalInputs,
) -> pd.DataFrame:
    values = {
        _clean(row["CHAVE_PARAM"]): _clean(row["VALOR"])
        for _, row in inputs.analysis_input.iterrows()
    }

    descriptions = {
        "CBS_2027_ANALYSIS_RATE_FRACTION": (
            "Hipótese analítica informada na Demo Operacional; "
            "não representa alíquota oficial da CBS 2027."
        ),
        "REGULAR_CREDIT_REALIZATION_FRACTION": (
            "Hipótese analítica de realização dos créditos elegíveis no período."
        ),
    }

    rows = [
        {
            "ID_ANALISE": inputs.run_id,
            "CHAVE_PARAM": key,
            "VALOR": values[key],
            "TIPO_VALOR": "decimal",
            "DESCRICAO": descriptions[key],
        }
        for key in (
            "CBS_2027_ANALYSIS_RATE_FRACTION",
            "REGULAR_CREDIT_REALIZATION_FRACTION",
        )
    ]
    return pd.DataFrame(
        rows,
        columns=TAX_ANALYSIS_PARAMETER_COLUMNS,
        dtype=object,
    )


def build_demo_tax_context(
    inputs: DemoOperationalInputs,
    *,
    root: Path | None = None,
) -> TaxContext:
    return TaxContext(
        entity_profile=build_demo_entity(inputs, root=root),
        fiscal_event_attributes=build_demo_fiscal_attributes(inputs),
        tax_scenarios=_load_fixture_csv(
            "tax_scenarios.csv", TAX_SCENARIO_COLUMNS, root=root
        ),
        tax_parameters=_load_fixture_csv(
            "tax_parameters.csv", TAX_PARAMETER_COLUMNS, root=root
        ),
    )


def build_demo_canonical_objects(
    inputs: DemoOperationalInputs,
    *,
    root: Path | None = None,
) -> DemoCanonicalObjects:
    events = build_demo_events(inputs)
    entity = build_demo_entity(inputs, root=root)
    fiscal = build_demo_fiscal_attributes(inputs)
    scenarios = _load_fixture_csv(
        "tax_scenarios.csv", TAX_SCENARIO_COLUMNS, root=root
    )
    parameters = _load_fixture_csv(
        "tax_parameters.csv", TAX_PARAMETER_COLUMNS, root=root
    )
    analysis = build_demo_analysis_parameters(inputs)

    return DemoCanonicalObjects(
        events=events,
        entity_profile=entity,
        fiscal_event_attributes=fiscal,
        tax_scenarios=scenarios,
        tax_parameters=parameters,
        analysis_parameters=analysis,
    )


def run_demo(
    input_dir: str | Path,
    *,
    root: Path | None = None,
) -> DemoRunResult:
    """Executa a Demo 0.1 reutilizando integralmente o motor da Spec 12."""
    inputs = load_demo_inputs(input_dir)
    canonical = build_demo_canonical_objects(inputs, root=root)

    report = run_simples_2027_counterfactual_report(
        canonical.events,
        canonical.tax_context,
        canonical.analysis_parameters,
    )
    memory = build_memory_results(inputs, report, canonical.tax_parameters)

    return DemoRunResult(
        run_id=inputs.run_id,
        report=report,
        memory_results=memory,
    )


def build_memory_results(
    inputs: DemoOperationalInputs,
    report: Simples2027CounterfactualReport,
    tax_parameters: pd.DataFrame,
) -> pd.DataFrame:
    """Monta memória legível sem recalcular a tributação."""
    results = report.scenario_results
    comparison = report.comparison_results

    puro = results.loc[results["ID_CENARIO"] == BASE_SCENARIO_ID].iloc[0]
    hibrido = results.loc[results["ID_CENARIO"] == ALT_SCENARIO_ID].iloc[0]
    delta_encargo = comparison.loc[
        comparison["METRICA"] == "ENCARGO_TRIBUTARIO_COMPARAVEL",
        "DELTA_CENTS",
    ].iloc[0]

    analysis_values = {
        _clean(row["CHAVE_PARAM"]): _clean(row["VALOR"])
        for _, row in inputs.analysis_input.iterrows()
    }

    operations = inputs.operations_input.copy()
    operations["VALOR_DECIMAL"] = operations["VALOR"].map(
        lambda value: _require_decimal(value, "VALOR")
    )

    purchases = sum(
        operations.loc[
            operations["TIPO_OPERACAO"] == "compra_revenda", "VALOR_DECIMAL"
        ],
        Decimal(0),
    )
    b2b = sum(
        operations.loc[
            operations["TIPO_OPERACAO"] == "venda_b2b", "VALOR_DECIMAL"
        ],
        Decimal(0),
    )
    b2c = sum(
        operations.loc[
            operations["TIPO_OPERACAO"] == "venda_b2c", "VALOR_DECIMAL"
        ],
        Decimal(0),
    )

    rbt12 = _require_decimal(
        _value_from_key_table(inputs.entity_input, "CHAVE", "VALOR", "RBT12"),
        "RBT12",
    )

    ibs_source = _parameter_source(
        tax_parameters, "IBS_2027_REGULAR_RATE_FRACTION"
    )

    rows = [
        _memory_row("FATO", "RBT12", rbt12, "BRL", "fato", "INPUT_EXCEL"),
        _memory_row(
            "FATO", "COMPRAS_ELEGIVEIS", purchases, "BRL", "fato", "OPERACOES"
        ),
        _memory_row("FATO", "VENDAS_B2B", b2b, "BRL", "fato", "OPERACOES"),
        _memory_row("FATO", "VENDAS_B2C", b2c, "BRL", "fato", "OPERACOES"),
        _memory_row(
            "HIPOTESE",
            "CBS_2027_ANALYSIS_RATE_FRACTION",
            Decimal(analysis_values["CBS_2027_ANALYSIS_RATE_FRACTION"]),
            "fraction",
            "hipotese_analitica",
            "ANALISE_PARAM",
        ),
        _memory_row(
            "HIPOTESE",
            "REGULAR_CREDIT_REALIZATION_FRACTION",
            Decimal(analysis_values["REGULAR_CREDIT_REALIZATION_FRACTION"]),
            "fraction",
            "hipotese_analitica",
            "ANALISE_PARAM",
        ),
        _memory_row(
            "NORMA",
            "IBS_2027_REGULAR_RATE_FRACTION",
            hibrido["IBS_REGULAR_RATE_FRACTION"],
            "fraction",
            "normativo",
            ibs_source,
        ),
        _memory_row(
            "RESULTADO",
            "ALIQUOTA_EFETIVA_SIMPLES",
            puro["ALIQUOTA_EFETIVA_SIMPLES"],
            "fraction",
            "derivado",
            "ENGINE_SPEC_12",
        ),
        _memory_row(
            "RESULTADO",
            "ENCARGO_PURO",
            _cents_to_money(puro["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"]),
            "BRL",
            "derivado",
            "ENGINE_SPEC_12",
        ),
        _memory_row(
            "RESULTADO",
            "ENCARGO_HIBRIDO",
            _cents_to_money(hibrido["ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"]),
            "BRL",
            "derivado",
            "ENGINE_SPEC_12",
        ),
        _memory_row(
            "RESULTADO",
            "DELTA_ENCARGO",
            _cents_to_money(delta_encargo),
            "BRL",
            "derivado",
            "ENGINE_SPEC_12",
        ),
        _memory_row(
            "RESULTADO",
            "CBS_BREAK_EVEN",
            report.cbs_break_even_rate_fraction,
            "fraction",
            "derivado_analitico",
            "ENGINE_SPEC_12",
        ),
        _memory_row(
            "RESULTADO",
            "CBS_RATE_SOURCE",
            report.cbs_rate_source,
            "text",
            "derivado",
            "ENGINE_SPEC_12",
        ),
    ]

    return pd.DataFrame(rows, columns=MEMORY_COLUMNS, dtype=object)


def _validate_entity_input(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise DemoInputError("entity_input.csv não pode ser vazio.")
    if frame["CHAVE"].duplicated().any():
        raise DemoInputError("entity_input.csv possui CHAVE duplicada.")

    value = _value_from_key_table(frame, "CHAVE", "VALOR", "RBT12")
    rbt12 = _require_decimal(value, "RBT12")
    if rbt12 <= 0:
        raise DemoInputError("RBT12 deve ser maior que zero.")


def _validate_operations_input(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise DemoInputError("operations_input.csv deve conter operações.")

    ids = frame["ID_OPERACAO"].map(_clean)
    if (ids == "").any():
        raise DemoInputError("ID_OPERACAO não pode ser vazio.")
    if ids.duplicated().any():
        raise DemoInputError("ID_OPERACAO deve ser único.")

    present_types: set[str] = set()

    for _, row in frame.iterrows():
        op_id = _clean(row["ID_OPERACAO"])
        op_type = _clean(row["TIPO_OPERACAO"])
        counterpart = _clean(row["REGIME_CONTRAPARTE"])

        if op_type not in SUPPORTED_OPERATION_TYPES:
            raise DemoInputError(
                f"{op_id}: TIPO_OPERACAO não suportado: {op_type!r}."
            )

        _require_iso_date(_clean(row["DATA"]), f"{op_id}.DATA")

        value = _require_decimal(row["VALOR"], f"{op_id}.VALOR")
        if value <= 0:
            raise DemoInputError(f"{op_id}: VALOR deve ser maior que zero.")

        expected = EXPECTED_COUNTERPART_REGIME[op_type]
        if counterpart != expected:
            raise DemoInputError(
                f"{op_id}: REGIME_CONTRAPARTE incompatível com {op_type}. "
                f"Esperado={expected!r}; recebido={counterpart!r}."
            )

        present_types.add(op_type)

    missing = SUPPORTED_OPERATION_TYPES - present_types
    if missing:
        raise DemoInputError(
            "O recorte demonstrativo da Spec 12 requer ao menos uma operação "
            f"de cada tipo. Ausentes: {sorted(missing)}."
        )


def _validate_analysis_input(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise DemoInputError("analysis_input.csv não pode ser vazio.")

    keys = frame["CHAVE_PARAM"].map(_clean)
    if keys.duplicated().any():
        raise DemoInputError("analysis_input.csv possui CHAVE_PARAM duplicada.")

    missing = REQUIRED_ANALYSIS_KEYS - set(keys)
    if missing:
        raise DemoInputError(
            f"Hipóteses analíticas obrigatórias ausentes: {sorted(missing)}."
        )

    cbs = _require_decimal(
        _value_from_key_table(
            frame,
            "CHAVE_PARAM",
            "VALOR",
            "CBS_2027_ANALYSIS_RATE_FRACTION",
        ),
        "CBS_2027_ANALYSIS_RATE_FRACTION",
    )
    if not (Decimal(0) < cbs < Decimal(1)):
        raise DemoInputError(
            "CBS_2027_ANALYSIS_RATE_FRACTION deve pertencer a (0,1)."
        )

    alpha = _require_decimal(
        _value_from_key_table(
            frame,
            "CHAVE_PARAM",
            "VALOR",
            "REGULAR_CREDIT_REALIZATION_FRACTION",
        ),
        "REGULAR_CREDIT_REALIZATION_FRACTION",
    )
    if not (Decimal(0) <= alpha <= Decimal(1)):
        raise DemoInputError(
            "REGULAR_CREDIT_REALIZATION_FRACTION deve pertencer a [0,1]."
        )


def _read_required_csv(path: Path, expected_columns: tuple[str, ...]) -> pd.DataFrame:
    if not path.exists():
        raise DemoInputError(f"Arquivo de entrada ausente: {path.name}.")

    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception as exc:
        raise DemoInputError(f"Falha ao ler {path.name}: {exc}") from exc

    actual = tuple(frame.columns)
    if actual != expected_columns:
        raise DemoInputError(
            f"Schema inválido em {path.name}. "
            f"Esperado={expected_columns}; recebido={actual}."
        )

    return frame.loc[:, list(expected_columns)].copy()


def _load_fixture_csv(
    filename: str,
    expected_columns: tuple[str, ...],
    *,
    root: Path | None = None,
) -> pd.DataFrame:
    path = fixture_dir(root) / filename
    if not path.exists():
        raise DemoConfigurationError(f"Fixture do repositório ausente: {path}.")

    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception as exc:
        raise DemoConfigurationError(f"Falha ao ler fixture {path}: {exc}") from exc

    missing = [col for col in expected_columns if col not in frame.columns]
    if missing:
        raise DemoConfigurationError(
            f"Fixture {filename} sem colunas obrigatórias: {missing}."
        )

    return frame.loc[:, list(expected_columns)].copy()


def _value_from_key_table(
    frame: pd.DataFrame,
    key_column: str,
    value_column: str,
    key: str,
) -> str:
    selected = frame.loc[frame[key_column].map(_clean) == key, value_column]
    if len(selected) != 1:
        raise DemoInputError(
            f"{key_column}={key!r} deve aparecer exatamente uma vez."
        )
    return _clean(selected.iloc[0])


def _require_decimal(value: object, field_name: str) -> Decimal:
    text = _clean(value).replace(",", ".")
    try:
        result = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise DemoInputError(f"{field_name} deve ser decimal válido.") from exc
    if not result.is_finite():
        raise DemoInputError(f"{field_name} deve ser decimal finito.")
    return result


def _money_to_cents(value: Decimal) -> int:
    return int(
        (value * Decimal(100)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    )


def _cents_to_money(value: object) -> Decimal:
    if value is None or pd.isna(value):
        return Decimal(0)
    return (Decimal(str(value)) / Decimal(100)).quantize(Decimal("0.01"))


def _require_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DemoInputError(
            f"{field_name} deve usar formato ISO YYYY-MM-DD."
        ) from exc


def _clean(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _memory_row(
    section: str,
    key: str,
    value: object,
    unit: str,
    status: str,
    source: str,
) -> dict[str, object]:
    if isinstance(value, Decimal):
        serialized = format(value, "f")
    elif value is None or pd.isna(value):
        serialized = ""
    else:
        serialized = str(value)

    return {
        "SECAO": section,
        "CHAVE": key,
        "VALOR": serialized,
        "UNIDADE": unit,
        "STATUS": status,
        "FONTE": source,
    }


def _parameter_source(tax_parameters: pd.DataFrame, key: str) -> str:
    selected = tax_parameters.loc[
        tax_parameters["CHAVE_PARAM"].astype(str).str.strip() == key
    ]
    if len(selected) != 1:
        return "FISCAL_PARAM"

    row = selected.iloc[0]
    title = _clean(row.get("FONTE_TITULO"))
    device = _clean(row.get("DISPOSITIVO"))
    if title and device:
        return f"{title} | {device}"
    return title or device or "FISCAL_PARAM"
