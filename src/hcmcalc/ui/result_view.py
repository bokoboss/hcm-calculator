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


def result_summary_items(
    primary_label: str,
    primary_value: str,
    secondary_metrics: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Return ordered display items for a result summary panel."""

    return [
        {"label": primary_label, "value": primary_value},
        *secondary_metrics,
    ]


def render_los_hero(
    *,
    label: str,
    level_of_service: str,
    supporting_label: str | None = None,
    supporting_value: str | None = None,
) -> None:
    """Render a consistent LOS-forward result hero."""

    import streamlit as st

    foreground, background = los_colors(level_of_service)
    supporting_line = ""
    if supporting_label is not None and supporting_value is not None:
        supporting_line = (
            f'<div class="los-hero-density">'
            f'{supporting_label} <strong>{supporting_value}</strong>'
            f"</div>"
        )
    st.markdown(
        f"""
        <div class="los-hero" style="--los-color: {foreground};
             --los-background: {background};">
            <div class="los-hero-label">{label}</div>
            <div class="los-hero-grade">LOS {level_of_service}</div>
            {supporting_line}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_summary_panel(
    *,
    primary_label: str,
    primary_value: str,
    secondary_metrics: list[dict[str, str]],
    primary_kind: str = "metric",
    hero_supporting_label: str | None = None,
    hero_supporting_value: str | None = None,
    notes: list[str] | None = None,
    warnings: list[str] | None = None,
) -> None:
    """Render the shared post-run calculator result summary."""

    import streamlit as st

    if primary_kind == "los":
        render_los_hero(
            label=primary_label,
            level_of_service=primary_value,
            supporting_label=hero_supporting_label,
            supporting_value=hero_supporting_value,
        )
        items = secondary_metrics
    else:
        items = result_summary_items(primary_label, primary_value, secondary_metrics)

    for index in range(0, len(items), 2):
        columns = st.columns(2)
        for column, metric in zip(columns, items[index : index + 2]):
            column.metric(metric["label"], metric["value"])

    for note in notes or []:
        st.caption(note)
    for warning in warnings or []:
        st.warning(warning)
