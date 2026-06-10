"""Single-page Streamlit viewer and manual single-segment calculator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from hcmcalc.cli import find_case, load_input_file, result_to_dict, run_case
from hcmcalc.core import HCMCalcError
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.result_view import compact_rows


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "example_inputs.yaml"
IMPLEMENTED_CASE_IDS = (
    "TLH-CH15-001",
    "TLH-CH15-002",
    "TLH-CH15-003",
    "TLH-CH15-004",
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

    st.info(
        "Manual scope: one straight Two-Lane Highway segment, Motorized Vehicle "
        "LOS only. Results outside the validated scope are rejected."
    )
    segment_type = st.selectbox(
        "Segment type",
        ["passing_constrained", "passing_zone", "passing_lane"],
    )
    terrain_type = st.selectbox("Terrain type", ["level", "mountainous"])
    if segment_type == "passing_lane":
        st.warning(
            "Single-segment passing lane results do not represent downstream "
            "passing-lane effects or full facility performance. Use facility "
            "analysis for corridor-level evaluation."
        )

    with st.form("manual_single_segment"):
        columns = st.columns(2)
        posted_speed = columns[0].number_input(
            "Posted speed (mph)", min_value=1.0, value=50.0
        )
        segment_length = columns[1].number_input(
            "Segment length (mi)", min_value=0.01, value=0.75
        )
        lane_width = columns[0].number_input(
            "Lane width (ft)", min_value=9.0, max_value=12.0, value=12.0
        )
        shoulder_width = columns[1].number_input(
            "Shoulder width (ft)", min_value=0.0, max_value=6.0, value=6.0
        )
        access_density = columns[0].number_input(
            "Access point density (per mi)", min_value=0.0, value=0.0
        )
        analysis_volume = columns[1].number_input(
            "Analysis direction volume (veh/h)", min_value=0.0, value=752.0
        )
        peak_hour_factor = columns[0].number_input(
            "Peak hour factor", min_value=0.01, max_value=1.0, value=0.94
        )
        heavy_vehicle_percent = columns[1].number_input(
            "Heavy vehicle percent",
            min_value=0.0,
            value=8.0 if segment_type == "passing_lane" else 5.0,
        )
        grade_percent = (
            columns[0].number_input("Grade percent", value=4.0)
            if terrain_type == "mountainous"
            else 0.0
        )
        opposing_volume = (
            columns[1].number_input(
                "Opposing direction volume (veh/h)", min_value=0.0, value=500.0
            )
            if segment_type == "passing_zone"
            else None
        )
        run_manual = st.form_submit_button("Run", type="primary")

    st.caption(
        "Locked assumptions: two_lane_highway; hcm7_ch15_two_lane_motorized; "
        "straight alignment; no upstream passing lane; single segment only."
    )
    if run_manual:
        values = {
            "segment_type": segment_type,
            "terrain_type": terrain_type,
            "posted_speed_mph": posted_speed,
            "segment_length_mi": segment_length,
            "lane_width_ft": lane_width,
            "shoulder_width_ft": shoulder_width,
            "access_point_density_per_mi": access_density,
            "analysis_direction_volume_veh_h": analysis_volume,
            "peak_hour_factor": peak_hour_factor,
            "heavy_vehicle_percent": heavy_vehicle_percent,
            "grade_percent": grade_percent,
            "opposing_direction_volume_veh_h": opposing_volume,
        }
        try:
            result = run_manual_single_segment(values)
            st.session_state["manual_segment_result"] = result_to_dict(result)
        except HCMCalcError as exc:
            st.session_state.pop("manual_segment_result", None)
            st.error(str(exc))

    stored_result = st.session_state.get("manual_segment_result")
    if stored_result is None:
        st.info("Enter one segment and click Run to calculate.")
        return
    render_result("manual-single-segment", stored_result)


def main() -> None:
    """Run the single-page Streamlit calculator."""

    st.set_page_config(page_title="HCM Calculator", layout="wide")
    st.title("HCM Calculator")
    st.caption("HCM 7th Edition Chapter 15 Two-Lane Highway")
    mode = st.radio(
        "Mode",
        ["Validated Case Viewer", "Manual Single Segment Calculator"],
        horizontal=True,
    )
    if mode == "Validated Case Viewer":
        render_validated_case_viewer()
    else:
        render_manual_single_segment_calculator()


if __name__ == "__main__":
    main()
