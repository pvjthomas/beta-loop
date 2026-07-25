"""Repo paths for agent tools."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PVJ_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
LITERATURE_DIR = DATA_DIR / "literature"
LITERATURE_REFS_DIR = LITERATURE_DIR / "refs"
COMPOUNDS_CSV = DATA_DIR / "compounds.csv"
COMPOUND_DOSSIERS_JSON = DATA_DIR / "compound_dossiers.json"
LITERATURE_SUMMARY_JSON = DATA_DIR / "literature_summary.json"
REFERENCE_INHIBITORS_CSV = DATA_DIR / "reference_inhibitors.csv"
SELECTION_STATE_JSON = DATA_DIR / "selection" / "state.json"
SIMILARITY_NEIGHBORS_JSON = DATA_DIR / "similarity" / "neighbors.json"
SELECTION_DRAFT_PLATE_JSON = DATA_DIR / "selection" / "plate_map_r1_draft.json"

LOCAL_ROOT = PVJ_ROOT / "local"
LOCAL_LITERATURE = LOCAL_ROOT / "literature"
LOCAL_DOCKING = LOCAL_ROOT / "docking"
LOCAL_SIMILARITY = LOCAL_ROOT / "similarity"
