# Assay results (git-tracked summaries)

Final per-compound assay outputs live here. **Raw plate-reader exports** default to [`pvjthomas/local/kinetics/`](../../pvjthomas/local/README.md).

See [`STORAGE.md`](../STORAGE.md) for the full git vs local policy.

## Files

| File | When | Contents |
|------|------|----------|
| `run_{n}_summary.json` | After screen run *n* | Slopes, `pct_inhibition`, labels per `compound_id` |

## `run_{n}_summary.json` shape

```json
{
  "run": 1,
  "round": 1,
  "status": "complete",
  "source_csv_local": "pvjthomas/local/kinetics/kinetics_r1.csv",
  "source_csv_git": null,
  "normalization": {
    "vehicle_wells": ["A1", "A2", "A3", "A4", "A5", "A6"],
    "no_tem1_wells": ["A7", "A8", "A9", "A10"]
  },
  "compounds": {
    "T19860": {
      "well": "B1",
      "concentration_uM": 50,
      "slope_a490_per_min": null,
      "pct_inhibition": null,
      "label": null
    }
  }
}
```

**Labels:** `confirmed_hit` | `confirmed_substrate` | `surprise_hit` | `surprise_miss` | `borderline` | `failed_well`

Results are merged into [`compound_dossiers.json`](../compound_dossiers.json) by analysis scripts after each run.
