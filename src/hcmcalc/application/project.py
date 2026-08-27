"""Project v2 persistence and scenario operations.

This module is intentionally storage-agnostic.  A project is a JSON document
that can be downloaded or opened by the browser; there is no database and no
serialized presentation object is treated as engineering authority.  Loading
validates identity and fingerprints only.  It never invokes an HCM engine.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from numbers import Real
from typing import Any, Mapping
from uuid import uuid4

from hcmcalc.application.registry import get_analysis_definition
from hcmcalc.application.workflow_state import calculation_input_fingerprint, snapshot_input_fingerprint


PROJECT_SCHEMA_VERSION = "2.0"
LEGACY_PROJECT_SCHEMA_VERSIONS = frozenset({"1.0", "1.1", "1.2"})


class ProjectFileError(ValueError):
    """Raised when a project document cannot be safely loaded or saved."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _json_ready(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ProjectFileError(f"Project contains a non-JSON value: {exc}") from exc


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectFileError(f"{field} must be a nonempty string.")
    return value


def _required_keys(value: Mapping[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    if missing:
        raise ProjectFileError(f"{label} requires: {', '.join(missing)}.")


def _reject_unknown(value: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ProjectFileError(
            f"{label} contains unsupported field(s): {', '.join(unknown)}."
        )


def _identity_fingerprint(
    method_identifier: str,
    input_contract: str,
    normalized_inputs: Mapping[str, Any],
) -> str:
    return calculation_input_fingerprint(
        method_identifier, input_contract, normalized_inputs
    )


def _snapshot_fingerprint(
    method_identifier: str,
    input_contract: str,
    displayed_inputs: Mapping[str, Any],
    normalized_inputs: Mapping[str, Any],
) -> str:
    return snapshot_input_fingerprint(
        method_identifier,
        input_contract,
        displayed_inputs,
        normalized_inputs,
    )


def _semantically_equal(left: Any, right: Any) -> bool:
    """Compare JSON values while treating browser numeric types equivalently."""

    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if isinstance(left, Real) and isinstance(right, Real):
        return float(left) == float(right)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(
            _semantically_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _semantically_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return left == right


def _canonical_project_normalized_inputs(
    *,
    method_id: str,
    template_id: Any,
    unit_system: Any,
    displayed_inputs: Mapping[str, Any],
    supplied_normalized_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Recover canonical adapter numeric types for delivered Phase 2 methods."""

    if (
        method_id not in {"multilane_segment", "two_lane_facility"}
        or not isinstance(template_id, str)
        or not template_id
        or template_id == "legacy_import"
    ):
        return deepcopy(dict(supplied_normalized_inputs))
    try:
        from hcmcalc.application.workflows import normalized_workflow_inputs

        canonical = normalized_workflow_inputs(
            method_id,
            template_id=template_id,
            unit_system=str(unit_system),
            displayed_inputs=displayed_inputs,
        )
    except Exception as exc:
        raise ProjectFileError(
            f"Project inputs are not valid for the selected workflow: {exc}"
        ) from exc
    if not _semantically_equal(canonical, supplied_normalized_inputs):
        raise ProjectFileError("Project normalized inputs do not match displayed workflow inputs.")
    return deepcopy(canonical)


def new_project(project_name: str = "Untitled HCM study") -> dict[str, Any]:
    """Create an empty Project v2 document with stable IDs."""

    timestamp = _now()
    return {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "project_id": _new_id("project"),
        "project_name": _require_text(project_name, "project_name"),
        "created_at": timestamp,
        "updated_at": timestamp,
        "locale": "en",
        "analyses": [],
    }


def add_analysis(
    project: Mapping[str, Any],
    *,
    method_id: str,
    scenario_name: str = "Base",
    analysis_name: str | None = None,
    snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Add an analysis and its independent Base scenario to a project."""

    document = _validated_copy(project)
    definition = get_analysis_definition(method_id)
    if definition is None:
        raise ProjectFileError(f"Unknown method_id: {method_id}.")
    scenario = _scenario_from_snapshot(
        definition,
        scenario_name=scenario_name,
        snapshot=snapshot,
        kind="base",
    )
    analysis = {
        "analysis_id": _new_id("analysis"),
        "analysis_name": analysis_name or definition.method_id,
        "method_id": definition.method_id,
        "method_identifier": definition.method_identifier,
        "engine_method_identifier": definition.engine_method_identifier,
        "method_version": definition.method_version,
        "input_contract": definition.input_contract,
        "project_type": definition.project_type,
        "hcm_edition": definition.hcm_edition,
        "hcm_chapter": definition.hcm_chapter,
        "scenarios": [scenario],
    }
    document["analyses"].append(analysis)
    document["updated_at"] = _now()
    return _json_ready(document)


def save_analysis_to_project(
    snapshot: Mapping[str, Any],
    *,
    project_name: str = "Untitled HCM study",
    analysis_name: str | None = None,
    scenario_name: str = "Base",
) -> dict[str, Any]:
    """Create a project containing a Quick Analysis snapshot.

    The snapshot may contain an ephemeral ``presentation`` mapping from the
    API response; only method/input identity, auditable result, assumptions,
    warnings, and audit data are persisted.
    """

    method_id = _require_text(snapshot.get("method_id"), "snapshot.method_id")
    document = add_analysis(
        new_project(project_name),
        method_id=method_id,
        scenario_name=scenario_name,
        analysis_name=analysis_name,
        snapshot=snapshot,
    )
    if isinstance(snapshot.get("result"), Mapping):
        analysis_id = document["analyses"][0]["analysis_id"]
        scenario_id = document["analyses"][0]["scenarios"][0]["scenario_id"]
        document = record_result(
            document,
            analysis_id=analysis_id,
            scenario_id=scenario_id,
            snapshot=snapshot,
        )
    return _json_ready(document)


def duplicate_scenario(
    project: Mapping[str, Any],
    *,
    analysis_id: str,
    scenario_id: str,
    scenario_name: str,
) -> dict[str, Any]:
    """Duplicate a scenario as an independently recalculable scenario."""

    document = _validated_copy(project)
    analysis = _find_analysis(document, analysis_id)
    source = _find_scenario(analysis, scenario_id)
    if not str(scenario_name).strip():
        raise ProjectFileError("scenario_name must be a nonempty string.")
    duplicate = deepcopy(source)
    duplicate["scenario_id"] = _new_id("scenario")
    duplicate["scenario_name"] = str(scenario_name).strip()
    duplicate["kind"] = "duplicate"
    duplicate["duplicated_from_scenario_id"] = source["scenario_id"]
    duplicate["result"] = None
    duplicate["result_status"] = "not_calculated"
    analysis["scenarios"].append(duplicate)
    document["updated_at"] = _now()
    return _json_ready(document)


def rename_scenario(
    project: Mapping[str, Any],
    *,
    analysis_id: str,
    scenario_id: str,
    scenario_name: str,
) -> dict[str, Any]:
    document = _validated_copy(project)
    scenario = _find_scenario(_find_analysis(document, analysis_id), scenario_id)
    if not str(scenario_name).strip():
        raise ProjectFileError("scenario_name must be a nonempty string.")
    scenario["scenario_name"] = str(scenario_name).strip()
    document["updated_at"] = _now()
    return _json_ready(document)


def update_scenario_inputs(
    project: Mapping[str, Any],
    *,
    analysis_id: str,
    scenario_id: str,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Replace scenario inputs and discard a result whose identity is stale."""

    document = _validated_copy(project)
    analysis = _find_analysis(document, analysis_id)
    scenario = _find_scenario(analysis, scenario_id)
    _apply_snapshot_identity(analysis, scenario, snapshot)
    scenario["result"] = None
    scenario["result_status"] = "stale"
    document["updated_at"] = _now()
    return _json_ready(document)


def record_result(
    project: Mapping[str, Any],
    *,
    analysis_id: str,
    scenario_id: str,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Retain a result only when its method and input identities match."""

    document = _validated_copy(project)
    analysis = _find_analysis(document, analysis_id)
    scenario = _find_scenario(analysis, scenario_id)
    _apply_snapshot_identity(analysis, scenario, snapshot)
    stored_result = snapshot.get("result")
    if not isinstance(stored_result, Mapping):
        raise ProjectFileError("A calculated result is required to retain a scenario result.")
    if stored_result.get("method") != analysis["engine_method_identifier"]:
        raise ProjectFileError("Result method identity does not match the analysis.")
    if snapshot.get("calculation_fingerprint") != scenario["calculation_fingerprint"]:
        raise ProjectFileError("Result fingerprint does not match the scenario inputs.")
    scenario["result"] = {
        "result_id": _new_id("result"),
        "method_identifier": analysis["method_identifier"],
        "engine_method_identifier": analysis["engine_method_identifier"],
        "method_version": analysis["method_version"],
        "input_contract": analysis["input_contract"],
        "calculation_fingerprint": scenario["calculation_fingerprint"],
        "input_snapshot_fingerprint": scenario["input_snapshot_fingerprint"],
        "engine_result": deepcopy(dict(stored_result)),
        "warnings": deepcopy(stored_result.get("warnings", [])),
        "assumptions": deepcopy(stored_result.get("assumptions", [])),
        "audit": deepcopy(snapshot.get("audit", {})),
        "stored_at": _now(),
    }
    scenario["result_status"] = "current"
    document["updated_at"] = _now()
    return _json_ready(document)


def compare_scenarios(
    project: Mapping[str, Any],
    *,
    analysis_id: str,
    left_scenario_id: str,
    right_scenario_id: str,
) -> dict[str, Any]:
    """Compare two current, compatible scenarios without recalculating."""

    document = _validated_copy(project)
    analysis = _find_analysis(document, analysis_id)
    left = _find_scenario(analysis, left_scenario_id)
    right = _find_scenario(analysis, right_scenario_id)
    if left["scenario_id"] == right["scenario_id"]:
        raise ProjectFileError("Compare requires two different scenarios.")
    _require_current_result(left)
    _require_current_result(right)
    left_result = left["result"]["engine_result"]
    right_result = right["result"]["engine_result"]
    if left_result.get("method") != right_result.get("method"):
        raise ProjectFileError("Scenario result methods are not compatible.")

    left_outputs = left_result.get("outputs", {})
    right_outputs = right_result.get("outputs", {})
    numeric_deltas: list[dict[str, Any]] = []
    for key in _comparison_keys(left_outputs, right_outputs):
        left_value = left_outputs.get(key)
        right_value = right_outputs.get(key)
        if isinstance(left_value, Real) and not isinstance(left_value, bool) and isinstance(right_value, Real) and not isinstance(right_value, bool):
            delta = float(right_value) - float(left_value)
            if abs(delta) > 1e-12:
                numeric_deltas.append({
                    "key": key,
                    "left": float(left_value),
                    "right": float(right_value),
                    "delta": delta,
                })
    left_los = _los_value(left_outputs)
    right_los = _los_value(right_outputs)
    return _json_ready(
        {
            "analysis_id": analysis_id,
            "method_id": analysis["method_id"],
            "method_identifier": analysis["method_identifier"],
            "input_contract": analysis["input_contract"],
            "current_only": True,
            "recalculated": False,
            "left": {
                "scenario_id": left["scenario_id"],
                "scenario_name": left["scenario_name"],
                "calculation_fingerprint": left["calculation_fingerprint"],
                "level_of_service": left_los,
            },
            "right": {
                "scenario_id": right["scenario_id"],
                "scenario_name": right["scenario_name"],
                "calculation_fingerprint": right["calculation_fingerprint"],
                "level_of_service": right_los,
            },
            "los_grade_transition": {
                "from": left_los,
                "to": right_los,
                "changed": left_los != right_los,
            },
            "numeric_deltas": numeric_deltas,
        }
    )


def project_to_json(project: Mapping[str, Any]) -> str:
    """Validate and serialize a deterministic Project v2 document."""

    return json.dumps(_validated_copy(project), indent=2, sort_keys=True) + "\n"


def load_project(data: str | bytes | Mapping[str, Any]) -> dict[str, Any]:
    """Load Project v2 or migrate a legacy 1.x manual project without rerun."""

    if isinstance(data, Mapping):
        payload = deepcopy(dict(data))
    else:
        try:
            payload = json.loads(data)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ProjectFileError(f"Project JSON is malformed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProjectFileError("Project document must be a JSON object.")
    version = payload.get("schema_version")
    if version == PROJECT_SCHEMA_VERSION:
        return _validated_copy(payload)
    if version in LEGACY_PROJECT_SCHEMA_VERSIONS:
        return migrate_legacy_project(payload)
    if isinstance(version, str) and version.startswith("2."):
        raise ProjectFileError(
            f"Project schema {version} is newer than supported schema {PROJECT_SCHEMA_VERSION}."
        )
    raise ProjectFileError(
        f"Unsupported project schema_version {version!r}; expected {PROJECT_SCHEMA_VERSION} or a supported legacy 1.x document."
    )


def migrate_legacy_project(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Map legacy 1.0/1.1/1.2 manual payloads into the Project v2 graph."""

    project_type = payload.get("project_type")
    mapping = {
        "manual_multilane_v0": "multilane_segment",
        "manual_two_lane_facility_v1": "two_lane_facility",
        "manual_facility_v0": "two_lane_facility",
        "manual_single_segment": "two_lane_segment",
        "manual_basic_freeway_v0": "basic_freeway_segment",
        "manual_freeway_weaving_segment_v1": "weaving_segment",
        "manual_freeway_merge_segment_v1": "merge_segment",
        "manual_freeway_diverge_segment_v1": "diverge_segment",
    }
    method_id = mapping.get(project_type)
    if method_id is None:
        raise ProjectFileError(f"Legacy project_type is not supported: {project_type!r}.")
    definition = get_analysis_definition(method_id)
    if definition is None:
        raise ProjectFileError(f"Legacy method is not registered: {method_id}.")

    displayed, normalized, stored_result, audit = _legacy_parts(payload, project_type)
    if not isinstance(displayed, Mapping):
        displayed = {}
    if not isinstance(normalized, Mapping):
        normalized = {}
    document = new_project(str(payload.get("project_name") or payload.get("facility_name") or "Migrated HCM study"))
    document["locale"] = (payload.get("presentation") or {}).get("locale", "en") if isinstance(payload.get("presentation"), Mapping) else "en"
    snapshot = {
        "method_id": method_id,
        "method_identifier": definition.method_identifier,
        "engine_method_identifier": definition.engine_method_identifier,
        "method_version": definition.method_version,
        "input_contract": definition.input_contract,
        "project_type": definition.project_type,
        "template_id": payload.get("template_id") or payload.get("template") or "legacy_import",
        "unit_system": payload.get("unit_system") or "imperial",
        "displayed_inputs": deepcopy(dict(displayed)),
        "normalized_inputs": deepcopy(dict(normalized)),
        "calculation_fingerprint": _identity_fingerprint(definition.method_identifier, definition.input_contract, normalized),
        "input_snapshot_fingerprint": _snapshot_fingerprint(definition.method_identifier, definition.input_contract, displayed, normalized),
        "result": stored_result if isinstance(stored_result, Mapping) else None,
        "audit": audit if isinstance(audit, Mapping) else {},
    }
    document = add_analysis(
        document,
        method_id=method_id,
        scenario_name="Migrated legacy Base",
        analysis_name=str(payload.get("analysis_name") or method_id),
        snapshot=snapshot,
    )
    analysis_id = document["analyses"][0]["analysis_id"]
    scenario_id = document["analyses"][0]["scenarios"][0]["scenario_id"]
    scenario = document["analyses"][0]["scenarios"][0]
    # Legacy calculation fingerprints are retained only when their normalized
    # identity and engine method match.  No engine is called during import.
    computed = _identity_fingerprint(definition.method_identifier, definition.input_contract, normalized)
    stored_fp = payload.get("calculation_fingerprint")
    engine_result = stored_result if isinstance(stored_result, Mapping) else None
    retained = bool(
        engine_result
        and (stored_fp is None or stored_fp == computed)
        and engine_result.get("method") == definition.engine_method_identifier
    )
    if retained:
        snapshot["calculation_fingerprint"] = computed
        document = record_result(
            document,
            analysis_id=analysis_id,
            scenario_id=scenario_id,
            snapshot=snapshot,
        )
    else:
        scenario["result"] = None
        scenario["result_status"] = "stale" if engine_result else "not_calculated"
    document["migration"] = {
        "source_schema_version": payload.get("schema_version"),
        "status": "migrated_legacy",
        "result_status": "retained_current" if retained else "discarded_stale_or_missing",
    }
    document["updated_at"] = _now()
    return _json_ready(document)


def _legacy_parts(payload: Mapping[str, Any], project_type: Any) -> tuple[Any, Any, Any, Any]:
    if project_type == "manual_multilane_v0":
        return (
            payload.get("displayed_ui_inputs", {}),
            payload.get("normalized_engine_inputs", {}),
            payload.get("calculation_result") or payload.get("result"),
            payload.get("audit") or payload.get("audit_record"),
        )
    if project_type in {"manual_two_lane_facility_v1", "manual_facility_v0"}:
        displayed = payload.get("segment_rows")
        if displayed is None and isinstance(payload.get("facility_inputs"), Mapping):
            displayed = payload["facility_inputs"].get("segments")
        normalized = payload.get("normalized_facility_inputs")
        if normalized is None:
            normalized = {
                "segments": payload.get("normalized_segment_inputs", []),
                "facility_id": payload.get("template_id") or "legacy_import",
            }
        return (
            {"rows": displayed or []},
            normalized,
            payload.get("calculation_result") or payload.get("result"),
            payload.get("audit_record") or payload.get("audit"),
        )
    return (
        payload.get("manual_inputs", {}),
        payload.get("normalized_engine_inputs", {}),
        payload.get("result"),
        payload.get("audit_record"),
    )


def _scenario_from_snapshot(
    definition: Any,
    *,
    scenario_name: str,
    snapshot: Mapping[str, Any] | None,
    kind: str,
) -> dict[str, Any]:
    if not str(scenario_name).strip():
        raise ProjectFileError("scenario_name must be a nonempty string.")
    values = snapshot or {}
    displayed = values.get("displayed_inputs", {})
    normalized = values.get("normalized_inputs")
    if not isinstance(displayed, Mapping):
        raise ProjectFileError("snapshot.displayed_inputs must be an object.")
    if not isinstance(normalized, Mapping):
        normalized = {}
    method_identifier = values.get("method_identifier", definition.method_identifier)
    engine_method_identifier = values.get("engine_method_identifier", definition.engine_method_identifier)
    method_version = values.get("method_version", definition.method_version)
    input_contract = values.get("input_contract", definition.input_contract)
    project_type = values.get("project_type", definition.project_type)
    if (
        method_identifier != definition.method_identifier
        or engine_method_identifier != definition.engine_method_identifier
        or method_version != definition.method_version
        or input_contract != definition.input_contract
        or project_type != definition.project_type
    ):
        raise ProjectFileError("Snapshot method/input contract does not match the analysis.")
    normalized = _canonical_project_normalized_inputs(
        method_id=definition.method_id,
        template_id=values.get("template_id"),
        unit_system=values.get("unit_system", "imperial"),
        displayed_inputs=displayed,
        supplied_normalized_inputs=normalized,
    )
    calculation_fp = _identity_fingerprint(method_identifier, input_contract, normalized)
    snapshot_fp = _snapshot_fingerprint(method_identifier, input_contract, displayed, normalized)
    scenario: dict[str, Any] = {
        "scenario_id": _new_id("scenario"),
        "scenario_name": str(scenario_name).strip(),
        "kind": kind,
        "unit_system": values.get("unit_system", "imperial"),
        "template_id": values.get("template_id"),
        "displayed_inputs": deepcopy(dict(displayed)),
        "normalized_inputs": deepcopy(dict(normalized)),
        "calculation_fingerprint": calculation_fp,
        "input_snapshot_fingerprint": snapshot_fp,
        "result_status": "not_calculated",
        "result": None,
    }
    if values.get("calculation_fingerprint") not in (None, calculation_fp):
        raise ProjectFileError("Snapshot calculation fingerprint does not match normalized inputs.")
    if values.get("input_snapshot_fingerprint") not in (None, snapshot_fp):
        raise ProjectFileError("Snapshot input fingerprint does not match displayed inputs.")
    return scenario


def _apply_snapshot_identity(
    analysis: Mapping[str, Any], scenario: Mapping[str, Any], snapshot: Mapping[str, Any]
) -> None:
    if snapshot.get("method_id") not in (None, analysis["method_id"]):
        raise ProjectFileError("Snapshot method_id does not match the analysis.")
    if snapshot.get("method_identifier") not in (None, analysis["method_identifier"]):
        raise ProjectFileError("Snapshot method identifier does not match the analysis.")
    if snapshot.get("engine_method_identifier") not in (None, analysis["engine_method_identifier"]):
        raise ProjectFileError("Snapshot engine method identifier does not match the analysis.")
    if snapshot.get("method_version") not in (None, analysis["method_version"]):
        raise ProjectFileError("Snapshot method version does not match the analysis.")
    if snapshot.get("input_contract") not in (None, analysis["input_contract"]):
        raise ProjectFileError("Snapshot input contract does not match the analysis.")
    if snapshot.get("project_type") not in (None, analysis["project_type"]):
        raise ProjectFileError("Snapshot project type does not match the analysis.")
    displayed = snapshot.get("displayed_inputs")
    normalized = snapshot.get("normalized_inputs")
    if not isinstance(displayed, Mapping) or not isinstance(normalized, Mapping):
        raise ProjectFileError("Snapshot displayed_inputs and normalized_inputs are required objects.")
    unit_system = snapshot.get("unit_system", scenario.get("unit_system", "imperial"))
    template_id = snapshot.get("template_id", scenario.get("template_id"))
    normalized = _canonical_project_normalized_inputs(
        method_id=str(analysis["method_id"]),
        template_id=template_id,
        unit_system=unit_system,
        displayed_inputs=displayed,
        supplied_normalized_inputs=normalized,
    )
    scenario["unit_system"] = unit_system
    scenario["template_id"] = template_id
    scenario["displayed_inputs"] = deepcopy(dict(displayed))
    scenario["normalized_inputs"] = normalized
    scenario["calculation_fingerprint"] = _identity_fingerprint(analysis["method_identifier"], analysis["input_contract"], normalized)
    scenario["input_snapshot_fingerprint"] = _snapshot_fingerprint(analysis["method_identifier"], analysis["input_contract"], displayed, normalized)
    if snapshot.get("calculation_fingerprint") not in (None, scenario["calculation_fingerprint"]):
        raise ProjectFileError("Snapshot calculation fingerprint does not match normalized inputs.")
    if snapshot.get("input_snapshot_fingerprint") not in (None, scenario["input_snapshot_fingerprint"]):
        raise ProjectFileError("Snapshot input fingerprint does not match displayed inputs.")


def _validated_copy(project: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(project, Mapping):
        raise ProjectFileError("Project must be an object.")
    document = _json_ready(dict(project))
    _validate_v2(document)
    return document


def _validate_v2(document: Mapping[str, Any]) -> None:
    _reject_unknown(document, {"schema_version", "project_id", "project_name", "created_at", "updated_at", "locale", "analyses", "migration"}, "project")
    _required_keys(document, {"schema_version", "project_id", "project_name", "created_at", "updated_at", "locale", "analyses"}, "project")
    if document["schema_version"] != PROJECT_SCHEMA_VERSION:
        raise ProjectFileError(f"Expected Project schema {PROJECT_SCHEMA_VERSION}.")
    for field in ("project_id", "project_name", "created_at", "updated_at", "locale"):
        _require_text(document[field], f"project.{field}")
    if document["locale"] not in {"en", "th"}:
        raise ProjectFileError("project.locale must be en or th.")
    if not isinstance(document["analyses"], list):
        raise ProjectFileError("project.analyses must be an array.")
    analysis_ids: set[str] = set()
    for analysis in document["analyses"]:
        _validate_analysis(analysis)
        if analysis["analysis_id"] in analysis_ids:
            raise ProjectFileError("Analysis identifiers must be unique within a project.")
        analysis_ids.add(analysis["analysis_id"])
    if "presentation" in document:
        raise ProjectFileError("Serialized presentation is not a Project v2 authority field.")


def _validate_analysis(analysis: Any) -> None:
    if not isinstance(analysis, Mapping):
        raise ProjectFileError("Each analysis must be an object.")
    _reject_unknown(analysis, {"analysis_id", "analysis_name", "method_id", "method_identifier", "engine_method_identifier", "method_version", "input_contract", "project_type", "hcm_edition", "hcm_chapter", "scenarios"}, "analysis")
    _required_keys(analysis, {"analysis_id", "analysis_name", "method_id", "method_identifier", "engine_method_identifier", "method_version", "input_contract", "project_type", "hcm_edition", "hcm_chapter", "scenarios"}, "analysis")
    for field in ("analysis_id", "analysis_name", "method_id", "method_identifier", "engine_method_identifier", "method_version", "input_contract", "project_type", "hcm_edition", "hcm_chapter"):
        _require_text(analysis[field], f"analysis.{field}")
    definition = get_analysis_definition(analysis["method_id"])
    if definition is None:
        raise ProjectFileError(f"Unknown analysis method_id: {analysis['method_id']}.")
    for field in ("method_identifier", "engine_method_identifier", "method_version", "input_contract", "project_type"):
        if analysis[field] != getattr(definition, field):
            raise ProjectFileError(f"Analysis {analysis['analysis_id']} has drifted method identity.")
    if not isinstance(analysis["scenarios"], list) or not analysis["scenarios"]:
        raise ProjectFileError("Each analysis must contain at least one scenario.")
    scenario_ids: set[str] = set()
    for scenario in analysis["scenarios"]:
        _validate_scenario(scenario, analysis)
        if scenario["scenario_id"] in scenario_ids:
            raise ProjectFileError("Scenario identifiers must be unique within an analysis.")
        scenario_ids.add(scenario["scenario_id"])


def _validate_scenario(scenario: Any, analysis: Mapping[str, Any]) -> None:
    if not isinstance(scenario, Mapping):
        raise ProjectFileError("Each scenario must be an object.")
    _reject_unknown(scenario, {"scenario_id", "scenario_name", "kind", "duplicated_from_scenario_id", "unit_system", "template_id", "displayed_inputs", "normalized_inputs", "calculation_fingerprint", "input_snapshot_fingerprint", "result_status", "result"}, "scenario")
    _required_keys(scenario, {"scenario_id", "scenario_name", "kind", "unit_system", "template_id", "displayed_inputs", "normalized_inputs", "calculation_fingerprint", "input_snapshot_fingerprint", "result_status", "result"}, "scenario")
    for field in ("scenario_id", "scenario_name", "kind", "unit_system", "calculation_fingerprint", "input_snapshot_fingerprint", "result_status"):
        _require_text(scenario[field], f"scenario.{field}")
    if scenario["kind"] not in {"base", "duplicate"}:
        raise ProjectFileError("scenario.kind must be base or duplicate.")
    if scenario["unit_system"] not in {"metric", "imperial"}:
        raise ProjectFileError("scenario.unit_system must be metric or imperial.")
    if not isinstance(scenario["displayed_inputs"], Mapping) or not isinstance(scenario["normalized_inputs"], Mapping):
        raise ProjectFileError("Scenario inputs must be objects.")
    canonical_normalized = _canonical_project_normalized_inputs(
        method_id=str(analysis["method_id"]),
        template_id=scenario["template_id"],
        unit_system=scenario["unit_system"],
        displayed_inputs=scenario["displayed_inputs"],
        supplied_normalized_inputs=scenario["normalized_inputs"],
    )
    calculation_fp = _identity_fingerprint(analysis["method_identifier"], analysis["input_contract"], canonical_normalized)
    snapshot_fp = _snapshot_fingerprint(analysis["method_identifier"], analysis["input_contract"], scenario["displayed_inputs"], canonical_normalized)
    if scenario["calculation_fingerprint"] != calculation_fp or scenario["input_snapshot_fingerprint"] != snapshot_fp:
        raise ProjectFileError(f"Scenario {scenario['scenario_id']} has an invalid fingerprint.")
    if scenario["result_status"] not in {"not_calculated", "current", "stale"}:
        raise ProjectFileError("scenario.result_status is invalid.")
    if scenario["result_status"] == "current" and scenario["result"] is None:
        raise ProjectFileError("A current scenario must retain a result.")
    if scenario["result"] is not None:
        _validate_result_record(scenario["result"], analysis, scenario)
        if scenario["result_status"] != "current":
            raise ProjectFileError("A retained result must have result_status=current.")


def _validate_result_record(result: Any, analysis: Mapping[str, Any], scenario: Mapping[str, Any]) -> None:
    if not isinstance(result, Mapping):
        raise ProjectFileError("scenario.result must be an object or null.")
    _reject_unknown(result, {"result_id", "method_identifier", "engine_method_identifier", "method_version", "input_contract", "calculation_fingerprint", "input_snapshot_fingerprint", "engine_result", "warnings", "assumptions", "audit", "stored_at"}, "result")
    _required_keys(result, {"result_id", "method_identifier", "engine_method_identifier", "method_version", "input_contract", "calculation_fingerprint", "input_snapshot_fingerprint", "engine_result", "warnings", "assumptions", "audit", "stored_at"}, "result")
    for field in ("result_id", "method_identifier", "engine_method_identifier", "method_version", "input_contract", "calculation_fingerprint", "input_snapshot_fingerprint", "stored_at"):
        _require_text(result[field], f"result.{field}")
    if result["method_identifier"] != analysis["method_identifier"] or result["engine_method_identifier"] != analysis["engine_method_identifier"] or result["method_version"] != analysis["method_version"] or result["input_contract"] != analysis["input_contract"]:
        raise ProjectFileError("Stored result method identity does not match its analysis.")
    if result["calculation_fingerprint"] != scenario["calculation_fingerprint"] or result["input_snapshot_fingerprint"] != scenario["input_snapshot_fingerprint"]:
        raise ProjectFileError("Stored result is not current for its scenario.")
    if not isinstance(result["engine_result"], Mapping) or "outputs" not in result["engine_result"]:
        raise ProjectFileError("Stored result.engine_result must contain outputs.")
    if result["engine_result"].get("method") != analysis["engine_method_identifier"]:
        raise ProjectFileError("Stored engine result method identity does not match its analysis.")
    if "presentation" in result:
        raise ProjectFileError("Serialized presentation is not a Project v2 result authority field.")
    if not isinstance(result["warnings"], list) or not isinstance(result["assumptions"], list) or not isinstance(result["audit"], Mapping):
        raise ProjectFileError("Stored result warnings, assumptions, and audit have invalid types.")


def _find_analysis(document: Mapping[str, Any], analysis_id: str) -> dict[str, Any]:
    for analysis in document["analyses"]:
        if analysis["analysis_id"] == analysis_id:
            return analysis
    raise ProjectFileError(f"Analysis not found: {analysis_id}.")


def _find_scenario(analysis: Mapping[str, Any], scenario_id: str) -> dict[str, Any]:
    for scenario in analysis["scenarios"]:
        if scenario["scenario_id"] == scenario_id:
            return scenario
    raise ProjectFileError(f"Scenario not found: {scenario_id}.")


def _require_current_result(scenario: Mapping[str, Any]) -> None:
    if scenario.get("result_status") != "current" or not isinstance(scenario.get("result"), Mapping):
        raise ProjectFileError("Compare and export require current results for both scenarios.")


def _comparison_keys(left: Mapping[str, Any], right: Mapping[str, Any]) -> list[str]:
    preferred = (
        "density_pc_mi_ln", "facility_follower_density_followers_mi_ln",
        "average_speed_mph", "facility_average_speed_mph",
        "demand_flow_rate_pc_h_ln", "capacity_pc_h_ln",
        "facility_percent_followers", "demand_capacity_ratio",
    )
    return [key for key in preferred if key in left and key in right]


def _los_value(outputs: Mapping[str, Any]) -> Any:
    return outputs.get("level_of_service", outputs.get("facility_level_of_service"))
