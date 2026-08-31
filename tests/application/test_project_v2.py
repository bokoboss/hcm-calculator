from copy import deepcopy
import json

import pytest

from hcmcalc.application.project import (
    ProjectFileError,
    compare_scenarios,
    duplicate_scenario,
    load_project,
    project_to_json,
    record_result,
    save_analysis_to_project,
    update_scenario_inputs,
)
import hcmcalc.application.phase3_workflows as phase3_services
from hcmcalc.application.workflows import MultilaneWorkflow, workflow_for_method
from hcmcalc.ui.project_io import (
    create_manual_freeway_project_payload,
    create_manual_multilane_project_payload,
    create_manual_project_payload,
    create_manual_ramp_project_payload,
    create_manual_weaving_project_payload,
)


def calculated_snapshot(demand: float | None = None) -> dict:
    workflow = MultilaneWorkflow()
    values = workflow.starting_values("MLH-CH26-004-EB", "imperial")["displayed_inputs"]
    if demand is not None:
        values["demand_volume_veh_h"] = demand
    return workflow.calculate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=values,
    )


def test_project_v2_roundtrip_retains_ids_and_result_identity_without_presentation() -> None:
    snapshot = calculated_snapshot()
    project = save_analysis_to_project(snapshot, project_name="Phase 2 study")
    scenario = project["analyses"][0]["scenarios"][0]
    assert project["schema_version"] == "2.0"
    assert scenario["result_status"] == "current"
    assert "presentation" not in scenario["result"]
    loaded = load_project(project_to_json(project))
    assert loaded["project_id"] == project["project_id"]
    assert loaded["analyses"][0]["analysis_id"] == project["analyses"][0]["analysis_id"]
    assert loaded["analyses"][0]["scenarios"][0]["scenario_id"] == scenario["scenario_id"]
    assert loaded["analyses"][0]["scenarios"][0]["result"]["calculation_fingerprint"] == scenario["calculation_fingerprint"]
    assert project_to_json(loaded) == project_to_json(project)


@pytest.mark.parametrize(
    "method_id, template_id",
    (
        ("two_lane_segment", "TLH-CH15-001"),
        ("basic_freeway_segment", "BF-CH26-001"),
        ("weaving_segment", "WVG-CH27-001"),
        ("merge_segment", "chapter_28_example_1_merge"),
        ("diverge_segment", "chapter_28_example_3_diverge_component"),
    ),
)
def test_phase3_project_v2_roundtrip_revalidates_all_delivered_methods(
    method_id: str,
    template_id: str,
) -> None:
    workflow = workflow_for_method(method_id)
    starting = workflow.starting_values(template_id, "imperial")
    snapshot = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=starting["displayed_inputs"],
    )
    project = save_analysis_to_project(snapshot, project_name=f"{method_id} study")
    loaded = load_project(project_to_json(project))
    scenario = loaded["analyses"][0]["scenarios"][0]
    assert scenario["result_status"] == "current"
    assert scenario["result"]["engine_result"]["method"] == snapshot["result"]["method"]


def test_project_v2_accepts_browser_numeric_round_trip_without_changing_fingerprint() -> None:
    snapshot = calculated_snapshot()

    def browser_numbers(value: object) -> object:
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, list):
            return [browser_numbers(item) for item in value]
        if isinstance(value, dict):
            return {key: browser_numbers(item) for key, item in value.items()}
        return value

    browser_snapshot = browser_numbers(snapshot)
    assert isinstance(browser_snapshot, dict)
    project = save_analysis_to_project(browser_snapshot, project_name="Browser round trip")
    loaded = load_project(project_to_json(project))
    scenario = loaded["analyses"][0]["scenarios"][0]
    assert scenario["result_status"] == "current"
    assert scenario["result"]["calculation_fingerprint"] == snapshot["calculation_fingerprint"]


