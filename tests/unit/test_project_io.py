import json

import pytest

from hcmcalc.core import UnsupportedScopeError
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    load_facility_template,
    run_manual_facility,
)
from hcmcalc.ui.manual_multilane import (
    build_manual_multilane_audit_record,
    load_multilane_template,
    multilane_template_ui_inputs,
    run_manual_multilane,
)
from hcmcalc.ui.manual_freeway import (
    build_manual_freeway_audit_record,
    freeway_preset_ui_inputs,
    load_freeway_preset,
    run_manual_freeway,
)
from hcmcalc.ui.project_io import (
    MANUAL_BASIC_FREEWAY_PROJECT_TYPE,
    MANUAL_FACILITY_PROJECT_TYPE,
    MANUAL_MULTILANE_PROJECT_TYPE,
    PROJECT_SCHEMA_VERSION,
    ProjectFileError,
    create_manual_freeway_project_json,
    create_manual_freeway_project_payload,
    create_manual_facility_project_json,
    create_manual_facility_project_payload,
    create_manual_multilane_project_json,
    create_manual_multilane_project_payload,
    create_manual_project_json,
    create_manual_project_payload,
    load_manual_facility_project_json,
    load_manual_freeway_project_json,
    load_manual_multilane_project_json,
    load_manual_project_json,
)
from hcmcalc.cli import result_to_dict
from hcmcalc.ui.units import manual_horizontal_curve_defaults


CURVE_SETUP = {
    "total_curve_length": 1200.0,
    "radius": 137.16,
    "superelevation_percent": 3.0,
    "central_angle_deg": 55.0,
    "horizontal_class": 3,
    "subsegment_count": 11,
}


def _manual_inputs(**overrides) -> dict:
    values = {
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
    }
    values.update(overrides)
    return values


def test_create_project_payload_from_manual_inputs() -> None:
    manual_inputs = _manual_inputs()

    payload = create_manual_project_payload(manual_inputs)

    assert payload["schema_version"] == PROJECT_SCHEMA_VERSION
    assert payload["project_type"] == "manual_single_segment"
    assert payload["unit_system"] == "metric"
    assert payload["manual_inputs"] == manual_inputs
    assert payload["normalized_engine_inputs"]["segment_length_mi"] == pytest.approx(
        1.2 / 1.609344
    )
    assert payload["created_at"]


def test_create_project_payload_including_result_and_audit_record() -> None:
    result = {"warnings": ["warning"], "assumptions": ["assumption"], "outputs": {}}
    audit_record = {
        "normalized_engine_inputs": {"segment_length_mi": 0.75},
        "warnings": ["audit warning"],
        "assumptions": ["audit assumption"],
    }

    payload = create_manual_project_payload(
        _manual_inputs(), result=result, audit_record=audit_record
    )

    assert payload["result"] == result
    assert payload["audit_record"] == audit_record
    assert payload["normalized_engine_inputs"] == {"segment_length_mi": 0.75}
    assert payload["warnings"] == ["warning"]
    assert payload["assumptions"] == ["assumption"]


def test_load_valid_project_json_returns_restored_manual_inputs() -> None:
    manual_inputs = _manual_inputs(segment_type="passing_lane")

    loaded = load_manual_project_json(create_manual_project_json(manual_inputs))

    assert loaded["manual_inputs"] == manual_inputs


def test_generalized_project_restores_inputs_then_runs() -> None:
    manual_inputs = _manual_inputs(
        terrain_type="mountainous",
        grade_percent=4.0,
        segment_length=1.0,
        heavy_vehicle_percent=8.0,
    )

    loaded = load_manual_project_json(create_manual_project_json(manual_inputs))

    assert loaded["manual_inputs"] == manual_inputs
    assert run_manual_single_segment(loaded["manual_inputs"]).outputs["vertical_class"] == 3


@pytest.mark.parametrize(
    "manual_inputs",
    [
        _manual_inputs(
            segment_type="passing_zone",
            opposing_direction_volume=500.0,
        ),
        _manual_inputs(
            segment_type="passing_lane",
            heavy_vehicle_percent=8.0,
        ),
    ],
    ids=["passing-zone", "passing-lane"],
)
def test_level_segment_type_project_round_trip(manual_inputs: dict) -> None:
    loaded = load_manual_project_json(create_manual_project_json(manual_inputs))

    assert loaded["manual_inputs"] == manual_inputs
    assert loaded["normalized_engine_inputs"]["segment_type"] == manual_inputs[
        "segment_type"
    ]


