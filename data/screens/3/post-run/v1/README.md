# Round 3 post-run analysis — v1

**Active** analysis for Run 3 v1 (`r3-discovery-v1`).

Scoring uses **substrate-control anchor** (T1008, T0224, T0985) — no vehicle wells. Decision tree: [`pvjthomas/runs/3/v1/run3_decision_tree.md`](../../../../pvjthomas/runs/3/v1/run3_decision_tree.md).

## Timing inputs (synthetic)

No run log or Gen5 PDF for this round. Root-level files are operator estimates:

- `../nitrocefin_timing.json` — 6 dispenses over 120 s
- `../reader_lid_close_utc.txt` — reader at 2 min mark

Q1T should pass (≤ 2 min stagger target). Absolute UTC timestamps are placeholders.

## Status

**Awaiting** `../kinetics_r3.csv` (Gen5 export).

Once present, regenerate analysis + figures (pipeline TBD; mirrors Round 2 `generate_run2_artifacts.py`).

| Artifact | Path | Status |
|----------|------|--------|
| Round summary + QC | `analysis/r3_round_summary_eda.json` | pending |
| Decision report | `run3_decision_report.md` | pending |
| Figures + conclusions | `figures/` · `conclusions.md` | pending |
| Assay summary (git) | `../../../assay/run_3_summary.json` | pending |

Raw execution inputs live in [`../`](../).
