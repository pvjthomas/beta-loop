"""Offline tests for Gen5 endpoint PDF parsing."""

from __future__ import annotations

import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILLS_DIR.parent.parent
sys.path.insert(0, str(SKILLS_DIR))

from gen5_pdf import parse_gen5_endpoint_pdf  # noqa: E402

SAMPLE_PDFS = [
    REPO_ROOT / "skill_platereader_measure_20260724_231705.pdf",
    REPO_ROOT
    / "mastermix/data/platereader/skill_platereader_measure_20260725_173839/skill_platereader_measure_20260725_173839.pdf",
    REPO_ROOT
    / "mastermix/data/platereader/skill_platereader_measure_20260725_174147/skill_platereader_measure_20260725_174147.pdf",
]

# Populated plate (7/25 17:41) — high 450 nm signal at B7–B9.
SPOT_CHECK_WELL = Path(SAMPLE_PDFS[2])
SPOT_CHECK = {
    "B7": {450: 0.610, 490: 0.038, 630: 0.042},
    "B8": {450: 0.560, 490: 0.038, 630: 0.044},
    "B9": {450: 0.520, 490: 0.039, 630: 0.039},
}


def _assert_close(actual: float, expected: float, tol: float = 0.001) -> None:
    if abs(actual - expected) > tol:
        raise AssertionError(f"expected {expected}, got {actual}")


def test_all_sample_pdfs() -> None:
    for pdf_path in SAMPLE_PDFS:
        if not pdf_path.exists():
            raise FileNotFoundError(f"Sample PDF missing: {pdf_path}")
        parsed = parse_gen5_endpoint_pdf(pdf_path)
        wells = parsed["wells"]
        assert len(wells) == 96, f"{pdf_path.name}: expected 96 wells, got {len(wells)}"
        for well, wl_map in wells.items():
            assert len(wl_map) == 3, f"{well}: expected 3 wavelengths, got {wl_map}"
        meta = parsed["metadata"]
        assert meta.get("reader_type") == "ELx808", meta
        assert meta.get("wavelengths_nm") == [450, 490, 630], meta
        print(f"OK  {pdf_path.name} — {len(wells)} wells, temp={meta.get('temperature_c')} °C")


def test_spot_check_high_absorbance() -> None:
    parsed = parse_gen5_endpoint_pdf(SPOT_CHECK_WELL)
    for well, expected_wls in SPOT_CHECK.items():
        for wl, expected in expected_wls.items():
            actual = parsed["wells"][well][wl]
            _assert_close(actual, expected)
    print(f"OK  spot check on {SPOT_CHECK_WELL.name}")


def test_empty_plate_near_zero() -> None:
    parsed = parse_gen5_endpoint_pdf(SAMPLE_PDFS[0])
    for well in ("A1", "A2", "H12"):
        for wl in (450, 490, 630):
            assert parsed["wells"][well][wl] == 0.0, (
                f"{well}@{wl}nm expected 0.0, got {parsed['wells'][well][wl]}"
            )
    print(f"OK  empty plate {SAMPLE_PDFS[0].name}")


if __name__ == "__main__":
    test_all_sample_pdfs()
    test_spot_check_high_absorbance()
    test_empty_plate_near_zero()
    print("All Gen5 PDF parser tests passed.")
