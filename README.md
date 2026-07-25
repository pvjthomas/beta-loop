# β-Loop

Closed-loop TEM-1 β-lactamase inhibitor discovery for the [Zeon Systems AI for Science hackathon](https://luma.com/avi3l01q) (Track A).

An ADK agent prioritizes compounds (Paperclip literature + GNINA docking), a Zeon robot runs the nitrocefin assay, and results feed back into the next plate design — two rounds, real wet lab.

## Team

| Folder | Member | Role |
|--------|--------|------|
| [pvjthomas/](pvjthomas/) | pvjthomas | Bio / hardware / integration |
| [learsch/](learsch/) | learsch | _Assign at kickoff_ |
| [changhu/](changhu/) | changhu | _Assign at kickoff_ |

| Role | Focus |
|------|-------|
| Robotics | Zeon workflows (CFPS, GFP gate, screen) |
| Bio / hardware | QC gates, integration, demo |
| ML | Google ADK agent, Paperclip, analysis |

## Docs

- **[PLAN.md](PLAN.md)** — full project plan, timeline, plate designs
- **[ROLES.md](ROLES.md)** — ownership and handoffs
- **[REQUIREMENTS.md](REQUIREMENTS.md)** — Paperclip, ADK, Python deps

## Quick start

```bash
git clone https://github.com/pvjthomas/beta-loop.git
cd beta-loop

# Use GitHub noreply email for commits (avoids GH007 push errors)
git config user.email "pvjthomas@users.noreply.github.com"
git config user.name "pvjthomas"

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add PAPERCLIP_API_KEY, GOOGLE_API_KEY
```

Paperclip CLI (run in your terminal):

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
```

## Repo layout

```
pvjthomas/      # pvjthomas — bio / hardware / integration
learsch/        # learsch — personal workspace
changhu/        # changhu — personal workspace
data/           # compounds, plate maps, kinetics, literature (shared)
agent/          # ADK agent (TODO, shared)
analysis/       # kinetics + IC50 (TODO, shared)
workflows/      # Zeon robot workflows (TODO, shared)
```

## Scientific goal

> Which compounds meaningfully reduce TEM-1 β-lactamase activity, and what dose-response patterns do they show?

TargetMol β-lactam library (~95 compounds) · nitrocefin kinetic read @ A490 · two closed-loop screening rounds.