def test_load_rejects_invalid_json() -> None:
    with pytest.raises(ProjectFileError, match="Invalid JSON"):
        load_manual_project_json("{not json")


def test_load_rejects_wrong_project_type() -> None:
    payload = create_manual_project_payload(_manual_inputs())
    payload["project_type"] = "validated_case"

    with pytest.raises(ProjectFileError, match="Wrong project_type"):
        load_manual_project_json(json.dumps(payload))


def test_load_rejects_unsupported_schema_version() -> None:
    payload = create_manual_project_payload(_manual_inputs())
    payload["schema_version"] = "2.0"

    with pytest.raises(ProjectFileError, match="Unsupported schema_version"):
        load_manual_project_json(json.dumps(payload))


def test_horizontal_curve_subsegments_survive_project_round_trip() -> None:
    subsegments = manual_horizontal_curve_defaults("metric", segment_length=1.2)
    manual_inputs = _manual_inputs(
        horizontal_alignment="horizontal_curves",
        horizontal_alignment_subsegments=subsegments,
    )

    loaded = load_manual_project_json(create_manual_project_json(manual_inputs))

    assert loaded["manual_inputs"]["horizontal_alignment_subsegments"] == subsegments


def test_curve_setup_and_subsegments_survive_project_round_trip() -> None:
    subsegments = manual_horizontal_curve_defaults("metric", segment_length=1.2)
    manual_inputs = _manual_inputs(
        horizontal_alignment="horizontal_curves",
        curve_setup=CURVE_SETUP,
        horizontal_alignment_subsegments=subsegments,
    )

    loaded = load_manual_project_json(create_manual_project_json(manual_inputs))

    assert loaded["manual_inputs"]["curve_setup"] == CURVE_SETUP
    assert loaded["manual_inputs"]["horizontal_alignment_subsegments"] == subsegments


def test_horizontal_curve_project_without_curve_setup_remains_compatible() -> None:
    subsegments = manual_horizontal_curve_defaults("metric", segment_length=1.2)
    manual_inputs = _manual_inputs(
        horizontal_alignment="horizontal_curves",
        horizontal_alignment_subsegments=subsegments,
    )

    loaded = load_manual_project_json(create_manual_project_json(manual_inputs))

    assert "curve_setup" not in loaded["manual_inputs"]


def test_load_rejects_missing_required_fields() -> None:
    payload = create_manual_project_payload(_manual_inputs())
    del payload["manual_inputs"]["segment_length"]

    with pytest.raises(ProjectFileError, match="Missing required manual_inputs fields"):
        load_manual_project_json(json.dumps(payload))


def test_load_rejects_malformed_horizontal_curve_subsegments() -> None:
    payload = create_manual_project_payload(
        _manual_inputs(
            horizontal_alignment="horizontal_curves",
            horizontal_alignment_subsegments=[{"type": "horizontal_curve", "length": 1}],
        )
    )

    with pytest.raises(ProjectFileError, match="Malformed horizontal curve subsegment"):
        load_manual_project_json(json.dumps(payload))


@pytest.mark.parametrize(
    ("template_id", "unit_system"),
    [("level_example_3", "imperial"), ("mountainous_example_4", "metric")],
)
def test_manual_facility_project_round_trip(template_id: str, unit_system: str) -> None:
    template = load_facility_template(template_id, unit_system)
    result = run_manual_facility(template_id, template["segments"], unit_system)
    audit = build_manual_facility_audit_record(
        template_id, template["segments"], unit_system, result=result
    )

    loaded = load_manual_facility_project_json(
        create_manual_facility_project_json(
            template_id,
            unit_system,
            template["segments"],
            result=result_to_dict(result),
            audit_record=audit,
        )
    )

    assert loaded["project_type"] == MANUAL_FACILITY_PROJECT_TYPE
    assert loaded["template_id"] == template_id
    assert loaded["segment_rows"] == template["segments"]
    assert loaded["normalized_facility_inputs"]["segments"]
    assert loaded["calculation_result"]["outputs"]["facility_level_of_service"]
    rerun = run_manual_facility(
        loaded["template_id"], loaded["segment_rows"], loaded["unit_system"]
    )
    assert rerun.outputs == loaded["calculation_result"]["outputs"]


