# Physical screen artifacts

Versioned plate maps for each nitrocefin screen run (robot team contract).

**Teammate index:** [`../README.md`](../README.md) · **Storage policy:** [`../STORAGE.md`](../STORAGE.md)  
**ADK compound selection (Philip):** [`../../ml/workflows/compound_selection/README.md`](../../ml/workflows/compound_selection/README.md)

## Rounds vs versions

| Term | Meaning | Example |
|------|---------|---------|
| **Round** | Closed-loop screening iteration | `plate_map_r**1**.json`, `assay/run_**1**_summary.json` |
| **Version** | Plate-design revision within a round | `screens/1/v**2**/plate_map.json` |

Version numbers are **assay-plan revisions**, not round numbers. Round is always in the filename (`_r1`, `_r2`).

## Layout

```
screens/
  {round}/           # matches round number (1, 2, …)
    v{version}/      # plate-design revision within that round
      plate_map.json
      plate_map.png
      manifest.json
```

Selection rationale mirrors the same `{round}/v{version}/` path under `pvjthomas/runs/`.

## Active vs frozen

| Purpose | Path |
|---------|------|
| Robot / workflow consumer | `data/plate_map_r{N}.json` (latest approved version for round *N*) |
| Human-readable rationale | `pvjthomas/selection_rationale.md` → points at active `v*` |
| Immutable snapshot | `data/screens/{round}/v{version}/plate_map.json` |

When a plate design changes, add a new `v{N+1}` directory; **do not edit** prior versions.

## Current state (Round 1)

| Version | Label | Status |
|---------|-------|--------|
| v1 | `r1-discovery-v1` | Superseded (24-compound single-replicate, not run) |
| **v2** | `r1-validation-v2` | **Active on robot** — clavulanic + DMSO @ 50 µM (8 wells) |
| v3 | `r1-discovery-v3` | Pending sign-off — 24 compound slots × triplicate on 96-well plate (84 wells) |

## Current state (Round 2)

| Version | Label | Status |
|---------|-------|--------|
| v1 | `r2-discovery-v1` | Superseded — 24 unique compounds × triplicate + `compound_list.json` / `.csv` |
| v2 | `r2-discovery-v2` | Superseded — 10 compounds (4 tier-1 + 4 substrate + 2 diverse) × triplicate |
| **v3** | `r2-discovery-v3` | **Pending sign-off** — same layout as v2 with literature-backed per-compound concentrations in `compound_list.json` (T1262 @ 1 µM) |

## Plate map visualization

Render a PNG grid from any plate map JSON (uses [wellmap](https://wellmap.readthedocs.io/)):

```bash
python scripts/render_platemap.py data/screens/1/v2/plate_map.json
```

Writes `plate_map.png` alongside the JSON. Regenerate after plate design changes. Use `--all-runs` to refresh every versioned snapshot, active map, and workflow draft.

```bash
python scripts/render_platemap.py --all-runs
python scripts/render_platemap.py data/plate_map_r1.json --cols role compound_id bucket
```

Adapter source: [`ml/analysis/plate_viz.py`](../../ml/analysis/plate_viz.py)
