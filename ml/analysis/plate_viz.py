"""Render nitrocefin plate map JSON as PNG via wellmap."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import wellmap

DEFAULT_COLS_BY_ASSAY = {
    "dose_response": ["compound_id", "concentration_uM"],
}
DEFAULT_COLS = ["role", "compound_id"]


def plate_map_to_df(plate_map: dict) -> pd.DataFrame:
    """Flatten plate_map['wells'] into a tidy DataFrame for wellmap.show_df()."""
    rows: list[dict] = []
    for well_id, well in plate_map.get("wells", {}).items():
        compound_id = well.get("compound_id")
        row = {
            "well": well_id,
            "role": well.get("role"),
            "compound_id": compound_id if compound_id is not None else "—",
            "concentration_uM": well.get("concentration_uM"),
            "bucket": well.get("bucket"),
        }
        if "replicate" in well:
            row["replicate"] = well["replicate"]
        rows.append(row)
    return pd.DataFrame(rows)


def _default_output_path(json_path: Path) -> Path:
    if json_path.name == "plate_map.json":
        return json_path.with_name("plate_map.png")
    return json_path.with_suffix(".png")


def _default_cols(plate_map: dict) -> list[str]:
    assay_type = plate_map.get("assay_type", "")
    return DEFAULT_COLS_BY_ASSAY.get(assay_type, DEFAULT_COLS)


def _build_title(plate_map: dict) -> str:
    parts: list[str] = []
    if label := plate_map.get("version_label"):
        parts.append(str(label))
    if assay_type := plate_map.get("assay_type"):
        parts.append(str(assay_type))
    if notes := plate_map.get("layout_notes"):
        note = str(notes)
        if len(note) > 120:
            note = note[:117] + "..."
        parts.append(note)
    return " · ".join(parts) if parts else "Plate map"


def render_plate_map(
    plate_map: dict,
    output_path: Path,
    *,
    cols: list[str] | None = None,
) -> Path:
    """Render a plate map dict to PNG using wellmap.show_df()."""
    df = plate_map_to_df(plate_map)
    if df.empty:
        raise ValueError("Plate map has no wells to render")

    plot_cols = cols if cols is not None else _default_cols(plate_map)
    fig = wellmap.show_df(df, cols=plot_cols)
    title = _build_title(plate_map)
    if title:
        fig.suptitle(title, fontsize=10, y=1.02)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return output_path


def load_and_render(
    path: str | Path,
    output_path: str | Path | None = None,
    *,
    cols: list[str] | None = None,
) -> Path:
    """Load plate map JSON and write PNG alongside it by default."""
    json_path = Path(path)
    plate_map = json.loads(json_path.read_text())
    out = Path(output_path) if output_path is not None else _default_output_path(json_path)
    return render_plate_map(plate_map, out, cols=cols)