def test_manual_facility_project_payload_contains_auditable_context() -> None:
    template = load_facility_template("level_example_3", "imperial")

    payload = create_manual_facility_project_payload(
        template["template_id"], template["unit_system"], template["segments"]
    )

    assert payload["template_name"] == template["template_label"]
    assert payload["editable_facility_inputs"]["segments"] == template["segments"]
    assert payload["normalized_facility_inputs"]["segments"]
    assert payload["unsupported_behavior_notes"]
    assert payload["app_version"]


def test_facility_loader_rejects_single_segment_project() -> None:
    with pytest.raises(ProjectFileError, match="Expected manual_facility_v0"):
        load_manual_facility_project_json(create_manual_project_json(_manual_inputs()))


def test_single_segment_loader_rejects_facility_project_without_breaking_round_trip() -> None:
    template = load_facility_template("level_example_3", "imperial")
    facility_json = create_manual_facility_project_json(
        template["template_id"], template["unit_system"], template["segments"]
    )

    with pytest.raises(ProjectFileError, match="Expected manual_single_segment"):
        load_manual_project_json(facility_json)
    loaded = load_manual_project_json(create_manual_project_json(_manual_inputs()))
    assert loaded["manual_inputs"] == _manual_inputs()


def test_facility_load_rejects_unknown_template_id() -> None:
    template = load_facility_template("level_example_3", "imperial")
    payload = create_manual_facility_project_payload(
        template["template_id"], template["unit_system"], template["segments"]
    )
    payload["template_id"] = "unknown"

    with pytest.raises(ProjectFileError, match="Unknown template_id"):
        load_manual_facility_project_json(json.dumps(payload))


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload.pop("project_type"), "Missing required field: project_type"),
        (lambda payload: payload.pop("template_id"), "Missing required field: template_id"),
        (lambda payload: payload.pop("segment_rows"), "Missing required field: segment_rows"),
        (
            lambda payload: payload.__setitem__("segment_rows", [{"segment_id": 1}]),
            "Malformed or unsupported segment rows",
        ),
        (
            lambda payload: payload["segment_rows"][0].__setitem__(
                "terrain_type", "mountainous"
            ),
            "Malformed or unsupported segment rows",
        ),
    ],
)
def test_facility_load_rejects_malformed_or_unsupported_projects(
    mutation, message: str
) -> None:
    template = load_facility_template("level_example_3", "imperial")
    payload = create_manual_facility_project_payload(
        template["template_id"], template["unit_system"], template["segments"]
    )
    mutation(payload)

    with pytest.raises(ProjectFileError, match=message):
        load_manual_facility_project_json(json.dumps(payload))


@pytest.mark.parametrize(
    ("template_id", "unit_system"),
    [
        ("MLH-CH26-004-EB", "imperial"),
        ("MLH-CH26-004-EB", "metric"),
        ("MLH-CH26-004-WB", "imperial"),
        ("MLH-CH26-004-WB", "metric"),
    ],
)
def test_manual_multilane_project_round_trip(
    template_id: str, unit_system: str
) -> None:
    template = load_multilane_template(template_id)
    displayed = multilane_template_ui_inputs(template_id, unit_system)
    result = run_manual_multilane(template["inputs"])
    audit = build_manual_multilane_audit_record(
        template_id,
        template["inputs"],
        unit_system=unit_system,
        displayed_inputs=displayed,
        result=result,
    )

    loaded = load_manual_multilane_project_json(
        create_manual_multilane_project_json(
            template_id,
            unit_system,
            displayed,
            result=result_to_dict(result),
            audit_record=audit,
        )
    )

    assert loaded["project_type"] == MANUAL_MULTILANE_PROJECT_TYPE
    assert loaded["unit_system"] == unit_system
    assert loaded["template_id"] == template_id
    assert loaded["displayed_ui_inputs"] == displayed
    assert loaded["normalized_engine_inputs"] == template["inputs"]
    assert loaded["calculation_result"]["outputs"]["level_of_service"] == "C"
    assert loaded["limitations"]
    assert loaded["unsupported_behavior_notes"]


