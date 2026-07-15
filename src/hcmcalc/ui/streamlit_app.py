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
from hcmcalc.ui.manual_freeway import (
    build_manual_freeway_audit_record,
    clear_manual_freeway_state,
    freeway_display_outputs,
    freeway_preset_options,
    freeway_preset_ui_inputs,
    freeway_ui_inputs_to_engine,
    load_freeway_preset,
    run_manual_freeway,
)
from hcmcalc.ui.manual_multilane import (
    build_manual_multilane_audit_record,
    clear_manual_multilane_state,
    load_multilane_template,
    multilane_display_outputs,
    multilane_template_options,
    multilane_template_ui_inputs,
    multilane_ui_inputs_to_engine,
    run_manual_multilane,
)
from hcmcalc.ui.manual_weaving import (
    build_manual_weaving_audit_record,
    clear_manual_weaving_state,
    run_manual_weaving,
    weaving_display_outputs,
    weaving_preset_options,
    weaving_preset_ui_inputs,
    weaving_ui_inputs_to_engine,
)
from hcmcalc.ui.weaving_diagrams import get_weaving_diagram, get_weaving_diagram_subtype
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.layout import (
    render_calculator_shell,
    render_export_report_section_container,
    render_page_header,
    render_project_load_section,
    render_project_output_section,
    render_section_label,
    render_starting_values_section,
    render_validation_basis_and_limitations,
)
from hcmcalc.ui.project_io import (
    ProjectFileError,
    create_manual_freeway_project_json,
    create_manual_facility_project_json,
    create_manual_multilane_project_json,
    create_manual_project_json,
    load_manual_freeway_project_json,
    load_manual_facility_project_json,
    load_manual_multilane_project_json,
    create_manual_weaving_project_json,
    load_manual_weaving_project_json,
    load_manual_project_json,
    project_load_message,
    project_presentation_locale,
)
from hcmcalc.ui.i18n import SUPPORTED_LOCALES, normalize_locale, translate
from hcmcalc.ui.result_view import (
    compact_rows,
    format_display_metric,
    render_result_summary_panel,
)
from hcmcalc.ui.reporting import (
    ReportingError,
    build_report,
    export_report,
    report_filename,
)
from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.supported_workflows import (
    APP_MODE_LABELS,
    AUDIT_EXPANDER_LABEL,
    BASIC_FREEWAY_RAMP_DENSITY_HELP,
    BASIC_FREEWAY_RAMP_DENSITY_LABEL,
    CALCULATION_DETAILS_LABEL,
    EXPORT_REPORT_LABEL,
    PRERUN_RESULTS_PLACEHOLDER,
    STARTING_VALUES_LABEL,
    SUPPORTED_WORKFLOW_SECTIONS,
    resolve_app_view,
)
from hcmcalc.ui.units import (
    DEFAULT_UNIT_SYSTEM,
    MILES_TO_KILOMETERS,
    display_outputs,
    manual_defaults,
)
from hcmcalc.ui.workflow_state import (
    CALCULATED,
    mark_calculated,
    workflow_status,
    localized_workflow_status,
)


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "example_inputs.yaml"
SEGMENT_TYPE_LABELS = {
    "passing_constrained": "Passing constrained",
    "passing_zone": "Passing zone",
    "passing_lane": "Passing lane",
}
FACILITY_DEFAULT_LABELS = {
    "level_example_3": "Level terrain facility defaults",
    "mountainous_example_4": "Mountainous facility defaults",
}
MULTILANE_DEFAULT_LABELS = {
    "MLH-CH26-004-EB": "Eastbound segment defaults",
    "MLH-CH26-004-WB": "Westbound segment defaults",
}
FREEWAY_DEFAULT_LABELS = {
    "BF-CH26-001": "Basic freeway segment defaults",
}
IMPLEMENTED_CASE_IDS = (
    "TLH-CH15-001",
    "TLH-CH15-002",
    "TLH-CH15-003",
    "TLH-CH15-004",
)
SCOPE_NOTICE = (
    "Manual HCM worksheets with auditable inputs, calculation details, project "
    "files, and report exports."
)
LIMITATIONS_FOOTER = (
    "Use each calculator's Validation basis and limitations section for method "
    "coverage details."
)


def _ui_locale() -> str:
    """Read the session-scoped presentation locale without touching calculation state."""

    return normalize_locale(st.session_state.get("ui_locale"))


def _weaving_text(key: str, **params: Any) -> str:
    return translate(f"weaving.{key}", _ui_locale(), **params)


def _weaving_preset_label(preset_id: str) -> str:
    normalized = preset_id.lower().replace("-", "_")
    return _weaving_text(f"preset.{normalized}")


def _restore_project_locale(project: dict[str, Any]) -> None:
    """Restore explicitly stored project presentation metadata, if present."""

    saved_locale = project_presentation_locale(project)
    if saved_locale is not None:
        st.session_state["ui_locale"] = saved_locale


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


def render_calculation_status(
    workflow: str, inputs: dict[str, Any], target: Any | None = None
) -> bool:
    """Render the shared compact freshness state and return export eligibility."""

    status = workflow_status(st.session_state, workflow, inputs)
    (target or st).caption(
        translate(
            "status.calculation",
            _ui_locale(),
            status=localized_workflow_status(status, _ui_locale()),
        )
    )
    return status == CALCULATED


def render_result(result_id: str, result_data: dict[str, Any]) -> None:
    """Render an auditable calculation result."""

    outputs = result_data["outputs"]
    segments = outputs.get("segments")
    full_result = {"result_id": result_id, **result_data}
    full_result_json = json.dumps(full_result, indent=2)

    st.subheader(translate("result.key_summary", _ui_locale()))
    summary_columns = st.columns(3)
    summary_columns[0].metric(translate("common.result", _ui_locale()), result_id)
    summary_columns[1].metric(translate("common.method", _ui_locale()), result_data["method"])
    summary_columns[2].metric(translate("common.facility_type", _ui_locale()), result_data["facility_type"])

    st.subheader(translate("result.outputs", _ui_locale()))
    scalar_outputs = compact_rows(outputs)
    if scalar_outputs:
        st.dataframe(scalar_outputs, hide_index=True, width="stretch")
    else:
        st.caption(translate("common.no_outputs", _ui_locale()))

    if isinstance(segments, list):
        st.subheader(translate("result.segment_outputs", _ui_locale()))
        st.dataframe(segments, hide_index=True, width="stretch")

    render_list(translate("common.assumptions", _ui_locale()), result_data["assumptions"], translate("common.no_assumptions", _ui_locale()))
    render_list(translate("common.warnings", _ui_locale()), result_data["warnings"], translate("common.no_warnings", _ui_locale()))

    with st.expander(translate("common.intermediate_values", _ui_locale())):
        st.dataframe(
            result_data["intermediate_values"],
            hide_index=True,
            width="stretch",
        )

    with st.expander(translate("result.full_json", _ui_locale())):
        st.json(full_result)

    st.download_button(
        translate("result.download_json", _ui_locale()),
        data=full_result_json,
        file_name=f"{result_id}-result.json",
        mime="application/json",
    )


