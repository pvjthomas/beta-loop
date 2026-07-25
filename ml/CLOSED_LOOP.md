# Closed-loop plan — ML (Philip)

**Owner:** Philip (pvjthomas) · **Task 2:** ADK agent + analysis pipeline  
**Code:** [`ml/agent/`](agent/) · [`ml/analysis/`](analysis/) · [`ml/workflows/compound_selection/`](workflows/compound_selection/)

Selection science: [pvjthomas/COMPOUND_SELECTION.md](../pvjthomas/COMPOUND_SELECTION.md).  
Master timeline: [PLAN.md](../PLAN.md).

---

## Progress snapshot (Sat ~15:30)

| Area | Status |
|------|--------|
| **Planning & schemas** | ✓ Done — file contract in [PLAN.md](../PLAN.md) |
| **ML workspace** | ✓ Done — agent, analysis, workflows consolidated under `ml/` |
| **Compound library** | ✓ Done — `data/compounds.csv` (105 compounds, tier/scaffold tags) |
| **Compound dossiers** | ✓ Done — `data/compound_dossiers.json` |
| **Python env** | ✓ Done — `.venv` + full `requirements.txt` |
| **Paperclip env** | ✓ Done — CLI + SDK installed, auth working |
| **Literature priors** | ✓ Done — `data/literature_summary.json` + per-compound refs in `data/compound_literature/refs/` |
| **Phase B ADK pipeline** | ✓ Done — forward / reverse / bridge / merger sub-agents |
| **Offline selection run** | ✓ Done — `ml/workflows/compound_selection/state.json`, draft plate, neighbors |
| **Forward v1 snapshot** | ✓ Done — `ml/workflows/compound_selection/snapshots/forward/v1/` |
| **ADK coordinator + tools** | ✓ Done — literature, kinetics, plates, selection, chem |
| **Analysis — kinetics** | ✓ Done — `ml/analysis/kinetics.py` + `analyze_kinetics()` tool |
| **Analysis — R2 plate design** | ✓ Done — `ml/analysis/plates.py` + `design_next_plate()` tool |
| **Agent tests** | ✓ Done — 23 tests passing (`pytest ml/agent/tests/`) |
| **R1 active plate** | ✓ Done — `data/plate_map_r1.json` v2 validation (8 wells) |
| **Discovery layouts archived** | ✓ Done — `data/screens/1/v1`, `v2`, `v3` |
| **R1 discovery draft** | ✓ Done — `ml/workflows/compound_selection/plate_map_r1_draft.json` (24 compounds) |
| **Paperclip batch searches** | ✗ Not done — raw `data/literature/*.txt` batch pending (per-compound refs done) |
| **GNINA docking** | ✗ Stub only — `run_gnina_batch()` not run |
| **`analysis/ic50.py`** | ✗ Not done — 4PL fit deferred until R2 data |
| **Synthetic kinetics fixture** | ✗ Not done — add `ml/agent/tests/fixtures/kinetics_r1_synthetic.csv` |
| **Live R1 kinetics** | ✗ Waiting — `data/kinetics_r1.csv` from Chang |
| **R1 analysis output** | ✗ Waiting — `data/round_summary_r1.json` after R1 export |
| **R2 plate map** | ✗ Waiting — agent writes after R1 analysis |
| **Demo artifacts** | ✗ Not done — heatmaps, IC50 table, dashboard |

**You are here:** Validation v2 on robot (or pending GFP). Build synthetic kinetics tests + demo plots while waiting for R1 CSV.

---

## Scope

### ML owns

