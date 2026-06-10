"""Display-oriented helpers for auditable calculation results."""

from __future__ import annotations

from typing import Any


LOS_COLORS = {
    "A": ("#17643a", "#e8f4ec"),
    "B": ("#39723e", "#eef6e9"),
    "C": ("#8a5a00", "#fff4d6"),
    "D": ("#a44700", "#ffead8"),
    "E": ("#a52a2a", "#fde8e7"),
    "F": ("#721c24", "#f5dddd"),
}


def compact_rows(values: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert scalar dictionary entries into compact display rows."""

    return [
        {"output": name, "value": value}
        for name, value in values.items()
        if not isinstance(value, (dict, list))
    ]


def los_colors(level_of_service: str) -> tuple[str, str]:
    """Return professional foreground and background colors for an LOS grade."""

    return LOS_COLORS.get(str(level_of_service).upper(), ("#374151", "#f3f4f6"))


def format_display_metric(
    metric_name: str,
    metric: dict[str, Any],
    unit_system: str,
) -> str:
    """Format a primary result metric consistently for the worksheet."""

    value = float(metric["value"])
    if metric_name in {"average_speed", "free_flow_speed"}:
        decimals = 1
    elif metric_name == "follower_density":
        decimals = 2 if unit_system.lower() == "metric" else 1
    elif metric_name == "percent_followers":
        decimals = 1
    else:
        decimals = 0
    return f'{value:.{decimals}f} {metric["unit"]}'
