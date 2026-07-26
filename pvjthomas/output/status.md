# Where we are — pvjthomas workspace

**Owner:** Philip (pvjthomas)  
**Updated:** 2026-07-25  
**Active screen:** Round 2 discovery **v4** (`r2-discovery-v4`) — pending sign-off

This folder is a working copy of reports and plate artifacts. Canonical versioned files live under [`data/screens/`](../../data/screens/) and [`pvjthomas/runs/`](../runs/).

---

## Round 2 discovery — current proposal (v4)

| Item | Value |
|------|-------|
| **Status** | Pending sign-off → promote to `data/plate_map_r2.json` for robot |
| **Compounds** | 10 (same list as v2/v3) |
| **Replicates** | 3 per compound |
| **Controls** | 3 vehicle · 3 no-TEM-1 · 3 positive (T19860 @ 50 µM) |
| **Wells used** | 39 of 96 |
| **Layout** | Spaced interior — no edge wells (A/H, cols 1/12 empty); samples on checkerboard |
| **Concentrations** | Literature-backed (unchanged from v3); T1262 @ **1 µM**, others mostly @ 50 µM |

### Version history (Round 2)

| Ver | Label | What changed | Status |
|-----|-------|--------------|--------|
| v1 | `r2-discovery-v1` | 24 compounds × triplicate | Superseded |
| v2 | `r2-discovery-v2` | Cut to 10 compounds; compact layout | Superseded |
| v3 | `r2-discovery-v3` | Same layout as v2 + per-compound literature concentrations | Superseded by v4 layout |
| **v4** | **`r2-discovery-v4`** | **Same compounds/concentrations as v3; spaced interior layout only** | **Current proposal** |

Rationale docs: [`pvjthomas/runs/2/`](../runs/2/) (v1–v4).

---

## Files in this folder

### Plate maps (working copies)

| File | Description |
|------|-------------|
| [`plate_map_r2_v4.json`](plate_map_r2_v4.json) | **Current** plate map JSON |
| [`plate_map_r2_v4.png`](plate_map_r2_v4.png) | Visualization — color by sample type |
| [`plate_map_r2_v4_by_compound.png`](plate_map_r2_v4_by_compound.png) | Visualization — color by compound ID |
| [`compound_list_r2_v4.json`](compound_list_r2_v4.json) | Compound list with literature-backed concentrations |
| `plate_map.json` / `plate_map.png` | Earlier v2-era working copy (archive) |

Canonical paths:

- `data/screens/2/v4/plate_map.json`
- `data/screens/2/v4/plate_map.png`
- `data/screens/2/v4/plate_map_by_compound.png`

### Reports & tables

| File | Description |
|------|-------------|
| [`phase_a_report.md`](phase_a_report.md) | Phase A library inventory (105 compounds classified) |
| [`concentration_table.md`](concentration_table.md) | Literature concentration rules 1–3 (full library scan) |
| [`concentration_table.json`](concentration_table.json) | Machine-readable concentration table |
| [`tier1example.md`](tier1example.md) | Tier-1 inhibitor example dossier |
| [`tier2example.md`](tier2example.md) | Tier-2 example dossier |

---

## 10 compounds on the v4 plate

| Slot | ID | Name | Screen µM | Bucket |
|------|-----|------|-----------|--------|
| 1 | T19860 | Clavulanic Acid | 50 | tier1_inhibitor |
| 2 | T1262 | Tazobactam | **1.0** | tier1_inhibitor |
| 3 | T6685 | Sulbactam sodium | 50 | tier1_inhibitor |
| 4 | T14081 | Enmetazobactam | 50 | tier1_inhibitor |
| 5 | T1005 | Amoxicillin | 50 | substrate_control |
| 6 | T1008 | Cephalexin | 50 | substrate_control |
| 7 | T0224 | Meropenem | 50 | substrate_control |
| 8 | T0985 | Oxacillin sodium salt | 50 | substrate_control |
| 9 | T0138 | Cefpiramide acid | 50 | diverse_pick |
| 10 | T8390 | Cefazolin | 50 | diverse_pick |

---

## Tooling

| Task | Command |
|------|---------|
| Build v4 from v3 | `python ml/scripts/build_screen2_v4.py` |
| Generate plate map from compound list | `python pvjthomas/scripts/generate_plate_map.py data/screens/2/v4/compound_list.json -o data/screens/2/v4/plate_map.json` |
| Render PNG (sample type) | `python scripts/render_platemap.py data/screens/2/v4/plate_map.json` |
| Render PNG (by compound) | `python scripts/render_platemap.py data/screens/2/v4/plate_map.json --by compound` |

Code:

- [`pvjthomas/plates.py`](../plates.py) — layout generator (`compact` vs `spaced_interior`)
- [`ml/analysis/plate_viz.py`](../../ml/analysis/plate_viz.py) — colored PNG renderer
- [`ml/scripts/build_screen2_v3.py`](../../ml/scripts/build_screen2_v3.py) — v3 concentrations from literature
- [`ml/scripts/build_screen2_v4.py`](../../ml/scripts/build_screen2_v4.py) — v4 layout from v3

---

## Next steps

1. **Sign off v4** plate map (layout + concentrations).
2. Promote: `cp data/screens/2/v4/plate_map.json data/plate_map_r2.json`
3. Point active rationale at [`pvjthomas/runs/2/v4/selection_rationale.md`](../runs/2/v4/selection_rationale.md)
4. Run on robot / plate reader; merge results back via `ml/analysis/` pipeline

---

## Other rounds

| Round | Active version | Notes |
|-------|----------------|-------|
| R1 | v2 validation | Clavulanic vs DMSO @ 50 µM, 8 wells — [`data/screens/1/v2/`](../../data/screens/1/v2/) |
| R2 | **v4 proposed** | See above |
