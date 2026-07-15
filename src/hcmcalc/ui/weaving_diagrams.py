"""Presentation-only configuration references for the weaving worksheet.

The qualified calculation contract intentionally remains limited to one-sided and
two-sided configuration.  These helpers derive a display subtype from already
entered geometry; they never feed a calculation, saved-engine input, or
calculation fingerprint.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


ASSET_PACKAGE = "hcmcalc.ui"
ASSET_DIRECTORY = ("assets", "weaving")
_FILENAMES = {
    "one_sided_major": "one_sided_weave.png",
    "one_sided_ramp": "one_sided_weave.png",
    "two_sided": "two_sided_weave.png",
}


@dataclass(frozen=True)
class WeavingDiagram:
    """A resolved, accessible diagram and its presentation-only subtype."""

    subtype: str
    filename: str
    path: Path


def get_weaving_diagram_subtype(
    configuration: str | None,
    number_of_weaving_lanes: int | None,
) -> str | None:
    """Map the qualified geometry values to a deterministic display subtype."""

    if configuration == "two_sided" and number_of_weaving_lanes == 0:
        return "two_sided"
    if configuration == "one_sided" and number_of_weaving_lanes == 3:
        return "one_sided_major"
    if configuration == "one_sided" and number_of_weaving_lanes == 2:
        return "one_sided_ramp"
    return None


def get_weaving_diagram(subtype: str | None) -> WeavingDiagram | None:
    """Resolve a packaged diagram without any checkout- or network dependency."""

    filename = _FILENAMES.get(subtype or "")
    if filename is None:
        return None
    resource = files(ASSET_PACKAGE).joinpath(*ASSET_DIRECTORY, filename)
    if not resource.is_file():
        return None
    return WeavingDiagram(str(subtype), filename, Path(resource))
