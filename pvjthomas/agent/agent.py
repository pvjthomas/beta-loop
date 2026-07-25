"""β-Loop ADK agent — closed-loop TEM-1 inhibitor screening."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

from agent.prompts import COORDINATOR_INSTRUCTION, ROUND1_INSTRUCTION, ROUND2_INSTRUCTION
from agent.tools.compounds import load_compounds, prioritize_compounds
from agent.tools.kinetics_tool import analyze_kinetics, load_round_summary
from agent.tools.literature import (
    load_literature_summary,
    save_literature_search,
    search_literature,
)
from agent.tools.plates import design_next_plate, load_plate_map

REPO_ROOT = Path(__file__).resolve().parents[2]

# Load env from pvjthomas/agent/ then repo root (Vertex + Paperclip).
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(REPO_ROOT / ".env")

MODEL = "gemini-2.5-flash"

# Shared tools available to all screening agents.
LITERATURE_TOOLS = [
    load_literature_summary,
    search_literature,
    save_literature_search,
]
COMPOUND_TOOLS = [load_compounds, prioritize_compounds]
ANALYSIS_TOOLS = [analyze_kinetics, load_round_summary]
PLATE_TOOLS = [load_plate_map, design_next_plate]

round1_agent = Agent(
    model=MODEL,
    name="round1_planner",
    description="Plans Round 1 using literature priors and the signed-off plate map.",
    instruction=ROUND1_INSTRUCTION,
    tools=[*LITERATURE_TOOLS, *COMPOUND_TOOLS, load_plate_map],
)

round2_agent = Agent(
    model=MODEL,
    name="round2_designer",
    description="Analyzes Round 1 kinetics and designs the Round 2 dose-response plate.",
    instruction=ROUND2_INSTRUCTION,
    tools=[*LITERATURE_TOOLS, *ANALYSIS_TOOLS, *PLATE_TOOLS],
)

root_agent = Agent(
    model=MODEL,
    name="beta_loop_coordinator",
    description=(
        "Coordinates the β-Loop closed-loop TEM-1 inhibitor screen: "
        "literature → Round 1 plate → kinetics analysis → Round 2 design."
    ),
    instruction=COORDINATOR_INSTRUCTION,
    tools=[
        *LITERATURE_TOOLS,
        *COMPOUND_TOOLS,
        *ANALYSIS_TOOLS,
        *PLATE_TOOLS,
    ],
    sub_agents=[round1_agent, round2_agent],
)