def test_manual_multilane_project_payload_contains_display_and_engine_values() -> None:
    displayed = multilane_template_ui_inputs("MLH-CH26-004-EB", "metric")

    payload = create_manual_multilane_project_payload(
        "MLH-CH26-004-EB", "metric", displayed
    )

    assert payload["direction"] == "eastbound"
    assert payload["displayed_ui_inputs"] == displayed
    assert payload["normalized_engine_inputs"]["segment_length_ft"] == 6600.0
    assert payload["display_result"] is None
    assert payload["app_version"]


def test_manual_multilane_non_example_project_round_trip_recalculates() -> None:
    displayed = multilane_template_ui_inputs("MLH-CH26-004-EB", "imperial")
    displayed.update(
        {
            "number_of_lanes": 3,
            "segment_length": 5280.0,
            "demand_volume_veh_h": 2400.0,
            "peak_hour_factor": 0.92,
            "heavy_vehicle_percent": 12.0,
            "grade_percent": 0.0,
            "ffs_source": "measured",
            "free_flow_speed": 55.0,
            "passenger_car_equivalent": 2.0,
        }
    )
    normalized = load_multilane_template("MLH-CH26-004-EB")["inputs"] | {
        "number_of_lanes": 3,
        "segment_length_ft": 5280.0,
        "demand_volume_veh_h": 2400.0,
        "peak_hour_factor": 0.92,
        "heavy_vehicle_percent": 12.0,
        "grade_percent": 0.0,
        "ffs_source": "measured",
        "free_flow_speed_mph": 55.0,
        "passenger_car_equivalent": 2.0,
    }
    result = run_manual_multilane(normalized)
    audit = build_manual_multilane_audit_record(
        "MLH-CH26-004-EB",
        normalized,
        unit_system="imperial",
        displayed_inputs=displayed,
        result=result,
    )

    loaded = load_manual_multilane_project_json(
        create_manual_multilane_project_json(
            "MLH-CH26-004-EB",
            "imperial",
            displayed,
            result=result_to_dict(result),
            audit_record=audit,
        )
    )
    rerun = run_manual_multilane(loaded["normalized_engine_inputs"])

    assert loaded["displayed_ui_inputs"]["number_of_lanes"] == 3
    assert loaded["normalized_engine_inputs"]["ffs_source"] == "measured"
    assert loaded["normalized_engine_inputs"]["free_flow_speed_mph"] == 55.0
    assert loaded["normalized_engine_inputs"]["number_of_lanes"] == 3
    assert loaded["normalized_engine_inputs"]["lane_width_ft"] == 12.0
    assert loaded["normalized_engine_inputs"]["roadside_lateral_clearance_ft"] == 12.0
    assert loaded["normalized_engine_inputs"]["access_point_density_per_mi"] == 10.0
    assert loaded["normalized_engine_inputs"]["peak_hour_factor"] == 0.92
    assert loaded["normalized_engine_inputs"]["heavy_vehicle_percent"] == 12.0
    assert loaded["normalized_engine_inputs"]["passenger_car_equivalent"] == 2.0
    assert loaded["calculation_result"]["outputs"]["level_of_service"]
    assert rerun.outputs["support_status"] == "bounded_multilane_segment_v0_1"
    assert rerun.outputs["density_pc_mi_ln"] >= 0


