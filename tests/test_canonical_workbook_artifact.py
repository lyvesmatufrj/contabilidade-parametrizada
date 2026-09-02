from decimal import Decimal

from scripts.build_canonical_workbook import build_canonical_workbook


def test_build_canonical_workbook_artifact_from_cbs_fixture(tmp_path):
    output_path = tmp_path / "contabilidade_parametrizada.xlsx"

    summary = build_canonical_workbook(output_path)

    assert output_path.exists()
    assert summary.path == output_path
    assert summary.sheet_count == 23
    assert summary.row_counts["EVENTOS"] == 3
    assert summary.row_counts["FISCAL_RESULTADOS_OPERACAO"] == 4
    assert summary.row_counts["FISCAL_APURACAO"] == 2
    assert summary.row_counts["COMPARATIVO_CENARIOS"] == 1
    assert Decimal(str(summary.baseline_assessment["S_APUR"])) == Decimal("9")
    assert Decimal(str(summary.baseline_assessment["T_RECOLHER"])) == Decimal("0")
    assert Decimal(str(summary.control_comparison["DELTA_S_APUR"])) == Decimal("0")
    assert Decimal(str(summary.control_comparison["DELTA_T_RECOLHER"])) == Decimal("0")
    assert summary.control_comparison["DELTA_P_CASH"] is None
    assert summary.control_comparison["DELTA_E_DRE"] is None
