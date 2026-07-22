"""Single-page Streamlit viewer and manual single-segment calculator."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from hcmcalc.cli import find_case, result_to_dict, run_case
from hcmcalc.core import HCMCalcError, MethodNotImplementedError, UnsupportedScopeError
from hcmcalc.ui.audit import build_manual_calculation_audit_record
from hcmcalc.ui.curve_editor import (
    curve_setup_defaults,
    generate_curve_subsegments,
    initial_curve_subsegments,
)
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    canonicalize_manual_facility_rows,
    clear_manual_facility_result_state,
    facility_segment_result_rows,
    facility_template_options,
    load_facility_template,
    run_manual_facility,
    validate_manual_facility_table,
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
from hcmcalc.ui.manual_ramp_influence import (
    build_manual_ramp_audit_record,
    calculation_contract as ramp_calculation_contract,
    clear_manual_ramp_state,
    diagram_path as ramp_diagram_path,
    method_family as ramp_method_family,
    project_type as ramp_project_type,
    ramp_display_outputs,
    ramp_preset_options,
    ramp_preset_ui_inputs,
    ramp_ui_inputs_to_engine,
    run_manual_ramp,
)
from hcmcalc.ui.weaving_diagrams import get_weaving_diagram, get_weaving_diagram_subtype
from hcmcalc.ui.manual_segment import (
    build_manual_segment_inputs,
    run_manual_single_segment,
)
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
    create_manual_ramp_project_json,
    load_manual_weaving_project_json,
    load_manual_ramp_project_json,
    load_manual_project_json,
    project_load_message,
    project_presentation_locale,
)
from hcmcalc.ui.i18n import SUPPORTED_LOCALES, normalize_locale, translate
from hcmcalc.ui.result_view import (
    compact_rows,
    format_display_metric,
    render_result_state_panel,
    render_result_summary_panel,
)
from hcmcalc.ui.reporting import (
    ReportingError,
    build_report,
    export_report,
    report_filename,
)
from hcmcalc.ui.runtime_resources import load_packaged_yaml
from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.supported_workflows import (
    APP_MODE_LABELS,
    APP_MODE_TO_VIEW,
    NAVIGATION_GROUPS,
    NAVIGATION_GROUP_VIEWS,
    AUDIT_EXPANDER_LABEL,
    BASIC_FREEWAY_RAMP_DENSITY_HELP,
    BASIC_FREEWAY_RAMP_DENSITY_LABEL,
    CALCULATION_DETAILS_LABEL,
    EXPORT_REPORT_LABEL,
    PRERUN_RESULTS_PLACEHOLDER,
    STARTING_VALUES_LABEL,
    APP_VIEW_TO_MODE,
    APP_VIEW_TO_NAV_KEY,
    SUPPORTED_PAGE_CAPABILITIES,
    SUPPORTED_PAGE_LIMITATIONS,
    SUPPORTED_PAGE_WORKFLOW_GROUPS,
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
    ResultPresentationState,
    mark_calculated,
    resolve_result_presentation_state,
    workflow_status,
    localized_workflow_status,
)


FIXTURE_FILENAME = "example_inputs.yaml"
SEGMENT_TYPE_LABELS = {
    "passing_constrained": "Passing constrained",
    "passing_zone": "Passing zone",
    "passing_lane": "Passing lane",
}
FACILITY_DEFAULT_LABELS = {
    "level_example_3": "Level terrain facility defaults",
    "mountainous_example_4": "Mountainous facility defaults",
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


def _weaving_text_for_locale(locale: str, key: str, **params: Any) -> str:
    return translate(f"weaving.{key}", locale, **params)


def _weaving_preset_label(preset_id: str) -> str:
    normalized = preset_id.lower().replace("-", "_")
    return _weaving_text(f"preset.{normalized}")


def _multilane_text(key: str, **params: Any) -> str:
    return translate(f"multilane.{key}", _ui_locale(), **params)


def _freeway_text(key: str, **params: Any) -> str:
    return translate(f"freeway.{key}", _ui_locale(), **params)


def _two_lane_text(key: str, **params: Any) -> str:
    return translate(f"two_lane.{key}", _ui_locale(), **params)


def _facility_text(key: str, **params: Any) -> str:
    return translate(f"facility.{key}", _ui_locale(), **params)


def _localized_option_to_value(
    value: Any, key_prefix: str, options: tuple[str, ...]
) -> str:
    """Recover canonical widget values if Streamlit returns a formatted label."""

    text = str(value)
    if text in options:
        return text
    lowered = text.lower()
    if "metric" in lowered or "เมต" in text:
        return "metric" if "metric" in options else text
    if "imperial" in lowered or "อิม" in text:
        return "imperial" if "imperial" in options else text
    if "estimated" in lowered or "ประมาณ" in text:
        return "estimated" if "estimated" in options else text
    if "measured" in lowered or "วัด" in text:
        return "measured" if "measured" in options else text
    if "internal" in lowered or "ภายใน" in text:
        return "internal" if "internal" in options else text
    if "external" in lowered or "ภายนอก" in text:
        return "external" if "external" in options else text
    for option in options:
        labels = {
            translate(f"{key_prefix}.{option}", "en"),
            translate(f"{key_prefix}.{option}", "th"),
        }
        if text in labels or any(label and label in text for label in labels):
            return option
    return text


def _multilane_template_id(value: str, template_options: dict[str, str]) -> str:
    if value in template_options:
        return value
    for template_id in template_options:
        if value in {
            template_options[template_id],
            translate(f"multilane.preset.{template_id}", "en"),
            translate(f"multilane.preset.{template_id}", "th"),
        }:
            return template_id
    return value


def _ramp_text(key: str, **params: Any) -> str:
    return translate(f"ramp.{key}", _ui_locale(), **params)


def _ramp_workflow_text(workflow: str, key: str, **params: Any) -> str:
    return translate(f"ramp.{workflow}.{key}", _ui_locale(), **params)


def _ramp_preset_label(preset_id: str) -> str:
    return _ramp_text(f"preset.{preset_id}")


def _ramp_text_for_locale(locale: str, key: str, **params: Any) -> str:
    return translate(f"ramp.{key}", locale, **params)


def _restore_project_locale(project: dict[str, Any]) -> None:
    """Restore explicitly stored project presentation metadata, if present."""

    saved_locale = project_presentation_locale(project)
    if saved_locale is not None:
        st.session_state["_pending_ui_locale"] = saved_locale


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
        fixture = load_packaged_yaml(FIXTURE_FILENAME)
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
        st.markdown(f"`{FIXTURE_FILENAME}`")
        with st.expander("Show full fixture path", expanded=False):
            st.code(f"packaged:hcmcalc.ui/data/{FIXTURE_FILENAME}", language=None)
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
        translate("supported.title", _ui_locale()),
        translate("supported.subtitle", _ui_locale()),
    )
    st.caption(translate("supported.intro", _ui_locale()))

    for group, workflow_ids in SUPPORTED_PAGE_WORKFLOW_GROUPS:
        render_section_label(translate(f"supported.section.{group}", _ui_locale()))
        for workflow_id in workflow_ids:
            with st.container(border=True):
                st.markdown(
                    f"**{translate(APP_VIEW_TO_NAV_KEY[workflow_id], _ui_locale())}**"
                )
                st.caption(
                    translate(f"supported.workflow.{workflow_id}.summary", _ui_locale())
                )
                columns = st.columns(2, gap="medium")
                with columns[0]:
                    st.markdown(f"**{translate('supported.currently_supported', _ui_locale())}**")
                    for index in range(1, 4):
                        st.markdown(
                            "- "
                            + translate(
                                f"supported.workflow.{workflow_id}.supported.{index}",
                                _ui_locale(),
                            )
                        )
                with columns[1]:
                    st.markdown(f"**{translate('supported.scope_limits', _ui_locale())}**")
                    for index in range(1, 4):
                        st.markdown(
                            "- "
                            + translate(
                                f"supported.workflow.{workflow_id}.limit.{index}",
                                _ui_locale(),
                            )
                        )

    render_section_label(translate("supported.section.product_capabilities", _ui_locale()))
    capability_columns = st.columns(2, gap="medium")
    for index, capability in enumerate(SUPPORTED_PAGE_CAPABILITIES):
        with capability_columns[index % 2]:
            st.markdown(
                "- " + translate(f"supported.capability.{capability}", _ui_locale())
            )

    render_section_label(translate("supported.section.current_limitations", _ui_locale()))
    for limitation in SUPPORTED_PAGE_LIMITATIONS:
        st.markdown("- " + translate(f"supported.limit.{limitation}", _ui_locale()))

    st.caption(translate("supported.phase_15_3_note", _ui_locale()))


def render_manual_ramp_calculator(workflow: str) -> None:
    """Render qualified HCM 7.0 merge or diverge worksheet."""

    pending = st.session_state.pop(f"manual_{workflow}_pending_project", None)
    if pending is not None:
        _restore_manual_ramp_project(workflow, pending)
    load_message = st.session_state.pop(f"manual_{workflow}_project_load_message", None)
    if load_message:
        st.success(load_message)
    render_page_header(_ramp_text(f"{workflow}.title"), _ramp_text(f"{workflow}.subtitle"))
    locale = _ui_locale()
    status_placeholder = st.empty()
    input_column, result_column = render_calculator_shell()
    with input_column:
        render_project_load_section(
            lambda: _render_manual_ramp_load_controls(workflow),
            label=_ramp_text("project_load"),
        )
        render_section_label(_ramp_text("setup"))
        st.caption(_ramp_text("method_caption"))
        st.caption(_ramp_text("fixed_scope"))
        st.session_state.setdefault(f"manual_{workflow}_unit_label", "Metric")
        unit_label = st.segmented_control(
            _ramp_text("unit_system"),
            ["Metric", "Imperial"],
            format_func=lambda item, locale=locale: _ramp_text_for_locale(locale, f"unit.{item.lower()}"),
            key=f"manual_{workflow}_unit_label",
        )
        preset_options = list(ramp_preset_options(workflow))
        preset_default = st.session_state.get(f"manual_{workflow}_preset_id", "blank_custom")
        if preset_default not in preset_options:
            preset_default = "blank_custom"
        preset_id = st.selectbox(
            _ramp_text("validation_preset"),
            preset_options,
            index=preset_options.index(preset_default),
            format_func=lambda preset, locale=locale: _ramp_text_for_locale(locale, f"preset.{preset}"),
            key=f"manual_{workflow}_preset_id_{locale}",
        )
        st.session_state[f"manual_{workflow}_preset_id"] = preset_id
    unit_system = unit_label.lower()
    context = (preset_id, unit_system)
    if st.session_state.get(f"manual_{workflow}_preset_context") != context:
        clear_manual_ramp_state(st.session_state, workflow)
        st.session_state[f"manual_{workflow}_preset_context"] = context
    ui = st.session_state.get(f"manual_{workflow}_loaded_displayed") or ramp_preset_ui_inputs(
        workflow, preset_id, unit_system
    )
    metric = unit_system == "metric"
    length_unit, speed_unit, width_unit = ("m", "km/h", "m") if metric else ("ft", "mph", "ft")
    ramp_density_unit = "ramps/km" if metric else "ramps/mi"
    with input_column:
        render_section_label(_ramp_text("geometry"))
        st.caption(_ramp_text("freeway_component"))
        geometry = st.columns(2)
        case_name = geometry[0].text_input(
            _ramp_text("case_name"),
            value=ui["case_name"],
            key=f"manual_{workflow}_input_case_{preset_id}_{unit_system}",
        )
        freeway_lanes = geometry[1].selectbox(
            _ramp_text("freeway_lanes"),
            [2, 3, 4],
            index=[2, 3, 4].index(int(ui["freeway_lanes"])),
            key=f"manual_{workflow}_input_lanes_{preset_id}_{unit_system}",
        )
        st.caption(_ramp_text("fixed_geometry_summary"))
        st.caption(_ramp_workflow_text(workflow, "ramp_component"))
        aux_label = "acceleration_length" if workflow == "merge" else "deceleration_length"
        auxiliary_lane_length = geometry[0].number_input(
            _ramp_text(aux_label, unit=length_unit),
            min_value=0.0,
            value=float(ui["auxiliary_lane_length"]),
            key=f"manual_{workflow}_input_aux_{preset_id}_{unit_system}",
            help=_ramp_text("auxiliary_length_help"),
        )
        render_section_label(_ramp_text("demand"))
        demand = st.columns(2)
        freeway_demand = demand[0].number_input(
            _ramp_text("freeway_demand"),
            min_value=0.0,
            value=float(ui["freeway_demand_veh_h"]),
            key=f"manual_{workflow}_input_freeway_demand_{preset_id}_{unit_system}",
        )
        ramp_demand_key = "on_ramp_demand" if workflow == "merge" else "off_ramp_demand"
        ramp_demand = demand[1].number_input(
            _ramp_text(ramp_demand_key),
            min_value=0.0,
            value=float(ui["ramp_demand_veh_h"]),
            key=f"manual_{workflow}_input_ramp_demand_{preset_id}_{unit_system}",
        )
        derived = freeway_demand + ramp_demand if workflow == "merge" else freeway_demand - ramp_demand
        st.caption(
            _ramp_text("derived_downstream" if workflow == "merge" else "derived_continuing", value=derived)
        )
        render_section_label(_ramp_text("ffs"))
        ffs = st.columns(2)
        ffs_source = ffs[0].selectbox(
            _ramp_text("ffs_source"),
            ["measured", "estimated"],
            index=0 if ui["ffs_source"] == "measured" else 1,
            format_func=lambda value, locale=locale: _ramp_text_for_locale(locale, f"ffs.{value}"),
            key=f"manual_{workflow}_input_ffs_source_{preset_id}_{unit_system}_{locale}",
            help=_ramp_text("freeway_ffs_help"),
        )
        if ffs_source == "measured":
            free_flow_speed = ffs[1].number_input(
                _ramp_text("measured_ffs", unit=speed_unit),
                min_value=1.0,
                value=float(ui["free_flow_speed"] or 60.0),
                key=f"manual_{workflow}_input_ffs_{preset_id}_{unit_system}",
            )
            base_free_flow_speed = lane_width = right_side_lateral_clearance = total_ramp_density = None
        else:
            free_flow_speed = None
            base_free_flow_speed = ffs[1].number_input(
                _ramp_text("base_ffs", unit=speed_unit),
                min_value=1.0,
                value=float(ui["base_free_flow_speed"] or 60.0),
                key=f"manual_{workflow}_input_base_ffs_{preset_id}_{unit_system}",
            )
            lane_width = ffs[0].number_input(
                _ramp_text("lane_width", unit=width_unit),
                min_value=0.1,
                value=float(ui["lane_width"] or (3.6 if metric else 12.0)),
                key=f"manual_{workflow}_input_lane_width_{preset_id}_{unit_system}",
            )
            right_side_lateral_clearance = ffs[1].number_input(
                _ramp_text("right_lateral_clearance", unit=width_unit),
                min_value=0.0,
                value=float(ui["right_side_lateral_clearance"] or (1.8 if metric else 6.0)),
                key=f"manual_{workflow}_input_clearance_{preset_id}_{unit_system}",
            )
            total_ramp_density = ffs[0].number_input(
                _ramp_text("total_ramp_density", unit=ramp_density_unit),
                min_value=0.0,
                value=float(ui["total_ramp_density"] or 0.0),
                key=f"manual_{workflow}_input_ramp_density_{preset_id}_{unit_system}",
            )
        ramp_ffs = ffs[1].number_input(
            _ramp_text("ramp_ffs", unit=speed_unit),
            min_value=1.0,
            value=float(ui["ramp_ffs"]),
            key=f"manual_{workflow}_input_ramp_ffs_{preset_id}_{unit_system}",
            help=_ramp_text("ramp_ffs_help"),
        )
        render_section_label(_ramp_text("phf_hv"))
        phf = st.columns(2)
        freeway_phf = phf[0].number_input(
            _ramp_text("freeway_phf"),
            min_value=0.01,
            max_value=1.0,
            value=float(ui["freeway_peak_hour_factor"]),
            key=f"manual_{workflow}_input_freeway_phf_{preset_id}_{unit_system}",
        )
        ramp_phf = phf[1].number_input(
            _ramp_text("ramp_phf"),
            min_value=0.01,
            max_value=1.0,
            value=float(ui["ramp_peak_hour_factor"]),
            key=f"manual_{workflow}_input_ramp_phf_{preset_id}_{unit_system}",
        )
        freeway_hv = phf[0].number_input(
            _ramp_text("freeway_hv"),
            min_value=0.0,
            max_value=100.0,
            value=float(ui["freeway_heavy_vehicle_percent"]),
            key=f"manual_{workflow}_input_freeway_hv_{preset_id}_{unit_system}",
        )
        ramp_hv = phf[1].number_input(
            _ramp_text("ramp_hv"),
            min_value=0.0,
            max_value=100.0,
            value=float(ui["ramp_heavy_vehicle_percent"]),
            key=f"manual_{workflow}_input_ramp_hv_{preset_id}_{unit_system}",
        )
        terrain_type = phf[0].selectbox(
            _ramp_text("terrain"),
            ["level", "rolling"],
            index=["level", "rolling"].index(ui["terrain_type"]),
            format_func=lambda value, locale=locale: _ramp_text_for_locale(locale, f"terrain.{value}"),
            key=f"manual_{workflow}_input_terrain_{preset_id}_{unit_system}_{locale}",
        )
        render_section_label(_ramp_text("evidence"))
        st.caption(_ramp_text("evidence_summary"))
        with st.expander(_ramp_text("evidence_details"), expanded=False):
            evidence = st.columns(2)
            geometry_source = evidence[0].text_input(
                _ramp_text("evidence_source"),
                value=ui["geometry_source"],
                key=f"manual_{workflow}_input_geometry_source_{preset_id}_{unit_system}",
            )
            geometry_notes = evidence[1].text_input(
                _ramp_text("evidence_notes"),
                value=ui["geometry_notes"],
                key=f"manual_{workflow}_input_geometry_notes_{preset_id}_{unit_system}",
            )
        render_section_label(_ramp_text("reference"))
        _render_manual_ramp_diagram(
            workflow=workflow,
            freeway_lanes=int(freeway_lanes),
            auxiliary_lane_length=float(auxiliary_lane_length),
            length_unit=length_unit,
        )
        run_ramp = st.button(_ramp_text("run"), type="primary", width="stretch", key=f"manual_{workflow}_run")
        displayed_inputs = {
            "case_name": case_name,
            "freeway_lanes": freeway_lanes,
            "auxiliary_lane_length": auxiliary_lane_length,
            "freeway_demand_veh_h": freeway_demand,
            "ramp_demand_veh_h": ramp_demand,
            "freeway_peak_hour_factor": freeway_phf,
            "ramp_peak_hour_factor": ramp_phf,
            "freeway_heavy_vehicle_percent": freeway_hv,
            "ramp_heavy_vehicle_percent": ramp_hv,
            "terrain_type": terrain_type,
            "ffs_source": ffs_source,
            "free_flow_speed": free_flow_speed,
            "base_free_flow_speed": base_free_flow_speed,
            "lane_width": lane_width,
            "right_side_lateral_clearance": right_side_lateral_clearance,
            "total_ramp_density": total_ramp_density,
            "ramp_ffs": ramp_ffs,
            "speed_adjustment_factor_source": "hcm_base_conditions",
            "capacity_adjustment_factor_source": "hcm_base_conditions",
            "geometry_source": geometry_source,
            "geometry_notes": geometry_notes,
        }
        try:
            submitted_inputs = ramp_ui_inputs_to_engine(workflow, displayed_inputs, unit_system)
        except (HCMCalcError, ValueError) as exc:
            submitted_inputs = {"invalid": str(exc)}
        workflow_inputs = {
            "method_family": ramp_method_family(workflow),
            "calculation_contract": ramp_calculation_contract(workflow),
            "normalized_engine_inputs": submitted_inputs,
        }
        current = render_calculation_status(f"manual_{workflow}", workflow_inputs, status_placeholder)
        if run_ramp:
            st.session_state.pop(f"manual_{workflow}_error", None)
            st.session_state.pop(f"manual_{workflow}_result", None)
            try:
                engine_inputs = ramp_ui_inputs_to_engine(workflow, displayed_inputs, unit_system)
                result = run_manual_ramp(workflow, engine_inputs)
                st.session_state[f"manual_{workflow}_result"] = result_to_dict(result)
                st.session_state[f"manual_{workflow}_audit"] = build_manual_ramp_audit_record(
                    workflow,
                    preset_id,
                    engine_inputs,
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    result=result,
                )
                mark_calculated(st.session_state, f"manual_{workflow}", workflow_inputs)
                current = render_calculation_status(f"manual_{workflow}", workflow_inputs, status_placeholder)
            except UnsupportedScopeError as exc:
                st.session_state[f"manual_{workflow}_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.UNSUPPORTED_SCOPE,
                }
                st.session_state[f"manual_{workflow}_audit"] = build_manual_ramp_audit_record(
                    workflow,
                    preset_id,
                    submitted_inputs if "invalid" not in submitted_inputs else {},
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    error=exc,
                )
            except (HCMCalcError, ValueError) as exc:
                st.session_state[f"manual_{workflow}_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.INVALID_INPUT,
                }
                st.session_state[f"manual_{workflow}_audit"] = build_manual_ramp_audit_record(
                    workflow,
                    preset_id,
                    submitted_inputs if "invalid" not in submitted_inputs else {},
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    error=exc,
                )
    with result_column:
        with st.expander(_ramp_text("validation"), expanded=False):
            st.markdown(f"**{_ramp_text('validation_basis_heading')}**")
            st.caption(_ramp_text("validation_basis"))
            st.markdown(f"**{_ramp_text('supported_scope_heading')}**")
            st.caption(_ramp_text("supported_scope"))
            st.markdown(f"**{_ramp_text('not_supported_heading')}**")
            st.caption(_ramp_text("not_supported"))
        render_section_label(_ramp_text("results"))
        error = st.session_state.get(f"manual_{workflow}_error")
        result_data = st.session_state.get(f"manual_{workflow}_result")
        audit = st.session_state.get(f"manual_{workflow}_audit")
        if error:
            error_state = (
                error.get("state")
                if isinstance(error, dict)
                else ResultPresentationState.INTERNAL_ERROR
            )
            if error_state not in {
                ResultPresentationState.UNSUPPORTED_SCOPE,
                ResultPresentationState.INVALID_INPUT,
                ResultPresentationState.INTERNAL_ERROR,
            }:
                error_state = ResultPresentationState.INTERNAL_ERROR
            message_key = {
                ResultPresentationState.UNSUPPORTED_SCOPE: "unsupported",
                ResultPresentationState.INVALID_INPUT: "invalid",
                ResultPresentationState.INTERNAL_ERROR: "internal_error",
            }[error_state]
            render_result_state_panel(error_state, _ramp_text(message_key))
            detail = error.get("message") if isinstance(error, dict) else str(error)
            if (
                workflow == "diverge"
                and isinstance(detail, str)
                and "off-ramp demand cannot exceed upstream freeway demand" in detail
            ):
                detail = _ramp_workflow_text("diverge", "invalid_continuing_detail")
            st.caption(_ramp_text("error_details", error=detail))
            with st.expander(_ramp_text("audit"), expanded=False):
                st.json(audit)
            render_manual_ramp_project_file_controls(
                workflow, preset_id, unit_system, displayed_inputs, None, None
            )
        elif not result_data:
            render_result_state_panel(ResultPresentationState.PRERUN, _ramp_text("prerun"))
            render_manual_ramp_project_file_controls(
                workflow, preset_id, unit_system, displayed_inputs, None, None
            )
        else:
            presentation_state = resolve_result_presentation_state(
                freshness=workflow_status(
                    st.session_state, f"manual_{workflow}", workflow_inputs
                ),
                has_result=True,
                warnings=_ramp_warning_messages(result_data["outputs"]),
                capacity_failure=_ramp_is_capacity_failure(result_data["outputs"]),
            )
            if presentation_state == ResultPresentationState.STALE_RESULT:
                render_result_state_panel(presentation_state, _ramp_text("stale_info"))
                render_manual_ramp_project_file_controls(
                    workflow, preset_id, unit_system, displayed_inputs, None, None
                )
                st.caption(_ramp_text("export_stale"))
                with st.expander(_ramp_text("audit"), expanded=False):
                    st.json(audit)
                return

            outputs = result_data["outputs"]
            result_unit_system = (
                str(audit.get("unit_system", unit_system))
                if isinstance(audit, dict)
                else unit_system
            )
            display = ramp_display_outputs(outputs, result_unit_system)
            downstream_key = (
                "downstream_freeway_flow_pc_h"
                if workflow == "merge"
                else "continuing_freeway_flow_pc_h"
            )
            vc_key = (
                "downstream_freeway_demand_capacity_ratio"
                if workflow == "merge"
                else "upstream_freeway_demand_capacity_ratio"
            )
            max_key = (
                "maximum_desirable_merge_flow_pc_h"
                if workflow == "merge"
                else "maximum_desirable_diverge_flow_pc_h"
            )
            ffs_source_result = (
                audit.get("normalized_engine_inputs", {}).get("ffs_source")
                if isinstance(audit, dict)
                else None
            ) or _ramp_text("not_evaluated")
            render_result_summary_panel(
                primary_label=translate("result.level_of_service", _ui_locale()),
                primary_value=str(outputs["level_of_service"]),
                primary_kind="los",
                hero_supporting_label=translate("result.density", _ui_locale()),
                hero_supporting_value=_ramp_display_metric(display["density"]),
                secondary_metrics=[
                    {
                        "label": _ramp_text("ramp_influence_speed"),
                        "value": _ramp_display_metric(display["ramp_influence_speed"]),
                    },
                    {
                        "label": _ramp_text("all_lanes_speed"),
                        "value": _ramp_display_metric(display["all_lanes_speed"]),
                    },
                    {
                        "label": _ramp_text("freeway_flow"),
                        "value": _ramp_flow_metric(outputs.get("freeway_flow_pc_h")),
                    },
                    {
                        "label": _ramp_text("ramp_flow"),
                        "value": _ramp_flow_metric(outputs.get("ramp_flow_pc_h")),
                    },
                    {
                        "label": _ramp_text("downstream_flow" if workflow == "merge" else "continuing_flow"),
                        "value": _ramp_flow_metric(outputs.get(downstream_key)),
                    },
                    {
                        "label": _ramp_text("influence_lane_flow"),
                        "value": _ramp_flow_metric(outputs.get("adjusted_v12_pc_h")),
                    },
                    {
                        "label": _ramp_text("governing_capacity"),
                        "value": _ramp_flow_metric(display["governing_capacity"]["value"]),
                    },
                    {
                        "label": _ramp_text("vc"),
                        "value": _ramp_ratio_metric(outputs.get(vc_key)),
                    },
                    {
                        "label": _ramp_text("capacity_status"),
                        "value": _ramp_text(f"capacity_status.{outputs['capacity_status']}"),
                    },
                    {"label": _ramp_text("ffs_source_label"), "value": ffs_source_result},
                    {"label": _ramp_text("method_version"), "value": outputs["method_version"]},
                    {
                        "label": _ramp_text("governing_reason"),
                        "value": outputs.get("governing_capacity_failure") or _ramp_text("none"),
                    },
                ],
            )
            if presentation_state == ResultPresentationState.CAPACITY_FAILURE:
                render_result_state_panel(
                    presentation_state, _ramp_text("capacity_failure")
                )
            elif presentation_state == ResultPresentationState.VALID_CURRENT_RESULT_WITH_WARNING:
                render_result_state_panel(
                    presentation_state,
                    _ramp_text(
                        "maximum_warning_detail",
                        actual=outputs.get("merge_influence_entering_flow_vr12_pc_h", outputs.get("adjusted_v12_pc_h")),
                        maximum=outputs.get(max_key),
                    ),
                )
            with st.expander(_ramp_text("calculation_details"), expanded=False):
                st.markdown(f"**{_ramp_text('flow_audit')}**")
                st.json({
                    key: outputs.get(key)
                    for key in (
                        "freeway_flow_pc_h", "ramp_flow_pc_h", downstream_key,
                        "adjusted_v12_pc_h", "merge_influence_entering_flow_vr12_pc_h",
                        "freeway_heavy_vehicle_adjustment_factor",
                        "ramp_heavy_vehicle_adjustment_factor",
                        "freeway_ffs_mph", "ramp_ffs_mph", "ffs_source",
                    )
                })
                st.markdown(f"**{_ramp_text('capacity_audit')}**")
                st.json({
                    key: outputs.get(key)
                    for key in (
                        "adjusted_freeway_capacity_pc_h",
                        "adjusted_ramp_roadway_capacity_pc_h",
                        "capacity_status", vc_key, "governing_capacity_failure",
                        "maximum_desirable_influence_flow_exceeded", max_key,
                    )
                })
                render_list(
                    translate("common.assumptions", _ui_locale()),
                    result_data["assumptions"],
                    translate("common.no_assumptions", _ui_locale()),
                )
                render_list(
                    translate("common.warnings", _ui_locale()),
                    result_data["warnings"],
                    translate("common.no_warnings", _ui_locale()),
                )
            with st.expander(_ramp_text("audit"), expanded=False):
                st.json(audit)
                st.dataframe(
                    [
                        {**value, "value": str(value["value"])}
                        for value in result_data["intermediate_values"]
                    ],
                    hide_index=True,
                    width="stretch",
                )
            with st.expander(_ramp_text("full_json")):
                st.json(
                    {
                        "calculation_type": ramp_project_type(workflow),
                        "unit_system": result_unit_system,
                        "display_outputs": display,
                        "engine_result": result_data,
                        "audit_record": audit,
                    }
                )
            render_manual_ramp_project_file_controls(
                workflow, preset_id, unit_system, displayed_inputs, result_data, audit
            )
            render_export_report_section(
                ramp_project_type(workflow),
                result_data,
                result_unit_system,
                inputs=(audit.get("displayed_inputs", displayed_inputs) if isinstance(audit, dict) else displayed_inputs),
                audit_record=audit,
                template_id=preset_id,
                label=_ramp_text("export_report"),
            )


def _render_manual_ramp_diagram(
    *,
    workflow: str,
    freeway_lanes: int,
    auxiliary_lane_length: float,
    length_unit: str,
) -> None:
    st.markdown(f"**{_ramp_workflow_text(workflow, 'diagram_title')}**")
    st.image(str(ramp_diagram_path(workflow)), caption=_ramp_text("reference_caption"))
    st.caption(
        _ramp_workflow_text(
            workflow,
            "diagram_summary",
            lanes=freeway_lanes,
            length=auxiliary_lane_length,
            unit=length_unit,
        )
    )
    st.caption(_ramp_text("reference_text_merge" if workflow == "merge" else "reference_text_diverge"))
    st.caption(_ramp_text("diagram_alt_merge" if workflow == "merge" else "diagram_alt_diverge"))


def _ramp_is_capacity_failure(outputs: dict[str, Any]) -> bool:
    return outputs.get("capacity_status") == "demand_exceeds_capacity"


def _ramp_warning_messages(outputs: dict[str, Any]) -> list[str]:
    return [_ramp_text("maximum_warning")] if outputs.get("maximum_desirable_influence_flow_exceeded") else []


def _ramp_display_metric(metric: dict[str, Any]) -> str:
    value = metric["value"]
    if value is None:
        return _ramp_text("not_predicted")
    return f"{value:.1f} {metric['unit']}" if metric["unit"] else f"{value:.3f}"


def _ramp_flow_metric(value: Any) -> str:
    if value is None:
        return _ramp_text("not_predicted")
    return f"{float(value):.0f} pc/h"


def _ramp_ratio_metric(value: Any) -> str:
    if value is None:
        return _ramp_text("not_predicted")
    return f"{float(value):.3f}"


def render_manual_ramp_project_file_controls(
    workflow: str,
    preset_id: str,
    unit_system: str,
    displayed_inputs: dict[str, Any],
    result: dict[str, Any] | None,
    audit: dict[str, Any] | None,
) -> None:
    try:
        project_json = create_manual_ramp_project_json(
            workflow,
            preset_id,
            unit_system,
            displayed_inputs,
            result=result,
            audit_record=audit,
            locale=_ui_locale(),
        )
    except ProjectFileError as exc:
        st.caption(_ramp_text("project_load_error", error=str(exc)))
        return
    render_project_output_section(
        _ramp_workflow_text(workflow, "project_caption"),
        lambda: st.download_button(
            _ramp_text("save_project"),
            data=project_json,
            file_name=f"manual-freeway-{workflow}-segment-project.json",
            mime="application/json",
            width="content",
            key=f"manual_{workflow}_save_project",
        ),
        label=_ramp_text("project_output"),
    )


def _render_manual_ramp_load_controls(workflow: str) -> None:
    uploaded = st.file_uploader(
        _ramp_workflow_text(workflow, "project_file"),
        type=["json"],
        key=f"manual_{workflow}_project_file_uploader",
    )
    if uploaded is not None and st.button(_ramp_text("load_project"), key=f"manual_{workflow}_project_load"):
        try:
            project = load_manual_ramp_project_json(
                uploaded.getvalue(), workflow
            )
            saved_locale = project_presentation_locale(project)
            if saved_locale is not None:
                st.session_state["_pending_ui_locale"] = saved_locale
            st.session_state[f"manual_{workflow}_pending_project"] = project
            st.rerun()
        except ProjectFileError as exc:
            st.error(_ramp_text("project_load_error", error=str(exc)))


def _restore_manual_ramp_project(workflow: str, project: dict[str, Any]) -> None:
    _restore_project_locale(project)
    clear_manual_ramp_state(st.session_state, workflow)
    unit_system = project["unit_system"]
    displayed = project["displayed_ui_inputs"]
    st.session_state[f"manual_{workflow}_loaded_displayed"] = displayed
    st.session_state[f"manual_{workflow}_unit_label"] = unit_system.title()
    st.session_state[f"manual_{workflow}_preset_id"] = project.get("preset_id", "blank_custom")
    st.session_state[f"manual_{workflow}_preset_context"] = (
        project.get("preset_id", "blank_custom"),
        unit_system,
    )
    if project.get("load_status") == "result_current":
        st.session_state[f"manual_{workflow}_result"] = project.get("calculation_result")
        st.session_state[f"manual_{workflow}_audit"] = project.get("audit")
        normalized = project["normalized_engine_inputs"]
        mark_calculated(
            st.session_state,
            f"manual_{workflow}",
            {
                "method_family": ramp_method_family(workflow),
                "calculation_contract": ramp_calculation_contract(workflow),
                "normalized_engine_inputs": normalized,
            },
        )
    st.session_state[f"manual_{workflow}_project_load_message"] = project_load_message(project, _ui_locale())


def render_manual_multilane_calculator() -> None:
    """Render the bounded Multilane segment worksheet."""

    pending_project = st.session_state.pop("manual_multilane_pending_project", None)
    if pending_project is not None:
        _restore_manual_multilane_project(pending_project)
    load_message = st.session_state.pop("manual_multilane_project_load_message", None)
    if load_message is not None:
        st.success(load_message)

    render_page_header(
        _multilane_text("title"),
        _multilane_text("subtitle"),
    )
    status_placeholder = st.empty()
    input_column, result_column = render_calculator_shell()
    template_options = multilane_template_options()
    with input_column:
        with st.expander(_multilane_text("project_load"), expanded=False):
            _render_manual_multilane_load_controls()
        render_section_label(_multilane_text("setup"))
        st.caption(_multilane_text("scope"))
        st.session_state.setdefault("manual_multilane_unit_label", "metric")
        unit_label = st.segmented_control(
            _multilane_text("unit_system"),
            ["metric", "imperial"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"multilane.unit.{value}", locale
            ),
            key="manual_multilane_unit_label",
        )
        st.caption(_multilane_text("unit_caption"))
        with st.expander(_multilane_text("starting_values"), expanded=False):
            st.caption(_multilane_text("starting_values_caption"))
            template_id = st.selectbox(
                _multilane_text("defaults"),
                list(template_options),
                format_func=lambda value, locale=_ui_locale(): translate(
                    f"multilane.preset.{value}", locale
                ),
                key=f"multilane_template_id_{_ui_locale()}",
            )
            template_id = _multilane_template_id(str(template_id), template_options)
            st.caption(_multilane_text("defaults_caption"))
    unit_system = unit_label
    template_context = (template_id, unit_system)
    if st.session_state.get("manual_multilane_template_context") != template_context:
        clear_manual_multilane_state(st.session_state)
        if "manual_multilane_template_context" in st.session_state:
            st.session_state["manual_multilane_reset_message"] = _multilane_text("reset_message")
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
        ffs_source_key = f"manual_multilane_input_ffs_source_{template_id}_{unit_system}"
        st.session_state.setdefault(
            ffs_source_key, str(ui_inputs.get("ffs_source", "estimated"))
        )
        ffs_source = st.segmented_control(
            _multilane_text("ffs_source"),
            ["estimated", "measured"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"multilane.ffs.{value}", locale
            ),
            key=ffs_source_key,
            help=_multilane_text("ffs_source_help"),
        )
        with st.container():
            render_section_label(_multilane_text("geometry"))
            roadway_columns = st.columns(2)
            number_of_lanes = roadway_columns[0].number_input(
                _multilane_text("number_of_lanes"),
                min_value=2,
                max_value=8,
                step=1,
                value=int(ui_inputs["number_of_lanes"]),
                key=f"manual_multilane_input_lanes_{template_id}_{unit_system}",
            )
            segment_length = roadway_columns[1].number_input(
                _multilane_text("segment_length", unit=length_unit),
                min_value=0.001,
                value=float(ui_inputs["segment_length"]),
                key=f"manual_multilane_input_length_{template_id}_{unit_system}",
            )
            free_flow_speed = None
            if ffs_source == "measured":
                free_flow_speed = roadway_columns[0].number_input(
                    _multilane_text("measured_ffs", unit=speed_unit),
                    min_value=1.0,
                    value=float(ui_inputs.get("free_flow_speed") or ui_inputs["posted_speed_limit"]),
                    key=f"manual_multilane_input_measured_ffs_{template_id}_{unit_system}",
                    help=_multilane_text("measured_ffs_help"),
                )
                posted_speed_limit = lane_width = roadside_lateral_clearance = None
                access_point_density = median_type = left_side_lateral_clearance = None
            else:
                posted_speed_limit = roadway_columns[0].number_input(
                    _multilane_text("posted_speed", unit=speed_unit), min_value=1.0,
                    value=float(ui_inputs["posted_speed_limit"]),
                    key=f"manual_multilane_input_speed_{template_id}_{unit_system}",
                    help=_multilane_text("posted_speed_help"),
                )
                lane_width = roadway_columns[1].number_input(
                    _multilane_text("lane_width", unit=width_unit), min_value=0.1,
                    value=float(ui_inputs["lane_width"]),
                    key=f"manual_multilane_input_lane_width_{template_id}_{unit_system}",
                )
                roadside_lateral_clearance = roadway_columns[0].number_input(
                    _multilane_text("right_clearance", unit=width_unit), min_value=0.0,
                    value=float(ui_inputs["roadside_lateral_clearance"]),
                    key=f"manual_multilane_input_clearance_{template_id}_{unit_system}",
                    help=_multilane_text("right_clearance_help"),
                )
                median_type = roadway_columns[1].selectbox(
                    _multilane_text("median_type"), ["twltl", "undivided", "divided"],
                    index=["twltl", "undivided", "divided"].index(ui_inputs.get("median_type", "twltl")),
                    format_func=lambda value, locale=_ui_locale(): translate(
                        f"multilane.median.{value}", locale
                    ),
                    key=f"manual_multilane_input_median_{template_id}_{unit_system}",
                    help=_multilane_text("median_help"),
                )
                left_side_lateral_clearance = None
                if median_type == "divided":
                    left_side_lateral_clearance = roadway_columns[0].number_input(
                        _multilane_text("left_clearance", unit=width_unit), min_value=0.0,
                        value=float(ui_inputs.get("left_side_lateral_clearance", 6.0)),
                        key=f"manual_multilane_input_left_clearance_{template_id}_{unit_system}",
                        help=_multilane_text("left_clearance_help"),
                    )
                access_point_density = roadway_columns[1].number_input(
                    _multilane_text("access_density", unit=access_unit), min_value=0.0,
                    value=float(ui_inputs["access_point_density"]),
                    key=f"manual_multilane_input_access_{template_id}_{unit_system}",
                )

            render_section_label(_multilane_text("demand"))
            traffic_columns = st.columns(2)
            demand_volume_veh_h = traffic_columns[0].number_input(
                _multilane_text("demand_volume"),
                min_value=1.0,
                value=float(ui_inputs["demand_volume_veh_h"]),
                key=f"manual_multilane_input_demand_{template_id}_{unit_system}",
            )
            peak_hour_factor = traffic_columns[1].number_input(
                _multilane_text("peak_hour_factor"),
                min_value=0.01,
                max_value=1.0,
                value=float(ui_inputs["peak_hour_factor"]),
                key=f"manual_multilane_input_phf_{template_id}_{unit_system}",
            )
            heavy_vehicle_percent = traffic_columns[0].number_input(
                _multilane_text("heavy_vehicles"),
                min_value=0.0,
                max_value=100.0,
                value=float(ui_inputs["heavy_vehicle_percent"]),
                key=f"manual_multilane_input_heavy_{template_id}_{unit_system}",
            )
            grade_percent = traffic_columns[1].number_input(
                _multilane_text("grade"),
                value=float(ui_inputs["grade_percent"]),
                key=f"manual_multilane_input_grade_{template_id}_{unit_system}",
            )
            render_section_label(_multilane_text("heavy_pce"))
            pce_mode_key = f"manual_multilane_input_pce_mode_{template_id}_{unit_system}"
            st.session_state.setdefault(
                pce_mode_key, str(ui_inputs.get("pce_mode", "internal"))
            )
            pce_mode = st.segmented_control(
                _multilane_text("pce_source"), ["internal", "external"],
                format_func=lambda value, locale=_ui_locale(): translate(
                    f"multilane.pce.{value}", locale
                ),
                key=pce_mode_key,
                help=_multilane_text("pce_source_help"),
            )
            passenger_car_equivalent = None
            terrain_type = truck_mix = None
            if pce_mode == "external":
                passenger_car_equivalent = traffic_columns[1].number_input(
                    _multilane_text("external_pce"),
                    min_value=0.01,
                    value=float(ui_inputs.get("passenger_car_equivalent") or 2.24),
                    key=f"manual_multilane_input_pce_{template_id}_{unit_system}",
                    help=_multilane_text("external_pce_help"),
                )
            else:
                terrain_type = traffic_columns[0].selectbox(
                    _multilane_text("terrain"), ["level", "rolling", "specific_grade"],
                    index=["level", "rolling", "specific_grade"].index(ui_inputs.get("terrain_type", "specific_grade")),
                    format_func=lambda value, locale=_ui_locale(): translate(
                        f"multilane.terrain.{value}", locale
                    ),
                    key=f"manual_multilane_input_terrain_{template_id}_{unit_system}",
                )
                if terrain_type == "specific_grade":
                    mixes = ["default_30_sut_70_tt", "equal_50_sut_50_tt", "majority_70_sut_30_tt"]
                    truck_mix = traffic_columns[1].selectbox(
                        _multilane_text("truck_mix"), mixes,
                        index=mixes.index(ui_inputs.get("truck_mix", mixes[0])),
                        format_func=lambda value, locale=_ui_locale(): translate(
                            f"multilane.truck_mix.{value}", locale
                        ),
                        key=f"manual_multilane_input_truck_mix_{template_id}_{unit_system}",
                        help=_multilane_text("truck_mix_help"),
                    )
            render_section_label(_multilane_text("advanced"))
            st.caption(_multilane_text("driver_population_caption"))
            run_multilane = st.button(
                _multilane_text("calculate"), type="primary", width="stretch"
            )

        displayed_inputs = {
            "number_of_lanes": int(number_of_lanes),
            "segment_length": segment_length,
            "demand_volume_veh_h": demand_volume_veh_h,
            "peak_hour_factor": peak_hour_factor,
            "heavy_vehicle_percent": heavy_vehicle_percent,
            "grade_percent": grade_percent,
            "ffs_source": ffs_source,
            "pce_mode": pce_mode,
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
        conversion_error: Exception | None = None
        try:
            submitted_inputs = multilane_ui_inputs_to_engine(
                displayed_inputs, inputs, unit_system
            )
        except (HCMCalcError, ValueError) as exc:
            conversion_error = exc
            submitted_inputs = {}
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
            try:
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
            except ProjectFileError:
                st.caption(_multilane_text("project_save_unavailable"))
                return
            st.download_button(
                _multilane_text("save_project"),
                data=project_json,
                file_name=f"{template_id}-manual-multilane-project.json",
                mime="application/json",
                width="stretch",
            )

    if run_multilane:
        st.session_state.pop("manual_multilane_result", None)
        st.session_state.pop("manual_multilane_error", None)
        if conversion_error is not None:
            st.session_state["manual_multilane_error"] = {
                "message": str(conversion_error),
                "state": ResultPresentationState.INVALID_INPUT,
            }
            st.session_state["manual_multilane_audit"] = (
                build_manual_multilane_audit_record(
                    template_id,
                    {},
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    error=conversion_error,
                )
            )
        else:
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
            except UnsupportedScopeError as exc:
                st.session_state["manual_multilane_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.UNSUPPORTED_SCOPE,
                }
                st.session_state["manual_multilane_audit"] = (
                    build_manual_multilane_audit_record(
                        template_id,
                        submitted_inputs,
                        unit_system=unit_system,
                        displayed_inputs=displayed_inputs,
                        error=exc,
                    )
                )
            except HCMCalcError as exc:
                st.session_state["manual_multilane_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.INVALID_INPUT,
                }
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
        with st.expander(_multilane_text("validation"), expanded=False):
            st.markdown(f"**{_multilane_text('validation_basis_heading')}**")
            st.caption(_multilane_text("validation_basis"))
            st.markdown(f"**{_multilane_text('supported_scope_heading')}**")
            st.caption(_multilane_text("supported_scope"))
            st.markdown(f"**{_multilane_text('not_supported_heading')}**")
            st.caption(_multilane_text("not_supported"))
        render_section_label(_multilane_text("results"))
        error = st.session_state.get("manual_multilane_error")
        audit = st.session_state.get("manual_multilane_audit")
        if error is not None:
            error_state = (
                error.get("state")
                if isinstance(error, dict)
                else ResultPresentationState.INTERNAL_ERROR
            )
            if error_state not in {
                ResultPresentationState.UNSUPPORTED_SCOPE,
                ResultPresentationState.INVALID_INPUT,
                ResultPresentationState.INTERNAL_ERROR,
            }:
                error_state = ResultPresentationState.INTERNAL_ERROR
            message_key = {
                ResultPresentationState.UNSUPPORTED_SCOPE: "unsupported",
                ResultPresentationState.INVALID_INPUT: "invalid",
                ResultPresentationState.INTERNAL_ERROR: "internal_error",
            }[error_state]
            render_result_state_panel(
                error_state,
                _multilane_text(message_key),
            )
            detail = error.get("message") if isinstance(error, dict) else str(error)
            st.caption(_multilane_text("error_details", error=detail))
            with st.expander(_multilane_text("audit"), expanded=False):
                st.json(audit)
            render_project_output_section(
                _multilane_text("project_caption"),
                render_multilane_project_download,
                label=_multilane_text("project_output"),
            )
            return
        result_data = st.session_state.get("manual_multilane_result")
        if result_data is None:
            render_result_state_panel(
                ResultPresentationState.PRERUN,
                _multilane_text("prerun"),
            )
            render_project_output_section(
                _multilane_text("project_caption"),
                render_multilane_project_download,
                label=_multilane_text("project_output"),
            )
            return

        presentation_state = resolve_result_presentation_state(
            freshness=workflow_status(
                st.session_state, "manual_multilane", multilane_workflow_inputs
            ),
            has_result=True,
            warnings=result_data.get("warnings", ()),
            capacity_failure=result_data["outputs"].get("capacity_check")
            == "demand_exceeds_capacity",
        )
        if presentation_state == ResultPresentationState.STALE_RESULT:
            render_result_state_panel(
                presentation_state, _multilane_text("stale")
            )
            render_project_output_section(
                _multilane_text("project_caption"),
                render_multilane_project_download,
                label=_multilane_text("project_output"),
            )
            st.caption(_multilane_text("export_stale"))
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
                else _multilane_text("not_predicted")
            )
        render_result_summary_panel(
            primary_label=translate("result.level_of_service", _ui_locale()),
            primary_value=str(outputs["level_of_service"]),
            primary_kind="los",
            hero_supporting_label=translate("result.density", _ui_locale()),
            hero_supporting_value=predicted(display["density"]),
            secondary_metrics=[
                {
                    "label": _multilane_text("speed_used_for_density"),
                    "value": predicted(display["speed_used_for_density"]),
                },
                {
                    "label": translate("result.demand_flow_rate", _ui_locale()),
                    "value": (
                        f"{display['demand_flow_rate']['value']:.0f} "
                        f"{display['demand_flow_rate']['unit']}"
                    ),
                },
                {
                    "label": translate("result.capacity", _ui_locale()),
                    "value": (
                        f"{display['capacity']['value']:.0f} "
                        f"{display['capacity']['unit']}"
                    ),
                },
                {
                    "label": _multilane_text("capacity_check"),
                    "value": _multilane_text(
                        f"capacity_status.{outputs['capacity_check']}"
                    ),
                },
                {"label": _multilane_text("ffs_source_label"), "value": outputs["ffs_source"]},
                {
                    "label": _multilane_text("adjusted_ffs"),
                    "value": (
                        f"{display['adjusted_free_flow_speed']['value']:.1f} "
                        f"{display['adjusted_free_flow_speed']['unit']}"
                    ),
                },
                {
                    "label": _multilane_text("base_ffs"),
                    "value": (
                        f"{display['base_free_flow_speed']['value']:.1f} "
                        f"{display['base_free_flow_speed']['unit']}"
                    ),
                },
                {
                    "label": _multilane_text("heavy_vehicle_factor"),
                    "value": f"{outputs['heavy_vehicle_adjustment_factor']:.3f}",
                },
                {
                    "label": _multilane_text("demand_capacity"),
                    "value": f"{outputs['demand_capacity_ratio']:.3f}",
                },
                {
                    "label": _multilane_text("pce"),
                    "value": f"{outputs['passenger_car_equivalent']:.2f} ({outputs['pce_source']})",
                },
            ],
        )
        if presentation_state == ResultPresentationState.CAPACITY_FAILURE:
            render_result_state_panel(
                presentation_state, _multilane_text("capacity_failure")
            )
        elif presentation_state == ResultPresentationState.VALID_CURRENT_RESULT_WITH_WARNING:
            render_result_state_panel(
                presentation_state, _multilane_text("warning")
            )

        with st.expander(_multilane_text("calculation_details"), expanded=False):
            st.markdown(f"**{_multilane_text('ffs_audit')}**")
            st.json({
                "ffs_source": outputs["ffs_source"],
                "base_free_flow_speed_mph": outputs["base_free_flow_speed_mph"],
                "lane_width_adjustment_mph": outputs["lane_width_adjustment_mph"],
                "total_lateral_clearance_adjustment_mph": outputs["total_lateral_clearance_adjustment_mph"],
                "median_type_adjustment_mph": outputs["median_type_adjustment_mph"],
                "access_point_adjustment_mph": outputs["access_point_adjustment_mph"],
                "adjusted_free_flow_speed_mph": outputs["adjusted_free_flow_speed_mph"],
            })
            st.markdown(f"**{_multilane_text('pce_audit')}**")
            st.json({
                key: outputs.get(key)
                for key in (
                    "passenger_car_equivalent", "pce_source", "pce_lookup_path",
                    "effective_grade_for_pce_percent", "effective_grade_length_mi_for_pce",
                    "truck_composition", "heavy_vehicle_adjustment_factor",
                )
            })
            render_list(
                translate("common.assumptions", _ui_locale()),
                result_data["assumptions"],
                translate("common.no_assumptions", _ui_locale()),
            )
            render_list(
                translate("common.warnings", _ui_locale()),
                result_data["warnings"],
                translate("common.no_warnings", _ui_locale()),
            )
            render_list(
                _multilane_text("unsupported_scope_notes"),
                outputs["unsupported_scope_notes"],
                _multilane_text("no_unsupported_scope_notes"),
            )
        with st.expander(_multilane_text("audit"), expanded=False):
            st.json(audit)
            st.dataframe(
                result_data["intermediate_values"],
                hide_index=True,
                width="stretch",
            )
        with st.expander(_multilane_text("full_json")):
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
            _multilane_text("project_caption"),
            render_multilane_project_download,
            label=_multilane_text("project_output"),
        )
        if multilane_is_current:
            render_export_report_section(
                "manual_multilane_v0", result_data, result_unit_system,
                inputs=(audit.get("displayed_inputs", displayed_inputs) if isinstance(audit, dict) else displayed_inputs),
                audit_record=audit, template_id=template_id,
                label=_multilane_text("export_report"),
            )
        else:
            st.caption(_multilane_text("export_stale"))


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


def _weaving_unit_value(value: Any) -> str:
    return _localized_option_to_value(value, "weaving.unit", ("metric", "imperial"))


def _weaving_result_metric(metric: dict[str, Any], decimals: int = 1) -> str:
    if metric["value"] is None:
        return translate("status.not_predicted", _ui_locale())
    return f"{metric['value']:.{decimals}f} {metric['unit']}"


def _weaving_error_state(error: Any) -> ResultPresentationState:
    if isinstance(error, dict):
        state = error.get("state")
        if state in {
            ResultPresentationState.UNSUPPORTED_SCOPE,
            ResultPresentationState.INVALID_INPUT,
            ResultPresentationState.INTERNAL_ERROR,
        }:
            return state
    return ResultPresentationState.INTERNAL_ERROR


def _weaving_stopping_or_handoff(outputs: dict[str, Any]) -> bool:
    return (
        outputs.get("support_status") == "hcm_handoff_required"
        or outputs.get("scope_status") == "hcm_handoff_lmax"
    )


def _weaving_project_download(
    *,
    preset_id: str,
    unit_system: str,
    displayed_inputs: dict[str, Any],
    current: bool,
) -> None:
    audit = st.session_state.get("manual_weaving_audit")
    result_data = st.session_state.get("manual_weaving_result")
    try:
        project_json = create_manual_weaving_project_json(
            preset_id,
            unit_system,
            displayed_inputs,
            result=result_data if current else None,
            audit_record=audit if current else None,
            locale=_ui_locale(),
        )
    except ProjectFileError:
        st.caption(_weaving_text("project_save_unavailable"))
        return
    st.download_button(
        _weaving_text("save_project"),
        project_json,
        file_name="hcm-7-0-weaving-project.json",
        mime="application/json",
        width="stretch",
    )


def render_manual_weaving_calculator() -> None:
    """Render the compact, public-facade-only HCM 7.0 weaving worksheet."""

    pending = st.session_state.pop("manual_weaving_pending_project", None)
    if pending is not None:
        _restore_manual_weaving_project(pending)
    load_message = st.session_state.pop("manual_weaving_project_load_message", None)
    if load_message:
        st.success(load_message)
    render_page_header(
        _weaving_text("title"),
        _weaving_text("subtitle"),
        _weaving_text("method_caption"),
    )
    status_placeholder = st.empty()
    input_column, result_column = render_calculator_shell()
    with input_column:
        render_project_load_section(
            _render_manual_weaving_load_controls,
            label=_weaving_text("project_load"),
        )
        render_section_label(_weaving_text("starting_values"))
        render_starting_values_section()
        unit_value = st.segmented_control(
            _weaving_text("unit_system"),
            ("metric", "imperial"),
            default=_weaving_unit_value(st.session_state.get("manual_weaving_unit_label", "metric")),
            format_func=lambda item: _weaving_text_for_locale(_ui_locale(), f"unit.{item}"),
            key="manual_weaving_unit_label",
        )
        unit_system = _weaving_unit_value(unit_value or "metric")
        preset_options = list(weaving_preset_options())
        preset_default = st.session_state.get("manual_weaving_preset_id", "blank_custom")
        if preset_default not in preset_options:
            preset_default = "blank_custom"
            st.session_state["manual_weaving_preset_id"] = preset_default
        preset_id = st.selectbox(
            _weaving_text("validation_preset"),
            preset_options,
            index=preset_options.index(preset_default),
            format_func=_weaving_preset_label,
            key="manual_weaving_preset_id",
        )

    context = (preset_id, unit_system)
    if st.session_state.get("manual_weaving_preset_context") != context:
        clear_manual_weaving_state(st.session_state)
        st.session_state["manual_weaving_preset_context"] = context
    ui = st.session_state.get("manual_weaving_loaded_displayed") or weaving_preset_ui_inputs(preset_id, unit_system)
    metric = unit_system == "metric"
    length_unit, speed_unit, width_unit = ("m", "km/h", "m") if metric else ("ft", "mph", "ft")
    density_unit = "interchanges/km" if metric else "interchanges/mi"
    with input_column:
        with st.container():
            render_section_label(_weaving_text("configuration_geometry"))
            geometry = st.columns(2)
            configuration = geometry[0].segmented_control(
                _weaving_text("configuration"),
                ("one_sided", "two_sided"),
                default=ui["configuration"] if ui["configuration"] in {"one_sided", "two_sided"} else "one_sided",
                format_func=lambda value: _weaving_text(f"config.{value}"),
                key=f"manual_weaving_input_configuration_{preset_id}_{unit_system}",
            )
            configuration = str(configuration or "one_sided")
            if st.session_state.get("manual_weaving_active_configuration") not in {None, configuration}:
                st.session_state.pop("manual_weaving_result", None)
                st.session_state.pop("manual_weaving_audit", None)
                st.session_state.pop("manual_weaving_error", None)
            st.session_state["manual_weaving_active_configuration"] = configuration
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
            volume_ff = traffic[0].number_input(_weaving_text("volume_ff"), min_value=0.0, value=float(ui["volume_ff_veh_h"]))
            volume_fr = traffic[1].number_input(_weaving_text("volume_fr"), min_value=0.0, value=float(ui["volume_fr_veh_h"]))
            volume_rf = traffic[0].number_input(_weaving_text("volume_rf"), min_value=0.0, value=float(ui["volume_rf_veh_h"]))
            volume_rr = traffic[1].number_input(_weaving_text("volume_rr"), min_value=0.0, value=float(ui["volume_rr_veh_h"]))
            peak_hour_factor = traffic[0].number_input(_weaving_text("peak_hour_factor"), min_value=0.01, max_value=1.0, value=float(ui["peak_hour_factor"]))
            interchange_density = traffic[1].number_input(_weaving_text("interchange_density", unit=density_unit), min_value=0.0, value=float(ui["interchange_density"]))
            render_section_label(_weaving_text("ffs_heavy"))
            ffs = st.columns(2)
            ffs_source = ffs[0].segmented_control(
                _weaving_text("ffs_source"),
                ("measured", "estimated"),
                default=ui["ffs_source"] if ui["ffs_source"] in {"measured", "estimated"} else "measured",
                format_func=lambda value: _weaving_text(f"ffs.{value}"),
            )
            ffs_source = str(ffs_source or "measured")
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
            if configuration == "one_sided":
                option_fr = evidence[0].checkbox(_weaving_text("option_fr"), value=bool(ui["option_fr"]))
                option_rf = evidence[1].checkbox(_weaving_text("option_rf"), value=bool(ui["option_rf"]))
                option_rr = False
            else:
                option_fr = option_rf = False
                option_rr = evidence[0].checkbox(_weaving_text("option_rr"), value=bool(ui["option_rr"]))
            reachable_ff = evidence[1].text_input(_weaving_text("reachable_ff"), value=ui["reachable_ff"])
            reachable_fr = evidence[0].text_input(_weaving_text("reachable_fr"), value=ui["reachable_fr"])
            reachable_rf = evidence[1].text_input(_weaving_text("reachable_rf"), value=ui["reachable_rf"])
            reachable_rr = evidence[0].text_input(_weaving_text("reachable_rr"), value=ui["reachable_rr"])
            nwl_basis = evidence[1].text_input(_weaving_text("nwl_basis"), value=ui["nwl_basis"])
            lane_change_basis = evidence[0].text_input(_weaving_text("lane_change_basis"), value=ui["lane_change_basis"])
            has_previous_result = st.session_state.get("manual_weaving_result") is not None
            run_weaving = st.button(
                _weaving_text("recalculate" if has_previous_result else "run"),
                type="primary",
                width="stretch",
            )
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
            conversion_error = None
        except (HCMCalcError, ValueError) as exc:
            submitted_inputs = {}
            conversion_error = exc
        workflow_inputs = {"preset_id": preset_id, "normalized_engine_inputs": submitted_inputs}
        current = render_calculation_status("manual_weaving", workflow_inputs, status_placeholder)
        if run_weaving:
            st.session_state.pop("manual_weaving_error", None)
            st.session_state.pop("manual_weaving_result", None)
            if conversion_error is not None:
                st.session_state["manual_weaving_error"] = {
                    "message": str(conversion_error),
                    "state": ResultPresentationState.INVALID_INPUT,
                }
                st.session_state["manual_weaving_audit"] = build_manual_weaving_audit_record(
                    preset_id,
                    {},
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    error=conversion_error,
                )
            else:
                try:
                    result = run_manual_weaving(submitted_inputs)
                    st.session_state["manual_weaving_result"] = result_to_dict(result)
                    st.session_state["manual_weaving_audit"] = build_manual_weaving_audit_record(
                        preset_id,
                        submitted_inputs,
                        unit_system=unit_system,
                        displayed_inputs=displayed_inputs,
                        result=result,
                    )
                    mark_calculated(st.session_state, "manual_weaving", workflow_inputs)
                    current = render_calculation_status("manual_weaving", workflow_inputs, status_placeholder)
                except UnsupportedScopeError as exc:
                    st.session_state["manual_weaving_error"] = {
                        "message": str(exc),
                        "state": ResultPresentationState.UNSUPPORTED_SCOPE,
                    }
                    st.session_state["manual_weaving_audit"] = build_manual_weaving_audit_record(
                        preset_id,
                        submitted_inputs,
                        unit_system=unit_system,
                        displayed_inputs=displayed_inputs,
                        error=exc,
                    )
                except HCMCalcError as exc:
                    st.session_state["manual_weaving_error"] = {
                        "message": str(exc),
                        "state": ResultPresentationState.INVALID_INPUT,
                    }
                    st.session_state["manual_weaving_audit"] = build_manual_weaving_audit_record(
                        preset_id,
                        submitted_inputs,
                        unit_system=unit_system,
                        displayed_inputs=displayed_inputs,
                        error=exc,
                    )
    with result_column:
        with st.expander(_weaving_text("validation"), expanded=False):
            st.markdown(f"**{_weaving_text('validation_basis_heading')}**")
            st.caption(_weaving_text("validation_basis"))
            st.markdown(f"**{_weaving_text('supported_scope_heading')}**")
            st.caption(_weaving_text("supported_scope"))
            st.markdown(f"**{_weaving_text('not_supported_heading')}**")
            st.caption(_weaving_text("not_supported"))
        render_section_label(_weaving_text("results"))
        error = st.session_state.get("manual_weaving_error")
        result_data = st.session_state.get("manual_weaving_result")
        audit = st.session_state.get("manual_weaving_audit")
        if error:
            error_state = _weaving_error_state(error)
            message_key = {
                ResultPresentationState.UNSUPPORTED_SCOPE: "unsupported",
                ResultPresentationState.INVALID_INPUT: "invalid",
                ResultPresentationState.INTERNAL_ERROR: "internal_error",
            }[error_state]
            render_result_state_panel(error_state, _weaving_text(message_key))
            detail = error.get("message") if isinstance(error, dict) else str(error)
            st.caption(_weaving_text("error_details", error=detail))
            with st.expander(_weaving_text("audit"), expanded=False):
                st.json(audit)
            render_project_output_section(
                _weaving_text("project_caption"),
                lambda: _weaving_project_download(
                    preset_id=preset_id,
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    current=False,
                ),
                label=_weaving_text("project_output"),
            )
        elif not result_data:
            render_result_state_panel(
                ResultPresentationState.PRERUN,
                _weaving_text("prerun"),
            )
            render_project_output_section(
                _weaving_text("project_caption"),
                lambda: _weaving_project_download(
                    preset_id=preset_id,
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    current=False,
                ),
                label=_weaving_text("project_output"),
            )
        else:
            outputs = result_data["outputs"]
            presentation_state = resolve_result_presentation_state(
                freshness=workflow_status(st.session_state, "manual_weaving", workflow_inputs),
                has_result=True,
                warnings=result_data.get("warnings", ()),
                capacity_failure=outputs.get("capacity_status") == "demand_exceeds_capacity",
                stopping_or_handoff=_weaving_stopping_or_handoff(outputs),
            )
            current_result = presentation_state != ResultPresentationState.STALE_RESULT
            if not current_result:
                render_result_state_panel(presentation_state, _weaving_text("stale"))
                with st.expander(_weaving_text("audit"), expanded=False):
                    st.json(audit)
                render_project_output_section(
                    _weaving_text("project_caption"),
                    lambda: _weaving_project_download(
                        preset_id=preset_id,
                        unit_system=unit_system,
                        displayed_inputs=displayed_inputs,
                        current=False,
                    ),
                    label=_weaving_text("project_output"),
                )
                st.caption(_weaving_text("export_stale"))
            else:
                result_unit_system = (
                    str(audit.get("unit_system", unit_system))
                    if isinstance(audit, dict)
                    else unit_system
                )
                display = weaving_display_outputs(outputs, result_unit_system)
                los = outputs.get("level_of_service")
                if los:
                    primary_label = translate("result.level_of_service", _ui_locale())
                    primary_value = str(los)
                    primary_kind = "los"
                    supporting_label = _weaving_text("density")
                    supporting_value = _weaving_result_metric(display["density"])
                else:
                    primary_label = _weaving_text("operational_status")
                    primary_value = _weaving_text("not_assigned")
                    primary_kind = "metric"
                    supporting_label = supporting_value = None
                render_result_summary_panel(
                    primary_label=primary_label,
                    primary_value=primary_value,
                    primary_kind=primary_kind,
                    hero_supporting_label=supporting_label,
                    hero_supporting_value=supporting_value,
                    secondary_metrics=[
                        {
                            "label": _weaving_text("mean_speed"),
                            "value": _weaving_result_metric(display["mean_speed"]),
                        },
                        {
                            "label": _weaving_text("weaving_speed"),
                            "value": _weaving_result_metric(display["weaving_speed"]),
                        },
                        {
                            "label": _weaving_text("nonweaving_speed"),
                            "value": _weaving_result_metric(display["nonweaving_speed"]),
                        },
                        {
                            "label": _weaving_text("governing_capacity"),
                            "value": _weaving_result_metric(display["capacity"], decimals=0),
                        },
                        {
                            "label": _weaving_text("demand_flow"),
                            "value": f"{display['demand']['value']:.0f} {display['demand']['unit']}",
                        },
                        {
                            "label": _weaving_text("vc"),
                            "value": _weaving_text("not_evaluated")
                            if outputs.get("demand_capacity_ratio") is None
                            else f"{outputs['demand_capacity_ratio']:.3f}",
                        },
                    ],
                )
                if presentation_state == ResultPresentationState.HCM_STOPPING_OR_HANDOFF:
                    render_result_state_panel(presentation_state, _weaving_text("handoff_warning"))
                    st.metric(
                        _weaving_text("entered_lmax"),
                        f"{outputs['input_summary']['segment_length_ft']:.0f} ft / {outputs['maximum_weaving_length_ft']:.0f} ft",
                    )
                elif presentation_state == ResultPresentationState.CAPACITY_FAILURE:
                    render_result_state_panel(presentation_state, _weaving_text("capacity_failure"))
                elif presentation_state == ResultPresentationState.VALID_CURRENT_RESULT_WITH_WARNING:
                    render_result_state_panel(presentation_state, _weaving_text("warning"))
                with st.expander(_weaving_text("calculation_details"), expanded=False):
                    st.json(outputs)
                    render_list(
                        translate("common.assumptions", _ui_locale()),
                        result_data["assumptions"],
                        translate("common.no_assumptions", _ui_locale()),
                    )
                    render_list(
                        translate("common.warnings", _ui_locale()),
                        result_data["warnings"],
                        translate("common.no_warnings", _ui_locale()),
                    )
                    render_list(
                        _weaving_text("unsupported_scope_notes"),
                        outputs["unsupported_scope_notes"],
                        _weaving_text("no_unsupported_scope_notes"),
                    )
                with st.expander(_weaving_text("audit"), expanded=False):
                    st.json(audit)
                    st.dataframe(result_data["intermediate_values"], hide_index=True, width="stretch")
                render_project_output_section(
                    _weaving_text("project_caption"),
                    lambda: _weaving_project_download(
                        preset_id=preset_id,
                        unit_system=unit_system,
                        displayed_inputs=displayed_inputs,
                        current=True,
                    ),
                    label=_weaving_text("project_output"),
                )
                render_export_report_section(
                    "manual_freeway_weaving_segment_v1",
                    result_data,
                    result_unit_system,
                    inputs=displayed_inputs,
                    audit_record=audit,
                    template_id=preset_id,
                    label=_weaving_text("export_report"),
                )


def _render_manual_weaving_load_controls() -> None:
    uploaded = st.file_uploader(_weaving_text("project_file"), type=["json"], key="manual_weaving_project_file_uploader")
    if uploaded is not None and st.button(_weaving_text("load_project"), key="manual_weaving_project_load"):
        try:
            st.session_state["manual_weaving_pending_project"] = load_manual_weaving_project_json(uploaded.getvalue())
            st.rerun()
        except ProjectFileError as exc:
            st.error(_weaving_text("project_load_error", error=str(exc)))


def _restore_manual_weaving_project(project: dict[str, Any]) -> None:
    _restore_project_locale(project)
    unit_system = project["unit_system"]
    displayed = project["displayed_ui_inputs"]
    st.session_state["manual_weaving_loaded_displayed"] = displayed
    st.session_state["manual_weaving_unit_label"] = unit_system
    st.session_state["manual_weaving_preset_id"] = project.get("preset_id", "blank_custom")
    st.session_state["manual_weaving_preset_context"] = (project.get("preset_id", "blank_custom"), unit_system)
    st.session_state["manual_weaving_active_configuration"] = displayed.get("configuration")
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
        _freeway_text("title"),
        _freeway_text("subtitle"),
    )
    status_placeholder = st.empty()
    input_column, result_column = render_calculator_shell()
    preset_options = freeway_preset_options()
    with input_column:
        with st.expander(_freeway_text("project_load"), expanded=False):
            _render_manual_freeway_load_controls()
        render_section_label(_freeway_text("setup"))
        st.caption(_freeway_text("scope"))
        st.session_state.setdefault("manual_freeway_unit_label", "metric")
        unit_label = st.segmented_control(
            _freeway_text("unit_system"),
            ["metric", "imperial"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"freeway.unit.{value}", locale
            ),
            key="manual_freeway_unit_label",
        )
        st.caption(_freeway_text("unit_caption"))
        with st.expander(_freeway_text("starting_values"), expanded=False):
            st.caption(_freeway_text("starting_values_caption"))
            preset_id = st.selectbox(
                _freeway_text("defaults"),
                list(preset_options),
                format_func=lambda value, locale=_ui_locale(): translate(
                    f"freeway.preset.{value}", locale
                ),
                key=f"freeway_preset_id_{_ui_locale()}",
            )
            st.caption(_freeway_text("defaults_caption"))
    unit_system = _localized_option_to_value(
        unit_label, "freeway.unit", ("metric", "imperial")
    )
    if unit_system not in {"metric", "imperial"}:
        unit_system = "imperial" if "imper" in str(unit_label).lower() else "metric"
    preset_context = (preset_id, unit_system)
    if st.session_state.get("manual_freeway_preset_context") != preset_context:
        clear_manual_freeway_state(st.session_state)
        if "manual_freeway_preset_context" in st.session_state:
            st.session_state["manual_freeway_reset_message"] = _freeway_text("reset_message")
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
        render_section_label(_freeway_text("geometry"))
        roadway_columns = st.columns(2)
        number_of_lanes = roadway_columns[0].number_input(
            _freeway_text("number_of_lanes"),
            min_value=2,
            step=1,
            value=int(ui_inputs["number_of_lanes"]),
            key=f"manual_freeway_input_lanes_{preset_id}_{unit_system}",
        )
        segment_length = roadway_columns[1].number_input(
            _freeway_text("segment_length", unit=length_unit),
            min_value=0.001,
            value=float(ui_inputs["segment_length"]),
            key=f"manual_freeway_input_length_{preset_id}_{unit_system}",
        )

        render_section_label(_freeway_text("demand"))
        traffic_columns = st.columns(2)
        demand_volume_veh_h = traffic_columns[0].number_input(
            _freeway_text("demand_volume"),
            min_value=1.0,
            value=float(ui_inputs["demand_volume_veh_h"]),
            key=f"manual_freeway_input_demand_{preset_id}_{unit_system}",
        )
        peak_hour_factor = traffic_columns[1].number_input(
            _freeway_text("peak_hour_factor"),
            min_value=0.01,
            max_value=1.0,
            value=float(ui_inputs["peak_hour_factor"]),
            key=f"manual_freeway_input_phf_{preset_id}_{unit_system}",
        )

        render_section_label(_freeway_text("ffs"))
        ffs_source_key = f"manual_freeway_input_ffs_source_{preset_id}_{unit_system}"
        st.session_state.setdefault(ffs_source_key, str(ui_inputs.get("ffs_source", "estimated")))
        ffs_source = st.segmented_control(
            _freeway_text("ffs_source"),
            ["estimated", "measured"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"freeway.ffs_source.{value}", locale
            ),
            key=ffs_source_key,
            help=_freeway_text("ffs_source_help"),
        )
        ffs_source = _localized_option_to_value(
            ffs_source, "freeway.ffs_source", ("estimated", "measured")
        )
        ffs_columns = st.columns(2)
        if ffs_source == "measured":
            st.caption(_freeway_text("measured_ffs_help"))
            fallback_speed = (
                ui_inputs.get("base_free_flow_speed")
                or 65.0 * (MILES_TO_KILOMETERS if metric else 1.0)
            )
            free_flow_speed = ffs_columns[0].number_input(
                _freeway_text("measured_ffs", unit=speed_unit),
                min_value=1.0,
                value=float(ui_inputs.get("free_flow_speed") or fallback_speed),
                key=f"manual_freeway_input_free_flow_speed_{preset_id}_{unit_system}",
            )
            base_free_flow_speed = lane_width = right_side_lateral_clearance = total_ramp_density = None
        else:
            st.caption(_freeway_text("estimated_ffs_help"))
            free_flow_speed = None
            base_free_flow_speed = ffs_columns[0].number_input(
                _freeway_text("base_ffs", unit=speed_unit),
                min_value=1.0,
                value=float(ui_inputs.get("base_free_flow_speed") or 60.0),
                key=f"manual_freeway_input_base_ffs_{preset_id}_{unit_system}",
            )
            lane_width = ffs_columns[1].number_input(
                _freeway_text("lane_width", unit=width_unit),
                min_value=0.1,
                value=float(ui_inputs.get("lane_width") or (3.6 if metric else 12.0)),
                key=f"manual_freeway_input_lane_width_{preset_id}_{unit_system}",
            )
            right_side_lateral_clearance = ffs_columns[0].number_input(
                _freeway_text("right_clearance", unit=width_unit),
                min_value=0.0,
                value=float(ui_inputs.get("right_side_lateral_clearance") or 0.0),
                key=f"manual_freeway_input_right_clearance_{preset_id}_{unit_system}",
            )
            total_ramp_density = ffs_columns[1].number_input(
                _freeway_text("total_ramp_density", unit=ramp_density_unit),
                min_value=0.0,
                value=float(ui_inputs.get("total_ramp_density") or 0.0),
                key=f"manual_freeway_input_ramp_density_{preset_id}_{unit_system}",
                help=_freeway_text("total_ramp_density_help"),
            )

        render_section_label(_freeway_text("heavy_adjustments"))
        heavy_columns = st.columns(2)
        heavy_vehicle_percent = heavy_columns[0].number_input(
            _freeway_text("heavy_vehicles"),
            min_value=0.0,
            max_value=100.0,
            value=float(ui_inputs["heavy_vehicle_percent"]),
            key=f"manual_freeway_input_heavy_{preset_id}_{unit_system}",
        )
        pce_mode_key = f"manual_freeway_input_pce_mode_{preset_id}_{unit_system}"
        st.session_state.setdefault(pce_mode_key, str(ui_inputs.get("pce_mode", "internal")))
        pce_mode = heavy_columns[1].segmented_control(
            _freeway_text("pce_source"),
            ["internal", "external"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"freeway.pce.{value}", locale
            ),
            key=pce_mode_key,
            help=_freeway_text("pce_source_help"),
        )
        pce_mode = _localized_option_to_value(
            pce_mode, "freeway.pce", ("internal", "external")
        )
        passenger_car_equivalent = None
        passenger_car_equivalent_provenance = None
        if pce_mode == "internal":
            terrain_type = heavy_columns[0].selectbox(
                _freeway_text("terrain"),
                ["level", "rolling", "specific_grade"],
                index=["level", "rolling", "specific_grade"].index(
                    ui_inputs.get("terrain_type", "level")
                ),
                format_func=lambda value, locale=_ui_locale(): translate(
                    f"freeway.terrain.{value}", locale
                ),
                key=f"manual_freeway_input_terrain_{preset_id}_{unit_system}",
                help=_freeway_text("terrain_help"),
            )
            if terrain_type == "specific_grade":
                grade_percent = heavy_columns[1].number_input(
                    _freeway_text("grade"),
                    value=float(ui_inputs.get("grade_percent") or 0.0),
                    key=f"manual_freeway_input_grade_{preset_id}_{unit_system}",
                )
                mixes = [
                    "default_30_sut_70_tt",
                    "equal_50_sut_50_tt",
                    "majority_70_sut_30_tt",
                ]
                truck_mix = heavy_columns[0].selectbox(
                    _freeway_text("truck_mix"),
                    mixes,
                    index=mixes.index(ui_inputs.get("truck_mix", mixes[0])),
                    format_func=lambda value, locale=_ui_locale(): translate(
                        f"freeway.truck_mix.{value}", locale
                    ),
                    key=f"manual_freeway_input_truck_mix_{preset_id}_{unit_system}",
                )
            else:
                grade_percent = None
                truck_mix = "default_30_sut_70_tt"
        else:
            terrain_type = "level"
            grade_percent = None
            truck_mix = "default_30_sut_70_tt"
            passenger_car_equivalent = heavy_columns[0].number_input(
                _freeway_text("external_pce"),
                min_value=0.01,
                value=float(ui_inputs.get("passenger_car_equivalent") or 1.0),
                key=f"manual_freeway_input_external_pce_{preset_id}_{unit_system}",
            )
            passenger_car_equivalent_provenance = heavy_columns[1].text_input(
                _freeway_text("external_pce_provenance"),
                value=ui_inputs.get("passenger_car_equivalent_provenance") or "",
                key=f"manual_freeway_input_external_pce_provenance_{preset_id}_{unit_system}",
                help=_freeway_text("external_pce_help"),
            )

        with st.expander(_freeway_text("advanced"), expanded=False):
            advanced_columns = st.columns(2)
            driver_options = [
                "regular",
                "mostly_familiar",
                "balanced",
                "mostly_unfamiliar",
                "overwhelmingly_unfamiliar",
            ]
            driver_population_category = advanced_columns[0].selectbox(
                _freeway_text("driver_population"),
                driver_options,
                index=driver_options.index(ui_inputs.get("driver_population_category", "regular")),
                format_func=lambda value, locale=_ui_locale(): translate(
                    f"freeway.driver_population.{value}", locale
                ),
                key=f"manual_freeway_input_driver_population_{preset_id}_{unit_system}",
                help=_freeway_text("driver_population_help"),
            )
            if driver_population_category == "regular":
                speed_adjustment_factor = advanced_columns[0].number_input(
                    _freeway_text("saf"),
                    min_value=0.01,
                    max_value=1.0,
                    value=float(ui_inputs["speed_adjustment_factor"]),
                    key=f"manual_freeway_input_saf_{preset_id}_{unit_system}",
                    help=_freeway_text("saf_help"),
                )
                capacity_adjustment_factor = advanced_columns[1].number_input(
                    _freeway_text("caf"),
                    min_value=0.01,
                    max_value=1.0,
                    value=float(ui_inputs["capacity_adjustment_factor"]),
                    key=f"manual_freeway_input_caf_{preset_id}_{unit_system}",
                    help=_freeway_text("caf_help"),
                )
                factor_sources = ["hcm_base_conditions", "project_local_calibration"]
                speed_adjustment_factor_source = advanced_columns[0].selectbox(
                    _freeway_text("saf_source"),
                    factor_sources,
                    index=factor_sources.index(
                        ui_inputs.get("speed_adjustment_factor_source", "hcm_base_conditions")
                    ),
                    format_func=lambda value, locale=_ui_locale(): translate(
                        f"freeway.factor_source.{value}", locale
                    ),
                    key=f"manual_freeway_input_saf_source_{preset_id}_{unit_system}",
                )
                capacity_adjustment_factor_source = advanced_columns[1].selectbox(
                    _freeway_text("caf_source"),
                    factor_sources,
                    index=factor_sources.index(
                        ui_inputs.get("capacity_adjustment_factor_source", "hcm_base_conditions")
                    ),
                    format_func=lambda value, locale=_ui_locale(): translate(
                        f"freeway.factor_source.{value}", locale
                    ),
                    key=f"manual_freeway_input_caf_source_{preset_id}_{unit_system}",
                )
            else:
                speed_adjustment_factor = ui_inputs["speed_adjustment_factor"]
                capacity_adjustment_factor = ui_inputs["capacity_adjustment_factor"]
                speed_adjustment_factor_source = "chapter_26_driver_population"
                capacity_adjustment_factor_source = "chapter_26_driver_population"
                advanced_columns[1].caption(_freeway_text("driver_population_factor_caption"))

        run_freeway = st.button(
            _freeway_text("calculate"), type="primary", width="stretch"
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
        conversion_error: Exception | None = None
        try:
            submitted_inputs = freeway_ui_inputs_to_engine(
                displayed_inputs, inputs, unit_system
            )
        except (HCMCalcError, ValueError) as exc:
            conversion_error = exc
            submitted_inputs = {}
        freeway_workflow_inputs = {
            "method_identifier": "hcm7_basic_freeway_segment",
            "input_contract": "phase_10_product_integration",
            "effective_engine_inputs": submitted_inputs,
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
                st.caption(_freeway_text("project_save_unavailable"))
                return
            st.download_button(
                _freeway_text("save_project"),
                data=project_json,
                file_name=f"{preset_id}-manual-basic-freeway-project.json",
                mime="application/json",
                width="stretch",
            )

    if run_freeway:
        st.session_state.pop("manual_freeway_result", None)
        st.session_state.pop("manual_freeway_error", None)
        if conversion_error is not None:
            st.session_state["manual_freeway_error"] = {
                "message": str(conversion_error),
                "state": ResultPresentationState.INVALID_INPUT,
            }
            st.session_state["manual_freeway_audit"] = (
                build_manual_freeway_audit_record(
                    preset_id,
                    {},
                    unit_system=unit_system,
                    displayed_inputs=displayed_inputs,
                    error=conversion_error,
                )
            )
        else:
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
            except UnsupportedScopeError as exc:
                st.session_state["manual_freeway_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.UNSUPPORTED_SCOPE,
                }
                st.session_state["manual_freeway_audit"] = (
                    build_manual_freeway_audit_record(
                        preset_id,
                        submitted_inputs,
                        unit_system=unit_system,
                        displayed_inputs=displayed_inputs,
                        error=exc,
                    )
                )
            except HCMCalcError as exc:
                st.session_state["manual_freeway_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.INVALID_INPUT,
                }
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
        with st.expander(_freeway_text("validation"), expanded=False):
            st.markdown(f"**{_freeway_text('validation_basis_heading')}**")
            st.caption(_freeway_text("validation_basis"))
            st.markdown(f"**{_freeway_text('supported_scope_heading')}**")
            st.caption(_freeway_text("supported_scope"))
            st.markdown(f"**{_freeway_text('not_supported_heading')}**")
            st.caption(_freeway_text("not_supported"))
        render_section_label(_freeway_text("results"))
        error = st.session_state.get("manual_freeway_error")
        audit = st.session_state.get("manual_freeway_audit")
        if error is not None:
            error_state = (
                error.get("state")
                if isinstance(error, dict)
                else ResultPresentationState.INTERNAL_ERROR
            )
            if error_state not in {
                ResultPresentationState.UNSUPPORTED_SCOPE,
                ResultPresentationState.INVALID_INPUT,
                ResultPresentationState.INTERNAL_ERROR,
            }:
                error_state = ResultPresentationState.INTERNAL_ERROR
            message_key = {
                ResultPresentationState.UNSUPPORTED_SCOPE: "unsupported",
                ResultPresentationState.INVALID_INPUT: "invalid",
                ResultPresentationState.INTERNAL_ERROR: "internal_error",
            }[error_state]
            render_result_state_panel(error_state, _freeway_text(message_key))
            detail = error.get("message") if isinstance(error, dict) else str(error)
            st.caption(_freeway_text("error_details", error=detail))
            with st.expander(_freeway_text("audit"), expanded=False):
                st.json(audit)
            render_project_output_section(
                _freeway_text("project_caption"),
                render_freeway_project_download,
                label=_freeway_text("project_output"),
            )
            return
        result_data = st.session_state.get("manual_freeway_result")
        if result_data is None:
            render_result_state_panel(
                ResultPresentationState.PRERUN,
                _freeway_text("prerun"),
            )
            render_project_output_section(
                _freeway_text("project_caption"),
                render_freeway_project_download,
                label=_freeway_text("project_output"),
            )
            return

        presentation_state = resolve_result_presentation_state(
            freshness=workflow_status(
                st.session_state, "manual_freeway", freeway_workflow_inputs
            ),
            has_result=True,
            warnings=result_data.get("warnings", ()),
            capacity_failure=result_data["outputs"].get("capacity_check")
            == "demand_exceeds_capacity",
        )
        if presentation_state == ResultPresentationState.STALE_RESULT:
            render_result_state_panel(presentation_state, _freeway_text("stale"))
            render_project_output_section(
                _freeway_text("project_caption"),
                render_freeway_project_download,
                label=_freeway_text("project_output"),
            )
            st.caption(_freeway_text("export_stale"))
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
                else _freeway_text("not_predicted")
            )
        render_result_summary_panel(
            primary_label=translate("result.level_of_service", _ui_locale()),
            primary_value=str(outputs["level_of_service"]),
            primary_kind="los",
            hero_supporting_label=translate("result.density", _ui_locale()),
            hero_supporting_value=predicted(display["density"]),
            secondary_metrics=[
                {
                    "label": _freeway_text("speed_used_for_density"),
                    "value": predicted(display["speed_used_for_density"]),
                },
                {
                    "label": translate("result.demand_flow_rate", _ui_locale()),
                    "value": (
                        f"{display['demand_flow_rate']['value']:.0f} "
                        f"{display['demand_flow_rate']['unit']}"
                    ),
                },
                {
                    "label": translate("result.capacity", _ui_locale()),
                    "value": (
                        f"{display['capacity']['value']:.0f} "
                        f"{display['capacity']['unit']}"
                    ),
                },
                {
                    "label": _freeway_text("capacity_check"),
                    "value": _freeway_text(
                        f"capacity_status.{outputs['capacity_check']}"
                    ),
                },
                {"label": _freeway_text("ffs_source_label"), "value": outputs["ffs_source"]},
                {
                    "label": _freeway_text("adjusted_ffs"),
                    "value": (
                        f"{display['adjusted_free_flow_speed']['value']:.1f} "
                        f"{display['adjusted_free_flow_speed']['unit']}"
                    ),
                },
                {
                    "label": _freeway_text("base_ffs_result"),
                    "value": (
                        f"{display['base_free_flow_speed']['value']:.1f} "
                        f"{display['base_free_flow_speed']['unit']}"
                    ),
                },
                {
                    "label": _freeway_text("heavy_vehicle_factor"),
                    "value": f"{outputs['heavy_vehicle_adjustment_factor']:.3f}",
                },
                {
                    "label": _freeway_text("demand_capacity"),
                    "value": f"{outputs['demand_capacity_ratio']:.3f}",
                },
                {
                    "label": _freeway_text("pce"),
                    "value": f"{outputs['passenger_car_equivalent']:.2f} ({outputs['pce_source']})",
                },
            ],
        )
        if presentation_state == ResultPresentationState.CAPACITY_FAILURE:
            render_result_state_panel(
                presentation_state, _freeway_text("capacity_failure")
            )
        elif presentation_state == ResultPresentationState.VALID_CURRENT_RESULT_WITH_WARNING:
            render_result_state_panel(presentation_state, _freeway_text("warning"))

        with st.expander(_freeway_text("calculation_details"), expanded=False):
            st.markdown(f"**{_freeway_text('ffs_audit')}**")
            st.json({key: outputs[key] for key in (
                "ffs_source", "base_free_flow_speed_mph", "lane_width_adjustment_mph",
                "right_lateral_clearance_adjustment_mph", "total_ramp_density_adjustment_mph",
                "free_flow_speed_before_saf_mph", "speed_adjustment_factor",
                "speed_adjustment_factor_source", "adjusted_free_flow_speed_mph",
            )})
            st.markdown(f"**{_freeway_text('pce_audit')}**")
            st.json({key: outputs[key] for key in (
                "passenger_car_equivalent", "pce_source", "pce_lookup_path",
                "terrain_grade_classification", "effective_grade_percent", "segment_length_mi",
                "heavy_vehicle_adjustment_factor", "driver_population_category",
                "driver_population_factor", "capacity_pc_h_ln", "capacity_adjustment_factor",
                "capacity_adjustment_factor_source", "adjusted_capacity_pc_h_ln",
            )})
            render_list(
                translate("common.assumptions", _ui_locale()),
                result_data["assumptions"],
                translate("common.no_assumptions", _ui_locale()),
            )
            render_list(
                translate("common.warnings", _ui_locale()),
                result_data["warnings"],
                translate("common.no_warnings", _ui_locale()),
            )
            render_list(
                _freeway_text("unsupported_scope_notes"),
                outputs["unsupported_scope_notes"],
                _freeway_text("no_unsupported_scope_notes"),
            )
        with st.expander(_freeway_text("audit"), expanded=False):
            st.json(audit)
            st.dataframe(
                [
                    {**value, "value": str(value["value"])}
                    for value in result_data["intermediate_values"]
                ],
                hide_index=True,
                width="stretch",
            )
        with st.expander(_freeway_text("full_json")):
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
            _freeway_text("project_caption"),
            render_freeway_project_download,
            label=_freeway_text("project_output"),
        )
        if freeway_is_current:
            render_export_report_section(
                "manual_basic_freeway_v0", result_data, result_unit_system,
                inputs=(audit.get("displayed_inputs", displayed_inputs) if isinstance(audit, dict) else displayed_inputs),
                audit_record=audit, template_id=preset_id,
                label=_freeway_text("export_report"),
            )
        else:
            st.caption(_freeway_text("export_stale"))


def _render_manual_freeway_load_controls() -> None:
    """Render bounded Manual Basic Freeway project loading controls."""

    uploaded_project = st.file_uploader(
        _freeway_text("project_file"),
        type=["json"],
        key="manual_freeway_project_file_uploader",
    )
    if st.button(
        _freeway_text("load_project"),
        disabled=uploaded_project is None,
        width="stretch",
    ):
        try:
            project = load_manual_freeway_project_json(uploaded_project.getvalue())
        except ProjectFileError as exc:
            st.error(_freeway_text("project_load_error", error=str(exc)))
        else:
            saved_locale = project_presentation_locale(project)
            if saved_locale is not None:
                st.session_state["_pending_ui_locale"] = saved_locale
            st.session_state["manual_freeway_pending_project"] = project
            st.rerun()


def _restore_manual_freeway_project(project: dict[str, Any]) -> None:
    """Restore validated Manual Basic Freeway project data into worksheet state."""

    preset_id = project["preset_id"]
    unit_system = project["unit_system"]
    displayed = project["displayed_ui_inputs"]
    st.session_state["manual_freeway_unit_label"] = unit_system
    st.session_state["freeway_preset_id"] = preset_id
    st.session_state["freeway_preset_id_en"] = preset_id
    st.session_state["freeway_preset_id_th"] = preset_id
    st.session_state["manual_freeway_preset_context"] = (preset_id, unit_system)
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
    ] = displayed.get("ffs_source", "estimated")
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
                "method_identifier": "hcm7_basic_freeway_segment",
                "input_contract": "phase_10_product_integration",
                "effective_engine_inputs": project["normalized_engine_inputs"],
            },
        )
    st.session_state.pop("manual_freeway_error", None)
    _restore_project_locale(project)
    st.session_state["manual_freeway_project_load_message"] = project_load_message(project, _ui_locale())


def _render_manual_multilane_load_controls() -> None:
    """Render guarded Manual Multilane project loading controls."""

    uploaded_project = st.file_uploader(
        _multilane_text("project_file"),
        type=["json"],
        key="manual_multilane_project_file_uploader",
    )
    if st.button(
        _multilane_text("load_project"),
        disabled=uploaded_project is None,
        width="stretch",
    ):
        try:
            project = load_manual_multilane_project_json(uploaded_project.getvalue())
        except ProjectFileError as exc:
            st.error(_multilane_text("project_load_error", error=str(exc)))
        else:
            saved_locale = project_presentation_locale(project)
            if saved_locale is not None:
                st.session_state["_pending_ui_locale"] = saved_locale
            st.session_state["manual_multilane_pending_project"] = project
            st.rerun()


def _restore_manual_multilane_project(project: dict[str, Any]) -> None:
    """Restore validated Manual Multilane project data into worksheet state."""

    template_id = project["template_id"]
    unit_system = project["unit_system"]
    displayed = project["displayed_ui_inputs"]
    st.session_state["manual_multilane_unit_label"] = unit_system
    st.session_state["multilane_template_id"] = template_id
    st.session_state["multilane_template_id_en"] = template_id
    st.session_state["multilane_template_id_th"] = template_id
    st.session_state["manual_multilane_template_context"] = (template_id, unit_system)
    st.session_state[
        f"manual_multilane_input_ffs_source_{template_id}_{unit_system}"
    ] = displayed.get("ffs_source", "estimated")
    st.session_state[
        f"manual_multilane_input_pce_mode_{template_id}_{unit_system}"
    ] = "external" if displayed.get("pce_mode") == "external" else "internal"
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
                "method_identifier": "hcm7_multilane_los",
                "input_contract": "phase_8",
                "effective_engine_inputs": project["normalized_engine_inputs"],
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
        _facility_text("title"),
        _facility_text("subtitle"),
        _facility_text("scope"),
    )
    status_placeholder = st.empty()
    input_column, result_column = render_calculator_shell()
    template_options = facility_template_options()
    with input_column:
        render_project_load_section(
            _render_manual_facility_load_controls,
            label=_facility_text("project_load"),
        )
        render_section_label(_facility_text("starting_values"))
        template_id = st.selectbox(
            _facility_text("template"),
            list(template_options),
            format_func=lambda value, locale=_ui_locale(): translate(
                f"facility.template.{value}", locale
            ),
            key="facility_template_id",
            help=_facility_text("template_caption"),
        )
        st.caption(_facility_text("template_caption"))
        render_section_label(_facility_text("setup"))
        st.session_state.setdefault("facility_unit_label", "metric")
        canonical_facility_unit = _localized_option_to_value(
            st.session_state.get("facility_unit_label"),
            "facility.unit",
            ("metric", "imperial"),
        )
        if canonical_facility_unit not in {"metric", "imperial"}:
            canonical_facility_unit = "metric"
        st.session_state["facility_unit_label"] = canonical_facility_unit
        unit_label = st.segmented_control(
            _facility_text("unit_system"),
            ["metric", "imperial"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"facility.unit.{value}", locale
            ),
            key="facility_unit_label",
        )
        unit_system = _localized_option_to_value(
            unit_label, "facility.unit", ("metric", "imperial")
        )
        if unit_system not in {"metric", "imperial"}:
            unit_system = "metric"
            st.session_state["facility_unit_label"] = unit_system
        st.caption(_facility_text("setup_caption"))
        selection_context = (template_id, unit_system)
        if st.session_state.get("manual_facility_selection_context") != selection_context:
            clear_manual_facility_result_state(st.session_state)
            st.session_state.pop("manual_facility_result", None)
            st.session_state.pop("manual_facility_audit", None)
            st.session_state.pop("manual_facility_result_rows", None)
            st.session_state["manual_facility_selection_context"] = selection_context
            st.session_state["manual_facility_editor_version"] = (
                st.session_state.get("manual_facility_editor_version", 0) + 1
            )

        try:
            template = load_facility_template(template_id, unit_system)
        except HCMCalcError as exc:
            st.error(str(exc))
            return

        render_section_label(_facility_text("segment_table"))
        st.caption(_facility_text("segment_table_caption"))
        editor_version = st.session_state.get("manual_facility_editor_version", 0)
        editor_seed = st.session_state.pop(
            "manual_facility_segment_rows_seed", template["segments"]
        )
        length_unit = "km" if unit_system == "metric" else "mi"
        speed_unit = "km/h" if unit_system == "metric" else "mph"
        width_unit = "m" if unit_system == "metric" else "ft"
        access_unit = "points/km" if unit_system == "metric" else "points/mi"
        edited_rows = st.data_editor(
            editor_seed,
            key=f"facility_segment_editor_{template_id}_{unit_system}_{editor_version}",
            hide_index=True,
            num_rows="dynamic",
            width="stretch",
            column_order=[
                "segment_id",
                "segment_name",
                "segment_type",
                "passing_lane_role",
                "segment_length",
                "posted_speed",
                "analysis_direction_volume_veh_h",
                "opposing_direction_volume_veh_h",
                "peak_hour_factor",
                "heavy_vehicle_percent",
                "terrain_type",
                "grade_percent",
                "horizontal_alignment",
                "lane_width",
                "shoulder_width",
                "access_point_density",
            ],
            column_config={
                "segment_id": st.column_config.NumberColumn(
                    _facility_text("col.segment_id"), min_value=1, required=True
                ),
                "segment_name": st.column_config.TextColumn(
                    _facility_text("col.segment_name")
                ),
                "segment_type": st.column_config.SelectboxColumn(
                    _facility_text("col.segment_type"),
                    options=["passing_constrained", "passing_zone", "passing_lane"],
                    required=True,
                ),
                "passing_lane_role": st.column_config.SelectboxColumn(
                    _facility_text("col.passing_lane_role"),
                    options=["none", "passing_lane", "downstream_affected"],
                    required=True,
                ),
                "segment_length": st.column_config.NumberColumn(
                    _facility_text("col.segment_length", unit=length_unit),
                    min_value=0.01,
                    required=True,
                ),
                "posted_speed": st.column_config.NumberColumn(
                    _facility_text("col.posted_speed", unit=speed_unit),
                    min_value=1.0,
                    required=True,
                ),
                "analysis_direction_volume_veh_h": st.column_config.NumberColumn(
                    _facility_text("col.analysis_volume"), min_value=0.0, required=True
                ),
                "opposing_direction_volume_veh_h": st.column_config.NumberColumn(
                    _facility_text("col.opposing_volume"), min_value=0.0
                ),
                "peak_hour_factor": st.column_config.NumberColumn(
                    _facility_text("col.peak_hour_factor"),
                    min_value=0.01,
                    max_value=1.0,
                    required=True,
                ),
                "heavy_vehicle_percent": st.column_config.NumberColumn(
                    _facility_text("col.heavy_vehicles"),
                    min_value=0.0,
                    max_value=100.0,
                    required=True,
                ),
                "terrain_type": st.column_config.SelectboxColumn(
                    _facility_text("col.terrain"),
                    options=["level", "mountainous"],
                ),
                "grade_percent": st.column_config.NumberColumn(_facility_text("col.grade")),
                "horizontal_alignment": st.column_config.SelectboxColumn(
                    _facility_text("col.alignment"),
                    options=["straight", "horizontal_curves"],
                    required=True,
                ),
                "lane_width": st.column_config.NumberColumn(
                    _facility_text("col.lane_width", unit=width_unit),
                    min_value=0.0,
                    required=True,
                ),
                "shoulder_width": st.column_config.NumberColumn(
                    _facility_text("col.shoulder_width", unit=width_unit),
                    min_value=0.0,
                    required=True,
                ),
                "access_point_density": st.column_config.NumberColumn(
                    _facility_text("col.access_density", unit=access_unit),
                    min_value=0.0,
                    required=True,
                ),
                "passing_lane": None,
                "downstream_affected": None,
                "horizontal_alignment_subsegments": None,
            },
        )
        canonical_edited_rows = canonicalize_manual_facility_rows(edited_rows)
        render_section_label(_facility_text("table_guidance"))
        validation_summary = validate_manual_facility_table(edited_rows)
        validation_message = _facility_text(f"validation.{validation_summary['status']}")
        if validation_summary["blocking"]:
            st.warning(validation_message)
        else:
            st.success(validation_message)
        for message in validation_summary["messages"][:5]:
            st.caption(_localize_facility_validation_message(message))
        st.caption(_facility_text("required_note"))
        st.caption(_facility_text("optional_note"))
        st.caption(_facility_text("inactive_note"))
        calculate_column, scope_column = st.columns([1, 2])
        action_label = (
            _facility_text("recalculate")
            if st.session_state.get("manual_facility_result") is not None
            else _facility_text("calculate")
        )
        calculate = calculate_column.button(
            action_label,
            type="primary",
            width="stretch",
            key="facility_calculate",
        )
        scope_column.caption(_facility_text("calculate_caption"))
        facility_workflow_inputs = {
            "template_id": template_id,
            "unit_system": unit_system,
            "segment_rows": canonical_edited_rows,
        }
        facility_is_current = render_calculation_status(
            "manual_facility", facility_workflow_inputs, status_placeholder
        )
    if calculate:
        clear_manual_facility_result_state(st.session_state)
        try:
            result = run_manual_facility(template_id, canonical_edited_rows, unit_system)
            st.session_state["manual_facility_result"] = result_to_dict(result)
            st.session_state["manual_facility_result_context"] = (
                template_id,
                unit_system,
            )
            st.session_state["manual_facility_result_rows"] = facility_segment_result_rows(
                result, canonical_edited_rows
            )
            st.session_state["manual_facility_audit"] = (
                build_manual_facility_audit_record(
                    template_id, canonical_edited_rows, unit_system, result=result
                )
            )
            mark_calculated(
                st.session_state, "manual_facility", facility_workflow_inputs
            )
            st.session_state.pop("manual_facility_error", None)
            st.session_state.pop("manual_facility_error_state", None)
            facility_is_current = render_calculation_status(
                "manual_facility", facility_workflow_inputs, status_placeholder
            )
        except HCMCalcError as exc:
            st.session_state["manual_facility_error"] = str(exc)
            st.session_state["manual_facility_error_state"] = (
                "unsupported"
                if isinstance(exc, (MethodNotImplementedError, UnsupportedScopeError))
                or validation_summary.get("status") == "unsupported_scope"
                else "invalid"
            )
            st.session_state["manual_facility_audit"] = (
                build_manual_facility_audit_record(
                    template_id, canonical_edited_rows, unit_system, error=exc
                )
            )
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            st.session_state["manual_facility_error"] = str(exc)
            st.session_state["manual_facility_error_state"] = "internal_error"
            st.session_state["manual_facility_audit"] = None

    with result_column:
        with st.expander(_facility_text("validation"), expanded=False):
            st.markdown(f"**{_facility_text('validation_basis_heading')}**")
            st.caption(_facility_text("validation_basis"))
            st.markdown(f"**{_facility_text('supported_scope_heading')}**")
            st.caption(_facility_text("supported_scope"))
            st.markdown(f"**{_facility_text('not_supported_heading')}**")
            st.caption(_facility_text("not_supported"))
        st.markdown(f"**{_facility_text('results')}**")
        render_manual_facility_result_panel(
            template_id, unit_system, canonical_edited_rows, template, facility_is_current
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
        error_state = st.session_state.get("manual_facility_error_state")
        state = {
            "unsupported": ResultPresentationState.UNSUPPORTED_SCOPE,
            "internal_error": ResultPresentationState.INTERNAL_ERROR,
        }.get(str(error_state), ResultPresentationState.INVALID_INPUT)
        message_key = {
            ResultPresentationState.UNSUPPORTED_SCOPE: "unsupported",
            ResultPresentationState.INTERNAL_ERROR: "internal_error",
        }.get(state, "invalid")
        render_result_state_panel(state, _facility_text(message_key))
        st.caption(_facility_text("error_details", error=error))
        with st.expander(_facility_text("audit"), expanded=False):
            st.json(audit)
        _render_manual_facility_project_file_controls(
            template_id,
            unit_system,
            edited_rows,
            translate(f"facility.template.{template_id}", _ui_locale()),
        )
        return

    result_data = st.session_state.get("manual_facility_result")
    if result_data is None:
        render_result_state_panel(
            ResultPresentationState.PRERUN, _facility_text("prerun")
        )
        _render_manual_facility_project_file_controls(
            template_id,
            unit_system,
            edited_rows,
            translate(f"facility.template.{template_id}", _ui_locale()),
        )
        return
    if not is_current:
        render_result_state_panel(
            ResultPresentationState.STALE_RESULT, _facility_text("stale")
        )
        _render_manual_facility_project_file_controls(
            template_id,
            unit_system,
            edited_rows,
            translate(f"facility.template.{template_id}", _ui_locale()),
        )
        st.caption(_facility_text("export_stale"))
        return

    outputs = result_data["outputs"]
    metric = unit_system == "metric"
    facility_follower_density = (
        f"{outputs['facility_follower_density_followers_mi_ln'] / 1.609344:.2f} fol/km/ln"
        if metric
        else f"{outputs['facility_follower_density_followers_mi_ln']:.1f} fol/mi/ln"
    )
    warnings = list(result_data.get("warnings", []))
    state = resolve_result_presentation_state(
        freshness=CALCULATED,
        has_result=True,
        warnings=warnings,
    )
    if state == ResultPresentationState.VALID_CURRENT_RESULT_WITH_WARNING:
        render_result_state_panel(state, _facility_text("warning"))
    st.subheader(_facility_text("summary"))
    display_rows = _facility_segment_display_rows(
        st.session_state.get("manual_facility_result_rows", []), unit_system
    )
    render_result_summary_panel(
        primary_label=_facility_text("facility_los"),
        primary_value=str(outputs["facility_level_of_service"]),
        primary_kind="los",
        hero_supporting_label=_facility_text("follower_density"),
        hero_supporting_value=facility_follower_density,
        secondary_metrics=[
            {
                "label": _facility_text("average_speed"),
                "value": (
                    f"{outputs['facility_average_speed_mph'] * 1.609344:.1f} km/h"
                    if metric
                    else f"{outputs['facility_average_speed_mph']:.1f} mph"
                ),
            },
            {
                "label": _facility_text("length"),
                "value": (
                    f"{outputs['facility_length_mi'] * 1.609344:.2f} km"
                    if metric
                    else f"{outputs['facility_length_mi']:.2f} mi"
                ),
            },
            {
                "label": _facility_text("segment_count"),
                "value": str(len(outputs["segments"])),
            },
            {
                "label": _facility_text("governing_segment"),
                "value": _facility_governing_segment(display_rows),
            },
        ],
    )

    st.subheader(_facility_text("segment_results"))
    st.dataframe(
        display_rows,
        hide_index=True,
        width="stretch",
        column_config={
            "segment_id": _facility_text("col.segment_id"),
            "segment_name": _facility_text("col.segment_name"),
            "segment_type": _facility_text("col.segment_type"),
            "segment_length": _facility_text(
                "col.segment_length", unit="km" if metric else "mi"
            ),
            "average_speed": _facility_text(
                "col.average_speed", unit="km/h" if metric else "mph"
            ),
            "percent_followers": _facility_text("col.percent_followers"),
            "follower_density": _facility_text(
                "col.follower_density", unit="fol/km/ln" if metric else "fol/mi/ln"
            ),
            "level_of_service": _facility_text("col.los"),
            "vertical_class": _facility_text("col.vertical_class"),
            "horizontal_curve_adjustment_applied": _facility_text("col.curve_adjustment"),
            "passing_lane": _facility_text("col.passing_lane"),
            "downstream_adjustment_applied": _facility_text("col.downstream_adjustment"),
            "key_warnings": _facility_text("col.key_warnings"),
        },
    )
    with st.expander(_facility_text("calculation_details"), expanded=False):
        render_list(
            translate("common.warnings", _ui_locale()),
            result_data["warnings"],
            translate("common.no_warnings", _ui_locale()),
        )
        render_list(
            translate("common.assumptions", _ui_locale()),
            result_data["assumptions"],
            translate("common.no_assumptions", _ui_locale()),
        )
        render_list(
            _facility_text("unsupported_notes"),
            template["unsupported_behavior_notes"],
            translate("common.no_warnings", _ui_locale()),
        )
    with st.expander(_facility_text("audit"), expanded=False):
        st.caption(_facility_text("audit_caption"))
        st.json(audit)
    full_result = {
        "calculation_type": "manual_two_lane_facility_v1",
        "template_id": template_id,
        "unit_system": unit_system,
        "engine_result": result_data,
        "audit_record": audit,
    }
    with st.expander(_facility_text("full_json")):
        st.caption(_facility_text("full_json_caption"))
        st.json(full_result)
        st.download_button(
            _facility_text("download_result_json"),
            data=json.dumps(full_result, indent=2),
            file_name=f"{template_id}-facility-result.json",
            mime="application/json",
            width="stretch",
        )
    _render_manual_facility_project_file_controls(
        template_id,
        unit_system,
        edited_rows,
        translate(f"facility.template.{template_id}", _ui_locale()),
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


def _facility_segment_display_rows(
    rows: list[dict[str, Any]], unit_system: str
) -> list[dict[str, Any]]:
    metric = unit_system == "metric"
    display_rows: list[dict[str, Any]] = []
    for row in rows:
        length = row.get("segment_length_mi")
        speed = row.get("average_speed_mph")
        density = row.get("follower_density_followers_mi_ln")
        display_rows.append(
            {
                "segment_id": row.get("segment_id"),
                "segment_name": row.get("segment_name"),
                "segment_type": translate(
                    f"facility.segment_type.{row.get('segment_type')}", _ui_locale()
                ),
                "segment_length": _format_facility_number(
                    float(length) * MILES_TO_KILOMETERS if metric and length is not None else length,
                    2,
                ),
                "average_speed": _format_facility_number(
                    float(speed) * MILES_TO_KILOMETERS if metric and speed is not None else speed,
                    1,
                ),
                "percent_followers": _format_facility_number(
                    row.get("percent_followers"), 1
                ),
                "follower_density": _format_facility_number(
                    float(density) / MILES_TO_KILOMETERS if metric and density is not None else density,
                    2 if metric else 1,
                ),
                "level_of_service": row.get("level_of_service")
                or _facility_text("not_predicted"),
                "vertical_class": row.get("vertical_class")
                if row.get("vertical_class") is not None
                else _facility_text("not_predicted"),
                "horizontal_curve_adjustment_applied": row.get(
                    "horizontal_curve_adjustment_applied"
                ),
                "passing_lane": row.get("passing_lane"),
                "downstream_adjustment_applied": row.get(
                    "downstream_adjustment_applied"
                ),
                "key_warnings": row.get("key_warnings")
                or _facility_text("not_predicted"),
            }
        )
    return display_rows


def _format_facility_number(value: Any, decimals: int) -> str:
    if value is None:
        return _facility_text("not_predicted")
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.{decimals}f}"


def _facility_governing_segment(rows: list[dict[str, Any]]) -> str:
    ordered = [
        row
        for row in rows
        if row.get("level_of_service") not in {None, _facility_text("not_predicted")}
    ]
    if not ordered:
        return _facility_text("not_predicted")
    governing = max(ordered, key=lambda row: str(row.get("level_of_service")))
    return str(governing.get("segment_id", _facility_text("not_predicted")))


def _localize_facility_validation_message(message: str) -> str:
    if _ui_locale() != "th":
        return message
    replacements = {
        "Facility requires at least one segment row.": "ต้องมีแถว segment อย่างน้อยหนึ่งแถว",
        "Segment row ": "แถว segment ",
        "Segment ": "segment ",
        ": missing required field(s):": ": ขาดฟิลด์จำเป็น:",
        " must be an integer.": " ต้องเป็นจำนวนเต็ม.",
        ": duplicate segment_id.": ": segment_id ซ้ำ.",
        ": segment_id must be positive.": ": segment_id ต้องมากกว่า 0.",
        ": unsupported segment_type ": ": segment_type ไม่รองรับ ",
        ": unsupported passing_lane_role ": ": passing_lane_role ไม่รองรับ ",
        ": unsupported horizontal_alignment ": ": horizontal_alignment ไม่รองรับ ",
        ": unsupported terrain_type ": ": terrain_type ไม่รองรับ ",
        ": Passing Lane segment requires passing_lane_role=passing_lane.": ": segment แบบ Passing Lane ต้องใช้ passing_lane_role=passing_lane.",
        ": only a Passing Lane segment may use passing_lane_role=passing_lane.": ": เฉพาะ segment แบบ Passing Lane เท่านั้นที่ใช้ passing_lane_role=passing_lane ได้.",
        ": downstream_affected requires an upstream Passing Lane segment.": ": downstream_affected ต้องมี Passing Lane segment อยู่ต้นน้ำ.",
        ": passing_zone requires opposing_direction_volume_veh_h.": ": passing_zone ต้องมี opposing_direction_volume_veh_h.",
        " must be numeric.": " ต้องเป็นตัวเลข.",
        " must be greater than 0.": " ต้องมากกว่า 0.",
        " must be 0 or greater.": " ต้องเป็น 0 หรือมากกว่า.",
        ": peak_hour_factor must be greater than 0 and at most 1.": ": peak_hour_factor ต้องมากกว่า 0 และไม่เกิน 1.",
    }
    localized = message
    for source, target in replacements.items():
        localized = localized.replace(source, target)
    return localized


def _render_manual_facility_project_file_controls(
    template_id: str,
    unit_system: str,
    segment_rows: list[dict[str, Any]],
    template_name: str,
) -> None:
    """Render guarded facility project save controls."""

    stored_audit = st.session_state.get("manual_facility_audit")
    segment_rows = canonicalize_manual_facility_rows(segment_rows)
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
        f"{_facility_text('project_caption')} {template_name}.",
        lambda: st.download_button(
            _facility_text("save_project"),
            data=project_json,
            file_name=f"{template_id}-manual-facility-project.json",
            mime="application/json",
            width="stretch",
        ),
        label=_facility_text("project_output"),
    )


def _render_manual_facility_load_controls() -> None:
    """Render guarded facility project loading controls."""

    uploaded_project = st.file_uploader(
        _facility_text("project_file"),
        type=["json"],
        key="manual_facility_project_file_uploader",
    )
    if st.button(
        _facility_text("load_project"),
        disabled=uploaded_project is None,
        width="stretch",
    ):
        try:
            project = load_manual_facility_project_json(uploaded_project.getvalue())
        except ProjectFileError as exc:
            st.error(_facility_text("project_load_error", error=str(exc)))
        else:
            st.session_state["manual_facility_pending_project"] = project
            st.rerun()


def _restore_manual_facility_project(project: dict[str, Any]) -> None:
    """Restore validated facility project data into worksheet session state."""

    unit_system = project["unit_system"]
    template_id = project["template_id"]
    st.session_state["facility_template_id"] = template_id
    st.session_state["facility_unit_label"] = unit_system
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
    """Render the localized manual Two-Lane Segment worksheet."""

    pending_project = st.session_state.pop("manual_pending_project", None)
    if pending_project is not None:
        _restore_manual_project(pending_project)
    load_message = st.session_state.pop("manual_project_load_message", None)
    if load_message is not None:
        st.success(load_message)
    generation_message = st.session_state.pop("manual_curve_generation_message", None)
    if generation_message is not None:
        st.success(generation_message)

    render_page_header(_two_lane_text("title"), _two_lane_text("subtitle"))
    status_placeholder = st.empty()
    worksheet_column, result_column = render_calculator_shell()

    with worksheet_column:
        render_project_load_section(
            _render_manual_project_load_controls,
            label=_two_lane_text("project_load"),
        )
        render_section_label(_two_lane_text("setup"))
        st.caption(_two_lane_text("scope"))
        st.session_state.setdefault("manual_unit_label", DEFAULT_UNIT_SYSTEM)
        unit_label = st.segmented_control(
            _two_lane_text("unit_system"),
            ["metric", "imperial"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"two_lane.unit.{value}", locale
            ),
            key="manual_unit_label",
        )
        unit_system = _localized_option_to_value(
            unit_label, "two_lane.unit", ("metric", "imperial")
        )
        if unit_system not in {"metric", "imperial"}:
            unit_system = DEFAULT_UNIT_SYSTEM
        st.caption(_two_lane_text("unit_caption"))
        defaults = manual_defaults(unit_system)
        metric = unit_system == "metric"
        length_unit = "km" if metric else "mi"
        speed_unit = "km/h" if metric else "mph"
        width_unit = "m" if metric else "ft"
        access_unit = "points/km" if metric else "points/mi"
        curve_length_unit = "m" if metric else "ft"

        with st.expander(_two_lane_text("starting_values"), expanded=False):
            st.caption(_two_lane_text("starting_values_caption"))
            st.caption(_two_lane_text("starting_values_note"))

        for name, default in defaults.items():
            st.session_state.setdefault(f"manual_{name}_{unit_system}", default)

        config_columns = st.columns(3)
        segment_type = config_columns[0].selectbox(
            _two_lane_text("segment_type"),
            list(SEGMENT_TYPE_LABELS),
            format_func=lambda value, locale=_ui_locale(): translate(
                f"two_lane.segment_type.{value}", locale
            ),
            key="manual_segment_type",
            help=_two_lane_text("segment_type_help"),
        )
        if segment_type == "passing_lane":
            st.session_state.setdefault(
                f"manual_heavy_vehicle_percent_{unit_system}", 8.0
            )
        terrain_type = config_columns[1].selectbox(
            _two_lane_text("terrain_type"),
            ["level", "mountainous"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"two_lane.terrain.{value}", locale
            ),
            key="manual_terrain_type",
        )
        horizontal_alignment = config_columns[2].selectbox(
            _two_lane_text("horizontal_alignment"),
            ["straight", "horizontal_curves"],
            format_func=lambda value, locale=_ui_locale(): translate(
                f"two_lane.alignment.{value}", locale
            ),
            help=_two_lane_text("horizontal_alignment_help"),
            key="manual_horizontal_alignment",
        )

        with st.container():
            render_section_label(_two_lane_text("geometry"))
            geometry_row_one = st.columns(3)
            segment_length = geometry_row_one[0].number_input(
                _two_lane_text("segment_length", unit=length_unit),
                key=f"manual_segment_length_{unit_system}",
            )
            posted_speed = geometry_row_one[1].number_input(
                _two_lane_text("posted_speed", unit=speed_unit),
                key=f"manual_posted_speed_{unit_system}",
                help=_two_lane_text("posted_speed_help"),
            )
            lane_width = geometry_row_one[2].number_input(
                _two_lane_text("lane_width", unit=width_unit),
                key=f"manual_lane_width_{unit_system}",
            )
            geometry_row_two = st.columns(3)
            shoulder_width = geometry_row_two[0].number_input(
                _two_lane_text("shoulder_width", unit=width_unit),
                key=f"manual_shoulder_width_{unit_system}",
            )
            access_density = geometry_row_two[1].number_input(
                _two_lane_text("access_density", unit=access_unit),
                key=f"manual_access_point_density_{unit_system}",
            )
            geometry_row_two[2].caption(_two_lane_text("method_caption"))

            render_section_label(_two_lane_text("traffic"))
            traffic_row_one = st.columns(3)
            analysis_volume = traffic_row_one[0].number_input(
                _two_lane_text("analysis_volume"),
                key=f"manual_analysis_direction_volume_{unit_system}",
            )
            peak_hour_factor = traffic_row_one[1].number_input(
                _two_lane_text("peak_hour_factor"),
                key=f"manual_peak_hour_factor_{unit_system}",
            )
            heavy_vehicle_percent = traffic_row_one[2].number_input(
                _two_lane_text("heavy_vehicles"),
                key=f"manual_heavy_vehicle_percent_{unit_system}",
            )
            traffic_row_two = st.columns(3)
            opposing_volume = None
            if segment_type == "passing_zone":
                opposing_volume = traffic_row_two[0].number_input(
                    _two_lane_text("opposing_volume"),
                    help=_two_lane_text("opposing_volume_help"),
                    key=f"manual_opposing_direction_volume_{unit_system}",
                )
            else:
                traffic_row_two[0].caption(_two_lane_text("opposing_inactive"))
            traffic_row_two[1].caption(_two_lane_text("directional_split_caption"))
            traffic_row_two[2].caption(_two_lane_text("no_passing_caption"))

            render_section_label(_two_lane_text("ffs_adjustments"))
            st.caption(_two_lane_text("ffs_caption"))

            render_section_label(_two_lane_text("advanced"))
            grade_columns = st.columns(2)
            if terrain_type == "mountainous":
                grade_percent = grade_columns[0].number_input(
                    _two_lane_text("grade_percent"),
                    key=f"manual_grade_percent_{unit_system}",
                    help=_two_lane_text("grade_help"),
                )
                grade_columns[1].caption(
                    _two_lane_text("grade_length_summary", length=segment_length, unit=length_unit)
                )
            else:
                grade_percent = 0.0
                grade_columns[0].caption(_two_lane_text("grade_inactive"))

            horizontal_subsegments: list[dict[str, Any]] = []
            curve_setup: dict[str, Any] | None = None
            generate_curve = False
            if horizontal_alignment == "horizontal_curves":
                st.caption(_two_lane_text("curve_active"))
                setup_defaults = curve_setup_defaults(unit_system, segment_length)
                for name, default in setup_defaults.items():
                    st.session_state.setdefault(
                        f"manual_curve_setup_{name}_{unit_system}", default
                    )
                curve_columns = st.columns(3)
                total_curve_length = curve_columns[0].number_input(
                    _two_lane_text("curve_length", unit=curve_length_unit),
                    key=f"manual_curve_setup_total_curve_length_{unit_system}",
                )
                curve_radius = curve_columns[1].number_input(
                    _two_lane_text("curve_radius", unit=curve_length_unit),
                    key=f"manual_curve_setup_radius_{unit_system}",
                )
                superelevation = curve_columns[2].number_input(
                    _two_lane_text("superelevation"),
                    key=f"manual_curve_setup_superelevation_percent_{unit_system}",
                )
                curve_columns_two = st.columns(3)
                central_angle = curve_columns_two[0].number_input(
                    _two_lane_text("central_angle"),
                    key=f"manual_curve_setup_central_angle_deg_{unit_system}",
                )
                horizontal_class = curve_columns_two[1].number_input(
                    _two_lane_text("horizontal_class"),
                    step=1,
                    key=f"manual_curve_setup_horizontal_class_{unit_system}",
                )
                subsegment_count = curve_columns_two[2].number_input(
                    _two_lane_text("subsegment_count"),
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
                generate_curve = st.button(
                    _two_lane_text("generate_curve"),
                    width="stretch",
                    key=f"manual_generate_curve_{unit_system}",
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
                st.caption(_two_lane_text("curve_editor_caption", unit=curve_length_unit))
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
                            _two_lane_text("subsegment_type"),
                            options=["tangent", "horizontal_curve"],
                            required=True,
                        ),
                        "length": st.column_config.NumberColumn(
                            _two_lane_text("subsegment_length", unit=curve_length_unit),
                            required=True,
                        ),
                        "superelevation_percent": st.column_config.NumberColumn(
                            _two_lane_text("superelevation")
                        ),
                        "radius": st.column_config.NumberColumn(
                            _two_lane_text("radius", unit=curve_length_unit)
                        ),
                        "central_angle_deg": st.column_config.NumberColumn(
                            _two_lane_text("central_angle")
                        ),
                        "horizontal_class": st.column_config.NumberColumn(
                            _two_lane_text("horizontal_class"),
                            step=1,
                        ),
                    },
                )
            else:
                st.caption(_two_lane_text("curve_inactive"))

            if segment_type == "passing_lane":
                st.caption(_two_lane_text("passing_lane_active"))
            else:
                st.caption(_two_lane_text("passing_lane_inactive"))

            run_manual = st.button(
                _two_lane_text("calculate"),
                type="primary",
                width="stretch",
                key=f"manual_segment_calculate_{unit_system}",
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

        conversion_error: Exception | None = None
        try:
            normalized_inputs = build_manual_segment_inputs(values)
        except HCMCalcError as exc:
            conversion_error = exc
            normalized_inputs = {}
        segment_workflow_inputs = {
            "method_identifier": "hcm7_two_lane_highway_segment",
            "input_contract": "phase_5_product_integration",
            "effective_engine_inputs": normalized_inputs,
        }
        segment_is_current = render_calculation_status(
            "manual_segment", segment_workflow_inputs, status_placeholder
        )
        if generate_curve and curve_setup is not None:
            try:
                generated_subsegments = generate_curve_subsegments(curve_setup)
            except HCMCalcError as exc:
                st.error(_two_lane_text("invalid_curve_detail", error=str(exc)))
            else:
                curve_version_key = f"manual_horizontal_subsegments_version_{unit_system}"
                st.session_state[curve_version_key] = (
                    st.session_state.get(curve_version_key, 0) + 1
                )
                st.session_state[
                    f"manual_horizontal_subsegments_seed_{unit_system}"
                ] = generated_subsegments
                st.session_state["manual_curve_generation_message"] = (
                    _two_lane_text("curve_generated", count=len(generated_subsegments))
                )
                st.rerun()

        _render_two_lane_schematic(
            segment_type=segment_type,
            segment_length=segment_length,
            unit=length_unit,
            terrain_type=terrain_type,
            grade_percent=grade_percent,
            horizontal_alignment=horizontal_alignment,
        )

    if run_manual:
        st.session_state.pop("manual_segment_result", None)
        st.session_state.pop("manual_segment_error", None)
        if conversion_error is not None:
            st.session_state["manual_segment_error"] = {
                "message": str(conversion_error),
                "state": ResultPresentationState.INVALID_INPUT,
            }
            st.session_state["manual_segment_audit"] = (
                build_manual_calculation_audit_record(values, error=conversion_error)
            )
        else:
            try:
                result = run_manual_single_segment(values)
                st.session_state["manual_segment_result"] = result_to_dict(result)
                st.session_state["manual_segment_audit"] = (
                    build_manual_calculation_audit_record(values, result=result)
                )
                mark_calculated(st.session_state, "manual_segment", segment_workflow_inputs)
                segment_is_current = render_calculation_status(
                    "manual_segment", segment_workflow_inputs, status_placeholder
                )
            except UnsupportedScopeError as exc:
                st.session_state["manual_segment_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.UNSUPPORTED_SCOPE,
                }
                st.session_state["manual_segment_audit"] = (
                    build_manual_calculation_audit_record(values, error=exc)
                )
            except HCMCalcError as exc:
                st.session_state["manual_segment_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.INVALID_INPUT,
                }
                st.session_state["manual_segment_audit"] = (
                    build_manual_calculation_audit_record(values, error=exc)
                )
            except Exception as exc:  # pragma: no cover - defensive UI boundary
                st.session_state["manual_segment_error"] = {
                    "message": str(exc),
                    "state": ResultPresentationState.INTERNAL_ERROR,
                }
                st.session_state["manual_segment_audit"] = {
                    "calculation_type": "manual_single_segment",
                    "unit_system": unit_system,
                    "user_inputs": values,
                    "normalized_engine_inputs": normalized_inputs,
                    "calculation_metadata": {
                        "status": "failed",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                }

    with result_column:
        with st.expander(_two_lane_text("validation"), expanded=False):
            st.markdown(f"**{_two_lane_text('validation_basis_heading')}**")
            st.caption(_two_lane_text("validation_basis"))
            st.markdown(f"**{_two_lane_text('supported_scope_heading')}**")
            st.caption(_two_lane_text("supported_scope"))
            st.markdown(f"**{_two_lane_text('not_supported_heading')}**")
            st.caption(_two_lane_text("not_supported"))
        render_section_label(_two_lane_text("results"))
        stored_result = st.session_state.get("manual_segment_result")
        audit_record = st.session_state.get("manual_segment_audit")
        stored_error = st.session_state.get("manual_segment_error")
        if stored_error is not None:
            error_state = (
                stored_error.get("state")
                if isinstance(stored_error, dict)
                else ResultPresentationState.INTERNAL_ERROR
            )
            if error_state not in {
                ResultPresentationState.UNSUPPORTED_SCOPE,
                ResultPresentationState.INVALID_INPUT,
                ResultPresentationState.INTERNAL_ERROR,
            }:
                error_state = ResultPresentationState.INTERNAL_ERROR
            message_key = {
                ResultPresentationState.UNSUPPORTED_SCOPE: "unsupported",
                ResultPresentationState.INVALID_INPUT: "invalid",
                ResultPresentationState.INTERNAL_ERROR: "internal_error",
            }[error_state]
            render_result_state_panel(error_state, _two_lane_text(message_key))
            detail = (
                stored_error.get("message")
                if isinstance(stored_error, dict)
                else str(stored_error)
            )
            st.caption(_two_lane_text("error_details", error=detail))
            render_audit_record(audit_record)
            render_manual_project_file_controls(values, segment_is_current)
            return
        if stored_result is None:
            render_result_state_panel(
                ResultPresentationState.PRERUN,
                _two_lane_text("prerun"),
            )
            render_manual_project_file_controls(values, segment_is_current)
            return

        presentation_state = resolve_result_presentation_state(
            freshness=workflow_status(
                st.session_state, "manual_segment", segment_workflow_inputs
            ),
            has_result=True,
            warnings=stored_result.get("warnings", ()),
            capacity_failure=False,
        )
        if presentation_state == ResultPresentationState.STALE_RESULT:
            render_result_state_panel(presentation_state, _two_lane_text("stale"))
            render_manual_project_file_controls(values, segment_is_current)
            st.caption(_two_lane_text("export_stale"))
            return

        result_unit_system = (
            str(audit_record.get("unit_system", unit_system))
            if isinstance(audit_record, dict)
            else unit_system
        )
        render_manual_result(
            stored_result,
            result_unit_system,
            audit_record,
            is_current=segment_is_current,
        )
        if presentation_state == ResultPresentationState.CAPACITY_FAILURE:
            render_result_state_panel(
                presentation_state, _two_lane_text("capacity_failure")
            )
        elif presentation_state == ResultPresentationState.VALID_CURRENT_RESULT_WITH_WARNING:
            render_result_state_panel(presentation_state, _two_lane_text("warning"))
        render_manual_project_file_controls(values, segment_is_current)
        if segment_is_current:
            render_export_report_section(
                "manual_single_segment",
                stored_result,
                result_unit_system,
                inputs=(
                    audit_record.get("user_inputs", {})
                    if isinstance(audit_record, dict)
                    else {}
                ),
                audit_record=audit_record,
                label=_two_lane_text("export_report"),
            )
        else:
            st.caption(_two_lane_text("export_stale"))


def _render_two_lane_schematic(
    *,
    segment_type: str,
    segment_length: float,
    unit: str,
    terrain_type: str,
    grade_percent: float | None,
    horizontal_alignment: str,
) -> None:
    """Render the shared-style Two-Lane conceptual schematic container."""

    render_section_label(_two_lane_text("schematic_title"))
    with st.container(border=True):
        schematic_path = get_segment_schematic_path(segment_type)
        if schematic_path is not None:
            st.image(schematic_path, width="stretch")
        active_geometry = [
            _two_lane_text(
                "schematic_length", length=float(segment_length), unit=unit
            ),
            _two_lane_text(
                "schematic_segment_type",
                segment_type=translate(
                    f"two_lane.segment_type.{segment_type}", _ui_locale()
                ),
            ),
            _two_lane_text(
                "schematic_alignment",
                alignment=translate(
                    f"two_lane.alignment.{horizontal_alignment}", _ui_locale()
                ),
            ),
        ]
        if terrain_type == "mountainous":
            active_geometry.append(
                _two_lane_text("schematic_grade", grade=float(grade_percent or 0.0))
            )
        st.caption(" | ".join(active_geometry))
        st.caption(_two_lane_text("schematic_caption"))
        st.caption(_two_lane_text("schematic_alt"))


def render_manual_project_file_controls(
    manual_inputs: dict[str, Any], is_current: bool | None = None
) -> None:
    """Render compact manual project save controls."""

    stored_audit = st.session_state.get("manual_segment_audit")
    if is_current is None:
        is_current = (
            workflow_status(st.session_state, "manual_segment", manual_inputs)
            == CALCULATED
        )
    calculation_matches_inputs = (
        is_current
        and
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
        _two_lane_text("project_caption"),
        lambda: st.download_button(
            _two_lane_text("save_project"),
            data=project_json,
            file_name="manual-single-segment-project.json",
            mime="application/json",
            width="stretch",
        ),
        label=_two_lane_text("project_output"),
    )


def _render_manual_project_load_controls() -> None:
    """Render compact manual project load controls."""

    uploaded_project = st.file_uploader(
        _two_lane_text("project_file"),
        type=["json"],
        key="manual_project_file_uploader",
    )
    if st.button(
        _two_lane_text("load_project"),
        disabled=uploaded_project is None,
        width="stretch",
    ):
        try:
            project = load_manual_project_json(uploaded_project.getvalue())
        except ProjectFileError as exc:
            st.error(_two_lane_text("project_load_error", error=str(exc)))
        else:
            saved_locale = project_presentation_locale(project)
            if saved_locale is not None:
                st.session_state["_pending_ui_locale"] = saved_locale
            st.session_state["manual_pending_project"] = project
            st.rerun()


def _restore_manual_project(project: dict[str, Any]) -> None:
    """Restore validated project data into manual worksheet session state."""

    manual_inputs = project["manual_inputs"]
    unit_system = project["unit_system"]
    st.session_state["manual_unit_label"] = unit_system
    st.session_state["manual_segment_type"] = manual_inputs["segment_type"]
    st.session_state["manual_terrain_type"] = manual_inputs["terrain_type"]
    st.session_state["manual_horizontal_alignment"] = manual_inputs["horizontal_alignment"]
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
        try:
            normalized_inputs = build_manual_segment_inputs(manual_inputs)
        except HCMCalcError:
            normalized_inputs = {}
        mark_calculated(
            st.session_state,
            "manual_segment",
            {
                "method_identifier": "hcm7_two_lane_highway_segment",
                "input_contract": "phase_5_product_integration",
                "effective_engine_inputs": normalized_inputs,
            },
        )
    st.session_state.pop("manual_segment_error", None)
    _restore_project_locale(project)
    st.session_state["manual_project_load_message"] = project_load_message(project, _ui_locale())


def render_audit_record(audit_record: dict[str, Any] | None) -> None:
    """Render a collapsed manual calculation audit record."""

    if audit_record is None:
        return
    with st.expander(_two_lane_text("audit")):
        st.caption(_two_lane_text("audit_caption"))
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
        primary_label=translate("result.level_of_service", _ui_locale()),
        primary_value=level_of_service,
        primary_kind="los",
        hero_supporting_label=translate("result.follower_density", _ui_locale()),
        hero_supporting_value=density,
        secondary_metrics=[
            {
                "label": {
                    "average_speed": translate(
                        "result.average_travel_speed", _ui_locale()
                    ),
                    "percent_followers": translate(
                        "result.percent_followers", _ui_locale()
                    ),
                    "demand_flow_rate": translate(
                        "result.demand_flow_rate", _ui_locale()
                    ),
                    "capacity": translate("result.capacity", _ui_locale()),
                    "free_flow_speed": translate(
                        "result.free_flow_speed", _ui_locale()
                    ),
                }.get(name, metric["label"]),
                "value": format_display_metric(name, metric, unit_system),
            }
            for name, metric in metrics.items()
            if name != "follower_density"
        ],
    )

    with st.expander(_two_lane_text("calculation_details"), expanded=False):
        st.markdown(f"**{translate('common.assumptions', _ui_locale())}**")
        for assumption in result_data["assumptions"]:
            st.markdown(f"- {assumption}")
        st.markdown(f"**{translate('common.warnings', _ui_locale())}**")
        for warning in result_data["warnings"]:
            st.markdown(f"- {warning}")
    with st.expander(_two_lane_text("audit"), expanded=False):
        st.markdown(f"**{translate('common.intermediate_values', _ui_locale())}**")
        st.dataframe(
            [
                {**value, "value": str(value["value"])}
                for value in result_data["intermediate_values"]
            ],
            hide_index=True,
            width="stretch",
        )
        if audit_record is not None:
            st.markdown(f"**{_two_lane_text('audit_record')}**")
            st.caption(_two_lane_text("audit_caption"))
            st.json(audit_record)

    full_result = {
        "unit_system": unit_system,
        "display_outputs": metrics,
        "engine_result": result_data,
    }
    full_result_json = json.dumps(full_result, indent=2)
    with st.expander(_two_lane_text("full_json"), expanded=False):
        st.caption(_two_lane_text("full_json_caption"))
        st.json(full_result)
        if is_current:
            st.download_button(
                translate("result.download_json", _ui_locale()),
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
    label: str | None = None,
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
        ),
        label=label,
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
    pending_locale = st.session_state.pop("_pending_ui_locale", None)
    if pending_locale is not None:
        st.session_state["ui_locale"] = normalize_locale(str(pending_locale))
    st.session_state.setdefault("ui_locale", "en")
    header_left, header_right = st.columns([1.4, 1.0], gap="large")
    with header_left:
        st.markdown(
            f"**{translate('app.title', _ui_locale())}** - "
            f"{translate('app.workflow_summary', _ui_locale())}"
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
        selected_view = st.session_state.get(
            "selected_calculator_view", APP_MODE_TO_VIEW[APP_MODE_LABELS[0]]
        )
        if selected_view not in APP_VIEW_TO_MODE:
            legacy_mode = st.session_state.get("selected_calculator_mode")
            selected_view = APP_MODE_TO_VIEW.get(
                str(legacy_mode), APP_MODE_TO_VIEW[APP_MODE_LABELS[0]]
            )
        group_by_view = {
            view: group for group, views in NAVIGATION_GROUP_VIEWS for view in views
        }
        selected_group = group_by_view[selected_view]
        groups = [name for name, _ in NAVIGATION_GROUP_VIEWS]
        group = st.selectbox(
            translate("nav.category", mode_locale),
            groups,
            index=groups.index(selected_group),
            format_func=lambda value, locale=mode_locale: translate(f"nav.group.{value}", locale),
            key="workflow.navigation.category",
        )
        views = dict(NAVIGATION_GROUP_VIEWS)[group]
        if selected_view not in views:
            selected_view = views[0]
        selected_view = st.selectbox(
            translate("nav.workflow", mode_locale),
            views,
            index=views.index(selected_view),
            format_func=lambda value, locale=mode_locale: translate(
                APP_VIEW_TO_NAV_KEY[value], locale
            ),
            key="workflow.navigation.view",
        )
        mode_label = APP_VIEW_TO_MODE[selected_view]
        st.session_state["selected_calculator_view"] = selected_view
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
    elif mode == "manual_merge":
        render_manual_ramp_calculator("merge")
    elif mode == "manual_diverge":
        render_manual_ramp_calculator("diverge")
    elif mode == "supported_workflows":
        render_supported_workflows_page()
    else:
        render_validated_case_viewer()
    st.divider()
    st.caption(translate("app.limitations_footer", _ui_locale()))


if __name__ == "__main__":
    main()