def test_manual_multilane_estimated_non_example_project_round_trip_recalculates() -> None:
    displayed = multilane_template_ui_inputs("MLH-CH26-004-EB", "imperial")
    displayed.update(
        {
            "segment_length": 5280.0,
            "demand_volume_veh_h": 1200.0,
            "peak_hour_factor": 0.95,
            "heavy_vehicle_percent": 15.0,
            "grade_percent": 0.0,
            "lane_width": 11.0,
            "roadside_lateral_clearance": 4.0,
            "access_point_density": 5.0,
            "ffs_source": "estimated",
            "passenger_car_equivalent": 2.5,
        }
    )
    normalized = load_multilane_template("MLH-CH26-004-EB")["inputs"] | {
        "segment_length_ft": 5280.0,
        "demand_volume_veh_h": 1200.0,
        "peak_hour_factor": 0.95,
        "heavy_vehicle_percent": 15.0,
        "grade_percent": 0.0,
        "lane_width_ft": 11.0,
        "roadside_lateral_clearance_ft": 4.0,
        "access_point_density_per_mi": 5.0,
        "ffs_source": "estimated",
        "passenger_car_equivalent": 2.5,
    }
    result = run_manual_multilane(normalized)
    audit = build_manual_multilane_audit_record(
        "MLH-CH26-004-EB",
        normalized,
        unit_system="imperial",
        displayed_inputs=displayed,
        result=result,
    )

    loaded = load_manual_multilane_project_json(
        create_manual_multilane_project_json(
            "MLH-CH26-004-EB",
            "imperial",
            displayed,
            result=result_to_dict(result),
            audit_record=audit,
        )
    )
    rerun = run_manual_multilane(loaded["normalized_engine_inputs"])

    assert loaded["normalized_engine_inputs"]["ffs_source"] == "estimated"
    assert loaded["normalized_engine_inputs"]["lane_width_ft"] == 11.0
    assert loaded["normalized_engine_inputs"]["roadside_lateral_clearance_ft"] == 4.0
    assert loaded["normalized_engine_inputs"]["access_point_density_per_mi"] == 5.0
    assert loaded["normalized_engine_inputs"]["peak_hour_factor"] == 0.95
    assert loaded["normalized_engine_inputs"]["heavy_vehicle_percent"] == 15.0
    assert loaded["normalized_engine_inputs"]["passenger_car_equivalent"] == 2.5
    assert rerun.outputs["base_free_flow_speed_mph"] == 52.0
    assert rerun.outputs["level_of_service"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload.pop("project_type"), "Missing required field: project_type"),
        (
            lambda payload: payload.__setitem__("project_type", "manual_facility_v0"),
            "Expected manual_multilane_v0",
        ),
        (lambda payload: payload.pop("unit_system"), "Missing required field: unit_system"),
        (lambda payload: payload.__setitem__("template_id", "unknown"), "Unknown template_id"),
        (
            lambda payload: payload.__setitem__("displayed_ui_inputs", []),
            "Malformed input payload",
        ),
        (
            lambda payload: payload["displayed_ui_inputs"].pop("segment_length"),
            "Malformed input payload",
        ),
    ],
)
def test_manual_multilane_load_rejects_invalid_projects(mutation, message: str) -> None:
    payload = create_manual_multilane_project_payload(
        "MLH-CH26-004-EB",
        "imperial",
        multilane_template_ui_inputs("MLH-CH26-004-EB", "imperial"),
    )
    mutation(payload)

    with pytest.raises(ProjectFileError, match=message):
        load_manual_multilane_project_json(json.dumps(payload))


@pytest.mark.parametrize("unit_system", ["imperial", "metric"])
def test_manual_freeway_project_round_trip(unit_system: str) -> None:
    preset = load_freeway_preset("BF-CH26-001")
    displayed = freeway_preset_ui_inputs("BF-CH26-001", unit_system)
    result = run_manual_freeway(preset["inputs"])
    audit = build_manual_freeway_audit_record(
        "BF-CH26-001",
        preset["inputs"],
        unit_system=unit_system,
        displayed_inputs=displayed,
        result=result,
    )

    loaded = load_manual_freeway_project_json(
        create_manual_freeway_project_json(
            "BF-CH26-001",
            unit_system,
            displayed,
            result=result_to_dict(result),
            audit_record=audit,
        )
    )

    assert loaded["project_type"] == MANUAL_BASIC_FREEWAY_PROJECT_TYPE
    assert loaded["unit_system"] == unit_system
    assert loaded["preset_id"] == "BF-CH26-001"
    assert loaded["displayed_ui_inputs"] == displayed
    assert loaded["normalized_engine_inputs"] == preset["inputs"]
    assert loaded["calculation_result"]["outputs"]["level_of_service"] == "C"
    assert loaded["limitations"]
    assert loaded["unsupported_behavior_notes"]


def test_manual_freeway_project_payload_contains_display_and_engine_values() -> None:
    displayed = freeway_preset_ui_inputs("BF-CH26-001", "metric")

    payload = create_manual_freeway_project_payload(
        "BF-CH26-001", "metric", displayed
    )

    assert payload["preset_name"] == "Chapter 26 Example 1 starting values"
    assert payload["displayed_ui_inputs"] == displayed
    assert payload["normalized_engine_inputs"]["segment_length_mi"] == 1.0
    assert payload["display_result"] is None
    assert payload["app_version"]


