# Compound selection pipeline (Phase B)

ADK-generated artifacts for forward / reverse / bridge compound list generation.

| File | Purpose |
|------|---------|
| [`state.json`](state.json) | Combined pipeline state (git-tracked summaries) |
| [`plate_map_r1_draft.json`](plate_map_r1_draft.json) | Draft Round 1 plate — **not** for robot until sign-off |

**Promote to robot:** copy draft → `data/plate_map_r1.json` only after pvjthomas approval.

Run offline:

```bash
cd /path/to/zeon_hack
source .venv/bin/activate
python -c "
import sys; sys.path.insert(0, 'pvjthomas')
from agent.tools.selection import run_compound_selection_pipeline
print(run_compound_selection_pipeline())
"
```

Or via ADK: `adk run pvjthomas/agent` → "Run compound selection pipeline without live Paperclip."

See [`../agent/README.md`](../agent/README.md) and [`../../pvjthomas/COMPOUND_SELECTION.md`](../../pvjthomas/COMPOUND_SELECTION.md).
