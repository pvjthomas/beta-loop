# Closed-loop plan — ML

**Owner:** ML · **Task 2:** ADK agent + analysis pipeline  
**Outputs:** `data/literature_summary.json`, `data/plate_map_r*.json`, `data/round_summary_r*.json`, `agent/`, `analysis/`

Philip ([pvjthomas/COMPOUND_SELECTION.md](../pvjthomas/COMPOUND_SELECTION.md)) owns compound **selection science** and wet-lab **QC sign-off**. You own **files, code, and turnaround** on the loop.

---

## Progress snapshot (Sat ~14:06)

| Area | Status |
|------|--------|
| **Planning & schemas** | Done — `ml/` workspace, file contract in [PLAN.md](../PLAN.md), ML scope boundary documented |
| **Compound library** | Done — `data/compounds.csv` (105 compounds, tier/scaffold tags, nitrocefin excluded) |
| **Python env** | Done — `.venv` with full `requirements.txt` (see [Installed stack](#installed-stack) below) |
| **Paperclip env** | Done — CLI + SDK installed, auth working; searches not run yet |
| **Literature priors** | Done — hardcoded `data/literature_summary.json` (Paperclip raw files pending) |
| **R1 plate map** | Done — `data/plate_map_r1.json` run 1 v1 ([`data/runs/1/v1/`](../data/runs/1/v1/)) |
| **Analysis code** | Not started — no `analysis/` directory |
| **ADK agent** | Not started — package installed; no `agent/` code yet |
| **GNINA / docking** | Not started — optional |

**You are here:** Phase 1 Sat AM — ship `analysis/kinetics.py` + ADK skeleton while Rob/Chang handle GFP.

### Installed stack (`.venv`, verified Sat ~14:06)

| Package | Version | Source |
|---------|---------|--------|
| `google-adk` | 2.5.0 | `requirements.txt` |
| `gxl-paperclip` | 0.7.11 | `scripts/install-paperclip.sh` |
| `numpy` | 2.4.6 | `requirements.txt` |
| `pandas` | 3.0.5 | `requirements.txt` |
| `scipy` | 1.17.1 | `requirements.txt` |
| `rdkit` | 2025.9.3 | `requirements.txt` |

Install / verify:

```bash
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/install-paperclip.sh   # if paperclip missing
python -c "import google.adk; from gxl_paperclip import PaperclipClient; import numpy, pandas, scipy; from rdkit import Chem; print('ok')"
```

---

## Scope boundary

### You own

| Area | Deliverables |
|------|--------------|
| Literature priors | `data/literature/*.txt`, `data/literature_summary.json` |
| Plate design (files) | `data/plate_map_r1.json`, `data/plate_map_r2.json` |
| Analysis | `analysis/kinetics.py`, `analysis/ic50.py` |
| Agent | `agent/` — ADK LoopAgent + tools |
| Post-run summaries | `round_summary_r1.json`, `round_summary_r2.json` |
| Demo artifacts | heatmaps, IC50 table, agent rationale text |

### Not your job — assume these work

| Area | Owner | Your assumption |
|------|-------|-----------------|
| GFP gate go/no-go | Rob + pvjthomas | Enzyme prep is ready when Chang screens |
| Minimal validation plate | pvjthomas | Assay works; clavulanate inhibits |
| CFPS / screen on hardware | Rob + Chang | `kinetics_r*.csv` lands on time |
| Wet-lab QC during runs | pvjthomas | You analyze whatever CSV you get |
| Demo pitch script | pvjthomas | You supply plots + numbers |

**Do not idle waiting for GFP or validation.** Ship R1 plate map and analysis code in parallel.

---

## File contract (do not drift)

Schemas in [PLAN.md](../PLAN.md#file-contract-freeze-before-hackathon). Key files:

```
data/compounds.csv              ✓ exists — consume tier/scaffold_class
data/literature/*.txt           ✗ empty — Paperclip searches pending
data/literature_summary.json    ✓ hardcoded v1
data/plate_map_r1.json          ✓ run 1 v1 (see data/runs/1/v1/)
data/plate_map_r2.json          ✗ agent writes after R1
data/kinetics_r1.csv            ✗ Chang writes
data/kinetics_r2.csv            ✗ Chang writes
data/round_summary_r1.json      ✗ you write
data/round_summary_r2.json      ✗ you write
agent/                          ✗ not created
analysis/                       ✗ not created
```

### Hit scoring (implement in code)

Philip defines thresholds; you implement:

```
pct_inhibition = 100 * (1 - (slope_sample - slope_no_enzyme) / (slope_vehicle - slope_no_enzyme))
```

- **Hit @ R1:** ≥ 50% inhibition at 50 µM
- **Round 2:** 8-point dose-response, 3–100 µM log scale on R1 hits

---

## Phase 0 — Data & agent prep (do first)

### 0.1 Environment

- [x] `python -m venv .venv && source .venv/bin/activate`
- [x] `pip install -r requirements.txt` (google-adk, numpy, pandas, scipy, rdkit)
- [x] Paperclip CLI + SDK (`bash scripts/install-paperclip.sh`; auth ✓)
- [x] `.env` present (Vertex AI / Paperclip — see `.env.example`)
- [x] Verify full stack: ADK + RDKit + analysis imports OK
- [ ] Verify: `paperclip search "TEM-1 beta-lactamase inhibitor" -n 3` → save to `data/literature/`

### 0.2 Literature (Paperclip)

- [ ] Run searches below → `data/literature/`
- [x] Write `data/literature_summary.json` (hardcoded v1)

Run and save under `data/literature/`:

```bash
paperclip search "TEM-1 beta-lactamase inhibitor IC50 nitrocefin" -n 30 \
  > data/literature/tem1_inhibitors.txt

paperclip search "nitrocefin beta-lactamase assay IC50 kinetic" -n 10 \
  > data/literature/nitrocefin_assay.txt

paperclip search "beta-lactam antibiotic substrate vs beta-lactamase inhibitor" -n 10 \
  > data/literature/substrate_vs_inhibitor.txt
```

Write `data/literature_summary.json` (minimal template in PLAN.md). **If Paperclip is slow, ship a hardcoded version** with known inhibitors + 50 µM screen conc — refine later.

### 0.3 Round 1 plate map — **critical path**

- [x] **`data/plate_map_r1.json`** — run 1 v1 shipped

**Hardcode `data/plate_map_r1.json` now.** Do not wait for full agent or GNINA.

Use Philip's buckets ([COMPOUND_SELECTION.md § Round 1](../pvjthomas/COMPOUND_SELECTION.md#4-confidence-tiers--round-1-plate-24-wells)):

| Bucket | Count | compound_ids (starting set) |
|--------|-------|----------------------------|
| Tier 1 inhibitors | 4 | T19860, T1262, T6685, T14081 |
| Tier 1 extras / analogs | 4 | T14979, T1631, T13038 + 1 diverse pick |
| Substrate controls | 8 | T1005, T1008, T1305, T0814L, T1122, T1063, T0199, T0198 |
| GNINA / diverse picks | 8 | top `dock_score` or manual diverse antibiotics |
| **Plate controls** | 12 | 6× vehicle, 4× no_enzyme, 2× T19860 positive |

Total test compounds: 24 + controls. Well count ≤ 96. **Exclude T19709 (nitrocefin).**

Philip signs off science; you encode JSON.

### 0.4 Analysis skeleton

- [ ] `analysis/kinetics.py` — parse CSV, compute slopes, `pct_inhibition`
- [ ] Synthetic fixture `ml/fixtures/kinetics_r1_synthetic.csv` for unit test
- [ ] `analysis/ic50.py` — 4PL or log-linear fit (stub OK until R2)

### 0.5 ADK agent skeleton

- [ ] `agent/main.py` — `LoopAgent` max 2 iterations
- [ ] Tools: `prioritize_compounds`, `analyze_kinetics`, `design_next_plate`, `search_literature`
- [ ] R1: **`prioritize_compounds` can return hardcoded list** matching `plate_map_r1.json`
- [ ] R2: agent reads `round_summary_r1.json`, emits `plate_map_r2.json`

### 0.6 Optional (time permitting)

- [ ] GNINA batch dock → merge `dock_score` into `compounds.csv`
- [ ] RDKit Tanimoto neighbors for Tier 2 picks
- [ ] Live Paperclip in agent vs pre-baked `literature_summary.json`

---

## Phase 1 — Sat AM (while Rob runs CFPS)

**You are not on GFP gate.** Work this list instead:

| Priority | Task | Status |
|----------|------|--------|
| **P0** | Ship `data/plate_map_r1.json` | **Done** (run 1 v1) |
| **P0** | Ship `data/literature_summary.json` | **Done** (hardcoded v1) |
| **P1** | `analyze_kinetics()` passes on synthetic CSV | **Not started** |
| **P1** | ADK tools registered; R1 path returns hardcoded map | **Not started** (ADK package installed) |
| **P2** | Paperclip raw files in `data/literature/` | **Not started** (CLI ready) |
| **P2** | GNINA scores in `compounds.csv` | **Not started** (optional) |

Sync with Chang: confirm `plate_map_r1.json` schema matches what `screen.json` expects.

---

## Phase 2 — Sat PM — Round 1

| Time | Your job |
|------|----------|
| ~15:00 | Chang runs R1 — **you do not QC wells on bench** |
| ≤5 min after `kinetics_r1.csv` lands | Run `analyze_kinetics()` → `round_summary_r1.json` |
| ~16:20 | Agent emits `plate_map_r2.json` + rationale; present at mandatory sync |
| 16:20–16:50 | R1 heatmap / rank table for demo |

**Target:** analysis turnaround **< 20 min** after reader export.

### R2 design rules (encode in `design_next_plate`)

| R1 result | R2 action |
|-----------|-----------|
| ≥50% @ 50 µM | 8-point dose-response |
| 20–50% | Retest or add to DR if scarce hits |
| <20% + substrate class | Drop |
| Tier 1 inhibitor fails | Flag for pvjthomas — assay debug, not your blocker |

---

## Phase 3 — Sat night — Round 2

| Time | Your job |
|------|----------|
| ~19:00 | Chang runs R2 |
| After `kinetics_r2.csv` | IC50 fit → `round_summary_r2.json` |
| ~21:00 | Demo dashboard: R1 vs R2 plate diff, IC50 table, agent log |

---

## Phase 4 — Sunday

- [ ] Confirmatory plots if replicate data exists
- [ ] Record-friendly figures for pvjthomas pitch
- [ ] Agent rationale text export for demo

---

## Execution order (checklist)

1. [x] Repo scaffold + ML plan (`ml/`, schemas, scope boundary)
2. [x] Compound library ready (`data/compounds.csv` — team; you consume)
3. [x] Paperclip CLI + SDK installed and authenticated
4. [x] `pip install -r requirements.txt` + paperclip (full stack verified)
5. [x] **`plate_map_r1.json`** (run 1 v1)
6. [x] `literature_summary.json` (hardcoded v1)
7. [ ] `analysis/kinetics.py` + synthetic test ← **you are here**
8. [ ] ADK skeleton + tool stubs
9. [ ] Paperclip searches → `data/literature/`
10. [ ] GNINA / RDKit similarity (optional)
11. [ ] After R1: analyze → summarize → R2 plate
12. [ ] After R2: IC50 + demo artifacts

---

## When blocked

| Blocker | You do |
|---------|--------|
| Waiting on GFP / validation | **Keep building** — ignore gate; ship R1 map |
| No `kinetics_r1.csv` yet | Test on synthetic data; polish agent R2 path |
| Paperclip auth fails | Use hardcoded `literature_summary.json` |
| Agent too slow | Hardcode R1; agent drives **R2 only** |
| R1 all flat curves | Check normalization code; ping pvjthomas for assay debug |
| Philip not available for R2 sign-off | Ship best-effort R2 map; note assumptions in `agent_rationale` |

---

## Related docs

- [PLAN.md](../PLAN.md) — master timeline, schemas, plate layouts
- [REQUIREMENTS.md](../REQUIREMENTS.md) — install
- [pvjthomas/COMPOUND_SELECTION.md](../pvjthomas/COMPOUND_SELECTION.md) — selection science (consume, don't duplicate)
- [changhu/README.md](../changhu/README.md) — consumes your plate maps, produces kinetics CSV

---

*Last updated: 2026-07-25 ~14:06 PT*
