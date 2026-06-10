"""Single-page Streamlit viewer and manual single-segment calculator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from hcmcalc.cli import find_case, load_input_file, result_to_dict, run_case
from hcmcalc.core import HCMCalcError
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.result_view import compact_rows, format_display_metric, los_colors
from hcmcalc.ui.units import DEFAULT_UNIT_SYSTEM, display_outputs, manual_defaults


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "example_inputs.yaml"
IMPLEMENTED_CASE_IDS = (
    "TLH-CH15-001",
    "TLH-CH15-002",
    "TLH-CH15-003",
    "TLH-CH15-004",
)
SCOPE_NOTICE = (
    "Current scope: one straight two-lane highway segment, with level and limited "
    "mountainous terrain support."
)
LIMITATIONS_FOOTER = (
    "Current limitations: example-scoped validation, selected mountainous "
    "combinations, and no downstream passing-lane effects."
)


def apply_ui_styles() -> None:
    """Apply restrained presentation styles without changing app behavior."""

    st.markdown(
        """
        <style>
        button[data-testid="stBaseButton-primaryFormSubmit"] {
            background-color: #245b86;
            border-color: #245b86;
        }
        button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
            background-color: #1d4a6e;
            border-color: #1d4a6e;
        }
        .los-hero {
            border: 1px solid var(--los-color);
            border-left-width: 0.45rem;
            border-radius: 0.55rem;
            background: var(--los-background);
            padding: 1.15rem 1.35rem;
            margin-bottom: 1rem;
        }
        .los-hero-label {
            color: #4b5563;
            font-size: 0.8rem;
            font-weight: 650;
            letter-spacing: 0.08em;
            margin-bottom: 0.15rem;
            text-transform: uppercase;
        }
        .los-hero-grade {
            color: var(--los-color);
            font-size: 3.4rem;
            font-weight: 750;
            line-height: 1;
        }
        .los-hero-density {
            color: #374151;
            font-size: 1rem;
            margin-top: 0.55rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_list(title: str, values: list[str], empty_message: str) -> None:
    """Render an audit list with a clear empty state."""

    st.subheader(title)
    if values:
        for value in values:
            st.markdown(f"- {value}")
    else:
        st.caption(empty_message)


def render_result(result_id: str, result_data: dict[str, Any]) -> None:
    """Render an auditable calculation result."""

    outputs = result_data["outputs"]
    segments = outputs.get("segments")
    full_result = {"result_id": result_id, **result_data}
    full_result_json = json.dumps(full_result, indent=2)

    st.subheader("Key result summary")
    summary_columns = st.columns(3)
    summary_columns[0].metric("Result", result_id)
    summary_columns[1].metric("Method", result_data["method"])
    summary_columns[2].metric("Facility type", result_data["facility_type"])

    st.subheader("Outputs")
    scalar_outputs = compact_rows(outputs)
    if scalar_outputs:
        st.dataframe(scalar_outputs, hide_index=True, use_container_width=True)
    else:
        st.caption("No scalar outputs were returned.")

    if isinstance(segments, list):
        st.subheader("Segment outputs")
        st.dataframe(segments, hide_index=True, use_container_width=True)

    render_list("Assumptions", result_data["assumptions"], "No assumptions reported.")
    render_list("Warnings", result_data["warnings"], "No warnings reported.")

    with st.expander("Intermediate values"):
        st.dataframe(
            result_data["intermediate_values"],
            hide_index=True,
            use_container_width=True,
        )

    with st.expander("Full result JSON"):
        st.json(full_result)

    st.download_button(
        "Download full result JSON",
        data=full_result_json,
        file_name=f"{result_id}-result.json",
        mime="application/json",
    )


def render_validated_case_viewer() -> None:
    """Render the implemented validation fixture cases."""

    st.warning(
        "Validated cases preserve the Example Problems 1 through 4 baseline."
    )

    try:
        fixture = load_input_file(FIXTURE_PATH)
        available_case_ids = [
            case_id
            for case_id in IMPLEMENTED_CASE_IDS
            if any(case.get("id") == case_id for case in fixture["cases"])
        ]
    except HCMCalcError as exc:
        st.error(str(exc))
        st.stop()

    with st.sidebar:
        st.header("Validated case")
        st.text_input("Fixture file", value=str(FIXTURE_PATH), disabled=True)
        selected_case_id = st.selectbox("Case ID", available_case_ids)
        run_selected = st.button("Run selected case", type="primary")

    if run_selected:
        try:
            case = find_case(fixture, selected_case_id)
            result = run_case(case)
            st.session_state["validated_case_result"] = (
                selected_case_id,
                result_to_dict(result),
            )
        except HCMCalcError as exc:
            st.error(str(exc))

    stored_result = st.session_state.get("validated_case_result")
    if stored_result is None:
        st.info("Select an implemented case and run it to view its validated result.")
        return

    result_case_id, result_data = stored_result
    if result_case_id != selected_case_id:
        st.info("Run the selected case to replace the currently displayed result.")
    render_result(result_case_id, result_data)


def render_manual_single_segment_calculator() -> None:
    """Render the v0.1 manual single-segment worksheet."""

    input_column, result_column = st.columns([1, 1.15], gap="large")

    with input_column:
        st.subheader("Manual single segment")
        unit_label = st.radio(
            "Unit system",
            ["Metric", "Imperial"],
            index=0 if DEFAULT_UNIT_SYSTEM == "metric" else 1,
            horizontal=True,
        )
        unit_system = str(unit_label).lower()
        defaults = manual_defaults(unit_system)
        st.markdown("#### § 1 — Segment setup")
        segment_type = st.selectbox(
            "Segment type",
            ["passing_constrained", "passing_zone", "passing_lane"],
            format_func=lambda value: {
                "passing_constrained": "Passing constrained",
                "passing_zone": "Passing zone",
                "passing_lane": "Passing lane",
            }[value],
        )
        terrain_type = st.selectbox(
            "Terrain type",
            ["level", "mountainous"],
            format_func=str.title,
        )
        if segment_type == "passing_lane":
            st.warning(
                "Single-segment passing lane results do not represent downstream "
                "passing-lane effects or full facility performance."
            )

        metric = unit_system == "metric"
        with st.form(f"manual_single_segment_{unit_system}"):
            segment_length = st.number_input(
                f"Segment length ({'km' if metric else 'mi'})",
                min_value=0.01,
                value=defaults["segment_length"],
            )
            posted_speed = st.number_input(
                f"Posted speed / base speed ({'km/h' if metric else 'mph'})",
                min_value=1.0,
                value=defaults["posted_speed"],
            )

            st.markdown("#### § 2 — Geometry")
            geometry_columns = st.columns(2)
            lane_width = geometry_columns[0].number_input(
                f"Lane width ({'m' if metric else 'ft'})",
                min_value=0.01,
                value=defaults["lane_width"],
            )
            shoulder_width = geometry_columns[1].number_input(
                f"Shoulder width ({'m' if metric else 'ft'})",
                min_value=0.0,
                value=defaults["shoulder_width"],
            )
            access_density = st.number_input(
                f"Access point density (points/{'km' if metric else 'mi'})",
                min_value=0.0,
                value=defaults["access_point_density"],
            )

            st.markdown("#### § 3 — Traffic demand")
            demand_columns = st.columns(2)
            analysis_volume = demand_columns[0].number_input(
                "Analysis-direction volume (veh/h)",
                min_value=0.0,
                value=defaults["analysis_direction_volume"],
            )
            peak_hour_factor = demand_columns[1].number_input(
                "Peak hour factor (PHF)",
                min_value=0.01,
                max_value=1.0,
                value=defaults["peak_hour_factor"],
            )
            heavy_vehicle_percent = demand_columns[0].number_input(
                "Heavy vehicles (%)",
                min_value=0.0,
                value=(
                    8.0
                    if segment_type == "passing_lane"
                    else defaults["heavy_vehicle_percent"]
                ),
            )
            opposing_volume = (
                demand_columns[1].number_input(
                    "Opposing-direction volume (veh/h)",
                    min_value=0.0,
                    value=defaults["opposing_direction_volume"],
                )
                if segment_type == "passing_zone"
                else None
            )

            if terrain_type == "mountainous":
                st.markdown("#### § 4 — Terrain / grade")
                st.info(
                    "Mountainous analysis is limited to validated grade and segment-"
                    "length combinations; unsupported combinations are rejected."
                )
                grade_percent = st.number_input(
                    "Grade (%)", value=defaults["grade_percent"]
                )
            else:
                grade_percent = 0.0

            run_manual = st.form_submit_button(
                "Run calculation", type="primary", use_container_width=True
            )

        st.caption(
            "Locked assumptions: straight alignment; no upstream passing lane; "
            "single segment only."
        )

    if run_manual:
        values = {
            "unit_system": unit_system,
            "segment_type": segment_type,
            "terrain_type": terrain_type,
            "posted_speed": posted_speed,
            "segment_length": segment_length,
            "lane_width": lane_width,
            "shoulder_width": shoulder_width,
            "access_point_density": access_density,
            "analysis_direction_volume": analysis_volume,
            "peak_hour_factor": peak_hour_factor,
            "heavy_vehicle_percent": heavy_vehicle_percent,
            "grade_percent": grade_percent,
            "opposing_direction_volume": opposing_volume,
        }
        st.session_state.pop("manual_segment_result", None)
        try:
            result = run_manual_single_segment(values)
            st.session_state["manual_segment_result"] = result_to_dict(result)
        except HCMCalcError as exc:
            with result_column:
                st.error(str(exc))

    with result_column:
        stored_result = st.session_state.get("manual_segment_result")
        if stored_result is None:
            st.info("Enter segment inputs and click Run calculation to see results.")
            return
        render_manual_result(stored_result, unit_system)


def render_manual_result(result_data: dict[str, Any], unit_system: str) -> None:
    """Render the manual result hierarchy with display-unit conversions."""

    outputs = result_data["outputs"]
    metrics = display_outputs(outputs, unit_system)
    level_of_service = str(outputs["level_of_service"])
    foreground, background = los_colors(level_of_service)
    density = format_display_metric(
        "follower_density", metrics["follower_density"], unit_system
    )
    st.markdown(
        f"""
        <div class="los-hero" style="--los-color: {foreground};
             --los-background: {background};">
            <div class="los-hero-label">Level of service</div>
            <div class="los-hero-grade">LOS {level_of_service}</div>
            <div class="los-hero-density">
                Follower density <strong>{density}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    supporting_metrics = [
        (name, metric)
        for name, metric in metrics.items()
        if name != "follower_density"
    ]
    metric_columns = st.columns(3)
    for index, (name, metric) in enumerate(supporting_metrics):
        metric_columns[index % 3].metric(
            metric["label"], format_display_metric(name, metric, unit_system)
        )

    for warning in result_data["warnings"]:
        st.warning(warning)

    with st.expander("Assumptions"):
        for assumption in result_data["assumptions"]:
            st.markdown(f"- {assumption}")

    with st.expander("Intermediate values"):
        st.dataframe(
            result_data["intermediate_values"],
            hide_index=True,
            use_container_width=True,
        )

    full_result = {
        "unit_system": unit_system,
        "display_outputs": metrics,
        "engine_result": result_data,
    }
    full_result_json = json.dumps(full_result, indent=2)
    with st.expander("Full result JSON (engine-native values are imperial)"):
        st.json(full_result)

    st.download_button(
        "Download JSON",
        data=full_result_json,
        file_name="manual-single-segment-result.json",
        mime="application/json",
        use_container_width=True,
    )


def main() -> None:
    """Run the single-page Streamlit calculator."""

    st.set_page_config(page_title="HCM Calculator", layout="wide")
    apply_ui_styles()
    st.title("HCM Calculator")
    st.caption("HCM 7th Edition Chapter 15 Two-Lane Highway")
    st.info(SCOPE_NOTICE)
    st.markdown("#### Analysis mode")
    mode = st.radio(
        "Choose the worksheet or validation viewer",
        ["Manual single segment calculator", "Validated examples / QA"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if mode == "Manual single segment calculator":
        render_manual_single_segment_calculator()
    else:
        render_validated_case_viewer()
    st.divider()
    st.caption(LIMITATIONS_FOOTER)


if __name__ == "__main__":
    main()
