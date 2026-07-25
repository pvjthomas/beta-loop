# Assay workflow — CFPS → GFP gate → nitrocefin screen

End-to-end wet-lab pipeline for the TEM-1 β-lactamase inhibitor screen (Track A). This document is the team reference for **what each assay does, what goes in each well, how the steps connect, and what “enzyme output” actually means**.

**Related docs**

- [PLAN.md](PLAN.md) — project plan, timeline, validation gates
- [mastermix/.zeon/CFPS_README.md](mastermix/.zeon/CFPS_README.md) — Part 1 robot workflow detail
- [pvjthomas/NITROCEFIN_ASSAY.md](pvjthomas/NITROCEFIN_ASSAY.md) — Part 3 cheat sheet (controls, scoring, DMSO rules)
- [learsch/README.md](learsch/README.md) — Rob owns Parts 1–2
- [changhu/README.md](changhu/README.md) — Chang owns Part 3

**Workflow status**

| Part | Zeon workflow | Owner | Status |
|------|---------------|-------|--------|
| 1 — CFPS | `mastermix/.zeon/workflows/cfps_mastermix.json` | Rob | Implemented |
| 2 — GFP gate | `workflows/gfp_read.json` (planned) | Rob | Planned |
| 3 — Nitrocefin screen | `workflows/screen.json` (planned) | Chang | Planned |

---

## Overview

The hack runs three sequential assays on robotics:

```
Part 1: CFPS          Part 2: GFP gate       Part 3: Nitrocefin screen
(make enzyme)    →    (confirm expression) → (measure inhibition)
     │                       │                         │
  CFPS plate              same plate              new plate
  (expression)            (read green)            (read red @ A490)
```

| Part | Question answered | Plate | Readout |
|------|-------------------|-------|---------|
| **1 — CFPS** | Can we synthesize protein cell-free? | 96-well flat bottom | *(none during run)* |
| **2 — GFP gate** | Was sfGFP–TEM-1 fusion actually made? | **Same CFPS plate** | Green **fluorescence** |
| **3 — Screen** | Does each compound inhibit TEM-1 activity? | **New assay plate** | Yellow → **red** (A490 kinetics) |

**Critical path:** Round 1 screening does not start until the GFP gate passes and the nitrocefin validation plate passes (vehicle active, no-enzyme flat, clavulanate inhibits).

---

## Part 1 — CFPS (cell-free protein synthesis)

**Goal:** Make TEM-1 by cell-free expression using the **OpenCFPS™ (SepiaBio)** kit.

**Kit:** SepiaBio OpenCFPS — Extract (3.33×), Buffer (2.5×), plus DNA templates.

### Robot steps (`cfps_mastermix`)

1. Log plate map (positive / negative / sample wells).
2. Pick up pipette.
3. Build **three master-mix tubes** (one per condition): pipette **Extract + Buffer + Water**, mix in place.
4. Aliquot each master mix into its destination wells on a 96-well flat-bottom plate.
5. Return pipette.

**Operator pre-step:** DNA is **pre-loaded by hand** into each master-mix tube before the run (volumes are below the on-deck ~0.5 µL pipetting minimum). The robot does not pipette DNA.

**After the run (downstream of workflow):** seal plate (gas-permeable seal, shiny side up) → incubate with shaking → cool. Kit protocol suggests ~6 h; green signal has been seen as early as ~30 min.

### Three conditions on the CFPS plate

| Condition | DNA template | GFP (Part 2) | Nitrocefin (Part 3) |
|-----------|--------------|--------------|---------------------|
| **Positive control** | ~2450 bp plasmid, sfGFP only; 200 nM stock (≈323 ng/µL) | Green | No β-lactamase activity |
| **Sample** | Same backbone + **sfGFP–TEM-1 fusion** insert | Green | Active enzyme — used for screening |
| **Negative control** | No DNA | Dark | Background only |

Positive and sample share the same vector backbone; sample adds the β-lactamase coding sequence. Both can glow green; only sample cleaves nitrocefin.

### Kit recipe (per 10 µL reference reaction)

The workflow scales these ratios to the chosen per-well volume (default **20 µL** per well).

| Reagent | Pos ctrl | Neg ctrl | Sample |
|---------|----------|----------|--------|
| Extract (3.33×) | 3 µL | 3 µL | 3 µL |
| Buffer (2.5×) | 4 µL | 4 µL | 4 µL |
| Control DNA (200 nM) | 0.2 µL | — | — |
| Sample DNA (plasmid) | — | — | see below* |
| Water / additives | 2.8 µL | 3 µL | remainder to 10 µL |
| **Total** | **10 µL** | **10 µL** | **10 µL** |

