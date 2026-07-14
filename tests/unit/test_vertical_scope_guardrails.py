import pytest

from hcmcalc.core import UnsupportedScopeError
from hcmcalc.methods.two_lane_highway_scope import (
    classify_vertical_scope,
    require_supported_vertical_scope,
)
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method
from hcmcalc.ui.manual_segment import run_manual_single_segment


@pytest.mark.parametrize(
    ("segment_type", "grade", "length", "expected_class"),
    [
        ("passing_constrained", 0.0, 0.25, 1),
        ("passing_zone", 4.0, 0.5, 2),
        ("passing_lane", 6.0, 0.5, 4),
        ("passing_constrained", 4.0, 1.3, 4),
        ("passing_zone", -3.0, 1.0, 2),
    ],
)
def test_phase_1_scope_classifies_without_chapter_26_metadata(
    segment_type: str, grade: float, length: float, expected_class: int
) -> None:
    decision = classify_vertical_scope(
        segment_type=segment_type,
        grade_percent=grade,
        segment_length_mi=length,
        heavy_vehicle_percent=37.0,
    )

    assert decision.supported
    assert decision.vertical_class == expected_class
    assert decision.validation_basis is None
    assert decision.classification is not None
    assert decision.segment_length_applicability is not None
    assert decision.classification.source_reference.endswith("Exhibit 15-11: Classifications for vertical alignment")
    assert decision.segment_length_applicability.source_reference == "HCM7 Exhibit 15-10"


def test_submitted_vertical_class_must_match_exhibit_15_11() -> None:
    decision = classify_vertical_scope(
        segment_type="passing_constrained",
        grade_percent=4.0,
        segment_length_mi=1.3,
        heavy_vehicle_percent=8.0,
        vertical_class=5,
    )

    assert decision.status == "unsupported"
    assert decision.vertical_class == 4
    assert "does not match" in decision.reason


def test_legacy_grade_length_is_accepted_but_never_changes_classification() -> None:
    decision = classify_vertical_scope(
        segment_type="passing_constrained",
        grade_percent=4.0,
        segment_length_mi=1.3,
        grade_length_mi=0.5,
        heavy_vehicle_percent=8.0,
    )

    assert decision.supported
    assert decision.vertical_class == 4
    assert decision.normalized_legacy_grade_length_mi == 0.5


def test_outside_exhibit_15_10_is_distinguished_from_invalid_input() -> None:
    decision = classify_vertical_scope(
        segment_type="passing_zone",
        grade_percent=4.0,
        segment_length_mi=2.1,
        heavy_vehicle_percent=8.0,
    )

    assert decision.status == "outside_exhibit_15_10_applicability"
    assert decision.segment_length_applicability is not None
    assert decision.segment_length_applicability.submitted_segment_length_mi == 2.1

    invalid = classify_vertical_scope(
        segment_type="passing_constrained",
        grade_percent=4.0,
        segment_length_mi=float("nan"),
        heavy_vehicle_percent=8.0,
    )
    assert invalid.status == "invalid_input"


def test_phase_2_downstream_calculations_support_nonlevel_passing_constrained() -> None:
    decision = classify_vertical_scope(
        segment_type="passing_constrained",
        grade_percent=4.0,
        segment_length_mi=1.3,
        heavy_vehicle_percent=8.0,
        calculation_scope="steps_4_10",
    )

    assert decision.status == "supported"
    assert require_supported_vertical_scope(
        segment_type="passing_constrained",
        grade_percent=4.0,
        segment_length_mi=1.3,
        heavy_vehicle_percent=8.0,
        calculation_scope="steps_4_10",
    ).vertical_class == 4


def test_phase_2_single_segment_supports_nonlevel_passing_zone() -> None:
    values = {
        "segment_type": "passing_zone",
        "terrain_type": "mountainous",
        "horizontal_alignment": "straight",
        "posted_speed_mph": 55.0,
        "segment_length_mi": 0.5,
        "lane_width_ft": 12.0,
        "shoulder_width_ft": 6.0,
        "access_point_density_per_mi": 0.0,
        "analysis_direction_volume_veh_h": 800.0,
        "opposing_direction_volume_veh_h": 500.0,
        "peak_hour_factor": 0.94,
        "heavy_vehicle_percent": 8.0,
        "grade_percent": 4.0,
    }
    result = run_manual_single_segment(values)
    assert result.outputs["vertical_class"] == 2
    assert result.outputs["segment_type"] == "passing_zone"


def test_legacy_saved_project_shape_without_grade_length_still_loads_to_scope() -> None:
    decision = classify_vertical_scope(
        segment_type="passing_constrained",
        grade_percent=6.0,
        segment_length_mi=0.5,
        heavy_vehicle_percent=8.0,
    )

    assert decision.supported
    assert decision.normalized_legacy_grade_length_mi is None


def test_level_terrain_with_grade_remains_invalid() -> None:
    with pytest.raises(UnsupportedScopeError, match="non-zero grade"):
        require_supported_vertical_scope(
            segment_type="passing_constrained",
            terrain_type="level",
            grade_percent=4.0,
            segment_length_mi=0.75,
            heavy_vehicle_percent=8.0,
        )
