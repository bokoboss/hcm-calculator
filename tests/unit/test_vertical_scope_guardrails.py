import pytest

from hcmcalc.core import UnsupportedScopeError
from hcmcalc.methods.two_lane_highway_scope import (
    classify_vertical_scope,
    require_supported_vertical_scope,
)
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method
from hcmcalc.ui.audit import build_manual_calculation_audit_record
from hcmcalc.ui.manual_segment import run_manual_single_segment


def _manual_values(**overrides) -> dict:
    values = {
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "horizontal_alignment": "straight",
        "posted_speed_mph": 50.0,
        "segment_length_mi": 0.75,
        "lane_width_ft": 12.0,
        "shoulder_width_ft": 6.0,
        "access_point_density_per_mi": 0.0,
        "analysis_direction_volume_veh_h": 752.0,
        "peak_hour_factor": 0.94,
        "heavy_vehicle_percent": 5.0,
        "grade_percent": 0.0,
        "opposing_direction_volume_veh_h": None,
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("kwargs", "status"),
    [
        (
            {
                "segment_type": "passing_constrained",
                "grade_percent": 4.0,
                "grade_length_mi": 1.0,
                "heavy_vehicle_percent": 8.0,
            },
            "unsupported_needs_hcm_table_data",
        ),
        (
            {
                "segment_type": "passing_constrained",
                "grade_percent": 4.0,
                "grade_length_mi": None,
                "heavy_vehicle_percent": 8.0,
            },
            "unsupported_needs_hcm_table_data",
        ),
        (
            {
                "segment_type": "passing_zone",
                "grade_percent": 4.0,
                "grade_length_mi": 1.3,
                "heavy_vehicle_percent": 8.0,
            },
            "unsupported_needs_validation_fixture",
        ),
        (
            {
                "segment_type": "passing_constrained",
                "grade_percent": 4.0,
                "grade_length_mi": 1.3,
                "segment_length_mi": 2.0,
                "heavy_vehicle_percent": 8.0,
            },
            "unsupported_needs_hcm_table_data",
        ),
    ],
)
def test_scope_classifier_distinguishes_unsupported_reasons(
    kwargs: dict, status: str
) -> None:
    decision = classify_vertical_scope(**kwargs)

    assert decision.status == status
    assert decision.reason


def test_scope_classifier_rejects_submitted_vertical_class_mismatch() -> None:
    decision = classify_vertical_scope(
        segment_type="passing_constrained",
        grade_percent=4.0,
        grade_length_mi=1.3,
        heavy_vehicle_percent=8.0,
        terrain_type="mountainous",
        vertical_class=5,
    )

    assert decision.status == "unsupported"
    assert "does not match" in decision.reason


@pytest.mark.parametrize(
    "values",
    [
        _manual_values(terrain_type="mountainous", grade_percent=0.0),
        _manual_values(
            terrain_type="mountainous",
            grade_percent=4.0,
            segment_length_mi=1.3,
            heavy_vehicle_percent=5.0,
        ),
        _manual_values(
            segment_type="passing_zone",
            terrain_type="mountainous",
            grade_percent=4.0,
            segment_length_mi=1.3,
            heavy_vehicle_percent=8.0,
            opposing_direction_volume_veh_h=500.0,
        ),
    ],
)
def test_manual_unsupported_vertical_combinations_reject_before_calculation(
    values: dict,
) -> None:
    with pytest.raises(UnsupportedScopeError):
        run_manual_single_segment(values)


def test_engine_rejects_level_terrain_with_nonzero_grade_instead_of_falling_back() -> None:
    inputs = {
        key: value
        for key, value in _manual_values(
            terrain_type="level", grade_percent=4.0
        ).items()
        if key != "terrain_type"
    }
    inputs.update(
        {
            "terrain_type": "level",
            "grade_length_mi": 0.75,
            "horizontal_alignment_subsegments": [],
        }
    )

    with pytest.raises(UnsupportedScopeError, match="fall back to level assumptions"):
        TwoLaneHighwayChapter15Method().calculate_single_segment(inputs)


def test_failed_scope_audit_has_context_and_no_outputs() -> None:
    values = _manual_values(
        unit_system="imperial",
        terrain_type="mountainous",
        grade_percent=4.0,
        segment_length_mi=1.0,
        heavy_vehicle_percent=8.0,
    )
    with pytest.raises(UnsupportedScopeError) as exc_info:
        run_manual_single_segment(values)

    audit = build_manual_calculation_audit_record(values, error=exc_info.value)

    assert audit["selected_segment_type"] == "passing_constrained"
    assert audit["selected_terrain_type"] == "mountainous"
    assert audit["selected_horizontal_alignment"] == "straight"
    assert audit["grade_percent"] == 4.0
    assert audit["grade_length"] == 1.0
    assert audit["heavy_vehicle_percent"] == 8.0
    assert audit["scope_status"] == "unsupported_needs_hcm_table_data"
    assert "Chapter 15 scope" in audit["unsupported_reason"]
    assert audit["normalized_engine_inputs"]
    assert audit["outputs"] == {}
    assert audit["intermediate_values"] == []


def test_require_supported_scope_error_carries_derived_vertical_class() -> None:
    with pytest.raises(UnsupportedScopeError) as exc_info:
        require_supported_vertical_scope(
            segment_type="passing_lane",
            grade_percent=4.0,
            grade_length_mi=1.3,
            heavy_vehicle_percent=8.0,
        )

    assert exc_info.value.scope_status == "unsupported_needs_hcm_table_data"
    assert exc_info.value.context["vertical_class"] == 4
