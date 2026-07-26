"""Render nitrocefin plate map JSON as PNG with typed colors and well labels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from wellmap.util import ij_from_well

PLATE_ROWS = 8
PLATE_COLS = 12
EMPTY_COLOR = "#F3F4F6"

ColorMode = Literal["sample_type", "compound"]

SAMPLE_TYPE_COLORS: dict[str, str] = {
    "vehicle": "#9CA3AF",
    "no_tem1": "#F59E0B",
    "pos_ctrl": "#DC2626",
    "tier1_inhibitor": "#2563EB",
    "substrate_control": "#16A34A",
    "diverse_pick": "#9333EA",
    "dose_response": "#0E7490",
    "sample": "#64748B",
    "control": "#9CA3AF",
}

SAMPLE_TYPE_LABELS: dict[str, str] = {
    "vehicle": "Vehicle (DMSO)",
    "no_tem1": "No TEM-1",
    "pos_ctrl": "Positive control",
    "tier1_inhibitor": "Tier-1 inhibitor",
    "substrate_control": "Substrate control",
    "diverse_pick": "Diverse pick",
    "dose_response": "Dose response",
    "sample": "Sample",
    "control": "Control",
}

CONTROL_GROUP_LABELS: dict[str, str] = {
    "vehicle": "Vehicle (DMSO)",
    "no_tem1": "No TEM-1",
    "pos_ctrl": "Positive control",
}

CONTROL_WELL_LABELS: dict[str, str] = {
    "vehicle": "VEH",
    "no_tem1": "noTEM1",
    "pos-ctrl-clavaculin": "POS",
}

# Distinct hues for compound-level coloring (supports 24+ unique groups).
COMPOUND_PALETTE: list[str] = [
    "#2563EB",
    "#DC2626",
    "#16A34A",
    "#9333EA",
    "#EA580C",
    "#0891B2",
    "#CA8A04",
    "#DB2777",
    "#059669",
    "#7C3AED",
    "#B45309",
    "#0D9488",
    "#4F46E5",
    "#E11D48",
    "#65A30D",
    "#C026D3",
    "#0284C7",
    "#D97706",
    "#10B981",
    "#6366F1",
    "#F43F5E",
    "#84CC16",
    "#8B5CF6",
    "#14B8A6",
]


def _choose_foreground_color(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    grey = r * 0.299 + g * 0.587 + b * 0.114
    return "black" if grey > 0.588 else "white"


def _sample_type(well: dict) -> str:
    role = well.get("role")
    if role == "vehicle":
        return "vehicle"
    if role == "no_tem1":
        return "no_tem1"
    if role == "pos-ctrl-clavaculin":
        return "pos_ctrl"
    if bucket := well.get("bucket"):
        if bucket in SAMPLE_TYPE_COLORS:
            return bucket
        if bucket == "control":
            return "control"
    if role == "sample":
        return "sample"
    return role or "sample"


def _compound_group(well: dict) -> str:
    if compound_id := well.get("compound_id"):
        return str(compound_id)
    role = well.get("role")
    if role == "vehicle":
        return "vehicle"
    if role == "no_tem1":
        return "no_tem1"
    if role == "pos-ctrl-clavaculin":
        return "pos_ctrl"
    return role or "unknown"


def _well_label(well: dict) -> str:
    role = well.get("role")
    if role in CONTROL_WELL_LABELS:
        return CONTROL_WELL_LABELS[role]
    if compound_id := well.get("compound_id"):
        return str(compound_id)
    return ""


def plate_map_to_df(plate_map: dict) -> pd.DataFrame:
    """Flatten plate_map['wells'] into a tidy DataFrame."""
    rows: list[dict] = []
    for well_id, well in plate_map.get("wells", {}).items():
        compound_id = well.get("compound_id")
        row = {
            "well": well_id,
            "role": well.get("role"),
            "sample_type": _sample_type(well),
            "compound_group": _compound_group(well),
            "label": _well_label(well),
            "compound_id": compound_id if compound_id is not None else "—",
            "concentration_uM": well.get("concentration_uM"),
            "bucket": well.get("bucket"),
        }
        if "replicate" in well:
            row["replicate"] = well["replicate"]
        row_i, col_j = ij_from_well(well_id)
        row["row_i"] = row_i
        row["col_j"] = col_j
        rows.append(row)
    return pd.DataFrame(rows)


def _default_output_path(json_path: Path, *, color_by: ColorMode = "sample_type") -> Path:
    if json_path.name == "plate_map.json":
        if color_by == "compound":
            return json_path.with_name("plate_map_by_compound.png")
        return json_path.with_name("plate_map.png")
    if color_by == "compound":
        return json_path.with_name(f"{json_path.stem}_by_compound.png")
    return json_path.with_suffix(".png")


def _build_title(plate_map: dict, *, color_by: ColorMode) -> str:
    parts: list[str] = []
    if label := plate_map.get("version_label"):
        parts.append(str(label))
    if assay_type := plate_map.get("assay_type"):
        parts.append(str(assay_type))
    parts.append("by sample type" if color_by == "sample_type" else "by compound")
    if notes := plate_map.get("layout_notes"):
        note = str(notes)
        if len(note) > 100:
            note = note[:97] + "..."
        parts.append(note)
    return " · ".join(parts) if parts else "Plate map"


def _colors_for_sample_types(present_types: list[str]) -> tuple[list[str], dict[str, str]]:
    colors = dict(SAMPLE_TYPE_COLORS)
    fallback_palette = ["#EC4899", "#14B8A6", "#EAB308", "#6366F1"]
    extra_types = [t for t in present_types if t not in colors]
    for idx, sample_type in enumerate(extra_types):
        colors[sample_type] = fallback_palette[idx % len(fallback_palette)]

    type_order = [t for t in SAMPLE_TYPE_COLORS if t in present_types]
    type_order.extend(t for t in present_types if t not in type_order)
    return type_order, colors


def _colors_for_compounds(present_groups: list[str]) -> tuple[list[str], dict[str, str]]:
    group_order = list(dict.fromkeys(present_groups))
    colors = {
        group: COMPOUND_PALETTE[idx % len(COMPOUND_PALETTE)]
        for idx, group in enumerate(group_order)
    }
    return group_order, colors


def _legend_label(group: str, *, color_by: ColorMode) -> str:
    if color_by == "sample_type":
        return SAMPLE_TYPE_LABELS.get(group, group.replace("_", " ").title())
    if group in CONTROL_GROUP_LABELS:
        return CONTROL_GROUP_LABELS[group]
    return group


def _render_colored_plate(
    df: pd.DataFrame,
    *,
    color_by: ColorMode = "sample_type",
    title: str | None = None,
) -> plt.Figure:
    """Draw a 96-well plate colored by sample type or compound group."""
    color_column = "sample_type" if color_by == "sample_type" else "compound_group"
    present_groups = list(dict.fromkeys(df[color_column].tolist()))

    if color_by == "sample_type":
        group_order, colors = _colors_for_sample_types(present_groups)
        legend_title = "Sample type"
    else:
        group_order, colors = _colors_for_compounds(present_groups)
        legend_title = "Compound"

    group_to_idx = {group: idx for idx, group in enumerate(group_order)}

    matrix = np.full((PLATE_ROWS, PLATE_COLS), np.nan)
    labels = [["" for _ in range(PLATE_COLS)] for _ in range(PLATE_ROWS)]

    for _, row in df.iterrows():
        i = int(row["row_i"])
        j = int(row["col_j"])
        matrix[i, j] = group_to_idx[row[color_column]]
        labels[i][j] = row["label"]

    cmap = ListedColormap([colors[group] for group in group_order])
    legend_cols = 1 if len(group_order) <= 12 else 2
    fig_width = 13 if legend_cols == 1 else 15
    fig, ax = plt.subplots(figsize=(fig_width, 5.5))
    ax.imshow(
        matrix,
        cmap=cmap,
        vmin=0,
        vmax=max(len(group_order) - 1, 1),
        origin="upper",
        aspect="equal",
    )

    ax.set_xticks(range(PLATE_COLS))
    ax.set_xticklabels(range(1, PLATE_COLS + 1))
    ax.set_yticks(range(PLATE_ROWS))
    ax.set_yticklabels(list("ABCDEFGH"))
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    ax.tick_params(length=0)
    ax.set_xticks(np.arange(-0.5, PLATE_COLS, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, PLATE_ROWS, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.set_facecolor(EMPTY_COLOR)

    for i in range(PLATE_ROWS):
        for j in range(PLATE_COLS):
            label = labels[i][j]
            if not label or np.isnan(matrix[i, j]):
                continue
            bg = colors[group_order[int(matrix[i, j])]]
            ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                fontsize=5.5,
                color=_choose_foreground_color(bg),
                weight="bold",
            )

    legend_handles = [
        Patch(
            facecolor=colors[group],
            edgecolor="white",
            label=_legend_label(group, color_by=color_by),
        )
        for group in group_order
    ]
    ax.legend(
        handles=legend_handles,
        title=legend_title,
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=True,
        fontsize=7 if color_by == "compound" else 8,
        title_fontsize=9,
        ncol=legend_cols,
    )

    if title:
        fig.suptitle(title, fontsize=10, y=1.02)

    fig.tight_layout()
    return fig


def render_plate_map(
    plate_map: dict,
    output_path: Path,
    *,
    color_by: ColorMode = "sample_type",
    cols: list[str] | None = None,
) -> Path:
    """Render a plate map dict to PNG with well labels."""
    del cols  # kept for CLI compatibility
    df = plate_map_to_df(plate_map)
    if df.empty:
        raise ValueError("Plate map has no wells to render")

    fig = _render_colored_plate(
        df,
        color_by=color_by,
        title=_build_title(plate_map, color_by=color_by),
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def load_and_render(
    path: str | Path,
    output_path: str | Path | None = None,
    *,
    color_by: ColorMode = "sample_type",
    cols: list[str] | None = None,
) -> Path:
    """Load plate map JSON and write PNG alongside it by default."""
    json_path = Path(path)
    plate_map = json.loads(json_path.read_text())
    out = (
        Path(output_path)
        if output_path is not None
        else _default_output_path(json_path, color_by=color_by)
    )
    return render_plate_map(plate_map, out, color_by=color_by, cols=cols)
