import json

import pytest

from hcmcalc.ui.project_io import (
    PROJECT_SCHEMA_VERSION,
    ProjectFileError,
    create_manual_project_json,
    create_manual_project_payload,
    load_manual_project_json,
)
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
