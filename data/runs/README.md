# Screen run artifacts

Versioned plate maps and selection rationale for each physical screen run.

## Layout

```
runs/
  {run}/           # screen execution number (1, 2, …)
    v{version}/    # plate-design revision within that run
      plate_map.json
      manifest.json
```

Selection rationale mirrors the same `{run}/v{version}/` path under `pvjthomas/runs/`.

## Active vs versioned

| Purpose | Path |
|---------|------|
| Robot / workflow consumer | `data/plate_map_r1.json` (points at latest approved v*) |
| Human-readable rationale | `pvjthomas/selection_rationale.md` |
| Immutable snapshot | `data/runs/{run}/v{version}/plate_map.json` |

When a plate design changes, add a new `v{N+1}` directory; do not edit prior versions.
