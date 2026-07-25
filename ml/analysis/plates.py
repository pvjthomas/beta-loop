"""Plate map helpers for Round 2 dose-response design."""

from __future__ import annotations

import json
from pathlib import Path

from analysis.kinetics import DOSE_RESPONSE_CONCENTRATIONS_UM

CONTROL_WELLS = {
    "A1": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
    "A2": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
    "A3": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
    "A4": {"compound_id": None, "concentration_uM": 0, "role": "no_tem1", "bucket": "control"},
    "A5": {"compound_id": None, "concentration_uM": 0, "role": "no_tem1", "bucket": "control"},
    "A6": {"compound_id": "T19860", "concentration_uM": 50, "role": "pos-ctrl-clavaculin", "bucket": "control"},
}


def design_dose_response_plate(
    hits: list[dict],
    *,
    round_number: int = 2,
    max_compounds: int = 3,
) -> dict:
    """Build an 8-point dose-response plate map for top R1 hits."""
    wells = dict(CONTROL_WELLS)
    row_labels = list("BCDEFGH")
    concentrations = DOSE_RESPONSE_CONCENTRATIONS_UM[:8]
    selected = hits[:max_compounds]

    for row_idx, hit in enumerate(selected):
        if row_idx >= len(row_labels):
            break
        row = row_labels[row_idx]
        compound_id = hit["compound_id"]
        for col_idx, conc in enumerate(concentrations, start=1):
            well = f"{row}{col_idx}"
            wells[well] = {
                "compound_id": compound_id,
                "concentration_uM": conc,
                "role": "sample",
                "bucket": "dose_response",
                "functional_class": "positive",
                "source_hit_pct_inhibition": hit.get("pct_inhibition"),
            }

    return {
        "round": round_number,
        "assay_type": "dose_response",
        "final_volume_ul": 50,
        "compound_concentration_uM": "variable",
        "layout_notes": (
            f"Dose-response on top {len(selected)} R1 hits; "
            f"8-point series {concentrations} µM (one compound per row)."
        ),
        "wells": wells,
    }


def write_plate_map(plate_map: dict, path: str | Path) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plate_map, indent=2) + "\n")
    return str(path)
