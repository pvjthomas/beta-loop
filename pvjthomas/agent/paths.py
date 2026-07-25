"""Repo paths for agent tools."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
LITERATURE_DIR = DATA_DIR / "literature"
COMPOUNDS_CSV = DATA_DIR / "compounds.csv"
LITERATURE_SUMMARY_JSON = DATA_DIR / "literature_summary.json"
