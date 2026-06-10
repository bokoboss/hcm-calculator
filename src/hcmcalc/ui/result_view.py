"""Display-oriented helpers for auditable calculation results."""

from __future__ import annotations

from typing import Any


def compact_rows(values: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert scalar dictionary entries into compact display rows."""

    return [
        {"output": name, "value": value}
        for name, value in values.items()
        if not isinstance(value, (dict, list))
    ]
