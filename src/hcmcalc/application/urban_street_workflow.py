"""Application adapter for the qualified, bounded HCM Chapter 18 engine."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from hcmcalc.application.registry import get_analysis_definition
from hcmcalc.core import UnsupportedScopeError
from hcmcalc.ui.units import FEET_TO_METERS, MILES_TO_KILOMETERS
from hcmcalc.urban_street_ch18 import (
    UrbanStreetSegmentInputs,
    UrbanStreetSegmentMethod,
    _validate_inputs,
)


METHOD_ID = "urban_street_segment"
TEMPLATE_ID = "USS-CH30-EP1"
DISPLAY_FIELDS = (
    "segment_length", "upstream_intersection_width", "signal_control_spacing",
    "through_lane_count", "subject_direction", "through_movement_id",
    "posted_speed_limit", "s_calib", "restrictive_median_proportion",
    "curb_proportion", "parking_proportion", "subject_side_access_count",
    "opposing_side_access_count", "v_m_veh_h", "access_point_delays_s_veh",
    "d_other_s_veh", "analysis_period_min", "control_type", "demand_balanced",
    "demand_adjustments_resolved", "capacity_effects_resolved", "spillback_present",
    "external_source_class", "external_source_tool", "external_source_method_note",
    "external_hcm_edition_note", "external_direction", "external_control_type",
    "external_through_movement_id", "external_analysis_period_min",
    "external_scenario_note", "v_th_veh_h", "c_th_veh_h", "d_t_s_veh",
)
EXTERNAL_FIELDS = {
    "external_source_class": "source_class",
    "external_source_tool": "source_tool",
    "external_source_method_note": "source_method_note",
    "external_hcm_edition_note": "hcm_edition_note",
    "external_direction": "direction",
    "external_control_type": "control_type",
    "external_through_movement_id": "through_movement_id",
    "external_analysis_period_min": "analysis_period_min",
    "external_scenario_note": "scenario_note",
    "v_th_veh_h": "v_th_veh_h",
    "c_th_veh_h": "c_th_veh_h",
    "d_t_s_veh": "d_t_s_veh",
}


def _example_inputs(unit: str) -> dict[str, Any]:
    metric = unit == "metric"
    length = lambda feet: feet * FEET_TO_METERS if metric else float(feet)
    speed = lambda mph: mph * MILES_TO_KILOMETERS if metric else float(mph)
    return {
        "segment_length": length(1800),
        "upstream_intersection_width": length(50),
        "signal_control_spacing": length(1800),
        "through_lane_count": 2,
        "subject_direction": "eastbound",
        "through_movement_id": "EB_TH",
        "posted_speed_limit": speed(35),
        "s_calib": speed(0),
        "restrictive_median_proportion": 0,
        "curb_proportion": 0.70,
        "parking_proportion": 0,
        "subject_side_access_count": 4,
        "opposing_side_access_count": 4,
        "v_m_veh_h": 1150,
        "access_point_delays_s_veh": [0.193, 0.194],
        "d_other_s_veh": 0,
        "analysis_period_min": 15,
        "control_type": "signalized",
        "demand_balanced": True,
        "demand_adjustments_resolved": True,
        "capacity_effects_resolved": True,
        "spillback_present": False,
        "external_source_class": "qualified_external_signal_analysis",
        "external_source_tool": "HCM 7 Chapter 30 Example Problem 1",
        "external_source_method_note": "HCM 7 Chapter 30 Example Problem 1",
        "external_hcm_edition_note": "HCM 7.0",
        "external_direction": "eastbound",
        "external_control_type": "signalized",
        "external_through_movement_id": "EB_TH",
        "external_analysis_period_min": 15,
        "external_scenario_note": "Chapter 30 Example Problem 1",
        "v_th_veh_h": 968,
        "c_th_veh_h": 1848,
        "d_t_s_veh": 18.310,
    }


def _field_schema() -> list[dict[str, Any]]:
    lengths = {"segment_length", "upstream_intersection_width", "signal_control_spacing"}
    speeds = {"posted_speed_limit", "s_calib"}
    choices = {"subject_direction", "through_movement_id", "control_type"}
    result = []
    for key in DISPLAY_FIELDS:
        kind = "choice" if key in choices else "boolean" if key in {
            "demand_balanced", "demand_adjustments_resolved", "capacity_effects_resolved", "spillback_present"
        } else "integer" if key in {
            "through_lane_count", "subject_side_access_count", "opposing_side_access_count", "analysis_period_min", "external_analysis_period_min"
        } else "number"
        field = {"key": key, "kind": kind, "required": True}
        if key in lengths:
            field.update(unit_metric="m", unit_imperial="ft")
        elif key in speeds:
            field.update(unit_metric="km/h", unit_imperial="mi/h")
        elif key.endswith("_veh_h"):
            field["unit"] = "veh/h"
        elif "delay" in key or key.endswith("d_t_s_veh") or key == "d_other_s_veh":
            field["unit"] = "s/veh"
        result.append(field)
    result[DISPLAY_FIELDS.index("access_point_delays_s_veh")]["kind"] = "number_list"
    result[DISPLAY_FIELDS.index("access_point_delays_s_veh")]["item_unit"] = "s/veh"
    return result


class UrbanStreetWorkflow:
    """Flat displayed inputs, canonical engine mapping, and current result evidence."""

    method_id = METHOD_ID

    def __init__(self) -> None:
        self.definition = get_analysis_definition(METHOD_ID)
        if self.definition is None:
            raise KeyError(METHOD_ID)

    def templates(self) -> dict[str, Any]:
        return {
            "method_id": METHOD_ID,
            "unit_systems": ["metric", "imperial"],
            "default_template_id": TEMPLATE_ID,
            "templates": [
                {"template_id": TEMPLATE_ID, "label": "HCM Chapter 30 Example Problem 1", "description": "Qualified HCM RHT-reference, signalized 15-minute case.", "validation_status": "reference_fixture", "starter_kind": "example"},
                {"template_id": "blank_custom", "label": "Blank worksheet", "description": "Supply every engineering input and external qualification explicitly.", "validation_status": "ui_starter_only", "starter_kind": "blank"},
            ],
            "fields": _field_schema(),
            "groups": [
                {"key": "segment", "field_keys": list(DISPLAY_FIELDS[:22])},
                {"key": "external_through", "field_keys": list(DISPLAY_FIELDS[22:])},
            ],
            "branches": {"validation_without_calculation": True, "bounded": True},
            "scope_notes": [
                "HCM 7.0 Chapter 18 bounded signalized 15-minute operational workflow; segment length is limited to 2 mi.",
                "HCM right-hand-traffic reference semantics only; no Thailand/LHT qualification or sided-value mirroring.",
                "Python calls the qualified Chapter 18 engine; external downstream through performance is required.",
            ],
        }

    def starting_values(self, template_id: str, unit_system: str) -> dict[str, Any]:
        from hcmcalc.application.workflows import _normalize_unit_system

        unit = _normalize_unit_system(unit_system)
        if template_id == TEMPLATE_ID:
            displayed = _example_inputs(unit)
            label = "HCM Chapter 30 Example Problem 1"
            validation_status = "reference_fixture"
        elif template_id == "blank_custom":
            displayed = {key: None for key in DISPLAY_FIELDS}
            displayed["access_point_delays_s_veh"] = None
            label = "Blank worksheet"
            validation_status = "ui_starter_only"
        else:
            raise self._application_error(f"Unknown Chapter 18 template: {template_id}.", "invalid_template", "api.invalid_template", {"template_id": template_id})
        from hcmcalc.application.workflows import _json_ready

        return _json_ready({
            "method_id": METHOD_ID,
            "template_id": template_id,
            "template_label": label,
            "template_description": self.templates()["templates"][0 if template_id == TEMPLATE_ID else 1]["description"],
            "validation_status": validation_status,
            "starter_kind": "example" if template_id == TEMPLATE_ID else "blank",
            "unit_system": unit,
            "displayed_inputs": displayed,
            "fields": _field_schema(),
            "groups": deepcopy(self.templates()["groups"]),
            "scope_notes": self.templates()["scope_notes"],
        })

    def _normalized(self, template_id: str, unit_system: str, displayed_inputs: Mapping[str, Any]) -> dict[str, Any]:
        from hcmcalc.application.workflows import _normalize_unit_system

        unit = _normalize_unit_system(unit_system)
        if template_id not in {TEMPLATE_ID, "blank_custom"}:
            raise self._application_error(f"Unknown Chapter 18 template: {template_id}.", "invalid_template", "api.invalid_template", {"template_id": template_id})
        if not isinstance(displayed_inputs, Mapping):
            raise self._application_error("displayed_inputs must be an object.", "invalid_input", "api.invalid_input", {"field": "displayed_inputs"})
        unknown = set(displayed_inputs) - set(DISPLAY_FIELDS)
        if unknown:
            field = sorted(unknown)[0]
            raise self._application_error(f"Unsupported Chapter 18 input: {field}.", "invalid_input", "api.invalid_input", {"field": field})
        values = dict(displayed_inputs)
        length_factor = 1 / FEET_TO_METERS if unit == "metric" else 1.0
        speed_factor = 1 / MILES_TO_KILOMETERS if unit == "metric" else 1.0
        normalized = {
            "segment_length_ft": _scaled(values.get("segment_length"), length_factor),
            "upstream_intersection_width_ft": _scaled(values.get("upstream_intersection_width"), length_factor),
            "signal_control_spacing_ft": _scaled(values.get("signal_control_spacing"), length_factor),
            "through_lane_count": values.get("through_lane_count"),
            "subject_direction": values.get("subject_direction"),
            "through_movement_id": values.get("through_movement_id"),
            "posted_speed_limit_mph": _scaled(values.get("posted_speed_limit"), speed_factor),
            "s_calib_mph": _scaled(values.get("s_calib"), speed_factor),
            "restrictive_median_proportion": values.get("restrictive_median_proportion"),
            "curb_proportion": values.get("curb_proportion"),
            "parking_proportion": values.get("parking_proportion"),
            "subject_side_access_count": values.get("subject_side_access_count"),
            "opposing_side_access_count": values.get("opposing_side_access_count"),
            "v_m_veh_h": values.get("v_m_veh_h"),
            "access_point_delays_s_veh": values.get("access_point_delays_s_veh"),
            "d_other_s_veh": values.get("d_other_s_veh"),
            "analysis_period_min": values.get("analysis_period_min"),
            "control_type": values.get("control_type"),
            "demand_balanced": values.get("demand_balanced"),
            "demand_adjustments_resolved": values.get("demand_adjustments_resolved"),
            "capacity_effects_resolved": values.get("capacity_effects_resolved"),
            "spillback_present": values.get("spillback_present"),
            "external_through": {
                engine_key: values.get(display_key)
                for display_key, engine_key in EXTERNAL_FIELDS.items()
            },
        }
        try:
            parsed = UrbanStreetSegmentInputs.from_mapping(normalized)
            _validate_inputs(parsed)
        except Exception as exc:
            code = "unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "invalid_input"
            raise self._application_error(str(exc), code, f"api.{code}") from exc
        from hcmcalc.application.workflows import _json_ready

        return _json_ready(normalized)

    def validate(self, *, template_id: str, unit_system: str, displayed_inputs: Mapping[str, Any]) -> dict[str, Any]:
        from hcmcalc.application.workflows import _error_issue, _json_ready, _normalize_unit_system, _snapshot
        from hcmcalc.application.workflow_state import ResultPresentationState

        try:
            normalized = self._normalized(template_id, unit_system, displayed_inputs)
        except Exception as exc:
            issue = _error_issue(exc)
            return {
                "method_id": METHOD_ID, "template_id": template_id, "unit_system": str(unit_system).lower(),
                "valid": False, "ready": False, "validation_status": issue["code"], "errors": [issue],
                "displayed_inputs": deepcopy(dict(displayed_inputs)) if isinstance(displayed_inputs, Mapping) else {},
                "normalized_inputs": None,
                "calculation_state": {"presentation_state": ResultPresentationState.INVALID_INPUT.value, "has_result": False, "warnings": []},
            }
        snapshot = _snapshot(self.definition, template_id=template_id, unit_system=_normalize_unit_system(unit_system), displayed_inputs=displayed_inputs, normalized_inputs=normalized)
        return _json_ready({
            **snapshot, "valid": True, "ready": True, "validation_status": "valid", "errors": [],
            "calculation_state": {"presentation_state": ResultPresentationState.PRERUN.value, "calculation_fingerprint": snapshot["calculation_fingerprint"], "has_result": False, "warnings": []},
        })

    def calculate(self, *, template_id: str, unit_system: str, displayed_inputs: Mapping[str, Any]) -> dict[str, Any]:
        from hcmcalc.application.workflows import _available_metric, _interpretation_mappings, _json_ready, _normalize_unit_system, _result_envelope, _snapshot
        from hcmcalc.application.workflow_state import READY, ResultPresentationState, resolve_result_presentation_state
        from hcmcalc.cli import result_to_dict

        unit = _normalize_unit_system(unit_system)
        normalized = self._normalized(template_id, unit, displayed_inputs)
        snapshot = _snapshot(self.definition, template_id=template_id, unit_system=unit, displayed_inputs=displayed_inputs, normalized_inputs=normalized)
        try:
            engine_result = UrbanStreetSegmentMethod().calculate(normalized)
            result = result_to_dict(engine_result)
        except Exception as exc:
            code = "unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "invalid_input"
            raise self._application_error(str(exc), code, f"api.{code}") from exc
        out = result["outputs"]
        state = resolve_result_presentation_state(freshness=READY, has_result=True, warnings=result.get("warnings", []))
        speed_factor = MILES_TO_KILOMETERS if unit == "metric" else 1.0
        speed_unit = "km/h" if unit == "metric" else "mi/h"
        metrics = [
            _available_metric("travel_speed", out["travel_speed_mph"] * speed_factor, speed_unit, source="HCM 7.0 Chapter 18; Eq. 18-15"),
            _available_metric("running_speed", out["running_speed_mph"] * speed_factor, speed_unit, source="HCM 7.0 Chapter 18; running time"),
            _available_metric("free_flow_speed", out["free_flow_speed_mph"] * speed_factor, speed_unit, source="HCM 7.0 Chapter 18; Eq. 18-5"),
            _available_metric("base_free_flow_speed", out["base_free_flow_speed_mph"] * speed_factor, speed_unit, source="HCM 7.0 Chapter 18; Eq. 18-3"),
            _available_metric("through_v_c", out["through_v_c"], "ratio", source="HCM 7.0 Exhibit 18-1; v_th/c_th"),
            _available_metric("running_time", out["running_time_s"], "s", source="HCM 7.0 Chapter 18; Eqs. 18-7 and 18-8"),
            _available_metric("total_travel_time", out["total_travel_time_s"], "s", source="Running time plus qualified external through delay"),
        ]
        presentation = {
            "answer": {"key": "level_of_service", "value": out["level_of_service"], "available": True, "source": "HCM 7.0 Exhibit 18-1"},
            "metrics": metrics,
            "capacity": {"through_v_c": out["through_v_c"], "source": "HCM 7.0 Exhibit 18-1; v_th/c_th"},
            "warning": None,
            "interpretations": _interpretation_mappings(state),
            "evidence": {"intermediate_values": result["intermediate_values"], "assumptions": result["assumptions"], "external_through_provenance": out["external_through_provenance"], "warnings": result["warnings"]},
            "workflow": {"scope": "bounded_hcm7_signalized_15min_rht_reference", "spillback_present": normalized["spillback_present"]},
        }
        audit = {
            "calculation_type": self.definition.project_type,
            "method_identifier": self.definition.method_identifier,
            "engine_method_identifier": self.definition.engine_method_identifier,
            "method_version": self.definition.method_version,
            "input_contract": self.definition.input_contract,
            "template_id": template_id,
            "unit_system": unit,
            "displayed_inputs": deepcopy(dict(displayed_inputs)),
            "normalized_engine_inputs": deepcopy(normalized),
            "outputs": deepcopy(out),
            "assumptions": list(result["assumptions"]),
            "intermediate_values": deepcopy(result["intermediate_values"]),
            "external_through_provenance": deepcopy(out["external_through_provenance"]),
        }
        return _result_envelope(self.definition, snapshot=snapshot, result=result, state=state, presentation=presentation, audit=audit)

    @staticmethod
    def _application_error(message: str, code: str, message_key: str, details: Mapping[str, Any] | None = None) -> ValueError:
        from hcmcalc.application.workflows import ApplicationWorkflowError

        return ApplicationWorkflowError(message, code=code, message_key=message_key, details=details)


def _scaled(value: Any, factor: float) -> Any:
    return None if value is None else float(value) * factor
