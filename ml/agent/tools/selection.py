"""Merge selection outputs into tiers and Round 1 plate draft."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from agent.paths import SELECTION_DRAFT_PLATE_JSON, SELECTION_STATE_JSON
from agent.tools.bridge import assign_tier2_analogs, cluster_library
from agent.tools.compounds import load_compounds
from agent.tools.forward import (
    match_literature_to_library,
    seed_reference_inhibitors,
    write_literature_summary_from_forward,
)
from agent.tools.reverse import classify_scaffolds_rdkit, rank_by_dock_score

# Canonical Tier-1 scaffold representatives (v1 layout).
TIER1_SCAFFOLD_REPS = ["T19860", "T1262", "T6685", "T14081"]
TIER1_ANALOG_FALLBACK = ["T14979", "T1631", "T13038", "T1213"]

# v1 substrate control set — used as fallback when clustering unavailable.
DEFAULT_SUBSTRATE_CONTROLS = [
    "T1005",
    "T1008",
    "T1305",
    "T0814L",
    "T1122",
    "T1063",
    "T0199",
    "T0198",
]

DEFAULT_DIVERSE_PICKS = [
    "T0224",
    "T1029",
    "T7387",
    "T1037",
    "T13926",
    "T0989",
    "T21369",
    "T124492",
]

REPLICATES_PER_COMPOUND = 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_selection_state() -> dict[str, Any]:
    if not SELECTION_STATE_JSON.exists():
        return {"schema_version": 1, "updated_at": None, "forward": {}, "reverse": {}, "bridge": {}, "merge": {}}
    return json.loads(SELECTION_STATE_JSON.read_text())


def _save_selection_state(state: dict[str, Any]) -> str:
    SELECTION_STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = _utc_now()
    SELECTION_STATE_JSON.write_text(json.dumps(state, indent=2) + "\n")
    return str(SELECTION_STATE_JSON)


def load_selection_state() -> dict[str, Any]:
    """Load ml/workflows/compound_selection/state.json — combined forward/reverse/bridge/merge outputs."""
    if not SELECTION_STATE_JSON.exists():
        return {
            "status": "missing",
            "path": str(SELECTION_STATE_JSON),
            "message": "Run run_compound_selection_pipeline() first.",
        }
    state = json.loads(SELECTION_STATE_JSON.read_text())
    return {"status": "ok", "path": str(SELECTION_STATE_JSON), "state": state}


def merge_tier_assignments() -> dict[str, Any]:
    """Merge forward/reverse/bridge state into tier buckets for plate design."""
    state = _load_selection_state()
    compounds = {c["compound_id"]: c for c in load_compounds()}

    tier1 = [cid for cid in TIER1_SCAFFOLD_REPS if cid in compounds]
    tier2 = [x["compound_id"] for x in state.get("bridge", {}).get("tier2_analogs", {}).get("candidates", [])]
    if len(tier2) < 4:
        for cid in TIER1_ANALOG_FALLBACK:
            if cid in compounds and cid not in tier1 and cid not in tier2:
                tier2.append(cid)
            if len(tier2) >= 4:
                break
    tier3_raw = state.get("reverse", {}).get("dock_rank", {}).get("tier3_candidates", [])
    tier3 = [x["compound_id"] if isinstance(x, dict) else x for x in tier3_raw]

    if not tier3:
        tier3 = DEFAULT_DIVERSE_PICKS

    # Substrate controls: cluster reps from antibiotic_substrate class, else v1 defaults.
    reverse_tags = state.get("reverse", {}).get("scaffold_classification", {}).get("compounds", [])
    substrates = [t["compound_id"] for t in reverse_tags if t.get("scaffold_class") == "antibiotic_substrate"]
    cluster_reps = state.get("bridge", {}).get("clustering", {}).get("representatives", [])
    tier4 = []
    if cluster_reps:
        for rep in cluster_reps:
            cid = rep["compound_id"]
            if cid in substrates and cid not in tier1 and cid not in tier2:
                tier4.append(cid)
            if len(tier4) >= 8:
                break
    if len(tier4) < 8:
        for cid in DEFAULT_SUBSTRATE_CONTROLS:
            if cid not in tier4:
                tier4.append(cid)
            if len(tier4) >= 8:
                break

    merge_payload = {
        "ran_at": _utc_now(),
        "tier1_inhibitors": tier1[:4],
        "tier2_analogs": tier2[:4],
        "tier3_docking_or_diverse": tier3[:8],
        "tier4_substrate_controls": tier4[:8],
    }
    state["merge"] = merge_payload
    path = _save_selection_state(state)

    return {"status": "ok", "selection_state": path, "tiers": merge_payload}


def _add_control_wells(wells: dict[str, Any]) -> None:
    wells.update(
        {
            "A1": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
            "A2": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
            "A3": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
            "A4": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
            "A5": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
            "A6": {"compound_id": None, "concentration_uM": 0, "role": "vehicle", "bucket": "control"},
            "A7": {"compound_id": None, "concentration_uM": 0, "role": "no_enzyme", "bucket": "control"},
            "A8": {"compound_id": None, "concentration_uM": 0, "role": "no_enzyme", "bucket": "control"},
            "A9": {"compound_id": None, "concentration_uM": 0, "role": "no_enzyme", "bucket": "control"},
            "A10": {"compound_id": None, "concentration_uM": 0, "role": "no_enzyme", "bucket": "control"},
            "A11": {"compound_id": "T19860", "concentration_uM": 50, "role": "positive_control", "bucket": "control"},
            "A12": {"compound_id": "T19860", "concentration_uM": 50, "role": "positive_control", "bucket": "control"},
        }
    )


def _add_triplicate_block(
    wells: dict[str, Any],
    start_row: str,
    compound_ids: list[str],
    bucket: str,
    functional: str,
) -> None:
    """Place each compound in REPLICATES_PER_COMPOUND adjacent columns; wrap at column 12."""
    row_idx = ord(start_row)
    col = 1
    for cid in compound_ids:
        for rep in range(1, REPLICATES_PER_COMPOUND + 1):
            if col > 12:
                row_idx += 1
                col = 1
            wells[f"{chr(row_idx)}{col}"] = {
                "compound_id": cid,
                "concentration_uM": 50,
                "role": "sample",
                "bucket": bucket,
                "functional_class": functional,
                "replicate": rep,
            }
            col += 1


def generate_round1_plate_draft() -> dict[str, Any]:
    """Build ml/workflows/compound_selection/plate_map_r1_draft.json from merged tiers (requires human sign-off to promote)."""
    merge_result = merge_tier_assignments()
    tiers = merge_result["tiers"]

    wells: dict[str, Any] = {}
    _add_control_wells(wells)
    _add_triplicate_block(wells, "B", tiers["tier1_inhibitors"], "tier1_inhibitor", "positive")
    _add_triplicate_block(wells, "C", tiers["tier2_analogs"], "inhibitor_analog", "positive")
    _add_triplicate_block(wells, "D", tiers["tier4_substrate_controls"], "substrate_control", "negative")
    _add_triplicate_block(wells, "F", tiers["tier3_docking_or_diverse"], "diverse_pick", "unknown")

    sample_wells = [w for w in wells.values() if w.get("role") == "sample"]
    unique_compounds = len({w["compound_id"] for w in sample_wells})

    plate = {
        "run": 1,
        "version": "draft",
        "version_label": "r1-selection-draft",
        "round": 1,
        "assay_type": "single_point",
        "final_volume_ul": 50,
        "compound_concentration_uM": 50,
        "working_solution_uM": 500,
        "compound_volume_ul": 5,
        "replicates_per_compound": REPLICATES_PER_COMPOUND,
        "exclude_compound_ids": ["T19709"],
        "rationale_doc": "pvjthomas/selection_rationale.md",
        "layout_notes": (
            f"96-well flat bottom: row A = 12 plate controls; rows B–G = {unique_compounds} test compounds "
            f"× {REPLICATES_PER_COMPOUND} triplicate ({len(sample_wells)} sample wells). "
            "Row H empty/reserved. ADK-generated draft — requires pvjthomas sign-off before replacing data/plate_map_r1.json."
        ),
        "wells": wells,
    }

    SELECTION_DRAFT_PLATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    SELECTION_DRAFT_PLATE_JSON.write_text(json.dumps(plate, indent=2) + "\n")

    state = _load_selection_state()
    state["merge"]["plate_draft"] = str(SELECTION_DRAFT_PLATE_JSON)
    path = _save_selection_state(state)

    return {
        "status": "ok",
        "selection_state": path,
        "draft_plate_path": str(SELECTION_DRAFT_PLATE_JSON),
        "unique_compounds": unique_compounds,
        "sample_compound_wells": len(sample_wells),
        "replicates_per_compound": REPLICATES_PER_COMPOUND,
        "note": "Draft only — do not run on robot until promoted.",
    }


def run_compound_selection_pipeline(
    run_literature_searches: bool = False,
    write_compounds_csv: bool = False,
) -> dict[str, Any]:
    """Run Phase B end-to-end: forward → reverse → bridge → merge → plate draft.

    Args:
        run_literature_searches: If True, call live Paperclip (slow; needs API key).
        write_compounds_csv: If True, patch data/compounds.csv with reverse scaffold tags.
    """
    steps: list[dict[str, Any]] = []

    steps.append(seed_reference_inhibitors())
    if run_literature_searches:
        from agent.tools.forward import run_forward_literature_searches

        steps.append(run_forward_literature_searches(save_raw=True))
    steps.append(match_literature_to_library())
    steps.append(write_literature_summary_from_forward())

    steps.append(classify_scaffolds_rdkit(write_csv=write_compounds_csv))
    steps.append(rank_by_dock_score(top_n=8))
    steps.append(assign_tier2_analogs(max_analogs=4))
    steps.append(cluster_library())

    draft = generate_round1_plate_draft()
    steps.append(draft)

    return {
        "status": "ok",
        "pipeline": "forward→reverse→bridge→merge",
        "steps": steps,
        "draft_plate_path": draft.get("draft_plate_path"),
        "selection_state": str(SELECTION_STATE_JSON),
    }
