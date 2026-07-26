"""Kinetics parsing and hit scoring for nitrocefin A490 time courses.

Scoring spec (canonical: ``pvjthomas/runs/2/v5/run2_decision_tree.md``,
``PLAN.md`` § Assay logic):

1. **Per-well metric** — A490 slope in the kinetic window (default 180–480 s),
   aligned per well to nitrocefin ``t0`` when timing metadata is available.
2. **Control anchors** — ``median`` of 3/3 vehicle wells and ``median`` of
   3/3 no-TEM-1 wells on the same plate (not mean).
3. **Per-well inhibition score** — ``compute_pct_inhibition(well, vehicle, no_tem1)``;
   vehicle → 0, no-TEM-1 → 100.
4. **Compound call** — score each of 3/3 sample wells, then ``median`` of those
   three scores → one ``pct_inhibition`` per ``compound_id``.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import pandas as pd

HIT_THRESHOLD_PCT = 50.0
DOSE_RESPONSE_CONCENTRATIONS_UM = [3, 6, 12, 25, 50, 75, 100]

EPS_ABS = 0.001  # A490/s — tune from first run CSV
STAGGER_THRESHOLD_MIN = 15.0
PRE_READ_OVERAGE_MIN = 30.0
EARLY_T0_MIN = 10.0  # minutes before vehicle t0 to flag early-dosed wells

SlopeClass = Literal["flat", "hot", "ambiguous"]

TIER1_INHIBITOR_IDS = {"T1262", "T6685", "T14081"}
SUBSTRATE_PRIOR_IDS = {"T1005", "T1008", "T0224", "T0985"}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {c: c.strip().lower().replace(" ", "_") for c in df.columns}
    return df.rename(columns=renamed)


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _parse_utc(ts: str) -> datetime:
    text = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.median(values))


def compute_pct_inhibition(
    slope_sample: float,
    slope_vehicle: float,
    slope_no_tem1: float,
) -> float:
    """Inhibition score for one well (0 = vehicle-like, 100 = no-TEM-1-like).

    ``slope_vehicle`` and ``slope_no_tem1`` should be the **median** slopes
    across 3/3 control replicates on the plate (see module docstring).
    """
    denom = slope_vehicle - slope_no_tem1
    if denom == 0:
        return 0.0
    return 100.0 * (1.0 - (slope_sample - slope_no_tem1) / denom)


def classify_slope(slope: float, slope_no_tem1_median: float) -> SlopeClass:
    """Classify a well slope as FLAT, HOT, or AMBIGUOUS (decision tree § Signal classification)."""
    flat_threshold = max(EPS_ABS, 3.0 * slope_no_tem1_median)
    hot_threshold = flat_threshold * 3.0
    if slope <= flat_threshold:
        return "flat"
    if slope >= hot_threshold:
        return "hot"
    return "ambiguous"


def align_slope_window(
    t0_well: datetime | None,
    reader_t0: datetime | None,
    schedule_start: float = 180.0,
    schedule_end: float = 480.0,
) -> tuple[float, float]:
    """Map reaction-time slope window (schedule_start–schedule_end from well t0) to reader axis."""
    if t0_well is None or reader_t0 is None:
        return schedule_start, schedule_end
    offset_s = (t0_well - reader_t0).total_seconds()
    return max(schedule_start, offset_s + schedule_start), min(
        schedule_end, offset_s + schedule_end
    )


def _compute_slope(
    group: pd.DataFrame,
    time_col: str,
    signal_col: str,
    window_start: float,
    window_end: float,
) -> float | None:
    window = group.sort_values(time_col)
    window = window[(window[time_col] >= window_start) & (window[time_col] <= window_end)]
    if len(window) < 2:
        return None
    dt = window[time_col].diff().mean()
    if dt == 0:
        return None
    return float(window[signal_col].diff().mean() / dt)


def _load_nitrocefin_timing(path: str | Path | None) -> dict[str, datetime]:
    if not path or not Path(path).exists():
        return {}
    data = json.loads(Path(path).read_text())
    by_well: dict[str, datetime] = {}
    for event in data.get("events", []):
        well = str(event.get("well", "")).strip()
        t0 = event.get("t0_utc")
        if well and t0:
            by_well[well] = _parse_utc(t0)
    return by_well


def _load_roles(plate_map_json: str | Path | None) -> tuple[dict[str, dict], dict[str, str | None]]:
    roles: dict[str, dict] = {}
    compound_by_well: dict[str, str | None] = {}
    if plate_map_json and Path(plate_map_json).exists():
        plate = json.loads(Path(plate_map_json).read_text())
        for well, spec in plate.get("wells", {}).items():
            roles[well] = spec
            compound_by_well[well] = spec.get("compound_id")
    return roles, compound_by_well


def _is_timing_suspect(
    *,
    global_class: SlopeClass,
    aligned_class: SlopeClass | None,
    aligned_slope: float | None,
    t0_well: datetime | None,
    t0_vehicle_median: datetime | None,
    pos_ctrl_median_class: SlopeClass | None,
) -> bool:
    if global_class == "hot":
        return False
    if aligned_slope is not None and aligned_class == "hot":
        return True
    if global_class != "flat":
        return False
    if t0_well and t0_vehicle_median:
        early_min = (t0_vehicle_median - t0_well).total_seconds() / 60.0
        if early_min > EARLY_T0_MIN and pos_ctrl_median_class == "hot":
            return True
    return False


def _compound_label(
    compound_id: str,
    median_score: float,
    timing_suspect_count: int,
) -> str:
    if timing_suspect_count >= 2:
        if compound_id in SUBSTRATE_PRIOR_IDS:
            return "false_flat_substrate"
        return "timing_suspect"
    if median_score >= HIT_THRESHOLD_PCT:
        if compound_id in TIER1_INHIBITOR_IDS:
            return "confirmed_hit"
        if compound_id in SUBSTRATE_PRIOR_IDS:
            return "surprise_hit"
        return "novel_hit"
    if median_score >= 20:
        if compound_id in TIER1_INHIBITOR_IDS:
            return "surprise_miss"
        if compound_id in SUBSTRATE_PRIOR_IDS:
            return "likely substrate"
        return "borderline"
    if compound_id in TIER1_INHIBITOR_IDS:
        return "surprise_miss"
    if compound_id in SUBSTRATE_PRIOR_IDS:
        return "confirmed_substrate"
    return "inactive"


def analyze_kinetics_file(
    kinetics_csv: str | Path,
    plate_map_json: str | Path | None = None,
    round_number: int = 1,
    slope_window_start_s: float | None = 180.0,
    slope_window_end_s: float | None = 480.0,
    nitrocefin_timing_json: str | Path | None = None,
    reader_lid_close_utc: str | None = None,
) -> dict:
    """Parse kinetics CSV, score wells, and return round summary with QC gates."""
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

    roles, compound_by_well = _load_roles(plate_map_json)
    timing_by_well = _load_nitrocefin_timing(nitrocefin_timing_json)

    reader_t0: datetime | None = None
    if reader_lid_close_utc:
        reader_t0 = _parse_utc(reader_lid_close_utc)
    elif timing_by_well:
        min_time = float(df[time_col].min())
        earliest_t0 = min(timing_by_well.values())
        reader_t0 = earliest_t0  # fallback: anchor reader to earliest nitrocefin add

    global_start = slope_window_start_s if slope_window_start_s is not None else 180.0
    global_end = slope_window_end_s if slope_window_end_s is not None else 480.0

    slopes_global: dict[str, float] = {}
    slopes_aligned: dict[str, float] = {}
    aligned_windows: dict[str, tuple[float, float]] = {}

    for well, group in df.groupby(well_col):
        well_id = str(well)
        global_slope = _compute_slope(group, time_col, signal_col, global_start, global_end)
        if global_slope is not None:
            slopes_global[well_id] = global_slope

        t0_well = timing_by_well.get(well_id)
        win_start, win_end = align_slope_window(
            t0_well, reader_t0, global_start, global_end
        )
        aligned_windows[well_id] = (win_start, win_end)
        aligned_slope = _compute_slope(group, time_col, signal_col, win_start, win_end)
        if aligned_slope is not None:
            slopes_aligned[well_id] = aligned_slope

    vehicle_slopes = [
        slopes_aligned.get(w, slopes_global[w])
        for w in slopes_global
        if roles.get(w, {}).get("role") == "vehicle"
    ]
    no_tem1_slopes = [
        slopes_aligned.get(w, slopes_global[w])
        for w in slopes_global
        if roles.get(w, {}).get("role") == "no_tem1"
    ]
    slope_vehicle = _median(vehicle_slopes) if vehicle_slopes else _median(list(slopes_global.values()))
    slope_no_tem1 = _median(no_tem1_slopes) if no_tem1_slopes else 0.0

    well_details: dict[str, dict] = {}
    for well, slope in slopes_global.items():
        aligned_slope = slopes_aligned.get(well)
        aligned_class = (
            classify_slope(aligned_slope, slope_no_tem1) if aligned_slope is not None else None
        )
        well_details[well] = {
            "slope_global": round(slope, 6),
            "slope_aligned": round(aligned_slope, 6) if aligned_slope is not None else None,
            "slope_class_global": classify_slope(slope, slope_no_tem1),
            "slope_class_aligned": aligned_class,
            "role": roles.get(well, {}).get("role", "sample"),
            "compound_id": compound_by_well.get(well),
            "aligned_window": aligned_windows.get(well),
        }

    vehicle_wells = [w for w, d in well_details.items() if d["role"] == "vehicle"]
    no_tem1_wells = [w for w, d in well_details.items() if d["role"] == "no_tem1"]
    pos_ctrl_wells = [w for w, d in well_details.items() if d["role"] == "pos-ctrl-clavaculin"]

    vehicle_hot = sum(1 for w in vehicle_wells if well_details[w]["slope_class_global"] == "hot")
    no_tem1_flat = sum(1 for w in no_tem1_wells if well_details[w]["slope_class_global"] == "flat")
    q2_pass = (
        vehicle_hot >= 2
        and no_tem1_flat >= 2
        and slope_vehicle >= 3.0 * slope_no_tem1
    )

    pos_ctrl_scores = []
    for w in pos_ctrl_wells:
        s = slopes_aligned.get(w, slopes_global.get(w))
        if s is not None:
            pos_ctrl_scores.append(compute_pct_inhibition(s, slope_vehicle, slope_no_tem1))
    pos_ctrl_median = _median(pos_ctrl_scores) if pos_ctrl_scores else 0.0
    q3_pass = pos_ctrl_median >= HIT_THRESHOLD_PCT

    pos_ctrl_classes = [
        well_details[w]["slope_class_global"] for w in pos_ctrl_wells if w in well_details
    ]
    pos_ctrl_median_class: SlopeClass | None = None
    if pos_ctrl_classes.count("flat") >= 2:
        pos_ctrl_median_class = "flat"
    elif pos_ctrl_classes.count("hot") >= 2:
        pos_ctrl_median_class = "hot"

    vehicle_t0s = [timing_by_well[w] for w in vehicle_wells if w in timing_by_well]
    t0_vehicle_median = (
        datetime.fromtimestamp(
            statistics.median([t.timestamp() for t in vehicle_t0s]), tz=timezone.utc
        )
        if vehicle_t0s
        else None
    )
    all_t0s = list(timing_by_well.values())
    timing_stagger_min: float | None = None
    timing_stagger_flag = False
    timing_unknown = not timing_by_well or len(timing_by_well) < 29
    if all_t0s and t0_vehicle_median:
        timing_stagger_min = (t0_vehicle_median - min(all_t0s)).total_seconds() / 60.0
        timing_stagger_flag = timing_stagger_min > STAGGER_THRESHOLD_MIN

    pre_read_overage_wells: list[str] = []
    if reader_t0:
        for well, t0 in timing_by_well.items():
            age_min = (reader_t0 - t0).total_seconds() / 60.0
            if age_min > PRE_READ_OVERAGE_MIN:
                pre_read_overage_wells.append(well)

    wells_timing_suspect: list[str] = []
    for well, detail in well_details.items():
        if detail["role"] not in {"sample"}:
            continue
        if _is_timing_suspect(
            global_class=detail["slope_class_global"],
            aligned_class=detail.get("slope_class_aligned"),
            aligned_slope=slopes_aligned.get(well),
            t0_well=timing_by_well.get(well),
            t0_vehicle_median=t0_vehicle_median,
            pos_ctrl_median_class=pos_ctrl_median_class,
        ):
            wells_timing_suspect.append(well)
            detail["timing_suspect"] = True
        else:
            detail["timing_suspect"] = False

    failed_wells: list[str] = []
    for well, detail in well_details.items():
        if detail["role"] != "sample":
            continue
        if detail["slope_aligned"] is None:
            failed_wells.append(well)
            continue
        slope = slopes_aligned.get(well, slopes_global.get(well))
        if slope is None:
            failed_wells.append(well)
            continue
        pct = compute_pct_inhibition(slope, slope_vehicle, slope_no_tem1)
        if pct < 0 or pct > 150:
            failed_wells.append(well)

    compound_wells: dict[str, list[dict]] = {}
    for well, detail in well_details.items():
        if detail["role"] != "sample":
            continue
        cid = detail.get("compound_id")
        if not cid:
            continue
        slope = slopes_aligned.get(well, slopes_global.get(well))
        if slope is None:
            continue
        pct = compute_pct_inhibition(slope, slope_vehicle, slope_no_tem1)
        if pct < 0 or pct > 150:
            if well not in failed_wells:
                failed_wells.append(well)
            continue
        compound_wells.setdefault(cid, []).append(
            {
                "well": well,
                "pct_inhibition": round(pct, 1),
                "timing_suspect": detail.get("timing_suspect", False),
                "concentration_uM": roles.get(well, {}).get("concentration_uM", 50),
            }
        )

    compounds: dict[str, dict] = {}
    hits = []
    for compound_id, wells in compound_wells.items():
        scores = [w["pct_inhibition"] for w in wells]
        median_score = _median(scores)
        timing_count = sum(1 for w in wells if w["timing_suspect"])
        label = _compound_label(compound_id, median_score, timing_count)
        compounds[compound_id] = {
            "median_pct_inhibition": round(median_score, 1),
            "wells": wells,
            "label": label,
            "timing_suspect_reps": timing_count,
        }
        if median_score >= HIT_THRESHOLD_PCT and timing_count < 2:
            hits.append(
                {
                    "well": wells[0]["well"],
                    "compound_id": compound_id,
                    "pct_inhibition": round(median_score, 1),
                    "concentration_uM": wells[0]["concentration_uM"],
                }
            )

    hits.sort(key=lambda h: h["pct_inhibition"], reverse=True)

    valid_well_count = len(slopes_global)
    assay_wells = len(roles) if roles else 36
    q1_pass = valid_well_count >= max(29, int(0.8 * assay_wells))

    return {
        "round": round_number,
        "hits": hits,
        "failed_wells": sorted(set(failed_wells)),
        "compounds": compounds,
        "wells": well_details,
        "control_stats": {
            "median_vehicle_slope": round(slope_vehicle, 6),
            "median_no_tem1_slope": round(slope_no_tem1, 6),
        },
        "qc_gates": {
            "q1_pass": q1_pass,
            "q1t_timing_unknown": timing_unknown,
            "q1t_timing_stagger": timing_stagger_flag,
            "q2_pass": q2_pass,
            "q3_pass": q3_pass,
            "pos_ctrl_median_pct": round(pos_ctrl_median, 1),
        },
        "timing_stagger_min": round(timing_stagger_min, 2) if timing_stagger_min is not None else None,
        "wells_timing_suspect": wells_timing_suspect,
        "pre_read_overage_wells": pre_read_overage_wells,
        "slope_window_start_s": slope_window_start_s,
        "slope_window_end_s": slope_window_end_s,
        "next_plate_design": "dose_response" if hits else "none",
    }
