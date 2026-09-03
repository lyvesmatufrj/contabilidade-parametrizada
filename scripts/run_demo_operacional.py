"""CLI da Demo Operacional da Spec 13.

Uso:
    python scripts/run_demo_operacional.py --input-dir <dir> --output-dir <dir>
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from accounting_sim.canonical import SchemaValidationError  # noqa: E402
from accounting_sim.demo_operacional import (  # noqa: E402
    DEMO_ENGINE_VERSION,
    DemoConfigurationError,
    DemoInputError,
    run_demo,
)


EXIT_SUCCESS = 0
EXIT_INPUT_ERROR = 2
EXIT_CONFIGURATION_ERROR = 3
EXIT_INTERNAL_ERROR = 4

RUN_STATUS_COLUMNS = (
    "RUN_ID",
    "OK",
    "STATUS_CODE",
    "MESSAGE",
    "ENGINE_SPEC_VERSION",
)


def execute(input_dir: str | Path, output_dir: str | Path) -> int:
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    run_id = _best_effort_run_id(input_path)

    try:
        result = run_demo(input_path, root=PROJECT_ROOT)
        run_id = result.run_id

        result.report.scenario_results.to_csv(
            output_path / "scenario_results.csv",
            index=False,
        )
        result.report.comparison_results.to_csv(
            output_path / "comparison_results.csv",
            index=False,
        )
        result.memory_results.to_csv(
            output_path / "memory_results.csv",
            index=False,
        )

        _write_status(
            output_path,
            run_id=run_id,
            ok=True,
            status_code=EXIT_SUCCESS,
            message="Simulação concluída com sucesso.",
        )
        return EXIT_SUCCESS

    except (DemoInputError, SchemaValidationError) as exc:
        _write_status(
            output_path,
            run_id=run_id,
            ok=False,
            status_code=EXIT_INPUT_ERROR,
            message=str(exc),
        )
        return EXIT_INPUT_ERROR

    except DemoConfigurationError as exc:
        _write_status(
            output_path,
            run_id=run_id,
            ok=False,
            status_code=EXIT_CONFIGURATION_ERROR,
            message=str(exc),
        )
        return EXIT_CONFIGURATION_ERROR

    except Exception as exc:  # proteção do boundary CLI
        _write_status(
            output_path,
            run_id=run_id,
            ok=False,
            status_code=EXIT_INTERNAL_ERROR,
            message=f"Erro interno inesperado: {type(exc).__name__}: {exc}",
        )
        return EXIT_INTERNAL_ERROR


def _write_status(
    output_dir: Path,
    *,
    run_id: str,
    ok: bool,
    status_code: int,
    message: str,
) -> None:
    frame = pd.DataFrame(
        [
            {
                "RUN_ID": run_id,
                "OK": bool(ok),
                "STATUS_CODE": int(status_code),
                "MESSAGE": message,
                "ENGINE_SPEC_VERSION": DEMO_ENGINE_VERSION,
            }
        ],
        columns=RUN_STATUS_COLUMNS,
    )
    frame.to_csv(output_dir / "run_status.csv", index=False)


def _best_effort_run_id(input_dir: Path) -> str:
    request = input_dir / "run_request.csv"
    if request.exists():
        try:
            frame = pd.read_csv(request, dtype=str, keep_default_na=False)
            if "RUN_ID" in frame.columns and len(frame) == 1:
                value = str(frame.iloc[0]["RUN_ID"]).strip()
                if value:
                    return value
        except Exception:
            pass
    return input_dir.name or "UNKNOWN_RUN"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa a Demo Operacional Simples 2027 da Spec 13."
    )
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return execute(args.input_dir, args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
