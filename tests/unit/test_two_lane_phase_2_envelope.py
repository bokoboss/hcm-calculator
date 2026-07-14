"""Phase 2 non-example method-conformance coverage.

These are deliberately not Chapter 26 examples.  Their expected class,
applicability, demand, capacity, and opposing-flow values are independently
transparent inputs to the HCM sequence; equation-level fixtures cover the
remaining coefficient calculations.
"""

from __future__ import annotations

import pytest

from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method


def _inputs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "horizontal_alignment": "straight",
        "posted_speed_mph": 55.0,
        "segment_length_mi": 0.5,
        "lane_width_ft": 12.0,
        "shoulder_width_ft": 6.0,
        "access_point_density_per_mi": 0.0,
        "analysis_direction_volume_veh_h": 800.0,
        "peak_hour_factor": 0.95,
        "heavy_vehicle_percent": 8.0,
        "grade_percent": 0.0,
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("grade_percent", "expected_class"),
    [(3.0, 2), (5.0, 3), (6.0, 4), (7.0, 5)],
)
def test_nonexample_passing_constrained_supports_each_nonlevel_class(
    grade_percent: float, expected_class: int
) -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        _inputs(terrain_type="mountainous", grade_percent=grade_percent)
    )

    assert result.outputs["vertical_class"] == expected_class
    assert result.outputs["capacity_veh_h"] == 1700.0
    assert result.outputs["opposing_flow_rate_veh_h"] == 1500.0
    assert result.outputs["follower_density_followers_mi_ln"] >= 0.0


def test_nonexample_passing_zone_uses_submitted_opposing_flow_and_downgrade() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        _inputs(
            segment_type="passing_zone",
            terrain_type="mountainous",
            grade_percent=-7.0,
            opposing_direction_volume_veh_h=475.0,
            peak_hour_factor=0.95,
            heavy_vehicle_percent=15.0,
        )
    )

    assert result.outputs["vertical_class"] == 4
    assert result.outputs["vertical_direction"] == "downgrade"
    assert result.outputs["opposing_flow_rate_veh_h"] == pytest.approx(500.0)
    assert result.outputs["opposing_flow_derivation"] == "submitted opposing-direction volume / PHF"


def test_general_horizontal_curve_accepts_non_example_subsegment_count() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        _inputs(
            horizontal_alignment="horizontal_curves",
            horizontal_alignment_subsegments=[
                {"subsegment_type": "tangent", "length_ft": 1000.0},
                {
                    "subsegment_type": "horizontal_curve",
                    "length_ft": 800.0,
                    "radius_ft": 800.0,
                    "superelevation_percent": 2.0,
                },
                {"subsegment_type": "tangent", "length_ft": 840.0},
            ],
        )
    )

    assert result.outputs["horizontal_curve_subsegment_count"] == 3
    assert result.outputs["horizontal_curve_adjustment_applied"] is True


@pytest.mark.parametrize(
    ("volume", "expected_exceeded"), [(0.0, False), (1615.0, False), (1615.1, True)])
def test_capacity_boundary_is_exposed_without_clamping(
    volume: float, expected_exceeded: bool
) -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        _inputs(analysis_direction_volume_veh_h=volume)
    )

    assert result.outputs["demand_flow_rate_veh_h"] == pytest.approx(volume / 0.95)
    assert result.outputs["capacity_exceeded"] is expected_exceeded
    if expected_exceeded:
        assert result.outputs["level_of_service"] == "F"
