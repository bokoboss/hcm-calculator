"""Runtime access to packaged UI fixture and preset data."""

from __future__ import annotations

from importlib.resources import files
from typing import Any

import yaml


DATA_PACKAGE = "hcmcalc.ui"
DATA_DIRECTORY = "data"


def load_packaged_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML resource packaged with the installed application."""

    resource = files(DATA_PACKAGE).joinpath(DATA_DIRECTORY, filename)
    with resource.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"Packaged resource is malformed: {filename}")
    return loaded
