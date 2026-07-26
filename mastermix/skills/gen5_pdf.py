"""Parse Gen5 endpoint absorbance PDF exports from BioTek ELx808 plate readers."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from pypdf import PdfReader

ROWS = "ABCDEFGH"
COLS = range(1, 13)
WAVELENGTHS_NM = (450, 490, 630)
WELLS_PER_PLATE = 96
VALUES_PER_PLATE = WELLS_PER_PLATE * len(WAVELENGTHS_NM)


def _extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_metadata(text: str) -> dict:
    meta: dict = {}

    if m := re.search(r"Software Version\s+([\d.]+)", text):
        meta["software_version"] = m.group(1)
    if m := re.search(r"Protocol File Path:\s*(.+)", text):
        meta["protocol_path"] = m.group(1).strip()
    if m := re.search(r"Experiment File Path:\s*(.+)", text):
        meta["experiment_path"] = m.group(1).strip()
    if m := re.search(r"Plate Number\s+(.+)", text):
        meta["plate_number"] = m.group(1).strip()
    if m := re.search(r"Date\s+(.+)", text):
        meta["date"] = m.group(1).strip()
    if m := re.search(r"Time\s+(.+)", text):
        meta["time"] = m.group(1).strip()
    if m := re.search(r"Reader Type:\s*(.+)", text):
        meta["reader_type"] = m.group(1).strip()
    if m := re.search(r"Read\s+(.+)", text):
        meta["read_type"] = m.group(1).strip()
    if m := re.search(r"Wavelengths:\s*([\d,\s]+)", text):
        meta["wavelengths_nm"] = [int(w.strip()) for w in m.group(1).split(",") if w.strip()]
    if m := re.search(r"Actual Temperature:\s*([\d.]+)", text):
        meta["temperature_c"] = float(m.group(1))

    return meta


def _well_id(row: str, col: int) -> str:
    return f"{row}{col}"


def _parse_absorbance_values(text: str, wavelengths_nm: list[int]) -> dict[str, dict[int, float]]:
    results_idx = text.find("Results")
    if results_idx < 0:
        raise ValueError("Gen5 PDF missing 'Results' section")

    after_results = text[results_idx:]
    values = [float(v) for v in re.findall(r"\d+\.\d+", after_results)]
    if len(values) != VALUES_PER_PLATE:
        raise ValueError(
            f"Expected {VALUES_PER_PLATE} absorbance values, found {len(values)}"
        )

    wells: dict[str, dict[int, float]] = {}
    for wl_idx, wl in enumerate(wavelengths_nm):
        block = values[wl_idx * WELLS_PER_PLATE : (wl_idx + 1) * WELLS_PER_PLATE]
        for row_idx, row in enumerate(ROWS):
            row_vals = block[row_idx * 12 : (row_idx + 1) * 12]
            for col_idx, absorbance in enumerate(row_vals, start=1):
                well = _well_id(row, col_idx)
                wells.setdefault(well, {})[wl] = absorbance

    return wells


def parse_gen5_endpoint_pdf(pdf_path: str | Path) -> dict:
    """Parse a Gen5 endpoint PDF into metadata and per-well absorbance.

    Returns:
        dict with ``metadata`` and ``wells`` keys. Each well maps wavelength (nm)
        to absorbance, e.g. ``wells["A1"][450] == 0.040``.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Gen5 PDF not found: {path}")

    text = _extract_text(path)
    metadata = _parse_metadata(text)
    wavelengths_nm = metadata.get("wavelengths_nm") or list(WAVELENGTHS_NM)
    wells = _parse_absorbance_values(text, wavelengths_nm)

    return {"metadata": metadata, "wells": wells}


def wells_to_csv_rows(parsed: dict) -> list[dict[str, str | int | float]]:
    """Flatten parsed wells to CSV-ready rows."""
    rows: list[dict[str, str | int | float]] = []
    for well in sorted(parsed["wells"], key=_well_sort_key):
        for wl in sorted(parsed["wells"][well]):
            rows.append(
                {
                    "well": well,
                    "wavelength_nm": wl,
                    "absorbance": parsed["wells"][well][wl],
                }
            )
    return rows


def _well_sort_key(well: str) -> tuple[int, int]:
    row = well[0]
    col = int(well[1:])
    return (ROWS.index(row), col)


def write_absorbance_csv(parsed: dict, csv_path: str | Path) -> Path:
    """Write flattened absorbance rows to CSV."""
    path = Path(csv_path)
    rows = wells_to_csv_rows(parsed)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["well", "wavelength_nm", "absorbance"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def absorbance_csv_string(parsed: dict) -> str:
    """Return CSV content as a string."""
    buf = io.StringIO()
    rows = wells_to_csv_rows(parsed)
    writer = csv.DictWriter(buf, fieldnames=["well", "wavelength_nm", "absorbance"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
