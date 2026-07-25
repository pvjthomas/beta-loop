"""Reverse selection tools — library → scaffold tags, docking, per-compound literature."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from agent.paths import (
    COMPOUNDS_CSV,
    COMPOUND_DOSSIERS_JSON,
    LOCAL_DOCKING,
    SELECTION_STATE_JSON,
)
from agent.tools.chem import RDKIT_AVAILABLE, normalize_name, rdkit_status, smarts_match
from agent.tools.compounds import load_compounds
from agent.tools.literature import search_literature

# Phase A bootstrap IDs — always inhibitor / exclude regardless of SMARTS.
TIER1_INHIBITOR_IDS = {
    "T19860",
    "T14979",
    "T6685",
    "T1631",
    "T1262",
    "T14081",
    "T13038",
}
EXCLUDE_IDS = {"T19709"}

INHIBITOR_NAME_FRAGMENTS = ("clavulan", "sulbactam", "tazobactam", "enmetazobactam", "sultamicillin")


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


def _classify_compound(compound: dict[str, Any]) -> tuple[str, int | None]:
    cid = compound.get("compound_id", "")
    name = (compound.get("name") or "").lower()
    receptor = (compound.get("receptor") or "").lower()
    target = (compound.get("target") or "").lower()
    text = " ".join([receptor, target, name])

    if cid in EXCLUDE_IDS:
        return "exclude", None
    if cid in TIER1_INHIBITOR_IDS or any(frag in name for frag in INHIBITOR_NAME_FRAGMENTS):
        return "inhibitor", 1

    smiles = compound.get("smiles") or ""
    if RDKIT_AVAILABLE and smiles:
        # Clavulanate / penicillanic sulfone warheads (minimal side chain).
        if smarts_match(smiles, "[#6]1[#6][#6](=O)[#7]1"):
            if any(k in name for k in ("sulbactam", "tazobactam", "clavulan", "enmetazobactam")):
                return "inhibitor", 1
        # Full acyl side chains → antibiotic substrate.
        if smarts_match(smiles, "NC(=O)[C@H]") and any(
            k in text for k in ("antibiotic", "pbp", "bacterial", "penicillin", "cephalosporin", "carbapenem")
        ):
            return "antibiotic_substrate", 3

    if any(k in text for k in ("antibiotic", "pbp", "bacterial")):
        return "antibiotic_substrate", 3
    return "other_β_lactam", 2


def classify_scaffolds_rdkit(write_csv: bool = False) -> dict[str, Any]:
    """Re-tag all library compounds using RDKit SMARTS + bootstrap inhibitor IDs (Phase B reverse R1).

    Args:
        write_csv: If True, patch scaffold_class/tier/exclude columns in data/compounds.csv.
    """
    compounds = load_compounds()
    tagged: list[dict[str, Any]] = []
    counts: dict[str, int] = {}

    for compound in compounds:
        scaffold_class, tier = _classify_compound(compound)
        counts[scaffold_class] = counts.get(scaffold_class, 0) + 1
        tagged.append(
            {
                "compound_id": compound["compound_id"],
                "name": compound.get("name"),
                "scaffold_class": scaffold_class,
                "tier": tier,
                "exclude": scaffold_class == "exclude",
            }
        )

    if write_csv and COMPOUNDS_CSV.exists():
        import csv

        with COMPOUNDS_CSV.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
            fieldnames = rows[0].keys() if rows else []
        tag_by_id = {t["compound_id"]: t for t in tagged}
        for row in rows:
            tag = tag_by_id.get(row["compound_id"])
            if not tag:
                continue
            row["scaffold_class"] = tag["scaffold_class"]
            row["tier"] = str(tag["tier"]) if tag["tier"] is not None else ""
            row["exclude"] = "true" if tag["exclude"] else "false"
        with COMPOUNDS_CSV.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    state = _load_selection_state()
    state["reverse"]["scaffold_classification"] = {
        "ran_at": _utc_now(),
        "rdkit": rdkit_status(),
        "counts": counts,
        "compounds": tagged,
        "csv_updated": write_csv,
    }
    path = _save_selection_state(state)

    return {
        "status": "ok",
        "selection_state": path,
        "rdkit": rdkit_status(),
        "counts": counts,
        "sample": tagged[:5],
    }


def run_gnina_batch(receptor_pdb: str = "1JQL", max_compounds: int = 105) -> dict[str, Any]:
    """Stub: batch GNINA docking vs TEM-1. Poses go to pvjthomas/local/docking/ (Phase B reverse R2)."""
    LOCAL_DOCKING.mkdir(parents=True, exist_ok=True)
    compounds = [c for c in load_compounds() if not c.get("exclude")][:max_compounds]
    state = _load_selection_state()
    state["reverse"]["gnina_batch"] = {
        "ran_at": _utc_now(),
        "status": "not_run",
        "receptor_pdb": receptor_pdb,
        "compound_count": len(compounds),
        "poses_local": str(LOCAL_DOCKING),
        "message": "GNINA binary not invoked — implement batch dock and write gnina_cnn_affinity to dossiers.",
    }
    path = _save_selection_state(state)
    return {
        "status": "stub",
        "selection_state": path,
        "receptor_pdb": receptor_pdb,
        "compound_count": len(compounds),
        "poses_local": str(LOCAL_DOCKING),
        "next_step": "Run GNINA locally; patch compound_dossiers.json docking.gnina_cnn_affinity.",
    }


def load_dock_scores() -> dict[str, Any]:
    """Load GNINA CNN affinity scores from compound_dossiers.json (if populated)."""
    if not COMPOUND_DOSSIERS_JSON.exists():
        return {"status": "missing", "path": str(COMPOUND_DOSSIERS_JSON), "scores": []}
    dossiers = json.loads(COMPOUND_DOSSIERS_JSON.read_text())
    scores = []
    for cid, entry in dossiers.get("compounds", {}).items():
        affinity = entry.get("docking", {}).get("gnina_cnn_affinity")
        if affinity is not None:
            scores.append({"compound_id": cid, "gnina_cnn_affinity": affinity})
    scores.sort(key=lambda x: x["gnina_cnn_affinity"])
    return {"status": "ok", "count": len(scores), "scores": scores}


def rank_by_dock_score(top_n: int = 8) -> dict[str, Any]:
    """Rank non-Tier-1 library compounds by GNINA score for Tier 3 picks (Phase B reverse R2)."""
    compounds = load_compounds()
    tier1_ids = {c["compound_id"] for c in compounds if str(c.get("tier")) == "1"}
    dock = load_dock_scores()

    if dock["count"] == 0:
        # Fallback: diverse antibiotic_substrate / other picks without scores.
        fallback = [
            c["compound_id"]
            for c in compounds
            if c["compound_id"] not in tier1_ids and not c.get("exclude")
        ][:top_n]
        state = _load_selection_state()
        state["reverse"]["dock_rank"] = {
            "ran_at": _utc_now(),
            "status": "fallback_no_scores",
            "tier3_candidates": fallback,
        }
        path = _save_selection_state(state)
        return {
            "status": "fallback",
            "selection_state": path,
            "message": "No GNINA scores in dossiers; returning first non-Tier-1 IDs.",
            "tier3_candidates": fallback,
        }

    ranked = [s for s in dock["scores"] if s["compound_id"] not in tier1_ids][:top_n]
    state = _load_selection_state()
    state["reverse"]["dock_rank"] = {"ran_at": _utc_now(), "status": "ok", "tier3_candidates": ranked}
    path = _save_selection_state(state)
    return {"status": "ok", "selection_state": path, "tier3_candidates": ranked}


def reverse_literature_check(compound_ids: list[str] | None = None, limit_per_compound: int = 3) -> dict[str, Any]:
    """Quick Paperclip search per Tier-1/2 candidate (Phase B reverse R3). Caps live API calls."""
    compounds = load_compounds()
    if compound_ids:
        targets = [c for c in compounds if c["compound_id"] in compound_ids]
    else:
        targets = [c for c in compounds if str(c.get("tier")) == "1"]

    results = []
    for compound in targets[:10]:
        query = f"{compound.get('name')} beta-lactamase inhibitor TEM-1"
        hit = search_literature(query=query, source="pmc", limit=limit_per_compound)
        results.append({"compound_id": compound["compound_id"], "name": compound.get("name"), "search": hit})

    state = _load_selection_state()
    state["reverse"]["literature_checks"] = {"ran_at": _utc_now(), "results": results}
    path = _save_selection_state(state)
    return {"status": "ok", "selection_state": path, "checked": len(results), "results": results}
