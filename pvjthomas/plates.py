"""Generate 96-well plate maps from compound_list.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROWS = list("ABCDEFGH")
COLS = 12

DEFAULT_CONTROL_ROW: dict[str, Any] = {
    "vehicle": 3,
    "no_tem1": 3,
    "positive": {"compound_id": "T19860", "count": 3, "concentration_uM": 50},
}


def well_id(row_idx: int, col_idx: int) -> str:
    """Return standard well label (e.g. B3) from 0-based row/col indices."""
    if not 0 <= row_idx < len(ROWS):
        raise ValueError(f"row_idx {row_idx} out of range (0–{len(ROWS) - 1})")
    if not 0 <= col_idx < COLS:
        raise ValueError(f"col_idx {col_idx} out of range (0–{COLS - 1})")
    return f"{ROWS[row_idx]}{col_idx + 1}"


def _vehicle_well() -> dict[str, Any]:
    return {
        "compound_id": None,
        "concentration_uM": 0,
        "role": "vehicle",
        "bucket": "control",
    }


def _no_tem1_well() -> dict[str, Any]:
    return {
        "compound_id": None,
        "concentration_uM": 0,
        "role": "no_tem1",
        "bucket": "control",
    }


def _positive_control_well(compound_id: str, concentration_uM: float) -> dict[str, Any]:
    return {
        "compound_id": compound_id,
        "concentration_uM": concentration_uM,
        "role": "pos-ctrl-clavaculin",
        "bucket": "control",
    }


def _sample_well(compound: dict[str, Any], replicate: int) -> dict[str, Any]:
    well: dict[str, Any] = {
        "compound_id": compound["compound_id"],
        "concentration_uM": compound.get("screen_conc_uM", 50),
        "role": "sample",
        "bucket": compound.get("bucket", "sample"),
        "replicate": replicate,
    }
    if functional_class := compound.get("functional_class"):
        well["functional_class"] = functional_class
    return well


def add_control_row(
    wells: dict[str, dict[str, Any]],
    *,
    control_row: dict[str, Any] | None = None,
    row_idx: int = 0,
) -> None:
    """Fill row A (by default) with vehicle, no-enzyme, and positive controls."""
    cfg = control_row if control_row is not None else DEFAULT_CONTROL_ROW
    col = 0

    for _ in range(int(cfg.get("vehicle", 0))):
        wells[well_id(row_idx, col)] = _vehicle_well()
        col += 1

    for _ in range(int(cfg.get("no_tem1", 0))):
        wells[well_id(row_idx, col)] = _no_tem1_well()
        col += 1

    positive = cfg.get("positive") or {}
    pos_count = int(positive.get("count", 0))
    pos_id = positive.get("compound_id", "T19860")
    pos_conc = float(positive.get("concentration_uM", 50))
    for _ in range(pos_count):
        wells[well_id(row_idx, col)] = _positive_control_well(pos_id, pos_conc)
        col += 1


def add_compound_block(
    wells: dict[str, dict[str, Any]],
    compounds: list[dict[str, Any]],
    *,
    replicates: int = 3,
    start_row: int = 1,
    start_col: int = 0,
) -> None:
    """Place compounds left-to-right, top-to-bottom; three replicates per compound."""
    idx = 0
    for compound in compounds:
        for rep in range(1, replicates + 1):
            linear = start_col + idx
            row = start_row + linear // COLS
            col = linear % COLS
            wells[well_id(row, col)] = _sample_well(compound, rep)
            idx += 1


def _variable_concentration_note(
    compounds: list[dict[str, Any]],
    *,
    default_uM: float = 50,
) -> str:
    """Append note when compounds use different screen concentrations."""
    non_default = [
        f"{c['compound_id']} @ {c['screen_conc_uM']} µM"
        + (f" (rule {c['concentration_rule']})" if c.get("concentration_rule") else "")
        for c in compounds
        if c.get("screen_conc_uM", default_uM) != default_uM
    ]
    if not non_default:
        return ""
    return (
        ". "
        + "; ".join(non_default)
        + f"; all others @ {default_uM} µM unless noted in compound_list.json"
    )


def _layout_notes(
    compounds: list[dict[str, Any]],
    *,
    replicates: int,
    control_row: dict[str, Any],
    default_uM: float = 50,
) -> str:
    vehicle = int(control_row.get("vehicle", 0))
    no_tem1 = int(control_row.get("no_tem1", 0))
    positive = control_row.get("positive") or {}
    pos_count = int(positive.get("count", 0))
    control_total = vehicle + no_tem1 + pos_count
    sample_total = len(compounds) * replicates

    buckets: dict[str, list[str]] = {}
    for compound in compounds:
        bucket = compound.get("bucket", "sample")
        buckets.setdefault(bucket, []).append(compound["compound_id"])

    bucket_bits: list[str] = []
    if tier1 := buckets.get("tier1_inhibitor"):
        bucket_bits.append(f"row B = {len(tier1)} tier-1 inhibitors × {replicates}")
    if substrate := buckets.get("substrate_control"):
        bucket_bits.append(f"row C = {len(substrate)} substrate controls × {replicates}")
    if diverse := buckets.get("diverse_pick"):
        bucket_bits.append(f"row D = {len(diverse)} diverse picks × {replicates}")

    sample_desc = "; ".join(bucket_bits) if bucket_bits else f"{len(compounds)} compounds × {replicates}"
    return (
        f"96-well flat bottom: row A = {control_total} plate controls; "
        f"{sample_desc} ({sample_total} sample wells, {len(compounds)} unique compounds)"
        + _variable_concentration_note(compounds, default_uM=default_uM)
        + ". Rows E–H empty/reserved."
    )


def design_single_point_plate(
    compound_list: dict[str, Any],
    *,
    control_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a plate map dict from a compound_list.json payload."""
    cfg = control_row if control_row is not None else DEFAULT_CONTROL_ROW
    compounds = compound_list["compounds"]
    replicates = int(compound_list.get("replicates_per_compound", 3))
    screen_conc = compound_list.get("default_screen_conc_uM", 50)
    working_multiplier = compound_list.get("working_solution_multiplier", 10)
    compound_volume = compound_list.get("compound_volume_ul", 5)
    final_volume = compound_list.get("final_volume_ul", 50)

    wells: dict[str, dict[str, Any]] = {}
    add_control_row(wells, control_row=cfg)
    add_compound_block(wells, compounds, replicates=replicates)

    run = compound_list.get("run")
    version = compound_list.get("version")
    version_label = compound_list.get("version_label")
    versioned_path = (
        f"data/screens/{run}/v{version}/plate_map.json"
        if run is not None and version is not None
        else None
    )
    compound_list_path = compound_list.get(
        "compound_list",
        versioned_path.replace("plate_map.json", "compound_list.json")
        if versioned_path
        else None,
    )
    screen_concs = {c.get("screen_conc_uM", screen_conc) for c in compounds}
    variable_concentrations = len(screen_concs) > 1

    plate_map: dict[str, Any] = {
        "run": run,
        "version": version,
        "round": compound_list.get("round"),
        "assay_type": compound_list.get("assay_type", "single_point"),
        "final_volume_ul": final_volume,
        "compound_volume_ul": compound_volume,
        "replicates_per_compound": replicates,
        "exclude_compound_ids": compound_list.get("exclude_compound_ids", []),
        "compound_list": compound_list_path,
        "rationale_doc": compound_list.get("rationale_doc"),
        "layout_notes": _layout_notes(
            compounds,
            replicates=replicates,
            control_row=cfg,
            default_uM=screen_conc,
        ),
        "wells": wells,
        "versioned_path": versioned_path,
        "rationale_doc_active": "pvjthomas/selection_rationale.md",
        "version_label": version_label,
    }

    if variable_concentrations:
        plate_map["default_compound_concentration_uM"] = screen_conc
        plate_map["concentrations_from"] = compound_list_path
        plate_map["working_solution_uM"] = screen_conc * working_multiplier
        plate_map["description"] = (
            f"Round {compound_list.get('round')} discovery v{version} — "
            f"{len(compounds)} compounds in triplicate with literature-backed "
            "per-compound concentrations (see compound_list.json)"
        )
    else:
        plate_map["compound_concentration_uM"] = screen_conc
        plate_map["working_solution_uM"] = screen_conc * working_multiplier
        plate_map["description"] = (
            f"Round {compound_list.get('round')} discovery v{version} — "
            f"{len(compounds)} compounds in triplicate @ {screen_conc} µM"
            + (f" (reduced from 24 in v{version - 1})" if version and version > 1 else "")
        )

    return plate_map


def load_compound_list(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def write_plate_map(plate_map: dict[str, Any], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plate_map, indent=2) + "\n")
    return out


def generate_plate_map_from_file(
    compound_list_path: str | Path,
    output_path: str | Path,
    *,
    control_row: dict[str, Any] | None = None,
) -> Path:
    compound_list = load_compound_list(compound_list_path)
    plate_map = design_single_point_plate(compound_list, control_row=control_row)
    return write_plate_map(plate_map, output_path)