| Area | Deliverables | Status |
|------|--------------|--------|
| Literature priors | `data/compound_literature/`, `data/literature_summary.json` | ✓ |
| Phase B pipeline | `ml/workflows/compound_selection/*` | ✓ |
| Plate design (files) | `data/plate_map_r1.json`, `data/plate_map_r2.json` | R1 ✓ · R2 ✗ |
| Analysis | `ml/analysis/kinetics.py`, `ml/analysis/plates.py` | ✓ · IC50 ✗ |
| Agent | `ml/agent/` — ADK coordinator + tools | ✓ |
| Post-run summaries | `round_summary_r1.json`, `round_summary_r2.json` | ✗ |
| Demo artifacts | heatmaps, IC50 table, agent rationale | ✗ |

### Shared with bio role (do not block on)

| Area | Owner | ML assumption |
|------|-------|---------------|
| GFP gate | Rob + Philip | Enzyme ready when Chang screens |
| Validation plate sign-off | Philip (bio) | Assay works; clavulanate inhibits |
| CFPS / screen hardware | Rob + Chang | `kinetics_r*.csv` lands on time |
| Demo pitch script | Philip (bio) | ML supplies plots + numbers |

---

## File contract

```
data/compounds.csv                              ✓
data/compound_dossiers.json                     ✓
data/reference_inhibitors.csv                   ✓
data/compound_literature/refs/{id}.json         ✓ (partial — forward hits)
data/literature_summary.json                    ✓
data/literature/*.txt                           ✗ batch searches pending
data/plate_map_r1.json                          ✓ v2 validation (active)
data/screens/1/v1/                              ✓ archived discovery
ml/workflows/compound_selection/plate_map_r1_draft.json  ✓ 24-compound draft
data/plate_map_r2.json                          ✗ after R1
data/kinetics_r1.csv                            ✗ Chang
data/kinetics_r2.csv                            ✗ Chang
data/round_summary_r1.json                      ✗ after R1
data/round_summary_r2.json                      ✗ after R2
ml/agent/                                       ✓
ml/analysis/                                    ✓ (no ic50.py yet)
```

Hit scoring (implemented in `ml/analysis/kinetics.py`):

```
pct_inhibition = 100 * (1 - (slope_sample - slope_no_enzyme) / (slope_vehicle - slope_no_enzyme))
```

- **Hit @ R1:** ≥ 50% inhibition at 50 µM
- **Round 2:** 8-point dose-response, 3–100 µM log scale on R1 hits

---

## Phase 0 — Prep

### Environment
- [x] `python -m venv .venv && source .venv/bin/activate`
- [x] `pip install -r requirements.txt` (google-adk, numpy, pandas, scipy, rdkit)
- [x] Paperclip CLI + SDK (`bash scripts/install-paperclip.sh`; auth ✓)
- [x] `.env` present (Vertex AI / Paperclip)
- [x] Verify imports: ADK + RDKit + analysis stack
- [ ] Batch Paperclip searches → `data/literature/*.txt`

### Literature
- [x] `data/literature_summary.json` (structured priors)
- [x] Per-compound refs (`data/compound_literature/refs/T19860.json`, …)
- [ ] Raw batch search files in `data/literature/`

### Round 1 plates
- [x] **`data/plate_map_r1.json`** — v2 validation (clavulanic @ 50 µM)
- [x] Discovery v1 archived — `data/screens/1/v1/`
- [x] Phase B draft — `ml/workflows/compound_selection/plate_map_r1_draft.json`
- [ ] Promote 24-compound discovery plate after validation sign-off

### Analysis
- [x] `ml/analysis/kinetics.py` — slopes, `pct_inhibition`, round summary dict
- [x] `ml/analysis/plates.py` — R2 dose-response layout
- [x] `analyze_kinetics()` ADK tool wrapper
- [ ] `analysis/ic50.py` — 4PL or log-linear fit (R2)
- [ ] Synthetic fixture + unit test on fake CSV

### ADK agent
- [x] `ml/agent/agent.py` — coordinator + 6 sub-agents
- [x] Tools: `prioritize_compounds`, `analyze_kinetics`, `design_next_plate`, `search_literature`, Phase B pipeline
- [x] Offline `run_compound_selection_pipeline()`
- [x] Test suite (`pytest ml/agent/tests/` — 23 passing)
- [ ] Optional: wrap coordinator in ADK `LoopAgent` max 2 iterations

