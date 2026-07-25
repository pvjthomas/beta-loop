"""Forward selection tools — literature → library matching."""

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.paths import (
    FORWARD_RUNS_DIR,
    LITERATURE_REFS_DIR,
    LITERATURE_SUMMARY_JSON,
    LOCAL_LITERATURE,
    REFERENCE_INHIBITORS_CSV,
    SELECTION_STATE_JSON,
)
from agent.tools.chem import normalize_name, tanimoto_smiles
from agent.tools.compounds import load_compounds
from agent.tools.literature import load_literature_summary, save_literature_search

FORWARD_AGENT_VERSION = "v1"
FORWARD_AGENT_LABEL = "forward-research-agent-v1"

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


def _compound_names(compound: dict[str, Any]) -> list[str]:
    names = [str(compound.get("name") or "")]
    synonyms = compound.get("synonyms")
    if synonyms and isinstance(synonyms, str):
        names.extend(synonyms.split(";"))
    return names


def _name_match_score(ref_name: str, compound: dict[str, Any]) -> int:
    """Score name overlap; 100 = exact normalized match."""
    ref_norm = normalize_name(ref_name)
    best = 0
    for name in _compound_names(compound):
        name_norm = normalize_name(name)
        if name_norm == ref_norm:
            return 100
        if ref_norm in name_norm:
            overlap = len(ref_norm)
            longer = max(len(ref_norm), len(name_norm))
            if longer and overlap / longer >= 0.9:
                best = max(best, overlap)
        elif name_norm in ref_norm:
            overlap = len(name_norm)
            longer = max(len(ref_norm), len(name_norm))
            if longer and overlap / longer >= 0.9:
                best = max(best, overlap)
    return best


def _name_match(ref_name: str, compound: dict[str, Any]) -> bool:
    return _name_match_score(ref_name, compound) >= 100 or _name_match_score(ref_name, compound) >= 8


def _best_name_match(ref_name: str, compounds: list[dict[str, Any]]) -> dict[str, Any] | None:
    best_compound = None
    best_score = 0
    for compound in compounds:
        if compound.get("exclude"):
            continue
        score = _name_match_score(ref_name, compound)
        if score > best_score:
            best_score = score
            best_compound = compound
    if best_score >= 100 or best_score >= 8:
        return best_compound
    return None


def _ref_file_is_curated(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return False
    for entry in payload.get("entries", []):
        if entry.get("source") == "paperclip" or entry.get("pmid") or entry.get("pmcid"):
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
        direct = _best_name_match(ref_name, compounds)
        analog = None
        best_tanimoto = 0.0

        if not direct and ref_smiles:
            for compound in compounds:
                if compound.get("exclude"):
                    continue
                if compound.get("smiles"):
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
        if not _ref_file_is_curated(ref_path):
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


def finalize_forward_run(version: int = 1, author: str = "pvjthomas") -> dict[str, Any]:
    """Snapshot forward-agent outputs to data/runs/forward/v{version}/ and write manifest."""
    state = _load_selection_state()
    forward = state.get("forward", {})
    if not forward.get("library_matches"):
        return {
            "status": "error",
            "message": "forward.library_matches missing — run match_literature_to_library() first",
        }

    version_label = f"v{version}"
    run_dir = FORWARD_RUNS_DIR / version_label
    refs_dir = run_dir / "refs"
    run_dir.mkdir(parents=True, exist_ok=True)
    refs_dir.mkdir(parents=True, exist_ok=True)

    rel_prefix = f"data/runs/forward/{version_label}"
    manifest_rel = f"{rel_prefix}/manifest.json"

    if REFERENCE_INHIBITORS_CSV.exists():
        shutil.copy2(REFERENCE_INHIBITORS_CSV, run_dir / "reference_inhibitors.csv")

    forward_snapshot = {
        "schema_version": 1,
        "agent": "forward_agent",
        "agent_version": version_label,
        "run_label": FORWARD_AGENT_LABEL if version == 1 else f"forward-research-agent-{version_label}",
        "forward": forward,
    }
    (run_dir / "state_forward.json").write_text(json.dumps(forward_snapshot, indent=2) + "\n")

    summary_patch: dict[str, Any] = {}
    if LITERATURE_SUMMARY_JSON.exists():
        summary = json.loads(LITERATURE_SUMMARY_JSON.read_text())
        summary_patch = {
            "known_inhibitors": summary.get("known_inhibitors", []),
            "library_notes": summary.get("library_notes", {}),
            "forward_updated_at": summary.get("forward_updated_at"),
        }
        (run_dir / "literature_summary_patch.json").write_text(json.dumps(summary_patch, indent=2) + "\n")

    copied_refs: list[str] = []
    for match in forward.get("library_matches", {}).get("matches", []):
        compound_id = match.get("compound_id")
        if not compound_id:
            continue
        src = LITERATURE_REFS_DIR / f"{compound_id}.json"
        if src.exists():
            dst = refs_dir / f"{compound_id}.json"
            shutil.copy2(src, dst)
            copied_refs.append(compound_id)

    created_at = _utc_now()
    manifest = {
        "agent": "forward_agent",
        "version": version,
        "label": FORWARD_AGENT_LABEL if version == 1 else f"forward-research-agent-{version_label}",
        "created_at": created_at,
        "author": author,
        "status": "complete",
        "description": (
            f"Forward research agent {version_label} — Phase B literature → library inhibitor matching"
        ),
        "files": {
            "manifest": manifest_rel,
            "reference_inhibitors": f"{rel_prefix}/reference_inhibitors.csv",
            "state_forward": f"{rel_prefix}/state_forward.json",
            "literature_summary_patch": f"{rel_prefix}/literature_summary_patch.json",
            "refs": f"{rel_prefix}/refs/",
            "active_reference_inhibitors": "data/reference_inhibitors.csv",
            "active_selection_state": "data/selection/state.json",
        },
        "match_count": len(forward.get("library_matches", {}).get("matches", [])),
        "literature_only_count": len(forward.get("library_matches", {}).get("literature_only", [])),
        "ref_compound_ids": sorted(copied_refs),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    state.setdefault("forward", {})
    state["forward"]["agent_version"] = version_label
    state["forward"]["run_label"] = manifest["label"]
    state["forward"]["manifest"] = manifest_rel
    state["forward"]["finalized_at"] = created_at
    selection_path = _save_selection_state(state)

    return {
        "status": "ok",
        "manifest": str(run_dir / "manifest.json"),
        "run_dir": str(run_dir),
        "selection_state": selection_path,
        "match_count": manifest["match_count"],
        "ref_compound_ids": copied_refs,
    }
