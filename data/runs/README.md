# Screen run artifacts

Versioned plate maps and selection rationale for each physical screen run.

**Teammate index:** [`../README.md`](../README.md) · **Storage policy:** [`../STORAGE.md`](../STORAGE.md)

## Rounds vs versions

| Term | Meaning | Example |
|------|---------|---------|
| **Round** | Closed-loop screening iteration | `plate_map_r**1**.json`, `assay/run_**1**_summary.json` |
| **Version** | Plate-design revision within a round | `runs/1/v**2**/plate_map.json` |

Version numbers are **assay-plan revisions**, not round numbers. Round is always in the filename (`_r1`, `_r2`).

## Layout

```
runs/
  {run}/           # matches round number (1, 2, …)
    v{version}/    # plate-design revision within that round
      plate_map.json
      manifest.json
```

Selection rationale mirrors the same `{run}/v{version}/` path under `pvjthomas/runs/`.

## Active vs frozen

| Purpose | Path |
|---------|------|
| Robot / workflow consumer | `data/plate_map_r{N}.json` (latest approved version for round *N*) |
| Human-readable rationale | `pvjthomas/selection_rationale.md` → points at active `v*` |
| Immutable snapshot | `data/runs/{run}/v{version}/plate_map.json` |

When a plate design changes, add a new `v{N+1}` directory; **do not edit** prior versions.

## Forward research agent (Phase B)

Forward-agent runs are versioned separately under `runs/forward/`:

```
runs/forward/
  v1/
    manifest.json
    reference_inhibitors.csv
    state_forward.json
    literature_summary_patch.json
    refs/
```

| Version | Label | Status |
|---------|-------|--------|
| **v1** | `forward-research-agent-v1` | Active — literature → library matching snapshot |

Active working copies remain in `data/reference_inhibitors.csv`, `data/selection/state.json`, and `data/literature/refs/`. Run `finalize_forward_run(version=1)` after a forward pass to freeze a snapshot.

## Current state (Round 1)

| Version | Label | Status |
|---------|-------|--------|
| v1 | `r1-discovery-v1` | Superseded (24-compound single-replicate, not run) |
| **v2** | `r1-validation-v2` | **Active on robot** — clavulanic + DMSO @ 50 µM (8 wells) |
| v3 | `r1-discovery-v3` | Pending sign-off — 24 compound slots × triplicate on 96-well plate (84 wells) |

## Plate map visualization

Render a PNG grid from any plate map JSON (uses [wellmap](https://wellmap.readthedocs.io/)):

```bash
python scripts/render_platemap.py data/runs/1/v2/plate_map.json
```

Writes `plate_map.png` alongside the JSON (e.g. `data/runs/1/v2/plate_map.png`). Regenerate after plate design changes. Use `--all-runs` to refresh every versioned snapshot, active map, and draft under `data/`.

```bash
# Batch: all runs/ snapshots + plate_map_r*.json + selection drafts
python scripts/render_platemap.py --all-runs

# Override projected columns (default: role + compound_id, or compound_id + concentration_uM for dose-response)
python scripts/render_platemap.py data/plate_map_r1.json --cols role compound_id bucket
```

Adapter source: [`pvjthomas/analysis/plate_viz.py`](../../pvjthomas/analysis/plate_viz.py)
