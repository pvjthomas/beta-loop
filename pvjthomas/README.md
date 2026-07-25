# Philip (pvjthomas)

**Primary role:** Bio / hardware / integration + **compound selection (Task 2)** (see [ROLES.md](../ROLES.md))

**Compound selection plan:** **[COMPOUND_SELECTION.md](COMPOUND_SELECTION.md)** — forward (literature → library), reverse (library → literature), Tanimoto bridge, tiers → Round 1 plate.

**ML implements your selection rules** in `data/plate_map_r*.json` and the ADK agent — see [ml/CLOSED_LOOP.md](../ml/CLOSED_LOOP.md).

**Assay cheat sheet:** **[NITROCEFIN_ASSAY.md](NITROCEFIN_ASSAY.md)** — what to mix, order, controls, DMSO rule, scoring.

Personal workspace for scripts, notes, and artifacts you own. Shared deliverables still land in `data/` and `workflows/` at repo root; ML ships the team agent under `agent/` when ready.

### Experimental agent (pvjthomas only)

| Path | Purpose |
|------|---------|
| [`agent/`](agent/) | ADK closed-loop sandbox (`adk run pvjthomas/agent`) |
| [`analysis/`](analysis/) | Kinetics + plate helpers used by the sandbox |
| [`.claude/skills/paperclip/`](.claude/skills/paperclip/SKILL.md) | Paperclip skill stub for Claude Code |

## Your lead tasks

- [ ] **Compound selection** — see [COMPOUND_SELECTION.md](COMPOUND_SELECTION.md); library in [`data/compounds.csv`](../data/compounds.csv)
- [ ] Sign off **minimal validation plate** before Round 1
- [ ] Kickoff organizer questions
- [ ] GFP / activity gate thresholds
- [ ] Demo narrative & pitch
- [ ] QC on CFPS and screen runs
- [ ] Sign off R2 plate map
- [ ] Approve file schemas

## Your folder

Use this directory for:

- Assay QC notes and gate criteria
- Kickoff Q&A answers from organizers
- Demo script and pitch slides (drafts)
- Integration notes (robot ↔ files ↔ agent)

## Handoffs you receive

- **H3:** `round_summary_r1.json` + proposed `plate_map_r2.json` → sign off R2
- **H4:** IC50 table, heatmaps, agent rationale → write final pitch

## Handoffs you send

- Gate pass/fail decision before screen slots
- Final demo script to team
