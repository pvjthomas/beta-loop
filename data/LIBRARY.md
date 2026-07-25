# Compound library

**Source:** [TargetMol Beta-Lactam Compound Library-A (Google Sheets)](https://docs.google.com/spreadsheets/d/1b7UuzXu_auqoq2hFT81X3UuRutxxWxZW/edit?gid=372192752#gid=372192752)

**Local file:** `compounds.csv` (105 compounds, synced from sheet gid `372192752`)

## Format

| Column | Description |
|--------|-------------|
| `compound_id` | TargetMol ID (e.g. T19860) |
| `plate` | Source plate ID (PHD215176 / PHD215177 / PHD215178) |
| `row`, `col` | Well on source plate (lowercase row letter) |
| `concentration_mM` | 10 mM stock in DMSO |
| `volume_ul` | 50 µL |
| `smiles` | From TargetMol sheet |
| `scaffold_class` | `inhibitor` \| `antibiotic_substrate` \| `exclude` \| `other_β_lactam` |
| `tier` | 1 = known inhibitor, 3 = substrate control, blank = TBD |
| `exclude` | `true` for nitrocefin (T19709) only |

## Re-export from Google Sheets

```bash
curl -fsSL "https://docs.google.com/spreadsheets/d/1b7UuzXu_auqoq2hFT81X3UuRutxxWxZW/export?format=csv&gid=372192752" \
  -o /tmp/compound_lib.csv
# then re-run parse script in pvjthomas/COMPOUND_SELECTION.md or project tooling
```

## Selection plan

See [pvjthomas/COMPOUND_SELECTION.md](../pvjthomas/COMPOUND_SELECTION.md).
