"""Human-readable Run 2 decision tree report from ``run_2_summary.json``."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

TIER1_INHIBITOR_IDS = frozenset({"T1262", "T6685", "T14081"})
SUBSTRATE_PRIOR_IDS = frozenset({"T1005", "T1008", "T0224", "T0985"})
HIT_LABELS = frozenset({"confirmed_hit", "surprise_hit", "novel_hit"})
MISS_LABELS = frozenset({"confirmed_substrate", "surprise_miss", "inactive", "likely substrate"})

DECISION_TREE_SPEC = "pvjthomas/runs/2/v5/run2_decision_tree.md"
HAND_Q2 = "pvjthomas/runs/2/v5/hand_q2_enzyme_check.md"
HAND_Q3 = "pvjthomas/runs/2/v5/hand_q3_inhibition_check.md"


def _gate_icon(passed: bool | None) -> str:
    if passed is True:
        return "PASS"
    if passed is False:
        return "FAIL"
    return "—"


def _load_compound_names(compound_list_path: Path | None) -> dict[str, str]:
    if not compound_list_path or not compound_list_path.exists():
        return {}
    import json

    data = json.loads(compound_list_path.read_text())
    names: dict[str, str] = {}
    for entry in data.get("compounds", data if isinstance(data, list) else []):
        if isinstance(entry, dict):
            cid = str(entry.get("compound_id") or entry.get("id") or "")
            name = str(entry.get("name") or entry.get("compound_name") or "")
            if cid:
                names[cid] = name
    return names


def infer_next_action(summary: dict[str, Any]) -> tuple[str, str]:
    """Return (headline, detail) for Step 4 plate-level outcome."""
    qc = summary.get("qc_gates") or {}
    compounds = summary.get("compounds") or {}

    if not qc.get("q1_pass"):
        return (
            "Fix data export",
            "Fewer than 29/36 wells have a valid metric. Re-export the Gen5 kinetic CSV before interpreting compound calls.",
        )

    if not qc.get("q2_pass"):
        return (
            "Assay enzyme QC failed — run hand Q2 check",
            f"Vehicle/no-TEM-1 separation failed. Follow [{HAND_Q2}]({HAND_Q2}) before trusting compound labels.",
        )

    if not qc.get("q3_pass"):
        pos = qc.get("pos_ctrl_median_pct", "?")
        return (
            "Inhibition detection failed — run hand Q3 check",
            f"Positive control (clavulanic) median score {pos}% (<50 required). Follow [{HAND_Q3}]({HAND_Q3}).",
        )

    timing_suspect = [
        cid
        for cid, spec in compounds.items()
        if int(spec.get("timing_suspect_reps") or 0) >= 2
    ]
    if len(timing_suspect) >= 3:
        return (
            "Fix nitrocefin stagger before trusting negatives",
            f"Widespread timing_suspect on {', '.join(timing_suspect)}. Shorten stagger or sync nitrocefin add, then re-run substrate priors.",
        )

    tier1 = {cid: compounds[cid] for cid in TIER1_INHIBITOR_IDS if cid in compounds}
    substrates = {cid: compounds[cid] for cid in SUBSTRATE_PRIOR_IDS if cid in compounds}

    tier1_hits = sum(1 for c in tier1.values() if c.get("label") in HIT_LABELS)
    tier1_misses = sum(1 for c in tier1.values() if c.get("label") in MISS_LABELS)
    substrate_hits = [
        cid for cid, c in substrates.items() if c.get("label") in HIT_LABELS
    ]
    borderline_only = all(
        20 <= float(c.get("median_pct_inhibition") or 0) < 50 for c in compounds.values()
    ) and not summary.get("hits")

    if tier1_hits == len(tier1) and tier1 and all(
        float(c.get("median_pct_inhibition") or 0) < 20 for c in substrates.values()
    ):
        return (
            "Best case — advance top inhibitors to dose-response",
            "Tier-1 inhibitors hit and substrate priors cold. Design 8-point DR (3–100 µM) on top 1–3 confirmed hits.",
        )

    if substrate_hits:
        names = ", ".join(substrate_hits)
        return (
            "Surprise hit(s) on substrate priors — priority follow-up",
            f"Unexpected inhibition on {names}. Run 8-point dose-response on the surprise hit(s) before broader library conclusions.",
        )

    if tier1_misses == len(tier1) and qc.get("q3_pass"):
        return (
            "Tier-1 all miss — debug assay before negative calls",
            "All tier-1 inhibitors scored as misses while pos ctrl passed. Check pre-incubation, enzyme batch, and replicates before concluding.",
        )

    if tier1_misses and not qc.get("q3_pass"):
        return (
            "Assay broken — repeat validation plate",
            "Tier-1 misses plus positive control failure. Repeat vehicle / no-TEM-1 / clavulanic validation.",
        )

    if tier1_hits and tier1_misses:
        return (
            "Mixed tier-1 results — retest misses",
            "Some tier-1 inhibitors hit and others missed. Inspect replicates and layout; retest misses before concluding.",
        )

    if borderline_only:
        return (
            "Borderline only — retest at 50 µM",
            "No clean hits ≥50% median. Retest borderline compounds with a 4th rep or mini dose-response.",
        )

    if summary.get("hits"):
        return (
            "Hits detected — dose-response on top compounds",
            f"{len(summary['hits'])} compound(s) ≥50% median inhibition. Proceed to 8-point DR on ranked hits.",
        )

    return (
        "Review compound table manually",
        "No automatic Step 4 pattern matched. Inspect per-compound labels and QC flags in the summary JSON.",
    )


def format_decision_tree_report(
    summary: dict[str, Any],
    *,
    compound_names: dict[str, str] | None = None,
    spec_path: str = DECISION_TREE_SPEC,
) -> str:
    """Render a readable markdown decision-tree report from ``run_2_summary.json``."""
    qc = summary.get("qc_gates") or {}
    compounds = summary.get("compounds") or {}
    control = summary.get("control_stats") or {}
    names = compound_names or {}

    headline, action_detail = infer_next_action(summary)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    valid_wells = sum(
        1
        for detail in (summary.get("wells") or {}).values()
        if detail.get("slope_aligned") is not None or detail.get("slope_global") is not None
    )
    failed = summary.get("failed_wells") or []
    timing_suspect_wells = summary.get("wells_timing_suspect") or []
    pre_read = summary.get("pre_read_overage_wells") or []

    lines = [
        "# Run 2 decision tree report",
        "",
        f"**Generated:** {generated}  ",
        f"**Plan:** {summary.get('plan_label', 'r2-discovery-v5')} (v{summary.get('plan_version', 5)})  ",
        f"**Spec:** [{spec_path}]({spec_path})",
        "",
        "---",
        "",
        "## Verdict",
        "",
        f"**{headline}**",
        "",
        action_detail,
        "",
        "---",
        "",
        "## QC gates",
        "",
        "| Gate | Question | Result | Notes |",
        "|------|----------|--------|-------|",
        f"| **Q1** | ≥29/36 wells valid? | **{_gate_icon(qc.get('q1_pass'))}** | {valid_wells}/36 wells scored |",
    ]

    q1t_note = "timing present"
    if qc.get("q1t_timing_unknown"):
        q1t_note = "timing missing — global window used"
    elif qc.get("q1t_timing_stagger"):
        stagger = summary.get("timing_stagger_min")
        q1t_note = f"stagger flagged ({stagger:.1f} min)" if stagger is not None else "stagger flagged (>15 min)"
    lines.append(
        f"| **Q1T** | Per-well t0 aligned? | **{'WARN' if qc.get('q1t_timing_stagger') or qc.get('q1t_timing_unknown') else 'PASS'}** | {q1t_note} |"
    )
    lines.append(
        f"| **Q2** | Vehicle HOT, no-TEM-1 FLAT? | **{_gate_icon(qc.get('q2_pass'))}** | "
        f"V slope {control.get('median_vehicle_slope', '?')} · NT slope {control.get('median_no_tem1_slope', '?')} |"
    )
    lines.append(
        f"| **Q3** | Clavulanic median ≥50? | **{_gate_icon(qc.get('q3_pass'))}** | "
        f"Pos ctrl median {qc.get('pos_ctrl_median_pct', '?')}% |"
    )
    lines.extend(["", "---", "", "## Compound calls", ""])
    lines.extend(
        [
            "Median of **3/3** well inhibition scores per compound (see spec for label definitions).",
            "",
            "| ID | Name | Screen µM | Median % inhib | Label | Timing suspect reps |",
            "|----|------|-----------|----------------|-------|---------------------|",
        ]
    )

    discovery_ids = sorted(
        compounds.keys(),
        key=lambda cid: (-float(compounds[cid].get("median_pct_inhibition") or 0), cid),
    )
    for cid in discovery_ids:
        spec = compounds[cid]
        well_rows = spec.get("wells") or []
        conc = well_rows[0].get("concentration_uM", "—") if well_rows else "—"
        name = names.get(cid, "—")
        lines.append(
            f"| {cid} | {name} | {conc} | {spec.get('median_pct_inhibition', '—')} | "
            f"`{spec.get('label', '—')}` | {spec.get('timing_suspect_reps', 0)}/3 |"
        )

    if not discovery_ids:
        lines.append("| — | — | — | — | — | — |")

    lines.extend(["", "### Per-well detail (discovery)", ""])
    for cid in discovery_ids:
        spec = compounds[cid]
        well_bits = []
        for w in spec.get("wells") or []:
            flag = " ⚠ timing" if w.get("timing_suspect") else ""
            well_bits.append(f"{w['well']}={w['pct_inhibition']}%{flag}")
        lines.append(f"- **{cid}:** {', '.join(well_bits)}")

    norm = summary.get("normalization") or {}
    lines.extend(["", "---", "", "## Controls", ""])
    lines.append(f"- **Vehicle wells:** {', '.join(norm.get('vehicle_wells', []))}")
    lines.append(f"- **No-TEM-1 wells:** {', '.join(norm.get('no_tem1_wells', []))}")
    lines.append(f"- **Clavulanic wells:** {', '.join(norm.get('pos_ctrl_clavaculin_wells', []))}")
    lines.append(
        f"- **Median slopes (A490/min, aligned window):** vehicle={control.get('median_vehicle_slope', '?')}, "
        f"no-TEM-1={control.get('median_no_tem1_slope', '?')}"
    )

    lines.extend(["", "---", "", "## Timing", ""])
    lines.append(f"- **Reader lid close (UTC):** `{summary.get('reader_lid_close_utc', '—')}`")
    lines.append(f"- **Nitrocefin timing:** `{summary.get('nitrocefin_timing_json', '—')}`")
    if summary.get("timing_stagger_min") is not None:
        lines.append(f"- **Stagger (vehicle median t0 − earliest t0):** {summary['timing_stagger_min']:.1f} min")
    if timing_suspect_wells:
        lines.append(f"- **Wells flagged timing_suspect:** {', '.join(timing_suspect_wells)}")
    if pre_read:
        lines.append(f"- **Pre-read overage (>30 min):** {', '.join(pre_read)}")

    lines.extend(["", "---", "", "## Data quality flags", ""])
    if failed:
        lines.append(f"- **Failed wells ({len(failed)}):** {', '.join(sorted(failed))}")
    else:
        lines.append("- **Failed wells:** none")

    hits = summary.get("hits") or []
    if hits:
        lines.extend(["", "---", "", "## Ranked hits (≥50% median)", ""])
        for i, hit in enumerate(hits, 1):
            lines.append(
                f"{i}. **{hit['compound_id']}** — {hit['pct_inhibition']}% @ {hit.get('concentration_uM', '?')} µM ({hit['well']})"
            )

    lines.extend(["", "---", "", "## Artifacts", ""])
    lines.append("- Summary JSON: `data/assay/run_2_summary.json`")
    if summary.get("source_csv_git"):
        lines.append(f"- Kinetics CSV: `{summary['source_csv_git']}`")
    if summary.get("plate_map_active"):
        lines.append(f"- Plate map: `{summary['plate_map_active']}`")
    lines.append("")
    lines.append(f"*Report generated by `ml/analysis/decision_tree_report.py`. Decision logic: [{spec_path}]({spec_path}).*")
    lines.append("")

    return "\n".join(lines)


def write_decision_tree_report(
    summary_path: str | Path,
    output_path: str | Path,
    *,
    compound_list_path: str | Path | None = None,
) -> Path:
    """Load summary JSON and write markdown report."""
    import json

    summary_path = Path(summary_path)
    output_path = Path(output_path)
    summary = json.loads(summary_path.read_text())

    if compound_list_path is None:
        compound_list_path = REPO_ROOT / "data" / "screens" / "2" / "v5" / "compound_list.json"
    names = _load_compound_names(Path(compound_list_path) if compound_list_path else None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_decision_tree_report(summary, compound_names=names))
    return output_path