def test_duplicate_is_independent_and_input_update_discards_result() -> None:
    base = calculated_snapshot()
    project = save_analysis_to_project(base)
    analysis = project["analyses"][0]
    base_scenario = analysis["scenarios"][0]
    duplicated = duplicate_scenario(
        project,
        analysis_id=analysis["analysis_id"],
        scenario_id=base_scenario["scenario_id"],
        scenario_name="Higher demand",
    )
    scenarios = duplicated["analyses"][0]["scenarios"]
    alternative = scenarios[1]
    assert alternative["scenario_id"] != base_scenario["scenario_id"]
    assert alternative["result"] is None
    assert alternative["result_status"] == "not_calculated"
    changed = calculated_snapshot(1800.0)
    stale = update_scenario_inputs(
        duplicated,
        analysis_id=analysis["analysis_id"],
        scenario_id=alternative["scenario_id"],
        snapshot=changed,
    )
    assert stale["analyses"][0]["scenarios"][1]["result"] is None
    assert stale["analyses"][0]["scenarios"][1]["result_status"] == "stale"
    recalculated = record_result(
        stale,
        analysis_id=analysis["analysis_id"],
        scenario_id=alternative["scenario_id"],
        snapshot=changed,
    )
    assert recalculated["analyses"][0]["scenarios"][1]["result_status"] == "current"
    comparison = compare_scenarios(
        recalculated,
        analysis_id=analysis["analysis_id"],
        left_scenario_id=base_scenario["scenario_id"],
        right_scenario_id=alternative["scenario_id"],
    )
    assert comparison["current_only"] is True
    assert comparison["recalculated"] is False
    assert comparison["numeric_deltas"]


def test_future_project_schema_is_rejected() -> None:
    future = {
        "schema_version": "2.1",
        "project_id": "project_future",
    }
    with pytest.raises(ProjectFileError, match="newer"):
        load_project(future)


def test_project_v2_rejects_drifted_result_identity_and_current_without_result() -> None:
    project = save_analysis_to_project(calculated_snapshot())

    drifted = deepcopy(project)
    drifted["analyses"][0]["scenarios"][0]["result"]["engine_result"]["method"] = "wrong_engine"
    with pytest.raises(ProjectFileError, match="engine result method identity"):
        load_project(drifted)

    missing_result = deepcopy(project)
    missing_result["analyses"][0]["scenarios"][0]["result"] = None
    with pytest.raises(ProjectFileError, match="current scenario"):
        load_project(missing_result)


def test_legacy_multilane_project_migrates_and_discards_mismatched_result_without_engine_call(monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = calculated_snapshot()
    legacy = create_manual_multilane_project_payload(
        snapshot["template_id"],
        "imperial",
        snapshot["displayed_inputs"],
        result=snapshot["result"],
        audit_record=snapshot["audit"],
        locale="en",
    )
    legacy_with_bad_result_identity = deepcopy(legacy)
    legacy_with_bad_result_identity["calculation_fingerprint"] = "wrong-fingerprint"

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("legacy import must not run the engine")

    monkeypatch.setattr("hcmcalc.application.workflows.run_manual_multilane", fail_if_called)
    retained = load_project(json.dumps(legacy))
    retained_scenario = retained["analyses"][0]["scenarios"][0]
    assert retained_scenario["result_status"] == "current"
    assert retained_scenario["result"]["engine_result"]["method"] == "hcm7_multilane_los"

    def browser_numbers(value: object) -> object:
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, list):
            return [browser_numbers(item) for item in value]
        if isinstance(value, dict):
            return {key: browser_numbers(item) for key, item in value.items()}
        return value

    browser_legacy = deepcopy(legacy)
    browser_legacy["displayed_ui_inputs"] = browser_numbers(browser_legacy["displayed_ui_inputs"])
    browser_legacy["normalized_engine_inputs"] = browser_numbers(browser_legacy["normalized_engine_inputs"])
    browser_retained = load_project(json.dumps(browser_legacy))
    assert browser_retained["analyses"][0]["scenarios"][0]["result_status"] == "current"

    migrated = load_project(json.dumps(legacy_with_bad_result_identity))
    scenario = migrated["analyses"][0]["scenarios"][0]
    assert migrated["schema_version"] == "2.0"
    assert migrated["migration"]["status"] == "migrated_legacy"
    assert scenario["result"] is None
    assert scenario["result_status"] == "stale"


