# Round 2 / version 5 — column-strip layout

**Round:** 2 · **Version:** 5 (`r2-discovery-v5`)  
**Supersedes:** [`data/screens/2/v4/`](../v4/)  
**Canonical concentrations:** [`compound_list.json`](../../../../data/screens/2/v5/compound_list.json) (unchanged from v4)

---

## What changed from v4

**Layout only** (plus dedupe clavulanic acid). Same concentrations as v4; **T19860 is positive control only** — removed from the discovery sample list so it is not plated twice.

| Aspect | v4 | v5 |
|--------|----|----|
| Discovery compounds | 10 (incl. T19860 sample) | **9** (T19860 POS control only) |
| Compounds & µM | unchanged for remaining 9 | unchanged |
| Replicate geometry | checkerboard | **one x-spaced column per compound** |
| Sample rows | B–G mixed | **B/D/F** then **C/E/G** (three bands) |
| Example (compound 1) | scattered | **B2, D2, F2** (Tazobactam) |
| Example (compound 6) | scattered | **C5, E5, G5** |
| Controls | B/D/F cols 3/7/11 | **B/D/F cols 3/7/11** (same spacing; C/E/G free for samples) |

---

## Layout sketch

```
      1  2  3  4  5  6  7  8  9 10 11 12
A    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·   ← empty (edge)
B    ·  1  V  2  ·  3  ·  4  ·  5  ·  ·   ← band 1; V @ 3/7
C    ·  8  ·  ·  ·  6  ·  9  ·  ·  V  ·   ← band 2/3; V @ 11
D    ·  1  N  2  ·  3  ·  4  ·  5  ·  ·   ← band 1; N @ 3/7
E    ·  8  ·  ·  ·  6  ·  9  ·  ·  N  ·   ← band 2/3; N @ 11
F    ·  1  P  2  ·  3  ·  4  ·  5  ·  ·   ← band 1; P @ 3/7
G    ·  8  ·  ·  ·  6  ·  9  ·  ·  P  ·   ← band 2/3; P @ 11
H    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·   ← empty (edge)
```

**V** @ B3/B7 + C11 · **N** @ D3/D7 + E11 · **P** @ F3/F7 + G11. Digits 1–5 = band 1 · **6–7** @ cols **5/9** · **8–9** @ cols **3/7**.

---

## Plate reader — nitrocefin kinetics

Canonical: [`kinetic_schedule.json`](../../../../data/screens/2/v5/kinetic_schedule.json) · Working copy: [`pvjthomas/output/kinetic_schedule_r2_v5.json`](../../../output/kinetic_schedule_r2_v5.json)

| Setting | Value |
|---------|-------|
| Incubator | **25 °C** |
| Equilibration after lid close | **120 s** |
| Read interval | **30 s** |
| Kinetic window | **600 s** (21 reads) |
| Slope fit window | **180–480 s** kinetic time |

Robot workflow: `mastermix/workflows/tem1_activity_screen.json` → `platereader_run_kinetic_schedule`.

Promote to robot: copy `plate_map.json` → `data/plate_map_r2.json` after sign-off.
