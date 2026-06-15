"""Single-page Streamlit viewer and manual single-segment calculator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from hcmcalc.cli import find_case, load_input_file, result_to_dict, run_case
from hcmcalc.core import HCMCalcError
from hcmcalc.ui.audit import build_manual_calculation_audit_record
from hcmcalc.ui.curve_editor import (
    curve_setup_defaults,
    generate_curve_subsegments,
    initial_curve_subsegments,
)
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    clear_manual_facility_result_state,
    facility_segment_result_rows,
    facility_template_options,
    load_facility_template,
    run_manual_facility,
)
from hcmcalc.ui.manual_multilane import (
    build_manual_multilane_audit_record,
    load_multilane_template,
    multilane_template_options,
    run_manual_multilane,
)
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.project_io import (
    ProjectFileError,
    create_manual_facility_project_json,
    create_manual_project_json,
    load_manual_facility_project_json,
    load_manual_project_json,
)
from hcmcalc.ui.result_view import compact_rows, format_display_metric, los_colors
from hcmcalc.ui.reporting import (
    ReportingError,
    build_report,
    export_report,
    report_filename,
)
from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.units import (
    DEFAULT_UNIT_SYSTEM,
    display_outputs,
    manual_defaults,
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
    "Current scope: limited Two-Lane manual workflows and an Example Problem "
    "4-backed Multilane segment workflow."
)
LIMITATIONS_FOOTER = (
    "Current limitations: example-scoped validation, selected mountainous "
    "combinations, no general downstream passing-lane support, and no general "
    "Multilane Highway support."
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


def render_manual_multilane_calculator() -> None:
    """Render the Example Problem 4-backed Multilane segment worksheet."""

    st.info("Limited validated-path Multilane Highway workflow")
    st.caption(
        "This v0.1 workflow is anchored to Chapter 26 Example Problem 4 and is "
        "not a general Multilane Highway calculator."
    )
    template_options = multilane_template_options()
    template_id = st.selectbox(
        "Case direction / template",
        list(template_options),
        format_func=template_options.__getitem__,
        key="multilane_template_id",
    )
    if st.session_state.get("manual_multilane_template_context") != template_id:
        for state_key in (
            "manual_multilane_result",
            "manual_multilane_error",
            "manual_multilane_audit",
        ):
            st.session_state.pop(state_key, None)
        st.session_state["manual_multilane_template_context"] = template_id
    try:
        template = load_multilane_template(template_id)
    except (HCMCalcError, ValueError) as exc:
        st.error(str(exc))
        return

    inputs = template["inputs"]
    input_column, result_column = st.columns([1.05, 0.95], gap="large")
    with input_column:
        st.markdown("**Inputs**")
        with st.form(f"multilane_form_{template_id}"):
            st.markdown('<div class="compact-section-label">Setup</div>', unsafe_allow_html=True)
            setup_columns = st.columns(2)
            setup_columns[0].text_input(
                "Analysis type",
                value="Multilane Highway Segment",
                disabled=True,
            )
            setup_columns[1].text_input(
                "Unit system",
                value="Imperial (engine-native)",
                disabled=True,
            )
            st.caption(
                f"{template['description']}. Support status: "
                f"{template['validation_status']}."
            )

            st.markdown(
                '<div class="compact-section-label">Roadway / Free-flow speed</div>',
                unsafe_allow_html=True,
            )
            roadway_columns = st.columns(2)
            number_of_lanes = roadway_columns[0].number_input(
                "Lanes in analysis direction",
                min_value=1,
                step=1,
                value=int(inputs["number_of_lanes"]),
            )
            segment_length_ft = roadway_columns[1].number_input(
                "Segment length (ft)",
                min_value=1.0,
                value=float(inputs["segment_length_ft"]),
            )
            posted_speed_limit_mph = roadway_columns[0].number_input(
                "Posted speed limit (mph)",
                min_value=1.0,
                value=float(inputs["posted_speed_limit_mph"]),
            )
            lane_width_ft = roadway_columns[1].number_input(
                "Lane width (ft)",
                min_value=1.0,
                value=float(inputs["lane_width_ft"]),
            )
            roadside_lateral_clearance_ft = roadway_columns[0].number_input(
                "Roadside lateral clearance (ft)",
                min_value=0.0,
                value=float(inputs["roadside_lateral_clearance_ft"]),
            )
            access_point_density_per_mi = roadway_columns[1].number_input(
                "Access point density (per mi)",
                min_value=0.0,
                value=float(inputs["access_point_density_per_mi"]),
            )

            st.markdown(
                '<div class="compact-section-label">Traffic</div>',
                unsafe_allow_html=True,
            )
            traffic_columns = st.columns(2)
            demand_volume_veh_h = traffic_columns[0].number_input(
                "Demand volume (veh/h)",
                min_value=1.0,
                value=float(inputs["demand_volume_veh_h"]),
            )
            peak_hour_factor = traffic_columns[1].number_input(
                "Peak hour factor",
                min_value=0.01,
                max_value=1.0,
                value=float(inputs["peak_hour_factor"]),
            )
            heavy_vehicle_percent = traffic_columns[0].number_input(
                "Heavy vehicles (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(inputs["heavy_vehicle_percent"]),
            )
            grade_percent = traffic_columns[1].number_input(
                "Grade (%)",
                value=float(inputs["grade_percent"]),
            )
            st.caption(
                "Locked template context: one direction, one segment, TWLTL median, "
                "and default 30% SUT / 70% TT truck mix."
            )
            run_multilane = st.form_submit_button(
                "Run calculation", type="primary", use_container_width=True
            )

        submitted_inputs = {
            **inputs,
            "number_of_lanes": int(number_of_lanes),
            "segment_length_ft": segment_length_ft,
            "posted_speed_limit_mph": posted_speed_limit_mph,
            "lane_width_ft": lane_width_ft,
            "roadside_lateral_clearance_ft": roadside_lateral_clearance_ft,
            "access_point_density_per_mi": access_point_density_per_mi,
            "demand_volume_veh_h": demand_volume_veh_h,
            "peak_hour_factor": peak_hour_factor,
            "heavy_vehicle_percent": heavy_vehicle_percent,
            "grade_percent": grade_percent,
        }
        with st.expander("Unsupported scope", expanded=False):
            st.caption(
                "Basic Freeway, ramps, weaving, merge/diverge, managed lanes, work "
                "zones, reliability, and facility/corridor workflows are not supported."
            )
            st.caption(
                "Any edit outside the exact validated Example Problem 4 EB/WB path "
                "is rejected by the existing Multilane engine validation."
            )

    if run_multilane:
        st.session_state.pop("manual_multilane_result", None)
        st.session_state.pop("manual_multilane_error", None)
        try:
            result = run_manual_multilane(submitted_inputs)
            st.session_state["manual_multilane_result"] = result_to_dict(result)
            st.session_state["manual_multilane_audit"] = (
                build_manual_multilane_audit_record(
                    template_id, submitted_inputs, result=result
                )
            )
        except HCMCalcError as exc:
            st.session_state["manual_multilane_error"] = str(exc)
            st.session_state["manual_multilane_audit"] = (
                build_manual_multilane_audit_record(
                    template_id, submitted_inputs, error=exc
                )
            )

    with result_column:
        st.markdown("**Results**")
        error = st.session_state.get("manual_multilane_error")
        audit = st.session_state.get("manual_multilane_audit")
        if error is not None:
            st.error(f"Unsupported Multilane case: {error}")
            with st.expander("Audit / intermediate values"):
                st.json(audit)
            return
        result_data = st.session_state.get("manual_multilane_result")
        if result_data is None:
            st.caption("Run calculation to see results.")
            return

        outputs = result_data["outputs"]
        summary = st.columns(3)
        summary[0].metric("Density", f"{outputs['density_pc_mi_ln']:.1f} pc/mi/ln")
        summary[1].metric("LOS", outputs["level_of_service"])
        summary[2].metric(
            "Speed used for density",
            f"{outputs['speed_used_for_density_mph']:.1f} mph",
        )
        metrics = st.columns(2)
        metrics[0].metric(
            "Demand flow rate", f"{outputs['demand_flow_rate_pc_h_ln']:.0f} pc/h/ln"
        )
        metrics[1].metric(
            "Adjusted free-flow speed",
            f"{outputs['adjusted_free_flow_speed_mph']:.1f} mph",
        )
        metrics[0].metric(
            "Base free-flow speed", f"{outputs['base_free_flow_speed_mph']:.1f} mph"
        )
        metrics[1].metric(
            "Heavy vehicle adjustment factor",
            f"{outputs['heavy_vehicle_adjustment_factor']:.3f}",
        )
        metrics[0].metric("Capacity", f"{outputs['capacity_pc_h_ln']:.0f} pc/h/ln")
        metrics[1].metric("Capacity check", outputs["capacity_check"].replace("_", " "))

        with st.expander("Calculation details"):
            render_list("Assumptions", result_data["assumptions"], "No assumptions reported.")
            render_list("Warnings", result_data["warnings"], "No warnings reported.")
            render_list(
                "Unsupported scope notes",
                outputs["unsupported_scope_notes"],
                "No unsupported scope notes reported.",
            )
        with st.expander("Audit / intermediate values"):
            st.json(audit)
            st.dataframe(
                result_data["intermediate_values"],
                hide_index=True,
                use_container_width=True,
            )
        with st.expander("Full JSON"):
            st.json(
                {
                    "calculation_type": "manual_multilane_segment_v0_1",
                    "unit_system": "imperial",
                    "engine_result": result_data,
                    "audit_record": audit,
                }
            )


def render_manual_facility_calculator() -> None:
    """Render the limited Example 3/4-backed facility worksheet."""

    pending_project = st.session_state.pop("manual_facility_pending_project", None)
    if pending_project is not None:
        _restore_manual_facility_project(pending_project)
    load_message = st.session_state.pop("manual_facility_project_load_message", None)
    if load_message is not None:
        st.success(load_message)

    st.info("Limited template-backed facility workflow")
    st.caption(
        "Validated example-based workflow only. This does not represent full "
        "general Chapter 15 facility support; unsupported combinations remain guarded."
    )
    controls = st.columns([2, 1])
    template_options = facility_template_options()
    template_id = controls[0].selectbox(
        "Facility template",
        list(template_options),
        format_func=template_options.__getitem__,
        key="facility_template_id",
        help="Choose the validated Example Problem 3 or Example Problem 4 basis.",
    )
    unit_label = controls[1].radio(
        "Unit system",
        ["Metric", "Imperial"],
        horizontal=True,
        key="facility_unit_label",
    )
    unit_system = str(unit_label).lower()
    selection_context = (template_id, unit_system)
    if st.session_state.get("manual_facility_selection_context") != selection_context:
        clear_manual_facility_result_state(st.session_state)
        st.session_state["manual_facility_selection_context"] = selection_context

    try:
        template = load_facility_template(template_id, unit_system)
    except HCMCalcError as exc:
        st.error(str(exc))
        return

    editable_fields = set(template["editable_fields"])
    disabled_fields = [
        field
        for field in template["segments"][0]
        if field not in editable_fields
    ]
    st.markdown(f"**{template['template_label']}**")
    st.caption(f"Basis: {template['template_basis']}. {template['supported_context']}")
    template_details = st.columns(2)
    template_details[0].success(f"Safe edits: {template['safe_edit_summary']}")
    template_details[1].warning(f"Locked or unsupported: {template['locked_summary']}")
    editor_version = st.session_state.get("manual_facility_editor_version", 0)
    editor_seed = st.session_state.pop(
        "manual_facility_segment_rows_seed", template["segments"]
    )
    edited_rows = st.data_editor(
        editor_seed,
        key=f"facility_segment_editor_{template_id}_{unit_system}_{editor_version}",
        hide_index=True,
        num_rows="fixed",
        disabled=disabled_fields,
        use_container_width=True,
        column_config={
            "segment_length": st.column_config.NumberColumn(
                f"Length ({'km' if unit_system == 'metric' else 'mi'})",
                min_value=0.01,
                required=True,
            ),
            "posted_speed": st.column_config.NumberColumn(
                f"Posted speed ({'km/h' if unit_system == 'metric' else 'mph'})",
                min_value=1.0,
                required=True,
            ),
            "analysis_direction_volume_veh_h": st.column_config.NumberColumn(
                "Analysis volume (veh/h)", min_value=0.0, required=True
            ),
            "opposing_direction_volume_veh_h": st.column_config.NumberColumn(
                "Opposing volume (veh/h)", min_value=0.0
            ),
            "peak_hour_factor": st.column_config.NumberColumn(
                "PHF", min_value=0.01, max_value=1.0, required=True
            ),
            "heavy_vehicle_percent": st.column_config.NumberColumn(
                "Heavy vehicles (%)", min_value=0.0, max_value=100.0, required=True
            ),
            "passing_lane": st.column_config.CheckboxColumn("Passing lane"),
            "downstream_affected": st.column_config.CheckboxColumn(
                "Downstream context"
            ),
            "segment_name": st.column_config.TextColumn("Segment name"),
            "segment_type": st.column_config.TextColumn("Segment type"),
            "terrain_type": st.column_config.TextColumn("Terrain"),
            "grade_percent": st.column_config.NumberColumn("Grade (%)"),
            "horizontal_alignment": st.column_config.TextColumn("Alignment"),
        },
    )
    st.warning(
        "Locked fields preserve the validated template. Manual downstream adjustment "
        "and arbitrary passing-lane, curve, nonlevel, or segment-sequence edits are unsupported."
    )

    calculate_column, scope_column = st.columns([1, 2])
    calculate = calculate_column.button(
        "Calculate facility",
        type="primary",
        use_container_width=True,
        key="facility_calculate",
    )
    scope_column.caption(
        "Calculation uses the existing guarded Example 3/4 engine path. "
        "Save/Load does not broaden methodology support."
    )
    if calculate:
        clear_manual_facility_result_state(st.session_state)
        try:
            result = run_manual_facility(template_id, edited_rows, unit_system)
            st.session_state["manual_facility_result"] = result_to_dict(result)
            st.session_state["manual_facility_result_context"] = (
                template_id,
                unit_system,
            )
            st.session_state["manual_facility_result_rows"] = facility_segment_result_rows(
                result, edited_rows
            )
            st.session_state["manual_facility_audit"] = (
                build_manual_facility_audit_record(
                    template_id, edited_rows, unit_system, result=result
                )
            )
        except HCMCalcError as exc:
            st.session_state["manual_facility_error"] = str(exc)
            st.session_state["manual_facility_audit"] = (
                build_manual_facility_audit_record(
                    template_id, edited_rows, unit_system, error=exc
                )
            )

    _render_manual_facility_project_file_controls(
        template_id, unit_system, edited_rows, template["template_label"]
    )

    error = st.session_state.get("manual_facility_error")
    audit = st.session_state.get("manual_facility_audit")
    if error is not None:
        st.error(f"Unsupported combination: {error}")
        with st.expander("Audit / details"):
            st.json(audit)
        return

    result_data = st.session_state.get("manual_facility_result")
    if result_data is None:
        st.info("Review the template-backed segment table and click Calculate facility.")
        return
    if st.session_state.get("manual_facility_result_context") != (
        template_id,
        unit_system,
    ):
        st.info("Calculate the selected template to replace the displayed facility result.")
        return

    outputs = result_data["outputs"]
    metric = unit_system == "metric"
    st.subheader("Facility summary")
    summary = st.columns(5)
    summary[0].metric(
        "Facility follower density",
        f"{outputs['facility_follower_density_followers_mi_ln'] / 1.609344:.2f} fol/km/ln"
        if metric
        else f"{outputs['facility_follower_density_followers_mi_ln']:.1f} fol/mi/ln",
    )
    summary[1].metric("Facility LOS", outputs["facility_level_of_service"])
    summary[2].metric(
        "Weighted average speed",
        f"{outputs['facility_average_speed_mph'] * 1.609344:.1f} km/h"
        if metric
        else f"{outputs['facility_average_speed_mph']:.1f} mph",
    )
    summary[3].metric("Segments", len(outputs["segments"]))
    summary[4].metric(
        "Total length",
        f"{outputs['facility_length_mi'] * 1.609344:.2f} km"
        if metric
        else f"{outputs['facility_length_mi']:.2f} mi",
    )

    st.subheader("Segment-level results")
    st.dataframe(
        st.session_state["manual_facility_result_rows"],
        hide_index=True,
        use_container_width=True,
        column_config={
            "segment_id": "Segment ID",
            "segment_name": "Segment name",
            "segment_type": "Segment type",
            "segment_length_mi": "Length (mi)",
            "average_speed_mph": "Average speed (mph)",
            "percent_followers": "Percent followers (%)",
            "follower_density_followers_mi_ln": "Follower density (fol/mi/ln)",
            "level_of_service": "LOS",
            "vertical_class": "Vertical class",
            "horizontal_curve_adjustment_applied": "Curve adjustment",
            "passing_lane": "Passing lane",
            "downstream_adjustment_applied": "Downstream adjustment",
            "key_warnings": "Key warnings",
        },
    )
    with st.expander("Assumptions / warnings"):
        render_list("Warnings", result_data["warnings"], "No warnings reported.")
        render_list("Assumptions", result_data["assumptions"], "No assumptions reported.")
        render_list(
            "Unsupported behavior notes",
            template["unsupported_behavior_notes"],
            "No unsupported behavior notes reported.",
        )
    with st.expander("Audit / details"):
        st.json(audit)
    render_export_report_section(
        "manual_facility_v0",
        result_data,
        unit_system,
        inputs=audit.get("facility_inputs", {}).get("segments", [])
        if isinstance(audit, dict)
        else [],
        audit_record=audit,
        template_id=template_id,
    )
    full_result = {
        "calculation_type": "manual_facility_v0",
        "template_id": template_id,
        "unit_system": unit_system,
        "engine_result": result_data,
        "audit_record": audit,
    }
    with st.expander("Download / export"):
        st.caption(
            "Project JSON restores the guarded worksheet. Result JSON exports the "
            "current calculation details."
        )
        st.json(full_result)
        st.download_button(
            "Download facility result JSON",
            data=json.dumps(full_result, indent=2),
            file_name=f"{template_id}-facility-result.json",
            mime="application/json",
            use_container_width=True,
        )


def _render_manual_facility_project_file_controls(
    template_id: str,
    unit_system: str,
    segment_rows: list[dict[str, Any]],
    template_name: str,
) -> None:
    """Render guarded facility project save and load controls."""

    stored_audit = st.session_state.get("manual_facility_audit")
    calculation_matches_inputs = (
        isinstance(stored_audit, dict)
        and stored_audit.get("template_id") == template_id
        and stored_audit.get("unit_system") == unit_system
        and stored_audit.get("facility_inputs", {}).get("segments") == segment_rows
    )
    project_json = create_manual_facility_project_json(
        template_id,
        unit_system,
        segment_rows,
        result=(
            st.session_state.get("manual_facility_result")
            if calculation_matches_inputs
            else None
        ),
        audit_record=stored_audit if calculation_matches_inputs else None,
    )
    with st.expander("Project file / Save and Load"):
        st.caption(
            f"Save or restore {template_name}. Facility projects remain template-backed."
        )
        st.download_button(
            "Download facility project JSON",
            data=project_json,
            file_name=f"{template_id}-manual-facility-project.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded_project = st.file_uploader(
            "Load facility project JSON",
            type=["json"],
            key="manual_facility_project_file_uploader",
        )
        if st.button(
            "Load facility project",
            disabled=uploaded_project is None,
            use_container_width=True,
        ):
            try:
                project = load_manual_facility_project_json(uploaded_project.getvalue())
            except ProjectFileError as exc:
                st.error(str(exc))
            else:
                st.session_state["manual_facility_pending_project"] = project
                st.rerun()


def _restore_manual_facility_project(project: dict[str, Any]) -> None:
    """Restore validated facility project data into worksheet session state."""

    unit_system = project["unit_system"]
    template_id = project["template_id"]
    st.session_state["facility_template_id"] = template_id
    st.session_state["facility_unit_label"] = unit_system.title()
    st.session_state["manual_facility_selection_context"] = (template_id, unit_system)
    st.session_state["manual_facility_editor_version"] = (
        st.session_state.get("manual_facility_editor_version", 0) + 1
    )
    st.session_state["manual_facility_segment_rows_seed"] = project["segment_rows"]
    for state_key, project_key in (
        ("manual_facility_result", "calculation_result"),
        ("manual_facility_audit", "audit"),
    ):
        if project.get(project_key) is None:
            st.session_state.pop(state_key, None)
        else:
            st.session_state[state_key] = project[project_key]
    result = project.get("calculation_result")
    if result is not None:
        st.session_state["manual_facility_result_context"] = (template_id, unit_system)
        st.session_state["manual_facility_result_rows"] = facility_segment_result_rows(
            _calculation_result_from_dict(result), project["segment_rows"]
        )
    st.session_state.pop("manual_facility_error", None)
    st.session_state["manual_facility_project_load_message"] = (
        "Facility project loaded. Review the restored template-backed inputs and "
        "click Calculate facility to calculate again."
    )


def _calculation_result_from_dict(result: dict[str, Any]) -> Any:
    """Provide attribute access needed by the facility result row adapter."""

    from types import SimpleNamespace

    return SimpleNamespace(outputs=result["outputs"])


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

    worksheet_column, result_column = st.columns([1.55, 1.0], gap="large")

    with worksheet_column:
        setup_column, schematic_column = st.columns([1.25, 1.0], gap="medium")
        with setup_column:
            st.markdown("**Setup**")
            setup_row_one = st.columns(2)
            unit_label = setup_row_one[0].radio(
                "Unit system",
                ["Metric", "Imperial"],
                index=0 if DEFAULT_UNIT_SYSTEM == "metric" else 1,
                horizontal=True,
                key="manual_unit_label",
            )
            unit_system = str(unit_label).lower()
            defaults = manual_defaults(unit_system)
            segment_type = setup_row_one[1].selectbox(
                "Segment type",
                list(SEGMENT_TYPE_LABELS),
                format_func=SEGMENT_TYPE_LABELS.__getitem__,
                key="manual_segment_type",
            )
            setup_row_two = st.columns(2)
            terrain_type = setup_row_two[0].selectbox(
                "Terrain type",
                ["level", "mountainous"],
                format_func=str.title,
                key="manual_terrain_type",
            )
            horizontal_alignment_label = setup_row_two[1].selectbox(
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
            st.caption("Unsupported combinations remain guarded.")

        with schematic_column:
            st.markdown("**Segment schematic**")
            schematic_path = get_segment_schematic_path(segment_type)
            if schematic_path is not None:
                st.image(schematic_path, width="stretch")
            st.caption("Schematic updates with segment type.")

        for name, default in defaults.items():
            if name == "heavy_vehicle_percent" and segment_type == "passing_lane":
                default = 8.0
            st.session_state.setdefault(f"manual_{name}_{unit_system}", default)

        metric = unit_system == "metric"
        with st.form(f"manual_single_segment_{unit_system}"):
            form_input_column = st.container()
            form_advanced_column = st.container()
            with form_input_column:
                st.markdown("**Geometry**")
                geometry_row_one = st.columns(3)
                segment_length = geometry_row_one[0].number_input(
                    f"Segment length ({'km' if metric else 'mi'})",
                    min_value=0.01,
                    key=f"manual_segment_length_{unit_system}",
                )
                posted_speed = geometry_row_one[1].number_input(
                    f"Posted speed / base speed ({'km/h' if metric else 'mph'})",
                    min_value=1.0,
                    key=f"manual_posted_speed_{unit_system}",
                )
                lane_width = geometry_row_one[2].number_input(
                    f"Lane width ({'m' if metric else 'ft'})",
                    min_value=0.01,
                    key=f"manual_lane_width_{unit_system}",
                )
                geometry_row_two = st.columns(3)
                shoulder_width = geometry_row_two[0].number_input(
                    f"Shoulder width ({'m' if metric else 'ft'})",
                    min_value=0.0,
                    key=f"manual_shoulder_width_{unit_system}",
                )
                access_density = geometry_row_two[1].number_input(
                    f"Access point density (points/{'km' if metric else 'mi'})",
                    min_value=0.0,
                    key=f"manual_access_point_density_{unit_system}",
                )
                if terrain_type == "mountainous":
                    grade_percent = geometry_row_two[2].number_input(
                        "Grade (%)",
                        key=f"manual_grade_percent_{unit_system}",
                    )
                    geometry_row_two[2].caption("Validated paths only.")
                else:
                    grade_percent = 0.0

                st.markdown("**Traffic**")
                traffic_row_one = st.columns(3)
                analysis_volume = traffic_row_one[0].number_input(
                    "Analysis-direction volume (veh/h)",
                    min_value=0.0,
                    key=f"manual_analysis_direction_volume_{unit_system}",
                )
                peak_hour_factor = traffic_row_one[1].number_input(
                    "Peak hour factor (PHF)",
                    min_value=0.01,
                    max_value=1.0,
                    key=f"manual_peak_hour_factor_{unit_system}",
                )
                heavy_vehicle_percent = traffic_row_one[2].number_input(
                    "Heavy vehicles (%)",
                    min_value=0.0,
                    max_value=100.0,
                    key=f"manual_heavy_vehicle_percent_{unit_system}",
                )
                opposing_volume = None
                if segment_type == "passing_zone":
                    traffic_row_two = st.columns(3)
                    opposing_volume = traffic_row_two[0].number_input(
                        "Opposing-direction volume (veh/h)",
                        min_value=1.0,
                        help=(
                            "Required for Passing Zone behavior and converted to "
                            "opposing demand flow using the submitted PHF."
                        ),
                        key=f"manual_opposing_direction_volume_{unit_system}",
                    )
                if segment_type == "passing_lane":
                    st.caption(
                        "Single-segment result only — downstream/facility effects "
                        "are not included here."
                    )

            with form_advanced_column:
                horizontal_subsegments: list[dict[str, Any]] = []
                curve_setup: dict[str, Any] | None = None
                generate_curve = False
                if horizontal_alignment == "horizontal_curves":
                    st.markdown("**Advanced / Optional**")
                    setup_defaults = curve_setup_defaults(unit_system, segment_length)
                    for name, default in setup_defaults.items():
                        st.session_state.setdefault(
                            f"manual_curve_setup_{name}_{unit_system}", default
                        )
                    with st.expander(
                        "Horizontal curve subsegments", expanded=False
                    ):
                        total_curve_length = st.number_input(
                            f"Total curve length ({'m' if metric else 'ft'})",
                            key=f"manual_curve_setup_total_curve_length_{unit_system}",
                        )
                        curve_radius = st.number_input(
                            f"Curve radius ({'m' if metric else 'ft'})",
                            key=f"manual_curve_setup_radius_{unit_system}",
                        )
                        superelevation = st.number_input(
                            "Superelevation (%)",
                            key=(
                                "manual_curve_setup_superelevation_percent_"
                                f"{unit_system}"
                            ),
                        )
                        central_angle = st.number_input(
                            "Central angle (deg)",
                            key=f"manual_curve_setup_central_angle_deg_{unit_system}",
                        )
                        horizontal_class = st.number_input(
                            "Horizontal class",
                            min_value=1,
                            max_value=5,
                            step=1,
                            key=f"manual_curve_setup_horizontal_class_{unit_system}",
                        )
                        subsegment_count = st.number_input(
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
                            initial_curve_subsegments(
                                horizontal_alignment, unit_system, segment_length
                            ),
                        )
                        st.caption(
                            "Review or edit generated rows. Subsegment lengths must "
                            f"total the segment length; lengths and radii are in "
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
                                "superelevation_percent": (
                                    st.column_config.NumberColumn(
                                        "Superelevation (%)"
                                    )
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
        if horizontal_alignment == "straight":
            st.markdown("**Advanced / Optional**")
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
        st.markdown("**Results**")
        stored_result = st.session_state.get("manual_segment_result")
        audit_record = st.session_state.get("manual_segment_audit")
        stored_error = st.session_state.get("manual_segment_error")
        if stored_error is not None:
            st.error(stored_error)
            render_audit_record(audit_record)
            return
        if stored_result is None:
            st.caption("Run calculation to see results.")
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

    st.caption("Save or load project JSON to preserve inputs.")
    st.download_button(
        "Download project JSON",
        data=project_json,
        file_name="manual-single-segment-project.json",
        mime="application/json",
        use_container_width=False,
    )
    with st.expander("Load project", expanded=False):
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
        if index % 2 == 0:
            metric_columns = st.columns(2)
        metric_columns[index % 2].metric(
            metric["label"], format_display_metric(name, metric, unit_system)
        )

    with st.expander("Calculation details & audit", expanded=False):
        st.markdown("**Assumptions**")
        for assumption in result_data["assumptions"]:
            st.markdown(f"- {assumption}")
        st.markdown("**Warnings**")
        for warning in result_data["warnings"]:
            st.markdown(f"- {warning}")
        st.markdown("**Intermediate values**")
        st.dataframe(
            result_data["intermediate_values"],
            hide_index=True,
            use_container_width=True,
        )
        if audit_record is not None:
            st.markdown("**Audit record**")
            st.caption(
                "Submitted values, engine-native imperial inputs, scope status, and "
                "calculation metadata."
            )
            st.json(audit_record)

    with st.expander("Export", expanded=False):
        render_export_report_downloads(
            "manual_single_segment",
            result_data,
            unit_system,
            inputs=audit_record.get("user_inputs", {})
            if isinstance(audit_record, dict)
            else {},
            audit_record=audit_record,
        )

    full_result = {
        "unit_system": unit_system,
        "display_outputs": metrics,
        "engine_result": result_data,
    }
    full_result_json = json.dumps(full_result, indent=2)
    with st.expander("Full JSON", expanded=False):
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


def render_export_report_section(
    calculation_type: str,
    result_data: dict[str, Any],
    unit_system: str,
    *,
    inputs: dict[str, Any] | list[dict[str, Any]],
    audit_record: dict[str, Any] | None,
    template_id: str | None = None,
) -> None:
    """Render compact report downloads from the existing calculated result."""

    with st.expander("Export / Report"):
        render_export_report_downloads(
            calculation_type,
            result_data,
            unit_system,
            inputs=inputs,
            audit_record=audit_record,
            template_id=template_id,
        )


def render_export_report_downloads(
    calculation_type: str,
    result_data: dict[str, Any],
    unit_system: str,
    *,
    inputs: dict[str, Any] | list[dict[str, Any]],
    audit_record: dict[str, Any] | None,
    template_id: str | None = None,
) -> None:
    """Render report downloads in the caller's selected container."""

    try:
        report = build_report(
            calculation_type,
            result_data,
            unit_system,
            inputs=inputs,
            audit_record=audit_record,
            template_id=template_id,
        )
        downloads = (
            ("Download CSV", "csv", "csv", "text/csv"),
            (
                "Download Excel",
                "xlsx",
                "xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            ("Download Markdown", "markdown", "md", "text/markdown"),
            ("Download Report JSON", "json", "json", "application/json"),
        )
        rendered = [
            (
                label,
                export_report(report, export_format),
                report_filename(report, extension),
                mime,
            )
            for label, export_format, extension, mime in downloads
        ]
    except ReportingError as exc:
        st.error(f"Report export unavailable: {exc}")
        return

    st.caption(
        "Exports reflect this calculated result in the selected display unit "
        "system. They do not broaden methodology support."
    )
    columns = st.columns(2)
    for index, (label, data, filename, mime) in enumerate(rendered):
        columns[index % 2].download_button(
            label,
            data=data,
            file_name=filename,
            mime=mime,
            use_container_width=True,
            key=f"{calculation_type}_{filename}",
        )


def main() -> None:
    """Run the single-page Streamlit calculator."""

    st.set_page_config(page_title="HCM Calculator", layout="wide")
    apply_ui_styles()
    header_left, header_right = st.columns([1.4, 1.0], gap="large")
    with header_left:
        st.markdown("**HCM Calculator** - Two-Lane and Multilane Highway")
    with header_right:
        mode_label = st.radio(
            "Calculator mode",
            ["Two-Lane", "Facility", "Multilane", "Examples"],
            horizontal=True,
            label_visibility="collapsed",
            key="calculator_mode",
        )
    st.caption(SCOPE_NOTICE)
    mode = {
        "Two-Lane": "Manual single segment calculator",
        "Facility": "Manual Facility Calculator v0.1",
        "Multilane": "Manual Multilane Highway Segment v0.1",
        "Examples": "Validated examples / QA",
    }[mode_label]
    if mode == "Manual single segment calculator":
        render_manual_single_segment_calculator()
    elif mode == "Manual Facility Calculator v0.1":
        render_manual_facility_calculator()
    elif mode == "Manual Multilane Highway Segment v0.1":
        render_manual_multilane_calculator()
    else:
        render_validated_case_viewer()
    st.divider()
    st.caption(LIMITATIONS_FOOTER)


if __name__ == "__main__":
    main()
