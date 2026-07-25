"""Paperclip literature tools for the β-Loop ADK agent."""

from __future__ import annotations

import json
from typing import Any

from agent.paths import LITERATURE_DIR, LITERATURE_SUMMARY_JSON


def _paperclip_client():
    from gxl_paperclip import PaperclipClient

    return PaperclipClient.from_env()


def load_literature_summary() -> dict[str, Any]:
    """Load pre-baked literature priors from data/literature_summary.json.

    Use this before Round 1 and as the default literature source. Faster and
    more reliable than live Paperclip searches during a screen turnaround.
    """
    if not LITERATURE_SUMMARY_JSON.exists():
        return {
            "status": "missing",
            "message": (
                f"No summary at {LITERATURE_SUMMARY_JSON}. "
                "Run Phase 0 Paperclip searches or hardcode a summary file."
            ),
            "known_inhibitors": [
                "clavulanic acid",
                "sulbactam",
                "tazobactam",
                "enmetazobactam",
            ],
            "expected_substrates_low_inhibition": [
                "ampicillin",
                "cephalexin",
                "penicillins",
                "cephalosporins",
            ],
            "assay_notes": {
                "typical_screen_conc_uM": 50,
                "pre_incubation_min": 10,
                "read_wavelength_nm": 490,
                "metric": "initial slope A490 vs time",
            },
        }
    return json.loads(LITERATURE_SUMMARY_JSON.read_text())


def search_literature(
    query: str,
    source: str = "pmc",
    limit: int = 10,
) -> dict[str, Any]:
    """Search biomedical literature via Paperclip (GXL).

    Prefer load_literature_summary() for Round 1. Use live search mainly after
    Round 1 for analogs, IC50 priors, or surprise hits.

    Args:
        query: Natural-language search query.
        source: Paperclip source flag, e.g. pmc, biorxiv, trials/us, proteins.
        limit: Maximum number of results (default 10, cap at 20).
    """
    limit = max(1, min(limit, 20))
    try:
        client = _paperclip_client()
        result = client.search(query, source=source, limit=limit)
        return {
            "status": "ok",
            "query": query,
            "source": source,
            "limit": limit,
            "result_id": result.result_id,
            "output": result.output,
        }
    except Exception as exc:  # noqa: BLE001 — surface tool errors to the agent
        summary = load_literature_summary()
        return {
            "status": "error",
            "query": query,
            "source": source,
            "error": str(exc),
            "fallback_summary": summary,
        }


def save_literature_search(
    query: str,
    source: str = "pmc",
    limit: int = 10,
    filename: str | None = None,
) -> dict[str, Any]:
    """Run a Paperclip search and save raw output under data/compound_literature/."""
    result = search_literature(query=query, source=source, limit=limit)
    if result.get("status") != "ok":
        return result

    LITERATURE_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = filename or f"{source}_{abs(hash(query)) % 10_000_000}.txt"
    out_path = LITERATURE_DIR / safe_name
    out_path.write_text(result.get("output", ""))
    result["saved_path"] = str(out_path)
    return result
