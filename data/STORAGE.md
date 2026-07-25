# Data storage policy — Git vs local

**Owner:** Philip (pvjthomas) · **Index:** [`compounds.csv`](compounds.csv) · **Summaries:** [`compound_dossiers.json`](compound_dossiers.json)

This repo splits **team contract** (small, final, shared) from **Philip workspace** (large, intermediate, regeneratable).

---

## Rule of thumb

| Push to GitHub | Keep local (`pvjthomas/local/`) |
|----------------|----------------------------------|
| Schemas, plate maps, rationales | Raw Paperclip search/map dumps |
| Summary JSON/CSV/MD (&lt; ~500 KB) | GNINA poses (`.sdf`, `.pdbqt`), docking logs |
| Final assay aggregates | Full plate-reader exports (if large) |
| Structured literature refs | Unstructured literature walls of text |
| `compound_dossiers.json` summaries | Notebooks, scratch plots, debug logs |

**`storage` field** in dossiers: `"git"` | `"local"` | `"both"`.

---

## Directory map

```
data/                              # GIT — team contract
├── compounds.csv                  # library index (plate lookup, coarse tags)
├── compound_dossiers.json         # per-compound summaries (agent + analysis)
├── literature_summary.json        # global assay priors
├── literature/
│   └── refs/                      # structured refs per compound (push when populated)
│       └── {compound_id}.json
├── assay/
│   └── run_{n}_summary.json       # final slopes / pct_inhibition per compound
├── plate_map_r1.json              # active plate (robot)
└── runs/                          # versioned plate snapshots

pvjthomas/local/                   # LOCAL — gitignored (see .gitignore)
├── literature/{compound_id}/      # raw Paperclip *.txt
├── docking/{compound_id}/         # GNINA poses, logs
├── kinetics/                      # full kinetics_r{n}.csv exports
├── similarity/                    # Tanimoto matrices, clustering debug
└── scratch/                       # notebooks, one-off scripts
```

---

## File-by-file

| Path | Git? | Who writes | Contents |
|------|:----:|------------|----------|
| `data/compounds.csv` | ✓ | Philip / ML | Identity, source well, `scaffold_class`, `tier` |
| `data/compound_dossiers.json` | ✓ | Philip / ML | Per-compound summaries; pointers to local paths |
| `data/literature/refs/{id}.json` | ✓ | Philip | PMIDs, IC50 rows, mechanism notes |
| `data/literature_summary.json` | ✓ | ML | Global priors for agent |
| `data/assay/run_{n}_summary.json` | ✓ | ML | One row per screened compound |
| `data/kinetics_r{n}.csv` | ○ | Rob → ML | Push only if small (&lt;1 MB); else summary only |
| `data/plate_map_r*.json` | ✓ | ML | Well assignments |
| `data/runs/{run}/v{ver}/` | ✓ | ML | Versioned plate snapshots |
| `pvjthomas/local/literature/` | ✗ | Philip | Raw Paperclip output |
| `pvjthomas/local/docking/` | ✗ | Philip | GNINA artifacts |
| `pvjthomas/local/kinetics/` | ✗ | ML | Full reader exports |
| `pvjthomas/selection_rationale.md` | ✓ | Philip | Human-readable plate story |

○ = case-by-case; default local if large.

---

## `compound_dossiers.json` contract

Single pushed file keyed by `compound_id`. Agents load this first; optional per-compound folders are **not** required.

Each entry includes:

- **`classification`** — `scaffold_class`, `functional_class`, `tier`, `exclude`
- **`selection`** — `on_plate` entries from `plate_map` (null if not screened)
- **`literature`** — summary in git (`refs_summary_file`); raw in `raw_local`
- **`docking`** — `gnina_cnn_affinity` in dossier; poses in `poses_local`
- **`assay`** — `expected_at_50uM`; results in `data/assay/run_{n}_summary.json`

Regenerate or patch dossiers after batch jobs; keep `compounds.csv` columns in sync for robot lookups.

---

## Workflow

```
Paperclip search  →  pvjthomas/local/literature/T19860/*.txt   (local)
                  →  data/literature/refs/T19860.json          (git, curated)
                  →  compound_dossiers.json literature fields (git)

GNINA dock        →  pvjthomas/local/docking/T19860/          (local)
                  →  compound_dossiers.json docking.gnina_*    (git)

Screen R1         →  pvjthomas/local/kinetics/kinetics_r1.csv (local, if large)
                  →  data/assay/run_1_summary.json             (git)
                  →  data/round_summary_r1.json                (git)
```

---

## Adding local-only files

1. Write under `pvjthomas/local/…` (never `git add` — covered by `.gitignore`).
2. Update the summary in `compound_dossiers.json` or `data/assay/run_{n}_summary.json`.
3. Set `*_storage: "local"` and `*_local` path in the dossier so teammates know where Philip's copy lives.

---

## Related docs

- [`LIBRARY.md`](LIBRARY.md) — `compounds.csv` columns
- [`runs/README.md`](runs/README.md) — plate versioning
- [`../pvjthomas/local/README.md`](../pvjthomas/local/README.md) — local workspace layout
