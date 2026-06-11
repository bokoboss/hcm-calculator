"""Single-page Streamlit viewer and manual single-segment calculator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from hcmcalc.cli import find_case, load_input_file, result_to_dict, run_case
from hcmcalc.core import HCMCalcError
from hcmcalc.ui.audit import build_manual_calculation_audit_record
from hcmcalc.ui.curve_editor import curve_setup_defaults, generate_curve_subsegments
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.project_io import (
    ProjectFileError,
    create_manual_project_json,
    load_manual_project_json,
)
from hcmcalc.ui.result_view import compact_rows, format_display_metric, los_colors
from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.units import (
    DEFAULT_UNIT_SYSTEM,
    display_outputs,
    manual_defaults,
    manual_horizontal_curve_defaults,
)


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "example_inputs.yaml"
SEGMENT_TYPE_LABELS = {
    "passing_constrained": "Passing constrained",
    "passing_zone": "Passing zone",
    "passing_lane": "Passing lane",
}
IMPLEMENTED_CASE_IDS = (
    "TLH-CH15-001",
    "TLH-CH15-002",
    "TLH-CH15-003",
    "TLH-CH15-004",
)
SCOPE_NOTICE = (
    "Current scope: one two-lane highway segment, with level and limited "
    "mountainous terrain support and Example Problem 2 horizontal curves."
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
            background-color: #245b86 !important;
            border-color: #245b86 !important;
            color: #ffffff !important;
        }
        button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
            background-color: #1d4a6e !important;
            border-color: #1d4a6e !important;
        }
        .compact-section-label {
            color: #4b5563;
            font-size: 0.82rem;
            font-weight: 650;
            letter-spacing: 0.04em;
            margin: 0.15rem 0 -0.25rem;
            text-transform: uppercase;
        }
        .los-hero {
            border: 1px solid var(--los-color);
            border-left-width: 0.45rem;
            border-radius: 0.55rem;
            background: var(--los-background);
            padding: 0.7rem 1rem;
            margin-bottom: 0.45rem;
        }
        .los-hero-label {
            color: #4b5563;
            font-size: 0.72rem;
            font-weight: 650;
            letter-spacing: 0.08em;
            margin-bottom: 0.05rem;
            text-transform: uppercase;
        }
        .los-hero-grade {
            color: var(--los-color);
            font-size: 2.7rem;
            font-weight: 750;
            line-height: 1;
        }
        .los-hero-density {
            color: #374151;
            font-size: 0.92rem;
            margin-top: 0.3rem;
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

    pending_project = st.session_state.pop("manual_pending_project", None)
    if pending_project is not None:
        _restore_manual_project(pending_project)
    load_message = st.session_state.pop("manual_project_load_message", None)
    if load_message is not None:
        st.success(load_message)
    generation_message = st.session_state.pop("manual_curve_generation_message", None)
    if generation_message is not None:
        st.success(generation_message)

    input_column, result_column = st.columns([1, 1.15], gap="large")

    with input_column:
        st.caption("Manual single segment")
        unit_label = st.radio(
            "Unit system",
            ["Metric", "Imperial"],
            index=0 if DEFAULT_UNIT_SYSTEM == "metric" else 1,
            horizontal=True,
            key="manual_unit_label",
        )
        unit_system = str(unit_label).lower()
        defaults = manual_defaults(unit_system)
        setup_columns = st.columns(2)
        segment_type = setup_columns[0].selectbox(
            "Segment type",
            list(SEGMENT_TYPE_LABELS),
            format_func=SEGMENT_TYPE_LABELS.__getitem__,
            key="manual_segment_type",
        )
        terrain_type = setup_columns[1].selectbox(
            "Terrain type",
            ["level", "mountainous"],
            format_func=str.title,
            key="manual_terrain_type",
        )
        for name, default in defaults.items():
            if name == "heavy_vehicle_percent" and segment_type == "passing_lane":
                default = 8.0
            st.session_state.setdefault(f"manual_{name}_{unit_system}", default)
        schematic_path = get_segment_schematic_path(segment_type)
        if schematic_path is None:
            st.caption("Schematic image not found for this segment type.")
        else:
            st.image(
                schematic_path,
                caption=f"Segment schematic: {SEGMENT_TYPE_LABELS[segment_type]}",
                width=420,
            )
        if segment_type == "passing_lane":
            st.warning(
                "Single-segment passing lane results do not represent downstream "
                "passing-lane effects or full facility performance."
            )

        metric = unit_system == "metric"
        with st.form(f"manual_single_segment_{unit_system}"):
            st.markdown(
                '<div class="compact-section-label">Geometry</div>',
                unsafe_allow_html=True,
            )
            geometry_primary = st.columns(3)
            segment_length = geometry_primary[0].number_input(
                f"Segment length ({'km' if metric else 'mi'})",
                min_value=0.01,
                key=f"manual_segment_length_{unit_system}",
            )
            posted_speed = geometry_primary[1].number_input(
                f"Posted speed / base speed ({'km/h' if metric else 'mph'})",
                min_value=1.0,
                key=f"manual_posted_speed_{unit_system}",
            )
            lane_width = geometry_primary[2].number_input(
                f"Lane width ({'m' if metric else 'ft'})",
                min_value=0.01,
                key=f"manual_lane_width_{unit_system}",
            )
            geometry_secondary = st.columns(2)
            shoulder_width = geometry_secondary[0].number_input(
                f"Shoulder width ({'m' if metric else 'ft'})",
                min_value=0.0,
                key=f"manual_shoulder_width_{unit_system}",
            )
            access_density = geometry_secondary[1].number_input(
                f"Access point density (points/{'km' if metric else 'mi'})",
                min_value=0.0,
                key=f"manual_access_point_density_{unit_system}",
            )
            horizontal_alignment_label = st.selectbox(
                "Horizontal alignment",
                ["Straight", "Horizontal curve"],
                help=(
                    "Horizontal curve adjustment uses the validated Example "
                    "Problem 2 calculation path."
                ),
                key="manual_horizontal_alignment_label",
            )
            horizontal_alignment = (
                "horizontal_curves"
                if horizontal_alignment_label == "Horizontal curve"
                else "straight"
            )
            horizontal_subsegments: list[dict[str, Any]] = []
            curve_setup: dict[str, Any] | None = None
            generate_curve = False
            if horizontal_alignment == "horizontal_curves":
                st.caption(
                    "Auto-generation is a convenience for the validated single-segment "
                    "horizontal curve workflow. You can still edit the generated "
                    "subsegments manually."
                )
                setup_defaults = curve_setup_defaults(unit_system, segment_length)
                for name, default in setup_defaults.items():
                    st.session_state.setdefault(
                        f"manual_curve_setup_{name}_{unit_system}", default
                    )
                st.markdown(
                    '<div class="compact-section-label">Curve setup</div>',
                    unsafe_allow_html=True,
                )
                curve_primary = st.columns(3)
                total_curve_length = curve_primary[0].number_input(
                    f"Total curve length ({'m' if metric else 'ft'})",
                    key=f"manual_curve_setup_total_curve_length_{unit_system}",
                )
                curve_radius = curve_primary[1].number_input(
                    f"Curve radius ({'m' if metric else 'ft'})",
                    key=f"manual_curve_setup_radius_{unit_system}",
                )
                superelevation = curve_primary[2].number_input(
                    "Superelevation (%)",
                    key=f"manual_curve_setup_superelevation_percent_{unit_system}",
                )
                curve_secondary = st.columns(3)
                central_angle = curve_secondary[0].number_input(
                    "Central angle (deg)",
                    key=f"manual_curve_setup_central_angle_deg_{unit_system}",
                )
                horizontal_class = curve_secondary[1].number_input(
                    "Horizontal class",
                    min_value=1,
                    max_value=5,
                    step=1,
                    key=f"manual_curve_setup_horizontal_class_{unit_system}",
                )
                subsegment_count = curve_secondary[2].number_input(
                    "Number of subsegments",
                    min_value=1,
                    step=1,
                    key=f"manual_curve_setup_subsegment_count_{unit_system}",
                )
                curve_setup = {
                    "total_curve_length": total_curve_length,
                    "radius": curve_radius,
                    "superelevation_percent": superelevation,
                    "central_angle_deg": central_angle,
                    "horizontal_class": horizontal_class,
                    "subsegment_count": subsegment_count,
                }
                generate_curve = st.form_submit_button(
                    "Generate curve subsegments", use_container_width=True
                )
                editor_version = st.session_state.get(
                    f"manual_horizontal_subsegments_version_{unit_system}", 0
                )
                editor_data = st.session_state.pop(
                    f"manual_horizontal_subsegments_seed_{unit_system}",
                    manual_horizontal_curve_defaults(unit_system, segment_length),
                )
                with st.expander("Curve subsegments"):
                    st.caption(
                        "Review or edit generated rows. Subsegment lengths must total "
                        f"the segment length; lengths and radii are in "
                        f"{'m' if metric else 'ft'}."
                    )
                    horizontal_subsegments = st.data_editor(
                        editor_data,
                        key=(
                            f"manual_horizontal_subsegments_{unit_system}_"
                            f"{editor_version}"
                        ),
                        hide_index=True,
                        num_rows="fixed",
                        use_container_width=True,
                        column_config={
                            "type": st.column_config.SelectboxColumn(
                                "Subsegment type",
                                options=["tangent", "horizontal_curve"],
                                required=True,
                            ),
                            "length": st.column_config.NumberColumn(
                                f"Length ({'m' if metric else 'ft'})",
                                min_value=0.01,
                                required=True,
                            ),
                            "superelevation_percent": st.column_config.NumberColumn(
                                "Superelevation (%)"
                            ),
                            "radius": st.column_config.NumberColumn(
                                f"Radius ({'m' if metric else 'ft'})",
                                min_value=0.01,
                            ),
                            "central_angle_deg": st.column_config.NumberColumn(
                                "Central angle (deg)"
                            ),
                            "horizontal_class": st.column_config.NumberColumn(
                                "Horizontal class",
                                min_value=1,
                                max_value=5,
                                step=1,
                            ),
                        },
                    )

            st.markdown(
                '<div class="compact-section-label">Traffic demand</div>',
                unsafe_allow_html=True,
            )
            demand_columns = st.columns(3)
            analysis_volume = demand_columns[0].number_input(
                "Analysis-direction volume (veh/h)",
                min_value=0.0,
                key=f"manual_analysis_direction_volume_{unit_system}",
            )
            peak_hour_factor = demand_columns[1].number_input(
                "Peak hour factor (PHF)",
                min_value=0.01,
                max_value=1.0,
                key=f"manual_peak_hour_factor_{unit_system}",
            )
            heavy_vehicle_percent = demand_columns[2].number_input(
                "Heavy vehicles (%)",
                min_value=0.0,
                key=f"manual_heavy_vehicle_percent_{unit_system}",
            )
            opposing_volume = (
                st.number_input(
                    "Opposing-direction volume (veh/h)",
                    min_value=0.0,
                    key=f"manual_opposing_direction_volume_{unit_system}",
                )
                if segment_type == "passing_zone"
                else None
            )

            if terrain_type == "mountainous":
                terrain_columns = st.columns([1, 2])
                grade_percent = terrain_columns[0].number_input(
                    "Grade (%)",
                    key=f"manual_grade_percent_{unit_system}",
                )
                terrain_columns[1].caption(
                    "Supported combinations are limited to validated mountainous "
                    "grades and segment lengths."
                )
            else:
                grade_percent = 0.0

            run_manual = st.form_submit_button(
                "Run calculation", type="primary", use_container_width=True
            )

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
            "horizontal_alignment": horizontal_alignment,
            "horizontal_alignment_subsegments": horizontal_subsegments,
        }
        if curve_setup is not None:
            values["curve_setup"] = curve_setup
        if generate_curve and curve_setup is not None:
            try:
                generated_subsegments = generate_curve_subsegments(curve_setup)
            except HCMCalcError as exc:
                st.error(str(exc))
            else:
                curve_version_key = (
                    f"manual_horizontal_subsegments_version_{unit_system}"
                )
                st.session_state[curve_version_key] = (
                    st.session_state.get(curve_version_key, 0) + 1
                )
                st.session_state[
                    f"manual_horizontal_subsegments_seed_{unit_system}"
                ] = generated_subsegments
                st.session_state["manual_curve_generation_message"] = (
                    f"Generated {len(generated_subsegments)} editable curve subsegments."
                )
                st.rerun()
        render_manual_project_file_controls(values)
        st.caption(
            "Locked assumptions: no upstream passing lane; single segment only. "
            "Horizontal curves are limited to the validated Example Problem 2 path."
        )

    if run_manual:
        st.session_state.pop("manual_segment_result", None)
        st.session_state.pop("manual_segment_error", None)
        try:
            result = run_manual_single_segment(values)
            st.session_state["manual_segment_result"] = result_to_dict(result)
            st.session_state["manual_segment_audit"] = (
                build_manual_calculation_audit_record(values, result=result)
            )
        except HCMCalcError as exc:
            st.session_state["manual_segment_error"] = str(exc)
            st.session_state["manual_segment_audit"] = (
                build_manual_calculation_audit_record(values, error=exc)
            )

    with result_column:
        stored_result = st.session_state.get("manual_segment_result")
        audit_record = st.session_state.get("manual_segment_audit")
        stored_error = st.session_state.get("manual_segment_error")
        if stored_error is not None:
            st.error(stored_error)
            render_audit_record(audit_record)
            return
        if stored_result is None:
            st.info("Enter segment inputs and click Run calculation to see results.")
            return
        render_manual_result(
            stored_result,
            str(audit_record.get("unit_system", unit_system))
            if isinstance(audit_record, dict)
            else unit_system,
            audit_record,
        )


def render_manual_project_file_controls(manual_inputs: dict[str, Any]) -> None:
    """Render compact manual project save and load controls."""

    stored_audit = st.session_state.get("manual_segment_audit")
    calculation_matches_inputs = (
        isinstance(stored_audit, dict)
        and stored_audit.get("user_inputs") == manual_inputs
    )
    result = (
        st.session_state.get("manual_segment_result")
        if calculation_matches_inputs
        else None
    )
    audit_record = stored_audit if calculation_matches_inputs else None
    project_json = create_manual_project_json(
        manual_inputs, result=result, audit_record=audit_record
    )

    with st.expander("Project file"):
        st.caption("Save this worksheet setup or restore a saved manual project.")
        st.download_button(
            "Download project JSON",
            data=project_json,
            file_name="manual-single-segment-project.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded_project = st.file_uploader(
            "Load project JSON",
            type=["json"],
            key="manual_project_file_uploader",
        )
        if st.button(
            "Load project",
            disabled=uploaded_project is None,
            use_container_width=True,
        ):
            try:
                project = load_manual_project_json(uploaded_project.getvalue())
            except ProjectFileError as exc:
                st.error(str(exc))
            else:
                st.session_state["manual_pending_project"] = project
                st.rerun()


def _restore_manual_project(project: dict[str, Any]) -> None:
    """Restore validated project data into manual worksheet session state."""

    manual_inputs = project["manual_inputs"]
    unit_system = project["unit_system"]
    st.session_state["manual_unit_label"] = unit_system.title()
    st.session_state["manual_segment_type"] = manual_inputs["segment_type"]
    st.session_state["manual_terrain_type"] = manual_inputs["terrain_type"]
    st.session_state["manual_horizontal_alignment_label"] = (
        "Horizontal curve"
        if manual_inputs["horizontal_alignment"] == "horizontal_curves"
        else "Straight"
    )
    for name in (
        "segment_length",
        "posted_speed",
        "lane_width",
        "shoulder_width",
        "access_point_density",
        "analysis_direction_volume",
        "peak_hour_factor",
        "heavy_vehicle_percent",
        "opposing_direction_volume",
        "grade_percent",
    ):
        value = manual_inputs.get(name)
        if value is not None:
            st.session_state[f"manual_{name}_{unit_system}"] = value
    curve_version_key = f"manual_horizontal_subsegments_version_{unit_system}"
    st.session_state[curve_version_key] = st.session_state.get(curve_version_key, 0) + 1
    st.session_state[f"manual_horizontal_subsegments_seed_{unit_system}"] = (
        manual_inputs.get("horizontal_alignment_subsegments", [])
    )
    curve_setup = manual_inputs.get("curve_setup")
    if isinstance(curve_setup, dict):
        for name, value in curve_setup.items():
            st.session_state[f"manual_curve_setup_{name}_{unit_system}"] = value

    for state_key, project_key in (
        ("manual_segment_result", "result"),
        ("manual_segment_audit", "audit_record"),
    ):
        if project.get(project_key) is None:
            st.session_state.pop(state_key, None)
        else:
            st.session_state[state_key] = project[project_key]
    st.session_state.pop("manual_segment_error", None)
    st.session_state["manual_project_load_message"] = (
        "Project loaded. Review the restored inputs and click Run calculation "
        "to calculate again."
    )


def render_audit_record(audit_record: dict[str, Any] | None) -> None:
    """Render a collapsed manual calculation audit record."""

    if audit_record is None:
        return
    with st.expander("Audit record"):
        st.caption(
            "Submitted values, engine-native imperial inputs, scope status, and "
            "calculation metadata."
        )
        st.json(audit_record)


def render_manual_result(
    result_data: dict[str, Any],
    unit_system: str,
    audit_record: dict[str, Any] | None = None,
) -> None:
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

    supporting_metrics = list(metrics.items())
    for index, (name, metric) in enumerate(supporting_metrics):
        if index % 3 == 0:
            metric_columns = st.columns(3)
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

    render_audit_record(audit_record)

    full_result = {
        "unit_system": unit_system,
        "display_outputs": metrics,
        "engine_result": result_data,
    }
    full_result_json = json.dumps(full_result, indent=2)
    with st.expander("Full result JSON"):
        st.caption(
            "Engine result JSON with display outputs. Engine-native values are "
            "imperial; the submitted-input record is in Audit record."
        )
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
    header_content, header_mode = st.columns([3, 1])
    with header_content:
        st.subheader("HCM Calculator")
        st.caption(f"HCM 7th Edition Chapter 15 Two-Lane Highway. {SCOPE_NOTICE}")
    with header_mode:
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
