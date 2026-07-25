"""Kinetics parsing and hit scoring for nitrocefin A490 time courses."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HIT_THRESHOLD_PCT = 50.0
DOSE_RESPONSE_CONCENTRATIONS_UM = [3, 6, 12, 25, 50, 75, 100]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {c: c.strip().lower().replace(" ", "_") for c in df.columns}
    return df.rename(columns=renamed)


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def compute_pct_inhibition(
    slope_sample: float,
    slope_vehicle: float,
    slope_no_tem1: float,
) -> float:
    denom = slope_vehicle - slope_no_tem1
    if denom == 0:
        return 0.0
    return 100.0 * (1.0 - (slope_sample - slope_no_tem1) / denom)


def analyze_kinetics_file(
    kinetics_csv: str | Path,
    plate_map_json: str | Path | None = None,
    round_number: int = 1,
) -> dict:
    """Parse kinetics CSV, score wells, and return round summary."""
    df = _normalize_columns(pd.read_csv(kinetics_csv))

    well_col = _pick_column(df, ["well", "well_id", "well_position"])
    time_col = _pick_column(df, ["time_s", "time", "time_sec", "elapsed_s"])
    signal_col = _pick_column(
        df,
        ["absorbance_a490", "a490", "absorbance", "signal", "od490"],
    )
    if not well_col or not time_col or not signal_col:
        raise ValueError(
            f"CSV must include well, time, and A490 columns. Found: {list(df.columns)}"
        )

    slopes: dict[str, float] = {}
    for well, group in df.groupby(well_col):
        group = group.sort_values(time_col)
        if len(group) < 2:
            continue
        dt = group[time_col].diff().mean()
        if dt == 0:
            continue
        slopes[str(well)] = float(group[signal_col].diff().mean() / dt)

    roles: dict[str, dict] = {}
    compound_by_well: dict[str, str | None] = {}
    if plate_map_json and Path(plate_map_json).exists():
        plate = json.loads(Path(plate_map_json).read_text())
        for well, spec in plate.get("wells", {}).items():
            roles[well] = spec
            compound_by_well[well] = spec.get("compound_id")

    vehicle_slopes = [
        s for w, s in slopes.items() if roles.get(w, {}).get("role") == "vehicle"
    ]
    no_tem1_slopes = [
        s for w, s in slopes.items() if roles.get(w, {}).get("role") == "no_tem1"
    ]
    slope_vehicle = sum(vehicle_slopes) / len(vehicle_slopes) if vehicle_slopes else max(
        slopes.values(), default=1.0
    )
    slope_no_tem1 = (
        sum(no_tem1_slopes) / len(no_tem1_slopes)
        if no_tem1_slopes
        else min(slopes.values(), default=0.0)
    )

    hits = []
    failed_wells = []
    for well, slope in slopes.items():
        role = roles.get(well, {}).get("role", "sample")
        if role in {"vehicle", "no_tem1", "pos-ctrl-clavaculin"}:
            continue
        pct = compute_pct_inhibition(slope, slope_vehicle, slope_no_tem1)
        if pct < 0 or pct > 150:
            failed_wells.append(well)
            continue
        compound_id = compound_by_well.get(well)
        if pct >= HIT_THRESHOLD_PCT and compound_id:
            hits.append(
                {
                    "well": well,
                    "compound_id": compound_id,
                    "pct_inhibition": round(pct, 1),
                    "concentration_uM": roles.get(well, {}).get("concentration_uM", 50),
                }
            )

    hits.sort(key=lambda h: h["pct_inhibition"], reverse=True)
    return {
        "round": round_number,
        "hits": hits,
        "failed_wells": failed_wells,
        "control_stats": {
            "mean_vehicle_slope": round(slope_vehicle, 4),
            "mean_no_tem1_slope": round(slope_no_tem1, 4),
        },
        "next_plate_design": "dose_response" if hits else "none",
    }
