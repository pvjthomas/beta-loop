# Team Roles & Handoffs

Quick reference for who does what during the hackathon.

## Ownership matrix

| Task | Robotics | You | ML |
|------|:--------:|:---:|:--:|
| Zeon workflow authoring | **lead** | review | — |
| Hardware booking | **lead** | assist | — |
| CFPS / screen execution | **lead** | QC | — |
| Plate reader export → CSV | **lead** | — | consume |
| Kickoff organizer questions | — | **lead** | — |
| GFP / activity gate thresholds | — | **lead** | implement |
| Demo narrative & pitch | assist | **lead** | assist |
| ADK agent & LoopAgent | — | review | **lead** |
| Kinetics analysis & IC50 | — | review | **lead** |
| Paperclip literature search | — | — | **lead** |
| GNINA / compound priors | — | — | **lead** |
| File schemas | review | **approve** | **lead** |
| R2 plate map sign-off | review | **approve** | **lead** |

## Handoff points

### H0: Paperclip → ML (Phase 0, before hackathon)
- **Artifact:** `data/literature/*.txt` + `data/literature_summary.json`
- **Verify:** known inhibitors listed, assay conc/timing documented

### H1: ML → Robotics (before each screen)
- **Artifact:** `data/plate_map_r{N}.json`
- **Verify:** well count ≤ 96, controls present, no nitrocefin, DMSO matched

### H2: Robotics → ML (after each screen)
- **Artifact:** `data/kinetics_r{N}.csv`
- **SLA:** ML starts analysis within 5 min of file landing

### H3: ML → Team (after R1 analysis)
- **Artifact:** `data/round_summary_r1.json` + proposed `plate_map_r2.json`
- **SLA:** 30-min team sync before R2 reagents touched

### H4: ML → You (before demo)
- **Artifact:** IC50 table, R1/R2 heatmaps, agent rationale text
- **You** writes final pitch from these

## When blocked

| Blocker | Robotics does | ML does | You do |
|---------|---------------|---------|--------|
| Incubator wait | Polish screen workflow | Test on fake data | Compound QA |
| GFP gate fail | Debug seal/temp/pipetting | — | Escalate to organizers |
| Reader queue | Prep next workflow | Dashboard | Slides |
| R1 flat curves | — | Check normalization code | Debug assay conditions |

## Sync schedule

- **11:00** — Kickoff (all)
- **Every 2h** — 5-min standup (all)
- **~16:20** — R1 review + R2 lock (all, mandatory)
- **21:00** — Demo prep check (all)
- **Sunday 12:00** — Final demo rehearsal (all)