\*Sample DNA volume per 10 µL reaction:

```
V_DNA (µL) = (final_nM × 10) / stock_nM
```

Default in run UI: **200 nM stock → 4 nM final → 0.2 µL** per 10 µL reaction.

**Master-mix scaling:** Each condition is mixed once in a tube, then split across wells. Tube volume = (wells × per-well volume) + dead-volume overage (default 10 µL). DNA pre-load amounts scale with the whole tube so every aliquoted well has the same concentration.

### What is *not* on the CFPS plate

Compound library plates (`wellplate_pcr_parts_1`…`_3`) are for **Part 3 only**, not expression.

---

## Part 2 — GFP gate (expression confirmation)

**Goal:** Go / no-go check — confirm the sfGFP–TEM-1 fusion was expressed before spending time and reagents on the inhibition screen.

### Input and readout

| | Detail |
|---|--------|
| **Input** | The **same CFPS expression plate** after seal → incubate → cool |
| **Readout** | **sfGFP fluorescence** (excitation ~488 nm; emission in green) |
| **Pass** | Sample (TEM-1 fusion) wells >> negative (no template); positive control also glows |
| **Fail** | Re-run CFPS; do not book screen slots |

This is an **in-situ read on CFPS lysate** — no purification step. The well still contains Extract, Buffer, DNA, water, and newly expressed fusion protein.

### GFP vs activity

Green fluorescence confirms **expression** (protein was made). It does **not** prove β-lactamase **activity**. The positive control (sfGFP only) glows green but has no TEM-1 activity — that distinction matters for Part 3.

**Handoff to Chang (when gate passes):** which plate/wells hold usable enzyme prep, incubation timing, gate read values.

---

## Part 3 — Nitrocefin screen (inhibition assay)

**Goal:** Measure whether each compound reduces TEM-1 β-lactamase activity using nitrocefin kinetics.

### What nitrocefin measures

Nitrocefin is a chromogenic β-lactam **substrate**. TEM-1 cleaves it → visible color shift **yellow → red** → **A490 increases over time**.

| Slope | Meaning |
|-------|---------|
| Fast A490 rise | High TEM-1 activity (vehicle control) |
| Slow rise | Inhibition |
| Flat | Strong inhibition, no enzyme, or failed well |

**Metric:** initial slope of A490 vs time (first ~3–5 min of linear phase).

### Screen plate contents (50 µL final per well)

| # | Component | Typical volume | Notes |
|---|-----------|----------------|--------|
| 1 | Assay buffer (BLB) | fills to volume | Na phosphate ~pH 7; often 0.1% BSA |
| 2 | **TEM-1 enzyme prep** | ~20 µL | From CFPS sample wells; see *What “enzyme prep” means* below |
| 3 | Compound or vehicle | 5 µL | From 10 mM DMSO library stock; **50 µM final** in Round 1 |
| 4 | Nitrocefin | 25 µL | Add **last** — starts the reaction clock |

**Purified-enzyme reference (from brief, not the default lysate path):** 20 µL at 0.1 ng/µL → 2 ng TEM-1 per well.

### Mixing order (do not reorder)

```
assay buffer / enzyme prep
  → add compound OR DMSO-matched vehicle
  → pre-incubate RT (~10 min)
  → add nitrocefin to ALL wells (track time)
  → plate reader: A490 every 30 s for several minutes
```

Nitrocefin addition starts the clock. Batch the nitrocefin add, then read immediately.

### Controls (every screen plate)

| Well type | Enzyme | Compound | Expected |
|-----------|--------|----------|----------|
| **Vehicle** | ✓ | DMSO only (matched %) | Max slope — normalization reference |
| **No-enzyme** | ✗ | DMSO or compound | Min slope — background |
| **Positive** (recommended) | ✓ | Clavulanic acid @ 50 µM (T19860) | Strong inhibition vs vehicle |

### Scoring

Normalize each well to controls on the **same plate**:

```
pct_inhibition = 100 × (1 - (slope_sample - slope_no_enzyme) / (slope_vehicle - slope_no_enzyme))
```

| Result @ 50 µM | Interpretation |
|----------------|----------------|
| ≥ 50% | Hit → dose-response in Round 2 |
| < 20% + antibiotic scaffold | Likely **substrate**, not inhibitor (expected for many library compounds) |

Round 1 plate map: `data/plate_map_r1.json` → robot well assignments from `data/compounds.csv`.

