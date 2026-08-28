"""Framework-independent services for the rebuilt HCM workflows.

The services in this module are the application boundary between the existing
qualified Python methods and any presentation layer.  They deliberately do
not import FastAPI, Streamlit, React, or a database.  Displayed values are
normalized at this boundary, calculation identity is captured before the
engine is called, and presentation data is derived from an existing result.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
from math import isclose
import re
from typing import Any, Mapping

from hcmcalc.application.contracts import CalculationIdentity
from hcmcalc.application.interpretation import (
    InterpretationCode,
    interpretations_for_state,
)
from hcmcalc.application.registry import AnalysisDefinition, get_analysis_definition
from hcmcalc.application.workflow_state import (
    MISSING_REQUIRED_INPUT,
    MetricAvailability,
    READY,
    ResultPresentationState,
    resolve_result_presentation_state,
    snapshot_input_fingerprint,
)
from hcmcalc.cli import result_to_dict
from hcmcalc.core import HCMCalcError, MethodNotImplementedError, UnsupportedScopeError
from hcmcalc.multilane.models import MultilaneBasicSegmentInputs
from hcmcalc.multilane.validation import reject_unsupported_scope_keys, validate_inputs
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    build_manual_facility_inputs,
    canonicalize_manual_facility_rows,
    facility_segment_result_rows,
    facility_template_options,
    load_facility_template,
    run_manual_facility,
    validate_manual_facility_table,
)
from hcmcalc.ui.manual_multilane import (
    HEAVY_VEHICLE_ADJUSTMENT_METHODS,
    MANUAL_MULTILANE_CALCULATION_TYPE,
    build_manual_multilane_audit_record,
    heavy_vehicle_adjustment_method_from_ui_inputs,
    load_multilane_template,
    multilane_blank_ui_inputs,
    multilane_display_outputs,
    multilane_engine_inputs_to_ui,
    multilane_template_options,
    multilane_ui_inputs_to_engine,
    run_manual_multilane,
)
from hcmcalc.ui.reporting import build_report, export_report, report_filename
from hcmcalc.ui.units import FEET_TO_METERS, MILES_TO_KILOMETERS


REPRESENTATIVE_METHOD_IDS = frozenset({"multilane_segment", "two_lane_facility"})
PHASE3_METHOD_IDS = frozenset({
    "two_lane_segment",
    "basic_freeway_segment",
    "weaving_segment",
    "merge_segment",
    "diverge_segment",
})
SUPPORTED_WORKFLOW_EXPORTS = frozenset({"csv", "xlsx", "markdown", "json"})


class ApplicationWorkflowError(ValueError):
    """A safe, structured application-boundary error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "invalid_input",
        message_key: str = "api.invalid_input",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message_key = message_key
        self.details = dict(details or {})