def render_validated_case_viewer() -> None:
    """Render the implemented validation fixture cases."""

    render_page_header(
        "Examples / Validation",
        "Validation examples and reference-backed checks for implemented paths.",
    )
    st.caption(
        "Calculator pages remain the primary workflow for engineering data entry."
    )
    render_validation_basis_and_limitations(
        validation_basis=(
            "Example-backed regression cases preserve the implemented Chapter 26 "
            "validation baselines."
        ),
        supported_scope="Reference-backed checks for implemented example paths.",
        not_supported=(
            "Validation examples are not a substitute workflow for engineering "
            "data entry."
        ),
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
        st.caption("Fixture file")
        st.markdown(f"`{FIXTURE_PATH.name}`")
        with st.expander("Show full fixture path", expanded=False):
            st.code(str(FIXTURE_PATH), language=None)
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


def render_supported_workflows_page() -> None:
    """Render the app-wide supported workflow and scope summary."""

    render_page_header(
        "Supported Workflows",
        "Calculator modes, project files, reporting, and reference checks.",
    )
    st.markdown(
        "Choose a calculator, optionally load a project, enter inputs, run the "
        "calculation, review results, inspect details and audit records, then "
        "save or export."
    )

    for section in SUPPORTED_WORKFLOW_SECTIONS:
        st.subheader(section["title"])
        columns = st.columns([1.1, 1.1, 0.9], gap="medium")
        with columns[0]:
            st.markdown("**Supported**")
            for item in section["supported"]:
                st.markdown(f"- {item}")
        with columns[1]:
            st.markdown("**Scope limits**")
            for item in section["limitations"]:
                st.markdown(f"- {item}")
        with columns[2]:
            st.markdown("**Save/Load and Export availability**")
            st.caption(section["save_load_export"])


def render_manual_multilane_calculator() -> None:
    """Render the bounded Multilane segment worksheet."""

    pending_project = st.session_state.pop("manual_multilane_pending_project", None)
    if pending_project is not None:
        _restore_manual_multilane_project(pending_project)
    load_message = st.session_state.pop("manual_multilane_project_load_message", None)
    if load_message is not None:
        st.success(load_message)

    render_page_header(
        "Multilane Highway Segment Calculator",
        "Bounded one-direction Multilane Highway Segment analysis within the implemented HCM scope.",
    )
    status_placeholder = st.empty()
    input_column, result_column = render_calculator_shell()
    template_options = multilane_template_options()
    with input_column:
        render_project_load_section(_render_manual_multilane_load_controls)
        render_section_label("Setup")
        st.caption("Analysis type: Multilane Highway Segment.")
        unit_label = st.radio(
            "Unit system",
            ["Metric", "Imperial"],
            horizontal=True,
            key="manual_multilane_unit_label",
        )
        st.caption(
            "Calculations remain engine-native Imperial; Metric values are "
            "converted at the UI boundary."
        )
        with st.expander(STARTING_VALUES_LABEL, expanded=False):
            render_starting_values_section("Use example defaults")
            template_id = st.selectbox(
                "Defaults",
                list(template_options),
                format_func=lambda value: MULTILANE_DEFAULT_LABELS.get(
                    value, template_options[value]
                ),
                key="multilane_template_id",
                label_visibility="collapsed",
            )
            st.caption(
                "HCM Chapter 26 Example 4 eastbound/westbound remains optional "
                "defaults and regression evidence."
            )
    unit_system = unit_label.lower()
    template_context = (template_id, unit_system)
    if st.session_state.get("manual_multilane_template_context") != template_context:
        clear_manual_multilane_state(st.session_state)
        if "manual_multilane_template_context" in st.session_state:
            st.session_state["manual_multilane_reset_message"] = (
                "Unit system or starting values changed. Inputs were reset to the "
                "selected starting values."
            )
        st.session_state["manual_multilane_template_context"] = template_context
    reset_message = st.session_state.pop("manual_multilane_reset_message", None)
    if reset_message is not None:
        st.caption(reset_message)
    try:
        template = load_multilane_template(template_id)
    except (HCMCalcError, ValueError) as exc:
        st.error(str(exc))
        return

    inputs = template["inputs"]
    ui_inputs = multilane_template_ui_inputs(template_id, unit_system)
    metric = unit_system == "metric"
    length_unit = "km" if metric else "ft"
    speed_unit = "km/h" if metric else "mph"
    width_unit = "m" if metric else "ft"
    access_unit = "points/km" if metric else "per mi"
    with input_column:
        ffs_source = st.radio(
            "Free-flow speed source",
            ["Estimated", "Measured"],
            index=0 if ui_inputs.get("ffs_source", "estimated") == "estimated" else 1,
            horizontal=True,
            key=f"manual_multilane_input_ffs_source_{template_id}_{unit_system}",
            help=(
                "Estimated FFS uses posted speed and roadway adjustments. "
                "Measured FFS uses the supplied speed and does not apply roadway-geometry adjustments."
            ),
        ).lower()
        with st.form(f"multilane_form_{template_id}"):
            render_section_label("Roadway / Geometry")
            roadway_columns = st.columns(2)
            number_of_lanes = roadway_columns[0].number_input(
                "Lanes in analysis direction",
                min_value=2,
                step=1,
                value=int(ui_inputs["number_of_lanes"]),
                key=f"manual_multilane_input_lanes_{template_id}_{unit_system}",
            )
            segment_length = roadway_columns[1].number_input(
                f"Segment length ({length_unit})",
                min_value=0.001,
                value=float(ui_inputs["segment_length"]),
                key=f"manual_multilane_input_length_{template_id}_{unit_system}",
            )
            free_flow_speed = None
            if ffs_source == "measured":
                free_flow_speed = roadway_columns[0].number_input(
                    f"Measured free-flow speed ({speed_unit})",
                    min_value=1.0,
                    value=float(ui_inputs.get("free_flow_speed") or ui_inputs["posted_speed_limit"]),
                    key=f"manual_multilane_input_measured_ffs_{template_id}_{unit_system}",
                    help="Roadway-geometry FFS adjustments are not applied in measured mode.",
                )
                posted_speed_limit = lane_width = roadside_lateral_clearance = None
                access_point_density = median_type = left_side_lateral_clearance = None
            else:
                posted_speed_limit = roadway_columns[0].number_input(
                    f"Posted speed limit ({speed_unit})", min_value=1.0,
                    value=float(ui_inputs["posted_speed_limit"]),
                    key=f"manual_multilane_input_speed_{template_id}_{unit_system}",
                    help="Base FFS is derived from the posted speed and HCM adjustments.",
                )
                lane_width = roadway_columns[1].number_input(
                    f"Lane width ({width_unit})", min_value=0.1,
                    value=float(ui_inputs["lane_width"]),
                    key=f"manual_multilane_input_lane_width_{template_id}_{unit_system}",
                )
                roadside_lateral_clearance = roadway_columns[0].number_input(
                    f"Right-side lateral clearance ({width_unit})", min_value=0.0,
                    value=float(ui_inputs["roadside_lateral_clearance"]),
                    key=f"manual_multilane_input_clearance_{template_id}_{unit_system}",
                    help="Clearance from the right edge of the travel lane to the roadside obstruction.",
                )
                median_type = roadway_columns[1].selectbox(
                    "Median type", ["twltl", "undivided", "divided"],
                    index=["twltl", "undivided", "divided"].index(ui_inputs.get("median_type", "twltl")),
                    key=f"manual_multilane_input_median_{template_id}_{unit_system}",
                    help="A divided median requires a separate left-side clearance; TWLTL and undivided use the HCM 6 ft left-side rule.",
                )
                left_side_lateral_clearance = None
                if median_type == "divided":
                    left_side_lateral_clearance = roadway_columns[0].number_input(
                        f"Left-side lateral clearance ({width_unit})", min_value=0.0,
                        value=float(ui_inputs.get("left_side_lateral_clearance", 6.0)),
                        key=f"manual_multilane_input_left_clearance_{template_id}_{unit_system}",
                        help="Required for divided-median estimated FFS; measured FFS does not use it.",
                    )
                access_point_density = roadway_columns[1].number_input(
                    f"Access point density ({access_unit})", min_value=0.0,
                    value=float(ui_inputs["access_point_density"]),
                    key=f"manual_multilane_input_access_{template_id}_{unit_system}",
                )

            render_section_label("Traffic")
            traffic_columns = st.columns(2)
            demand_volume_veh_h = traffic_columns[0].number_input(
                "Demand volume (veh/h)",
                min_value=1.0,
                value=float(ui_inputs["demand_volume_veh_h"]),
                key=f"manual_multilane_input_demand_{template_id}_{unit_system}",
            )
            peak_hour_factor = traffic_columns[1].number_input(
                "Peak hour factor",
                min_value=0.01,
                max_value=1.0,
                value=float(ui_inputs["peak_hour_factor"]),
                key=f"manual_multilane_input_phf_{template_id}_{unit_system}",
            )
            heavy_vehicle_percent = traffic_columns[0].number_input(
                "Heavy vehicles (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(ui_inputs["heavy_vehicle_percent"]),
                key=f"manual_multilane_input_heavy_{template_id}_{unit_system}",
            )
            grade_percent = traffic_columns[1].number_input(
                "Grade (%)",
                value=float(ui_inputs["grade_percent"]),
                key=f"manual_multilane_input_grade_{template_id}_{unit_system}",
            )
            render_section_label("Heavy vehicles / PCE")
            pce_mode = st.radio(
                "Passenger-car-equivalent source", ["Internal HCM lookup", "External override"],
                index=0 if ui_inputs.get("pce_mode", "internal") == "internal" else 1,
                horizontal=True, key=f"manual_multilane_input_pce_mode_{template_id}_{unit_system}",
                help="Internal lookup is bounded to printed HCM table combinations. Use an external PCE when a combination is unsupported.",
            )
            passenger_car_equivalent = None
            terrain_type = truck_mix = None
            if pce_mode == "External override":
                passenger_car_equivalent = traffic_columns[1].number_input(
                    "External passenger-car equivalent",
                    min_value=0.01,
                    value=float(ui_inputs.get("passenger_car_equivalent") or 2.24),
                    key=f"manual_multilane_input_pce_{template_id}_{unit_system}",
                    help="Positive, finite PCE supplied by the user. Internal lookup is bypassed.",
                )
            else:
                terrain_type = traffic_columns[0].selectbox(
                    "PCE terrain treatment", ["level", "rolling", "specific_grade"],
                    index=["level", "rolling", "specific_grade"].index(ui_inputs.get("terrain_type", "specific_grade")),
                    key=f"manual_multilane_input_terrain_{template_id}_{unit_system}",
                )
                if terrain_type == "specific_grade":
                    mixes = ["default_30_sut_70_tt", "equal_50_sut_50_tt", "majority_70_sut_30_tt"]
                    truck_mix = traffic_columns[1].selectbox(
                        "Truck mix", mixes, index=mixes.index(ui_inputs.get("truck_mix", mixes[0])),
                        key=f"manual_multilane_input_truck_mix_{template_id}_{unit_system}",
                        help="Only the printed SUT/TT mixtures are supported; the terminal >25% category requires an external PCE.",
                    )
            st.caption(
                "Driver population factor is fixed at 1.0 because the bounded Multilane method has no adjustable factor."
            )
            run_multilane = st.form_submit_button(
                "Run calculation", type="primary", width="stretch"
            )

        displayed_inputs = {
            "number_of_lanes": int(number_of_lanes),
            "segment_length": segment_length,
            "demand_volume_veh_h": demand_volume_veh_h,
            "peak_hour_factor": peak_hour_factor,
            "heavy_vehicle_percent": heavy_vehicle_percent,
            "grade_percent": grade_percent,
            "ffs_source": ffs_source,
            "pce_mode": "external" if pce_mode == "External override" else "internal",
        }
        if ffs_source == "measured":
            displayed_inputs["free_flow_speed"] = free_flow_speed
        else:
            displayed_inputs.update({
                "posted_speed_limit": posted_speed_limit,
                "lane_width": lane_width,
                "roadside_lateral_clearance": roadside_lateral_clearance,
                "median_type": median_type,
                "access_point_density": access_point_density,
            })
            if left_side_lateral_clearance is not None:
                displayed_inputs["left_side_lateral_clearance"] = left_side_lateral_clearance
        if passenger_car_equivalent is not None:
            displayed_inputs["passenger_car_equivalent"] = passenger_car_equivalent
        if terrain_type is not None:
            displayed_inputs["terrain_type"] = terrain_type
        if truck_mix is not None:
            displayed_inputs["truck_mix"] = truck_mix
        submitted_inputs = multilane_ui_inputs_to_engine(
            displayed_inputs, inputs, unit_system
        )
        multilane_workflow_inputs = {
            "method_identifier": "hcm7_multilane_los",
            "input_contract": "phase_8",
            "effective_engine_inputs": submitted_inputs,
        }
        multilane_is_current = render_calculation_status(
            "manual_multilane", multilane_workflow_inputs, status_placeholder
        )
        def render_multilane_project_download() -> None:
            stored_audit = st.session_state.get("manual_multilane_audit")
            calculation_matches_inputs = (
                multilane_is_current
                and
                isinstance(stored_audit, dict)
                and stored_audit.get("displayed_inputs") == displayed_inputs
                and stored_audit.get("submitted_inputs") == submitted_inputs
                and stored_audit.get("unit_system") == unit_system
                and stored_audit.get("template_id") == template_id
            )
            project_json = create_manual_multilane_project_json(
                template_id,
                unit_system,
                displayed_inputs,
                result=st.session_state.get("manual_multilane_result")
                if calculation_matches_inputs
                else None,
                audit_record=stored_audit if calculation_matches_inputs else None,
                locale=_ui_locale(),
            )
            st.download_button(
                "Save project",
                data=project_json,
                file_name=f"{template_id}-manual-multilane-project.json",
                mime="application/json",
                width="stretch",
            )

    if run_multilane:
        st.session_state.pop("manual_multilane_result", None)
        st.session_state.pop("manual_multilane_error", None)
        try:
            result = run_manual_multilane(submitted_inputs)
            st.session_state["manual_multilane_result"] = result_to_dict(result)
            st.session_state["manual_multilane_audit"] = (
                build_manual_multilane_audit_record(
                    template_id,
                    submitted_inputs,
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    result=result,
                )
            )
            mark_calculated(
                st.session_state, "manual_multilane", multilane_workflow_inputs
            )
            multilane_is_current = render_calculation_status(
                "manual_multilane", multilane_workflow_inputs, status_placeholder
            )
        except HCMCalcError as exc:
            st.session_state["manual_multilane_error"] = str(exc)
            st.session_state["manual_multilane_audit"] = (
                build_manual_multilane_audit_record(
                    template_id,
                    submitted_inputs,
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    error=exc,
                )
            )

    with result_column:
        render_validation_basis_and_limitations(
            validation_basis=(
                "HCM7 Chapter 26 Example Problem 4 eastbound and westbound "
                "optional defaults and regression evidence."
            ),
            supported_scope=(
                "Bounded Multilane Highway Segment calculator for one-direction "
                "segment analysis within the implemented HCM scope. Metric values "
                "are converted at the UI boundary."
            ),
            not_supported=(
                "Basic Freeway, ramps, weaving, merge/diverge, managed lanes, "
                "work zones, reliability, and facility/corridor workflows. "
                "Unsupported methodology branches are rejected by engine validation."
            ),
        )
        st.markdown("**Results**")
        error = st.session_state.get("manual_multilane_error")
        audit = st.session_state.get("manual_multilane_audit")
        if error is not None:
            st.error(f"Unsupported Multilane case: {error}")
            with st.expander(AUDIT_EXPANDER_LABEL, expanded=False):
                st.json(audit)
            render_project_output_section(
                "Save the current guarded Multilane Segment worksheet and result.",
                render_multilane_project_download,
            )
            return
        result_data = st.session_state.get("manual_multilane_result")
        if result_data is None:
            st.caption(PRERUN_RESULTS_PLACEHOLDER)
            render_project_output_section(
                "Save the current guarded Multilane Segment worksheet and result.",
                render_multilane_project_download,
            )
            return

        outputs = result_data["outputs"]
        result_unit_system = (
            str(audit.get("unit_system", unit_system))
            if isinstance(audit, dict)
            else unit_system
        )
        display = multilane_display_outputs(outputs, result_unit_system)
        def predicted(metric: dict[str, Any], precision: str = ".1f") -> str:
            value = metric["value"]
            return (
                f"{value:{precision}} {metric['unit']}"
                if value is not None
                else "Not predicted"
            )
        render_result_summary_panel(
            primary_label="Level of service",
            primary_value=str(outputs["level_of_service"]),
            primary_kind="los",
            hero_supporting_label="Density",
            hero_supporting_value=predicted(display["density"]),
            secondary_metrics=[
                {
                    "label": "Speed used for density",
                    "value": predicted(display["speed_used_for_density"]),
                },
                {
                    "label": "Demand flow rate",
                    "value": (
                        f"{display['demand_flow_rate']['value']:.0f} "
                        f"{display['demand_flow_rate']['unit']}"
                    ),
                },
                {
                    "label": "Capacity",
                    "value": (
                        f"{display['capacity']['value']:.0f} "
                        f"{display['capacity']['unit']}"
                    ),
                },
                {
                    "label": "Capacity check",
                    "value": outputs["capacity_check"].replace("_", " "),
                },
                {"label": "FFS source", "value": outputs["ffs_source"]},
                {
                    "label": "Adjusted free-flow speed",
                    "value": (
                        f"{display['adjusted_free_flow_speed']['value']:.1f} "
                        f"{display['adjusted_free_flow_speed']['unit']}"
                    ),
                },
                {
                    "label": "Base free-flow speed",
                    "value": (
                        f"{display['base_free_flow_speed']['value']:.1f} "
                        f"{display['base_free_flow_speed']['unit']}"
                    ),
                },
                {
                    "label": "Heavy vehicle adjustment factor",
                    "value": f"{outputs['heavy_vehicle_adjustment_factor']:.3f}",
                },
                {
                    "label": "Demand / capacity",
                    "value": f"{outputs['demand_capacity_ratio']:.3f}",
                },
                {
                    "label": "PCE",
                    "value": f"{outputs['passenger_car_equivalent']:.2f} ({outputs['pce_source']})",
                },
            ],
        )

        with st.expander(CALCULATION_DETAILS_LABEL, expanded=False):
            st.markdown("**Free-flow speed audit**")
            st.json({
                "ffs_source": outputs["ffs_source"],
                "base_free_flow_speed_mph": outputs["base_free_flow_speed_mph"],
                "lane_width_adjustment_mph": outputs["lane_width_adjustment_mph"],
                "total_lateral_clearance_adjustment_mph": outputs["total_lateral_clearance_adjustment_mph"],
                "median_type_adjustment_mph": outputs["median_type_adjustment_mph"],
                "access_point_adjustment_mph": outputs["access_point_adjustment_mph"],
                "adjusted_free_flow_speed_mph": outputs["adjusted_free_flow_speed_mph"],
            })
            st.markdown("**Heavy-vehicle / PCE audit**")
            st.json({
                key: outputs.get(key)
                for key in (
                    "passenger_car_equivalent", "pce_source", "pce_lookup_path",
                    "effective_grade_for_pce_percent", "effective_grade_length_mi_for_pce",
                    "truck_composition", "heavy_vehicle_adjustment_factor",
                )
            })
            render_list("Assumptions", result_data["assumptions"], "No assumptions reported.")
            render_list("Warnings", result_data["warnings"], "No warnings reported.")
            render_list(
                "Unsupported scope notes",
                outputs["unsupported_scope_notes"],
                "No unsupported scope notes reported.",
            )
        with st.expander(AUDIT_EXPANDER_LABEL, expanded=False):
            st.json(audit)
            st.dataframe(
                result_data["intermediate_values"],
                hide_index=True,
                width="stretch",
            )
        with st.expander("Full JSON"):
            st.json(
                {
                    "calculation_type": "manual_multilane_v0",
                    "unit_system": result_unit_system,
                    "display_outputs": display,
                    "engine_result": result_data,
                    "audit_record": audit,
                }
            )
        render_project_output_section(
            "Save the current guarded Multilane Segment worksheet and result.",
            render_multilane_project_download,
        )
        if multilane_is_current:
            render_export_report_section(
                "manual_multilane_v0", result_data, result_unit_system,
                inputs=(audit.get("displayed_inputs", displayed_inputs) if isinstance(audit, dict) else displayed_inputs),
                audit_record=audit, template_id=template_id,
            )
        else:
            st.caption("Export unavailable until recalculation completes.")


def _render_weaving_configuration_reference(
    *,
    configuration: str,
    number_of_lanes: int,
    number_of_weaving_lanes: int,
    entry_side: str,
    exit_side: str,
    lc_rf: int | None,
    lc_fr: int | None,
    lc_rr: int | None,
) -> None:
    """Render the owner-authorized, presentation-only configuration reference."""

    render_section_label(_weaving_text("reference.title"))
    subtype = get_weaving_diagram_subtype(configuration, number_of_weaving_lanes)
    diagram = get_weaving_diagram(subtype)
    if diagram is None:
        st.info(_weaving_text("reference.incomplete"))
        return
    title = _weaving_text(f"reference.subtype.{subtype}")
    movement_text = _weaving_text("movement_caption")
    lane_changes = ", ".join(
        f"{label}={value}"
        for label, value in (("LC_RF", lc_rf), ("LC_FR", lc_fr), ("LC_RR", lc_rr))
        if value is not None
    )
    st.markdown(f"**{title}**")
    st.image(str(diagram.path), width="stretch")
    st.caption(_weaving_text("reference.caption"))
    st.caption(
        _weaving_text(
            "reference.geometry_summary",
            lanes=number_of_lanes,
            weaving_lanes=number_of_weaving_lanes,
            entry=_weaving_text(f"side.{entry_side}"),
            exit=_weaving_text(f"side.{exit_side}"),
            lane_changes=lane_changes or _weaving_text("schematic.option_none"),
        )
    )
    st.markdown(f"**{_weaving_text('reference.movement_legend')}** {movement_text}")
    st.caption(_weaving_text("reference.accessible_text", title=title))


def render_manual_weaving_calculator() -> None:
    """Render the compact, public-facade-only HCM 7.0 weaving worksheet."""

    pending = st.session_state.pop("manual_weaving_pending_project", None)
    if pending is not None:
        _restore_manual_weaving_project(pending)
    load_message = st.session_state.pop("manual_weaving_project_load_message", None)
    if load_message:
        st.success(load_message)
    render_page_header(_weaving_text("title"), _weaving_text("subtitle"))
    status_placeholder = st.empty()
    input_column, result_column = render_calculator_shell()
    with input_column:
        render_project_load_section(_render_manual_weaving_load_controls)
        render_section_label(_weaving_text("setup"))
        st.caption(_weaving_text("method_caption"))
        unit_label = st.radio(
            _weaving_text("unit_system"),
            ["Metric", "Imperial"],
            horizontal=True,
            format_func=lambda item: _weaving_text(f"unit.{item.lower()}"),
            key="manual_weaving_unit_label",
        )
        preset_id = st.selectbox(
            _weaving_text("validation_preset"),
            list(weaving_preset_options()),
            format_func=_weaving_preset_label,
            key="manual_weaving_preset_id",
        )
    unit_system = unit_label.lower()
    context = (preset_id, unit_system)
    if st.session_state.get("manual_weaving_preset_context") != context:
        clear_manual_weaving_state(st.session_state)
        st.session_state["manual_weaving_preset_context"] = context
    ui = st.session_state.get("manual_weaving_loaded_displayed") or weaving_preset_ui_inputs(preset_id, unit_system)
    metric = unit_system == "metric"
    length_unit, speed_unit, width_unit = ("m", "km/h", "m") if metric else ("ft", "mph", "ft")
    density_unit = "interchanges/km" if metric else "interchanges/mi"
    with input_column:
        # This is deliberately a container rather than a form: the reference image
        # must refresh as a user changes the coded configuration.
        with st.container():
            render_section_label(_weaving_text("configuration_geometry"))
            geometry = st.columns(2)
            configuration = geometry[0].selectbox(_weaving_text("configuration"), ["one_sided", "two_sided"], index=["one_sided", "two_sided"].index(ui["configuration"]), format_func=lambda value: _weaving_text(f"config.{value}"))
            case_name = geometry[1].text_input(_weaving_text("case_name"), value=ui["case_name"], key=f"manual_weaving_input_name_{preset_id}_{unit_system}")
            segment_length = geometry[0].number_input(_weaving_text("segment_length", unit=length_unit), min_value=0.1, value=float(ui["segment_length"]), key=f"manual_weaving_input_length_{preset_id}_{unit_system}")
            number_of_lanes = geometry[1].selectbox(_weaving_text("total_lanes"), [3, 4], index=[3, 4].index(ui["number_of_lanes"]))
            nwl_options = [2, 3] if configuration == "one_sided" else [0]
            number_of_weaving_lanes = geometry[0].selectbox(_weaving_text("weaving_lanes"), nwl_options, index=nwl_options.index(ui["number_of_weaving_lanes"]) if ui["number_of_weaving_lanes"] in nwl_options else 0)
            entry_side = geometry[1].selectbox(_weaving_text("entry_side"), ["right", "left"], index=["right", "left"].index(ui["entry_side"]), format_func=lambda value: _weaving_text(f"side.{value}"))
            exit_options = [entry_side] if configuration == "one_sided" else [side for side in ("right", "left") if side != entry_side]
            exit_side = geometry[0].selectbox(_weaving_text("exit_side"), exit_options, index=0, format_func=lambda value: _weaving_text(f"side.{value}"))
            st.caption(_weaving_text("movement_caption"))
            if configuration == "one_sided":
                lc_rf = geometry[1].selectbox("LC_RF", [0, 1, 2], index=[0, 1, 2].index(ui["lc_rf"] if ui["lc_rf"] is not None else 0))
                lc_fr = geometry[0].selectbox("LC_FR", [0, 1, 2], index=[0, 1, 2].index(ui["lc_fr"] if ui["lc_fr"] is not None else 0))
                lc_rr = None
                geometry[1].caption(_weaving_text("lc_rr_inactive"))
            else:
                lc_rf = lc_fr = None
                lc_rr = geometry[1].selectbox("LC_RR", [2, 3, 4], index=[2, 3, 4].index(ui["lc_rr"] if ui["lc_rr"] in {2, 3, 4} else 2))
            _render_weaving_configuration_reference(
                configuration=configuration,
                number_of_lanes=number_of_lanes,
                number_of_weaving_lanes=number_of_weaving_lanes,
                entry_side=entry_side,
                exit_side=exit_side,
                lc_rf=lc_rf,
                lc_fr=lc_fr,
                lc_rr=lc_rr,
            )
            render_section_label(_weaving_text("traffic_demand"))
            traffic = st.columns(2)
            volume_ff = traffic[0].number_input("FF (veh/h)", min_value=0.0, value=float(ui["volume_ff_veh_h"]))
            volume_fr = traffic[1].number_input("FR (veh/h)", min_value=0.0, value=float(ui["volume_fr_veh_h"]))
            volume_rf = traffic[0].number_input("RF (veh/h)", min_value=0.0, value=float(ui["volume_rf_veh_h"]))
            volume_rr = traffic[1].number_input("RR (veh/h)", min_value=0.0, value=float(ui["volume_rr_veh_h"]))
            peak_hour_factor = traffic[0].number_input("Peak-hour factor (PHF)", min_value=0.01, max_value=1.0, value=float(ui["peak_hour_factor"]))
            interchange_density = traffic[1].number_input(_weaving_text("interchange_density", unit=density_unit), min_value=0.0, value=float(ui["interchange_density"]))
            render_section_label(_weaving_text("ffs_heavy"))
            ffs = st.columns(2)
            ffs_source = ffs[0].selectbox(_weaving_text("ffs_source"), ["measured", "estimated"], index=0 if ui["ffs_source"] == "measured" else 1, format_func=lambda value: _weaving_text(f"ffs.{value}"))
            if ffs_source == "measured":
                free_flow_speed = ffs[1].number_input(_weaving_text("measured_ffs", unit=speed_unit), min_value=1.0, value=float(ui["free_flow_speed"] or 60.0))
                base_free_flow_speed = lane_width = right_side_lateral_clearance = total_ramp_density = None
            else:
                free_flow_speed = None
                base_free_flow_speed = ffs[1].number_input(_weaving_text("base_ffs", unit=speed_unit), min_value=1.0, value=float(ui["base_free_flow_speed"] or 60.0))
                lane_width = ffs[0].number_input(_weaving_text("lane_width", unit=width_unit), min_value=0.1, value=float(ui["lane_width"] or 3.6))
                right_side_lateral_clearance = ffs[1].number_input(_weaving_text("right_lateral_clearance", unit=width_unit), min_value=0.0, value=float(ui["right_side_lateral_clearance"] or 1.8))
                total_ramp_density = ffs[0].number_input(_weaving_text("total_ramp_density", unit=density_unit.replace("interchanges", "ramps")), min_value=0.0, value=float(ui["total_ramp_density"] or 0.0))
            heavy_vehicle_percent = ffs[0].number_input(_weaving_text("heavy_vehicles"), min_value=0.0, max_value=100.0, value=float(ui["heavy_vehicle_percent"]))
            terrain_type = ffs[1].selectbox(_weaving_text("terrain"), ["level", "rolling"], index=["level", "rolling"].index(ui["terrain_type"]), format_func=lambda value: _weaving_text(f"terrain.{value}"))
            render_section_label(_weaving_text("advanced_geometry"))
            evidence = st.columns(2)
            option_fr = evidence[0].checkbox(_weaving_text("option_fr"), value=bool(ui["option_fr"]))
            option_rf = evidence[1].checkbox(_weaving_text("option_rf"), value=bool(ui["option_rf"]))
            option_rr = evidence[0].checkbox(_weaving_text("option_rr"), value=bool(ui["option_rr"]))
            reachable_ff = evidence[1].text_input(_weaving_text("reachable_ff"), value=ui["reachable_ff"])
            reachable_fr = evidence[0].text_input(_weaving_text("reachable_fr"), value=ui["reachable_fr"])
            reachable_rf = evidence[1].text_input(_weaving_text("reachable_rf"), value=ui["reachable_rf"])
            reachable_rr = evidence[0].text_input(_weaving_text("reachable_rr"), value=ui["reachable_rr"])
            nwl_basis = evidence[1].text_input(_weaving_text("nwl_basis"), value=ui["nwl_basis"])
            lane_change_basis = evidence[0].text_input(_weaving_text("lane_change_basis"), value=ui["lane_change_basis"])
            run_weaving = st.button(_weaving_text("run"), type="primary", width="stretch")
        displayed_inputs = {
            "case_name": case_name, "configuration": configuration, "segment_length": segment_length, "number_of_lanes": number_of_lanes, "number_of_weaving_lanes": number_of_weaving_lanes,
            "entry_side": entry_side, "exit_side": exit_side, "option_fr": option_fr, "option_rf": option_rf, "option_rr": option_rr,
            "reachable_ff": reachable_ff, "reachable_fr": reachable_fr, "reachable_rf": reachable_rf, "reachable_rr": reachable_rr,
            "nwl_basis": nwl_basis, "lane_change_basis": lane_change_basis, "lc_rf": lc_rf, "lc_fr": lc_fr, "lc_rr": lc_rr,
            "volume_ff_veh_h": volume_ff, "volume_fr_veh_h": volume_fr, "volume_rf_veh_h": volume_rf, "volume_rr_veh_h": volume_rr,
            "peak_hour_factor": peak_hour_factor, "interchange_density": interchange_density, "ffs_source": ffs_source,
            "free_flow_speed": free_flow_speed, "base_free_flow_speed": base_free_flow_speed, "lane_width": lane_width,
            "right_side_lateral_clearance": right_side_lateral_clearance, "total_ramp_density": total_ramp_density,
            "heavy_vehicle_percent": heavy_vehicle_percent, "terrain_type": terrain_type,
        }
        try:
            submitted_inputs = weaving_ui_inputs_to_engine(displayed_inputs, unit_system)
        except (HCMCalcError, ValueError) as exc:
            submitted_inputs = {"invalid": str(exc)}
        workflow_inputs = {"preset_id": preset_id, "normalized_engine_inputs": submitted_inputs}
        current = render_calculation_status("manual_weaving", workflow_inputs, status_placeholder)
        if run_weaving:
            st.session_state.pop("manual_weaving_error", None)
            st.session_state.pop("manual_weaving_result", None)
            try:
                engine_inputs = weaving_ui_inputs_to_engine(displayed_inputs, unit_system)
                result = run_manual_weaving(engine_inputs)
                st.session_state["manual_weaving_result"] = result_to_dict(result)
                st.session_state["manual_weaving_audit"] = build_manual_weaving_audit_record(preset_id, engine_inputs, unit_system=unit_system, displayed_inputs=displayed_inputs, result=result)
                mark_calculated(st.session_state, "manual_weaving", workflow_inputs)
                current = render_calculation_status("manual_weaving", workflow_inputs, status_placeholder)
            except (HCMCalcError, ValueError) as exc:
                st.session_state["manual_weaving_error"] = str(exc)
    with result_column:
        render_validation_basis_and_limitations(
            validation_basis=_weaving_text("validation_basis"),
            supported_scope=_weaving_text("supported_scope"),
            not_supported=_weaving_text("not_supported"),
        )
        error = st.session_state.get("manual_weaving_error")
        result_data = st.session_state.get("manual_weaving_result")
        audit = st.session_state.get("manual_weaving_audit")
        if error:
            st.error(error)
        elif not result_data:
            st.caption(PRERUN_RESULTS_PLACEHOLDER)
        elif not current:
            st.info(_weaving_text("stale_info"))
            with st.expander(AUDIT_EXPANDER_LABEL):
                st.json(audit)
        else:
            outputs = result_data["outputs"]
            display = weaving_display_outputs(outputs, unit_system)
            if outputs["support_status"] == "hcm_handoff_required":
                st.warning(_weaving_text("handoff_warning"))
                st.metric(_weaving_text("entered_lmax"), f"{outputs['input_summary']['segment_length_ft']:.0f} ft / {outputs['maximum_weaving_length_ft']:.0f} ft")
            else:
                los = outputs.get("level_of_service") or _weaving_text("not_assigned")
                st.metric(_weaving_text("los"), los)
                if outputs["capacity_status"] == "demand_exceeds_capacity":
                    st.warning(_weaving_text("above_capacity_warning"))
                st.metric(_weaving_text("mean_speed"), translate("status.not_predicted", _ui_locale()) if display["mean_speed"]["value"] is None else f"{display['mean_speed']['value']:.1f} {display['mean_speed']['unit']}")
                st.metric(_weaving_text("density"), translate("status.not_predicted", _ui_locale()) if display["density"]["value"] is None else f"{display['density']['value']:.1f} {display['density']['unit']}")
                st.metric(_weaving_text("governing_capacity"), f"{display['capacity']['value']:.0f} veh/h")
                st.metric(_weaving_text("vc"), _weaving_text("not_evaluated") if outputs.get("demand_capacity_ratio") is None else f"{outputs['demand_capacity_ratio']:.3f}")
            with st.expander(CALCULATION_DETAILS_LABEL):
                st.json(outputs)
            with st.expander(AUDIT_EXPANDER_LABEL):
                st.json(audit)
            render_export_report_section("manual_freeway_weaving_segment_v1", result_data, unit_system, inputs=displayed_inputs, audit_record=audit, template_id=preset_id)
        try:
            project_json = create_manual_weaving_project_json(preset_id, unit_system, displayed_inputs, result=result_data if current else None, audit_record=audit if current else None, locale=_ui_locale())
            st.download_button(_weaving_text("save_project"), project_json, file_name="hcm-7-0-weaving-project.json", mime="application/json", width="stretch")
        except ProjectFileError:
            st.caption(_weaving_text("project_save_unavailable"))


def _render_manual_weaving_load_controls() -> None:
    uploaded = st.file_uploader(_weaving_text("project_file"), type=["json"], key="manual_weaving_project_file_uploader")
    if uploaded is not None and st.button(_weaving_text("load_project"), key="manual_weaving_project_load"):
        try:
            st.session_state["manual_weaving_pending_project"] = load_manual_weaving_project_json(uploaded.getvalue())
            st.rerun()
        except ProjectFileError as exc:
            st.error(str(exc))


def _restore_manual_weaving_project(project: dict[str, Any]) -> None:
    _restore_project_locale(project)
    unit_system = project["unit_system"]
    displayed = project["displayed_ui_inputs"]
    st.session_state["manual_weaving_loaded_displayed"] = displayed
    st.session_state["manual_weaving_unit_label"] = unit_system.title()
    st.session_state["manual_weaving_preset_id"] = project.get("preset_id", "blank_custom")
    st.session_state["manual_weaving_preset_context"] = (project.get("preset_id", "blank_custom"), unit_system)
    if project.get("load_status") == "result_current":
        st.session_state["manual_weaving_result"] = project.get("calculation_result")
        st.session_state["manual_weaving_audit"] = project.get("audit")
        normalized = project["normalized_engine_inputs"]
        mark_calculated(st.session_state, "manual_weaving", {"preset_id": project.get("preset_id", "blank_custom"), "normalized_engine_inputs": normalized})
    st.session_state["manual_weaving_project_load_message"] = project_load_message(project, _ui_locale())


def render_manual_freeway_calculator() -> None:
    """Render the bounded Basic Freeway Segment worksheet."""

    pending_project = st.session_state.pop("manual_freeway_pending_project", None)
    if pending_project is not None:
        _restore_manual_freeway_project(pending_project)
    load_message = st.session_state.pop("manual_freeway_project_load_message", None)
    if load_message is not None:
        st.success(load_message)

    render_page_header(
        "Basic Freeway Segment Calculator",
        "Basic Freeway Segment calculator for one-direction, one-segment uninterrupted-flow analysis within the implemented Chapter 12 scope.",
    )
    status_placeholder = st.empty()

    input_column, result_column = render_calculator_shell()
    preset_options = freeway_preset_options()
    with input_column:
        render_project_load_section(_render_manual_freeway_load_controls)
        render_section_label("Setup")
        st.caption("Analysis type: Basic Freeway Segment.")
        unit_label = st.radio(
            "Unit system",
            ["Metric", "Imperial"],
            horizontal=True,
            key="manual_freeway_unit_label",
        )
        st.caption(
            "Calculations remain engine-native Imperial; Metric values are "
            "converted at the UI boundary."
        )
        with st.expander(STARTING_VALUES_LABEL, expanded=False):
            render_starting_values_section("Use example defaults")
            preset_id = st.selectbox(
                "Defaults",
                list(preset_options),
                format_func=lambda value: FREEWAY_DEFAULT_LABELS.get(
                    value, preset_options[value]
                ),
                key="freeway_preset_id",
                label_visibility="collapsed",
            )
            st.caption(
                "Example 1 remains available as optional defaults and regression evidence."
            )
    unit_system = unit_label.lower()
    preset_context = (preset_id, unit_system)
    if st.session_state.get("manual_freeway_preset_context") != preset_context:
        clear_manual_freeway_state(st.session_state)
        if "manual_freeway_preset_context" in st.session_state:
            st.session_state["manual_freeway_reset_message"] = (
                "Unit system or starting values changed. Inputs were reset to the "
                "selected starting values."
            )
        st.session_state["manual_freeway_preset_context"] = preset_context
    reset_message = st.session_state.pop("manual_freeway_reset_message", None)
    if reset_message is not None:
        st.caption(reset_message)
    try:
        preset = load_freeway_preset(preset_id)
    except (HCMCalcError, ValueError) as exc:
        st.error(str(exc))
        return

    inputs = preset["inputs"]
    ui_inputs = freeway_preset_ui_inputs(preset_id, unit_system)
    metric = unit_system == "metric"
    length_unit = "km" if metric else "mi"
    speed_unit = "km/h" if metric else "mph"
    width_unit = "m" if metric else "ft"
    ramp_density_unit = "ramps/km" if metric else "ramps/mi"
    with input_column:
        with st.form(f"freeway_form_{preset_id}"):
            render_section_label("Roadway / Geometry")
            roadway_columns = st.columns(2)
            number_of_lanes = roadway_columns[0].number_input(
                "Lanes in analysis direction",
                min_value=2,
                step=1,
                value=int(ui_inputs["number_of_lanes"]),
                key=f"manual_freeway_input_lanes_{preset_id}_{unit_system}",
            )
            segment_length = roadway_columns[1].number_input(
                f"Segment length ({length_unit})",
                min_value=0.001,
                value=float(ui_inputs["segment_length"]),
                key=f"manual_freeway_input_length_{preset_id}_{unit_system}",
            )
            ffs_source_label = roadway_columns[0].selectbox(
                "Free-flow speed source",
                ["Estimated from geometry", "Measured"],
                index=0 if ui_inputs["ffs_source"] == "estimated" else 1,
                key=f"manual_freeway_input_ffs_source_{preset_id}_{unit_system}",
            )
            ffs_source = (
                "estimated"
                if ffs_source_label == "Estimated from geometry"
                else "measured"
            )
            if ffs_source == "measured":
                free_flow_speed = roadway_columns[1].number_input(
                    f"Free-flow speed ({speed_unit})",
                    min_value=1.0,
                    value=float(
                        ui_inputs["free_flow_speed"] or min(
                            ui_inputs["base_free_flow_speed"],
                            75.0 * (MILES_TO_KILOMETERS if metric else 1.0),
                        )
                    ),
                    key=f"manual_freeway_input_free_flow_speed_{preset_id}_{unit_system}",
                )
                base_free_flow_speed = ui_inputs["base_free_flow_speed"]
                lane_width = ui_inputs["lane_width"]
                right_side_lateral_clearance = ui_inputs[
                    "right_side_lateral_clearance"
                ]
                total_ramp_density = ui_inputs["total_ramp_density"]
            else:
                free_flow_speed = ui_inputs["free_flow_speed"]
                base_free_flow_speed = roadway_columns[1].number_input(
                    f"Base free-flow speed ({speed_unit})",
                    min_value=1.0,
                    value=float(ui_inputs["base_free_flow_speed"]),
                    key=f"manual_freeway_input_base_ffs_{preset_id}_{unit_system}",
                )
                lane_width = roadway_columns[0].number_input(
                    f"Lane width ({width_unit})",
                    min_value=0.1,
                    value=float(ui_inputs["lane_width"]),
                    key=f"manual_freeway_input_lane_width_{preset_id}_{unit_system}",
                )
                right_side_lateral_clearance = roadway_columns[1].number_input(
                    f"Right-side lateral clearance ({width_unit})",
                    min_value=0.0,
                    value=float(ui_inputs["right_side_lateral_clearance"]),
                    key=f"manual_freeway_input_right_clearance_{preset_id}_{unit_system}",
                )
                total_ramp_density = roadway_columns[0].number_input(
                    f"{BASIC_FREEWAY_RAMP_DENSITY_LABEL} ({ramp_density_unit})",
                    min_value=0.0,
                    value=float(ui_inputs["total_ramp_density"]),
                    key=f"manual_freeway_input_ramp_density_{preset_id}_{unit_system}",
                    help=BASIC_FREEWAY_RAMP_DENSITY_HELP,
                )

            render_section_label("Traffic")
            traffic_columns = st.columns(2)
            demand_volume_veh_h = traffic_columns[0].number_input(
                "Demand volume (veh/h)",
                min_value=1.0,
                value=float(ui_inputs["demand_volume_veh_h"]),
                key=f"manual_freeway_input_demand_{preset_id}_{unit_system}",
            )
            peak_hour_factor = traffic_columns[1].number_input(
                "Peak hour factor",
                min_value=0.01,
                max_value=1.0,
                value=float(ui_inputs["peak_hour_factor"]),
                key=f"manual_freeway_input_phf_{preset_id}_{unit_system}",
            )
            heavy_vehicle_percent = traffic_columns[0].number_input(
                "Heavy vehicles (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(ui_inputs["heavy_vehicle_percent"]),
                key=f"manual_freeway_input_heavy_{preset_id}_{unit_system}",
            )
            pce_mode = traffic_columns[1].selectbox(
                "Heavy-vehicle PCE source",
                ["internal", "external"],
                index=0 if ui_inputs.get("pce_mode", "internal") == "internal" else 1,
                format_func=lambda value: "Internal HCM lookup" if value == "internal" else "External PCE override",
                key=f"manual_freeway_input_pce_mode_{preset_id}_{unit_system}",
                help="External override bypasses the internal PCE lookup; it does not bypass the heavy-vehicle adjustment.",
            )
            if pce_mode == "internal":
                terrain_type = traffic_columns[0].selectbox(
                    "Terrain / grade path",
                    ["level", "rolling", "specific_grade"],
                    index=["level", "rolling", "specific_grade"].index(ui_inputs["terrain_type"]),
                    key=f"manual_freeway_input_terrain_{preset_id}_{unit_system}",
                    help="Mountainous and mixed-flow domains are not supported.",
                )
                if terrain_type == "specific_grade":
                    grade_percent = traffic_columns[1].number_input(
                        "Grade (%)", value=float(ui_inputs.get("grade_percent") or 0.0),
                        key=f"manual_freeway_input_grade_{preset_id}_{unit_system}",
                    )
                    truck_mix = traffic_columns[0].selectbox(
                        "Truck mix (SUT/TT)",
                        ["default_30_sut_70_tt", "equal_50_sut_50_tt", "majority_70_sut_30_tt"],
                        index=["default_30_sut_70_tt", "equal_50_sut_50_tt", "majority_70_sut_30_tt"].index(ui_inputs.get("truck_mix", "default_30_sut_70_tt")),
                        key=f"manual_freeway_input_truck_mix_{preset_id}_{unit_system}",
                    )
                else:
                    grade_percent = None
                    truck_mix = "default_30_sut_70_tt"
            else:
                terrain_type = "level"
                grade_percent = None
                truck_mix = "default_30_sut_70_tt"
                passenger_car_equivalent = traffic_columns[0].number_input(
                    "External passenger-car equivalent", min_value=0.01,
                    value=float(ui_inputs.get("passenger_car_equivalent") or 1.0),
                    key=f"manual_freeway_input_external_pce_{preset_id}_{unit_system}",
                )
                passenger_car_equivalent_provenance = traffic_columns[1].text_input(
                    "External PCE provenance", value=ui_inputs.get("passenger_car_equivalent_provenance") or "",
                    key=f"manual_freeway_input_external_pce_provenance_{preset_id}_{unit_system}",
                    help="Identify the approved external source; this bypasses internal lookup only.",
                )
            if pce_mode == "internal":
                passenger_car_equivalent = None
                passenger_car_equivalent_provenance = None

            render_section_label("Advanced / Optional")
            advanced_columns = st.columns(2)
            driver_population_category = advanced_columns[0].selectbox(
                "Driver population category",
                ["regular", "mostly_familiar", "balanced", "mostly_unfamiliar", "overwhelmingly_unfamiliar"],
                index=["regular", "mostly_familiar", "balanced", "mostly_unfamiliar", "overwhelmingly_unfamiliar"].index(ui_inputs.get("driver_population_category", "regular")),
                key=f"manual_freeway_input_driver_population_{preset_id}_{unit_system}",
                help="Non-regular categories use the paired Chapter 26 SAF and CAF values required by the engine.",
            )
            if driver_population_category == "regular":
                speed_adjustment_factor = advanced_columns[0].number_input(
                    "Speed adjustment factor (SAF)", min_value=0.01, max_value=1.0,
                    value=float(ui_inputs["speed_adjustment_factor"]),
                    key=f"manual_freeway_input_saf_{preset_id}_{unit_system}",
                    help="A calibrated or user-governed factor; it is applied once to FFS.",
                )
                capacity_adjustment_factor = advanced_columns[1].number_input(
                    "Capacity adjustment factor (CAF)", min_value=0.01, max_value=1.0,
                    value=float(ui_inputs["capacity_adjustment_factor"]),
                    key=f"manual_freeway_input_caf_{preset_id}_{unit_system}",
                    help="A calibrated or user-governed factor; it is applied once to capacity.",
                )
                speed_adjustment_factor_source = advanced_columns[0].selectbox(
                    "SAF provenance", ["hcm_base_conditions", "project_local_calibration"],
                    index=0 if ui_inputs.get("speed_adjustment_factor_source", "hcm_base_conditions") == "hcm_base_conditions" else 1,
                    key=f"manual_freeway_input_saf_source_{preset_id}_{unit_system}",
                )
                capacity_adjustment_factor_source = advanced_columns[1].selectbox(
                    "CAF provenance", ["hcm_base_conditions", "project_local_calibration"],
                    index=0 if ui_inputs.get("capacity_adjustment_factor_source", "hcm_base_conditions") == "hcm_base_conditions" else 1,
                    key=f"manual_freeway_input_caf_source_{preset_id}_{unit_system}",
                )
            else:
                speed_adjustment_factor = ui_inputs["speed_adjustment_factor"]
                capacity_adjustment_factor = ui_inputs["capacity_adjustment_factor"]
                speed_adjustment_factor_source = "chapter_26_driver_population"
                capacity_adjustment_factor_source = "chapter_26_driver_population"
                advanced_columns[1].caption("SAF and CAF use the paired Chapter 26 values for the selected driver-population category.")
            run_freeway = st.form_submit_button(
                "Run calculation", type="primary", width="stretch"
            )

        displayed_inputs = {
            "number_of_lanes": int(number_of_lanes),
            "segment_length": segment_length,
            "ffs_source": ffs_source,
            "free_flow_speed": free_flow_speed,
            "base_free_flow_speed": base_free_flow_speed,
            "lane_width": lane_width,
            "right_side_lateral_clearance": right_side_lateral_clearance,
            "total_ramp_density": total_ramp_density,
            "demand_volume_veh_h": demand_volume_veh_h,
            "peak_hour_factor": peak_hour_factor,
            "heavy_vehicle_percent": heavy_vehicle_percent,
            "terrain_type": terrain_type,
            "grade_percent": grade_percent,
            "truck_mix": truck_mix,
            "pce_mode": pce_mode,
            "passenger_car_equivalent": passenger_car_equivalent,
            "passenger_car_equivalent_provenance": passenger_car_equivalent_provenance,
            "speed_adjustment_factor": speed_adjustment_factor,
            "capacity_adjustment_factor": capacity_adjustment_factor,
            "speed_adjustment_factor_source": speed_adjustment_factor_source,
            "capacity_adjustment_factor_source": capacity_adjustment_factor_source,
            "driver_population_category": driver_population_category,
        }
        submitted_inputs = freeway_ui_inputs_to_engine(
            displayed_inputs, inputs, unit_system
        )
        freeway_workflow_inputs = {
            "preset_id": preset_id,
            "unit_system": unit_system,
            "normalized_engine_inputs": submitted_inputs,
        }
        freeway_is_current = render_calculation_status(
            "manual_freeway", freeway_workflow_inputs, status_placeholder
        )
        def render_freeway_project_download() -> None:
            stored_audit = st.session_state.get("manual_freeway_audit")
            calculation_matches_inputs = (
                freeway_is_current
                and
                isinstance(stored_audit, dict)
                and stored_audit.get("displayed_inputs") == displayed_inputs
                and stored_audit.get("submitted_inputs") == submitted_inputs
                and stored_audit.get("unit_system") == unit_system
                and stored_audit.get("preset_id") == preset_id
            )
            try:
                project_json = create_manual_freeway_project_json(
                    preset_id,
                    unit_system,
                    displayed_inputs,
                    result=st.session_state.get("manual_freeway_result")
                    if calculation_matches_inputs
                    else None,
                    audit_record=stored_audit if calculation_matches_inputs else None,
                    locale=_ui_locale(),
                )
            except ProjectFileError:
                st.caption("Project save is unavailable until the displayed inputs are valid.")
                return
            st.download_button(
                "Save project",
                data=project_json,
                file_name=f"{preset_id}-manual-basic-freeway-project.json",
                mime="application/json",
                width="stretch",
            )

    if run_freeway:
        st.session_state.pop("manual_freeway_result", None)
        st.session_state.pop("manual_freeway_error", None)
        try:
            result = run_manual_freeway(submitted_inputs)
            st.session_state["manual_freeway_result"] = result_to_dict(result)
            st.session_state["manual_freeway_audit"] = (
                build_manual_freeway_audit_record(
                    preset_id,
                    submitted_inputs,
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    result=result,
                )
            )
            mark_calculated(
                st.session_state, "manual_freeway", freeway_workflow_inputs
            )
            freeway_is_current = render_calculation_status(
                "manual_freeway", freeway_workflow_inputs, status_placeholder
            )
        except HCMCalcError as exc:
            st.session_state["manual_freeway_error"] = str(exc)
            st.session_state["manual_freeway_audit"] = (
                build_manual_freeway_audit_record(
                    preset_id,
                    submitted_inputs,
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    error=exc,
                )
            )

    with result_column:
        render_validation_basis_and_limitations(
            validation_basis=(
                "Implemented Chapter 12 Basic Freeway Segment scope; BF-CH26-001 optional defaults and regression evidence."
            ),
            supported_scope=(
                "One direction, one uninterrupted-flow Basic Freeway Segment, "
                "general-purpose lanes only. Metric values are converted at the "
                "UI boundary; calculations remain engine-native Imperial."
            ),
            not_supported=(
                "General freeway facility support, ramp analysis, merge/diverge, "
                "weaving, managed lanes, work zones, reliability, and "
                "facility/corridor workflows. Unsupported combinations remain "
                "guarded by engine validation."
            ),
        )
        st.markdown("**Results**")
        error = st.session_state.get("manual_freeway_error")
        audit = st.session_state.get("manual_freeway_audit")
        if error is not None:
            st.error(f"Unsupported Basic Freeway case: {error}")
            with st.expander(AUDIT_EXPANDER_LABEL, expanded=False):
                st.json(audit)
            render_project_output_section(
                "Project JSON restores displayed inputs and engine-native values for this bounded Basic Freeway Segment workflow.",
                render_freeway_project_download,
            )
            return
        result_data = st.session_state.get("manual_freeway_result")
        if result_data is None:
            st.caption(PRERUN_RESULTS_PLACEHOLDER)
            render_project_output_section(
                "Project JSON restores displayed inputs and engine-native values for this bounded Basic Freeway Segment workflow.",
                render_freeway_project_download,
            )
            return

        outputs = result_data["outputs"]
        result_unit_system = (
            str(audit.get("unit_system", unit_system))
            if isinstance(audit, dict)
            else unit_system
        )
        display = freeway_display_outputs(outputs, result_unit_system)
        def predicted(metric: dict[str, Any], precision: str = ".1f") -> str:
            value = metric["value"]
            return (
                f"{value:{precision}} {metric['unit']}"
                if value is not None
                else "Not predicted"
            )
        render_result_summary_panel(
            primary_label="Level of service",
            primary_value=str(outputs["level_of_service"]),
            primary_kind="los",
            hero_supporting_label="Density",
            hero_supporting_value=predicted(display["density"]),
            secondary_metrics=[
                {
                    "label": "Speed used for density",
                    "value": predicted(display["speed_used_for_density"]),
                },
                {
                    "label": "Demand flow rate",
                    "value": (
                        f"{display['demand_flow_rate']['value']:.0f} "
                        f"{display['demand_flow_rate']['unit']}"
                    ),
                },
                {
                    "label": "Capacity",
                    "value": (
                        f"{display['capacity']['value']:.0f} "
                        f"{display['capacity']['unit']}"
                    ),
                },
                {
                    "label": "Capacity check",
                    "value": outputs["capacity_check"].replace("_", " "),
                },
                {
                    "label": "Adjusted free-flow speed",
                    "value": (
                        f"{display['adjusted_free_flow_speed']['value']:.1f} "
                        f"{display['adjusted_free_flow_speed']['unit']}"
                    ),
                },
                {
                    "label": "Base free-flow speed",
                    "value": (
                        f"{display['base_free_flow_speed']['value']:.1f} "
                        f"{display['base_free_flow_speed']['unit']}"
                    ),
                },
                {
                    "label": "Heavy vehicle adjustment factor",
                    "value": f"{outputs['heavy_vehicle_adjustment_factor']:.3f}",
                },
            ],
        )

        with st.expander(CALCULATION_DETAILS_LABEL, expanded=False):
            st.markdown("**FFS and SAF audit**")
            st.json({key: outputs[key] for key in (
                "ffs_source", "base_free_flow_speed_mph", "lane_width_adjustment_mph",
                "right_lateral_clearance_adjustment_mph", "total_ramp_density_adjustment_mph",
                "free_flow_speed_before_saf_mph", "speed_adjustment_factor",
                "speed_adjustment_factor_source", "adjusted_free_flow_speed_mph",
            )})
            st.markdown("**PCE, CAF, and driver-population audit**")
            st.json({key: outputs[key] for key in (
                "passenger_car_equivalent", "pce_source", "pce_lookup_path",
                "terrain_grade_classification", "effective_grade_percent", "segment_length_mi",
                "heavy_vehicle_adjustment_factor", "driver_population_category",
                "driver_population_factor", "capacity_pc_h_ln", "capacity_adjustment_factor",
                "capacity_adjustment_factor_source", "adjusted_capacity_pc_h_ln",
            )})
            render_list("Assumptions", result_data["assumptions"], "No assumptions reported.")
            render_list("Warnings", result_data["warnings"], "No warnings reported.")
            render_list(
                "Unsupported scope notes",
                outputs["unsupported_scope_notes"],
                "No unsupported scope notes reported.",
            )
        with st.expander(AUDIT_EXPANDER_LABEL, expanded=False):
            st.json(audit)
            st.dataframe(
                [
                    {**value, "value": str(value["value"])}
                    for value in result_data["intermediate_values"]
                ],
                hide_index=True,
                width="stretch",
            )
        with st.expander("Full JSON"):
            st.json(
                {
                    "calculation_type": "manual_basic_freeway_segment_v1",
                    "unit_system": result_unit_system,
                    "display_outputs": display,
                    "engine_result": result_data,
                    "audit_record": audit,
                }
            )
        render_project_output_section(
            "Project JSON restores displayed inputs and engine-native values for this bounded Basic Freeway Segment workflow.",
            render_freeway_project_download,
        )
        if freeway_is_current:
            render_export_report_section(
                "manual_basic_freeway_v0", result_data, result_unit_system,
                inputs=(audit.get("displayed_inputs", displayed_inputs) if isinstance(audit, dict) else displayed_inputs),
                audit_record=audit, template_id=preset_id,
            )
        else:
            st.caption("Export unavailable until recalculation completes.")


def _render_manual_freeway_load_controls() -> None:
    """Render bounded Manual Basic Freeway project loading controls."""

    uploaded_project = st.file_uploader(
        "Project JSON file",
        type=["json"],
        key="manual_freeway_project_file_uploader",
    )
    if st.button(
        "Load saved project",
        disabled=uploaded_project is None,
        width="stretch",
    ):
        try:
            project = load_manual_freeway_project_json(uploaded_project.getvalue())
        except ProjectFileError as exc:
            st.error(str(exc))
        else:
            st.session_state["manual_freeway_pending_project"] = project
            st.rerun()


def _restore_manual_freeway_project(project: dict[str, Any]) -> None:
    """Restore validated Manual Basic Freeway project data into worksheet state."""

    preset_id = project["preset_id"]
    unit_system = project["unit_system"]
    displayed = project["displayed_ui_inputs"]
    st.session_state["manual_freeway_unit_label"] = unit_system.title()
    st.session_state["freeway_preset_id"] = preset_id
    st.session_state["manual_freeway_preset_context"] = (preset_id, unit_system)
    ffs_source_label = (
        "Estimated from geometry"
        if displayed["ffs_source"] == "estimated"
        else "Measured"
    )
    widget_fields = {
        "lanes": "number_of_lanes",
        "length": "segment_length",
        "base_ffs": "base_free_flow_speed",
        "lane_width": "lane_width",
        "right_clearance": "right_side_lateral_clearance",
        "ramp_density": "total_ramp_density",
        "demand": "demand_volume_veh_h",
        "phf": "peak_hour_factor",
        "heavy": "heavy_vehicle_percent",
        "terrain": "terrain_type",
        "grade": "grade_percent",
        "truck_mix": "truck_mix",
        "pce_mode": "pce_mode",
        "external_pce": "passenger_car_equivalent",
        "external_pce_provenance": "passenger_car_equivalent_provenance",
        "driver_population": "driver_population_category",
        "saf": "speed_adjustment_factor",
        "caf": "capacity_adjustment_factor",
        "saf_source": "speed_adjustment_factor_source",
        "caf_source": "capacity_adjustment_factor_source",
    }
    for widget_name, input_name in widget_fields.items():
        if displayed.get(input_name) is not None:
            st.session_state[
                f"manual_freeway_input_{widget_name}_{preset_id}_{unit_system}"
            ] = displayed[input_name]
    st.session_state[
        f"manual_freeway_input_ffs_source_{preset_id}_{unit_system}"
    ] = ffs_source_label
    if displayed.get("free_flow_speed") is not None:
        st.session_state[
            f"manual_freeway_input_free_flow_speed_{preset_id}_{unit_system}"
        ] = displayed["free_flow_speed"]
    for state_key, project_key in (
        ("manual_freeway_result", "calculation_result"),
        ("manual_freeway_audit", "audit"),
    ):
        if project.get(project_key) is None:
            st.session_state.pop(state_key, None)
        else:
            st.session_state[state_key] = project[project_key]
    if project.get("calculation_result") is not None:
        mark_calculated(
            st.session_state,
            "manual_freeway",
            {
                "preset_id": preset_id,
                "unit_system": unit_system,
                "normalized_engine_inputs": project["normalized_engine_inputs"],
            },
        )
    st.session_state.pop("manual_freeway_error", None)
    _restore_project_locale(project)
    st.session_state["manual_freeway_project_load_message"] = project_load_message(project, _ui_locale())


def _render_manual_multilane_load_controls() -> None:
    """Render guarded Manual Multilane project loading controls."""

    uploaded_project = st.file_uploader(
        "Project JSON file",
        type=["json"],
        key="manual_multilane_project_file_uploader",
    )
    if st.button(
        "Load saved project",
        disabled=uploaded_project is None,
        width="stretch",
    ):
        try:
            project = load_manual_multilane_project_json(uploaded_project.getvalue())
        except ProjectFileError as exc:
            st.error(str(exc))
        else:
            st.session_state["manual_multilane_pending_project"] = project
            st.rerun()


def _restore_manual_multilane_project(project: dict[str, Any]) -> None:
    """Restore validated Manual Multilane project data into worksheet state."""

    template_id = project["template_id"]
    unit_system = project["unit_system"]
    displayed = project["displayed_ui_inputs"]
    st.session_state["manual_multilane_unit_label"] = unit_system.title()
    st.session_state["multilane_template_id"] = template_id
    st.session_state["manual_multilane_template_context"] = (template_id, unit_system)
    st.session_state[
        f"manual_multilane_input_ffs_source_{template_id}_{unit_system}"
    ] = displayed.get("ffs_source", "estimated").title()
    st.session_state[
        f"manual_multilane_input_pce_mode_{template_id}_{unit_system}"
    ] = "External override" if displayed.get("pce_mode") == "external" else "Internal HCM lookup"
    widget_fields = {
        "lanes": "number_of_lanes",
        "length": "segment_length",
        "demand": "demand_volume_veh_h",
        "phf": "peak_hour_factor",
        "heavy": "heavy_vehicle_percent",
        "grade": "grade_percent",
    }
    for widget_name, input_name in widget_fields.items():
        if input_name in displayed:
            st.session_state[
                f"manual_multilane_input_{widget_name}_{template_id}_{unit_system}"
            ] = displayed[input_name]
    for widget_name, input_name in {
        "speed": "posted_speed_limit", "lane_width": "lane_width",
        "clearance": "roadside_lateral_clearance", "access": "access_point_density",
        "median": "median_type", "left_clearance": "left_side_lateral_clearance",
        "measured_ffs": "free_flow_speed", "pce": "passenger_car_equivalent",
        "terrain": "terrain_type", "truck_mix": "truck_mix",
    }.items():
        if input_name in displayed:
            st.session_state[
                f"manual_multilane_input_{widget_name}_{template_id}_{unit_system}"
            ] = displayed[input_name]
    for state_key, project_key in (
        ("manual_multilane_result", "calculation_result"),
        ("manual_multilane_audit", "audit"),
    ):
        if project.get(project_key) is None:
            st.session_state.pop(state_key, None)
        else:
            st.session_state[state_key] = project[project_key]
    if project.get("calculation_result") is not None:
        mark_calculated(
            st.session_state,
            "manual_multilane",
            {
                "template_id": template_id,
                "unit_system": unit_system,
                "displayed_inputs": displayed,
                "submitted_inputs": project["normalized_engine_inputs"],
            },
        )
    st.session_state.pop("manual_multilane_error", None)
    _restore_project_locale(project)
    st.session_state["manual_multilane_project_load_message"] = project_load_message(project, _ui_locale())


def render_manual_facility_calculator() -> None:
    """Render the general ordered two-lane facility worksheet."""

    pending_project = st.session_state.pop("manual_facility_pending_project", None)
    if pending_project is not None:
        _restore_manual_facility_project(pending_project)
    load_message = st.session_state.pop("manual_facility_project_load_message", None)
    if load_message is not None:
        st.success(load_message)

    render_page_header(
        "Two-Lane Facility Calculator",
        "Two-Lane Highway Facility worksheet.",
    )
    status_placeholder = st.empty()
    input_column, result_column = render_calculator_shell()
    template_options = facility_template_options()
    with input_column:
        render_project_load_section(_render_manual_facility_load_controls)
        render_section_label("Setup")
        st.caption("Analysis type: Two-Lane Highway Facility.")
        unit_label = st.radio(
            "Unit system",
            ["Metric", "Imperial"],
            horizontal=True,
            key="facility_unit_label",
        )
        with st.expander(STARTING_VALUES_LABEL, expanded=False):
            render_starting_values_section("Use example defaults")
            template_id = st.selectbox(
                "Defaults",
                list(template_options),
                format_func=lambda value: FACILITY_DEFAULT_LABELS.get(
                    value, template_options[value]
                ),
                key="facility_template_id",
                help="Load example defaults for the editable facility worksheet.",
                label_visibility="collapsed",
            )
            st.caption(
                "HCM Chapter 26 Example 3 and 4 references back these defaults."
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

        st.caption(
            "Defaults: "
            f"{FACILITY_DEFAULT_LABELS.get(template_id, template['template_label'])}."
        )
        st.caption("Examples are starting values only. Every calculation-relevant field below is editable and stored in the facility input.")
        render_section_label("Roadway / Geometry")
        editor_version = st.session_state.get("manual_facility_editor_version", 0)
        editor_seed = st.session_state.pop(
            "manual_facility_segment_rows_seed", template["segments"]
        )
        edited_rows = st.data_editor(
            editor_seed,
            key=f"facility_segment_editor_{template_id}_{unit_system}_{editor_version}",
            hide_index=True,
            num_rows="dynamic",
            width="stretch",
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
                "passing_lane_role": st.column_config.SelectboxColumn("Passing Lane role", options=["none", "passing_lane", "downstream_affected"], required=True),
                "segment_name": st.column_config.TextColumn("Segment name"),
                "segment_type": st.column_config.SelectboxColumn("Segment type", options=["passing_constrained", "passing_zone", "passing_lane"], required=True),
                "terrain_type": st.column_config.TextColumn("Terrain"),
                "grade_percent": st.column_config.NumberColumn("Grade (%)"),
                "horizontal_alignment": st.column_config.SelectboxColumn("Alignment", options=["straight", "horizontal_curves"], required=True),
                "lane_width": st.column_config.NumberColumn("Lane width", min_value=9.0, max_value=12.0, required=True),
                "shoulder_width": st.column_config.NumberColumn("Shoulder width", min_value=0.0, max_value=6.0, required=True),
                "access_point_density": st.column_config.NumberColumn("Access density", min_value=0.0, required=True),
            },
        )
        render_section_label("Traffic")
        st.caption("Traffic values are edited in the facility segment table.")
        render_section_label("Advanced / Optional")
        st.caption("Use the row controls to add or remove segments. Row order is the engineered facility order; Passing Lane context is explicit.")
        calculate_column, scope_column = st.columns([1, 2])
        calculate = calculate_column.button(
            "Run calculation",
            type="primary",
            width="stretch",
            key="facility_calculate",
        )
        scope_column.caption(
            "Run the worksheet with the current segment table values."
        )
        facility_workflow_inputs = {
            "template_id": template_id,
            "unit_system": unit_system,
            "segment_rows": edited_rows,
        }
        facility_is_current = render_calculation_status(
            "manual_facility", facility_workflow_inputs, status_placeholder
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
            mark_calculated(
                st.session_state, "manual_facility", facility_workflow_inputs
            )
            facility_is_current = render_calculation_status(
                "manual_facility", facility_workflow_inputs, status_placeholder
            )
        except HCMCalcError as exc:
            st.session_state["manual_facility_error"] = str(exc)
            st.session_state["manual_facility_audit"] = (
                build_manual_facility_audit_record(
                    template_id, edited_rows, unit_system, error=exc
                )
            )

    with result_column:
        render_validation_basis_and_limitations(
            validation_basis=(
                f"HCM Chapter 26 Two-Lane Highway {template['template_basis']}."
            ),
            supported_scope=(
                "Ordered Passing Constrained, Passing Zone, and Passing Lane "
                "segments within the documented Chapter 15 input domains."
            ),
            not_supported=(
                "Reliability, automatic segmentation, Passing Lane warrant/design, "
                "pedestrian/bicycle LOS, overlapping Passing Lane interactions, and "
                "unsupported geometry or physical domains."
            ),
        )
        st.markdown("**Results**")
        render_manual_facility_result_panel(
            template_id, unit_system, edited_rows, template, facility_is_current
        )


def render_manual_facility_result_panel(
    template_id: str,
    unit_system: str,
    edited_rows: list[dict[str, Any]],
    template: dict[str, Any],
    is_current: bool,
) -> None:
    """Render facility results, project output, audit, and exports."""

    error = st.session_state.get("manual_facility_error")
    audit = st.session_state.get("manual_facility_audit")
    if error is not None:
        st.error(f"Unsupported combination: {error}")
        with st.expander(AUDIT_EXPANDER_LABEL, expanded=False):
            st.json(audit)
        _render_manual_facility_project_file_controls(
            template_id,
            unit_system,
            edited_rows,
            FACILITY_DEFAULT_LABELS.get(template_id, template["template_label"]),
        )
        return

    result_data = st.session_state.get("manual_facility_result")
    if result_data is None:
        st.caption(PRERUN_RESULTS_PLACEHOLDER)
        _render_manual_facility_project_file_controls(
            template_id,
            unit_system,
            edited_rows,
            FACILITY_DEFAULT_LABELS.get(template_id, template["template_label"]),
        )
        return
    outputs = result_data["outputs"]
    metric = unit_system == "metric"
    facility_follower_density = (
        f"{outputs['facility_follower_density_followers_mi_ln'] / 1.609344:.2f} fol/km/ln"
        if metric
        else f"{outputs['facility_follower_density_followers_mi_ln']:.1f} fol/mi/ln"
    )
    st.subheader("Facility summary")
    render_result_summary_panel(
        primary_label="Facility level of service",
        primary_value=str(outputs["facility_level_of_service"]),
        primary_kind="los",
        hero_supporting_label="Facility follower density",
        hero_supporting_value=facility_follower_density,
        secondary_metrics=[
            {
                "label": "Weighted average speed",
                "value": (
                    f"{outputs['facility_average_speed_mph'] * 1.609344:.1f} km/h"
                    if metric
                    else f"{outputs['facility_average_speed_mph']:.1f} mph"
                ),
            },
            {
                "label": "Total length",
                "value": (
                    f"{outputs['facility_length_mi'] * 1.609344:.2f} km"
                    if metric
                    else f"{outputs['facility_length_mi']:.2f} mi"
                ),
            },
            {
                "label": "Segments",
                "value": str(len(outputs["segments"])),
            },
        ],
    )

    st.subheader("Segment-level results")
    st.dataframe(
        st.session_state["manual_facility_result_rows"],
        hide_index=True,
        width="stretch",
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
    with st.expander(CALCULATION_DETAILS_LABEL, expanded=False):
        render_list("Warnings", result_data["warnings"], "No warnings reported.")
        render_list("Assumptions", result_data["assumptions"], "No assumptions reported.")
        render_list(
            "Unsupported behavior notes",
            template["unsupported_behavior_notes"],
            "No unsupported behavior notes reported.",
        )
    with st.expander(AUDIT_EXPANDER_LABEL, expanded=False):
        st.json(audit)
    full_result = {
        "calculation_type": "manual_two_lane_facility_v1",
        "template_id": template_id,
        "unit_system": unit_system,
        "engine_result": result_data,
        "audit_record": audit,
    }
    with st.expander("Full JSON"):
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
            width="stretch",
        )
    if not is_current:
        st.caption("Export unavailable until recalculation completes.")
        return
    _render_manual_facility_project_file_controls(
        template_id,
        unit_system,
        edited_rows,
        FACILITY_DEFAULT_LABELS.get(template_id, template["template_label"]),
    )
    render_export_report_section(
        "manual_two_lane_facility_v1",
        result_data,
        unit_system,
        inputs=audit.get("facility_inputs", {}).get("segments", [])
        if isinstance(audit, dict)
        else [],
        audit_record=audit,
        template_id=template_id,
    )


def _render_manual_facility_project_file_controls(
    template_id: str,
    unit_system: str,
    segment_rows: list[dict[str, Any]],
    template_name: str,
) -> None:
    """Render guarded facility project save controls."""

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
        locale=_ui_locale(),
    )
    render_project_output_section(
        (
            f"Save {template_name}. Facility projects remain guarded "
            "to the selected validation basis."
        ),
        lambda: st.download_button(
            "Save project",
            data=project_json,
            file_name=f"{template_id}-manual-facility-project.json",
            mime="application/json",
            width="stretch",
        ),
    )


def _render_manual_facility_load_controls() -> None:
    """Render guarded facility project loading controls."""

    uploaded_project = st.file_uploader(
        "Project JSON file",
        type=["json"],
        key="manual_facility_project_file_uploader",
    )
    if st.button(
        "Load saved project",
        disabled=uploaded_project is None,
        width="stretch",
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
        mark_calculated(
            st.session_state,
            "manual_facility",
            {
                "template_id": template_id,
                "unit_system": unit_system,
                "segment_rows": project["segment_rows"],
            },
        )
    st.session_state.pop("manual_facility_error", None)
    _restore_project_locale(project)
    st.session_state["manual_facility_project_load_message"] = project_load_message(project, _ui_locale())


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

    render_page_header(
        "Two-Lane Highway Manual Segment Calculator",
        "Two-Lane Highway single-segment worksheet.",
    )
    status_placeholder = st.empty()
    worksheet_column, result_column = render_calculator_shell()

    with worksheet_column:
        render_project_load_section(_render_manual_project_load_controls)
        setup_column, schematic_column = st.columns([1.25, 1.0], gap="medium")
        with setup_column:
            render_section_label("Setup")
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
                    "When selected, curve subsegments can be reviewed and edited below."
                ),
                key="manual_horizontal_alignment_label",
            )
            horizontal_alignment = (
                "horizontal_curves"
                if horizontal_alignment_label == "Horizontal curve"
                else "straight"
            )

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
                render_section_label("Roadway / Geometry")
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

                render_section_label("Traffic")
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
                        "Single-segment result only - downstream/facility effects "
                        "are not included here."
                    )

            with form_advanced_column:
                horizontal_subsegments: list[dict[str, Any]] = []
                curve_setup: dict[str, Any] | None = None
                generate_curve = False
                render_section_label("Advanced / Optional")
                if horizontal_alignment == "horizontal_curves":
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
                            "Generate curve subsegments", width="stretch"
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
                            width="stretch",
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
                else:
                    st.caption(
                        "Horizontal curve setup is available when Horizontal alignment is selected."
                    )

            run_manual = st.form_submit_button(
                "Run calculation", type="primary", width="stretch"
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
        segment_is_current = render_calculation_status(
            "manual_segment", values, status_placeholder
        )
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

    if run_manual:
        st.session_state.pop("manual_segment_result", None)
        st.session_state.pop("manual_segment_error", None)
        try:
            result = run_manual_single_segment(values)
            st.session_state["manual_segment_result"] = result_to_dict(result)
            st.session_state["manual_segment_audit"] = (
                build_manual_calculation_audit_record(values, result=result)
            )
            mark_calculated(st.session_state, "manual_segment", values)
            segment_is_current = render_calculation_status(
                "manual_segment", values, status_placeholder
            )
        except HCMCalcError as exc:
            st.session_state["manual_segment_error"] = str(exc)
            st.session_state["manual_segment_audit"] = (
                build_manual_calculation_audit_record(values, error=exc)
            )

    with result_column:
        render_validation_basis_and_limitations(
            validation_basis=(
                "HCM7 Chapter 26 Two-Lane Highway example-backed checks for "
                "implemented Chapter 15 paths."
            ),
            supported_scope=(
                "Manual single-segment Two-Lane Highway calculations for the "
                "implemented guarded paths."
            ),
            not_supported=(
                "Full arbitrary Chapter 15 coverage, upstream passing-lane "
                "context, downstream facility effects in this single-segment "
                "worksheet, and unsupported horizontal-curve combinations."
            ),
        )
        st.markdown("**Results**")
        stored_result = st.session_state.get("manual_segment_result")
        audit_record = st.session_state.get("manual_segment_audit")
        stored_error = st.session_state.get("manual_segment_error")
        if stored_error is not None:
            st.error(stored_error)
            render_audit_record(audit_record)
            render_manual_project_file_controls(values)
            return
        if stored_result is None:
            st.caption(PRERUN_RESULTS_PLACEHOLDER)
            render_manual_project_file_controls(values)
            return
        render_manual_result(
            stored_result,
            str(audit_record.get("unit_system", unit_system))
            if isinstance(audit_record, dict)
            else unit_system,
            audit_record,
            is_current=segment_is_current,
        )
        result_unit_system = (
            str(audit_record.get("unit_system", unit_system))
            if isinstance(audit_record, dict)
            else unit_system
        )
        if segment_is_current:
            render_manual_project_file_controls(values)
            render_export_report_section(
                "manual_single_segment", stored_result, result_unit_system,
                inputs=audit_record.get("user_inputs", {}) if isinstance(audit_record, dict) else {},
                audit_record=audit_record,
            )
        else:
            st.caption("Export unavailable until recalculation completes.")


def render_manual_project_file_controls(manual_inputs: dict[str, Any]) -> None:
    """Render compact manual project save controls."""

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
        manual_inputs, result=result, audit_record=audit_record, locale=_ui_locale()
    )

    render_project_output_section(
        "Save project JSON to preserve inputs.",
        lambda: st.download_button(
            "Save project",
            data=project_json,
            file_name="manual-single-segment-project.json",
            mime="application/json",
            width="content",
        ),
    )