---

## What “enzyme prep” actually means

This is the main handoff between Parts 1–2 and Part 3. The docs say “use enzyme **output**” and “do not add CFPS master mix / DNA / Sepia reagents as separate screen reagents.” That means **do not pipette fresh kit components onto the screen plate** — it does **not** mean the transferred material is purified TEM-1.

### If CFPS lysate is transferred directly (~20 µL from a CFPS well)

The aliquot is the **entire CFPS reaction mixture**:

| Component | Carried over from CFPS |
|-----------|------------------------|
| Sepia Extract (cell-free machinery) | ✓ |
| Sepia Buffer (energy / salts) | ✓ |
| DNA template (plasmid) | ✓ |
| Water | ✓ |
| Expressed sfGFP–TEM-1 fusion | ✓ |

There is **no purification or buffer exchange** in the current plan. Enzyme prep = **TEM-1-containing lysate**, not isolated protein.

### Dilution in the screen well

Default volumes:

- CFPS well: **~20 µL** total reaction
- Screen well: **50 µL** final ≈ 20 µL enzyme prep + 5 µL compound + 25 µL nitrocefin

Everything in the lysate aliquot is therefore diluted **~2.5×** (20 µL into 50 µL). Approximate carryover into one screen well from a 20 µL CFPS well (kit recipe scaled 2× from the 10 µL reference):

| Component | In CFPS well (~20 µL) | In screen well (~50 µL) | ~Fraction of CFPS concentration |
|-----------|------------------------|-------------------------|----------------------------------|
| Extract | ~6 µL | ~6 µL | ~40% |
| Buffer | ~8 µL | ~8 µL | ~40% |
| DNA | trace | trace | ~40% |
| Expressed fusion | in lysate | in lysate | ~40% |

An optional **enzyme prep step** (pool sample wells, dilute into BLB before plating) would further dilute and recondition the lysate — still not purified enzyme. **Kickoff TBD:** direct lysate transfer vs BLB dilution prep.

### Practical implications

- **Extract carryover** may contribute background or interfere with compounds — check lysate compatibility.
- **DNA carryover** is usually irrelevant once protein is expressed.
- **Assay tuning** (lysate volume per well) affects signal vs background together.
- The **GFP gate** and **screen** therefore read different things on different plates: expression in messy lysate (Part 2) vs activity in diluted lysate + compound + nitrocefin (Part 3).

---

## GFP vs nitrocefin — side by side

| | **GFP gate (Part 2)** | **Nitrocefin screen (Part 3)** |
|---|----------------------|--------------------------------|
| **Physics** | Fluorescence | Absorbance / visible color change |
| **Color / signal** | Green glow when sfGFP is expressed | Yellow → **red** as substrate is cleaved |
| **Instrument** | Fluorescence reader (~488 nm excitation) | Plate reader **A490** |
| **Measures** | Expression — was protein made? | Activity — is β-lactamase working? |
| **Plate** | CFPS plate (in situ) | New assay plate |
| **Material** | Full CFPS lysate in well | Diluted lysate aliquot + buffer + compound + nitrocefin |

---

## Validation before Round 1

Run a minimal validation plate (~10 wells) before committing the full Round 1 library plate. Antibiotics are **not required** to prove the assay works.

| Wells | Role | Pass criterion |
|-------|------|----------------|
| 4× Vehicle | enzyme + DMSO + nitrocefin | Strong linear A490 slope |
| 2× No-enzyme | nitrocefin, no enzyme | Flat (background) |
| 2× Clavulanate @ 50 µM | known inhibitor | ≥ 50% inhibition vs vehicle |

Philip signs off → Chang runs Round 1. See [NITROCEFIN_ASSAY.md](pvjthomas/NITROCEFIN_ASSAY.md) for DMSO matching rules and library class notes.

---

## Open kickoff questions

- [ ] CFPS lysate **directly** in screen wells, or **BLB dilution prep** first?
- [ ] Nitrocefin stock concentration (brief typo: 20 µM vs 20 mM)
- [ ] Exact BLB recipe and pre-incubation time on hardware
- [ ] GFP reader instrument and pass/fail thresholds
- [ ] CFPS incubation time validated at event (30 min vs 6 h)
- [ ] Plate reader export format for `kinetics_r*.csv`

---

## One-line demo explanation

> We make TEM-1 cell-free, confirm it glows green, then mix each β-lactam compound with the lysate, add nitrocefin, and watch whether the red product forms fast (substrate / antibiotic) or slow (true inhibitor like clavulanate).
