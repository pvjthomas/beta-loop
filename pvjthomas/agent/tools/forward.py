"""Forward selection tools — literature → library matching."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from typing import Any

from agent.paths import (
    LITERATURE_REFS_DIR,
    LITERATURE_SUMMARY_JSON,
    LOCAL_LITERATURE,
    REFERENCE_INHIBITORS_CSV,
    SELECTION_STATE_JSON,
)
from agent.tools.chem import normalize_name, tanimoto_smiles
from agent.tools.compounds import load_compounds
from agent.tools.literature import load_literature_summary, save_literature_search

FORWARD_QUERIES = [
    ("TEM-1 beta-lactamase inhibitor IC50 nitrocefin", "pmc"),
    ("clavulanic acid sulbactam tazobactam beta-lactamase inhibitor", "pmc"),
]

SEED_INHIBITORS = [
    {
        "name": "clavulanic acid",
        "smiles": "",
        "ic50_uM": None,
        "assay": "nitrocefin",
        "source": "manual_seed",
        "pmid_or_chembl_id": "",
    },
    {
        "name": "sulbactam",
        "smiles": "",
        "ic50_uM": None,
        "assay": "nitrocefin",
        "source": "manual_seed",
        "pmid_or_chembl_id": "",
    },
    {
        "name": "tazobactam",
        "smiles": "",
        "ic50_uM": None,
        "assay": "nitrocefin",
        "source": "manual_seed",
        "pmid_or_chembl_id": "",
    },
    {
        "name": "enmetazobactam",
        "smiles": "",
        "ic50_uM": None,
        "assay": "nitrocefin",
        "source": "manual_seed",
        "pmid_or_chembl_id": "",
    },
]


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


def load_reference_inhibitors() -> dict[str, Any]:
    """Load data/reference_inhibitors.csv if present, else return seed inhibitors."""
    if REFERENCE_INHIBITORS_CSV.exists():
        with REFERENCE_INHIBITORS_CSV.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        return {"status": "ok", "source": str(REFERENCE_INHIBITORS_CSV), "count": len(rows), "inhibitors": rows}
    return {"status": "seed", "source": "built_in", "count": len(SEED_INHIBITORS), "inhibitors": SEED_INHIBITORS}


def _name_match(ref_name: str, compound: dict[str, Any]) -> bool:
    ref_norm = normalize_name(ref_name)
    names = [str(compound.get("name") or "")]
    synonyms = compound.get("synonyms")
    if synonyms and isinstance(synonyms, str):
        names.extend(synonyms.split(";"))
    for name in names:
        if normalize_name(name) == ref_norm:
            return True
        if ref_norm in normalize_name(name) or normalize_name(name) in ref_norm:
            return True
    return False


def _smiles_for_seed_name(name: str, compounds: list[dict[str, Any]]) -> str:
    for compound in compounds:
        if _name_match(name, compound):
            return compound.get("smiles") or ""
    return ""


def seed_reference_inhibitors() -> dict[str, Any]:
    """Write data/reference_inhibitors.csv from manual seeds + literature_summary known inhibitors."""
    summary = load_literature_summary()
    compounds = load_compounds()
    rows = []
    for seed in SEED_INHIBITORS:
        row = dict(seed)
        if not row.get("smiles"):
            row["smiles"] = _smiles_for_seed_name(row["name"], compounds)
        rows.append(row)
    seen = {normalize_name(r["name"]) for r in rows}
    for name in summary.get("known_inhibitors", []):
        key = normalize_name(name)
        if key in seen:
            continue
        rows.append(
            {
                "name": name,
                "smiles": "",
                "ic50_uM": "",
                "assay": "nitrocefin",
                "source": "literature_summary",
                "pmid_or_chembl_id": "",
            }
        )
        seen.add(key)

    REFERENCE_INHIBITORS_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["name", "smiles", "ic50_uM", "assay", "source", "pmid_or_chembl_id"]
    with REFERENCE_INHIBITORS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    return {"status": "ok", "path": str(REFERENCE_INHIBITORS_CSV), "count": len(rows)}


def run_forward_literature_searches(save_raw: bool = True) -> dict[str, Any]:
    """Run predefined Paperclip queries for TEM-1 inhibitors (Phase B forward F1)."""
    results = []
    for query, source in FORWARD_QUERIES:
        if save_raw:
            result = save_literature_search(query=query, source=source, limit=15)
        else:
            from agent.tools.literature import search_literature

            result = search_literature(query=query, source=source, limit=15)
        results.append(result)

    state = _load_selection_state()
    state["forward"]["literature_searches"] = {
        "ran_at": _utc_now(),
        "queries": [{"query": q, "source": s} for q, s in FORWARD_QUERIES],
        "results": results,
    }
    path = _save_selection_state(state)
    return {"status": "ok", "selection_state": path, "search_results": results}


def match_literature_to_library(tanimoto_threshold: float = 0.85) -> dict[str, Any]:
    """Match reference inhibitors to library compounds (name → synonym → Tanimoto).

    Writes per-compound refs under data/literature/refs/{compound_id}.json for direct hits.
    """
    refs_payload = load_reference_inhibitors()
    compounds = load_compounds()
    matches: list[dict[str, Any]] = []
    literature_only: list[dict[str, Any]] = []

    for ref in refs_payload["inhibitors"]:
        ref_name = ref.get("name", "")
        ref_smiles = ref.get("smiles") or ""
        direct = None
        analog = None
        best_tanimoto = 0.0

        for compound in compounds:
            if compound.get("exclude"):
                continue
            if _name_match(ref_name, compound):
                direct = compound
                break
            if ref_smiles and compound.get("smiles"):
                score = tanimoto_smiles(ref_smiles, compound["smiles"])
                if score is not None and score >= tanimoto_threshold and score > best_tanimoto:
                    best_tanimoto = score
                    analog = compound

        if direct:
            match_type = "direct"
            target = direct
        elif analog:
            match_type = "analog"
            target = analog
        else:
            literature_only.append({"reference": ref, "match": "none"})
            continue

        entry = {
            "reference_name": ref_name,
            "match_type": match_type,
            "compound_id": target["compound_id"],
            "compound_name": target.get("name"),
            "tanimoto": best_tanimoto if match_type == "analog" else 1.0,
        }
        matches.append(entry)

        LITERATURE_REFS_DIR.mkdir(parents=True, exist_ok=True)
        ref_path = LITERATURE_REFS_DIR / f"{target['compound_id']}.json"
        payload = {
            "compound_id": target["compound_id"],
            "match": "yes" if match_type == "direct" else "analog",
            "support": "strong" if match_type == "direct" else "weak",
            "reference_inhibitor": ref_name,
            "entries": [ref],
            "raw_local": str(LOCAL_LITERATURE / target["compound_id"] / ""),
        }
        ref_path.write_text(json.dumps(payload, indent=2) + "\n")

    state = _load_selection_state()
    state["forward"]["library_matches"] = {
        "ran_at": _utc_now(),
        "tanimoto_threshold": tanimoto_threshold,
        "matches": matches,
        "literature_only": literature_only,
    }
    path = _save_selection_state(state)

    return {
        "status": "ok",
        "selection_state": path,
        "direct_and_analog_matches": len(matches),
        "literature_only_count": len(literature_only),
        "matches": matches,
        "literature_only": literature_only,
    }


def write_literature_summary_from_forward() -> dict[str, Any]:
    """Merge forward match results into data/literature_summary.json (non-destructive patch)."""
    state = _load_selection_state()
    forward = state.get("forward", {})
    matches = forward.get("library_matches", {}).get("matches", [])

    if LITERATURE_SUMMARY_JSON.exists():
        summary = json.loads(LITERATURE_SUMMARY_JSON.read_text())
    else:
        summary = {}

    matched_names = [m["reference_name"] for m in matches]
    known = list(summary.get("known_inhibitors", []))
    for name in matched_names:
        if name not in known:
            known.append(name)
    summary["known_inhibitors"] = known
    summary.setdefault("library_notes", {})["forward_match_count"] = len(matches)
    summary["forward_updated_at"] = _utc_now()

    LITERATURE_SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    LITERATURE_SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    return {"status": "ok", "path": str(LITERATURE_SUMMARY_JSON), "known_inhibitors": known}
