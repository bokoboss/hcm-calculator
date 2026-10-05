from copy import deepcopy
import json

import pytest

from hcmcalc.application.project import (
    load_project,
    project_to_json,
    save_analysis_to_project,
    update_scenario_inputs,
    duplicate_scenario,
    record_result,
    compare_scenarios,
)
from hcmcalc.application.registry import get_analysis_definition
from hcmcalc.application.workflows import (
    export_current_workflow,
    workflow_for_method,
)
from hcmcalc.urban_street_ch18 import UrbanStreetSegmentMethod

METHOD = "urban_street_segment_th_lht"
TEMPLATE = "USS-TH-LHT-CH30-EP1"


def lht():
    return workflow_for_method(METHOD)


def starter():
    return lht().starting_values(TEMPLATE, "imperial")["displayed_inputs"]


def test_registry_and_frozen_lht_identity():
    definition = get_analysis_definition(METHOD)
    assert definition is not None
    assert (
        definition.method_id,
        definition.family,
        definition.method_identifier,
        definition.engine_method_identifier,
        definition.method_version,
        definition.input_contract,
        definition.project_type,
        definition.hcm_edition,
        definition.hcm_chapter,
        definition.chapter_reference,
    ) == (
        METHOD,
        "urban_streets",
        "hcm7_urban_street_segment_th_lht",
        "urban_street_segment_ch18_v0_1",
        "hcm_7_0_bounded_th_lht_v1",
        "hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1",
        "manual_urban_street_segment_th_lht_v1",
        "HCM 7.0",
        "18",
        "HCM 7.0 Chapter 18; Chapter 30 Example Problem 1; Thailand/LHT semantic qualification",
    )


def test_lht_starter_schema_and_old_rht_fields_are_rejected():
    workflow = lht()
    templates = workflow.templates()
    assert {item["template_id"] for item in templates["templates"]} == {TEMPLATE, "blank_custom"}
    inputs = starter()
    assert inputs["kerbside_curb_proportion"] == 0.70
    assert inputs["kerbside_parking_proportion"] == 0
    assert inputs["subject_kerbside_access_count"] == 4
    assert inputs["opposing_kerbside_access_count"] == 4
    assert inputs["calibration_status"] == "hcm_reference_uncalibrated"
    assert inputs["calibration_source_note"] in (None, "")
    fields = {item["key"]: item for item in templates["fields"]}
    grouped_fields = [field for group in templates["groups"] for field in group["field_keys"]]
    assert len(grouped_fields) == len(set(grouped_fields))
    assert set(grouped_fields) == set(fields)
    for field in (
        "kerbside_curb_proportion",
        "kerbside_parking_proportion",
        "subject_kerbside_access_count",
        "opposing_kerbside_access_count",
        "calibration_status",
        "calibration_source_note",
    ):
        assert fields[field]["label_key"] == f"{METHOD}.{field}"
    assert not {"curb_proportion", "parking_proportion", "subject_side_access_count", "opposing_side_access_count"} & set(fields)
    inputs["curb_proportion"] = 0.2
    validation = workflow.validate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=inputs)
    assert validation["valid"] is False
    assert validation["errors"][0]["field"] == "curb_proportion"


def test_role_mirror_canonical_inputs_and_engine_result_match_rht():
    lht_workflow = lht()
    lht_inputs = starter()
    lht_snapshot = lht_workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=lht_inputs)
    rht_workflow = workflow_for_method("urban_street_segment")
    rht_inputs = rht_workflow.starting_values("USS-CH30-EP1", "imperial")["displayed_inputs"]
    rht_snapshot = rht_workflow.calculate(template_id="USS-CH30-EP1", unit_system="imperial", displayed_inputs=rht_inputs)
    assert lht_snapshot["normalized_inputs"] == rht_snapshot["normalized_inputs"]
    assert lht_snapshot["result"] == rht_snapshot["result"]
    assert lht_snapshot["calculation_fingerprint"] != rht_snapshot["calculation_fingerprint"]
    assert lht_snapshot["input_snapshot_fingerprint"] != rht_snapshot["input_snapshot_fingerprint"]
    assert "calibration_status" not in lht_snapshot["normalized_inputs"]
    assert "calibration_source_note" not in lht_snapshot["normalized_inputs"]


