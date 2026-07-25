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
| v1 | `r1-discovery-v1` | Superseded (24-compound layout, not run) |
| **v2** | `r1-validation-v2` | **Active** — clavulanic + DMSO @ 50 µM |
