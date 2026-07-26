"""Tests for deterministic kinetics pattern EDA."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "ml"))
sys.path.insert(0, str(REPO_ROOT / "mastermix" / "skills"))

from analysis.kinetics_eda import (  # noqa: E402
    build_kinetics_llm_context,
    format_kinetics_summary,
    format_llm_interpretation_prompt,
    summarize_kinetics_patterns,
)
from gen5_pdf import parse_gen5_kinetic_pdf  # noqa: E402

TEAM3_CSV = REPO_ROOT / "data" / "team3" / "Team_3_Data_kinetics.csv"
TEAM3_PARSED = REPO_ROOT / "data" / "team3" / "Team_3_Data_parsed.json"
TEAM3_PDF = REPO_ROOT / "Team_3_Data.pdf"
PLATE_MAP = REPO_ROOT / "data" / "screens" / "2" / "v5" / "plate_map.json"


@pytest.fixture(scope="module")
def team3_parsed() -> dict:
    if not TEAM3_PDF.exists():
        pytest.skip("Team_3_Data.pdf not available")
    return parse_gen5_kinetic_pdf(TEAM3_PDF)


def test_gen5_kinetic_results_parsed(team3_parsed: dict) -> None:
    results = team3_parsed.get("gen5_results", {})
    assert len(results) == 96
    assert results["A1"][490]["max_v"] == pytest.approx(-2.0)
    assert results["F6"][490]["max_v"] == pytest.approx(14.0)
    # Gen5 reports D5 (not G11) with strongly negative Max V in this export
    assert results["D5"][490]["max_v"] == pytest.approx(-58.0)


@pytest.mark.skipif(not TEAM3_CSV.exists(), reason="Team 3 kinetics CSV missing")
def test_team3_flat_rows() -> None:
    report = summarize_kinetics_patterns(
        TEAM3_CSV,
        PLATE_MAP,
        parsed_json=TEAM3_PARSED if TEAM3_PARSED.exists() else None,
        gen5_results=_load_gen5_results(),
    )
    flat_a = report["flat_rows"].get("A", [])
    flat_h = report["flat_rows"].get("H", [])
    assert len(flat_a) >= 6, f"expected most of row A flat, got {flat_a}"
    assert len(flat_h) == 12, f"expected all of row H flat, got {flat_h}"


@pytest.mark.skipif(not TEAM3_CSV.exists(), reason="Team 3 kinetics CSV missing")
def test_team3_high_initial_wells() -> None:
    report = summarize_kinetics_patterns(
        TEAM3_CSV,
        PLATE_MAP,
        parsed_json=TEAM3_PARSED if TEAM3_PARSED.exists() else None,
        gen5_results=_load_gen5_results(),
    )
    top_wells = {item["well"] for item in report["high_initial"][:6]}
    assert "D6" in top_wells
    assert "F6" in top_wells
    d6 = report["per_well"]["D6"]
    assert d6["A0"] == pytest.approx(0.298, abs=0.01)


@pytest.mark.skipif(not TEAM3_CSV.exists(), reason="Team 3 kinetics CSV missing")
def test_team3_rising_and_peak_decline() -> None:
    report = summarize_kinetics_patterns(
        TEAM3_CSV,
        PLATE_MAP,
        parsed_json=TEAM3_PARSED if TEAM3_PARSED.exists() else None,
        gen5_results=_load_gen5_results(),
    )
    rising_wells = {item["well"] for item in report["rising"]}
    assert "E5" in rising_wells or "E9" in rising_wells or "B7" in rising_wells

    peak_wells = {item["well"] for item in report["peak_decline"]}
    assert "D10" in peak_wells

    d10 = next(item for item in report["peak_decline"] if item["well"] == "D10")
    assert 240 <= d10["t_peak_s"] <= 360


@pytest.mark.skipif(not TEAM3_CSV.exists(), reason="Team 3 kinetics CSV missing")
def test_team3_wavelength_divergence() -> None:
    report = summarize_kinetics_patterns(
        TEAM3_CSV,
        PLATE_MAP,
        parsed_json=TEAM3_PARSED if TEAM3_PARSED.exists() else TEAM3_PARSED,
        gen5_results=_load_gen5_results(),
    )
    div_wells = {item["well"] for item in report["wavelength_divergence"]}
    assert "D6" in div_wells or "D8" in div_wells


@pytest.mark.skipif(not TEAM3_CSV.exists(), reason="Team 3 kinetics CSV missing")
def test_format_kinetics_summary_is_deterministic() -> None:
    report = summarize_kinetics_patterns(
        TEAM3_CSV,
        PLATE_MAP,
        parsed_json=TEAM3_PARSED if TEAM3_PARSED.exists() else None,
        gen5_results=_load_gen5_results(),
    )
    text = format_kinetics_summary(report, PLATE_MAP)
    assert "Kinetics pattern summary" in text
    assert "490 nm" in text
    assert "Row A" in text or "flat baseline" in text
    assert format_kinetics_summary(report, PLATE_MAP) == text


@pytest.mark.skipif(not TEAM3_CSV.exists(), reason="Team 3 kinetics CSV missing")
def test_build_kinetics_llm_context_merges_deterministic_inputs() -> None:
    from analysis.kinetics import analyze_kinetics_file

    pattern = summarize_kinetics_patterns(
        TEAM3_CSV,
        PLATE_MAP,
        parsed_json=TEAM3_PARSED if TEAM3_PARSED.exists() else None,
        gen5_results=_load_gen5_results(),
    )
    round_summary = analyze_kinetics_file(
        TEAM3_CSV,
        plate_map_json=PLATE_MAP,
        round_number=2,
        slope_window_start_s=30,
        slope_window_end_s=210,
    )
    plate_map = json.loads(PLATE_MAP.read_text())
    parsed_meta = None
    if TEAM3_PARSED.exists():
        parsed_meta = json.loads(TEAM3_PARSED.read_text()).get("metadata")

    ctx = build_kinetics_llm_context(
        pattern,
        round_summary,
        plate_map=plate_map,
        parsed_metadata=parsed_meta,
        artifact_paths={
            "kinetics_csv": str(TEAM3_CSV),
            "round_summary_json": "round_summary.json",
            "pattern_summary_json": "pattern_summary.json",
        },
        plate_map_json=PLATE_MAP,
    )

    assert ctx["feed_to_llm"] is True
    assert ctx["context_marker"] == "LLM_INTERPRETATION_INPUT"
    inputs = ctx["deterministic_inputs"]
    assert "qc_gates" in inputs
    assert "pattern_buckets" in inputs
    assert "compounds" in inputs
    assert inputs["pattern_buckets"]["flat_rows"]
    assert inputs["run_metadata"]["setpoint_temperature_c"] == 37.0

    prompt = format_llm_interpretation_prompt(ctx)
    assert "Kinetics interpretation request" in prompt
    assert "QC gates" in prompt
    assert "Flat rows" in prompt or "flat" in prompt.lower()


def _load_gen5_results() -> dict | None:
    if TEAM3_PDF.exists():
        return parse_gen5_kinetic_pdf(TEAM3_PDF).get("gen5_results")
    return None