def test_asymmetric_mapping_and_calibration_contract():
    workflow = lht()
    values = starter()
    values.update({
        "kerbside_curb_proportion": 0.23,
        "kerbside_parking_proportion": 0.61,
        "subject_kerbside_access_count": 7,
        "opposing_kerbside_access_count": 2,
    })
    normalized = workflow._normalized(TEMPLATE, "imperial", values)
    assert normalized["curb_proportion"] == 0.23
    assert normalized["parking_proportion"] == 0.61
    assert normalized["subject_side_access_count"] == 7
    assert normalized["opposing_side_access_count"] == 2

    values["s_calib"] = 1.0
    invalid = workflow.validate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=values)
    assert invalid["valid"] is False
    assert invalid["errors"][0]["field"] in {"s_calib", "calibration_status"}

    values["calibration_status"] = "user_local_calibration"
    missing_source = workflow.validate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=values)
    assert missing_source["valid"] is False
    assert missing_source["errors"][0]["field"] == "calibration_source_note"

    values["calibration_source_note"] = "Local field study, report TH-2026-07"
    accepted = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=values)
    assert accepted["audit"]["calibration_source_note"] == values["calibration_source_note"]
    changed = deepcopy(values)
    changed["calibration_source_note"] = "Local field study, report TH-2026-08"
    next_snapshot = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=changed)
    assert next_snapshot["calculation_fingerprint"] == accepted["calculation_fingerprint"]
    assert next_snapshot["input_snapshot_fingerprint"] != accepted["input_snapshot_fingerprint"]


def test_project_v2_roundtrip_stale_and_exports_without_rerun(monkeypatch):
    workflow = lht()
    values = starter()
    snapshot = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=values)
    project = save_analysis_to_project(snapshot, project_name="LHT study")
    assert project["schema_version"] == "2.0"

    def fail(*args, **kwargs):
        raise AssertionError("Project load/export must not rerun the engine")

    monkeypatch.setattr(UrbanStreetSegmentMethod, "calculate", fail)
    loaded = load_project(project_to_json(project))
    scenario = loaded["analyses"][0]["scenarios"][0]
    assert scenario["result_status"] == "current"
    assert scenario["result"]["engine_result"]["method"] == "urban_street_segment_ch18_v0_1"

    for export_format in ("json", "markdown", "csv", "xlsx"):
        exported = export_current_workflow(
            METHOD,
            template_id=TEMPLATE,
            unit_system="imperial",
            displayed_inputs=values,
            calculation_fingerprint=snapshot["calculation_fingerprint"],
            input_snapshot_fingerprint=snapshot["input_snapshot_fingerprint"],
            result=snapshot["result"],
            export_format=export_format,
        )
        assert exported["recalculated"] is False
        assert exported["content"] or exported["content_base64"]

    monkeypatch.undo()
    changed = deepcopy(values)
    changed["kerbside_curb_proportion"] = 0.24
    edited = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=changed)
    stale = update_scenario_inputs(
        loaded,
        analysis_id=loaded["analyses"][0]["analysis_id"],
        scenario_id=scenario["scenario_id"],
        snapshot=edited,
    )
    assert stale["analyses"][0]["scenarios"][0]["result_status"] == "stale"
    assert stale["analyses"][0]["scenarios"][0]["result"] is None


def test_report_exposes_operator_semantics_engine_roles_and_calibration_disclosure():
    workflow = lht()
    values = starter()
    snapshot = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=values)
    exported = export_current_workflow(
        METHOD,
        template_id=TEMPLATE,
        unit_system="imperial",
        displayed_inputs=values,
        calculation_fingerprint=snapshot["calculation_fingerprint"],
        input_snapshot_fingerprint=snapshot["input_snapshot_fingerprint"],
        result=snapshot["result"],
        export_format="json",
    )
    report = json.loads(exported["content"])
    assert report["calculation_type"] == "manual_urban_street_segment_th_lht_v1"
    assert report["method_identifier"] == "hcm7_urban_street_segment_th_lht"
    assert report["traffic_side"] == "left_hand_traffic"
    assert report["kerbside_physical_side"] == "left_for_each_travel_direction"
    assert report["input_contract"] == "hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1"
    assert report["calibration_status"] == "hcm_reference_uncalibrated"
    assert any("not Thai empirically calibrated by default" in text for text in report["limitations"])
    shown = {item["label"]: item["value"] for item in report["inputs_summary"]}
    assert shown["kerbside_curb_proportion"] == 0.70
    assert "curb_proportion" not in shown
    canonical = {item["label"]: item["value"] for item in report["normalized_engine_inputs_summary"]}
    assert canonical["curb_proportion"] == 0.70
    assert {item["label"]: item["value"] for item in report["audit_summary"]}["semantic_mapping.kerbside_curb_proportion"] == "curb_proportion"