def test_legacy_single_segment_reference_method_migrates_to_view_only_project() -> None:
    legacy = create_manual_project_payload(
        {
            "unit_system": "metric",
            "segment_type": "passing_constrained",
            "terrain_type": "level",
            "horizontal_alignment": "straight",
            "segment_length": 1.2,
            "posted_speed": 80.0,
            "lane_width": 3.5,
            "shoulder_width": 1.8,
            "access_point_density": 0.0,
            "analysis_direction_volume": 750.0,
            "peak_hour_factor": 0.94,
            "heavy_vehicle_percent": 5.0,
            "grade_percent": 0.0,
            "opposing_direction_volume": None,
            "horizontal_alignment_subsegments": [],
        },
    )
    legacy["generated_by"] = "hcm-calculator 0.9.0"

    migrated = load_project(json.dumps(legacy))
    analysis = migrated["analyses"][0]
    scenario = analysis["scenarios"][0]
    assert migrated["schema_version"] == "2.0"
    assert migrated["migration"]["status"] == "migrated_legacy"
    assert analysis["method_id"] == "two_lane_segment"
    assert scenario["template_id"] == "legacy_import"
    assert scenario["result_status"] == "not_calculated"
    assert scenario["result"] is None


@pytest.mark.parametrize(
    "method_id, template_id",
    (
        ("two_lane_segment", "TLH-CH15-001"),
        ("basic_freeway_segment", "BF-CH26-001"),
        ("weaving_segment", "WVG-CH27-001"),
        ("merge_segment", "chapter_28_example_1_merge"),
        ("diverge_segment", "chapter_28_example_3_diverge_component"),
    ),
)
def test_phase3_legacy_projects_retain_current_results_without_engine_calls(
    monkeypatch: pytest.MonkeyPatch,
    method_id: str,
    template_id: str,
) -> None:
    workflow = workflow_for_method(method_id)
    starting = workflow.starting_values(template_id, "imperial")
    snapshot = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=starting["displayed_inputs"],
    )
    displayed = deepcopy(snapshot["displayed_inputs"])
    if method_id == "two_lane_segment":
        displayed["unit_system"] = "imperial"
        legacy = create_manual_project_payload(
            displayed,
            result=snapshot["result"],
            audit_record=snapshot["audit"],
            locale="en",
        )
    elif method_id == "basic_freeway_segment":
        legacy = create_manual_freeway_project_payload(
            template_id,
            "imperial",
            displayed,
            result=snapshot["result"],
            audit_record=snapshot["audit"],
            locale="en",
        )
    elif method_id == "weaving_segment":
        legacy = create_manual_weaving_project_payload(
            template_id,
            "imperial",
            displayed,
            result=snapshot["result"],
            audit_record=snapshot["audit"],
            locale="en",
        )
    else:
        legacy = create_manual_ramp_project_payload(
            "merge" if method_id == "merge_segment" else "diverge",
            template_id,
            "imperial",
            displayed,
            result=snapshot["result"],
            audit_record=snapshot["audit"],
            locale="en",
        )

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("legacy import must not run an HCM engine")

    for engine_name in ("run_manual_single_segment", "run_manual_freeway", "run_manual_weaving", "run_manual_ramp"):
        monkeypatch.setattr(phase3_services, engine_name, fail_if_called)

    migrated = load_project(json.dumps(legacy))
    scenario = migrated["analyses"][0]["scenarios"][0]
    assert migrated["schema_version"] == "2.0"
    assert scenario["result_status"] == "current"
    assert scenario["result"]["engine_result"]["method"] == snapshot["result"]["method"]
