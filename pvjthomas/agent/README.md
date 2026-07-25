# β-Loop ADK agent

**Personal / experimental** — Philip's ADK sandbox under `pvjthomas/`, not the shared repo-root `agent/` (ML owns that when shipped).

Closed-loop agent for compound screening experiments. Reads/writes shared `data/` per [STORAGE.md](../../data/STORAGE.md).

## Architecture

```
beta_loop_coordinator (root_agent)          ← adk run / adk web entry point
├── Phase B — compound list generation
│   ├── forward_agent                       ← literature → library matching
│   ├── reverse_agent                       ← RDKit scaffolds, GNINA rank stub
│   ├── bridge_agent                        ← Tanimoto + clustering
│   └── selection_merger                    ← tiers → plate_map_r1_draft.json
├── Screening rounds
│   ├── round1_planner                      ← literature + R1 plate confirmation
│   └── round2_designer                     ← R1 analysis + R2 design
└── Tools (also on coordinator)
    ├── run_compound_selection_pipeline()   ← offline F→R→B→merge
    ├── load_literature_summary() / search_literature()
    ├── classify_scaffolds_rdkit()
    ├── find_tanimoto_neighbors()
    └── analyze_kinetics() / design_next_plate()
```

Human-in-the-loop: draft plates live in `data/selection/` until sign-off; then promote to `data/plate_map_r1.json`.

## Run

From repo root (with `.env` configured for Vertex + Paperclip):

```bash
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/install-paperclip.sh

# Interactive CLI
adk run pvjthomas/agent

# Web UI
adk web pvjthomas/agent --port 8000
```

### Offline pipeline (no live Paperclip)

```bash
python -c "
import sys
sys.path.insert(0, 'pvjthomas')
from agent.tools.selection import run_compound_selection_pipeline
import json
print(json.dumps(run_compound_selection_pipeline(), indent=2))
"
```

### Example ADK prompts

| Phase | Prompt |
|-------|--------|
| **Phase B full** | "Run compound selection pipeline without live Paperclip searches." |
| **Forward only** | "Delegate to forward_agent: seed references, match literature to library, and finalize v1." |
| **Reverse only** | "Delegate to reverse_agent: classify scaffolds with RDKit and rank Tier 3." |
| **Bridge only** | "Delegate to bridge_agent: find Tanimoto neighbors and Tier 2 analogs." |
| **Merge** | "Delegate to selection_merger: merge tiers and write plate draft." |
| **Before R1** | "Load literature summary and confirm Round 1 compound picks." |
| **After R1** | "Analyze Round 1 kinetics and design the Round 2 dose-response plate." |

## Phase B outputs

| Path | Git? | Description |
|------|------|-------------|
| `data/reference_inhibitors.csv` | ✓ | Gold inhibitor list (forward) |
| `data/selection/state.json` | ✓ | Pipeline state (forward/reverse/bridge/merge) |
| `data/selection/plate_map_r1_draft.json` | ✓ | Draft plate — not for robot |
| `data/similarity/neighbors.json` | ✓ | Tanimoto neighbor summary |
| `data/literature/refs/{id}.json` | ✓ | Per-compound lit refs (forward hits) |
| `data/runs/forward/v1/` | ✓ | Frozen forward research agent v1 snapshot + manifest |
| `pvjthomas/local/literature/` | ✗ | Raw Paperclip dumps |
| `pvjthomas/local/docking/` | ✗ | GNINA poses (when run) |
| `pvjthomas/local/similarity/` | ✗ | Cluster debug / FP caches |

## Tool modules

| Module | Tools |
|--------|-------|
| `tools/forward.py` | `seed_reference_inhibitors`, `match_literature_to_library`, `build_compound_groups`, `search_literature_only_forms`, `finalize_forward_run`, … |

See [`tests/FORWARD_TEST_PLAN.md`](tests/FORWARD_TEST_PLAN.md) for v1 test plan (alternate forms, literature caps, clavulanic benchmark).
| `tools/reverse.py` | `classify_scaffolds_rdkit`, `run_gnina_batch` (stub), `rank_by_dock_score`, … |
| `tools/bridge.py` | `find_tanimoto_neighbors`, `cluster_library`, `assign_tier2_analogs` |
| `tools/selection.py` | `run_compound_selection_pipeline`, `generate_round1_plate_draft`, … |
| `tools/chem.py` | RDKit helpers (Tanimoto, SMARTS, name normalize) |

## File contract (screening rounds)

| Tool | Reads | Writes |
|------|-------|--------|
| `run_compound_selection_pipeline` | `compounds.csv`, `literature_summary.json` | `data/selection/*`, `reference_inhibitors.csv` |
| `prioritize_compounds` | `plate_map_r1.json`, `compounds.csv` | — |
| `analyze_kinetics` | `kinetics_r{N}.csv`, `plate_map_r{N}.json` | `round_summary_r{N}.json` |
| `design_next_plate` | `round_summary_r1.json` | `plate_map_r2.json` |

Analysis logic lives in [`../analysis/`](../analysis/); agent tools are thin wrappers.

See also [`../COMPOUND_SELECTION.md`](../COMPOUND_SELECTION.md) for the science plan.
