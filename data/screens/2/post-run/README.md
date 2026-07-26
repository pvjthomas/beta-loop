# Round 2 — post-run artifacts

Robot execution outputs for the physical screen, after the plate design in [`../v5/`](../v5/) was run.

| File | Contents |
|------|----------|
| `run_log_exec_*.txt` | Human-readable Zeon run log (exported from execution) |
| `r2_timing_log_analysis.md` | Phase budget and dispense-stagger write-up |
| `manifest.json` | Links this run to plate version v5 and artifact paths |
| `kinetics_r2.csv` | Plate reader kinetic export (Gen5 A490 time course) |
| `r2_gen5_export.pdf` | Source Gen5 PDF export |
| `run2_decision_report.md` | **Readable decision-tree outcome** (QC gates, compound calls, next action) |
| `nitrocefin_timing.json` | Per-well nitrocefin t0 from robot run log (Q1T) |
| `reader_lid_close_utc.txt` | Plate reader protocol start (UTC) from Gen5 export |
| `analysis/` | EDA derivatives (annotated CSV, parsed JSON, round/pattern summaries, LLM context) |

Regenerate timing + assay summary: `python ml/scripts/generate_run2_artifacts.py` or agent tool `generate_run2_artifacts()`.

### `analysis/` layout

| File | Contents |
|------|----------|
| `r2_kinetics_annotated.csv` | Wells mapped to plate layout |
| `r2_parsed.json` | Parsed Gen5 PDF (metadata + Max V QC) |
| `r2_round_summary_eda.json` | Q1/Q2/Q3 hit scoring and QC gates |
| `r2_pattern_summary.json` / `.md` | Deterministic pattern buckets |
| `r2_kinetics_llm_context.json` / `.md` | LLM interpretation input bundle |

Regenerate analysis: `analyze_kinetics_run("data/screens/2/post-run/kinetics_r2.csv", run=2, version=5)`.

Agent promotion copy: `data/kinetics_r2.csv` (for `analyze_kinetics(round_number=2)`).

Regenerate data audit: `python ml/scripts/audit_run2_data.py` or agent tool `audit_run2_data_tool()`.

Timing parser docs: [`ml/analysis/RUN_LOG_TIMING.md`](../../../ml/analysis/RUN_LOG_TIMING.md).
