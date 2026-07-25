# Project Requirements

Setup checklist for β-Loop (Track A). Complete **Phase 0** items before Saturday kickoff.

---

## 1. Paperclip — literature search

[Paperclip](https://paperclip.gxl.ai/) indexes 11M+ full-text papers, clinical trials, FDA docs, ChEMBL, PDB, and UniProt. We use it **before Round 1** to ground compound prioritization in known TEM-1 / β-lactamase inhibitor literature.

### Install (choose one)

#### Option A: CLI + agent skill (recommended for ML person)

Run in **your terminal** (not via an agent — sign-in opens a browser):

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
```

Verify:

```bash
paperclip config
# Server:  https://paperclip.gxl.ai
# Auth:    ✓ you@example.com
# Config:  ~/.paperclip
```

#### Option B: Python SDK (for ADK function tool)

Included in `requirements.txt`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Authenticate with an API key from [paperclip.gxl.ai](https://paperclip.gxl.ai/) (API Keys section):

```bash
export PAPERCLIP_API_KEY="pk_..."
```

Or use credentials saved by `paperclip login` (`~/.paperclip/credentials.json`).

#### Option C: MCP server (for Cursor / Claude Code)

No local install. Add to your MCP client config:

```
https://paperclip.gxl.ai/mcp
```

See [Paperclip docs](https://paperclip.gxl.ai/docs) for Cursor, Claude Code, and other client setup guides.

### Hackathon usage

**Owner:** ML (wrap as ADK function tool `search_literature()`)

Example queries to run in Phase 0:

```bash
paperclip search "TEM-1 beta-lactamase inhibitor clavulanate sulbactam tazobactam" -n 20
paperclip search "nitrocefin beta-lactamase assay IC50" -n 10
paperclip search "beta-lactam antibiotic substrate vs inhibitor TEM-1" -n 10
```

For synthesis across multiple papers:

```bash
paperclip map --from s_<result_id> "What IC50 values and assay conditions were used for TEM-1 inhibitors?"
```

Save outputs to `data/literature/` for the agent to reference when designing Round 1 and Round 2 plates.

### Integration with ADK agent

Replace generic web search with a dedicated tool:

```python
# agent/tools/literature.py (stub)
from gxl_paperclip import PaperclipClient

def search_literature(query: str, limit: int = 10) -> str:
    """Search scientific literature for TEM-1 inhibitor context."""
    client = PaperclipClient.from_env()
    result = client.search(query, limit=limit, source="pmc")
    return result.output
```

Register as an ADK function tool on the `LlmAgent` decision-maker.

---

## 2. Google ADK — agent framework

**Owner:** ML

```bash
pip install google-adk
```

- `LlmAgent` — reads round results, picks compounds, emits plate layout
- `LoopAgent` — Round 1 → Round 2 with session state
- Function tools: `prioritize_compounds`, `analyze_kinetics`, `design_next_plate`, **`search_literature`** (Paperclip)

Docs: [Google Agent Development Kit](https://google.github.io/adk-docs/)

---

## 3. Cheminformatics & analysis

**Owner:** ML

| Package | Purpose |
|---------|---------|
| `rdkit` | β-lactam substructure tags, fingerprints, similarity |
| `numpy`, `pandas`, `scipy` | Kinetics slopes, IC50 fitting |

```bash
pip install -r requirements.txt
```

---

## 4. Docking (optional, Phase 0)

**Owner:** ML

GNINA is not on PyPI — install binary separately if used:

- [GNINA](https://github.com/gnina/gnina) — CNN-scored docking vs TEM-1 (PDB 1JQL)
- Batch dock all 95 compounds → merge scores into `data/compounds.csv`

DiffDock and Boltz-2 are optional stretch goals per hackathon brief.

---

## 5. Zeon robotics

**Owner:** Robotics

- Zeon GitHub repo (TBA at event) — robotic skills and example workflows
- Simulation environment for `cfps`, `gfp_read`, `screen` workflows before hardware

---

## 6. Environment variables

| Variable | Required by | Notes |
|----------|-------------|-------|
| `PAPERCLIP_API_KEY` | Paperclip SDK | Or use `paperclip login` credentials |
| `GOOGLE_API_KEY` | Google ADK | Gemini / ADK backend |

Add a local `.env` (do not commit):

```bash
PAPERCLIP_API_KEY=pk_...
GOOGLE_API_KEY=...
```

---

## Phase 0 install checklist

| Who | Task | Done |
|-----|------|:----:|
| ML | `pip install -r requirements.txt` | ☐ partial |
| ML | Paperclip CLI or API key configured | ☑ |
| ML | Run TEM-1 literature searches → `data/literature/` | ☐ |
| ML | ADK agent with `search_literature` tool | ☐ |
| ML | GNINA batch dock (optional) | ☐ |
| Robotics | Zeon sim + workflow drafts | ☐ |
| You | `.env` template shared with team (secrets excluded) | ☑ |

---

## Quick verify (all tools)

```bash
source .venv/bin/activate
python -c "from gxl_paperclip import PaperclipClient; print('paperclip ok')"
paperclip search "TEM-1 beta-lactamase inhibitor" -n 3
python -c "import google.adk; print('adk ok')"
python -c "from rdkit import Chem; print('rdkit ok')"
```