def test_project_calibration_provenance_change_stales_without_schema_change():
    workflow = lht()
    values = starter()
    snapshot = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=values)
    project = save_analysis_to_project(snapshot, project_name="LHT provenance")
    analysis = project["analyses"][0]
    scenario = analysis["scenarios"][0]
    changed = deepcopy(values)
    changed["calibration_status"] = "user_local_calibration"
    changed["calibration_source_note"] = "Local field study TH-2026-07"
    edited = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=changed)
    assert edited["calculation_fingerprint"] == snapshot["calculation_fingerprint"]
    assert edited["input_snapshot_fingerprint"] != snapshot["input_snapshot_fingerprint"]
    stale = update_scenario_inputs(
        project,
        analysis_id=analysis["analysis_id"],
        scenario_id=scenario["scenario_id"],
        snapshot=edited,
    )
    assert stale["schema_version"] == "2.0"
    assert stale["analyses"][0]["scenarios"][0]["result_status"] == "stale"


def test_lht_scenario_comparison_uses_current_results_without_rerun(monkeypatch):
    workflow = lht()
    values = starter()
    base_snapshot = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=values)
    project = save_analysis_to_project(base_snapshot, project_name="LHT comparison")
    analysis = project["analyses"][0]
    first = analysis["scenarios"][0]
    duplicated = duplicate_scenario(
        project,
        analysis_id=analysis["analysis_id"],
        scenario_id=first["scenario_id"],
        scenario_name="Higher subject flow",
    )
    second = duplicated["analyses"][0]["scenarios"][1]
    changed = deepcopy(values)
    changed["v_m_veh_h"] = 1200
    changed_snapshot = workflow.calculate(template_id=TEMPLATE, unit_system="imperial", displayed_inputs=changed)
    current = record_result(
        duplicated,
        analysis_id=analysis["analysis_id"],
        scenario_id=second["scenario_id"],
        snapshot=changed_snapshot,
    )

    def fail(*args, **kwargs):
        raise AssertionError("Scenario comparison must not rerun the engine")

    monkeypatch.setattr(UrbanStreetSegmentMethod, "calculate", fail)
    comparison = compare_scenarios(
        current,
        analysis_id=analysis["analysis_id"],
        left_scenario_id=first["scenario_id"],
        right_scenario_id=second["scenario_id"],
    )
    deltas = {item["key"]: item for item in comparison["numeric_deltas"]}
    assert comparison["method_id"] == METHOD
    assert comparison["recalculated"] is False
    assert "travel_speed_mph" in deltas


def test_direction_and_external_through_provenance_are_preserved():
    workflow = lht()
    values = starter()
    values.update({
        "subject_direction": "northbound",
        "through_movement_id": "NB_TH",
        "external_direction": "northbound",
        "external_through_movement_id": "NB_TH",
    })
    normalized = workflow._normalized(TEMPLATE, "imperial", values)
    assert normalized["subject_direction"] == normalized["external_through"]["direction"] == "northbound"
    assert normalized["through_movement_id"] == normalized["external_through"]["through_movement_id"] == "NB_TH"
    assert normalized["analysis_period_min"] == normalized["external_through"]["analysis_period_min"] == 15
    assert normalized["control_type"] == normalized["external_through"]["control_type"] == "signalized"
    assert normalized["v_m_veh_h"] == 1150
    assert normalized["external_through"]["v_th_veh_h"] == 968
    assert normalized["external_through"]["c_th_veh_h"] == 1848
    assert normalized["external_through"]["d_t_s_veh"] == 18.310
