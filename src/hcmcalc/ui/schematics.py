"""Packaged paths for UI schematic assets."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


ASSET_PACKAGE = "hcmcalc.ui"
ASSET_DIRECTORY = ("assets", "two_lane")
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

    resource = files(ASSET_PACKAGE).joinpath(*ASSET_DIRECTORY, filename)
    if not resource.is_file():
        return None
    return Path(resource)