class StaleResultError(ApplicationWorkflowError):
    """Raised when a report/export request is not backed by a current result."""

    def __init__(self, message: str = "The supplied result is stale.") -> None:
        super().__init__(
            message,
            code="stale_result",
            message_key="api.stale_result",
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_ready(value: Any) -> Any:
    """Return a detached value and reject NaN/Infinity at the app boundary."""

    try:
        encoded = json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ApplicationWorkflowError(
            f"Workflow value is not JSON serializable: {exc}",
            code="internal_error",
            message_key="api.internal_error",
        ) from exc
    return json.loads(encoded)


def _error_issue(exc: Exception, *, field: str | None = None) -> dict[str, Any]:
    details = getattr(exc, "details", {})
    issue_field = field or (details.get("field") if isinstance(details, Mapping) else None)
    if issue_field is None:
        for candidate in (
            "number_of_lanes", "segment_length", "demand_volume_veh_h",
            "peak_hour_factor", "heavy_vehicle_percent", "ffs_source",
            "free_flow_speed", "posted_speed_limit", "lane_width",
            "roadside_lateral_clearance", "left_side_lateral_clearance",
            "access_point_density", "heavy_vehicle_adjustment_method",
            "terrain_type", "grade_percent", "truck_mix",
            "passenger_car_equivalent",
            "segment_type", "horizontal_alignment", "configuration",
            "entry_side", "exit_side", "number_of_weaving_lanes",
            "freeway_lanes", "ramp_demand_veh_h", "freeway_demand_veh_h",
            "geometry_notes", "geometry_source", "pce_mode",
        ):
            if candidate in str(exc):
                issue_field = candidate
                break
    if isinstance(exc, ApplicationWorkflowError):
        code = exc.code
        message_key = exc.message_key
    elif isinstance(exc, UnsupportedScopeError):
        code = "unsupported_scope"
        message_key = "api.unsupported_scope"
    elif isinstance(exc, MethodNotImplementedError):
        code = "unsupported_scope"
        message_key = "api.unsupported_scope"
    else:
        code = "invalid_input"
        message_key = "api.invalid_input"
    return {
        "code": code,
        "field": issue_field,
        "message": str(exc),
        "message_key": message_key,
    }


def _definition(method_id: str) -> AnalysisDefinition:
    definition = get_analysis_definition(method_id)
    if definition is None:
        raise ApplicationWorkflowError(
            f"Unknown method_id: {method_id}.",
            code="method_not_found",
            message_key="api.method_not_found",
            details={"method_id": method_id},
        )
    return definition


def _normalize_unit_system(unit_system: str) -> str:
    value = str(unit_system).strip().lower()
    if value not in {"metric", "imperial"}:
        raise ApplicationWorkflowError(
            "unit_system must be metric or imperial.",
            details={"field": "unit_system"},
        )
    return value


def _snapshot_fingerprint(
    definition: AnalysisDefinition,
    displayed_inputs: Mapping[str, Any],
    normalized_inputs: Mapping[str, Any],
) -> str:
    """Fingerprint the complete user snapshot for current/stale UX.

    ``calculation_fingerprint`` remains the legacy-compatible fingerprint of
    normalized engine inputs.  This second fingerprint also includes the
    displayed snapshot so a persisted worksheet can be recognized exactly.
    """

    return snapshot_input_fingerprint(
        definition.method_identifier,
        definition.input_contract,
        displayed_inputs,
        normalized_inputs,
    )


def _snapshot(
    definition: AnalysisDefinition,
    *,
    template_id: str,
    unit_system: str,
    displayed_inputs: Mapping[str, Any],
    normalized_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    identity = CalculationIdentity(
        definition.method_identifier,
        definition.input_contract,
        normalized_inputs,
    )
    return {
        "method_id": definition.method_id,
        "method_identifier": definition.method_identifier,
        "engine_method_identifier": definition.engine_method_identifier,
        "method_version": definition.method_version,
        "input_contract": definition.input_contract,
        "project_type": definition.project_type,
        "template_id": template_id,
        "unit_system": unit_system,
        "displayed_inputs": deepcopy(dict(displayed_inputs)),
        "normalized_inputs": deepcopy(dict(normalized_inputs)),
        "calculation_fingerprint": identity.fingerprint,
        "input_snapshot_fingerprint": _snapshot_fingerprint(
            definition, displayed_inputs, normalized_inputs
        ),
    }


def _available_metric(
    key: str,
    value: Any,
    unit: str | None,
    *,
    source: str | None = None,
    availability: MetricAvailability | str | None = None,
    capacity_failure: bool = False,
) -> dict[str, Any]:
    available = value is not None
    if available:
        resolved_availability = MetricAvailability.CALCULATED.value
    elif availability is not None:
        resolved_availability = (
            availability.value
            if isinstance(availability, MetricAvailability)
            else str(availability)
        )
    elif capacity_failure:
        resolved_availability = MetricAvailability.NOT_PREDICTED.value
    else:
        resolved_availability = MetricAvailability.NOT_CALCULATED.value
    if resolved_availability not in {item.value for item in MetricAvailability}:
        raise ValueError(f"Unsupported metric availability: {resolved_availability}")
    return {
        "key": key,
        "value": None if value is None else float(value),
        "unit": unit,
        "available": available,
        "availability": resolved_availability,
        "source": source,
    }


def _scale_optional(value: Any, factor: float) -> float | None:
    """Scale an optional engine value without turning unavailable into zero."""

    return None if value is None else float(value) * factor


def _interpretation_mappings(
    state: ResultPresentationState,
    *,
    warning_codes: tuple[InterpretationCode, ...] = (),
) -> list[dict[str, Any]]:
    return [item.to_mapping() for item in interpretations_for_state(state, warning_codes=warning_codes)]


def _capacity_failure(result: Mapping[str, Any]) -> bool:
    outputs = result.get("outputs", {})
    if not isinstance(outputs, Mapping):
        return False
    return bool(
        outputs.get("demand_exceeds_capacity")
        or outputs.get("facility_has_capacity_failure")
        or outputs.get("capacity_exceeded")
        or outputs.get("capacity_status") in {"demand_exceeds_capacity", "capacity_exceeded"}
        or outputs.get("capacity_check") in {"demand_exceeds_capacity", "capacity_exceeded"}
    )


def _result_envelope(
    definition: AnalysisDefinition,
    *,
    snapshot: Mapping[str, Any],
    result: Mapping[str, Any],
    state: ResultPresentationState,
    presentation: Mapping[str, Any],
    audit: Mapping[str, Any],
) -> dict[str, Any]:
    return _json_ready(
        {
            **dict(snapshot),
            "calculation_state": {
                "presentation_state": state.value,
                "calculation_fingerprint": snapshot["calculation_fingerprint"],
                "has_result": True,
                "warnings": list(result.get("warnings", [])),
            },
            "result": dict(result),
            "presentation": dict(presentation),
            "audit": dict(audit),
            "method": {
                "method_id": definition.method_id,
                "method_identifier": definition.method_identifier,
                "input_contract": definition.input_contract,
                "method_version": definition.method_version,
            },
            "generated_at": _now(),
        }
    )


MULTILANE_FIELD_SCHEMA: tuple[dict[str, Any], ...] = (
    {"key": "number_of_lanes", "kind": "integer", "required": True, "unit": "lanes", "label_key": "multilane.number_of_lanes"},
    {"key": "segment_length", "kind": "number", "required": True, "unit_metric": "m", "unit_imperial": "ft", "label_key": "multilane.segment_length"},
    {"key": "demand_volume_veh_h", "kind": "number", "required": True, "unit": "veh/h", "label_key": "multilane.demand_volume"},
    {"key": "peak_hour_factor", "kind": "number", "required": True, "unit": "PHF", "label_key": "multilane.peak_hour_factor"},
    {"key": "heavy_vehicle_percent", "kind": "number", "required": True, "unit": "%", "label_key": "multilane.heavy_vehicles"},
    {"key": "ffs_source", "kind": "choice", "required": True, "options": ["estimated", "measured"], "label_key": "multilane.ffs_source"},
    {"key": "free_flow_speed", "kind": "number", "required_if": {"ffs_source": "measured"}, "unit_metric": "km/h", "unit_imperial": "mph", "label_key": "multilane.measured_ffs"},
    {"key": "posted_speed_limit", "kind": "number", "required_if": {"ffs_source": "estimated"}, "unit_metric": "km/h", "unit_imperial": "mph", "label_key": "multilane.posted_speed"},
    {"key": "lane_width", "kind": "number", "required_if": {"ffs_source": "estimated"}, "unit_metric": "m", "unit_imperial": "ft", "label_key": "multilane.lane_width"},
    {"key": "roadside_lateral_clearance", "kind": "number", "required_if": {"ffs_source": "estimated"}, "unit_metric": "m", "unit_imperial": "ft", "label_key": "multilane.right_clearance"},
    {"key": "median_type", "kind": "choice", "required_if": {"ffs_source": "estimated"}, "options": ["twltl", "divided"], "label_key": "multilane.median_type"},
    {"key": "left_side_lateral_clearance", "kind": "number", "required_if": {"median_type": "divided"}, "unit_metric": "m", "unit_imperial": "ft", "label_key": "multilane.left_clearance"},
    {"key": "access_point_density", "kind": "number", "required_if": {"ffs_source": "estimated"}, "unit_metric": "per km", "unit_imperial": "per mi", "label_key": "multilane.access_density"},
    {"key": "heavy_vehicle_adjustment_method", "kind": "choice", "required": True, "options": sorted(HEAVY_VEHICLE_ADJUSTMENT_METHODS), "label_key": "multilane.heavy_method"},
    {"key": "terrain_type", "kind": "choice", "required_if": {"heavy_vehicle_adjustment_method": "general_terrain"}, "options": ["level", "rolling"], "label_key": "multilane.terrain"},
    {"key": "grade_percent", "kind": "number", "required_if": {"heavy_vehicle_adjustment_method": "specific_grade"}, "unit": "%", "label_key": "multilane.grade"},
    {"key": "truck_mix", "kind": "choice", "required_if": {"heavy_vehicle_adjustment_method": "specific_grade"}, "options": ["default_30_sut_70_tt", "equal_50_sut_50_tt", "majority_70_sut_30_tt"], "label_key": "multilane.heavy_vehicle_composition"},
    {"key": "passenger_car_equivalent", "kind": "number", "required_if": {"heavy_vehicle_adjustment_method": "external_pce"}, "unit": "PCE", "label_key": "multilane.external_pce"},
)


FACILITY_FIELD_SCHEMA: tuple[dict[str, Any], ...] = (
    {"key": "segment_name", "kind": "text", "editable": True, "label_key": "facility.col.segment_name"},
    {"key": "segment_id", "kind": "integer", "editable": False, "label_key": "facility.col.segment_id"},
    {"key": "segment_type", "kind": "locked_choice", "editable": False, "label_key": "facility.col.segment_type"},
    {"key": "segment_length", "kind": "number", "editable": False, "label_key": "facility.col.segment_length"},
    {"key": "posted_speed", "kind": "number", "editable": True, "label_key": "facility.col.posted_speed"},
    {"key": "analysis_direction_volume_veh_h", "kind": "number", "editable": True, "label_key": "facility.col.analysis_volume"},
    {"key": "opposing_direction_volume_veh_h", "kind": "number", "editable": True, "conditional": "passing_zone", "label_key": "facility.col.opposing_volume"},
    {"key": "peak_hour_factor", "kind": "number", "editable": True, "label_key": "facility.col.peak_hour_factor"},
    {"key": "heavy_vehicle_percent", "kind": "number", "editable": True, "label_key": "facility.col.heavy_vehicles"},
    {"key": "terrain_type", "kind": "locked_choice", "editable": False, "label_key": "facility.col.terrain"},
    {"key": "grade_percent", "kind": "number", "editable": False, "label_key": "facility.col.grade"},
    {"key": "horizontal_alignment", "kind": "locked_choice", "editable": False, "label_key": "facility.col.alignment"},
    {"key": "lane_width", "kind": "number", "editable": False, "label_key": "facility.col.lane_width"},
    {"key": "shoulder_width", "kind": "number", "editable": False, "label_key": "facility.col.shoulder_width"},
    {"key": "access_point_density", "kind": "number", "editable": False, "label_key": "facility.col.access_density"},
    {"key": "passing_lane_role", "kind": "locked_choice", "editable": False, "label_key": "facility.col.passing_role"},
)


class MultilaneWorkflow:
    """Application service for the bounded Multilane Highway Segment."""

    method_id = "multilane_segment"

    def __init__(self) -> None:
        self.definition = _definition(self.method_id)

    def templates(self) -> dict[str, Any]:
        return {
            "method_id": self.method_id,
            "unit_systems": ["metric", "imperial"],
            "templates": [
                {"template_id": key, "label": label}
                for key, label in multilane_template_options(include_blank=True).items()
            ],
            "fields": [deepcopy(field) for field in MULTILANE_FIELD_SCHEMA],
            "branches": {
                "ffs": ["estimated", "measured"],
                "heavy_vehicle_adjustment": sorted(HEAVY_VEHICLE_ADJUSTMENT_METHODS),
                "median": ["twltl", "divided"],
            },
        }

    def starting_values(self, template_id: str, unit_system: str) -> dict[str, Any]:
        unit_system = _normalize_unit_system(unit_system)
        try:
            template = load_multilane_template(template_id)
            displayed = (
                multilane_blank_ui_inputs()
                if template_id == "blank_custom"
                else multilane_engine_inputs_to_ui(template["inputs"], unit_system)
            )
            # Older qualified templates omit this UI-only discriminator and
            # rely on the adapter's estimated-FFS default.  Surface that
            # default explicitly so the React branch controls reflect the
            # actual submitted path instead of appearing unselected.
            displayed.setdefault("ffs_source", "estimated")
            displayed["heavy_vehicle_adjustment_method"] = heavy_vehicle_adjustment_method_from_ui_inputs(displayed)
        except Exception as exc:
            if isinstance(exc, ApplicationWorkflowError):
                raise
            raise ApplicationWorkflowError(
                str(exc),
                code="invalid_template",
                message_key="api.invalid_template",
                details={"template_id": template_id},
            ) from exc
        return _json_ready(
            {
                "method_id": self.method_id,
                "template_id": template_id,
                "template_label": template["template_label"],
                "template_description": template["description"],
                "validation_status": template["validation_status"],
                "unit_system": unit_system,
                "displayed_inputs": displayed,
                "fields": [deepcopy(field) for field in MULTILANE_FIELD_SCHEMA],
                "scope_notes": [
                    "Python remains the sole HCM calculation authority.",
                    "Metric values are converted at the application boundary; the engine remains Imperial-native.",
                    "Blank is a worksheet starter and is not a validation fixture.",
                ],
            }
        )

    def _normalized(
        self,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        unit_system = _normalize_unit_system(unit_system)
        if not isinstance(displayed_inputs, Mapping):
            raise ApplicationWorkflowError(
                "displayed_inputs must be an object.",
                details={"field": "displayed_inputs"},
            )
        try:
            template_inputs = load_multilane_template(template_id)["inputs"]
            normalized = multilane_ui_inputs_to_engine(
                dict(displayed_inputs), template_inputs, unit_system
            )
            reject_unsupported_scope_keys(normalized)
            parsed = MultilaneBasicSegmentInputs.from_mapping(normalized)
            validate_inputs(parsed)
            return _json_ready(normalized)
        except ApplicationWorkflowError:
            raise
        except Exception as exc:
            raise ApplicationWorkflowError(
                str(exc),
                code="unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "invalid_input",
                message_key="api.unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "api.invalid_input",
            ) from exc

    def validate(
        self,
        *,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        try:
            normalized = self._normalized(template_id, unit_system, displayed_inputs)
        except Exception as exc:
            issue = _error_issue(exc)
            return {
                "method_id": self.method_id,
                "template_id": template_id,
                "unit_system": str(unit_system).lower(),
                "valid": False,
                "ready": False,
                "validation_status": issue["code"],
                "errors": [issue],
                "displayed_inputs": deepcopy(dict(displayed_inputs)) if isinstance(displayed_inputs, Mapping) else {},
                "normalized_inputs": None,
                "calculation_state": {"presentation_state": ResultPresentationState.INVALID_INPUT.value, "has_result": False, "warnings": []},
            }
        snapshot = _snapshot(
            self.definition,
            template_id=template_id,
            unit_system=_normalize_unit_system(unit_system),
            displayed_inputs=displayed_inputs,
            normalized_inputs=normalized,
        )
        return _json_ready(
            {
                **snapshot,
                "valid": True,
                "ready": True,
                "validation_status": "valid",
                "errors": [],
                "calculation_state": {
                    "presentation_state": ResultPresentationState.PRERUN.value,
                    "calculation_fingerprint": snapshot["calculation_fingerprint"],
                    "has_result": False,
                    "warnings": [],
                },
            }
        )

    def calculate(
        self,
        *,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        normalized = self._normalized(template_id, unit_system, displayed_inputs)
        normalized_unit = _normalize_unit_system(unit_system)
        snapshot = _snapshot(
            self.definition,
            template_id=template_id,
            unit_system=normalized_unit,
            displayed_inputs=displayed_inputs,
            normalized_inputs=normalized,
        )
        try:
            engine_result = run_manual_multilane(normalized)
            result = result_to_dict(engine_result)
        except Exception as exc:
            raise ApplicationWorkflowError(
                str(exc),
                code="unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "invalid_input",
                message_key="api.unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "api.invalid_input",
            ) from exc
        outputs = result["outputs"]
        capacity_failure = _capacity_failure(result)
        warnings = tuple(result.get("warnings", []))
        state = resolve_result_presentation_state(
            freshness=READY,
            has_result=True,
            warnings=warnings,
            capacity_failure=capacity_failure,
        )
        displayed_outputs = multilane_display_outputs(outputs, normalized_unit)
        metric_values = [
            _available_metric("density", displayed_outputs["density"]["value"], displayed_outputs["density"]["unit"], source="HCM Eq. 12-11", capacity_failure=capacity_failure),
            _available_metric("speed_used_for_density", displayed_outputs["speed_used_for_density"]["value"], displayed_outputs["speed_used_for_density"]["unit"], source="HCM Eq. 12-1", capacity_failure=capacity_failure),
            _available_metric("adjusted_free_flow_speed", displayed_outputs["adjusted_free_flow_speed"]["value"], displayed_outputs["adjusted_free_flow_speed"]["unit"], source="HCM Eq. 12-3", capacity_failure=capacity_failure),
            _available_metric("base_free_flow_speed", displayed_outputs["base_free_flow_speed"]["value"], displayed_outputs["base_free_flow_speed"]["unit"], source="HCM Exhibit 12-18", capacity_failure=capacity_failure),
            _available_metric("demand_flow_rate", displayed_outputs["demand_flow_rate"]["value"], displayed_outputs["demand_flow_rate"]["unit"], source="HCM Eq. 12-9", capacity_failure=capacity_failure),
        ]
        capacity = {
            "status": outputs.get("capacity_status", outputs.get("capacity_check")),
            "failure": capacity_failure,
            "demand_flow_rate": outputs.get("demand_flow_rate_pc_h_ln"),
            "capacity": outputs.get("capacity_pc_h_ln"),
            "demand_capacity_ratio": outputs.get("demand_capacity_ratio"),
            "source": "HCM Eq. 12-7 and capacity check",
        }
        interpretation_codes: tuple[InterpretationCode, ...] = (
            () if capacity_failure else (InterpretationCode.CAPACITY_BELOW_LIMIT,)
        )
        presentation = {
            "answer": {
                "key": "level_of_service",
                "value": outputs.get("level_of_service"),
                "available": outputs.get("level_of_service") is not None,
                "source": "HCM Exhibit 12-15",
            },
            "metrics": metric_values,
            "capacity": capacity,
            "interpretations": _interpretation_mappings(state, warning_codes=interpretation_codes),
            "evidence": {
                "intermediate_values": result.get("intermediate_values", []),
                "source_references": outputs.get("source_references", []),
                "assumptions": result.get("assumptions", []),
                "warnings": list(warnings),
            },
            "workflow": {
                "adjustment_method": heavy_vehicle_adjustment_method_from_ui_inputs(displayed_inputs),
                "ffs_source": outputs.get("ffs_source"),
                "speed_flow_branch": outputs.get("speed_flow_branch"),
                "pce_source": outputs.get("pce_source"),
            },
        }
        audit = build_manual_multilane_audit_record(
            template_id,
            normalized,
            unit_system=normalized_unit,
            displayed_inputs=dict(displayed_inputs),
            result=engine_result,
        )
        return _result_envelope(
            self.definition,
            snapshot=snapshot,
            result=result,
            state=state,
            presentation=presentation,
            audit=audit,
        )


class FacilityWorkflow:
    """Application service for the bounded Example 3/4 Two-Lane Facility."""

    method_id = "two_lane_facility"

    def __init__(self) -> None:
        self.definition = _definition(self.method_id)

    def templates(self) -> dict[str, Any]:
        options = [
            {"template_id": template_id, "label": label}
            for template_id, label in facility_template_options().items()
        ]
        return {
            "method_id": self.method_id,
            "unit_systems": ["metric", "imperial"],
            "templates": options,
            "fields": [deepcopy(field) for field in FACILITY_FIELD_SCHEMA],
            "scope_notes": [
                "This Phase 2 prototype is bounded to validated Chapter 26 Example Problems 3 and 4.",
                "Locked geometry, terrain, curve, passing-lane, and downstream context remains template-controlled.",
                "Facility answer uses length-weighted Eq. 15-39 evidence; LOS letters are not averaged.",
            ],
        }

    def starting_values(self, template_id: str, unit_system: str) -> dict[str, Any]:
        unit_system = _normalize_unit_system(unit_system)
        try:
            template = load_facility_template(template_id, unit_system)
        except Exception as exc:
            raise ApplicationWorkflowError(
                str(exc),
                code="invalid_template",
                message_key="api.invalid_template",
                details={"template_id": template_id},
            ) from exc
        return _json_ready(
            {
                "method_id": self.method_id,
                "template_id": template_id,
                "template_label": template["template_label"],
                "template_source_reference": template["template_source_reference"],
                "template_basis": template["template_basis"],
                "supported_context": template["supported_context"],
                "safe_edit_summary": template["safe_edit_summary"],
                "locked_summary": template["locked_summary"],
                "unit_system": unit_system,
                "segments": template["segments"],
                "editable_fields": template["editable_fields"],
                "fields": [deepcopy(field) for field in FACILITY_FIELD_SCHEMA],
                "unsupported_behavior_notes": template["unsupported_behavior_notes"],
            }
        )

    def _locked_issues(
        self,
        template_id: str,
        unit_system: str,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        template = self.starting_values(template_id, unit_system)
        source_rows = template["segments"]
        editable = set(template["editable_fields"])
        if len(rows) != len(source_rows):
            return [{
                "code": "unsupported_scope",
                "field": "rows",
                "message": "The selected facility template requires its validated segment count and order.",
                "message_key": "api.unsupported_scope",
            }]
        issues: list[dict[str, Any]] = []
        allowed = {field["key"] for field in FACILITY_FIELD_SCHEMA} | {
            "horizontal_alignment_subsegments", "passing_lane", "downstream_affected"
        }
        for index, (row, source) in enumerate(zip(rows, source_rows), start=1):
            extras = sorted(set(row) - allowed)
            if extras:
                issues.append({
                    "code": "unsupported_scope",
                    "field": f"rows[{index - 1}]",
                    "message": f"Segment {index} contains unsupported field(s): {', '.join(extras)}.",
                    "message_key": "api.unsupported_scope",
                })
            for field, expected in source.items():
                if field in editable:
                    continue
                actual = row.get(field)
                if not _same_value(actual, expected):
                    issues.append({
                        "code": "unsupported_scope",
                        "field": f"rows[{index - 1}].{field}",
                        "message": f"Segment {index} field {field} is locked by the selected template.",
                        "message_key": "api.unsupported_scope",
                    })
        return issues

    def _normalized(
        self,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        unit_system = _normalize_unit_system(unit_system)
        if not isinstance(displayed_inputs, Mapping) or not isinstance(displayed_inputs.get("rows"), list):
            raise ApplicationWorkflowError(
                "displayed_inputs.rows must be an array.",
                details={"field": "displayed_inputs.rows"},
            )
        rows = canonicalize_manual_facility_rows(displayed_inputs["rows"])
        summary = validate_manual_facility_table(rows)
        if summary["blocking"]:
            code = "unsupported_scope" if summary["status"] == "unsupported_scope" else "invalid_input"
            raise ApplicationWorkflowError(
                " ".join(summary["messages"]),
                code=code,
                message_key=f"api.{code}",
                details={
                    "validation": summary,
                    "issues": [
                        {
                            **issue,
                            "code": code,
                            "message_key": f"api.{code}",
                        }
                        for issue in _facility_validation_issues(summary["messages"], rows)
                    ],
                },
            )
        lock_issues = self._locked_issues(template_id, unit_system, rows)
        if lock_issues:
            raise ApplicationWorkflowError(
                lock_issues[0]["message"],
                code="unsupported_scope",
                message_key="api.unsupported_scope",
                details={"issues": lock_issues},
            )
        try:
            normalized = build_manual_facility_inputs(template_id, rows, unit_system)
        except Exception as exc:
            raise ApplicationWorkflowError(
                str(exc),
                code="invalid_input",
                message_key="api.invalid_input",
            ) from exc
        return rows, _json_ready(normalized)

    def validate(
        self,
        *,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        try:
            rows, normalized = self._normalized(template_id, unit_system, displayed_inputs)
        except Exception as exc:
            details = getattr(exc, "details", {})
            issues = details.get("issues") or details.get("validation", {}).get("messages")
            if isinstance(issues, list) and issues and isinstance(issues[0], str):
                issues = [{"code": "invalid_input", "field": "rows", "message": item, "message_key": "api.invalid_input"} for item in issues]
            issue = _error_issue(exc)
            errors = issues if isinstance(issues, list) and issues else [issue]
            return {
                "method_id": self.method_id,
                "template_id": template_id,
                "unit_system": str(unit_system).lower(),
                "valid": False,
                "ready": False,
                "validation_status": issue["code"],
                "errors": errors,
                "displayed_inputs": deepcopy(dict(displayed_inputs)) if isinstance(displayed_inputs, Mapping) else {},
                "normalized_inputs": None,
                "calculation_state": {"presentation_state": ResultPresentationState.INVALID_INPUT.value, "has_result": False, "warnings": []},
            }
        snapshot = _snapshot(
            self.definition,
            template_id=template_id,
            unit_system=_normalize_unit_system(unit_system),
            displayed_inputs={"rows": rows},
            normalized_inputs=normalized,
        )
        return _json_ready(
            {
                **snapshot,
                "displayed_inputs": {"rows": rows},
                "valid": True,
                "ready": True,
                "validation_status": "valid",
                "errors": [],
                "calculation_state": {
                    "presentation_state": ResultPresentationState.PRERUN.value,
                    "calculation_fingerprint": snapshot["calculation_fingerprint"],
                    "has_result": False,
                    "warnings": [],
                },
            }
        )

    def calculate(
        self,
        *,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        rows, normalized = self._normalized(template_id, unit_system, displayed_inputs)
        normalized_unit = _normalize_unit_system(unit_system)
        snapshot = _snapshot(
            self.definition,
            template_id=template_id,
            unit_system=normalized_unit,
            displayed_inputs={"rows": rows},
            normalized_inputs=normalized,
        )
        try:
            engine_result = run_manual_facility(template_id, rows, normalized_unit)
            result = result_to_dict(engine_result)
        except Exception as exc:
            raise ApplicationWorkflowError(
                str(exc),
                code="unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "invalid_input",
                message_key="api.unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "api.invalid_input",
            ) from exc
        outputs = result["outputs"]
        capacity_failure = _capacity_failure(result)
        warnings = tuple(result.get("warnings", []))
        state = resolve_result_presentation_state(
            freshness=READY,
            has_result=True,
            warnings=warnings,
            capacity_failure=capacity_failure,
        )
        metric_factor = MILES_TO_KILOMETERS if normalized_unit == "metric" else 1.0
        density_factor = 1.0 / MILES_TO_KILOMETERS if normalized_unit == "metric" else 1.0
        segment_rows = []
        for row in facility_segment_result_rows(engine_result, rows):
            segment_rows.append(
                {
                    **row,
                    "segment_length": row["segment_length_mi"] * metric_factor,
                    "segment_length_unit": "km" if normalized_unit == "metric" else "mi",
                    "average_speed": row["average_speed_mph"] * metric_factor,
                    "average_speed_unit": "km/h" if normalized_unit == "metric" else "mph",
                    "follower_density": row["follower_density_followers_mi_ln"] * density_factor,
                    "follower_density_unit": "fol/km/ln" if normalized_unit == "metric" else "fol/mi/ln",
                }
            )
        presentation = {
            "answer": {
                "key": "facility_level_of_service",
                "value": outputs.get("facility_level_of_service"),
                "available": outputs.get("facility_level_of_service") is not None,
                "source": "HCM7 Exhibit 15-6 using facility density",
            },
            "metrics": [
                _available_metric("facility_length", outputs.get("facility_length_mi", 0.0) * metric_factor, "km" if normalized_unit == "metric" else "mi", source="HCM Eq. 15-39"),
                _available_metric("facility_average_speed", _scale_optional(outputs.get("facility_average_speed_mph"), metric_factor), "km/h" if normalized_unit == "metric" else "mph", source="HCM Eq. 15-39", capacity_failure=capacity_failure),
                _available_metric("facility_density", _scale_optional(outputs.get("facility_follower_density_followers_mi_ln"), density_factor), "fol/km/ln" if normalized_unit == "metric" else "fol/mi/ln", source="HCM Eq. 15-39", capacity_failure=capacity_failure),
                _available_metric("facility_percent_followers", outputs.get("facility_percent_followers"), "%", source="HCM Eq. 15-39", capacity_failure=capacity_failure),
            ],
            "capacity": {
                "status": "capacity_failure" if capacity_failure else "within_capacity",
                "failure": capacity_failure,
                "critical_segment_id": outputs.get("critical_segment_id"),
                "source": "HCM Chapter 15 capacity checks",
            },
            "segments": segment_rows,
            "interpretations": _interpretation_mappings(
                state,
                warning_codes=(
                    InterpretationCode.FACILITY_LENGTH_WEIGHTED,
                    InterpretationCode.FACILITY_CRITICAL_SEGMENT,
                ) + (() if capacity_failure else (InterpretationCode.CAPACITY_BELOW_LIMIT,)),
            ),
            "evidence": {
                "intermediate_values": result.get("intermediate_values", []),
                "step_11_weighting": outputs.get("step_11_weighting"),
                "source_references": [
                    "HCM Eq. 15-39",
                    "HCM7 Exhibit 15-6",
                ],
                "assumptions": result.get("assumptions", []),
                "warnings": list(warnings),
            },
        }
        audit = build_manual_facility_audit_record(
            template_id,
            rows,
            normalized_unit,
            result=engine_result,
        )
        return _result_envelope(
            self.definition,
            snapshot=snapshot,
            result=result,
            state=state,
            presentation=presentation,
            audit=audit,
        )


def _same_value(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-7)
    return left == right


def _facility_validation_issues(messages: list[str], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach stable row/cell paths to the existing facility messages."""

    fields = (
        "segment_id", "segment_name", "segment_type", "segment_length",
        "posted_speed", "analysis_direction_volume_veh_h",
        "opposing_direction_volume_veh_h", "peak_hour_factor",
        "heavy_vehicle_percent", "terrain_type", "grade_percent",
        "horizontal_alignment", "lane_width", "shoulder_width",
        "access_point_density", "passing_lane_role",
    )
    issues: list[dict[str, Any]] = []
    for message in messages:
        match = re.match(r"Segment(?: row)? ([^:]+):\s*(.*)", message)
        field: str | None = None
        target: str | None = None
        if match:
            segment_label, detail = match.groups()
            row_index = next(
                (
                    index
                    for index, row in enumerate(rows)
                    if str(row.get("segment_id", index + 1)) == segment_label
                ),
                None,
            )
            if row_index is None and segment_label.isdigit():
                candidate_index = int(segment_label) - 1
                if 0 <= candidate_index < len(rows):
                    row_index = candidate_index
            if "missing required field(s):" in detail:
                field = detail.split("missing required field(s):", 1)[1].split(",", 1)[0].strip()
            else:
                field = next((candidate for candidate in fields if candidate in detail), None)
            if field is None and "Passing Lane" in detail:
                field = "segment_type"
            if row_index is not None and field in fields:
                target = f"rows[{row_index}].{field}"
        issues.append({
            "code": "invalid_input",
            "field": target,
            "message": message,
            "message_key": "api.invalid_input",
        })
    return issues


def workflow_for_method(method_id: str) -> Any:
    if method_id == "multilane_segment":
        return MultilaneWorkflow()
    if method_id == "two_lane_facility":
        return FacilityWorkflow()
    if method_id in PHASE3_METHOD_IDS:
        from hcmcalc.application.phase3_workflows import Phase3Workflow

        return Phase3Workflow(method_id)
    _definition(method_id)
    raise AssertionError("unreachable")


def normalized_workflow_inputs(
    method_id: str,
    *,
    template_id: str,
    unit_system: str,
    displayed_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize a delivered workflow without invoking its HCM engine.

    Project persistence uses this seam to reconstruct server-side numeric
    types after a browser JSON round trip. JavaScript represents integral
    floats and integers with the same ``Number`` type, while the established
    Python fingerprint contract distinguishes their JSON spellings. The
    workflow adapter remains the authority for recovering canonical inputs;
    this helper never calculates a result.
    """

    workflow = workflow_for_method(method_id)
    if isinstance(workflow, MultilaneWorkflow):
        return workflow._normalized(template_id, unit_system, displayed_inputs)
    if isinstance(workflow, FacilityWorkflow):
        return workflow._normalized(template_id, unit_system, displayed_inputs)[1]
    return workflow._normalized(template_id, unit_system, displayed_inputs)


def validate_workflow_request(
    method_id: str,
    *,
    template_id: str,
    unit_system: str,
    displayed_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    return workflow_for_method(method_id).validate(
        template_id=template_id,
        unit_system=unit_system,
        displayed_inputs=displayed_inputs,
    )


def calculate_workflow_request(
    method_id: str,
    *,
    template_id: str,
    unit_system: str,
    displayed_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    return workflow_for_method(method_id).calculate(
        template_id=template_id,
        unit_system=unit_system,
        displayed_inputs=displayed_inputs,
    )


def workflow_templates(method_id: str) -> dict[str, Any]:
    return workflow_for_method(method_id).templates()


def workflow_starting_values(method_id: str, template_id: str, unit_system: str) -> dict[str, Any]:
    return workflow_for_method(method_id).starting_values(template_id, unit_system)


def export_current_workflow(
    method_id: str,
    *,
    template_id: str,
    unit_system: str,
    displayed_inputs: Mapping[str, Any],
    calculation_fingerprint: str,
    input_snapshot_fingerprint: str,
    result: Mapping[str, Any],
    export_format: str,
) -> dict[str, Any]:
    """Export a supplied current result without executing an HCM method."""

    workflow = workflow_for_method(method_id)
    if export_format not in SUPPORTED_WORKFLOW_EXPORTS:
        raise ApplicationWorkflowError(
            f"Unsupported export format: {export_format}.",
            code="unsupported_export_format",
            message_key="api.unsupported_export_format",
        )
    if not isinstance(result, Mapping) or not isinstance(result.get("outputs"), Mapping):
        raise ApplicationWorkflowError(
            "A calculated result is required for export.",
            code="result_required",
            message_key="api.result_required",
        )
    if isinstance(workflow, MultilaneWorkflow):
        normalized = workflow._normalized(template_id, unit_system, displayed_inputs)  # type: ignore[attr-defined]
        effective_displayed = displayed_inputs
    elif isinstance(workflow, FacilityWorkflow):
        rows, normalized = workflow._normalized(template_id, unit_system, displayed_inputs)  # type: ignore[attr-defined]
        effective_displayed = {"rows": rows}
    else:
        normalized = workflow._normalized(template_id, unit_system, displayed_inputs)  # type: ignore[attr-defined]
        effective_displayed = displayed_inputs
    snapshot = _snapshot(
        workflow.definition,
        template_id=template_id,
        unit_system=_normalize_unit_system(unit_system),
        displayed_inputs=effective_displayed,
        normalized_inputs=normalized,
    )
    if str(calculation_fingerprint) != snapshot["calculation_fingerprint"]:
        raise StaleResultError()
    if str(input_snapshot_fingerprint) != snapshot["input_snapshot_fingerprint"]:
        raise StaleResultError("The supplied result is not current for these displayed inputs.")
    if result.get("method") != workflow.definition.engine_method_identifier:
        raise StaleResultError("The supplied result method identity does not match the worksheet.")
    try:
        report = build_report(
            workflow.definition.project_type,
            dict(result),
            _normalize_unit_system(unit_system),
            inputs=dict(normalized),
            template_id=template_id,
            generated_at=_now(),
        )
        rendered = export_report(report, export_format)
    except Exception as exc:
        raise ApplicationWorkflowError(
            str(exc),
            code="export_failed",
            message_key="api.export_failed",
        ) from exc
    extension = "md" if export_format == "markdown" else export_format
    content: str | None = rendered if isinstance(rendered, str) else None
    encoded: str | None = None if content is not None else base64.b64encode(rendered).decode("ascii")
    return {
        "export_format": export_format,
        "filename": report_filename(report, extension),
        "content": content,
        "content_base64": encoded,
        "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if export_format == "xlsx" else "text/markdown" if export_format == "markdown" else "text/csv" if export_format == "csv" else "application/json",
        "calculation_fingerprint": snapshot["calculation_fingerprint"],
        "recalculated": False,
    }
