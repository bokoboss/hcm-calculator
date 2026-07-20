"""Shared Streamlit layout helpers for compact calculator pages."""

from __future__ import annotations

from typing import Any

import streamlit as st

from hcmcalc.ui.supported_workflows import (
    AUDIT_EXPANDER_LABEL,
    CALCULATION_DETAILS_LABEL,
    EXPORT_REPORT_LABEL,
    PROJECT_LOAD_LABEL,
    PROJECT_OUTPUT_LABEL,
    STARTING_VALUES_CAPTION,
    STARTING_VALUES_LABEL,
    VALIDATION_EXPANDER_LABEL,
)


def render_page_header(title: str, caption: str, status: str | None = None) -> None:
    """Render the standard compact page heading."""

    st.title(title)
    st.caption(caption)
    if status:
        st.caption(status)


def render_calculator_shell() -> tuple[Any, Any]:
    """Return the shared input and result columns for calculator pages."""

    return st.columns([1.05, 0.95], gap="large")


def render_section_label(label: str) -> None:
    """Render a consistent compact section label."""

    st.markdown(f"**{label}**")


def render_starting_values_section(label: str | None = None) -> None:
    """Render the common optional-defaults caption."""

    st.caption(STARTING_VALUES_CAPTION)


def render_validation_basis_and_limitations(
    *,
    validation_basis: str,
    supported_scope: str,
    not_supported: str,
) -> None:
    """Render the standard collapsed validation and limitation summary."""

    with st.expander(VALIDATION_EXPANDER_LABEL, expanded=False):
        st.markdown("**Validation basis**")
        st.caption(validation_basis)
        st.markdown("**Current supported scope**")
        st.caption(supported_scope)
        st.markdown("**Not supported**")
        st.caption(not_supported)


def render_project_load_section(render_controls: Any, label: str | None = None) -> None:
    """Render a compact project load section around existing load controls."""

    with st.expander(label or PROJECT_LOAD_LABEL, expanded=False):
        render_controls()


def render_project_output_section(
    caption: str, render_controls: Any, label: str | None = None
) -> None:
    """Render a compact project output section around existing save controls."""

    st.markdown(f"**{label or PROJECT_OUTPUT_LABEL}**")
    st.caption(caption)
    render_controls()


def render_export_report_section_container(
    render_controls: Any, label: str | None = None
) -> None:
    """Render the standard collapsed export/report section."""

    with st.expander(label or EXPORT_REPORT_LABEL, expanded=False):
        render_controls()


__all__ = [
    "AUDIT_EXPANDER_LABEL",
    "CALCULATION_DETAILS_LABEL",
    "EXPORT_REPORT_LABEL",
    "PROJECT_LOAD_LABEL",
    "PROJECT_OUTPUT_LABEL",
    "STARTING_VALUES_LABEL",
    "VALIDATION_EXPANDER_LABEL",
    "render_calculator_shell",
    "render_export_report_section_container",
    "render_page_header",
    "render_project_load_section",
    "render_project_output_section",
    "render_section_label",
    "render_starting_values_section",
    "render_validation_basis_and_limitations",
]
