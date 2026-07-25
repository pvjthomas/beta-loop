# β-Loop ADK agent

**Personal / experimental** — Philip's ADK sandbox under `pvjthomas/`, not the shared repo-root `agent/` (ML owns that when shipped).

Closed-loop agent for compound screening experiments. Reads/writes shared `data/` per [PLAN.md](../../PLAN.md).

## Architecture

```
beta_loop_coordinator (root_agent)          ← adk run / adk web entry point
├── Tools (all phases)
│   ├── load_literature_summary()           ← pre-baked priors (default)
│   ├── search_literature()                 ← Paperclip live search (R2 on-demand)
│   ├── save_literature_search()            ← Paperclip → data/literature/
│   ├── prioritize_compounds()              ← Round 1 (reads plate_map_r1.json)
│   ├── analyze_kinetics()                  ← kinetics CSV → round_summary JSON
│   ├── design_next_plate()                 ← Round 2 dose-response plate
│   └── load_plate_map() / load_round_summary()
└── Sub-agents (delegation)
    ├── round1_planner                      ← literature + R1 plate confirmation
    └── round2_designer                     ← R1 analysis + R2 design
```

Human-in-the-loop between rounds: run Round 1 on hardware, wait for `kinetics_r1.csv`, then prompt the coordinator for Round 2 design.

## Run

From repo root (with `.env` configured for Vertex + Paperclip):

```bash
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/install-paperclip.sh

# Interactive CLI (entry point is pvjthomas/agent, not repo root)
adk run pvjthomas/agent

# Web UI
adk web pvjthomas/agent --port 8000
```

Example prompts:

- **Before R1:** "Load literature summary and confirm Round 1 compound picks."
- **After R1 CSV:** "Analyze Round 1 kinetics and design the Round 2 dose-response plate."
- **Phase 0:** "Search Paperclip for TEM-1 inhibitor IC50 in nitrocefin assays and save to data/literature/."

## Paperclip wiring

- `search_literature()` → `gxl_paperclip.PaperclipClient.from_env()`
- Auth: `PAPERCLIP_API_KEY` in `.env` or `paperclip login` credentials
- Prefer `load_literature_summary()` for Round 1; live search mainly for Round 2

## File contract

| Tool | Reads | Writes |
|------|-------|--------|
| `prioritize_compounds` | `plate_map_r1.json`, `compounds.csv` | — |
| `analyze_kinetics` | `kinetics_r{N}.csv`, `plate_map_r{N}.json` | `round_summary_r{N}.json` |
| `design_next_plate` | `round_summary_r1.json` | `plate_map_r2.json` |
| `save_literature_search` | — | `data/literature/*.txt` |

Analysis logic lives in [`../analysis/`](../analysis/); agent tools are thin wrappers.
