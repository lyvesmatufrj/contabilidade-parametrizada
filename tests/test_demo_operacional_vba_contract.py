from __future__ import annotations

from pathlib import Path
import re


VBA_DIR = Path(__file__).resolve().parents[1] / "vba" / "demo_operacional"
MODULES = (
    "modDemoMain.bas",
    "modDemoConfig.bas",
    "modDemoRuntime.bas",
    "modDemoCsv.bas",
    "modDemoPayload.bas",
    "modDemoResults.bas",
)


def _read_module(name: str) -> str:
    return (VBA_DIR / name).read_text(encoding="cp1252")


def test_expected_vba_modules_exist_with_option_explicit() -> None:
    for module in MODULES:
        path = VBA_DIR / module
        assert path.exists()
        text = _read_module(module)
        assert 'Attribute VB_Name = "' in text
        assert re.search(r"(?im)^Option Explicit$", text)


def test_only_main_exposes_public_simular_macro() -> None:
    for module in MODULES:
        matches = re.findall(r"(?im)^Public\s+Sub\s+Simular\s*\(", _read_module(module))
        if module == "modDemoMain.bas":
            assert len(matches) == 1
        else:
            assert not matches


def test_vba_has_no_local_paths_pywin32_or_ansi_output_writer() -> None:
    combined = "\n".join(_read_module(module) for module in MODULES)
    assert "pywin32" not in combined.lower()
    assert not re.search(r"[A-Za-z]:\\", combined)
    assert not re.search(r"(?is)\bOpen\b.+\bFor\s+Output\b", combined)


def test_csv_contract_is_utf8_bom_decimal_point_and_escaped() -> None:
    csv_module = _read_module("modDemoCsv.bas")
    assert "ADODB.Stream" in csv_module
    assert '.Charset = "utf-8"' in csv_module or 'Charset = "utf-8"' in csv_module
    assert "SaveToFile" in csv_module
    assert 'DecimalSeparator:="."' in csv_module
    assert 'Replace(text, quote, quote & quote)' in csv_module
    assert "vbCrLf" in csv_module


def test_named_range_access_is_qualified() -> None:
    combined = "\n".join(_read_module(module) for module in MODULES)
    assert not re.search(r'(?<![\.\w])Range\("inp', combined)
    assert "ThisWorkbook.Names(\"inpRBT12\").RefersToRange" in combined
    assert "ThisWorkbook.Names(\"inpCBS2027\").RefersToRange" in combined
    assert "ThisWorkbook.Names(\"inpCreditRealization\").RefersToRange" in combined


def test_vba_does_not_copy_tax_formula_constants() -> None:
    combined = "\n".join(_read_module(module) for module in MODULES)
    for forbidden in ("0.1533", "0.0017", "0.08825", "882500", "897213", "0.090191"):
        assert forbidden not in combined
    assert "SIMPLES_ANNEX" not in combined
    assert "REGULAR_CREDIT_REALIZATION_FRACTION = " not in combined
    assert "CBS_2027_ANALYSIS_RATE_FRACTION = " not in combined
