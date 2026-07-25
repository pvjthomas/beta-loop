# ML — Closed-loop agent & analysis

**Primary role:** Task 2 — compound screening closed loop (see [ROLES.md](../ROLES.md))

**Detailed plan:** **[CLOSED_LOOP.md](CLOSED_LOOP.md)** — Paperclip → priors → R1 plate map → kinetics analysis → R2 design → IC50 → demo artifacts.

Personal workspace for agent code, analysis scripts, and ML notes. Shared deliverables land in `agent/`, `analysis/`, and `data/` at repo root.

## Not your job (assumed working)

These are **pvjthomas + Rob/Chang** — do not block your work on them:

- GFP gate go/no-go
- Minimal validation plate sign-off
- CFPS / screen hardware execution
- Wet-lab QC during robot runs

**Assumption:** enzyme prep and assay controls pass; you ship `plate_map_r1.json` on schedule.

## Your lead tasks

- [x] ML workspace + closed-loop plan ([CLOSED_LOOP.md](CLOSED_LOOP.md))
- [x] Paperclip CLI + SDK installed and authenticated
- [ ] `pip install -r requirements.txt` (finish ADK, RDKit, analysis stack)
- [ ] Paperclip searches → `data/literature/` + `data/literature_summary.json`
- [ ] **`data/plate_map_r1.json`** — hardcode for first run; don't wait on full agent ← **P0**
- [ ] ADK agent skeleton (`agent/`) with function tools
- [ ] `analyze_kinetics()` on synthetic CSV → `analysis/`
- [ ] After R1: `round_summary_r1.json` + `plate_map_r2.json` within 20 min of export
- [ ] After R2: IC50 table, heatmaps, `round_summary_r2.json`
- [ ] Demo dashboard / plots for pitch

## Your folder

Use this directory for:

- WIP agent prompts and tool stubs before promoting to `agent/`
- Analysis notebooks or one-off scripts before promoting to `analysis/`
- GNINA / RDKit batch job notes
- Test fixtures (synthetic `kinetics_*.csv`)

## Handoffs you receive

- **H0 (optional):** Philip's compound tiers in `data/compounds.csv` — consume, don't re-tag from scratch
- **H2:** `data/kinetics_r{N}.csv` from Chang — start analysis within 5 min

## Handoffs you send

- **H1:** `data/plate_map_r1.json` / `plate_map_r2.json` → Chang (before each screen)
- **H3:** `round_summary_r1.json` + proposed `plate_map_r2.json` → team sync (~16:20)
- **H4:** IC50 table, heatmaps, agent rationale → pvjthomas for pitch

## Interface with pvjthomas

Philip owns **compound selection rationale** and **sign-off** on R1/R2 plate science. You own **implementation**:

| Philip | You |
|--------|-----|
| Tier buckets, inhibitor vs substrate story | `plate_map_r*.json` encoding |
| R2 sign-off after R1 | Agent emits R2 proposal + rationale |
| Demo narrative | Figures, IC50 table, agent logs |

See [pvjthomas/COMPOUND_SELECTION.md](../pvjthomas/COMPOUND_SELECTION.md) for selection rules; your job is to encode them in code and files.

## Shared paths

| Path | Your files |
|------|------------|
| `agent/` | ADK LoopAgent, tools |
| `analysis/` | kinetics, IC50, plots |
| `data/literature/` | Paperclip raw outputs |
| `data/literature_summary.json` | structured priors |
| `data/plate_map_r*.json` | generate |
| `data/round_summary_r*.json` | generate |
| `data/kinetics_r*.csv` | consume |

See [PLAN.md](../PLAN.md) and [REQUIREMENTS.md](../REQUIREMENTS.md) for schemas and install.
