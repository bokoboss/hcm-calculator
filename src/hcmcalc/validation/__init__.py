"""Validation fixture helpers."""

from pathlib import Path
from typing import Any

import yaml


def load_yaml_fixture(path: str | Path) -> dict[str, Any]:
    """Load a YAML validation fixture."""

    with Path(path).open("r", encoding="utf-8") as fixture_file:
        loaded = yaml.safe_load(fixture_file)
    return loaded or {}