### Optional
- [ ] GNINA batch dock → `dock_score` in `compounds.csv`
- [ ] Live Paperclip in agent vs pre-baked priors only

---

## Phase 1 — Sat AM (parallel to GFP/CFPS)

| Priority | Task | Status |
|----------|------|--------|
| **P0** | Active validation plate `data/plate_map_r1.json` | ✓ Done |
| **P0** | `literature_summary.json` + compound refs | ✓ Done |
| **P0** | ADK agent + Phase B pipeline | ✓ Done |
| **P1** | Synthetic kinetics test | ✗ Not started |
| **P1** | Confirm plate schema with Chang | ✗ TODO |
| **P2** | Paperclip batch raw files | ✗ Not started |
| **P2** | GNINA scores | ✗ Optional |

---

## Phase 2 — Sat PM — Round 1

| Time | ML job |
|------|--------|
| ~15:00 | Chang runs R1 — no bench QC from ML |
| ≤5 min after `kinetics_r1.csv` | `analyze_kinetics(round_number=1)` → `round_summary_r1.json` |
| ~16:20 | `design_next_plate()` → `plate_map_r2.json` + rationale; team sync |
| 16:20–16:50 | R1 heatmap / rank table for demo |

**Target:** analysis turnaround **< 20 min** after reader export.

### R2 design rules (in `design_next_plate`)

| R1 result | R2 action |
|-----------|-----------|
| ≥50% @ 50 µM | 8-point dose-response |
| 20–50% | Retest or add to DR if scarce hits |
| <20% + substrate class | Drop |
| Tier 1 inhibitor fails | Flag for assay debug |

---

## Phase 3 — Sat night — Round 2

| Time | ML job |
|------|--------|
| ~19:00 | Chang runs R2 |
| After `kinetics_r2.csv` | IC50 fit → `round_summary_r2.json` |
| ~21:00 | Demo dashboard: R1 vs R2 diff, IC50 table, agent log |

---

## Phase 4 — Sunday

- [ ] Confirmatory plots if replicate data exists
- [ ] Record-friendly figures for pitch
- [ ] Agent rationale text export for demo

---

## Execution order

1. [x] Repo scaffold + ML plan
2. [x] Compound library (`data/compounds.csv`)
3. [x] Python + Paperclip env
4. [x] Consolidate code under `ml/` (agent, analysis, workflows)
5. [x] Phase B pipeline + R1 validation plate
6. [x] ADK coordinator + analysis tools + tests
7. [ ] Synthetic kinetics fixture + test ← **next**
8. [ ] Paperclip batch → `data/literature/`
9. [ ] GNINA / RDKit similarity (optional)
10. [ ] After R1: analyze → summarize → R2 plate
11. [ ] After R2: IC50 + demo artifacts

---

## When blocked

| Blocker | ML does |
|---------|---------|
| Waiting on GFP / validation | Keep building — synthetic kinetics, R2 path, demo plots |
| No `kinetics_r1.csv` yet | Test on synthetic data; polish agent R2 path |
| Paperclip auth fails | Use hardcoded `literature_summary.json` (already shipped) |
| Agent too slow | Hardcode R1; agent drives **R2 only** |
| R1 all flat curves | Check normalization code; ping Philip for assay debug |

---

## Related docs

- [ml/README.md](README.md) — layout, run commands
- [ml/agent/README.md](agent/README.md) — ADK architecture
- [PLAN.md](../PLAN.md) — master timeline, schemas
- [pvjthomas/COMPOUND_SELECTION.md](../pvjthomas/COMPOUND_SELECTION.md) — selection science
- [changhu/README.md](../changhu/README.md) — consumes plate maps, produces kinetics CSV

---

*Last updated: 2026-07-25 ~15:30 PT*