def test_manual_freeway_non_example_project_round_trip_recalculates() -> None:
    displayed = freeway_preset_ui_inputs("BF-CH26-001", "imperial")
    displayed.update(
        {
            "number_of_lanes": 4,
            "segment_length": 2.2,
            "ffs_source": "measured",
            "free_flow_speed": 68.0,
            "base_free_flow_speed": None,
            "lane_width": None,
            "right_side_lateral_clearance": None,
            "total_ramp_density": None,
            "demand_volume_veh_h": 5600.0,
            "peak_hour_factor": 0.9,
            "heavy_vehicle_percent": 8.0,
            "terrain_type": "level",
        }
    )
    normalized = load_freeway_preset("BF-CH26-001")["inputs"] | {
        "number_of_lanes": 4,
        "segment_length_mi": 2.2,
        "demand_volume_veh_h": 5600.0,
        "peak_hour_factor": 0.9,
        "heavy_vehicle_percent": 8.0,
        "terrain_type": "level",
        "ffs_source": "measured",
        "free_flow_speed_mph": 68.0,
        "base_free_flow_speed_mph": None,
        "lane_width_ft": None,
        "right_side_lateral_clearance_ft": None,
        "total_ramp_density_per_mi": None,
    }
    result = run_manual_freeway(normalized)
    audit = build_manual_freeway_audit_record(
        "BF-CH26-001",
        normalized,
        unit_system="imperial",
        displayed_inputs=displayed,
        result=result,
    )

    loaded = load_manual_freeway_project_json(
        create_manual_freeway_project_json(
            "BF-CH26-001",
            "imperial",
            displayed,
            result=result_to_dict(result),
            audit_record=audit,
        )
    )
    rerun = run_manual_freeway(loaded["normalized_engine_inputs"])

    assert loaded["displayed_ui_inputs"]["number_of_lanes"] == 4
    assert loaded["displayed_ui_inputs"]["free_flow_speed"] == 68.0
    assert loaded["normalized_engine_inputs"]["segment_length_mi"] == 2.2
    assert loaded["normalized_engine_inputs"]["demand_volume_veh_h"] == 5600.0
    assert loaded["normalized_engine_inputs"]["ffs_source"] == "measured"
    assert rerun.outputs["support_status"] == "supported_basic_freeway_segment_v0_1"
    assert rerun.outputs["level_of_service"]
    assert rerun.outputs["density_pc_mi_ln"] >= 0


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload.pop("project_type"), "Missing required field: project_type"),
        (
            lambda payload: payload.__setitem__("project_type", "manual_multilane_v0"),
            "Expected manual_basic_freeway_v0",
        ),
        (lambda payload: payload.pop("unit_system"), "Missing required field: unit_system"),
        (lambda payload: payload.__setitem__("preset_id", "unknown"), "Unknown preset_id"),
        (
            lambda payload: payload.__setitem__("displayed_ui_inputs", []),
            "Malformed input payload",
        ),
        (
            lambda payload: payload["displayed_ui_inputs"].pop("segment_length"),
            "Malformed input payload",
        ),
        (
            lambda payload: payload["displayed_ui_inputs"].__setitem__(
                "terrain_type", "mountainous"
            ),
            "Malformed or unsupported input payload",
        ),
    ],
)
def test_manual_freeway_load_rejects_invalid_projects(mutation, message: str) -> None:
    payload = create_manual_freeway_project_payload(
        "BF-CH26-001",
        "imperial",
        freeway_preset_ui_inputs("BF-CH26-001", "imperial"),
    )
    mutation(payload)

    with pytest.raises(ProjectFileError, match=message):
        load_manual_freeway_project_json(json.dumps(payload))


def test_manual_freeway_load_clears_stale_result_when_engine_inputs_change() -> None:
    displayed = freeway_preset_ui_inputs("BF-CH26-001", "imperial")
    result = result_to_dict(run_manual_freeway(load_freeway_preset("BF-CH26-001")["inputs"]))
    payload = create_manual_freeway_project_payload(
        "BF-CH26-001",
        "imperial",
        displayed,
        result=result,
    )
    payload["normalized_engine_inputs"]["demand_volume_veh_h"] = 1.0

    loaded = load_manual_freeway_project_json(json.dumps(payload))

    assert loaded["calculation_result"] is None
    assert loaded["display_result"] is None
    assert loaded["audit"] is None
