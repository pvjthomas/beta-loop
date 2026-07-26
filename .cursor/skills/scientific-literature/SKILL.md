---
name: scientific-literature
description: >-
  Search biomedical literature via Europe PMC, PubMed (NCBI E-utilities), ChEMBL,
  Semantic Scholar, OpenAlex, and optional Paperclip. Use for TEM-1 beta-lactamase
  inhibitor Ki/IC50, nitrocefin assay priors, and compound literature curation.
---

# Scientific literature (β-Loop)

Prefer structured repository search before Paperclip map when extracting Ki/IC50 or nitrocefin assay parameters.

## Python tools (ADK agent)

| Tool | Sources |
|------|---------|
| `search_literature(query, source=...)` | `europe_pmc`, `pubmed`, `chembl`, `semantic_scholar`, `openalex`, plus Paperclip `pmc`, `biorxiv`, `proteins` |
| `list_literature_sources()` | All registered repositories |
| `search_chembl_activities(compound_name, target_query="TEM-1")` | Structured Ki/IC50 from ChEMBL |

## When to use which source

| Goal | Primary source |
|------|----------------|
| Biomedical full-text discovery | `europe_pmc` |
| PubMed citations / MeSH | `pubmed` |
| Structured Ki / IC50 | `chembl` or `search_chembl_activities()` |
| Cross-field + citations | `semantic_scholar`, `openalex` |
| Broad full-text map (quota-limited) | Paperclip `pmc` |

## K-Dense skills (reference)

Upstream skill library: `.cursor/skills/scientific-agent-skills/` (install via `bash scripts/install-scientific-skills.sh`).

- **paper-lookup** — REST patterns for PubMed, PMC, OpenAlex, Semantic Scholar
- **database-lookup** — ChEMBL, UniProt, and 78+ databases

## Environment (optional, improves rate limits)

- `NCBI_API_KEY` — PubMed E-utilities (10 req/s vs 3)
- `S2_API_KEY` — Semantic Scholar
- `OPENALEX_API_KEY` — OpenAlex polite pool
- `PAPERCLIP_API_KEY` — Paperclip only
