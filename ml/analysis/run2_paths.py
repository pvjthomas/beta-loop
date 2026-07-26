"""Canonical paths for Round 2 post-run artifacts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
SCREENS_DIR = DATA_DIR / "screens"

R2_POST_RUN_DIR = SCREENS_DIR / "2" / "post-run"
R2_ANALYSIS_DIR = R2_POST_RUN_DIR / "analysis"
R2_PLATE_DESIGN_DIR = SCREENS_DIR / "2" / "v5"

# Primary post-run exports
R2_KINETICS_CSV = R2_POST_RUN_DIR / "kinetics_r2.csv"
R2_GEN5_PDF = R2_POST_RUN_DIR / "r2_gen5_export.pdf"

# EDA / analysis derivatives (under post-run/analysis/)
R2_KINETICS_ANNOTATED_CSV = R2_ANALYSIS_DIR / "r2_kinetics_annotated.csv"
R2_PARSED_JSON = R2_ANALYSIS_DIR / "r2_parsed.json"
R2_ROUND_SUMMARY_EDA_JSON = R2_ANALYSIS_DIR / "r2_round_summary_eda.json"
R2_PATTERN_SUMMARY_JSON = R2_ANALYSIS_DIR / "r2_pattern_summary.json"
R2_PATTERN_SUMMARY_MD = R2_ANALYSIS_DIR / "r2_pattern_summary.md"
R2_LLM_CONTEXT_JSON = R2_ANALYSIS_DIR / "r2_kinetics_llm_context.json"
R2_LLM_CONTEXT_MD = R2_ANALYSIS_DIR / "r2_kinetics_llm_context.md"

# Agent tool promotion target (symlink/copy of kinetics_r2.csv)
R2_KINETICS_CSV_PROMOTED = DATA_DIR / "kinetics_r2.csv"

R2_ARTIFACT_PATHS = {
    "kinetics_csv": R2_KINETICS_CSV,
    "gen5_pdf": R2_GEN5_PDF,
    "annotated_csv": R2_KINETICS_ANNOTATED_CSV,
    "parsed_json": R2_PARSED_JSON,
    "round_summary_json": R2_ROUND_SUMMARY_EDA_JSON,
    "pattern_summary_json": R2_PATTERN_SUMMARY_JSON,
    "pattern_summary_md": R2_PATTERN_SUMMARY_MD,
    "llm_context_json": R2_LLM_CONTEXT_JSON,
    "llm_context_md": R2_LLM_CONTEXT_MD,
}