def _render_manual_project_load_controls() -> None:
    """Render compact manual project load controls."""

    uploaded_project = st.file_uploader(
        "Project JSON file",
        type=["json"],
        key="manual_project_file_uploader",
    )
    if st.button(
        "Load saved project",
        disabled=uploaded_project is None,
        width="stretch",
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
    if project.get("result") is not None:
        mark_calculated(st.session_state, "manual_segment", manual_inputs)
    st.session_state.pop("manual_segment_error", None)
    _restore_project_locale(project)
    st.session_state["manual_project_load_message"] = project_load_message(project, _ui_locale())


def render_audit_record(audit_record: dict[str, Any] | None) -> None:
    """Render a collapsed manual calculation audit record."""

    if audit_record is None:
        return
    with st.expander(AUDIT_EXPANDER_LABEL):
        st.caption(
            "Submitted values, engine-native imperial inputs, scope status, and "
            "calculation metadata."
        )
        st.json(audit_record)


def render_manual_result(
    result_data: dict[str, Any],
    unit_system: str,
    audit_record: dict[str, Any] | None = None,
    *,
    is_current: bool = True,
) -> None:
    """Render the manual result hierarchy with display-unit conversions."""

    outputs = result_data["outputs"]
    metrics = display_outputs(outputs, unit_system)
    level_of_service = str(outputs["level_of_service"])
    density = format_display_metric(
        "follower_density", metrics["follower_density"], unit_system
    )
    render_result_summary_panel(
        primary_label="Level of service",
        primary_value=level_of_service,
        primary_kind="los",
        hero_supporting_label="Follower density",
        hero_supporting_value=density,
        secondary_metrics=[
            {
                "label": metric["label"],
                "value": format_display_metric(name, metric, unit_system),
            }
            for name, metric in metrics.items()
            if name != "follower_density"
        ],
    )

    with st.expander(CALCULATION_DETAILS_LABEL, expanded=False):
        st.markdown("**Assumptions**")
        for assumption in result_data["assumptions"]:
            st.markdown(f"- {assumption}")
        st.markdown("**Warnings**")
        for warning in result_data["warnings"]:
            st.markdown(f"- {warning}")
    with st.expander(AUDIT_EXPANDER_LABEL, expanded=False):
        st.markdown("**Intermediate values**")
        st.dataframe(
            result_data["intermediate_values"],
            hide_index=True,
            width="stretch",
        )
        if audit_record is not None:
            st.markdown("**Audit record**")
            st.caption(
                "Submitted values, engine-native imperial inputs, scope status, and "
                "calculation metadata."
            )
            st.json(audit_record)

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
        if is_current:
            st.download_button(
                "Download JSON",
                data=full_result_json,
                file_name="manual-single-segment-result.json",
                mime="application/json",
                width="stretch",
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

    render_export_report_section_container(
        lambda: render_export_report_downloads(
            calculation_type,
            result_data,
            unit_system,
            inputs=inputs,
            audit_record=audit_record,
            template_id=template_id,
        )
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

    export_choice = st.selectbox(
        translate("export.language", _ui_locale()),
        ("same_ui", "en", "th"),
        format_func=lambda value: translate(f"export.{value.replace('same_ui', 'same_as_ui')}", _ui_locale()),
        key=f"{calculation_type}_export_locale",
    )
    export_locale = _ui_locale() if export_choice == "same_ui" else export_choice
    try:
        report = build_report(
            calculation_type,
            result_data,
            unit_system,
            inputs=inputs,
            audit_record=audit_record,
            template_id=template_id,
            locale=export_locale,
        )
        downloads = (
            (translate("export.download_csv", _ui_locale()), "csv", "csv", "text/csv"),
            (
                translate("export.download_excel", _ui_locale()),
                "xlsx",
                "xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            (translate("export.download_markdown", _ui_locale()), "markdown", "md", "text/markdown"),
            (translate("export.download_json", _ui_locale()), "json", "json", "application/json"),
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
        st.error(translate("export.unavailable", _ui_locale(), error=str(exc)))
        return

    st.caption(translate("export.guidance", _ui_locale()))
    columns = st.columns(2)
    for index, (label, data, filename, mime) in enumerate(rendered):
        columns[index % 2].download_button(
            label,
            data=data,
            file_name=filename,
            mime=mime,
            width="stretch",
            key=f"{calculation_type}_{filename}",
        )


def main() -> None:
    """Run the single-page Streamlit calculator."""

    st.set_page_config(page_title=translate("app.title"), layout="wide")
    apply_ui_styles()
    st.session_state.setdefault("ui_locale", "en")
    header_left, header_right = st.columns([1.4, 1.0], gap="large")
    with header_left:
        st.markdown(
            f"**{translate('app.title', _ui_locale())}** - Two-Lane Highway, Multilane Highway, Basic Freeway, and Weaving Segment"
        )
    with header_right:
        st.selectbox(
            translate("locale.label", _ui_locale()),
            SUPPORTED_LOCALES,
            # Keep these option labels stable while the widget itself changes
            # locale; a dynamic formatter would invalidate Streamlit's prior
            # widget state during an English ↔ Thai switch.
            format_func=lambda value: {"en": "English", "th": "ไทย"}[value],
            key="ui_locale",
        )
        mode_locale = _ui_locale()
        selected_mode = st.session_state.get("selected_calculator_mode", APP_MODE_LABELS[0])
        if selected_mode not in APP_MODE_LABELS:
            selected_mode = APP_MODE_LABELS[0]
        mode_label = st.radio(
            translate("nav.calculator_mode", mode_locale),
            APP_MODE_LABELS,
            index=APP_MODE_LABELS.index(selected_mode),
            format_func=lambda value, locale=mode_locale: translate(
                {
                    "Two-Lane Segment": "nav.two_lane_segment",
                    "Two-Lane Facility": "nav.two_lane_facility",
                    "Multilane Segment": "nav.multilane_segment",
                    "Basic Freeway Segment": "nav.basic_freeway_segment",
                    "Weaving Segment": "nav.weaving_segment",
                    "Supported Workflows": "nav.supported_workflows",
                }[value], locale
            ),
            horizontal=True,
            label_visibility="collapsed",
            key=f"calculator_mode_{mode_locale}",
        )
        st.session_state["selected_calculator_mode"] = mode_label
    st.caption(translate("app.scope_notice", _ui_locale()))
    mode = resolve_app_view(mode_label, st.query_params)
    if mode == "manual_single_segment":
        render_manual_single_segment_calculator()
    elif mode == "manual_facility":
        render_manual_facility_calculator()
    elif mode == "manual_multilane":
        render_manual_multilane_calculator()
    elif mode == "manual_basic_freeway":
        render_manual_freeway_calculator()
    elif mode == "manual_weaving":
        render_manual_weaving_calculator()
    elif mode == "supported_workflows":
        render_supported_workflows_page()
    else:
        render_validated_case_viewer()
    st.divider()
    st.caption(translate("app.limitations_footer", _ui_locale()))


if __name__ == "__main__":
    main()
