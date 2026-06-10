"""Repository-relative paths for UI schematic assets."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SEGMENT_SCHEMATIC_DIRECTORY = (
    ROOT / "assets" / "schematics" / "two_lane" / "left_hand"
)
SEGMENT_SCHEMATIC_FILENAMES = {
    "passing_constrained": "passing_constrained.png",
    "passing_zone": "passing_zone.png",
    "passing_lane": "passing_lane.png",
}


def get_segment_schematic_path(segment_type: str) -> Path | None:
    """Return the existing schematic path for a supported segment type."""

    filename = SEGMENT_SCHEMATIC_FILENAMES.get(segment_type)
    if filename is None:
        return None

    schematic_path = SEGMENT_SCHEMATIC_DIRECTORY / filename
    return schematic_path if schematic_path.is_file() else None
