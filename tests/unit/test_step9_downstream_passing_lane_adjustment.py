from pathlib import Path

import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import (
    TwoLaneHighwayChapter15Method,
    downstream_percent_followers_improvement,
    downstream_speed_improvement,
    estimate_adjusted_downstream_follower_density,
    estimate_passing_lane_downstream_adjustment,
)
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def _step9_inputs() -> dict[str, object]:
    return {
        "downstream_segment_affected_by_passing_lane": True,
        "downstream_distance_mi": 2.5,
        "passing_lane_length_mi": 1.5,
        "percent_followers": 68.0,
        "entering_passing_lane_percent_followers": 69.7,
        "flow_rate": 820.0 / 0.95,
        "average_speed": 58.9,
        "unadjusted_follower_density": 10.0,
    }


def test_eq_15_36_representative_percent_followers_improvement() -> None:
    improvement = downstream_percent_followers_improvement(
        2.5, 69.7, 1.5, 820.0 / 0.95
    )

    assert improvement == pytest.approx(15.7, abs=0.1)


def test_eq_15_37_representative_speed_improvement() -> None:
    improvement = downstream_speed_improvement(2.5, 69.7, 1.5, 820.0 / 0.95)

    assert improvement == pytest.approx(1.8, abs=0.1)


def test_eq_15_38_representative_adjusted_follower_density() -> None:
    density = estimate_adjusted_downstream_follower_density(
        percent_followers=68.0,
        flow_rate=820.0 / 0.95,
        average_speed=58.9,
        downstream_percent_followers_improvement=15.7,
        downstream_speed_improvement=1.8,
    )

    assert density == pytest.approx(8.2, abs=0.1)


def test_step9_estimate_exposes_auditable_inputs_outputs_and_sources() -> None:
    estimate = estimate_passing_lane_downstream_adjustment(**_step9_inputs())

    assert estimate.downstream_adjustment_applied is True
    assert estimate.downstream_distance_mi == 2.5
    assert estimate.passing_lane_length_mi == 1.5
    assert estimate.unadjusted_percent_followers == 68.0
    assert estimate.entering_passing_lane_percent_followers == 69.7
    assert estimate.unadjusted_average_speed == 58.9
    assert estimate.unadjusted_flow_rate == pytest.approx(820.0 / 0.95)
    assert estimate.unadjusted_follower_density == 10.0
    assert estimate.source_references == (
        "HCM Eq. 15-36",
        "HCM Eq. 15-37",
        "HCM Eq. 15-38",
    )


def test_eq_15_36_and_eq_15_37_floor_improvements_at_zero() -> None:
    assert downstream_percent_followers_improvement(30.0, 30.0, 0.3, 2000.0) == 0
    assert downstream_speed_improvement(30.0, 30.0, 0.3, 2000.0) == 0


def test_eq_15_36_uses_minimum_log_downstream_distance() -> None:
    assert downstream_percent_followers_improvement(
        0.0, 69.7, 1.5, 863.0
    ) == pytest.approx(
        downstream_percent_followers_improvement(0.1, 69.7, 1.5, 863.0)
    )


def test_eq_15_36_uses_minimum_log_passing_lane_length() -> None:
    assert downstream_percent_followers_improvement(
        2.5, 69.7, 0.1, 863.0
    ) == pytest.approx(
        downstream_percent_followers_improvement(2.5, 69.7, 0.3, 863.0)
    )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"downstream_distance_mi": None}, "downstream distance is required"),
        ({"downstream_distance_mi": -0.1}, "downstream distance must be nonnegative"),
        ({"downstream_distance_mi": float("nan")}, "downstream distance must be a finite"),
        ({"passing_lane_length_mi": None}, "passing lane length is required"),
        ({"passing_lane_length_mi": 0.0}, "passing lane length must be greater than zero"),
        ({"percent_followers": None}, "subject-segment percent followers is required"),
        ({"percent_followers": -0.1}, "subject-segment percent followers"),
        ({"percent_followers": 100.1}, "subject-segment percent followers"),
        (
            {"entering_passing_lane_percent_followers": float("inf")},
            "entering-passing-lane percent followers",
        ),
        ({"flow_rate": None}, "flow rate is required"),
        ({"flow_rate": 0.0}, "flow rate must be greater than zero"),
        ({"average_speed": None}, "average speed is required"),
        ({"average_speed": 0.0}, "average speed must be greater than zero"),
        (
            {"unadjusted_follower_density": None},
            "unadjusted follower density is required",
        ),
    ],
)
def test_step9_invalid_inputs_are_rejected_clearly(
    overrides: dict[str, object], message: str
) -> None:
    inputs = _step9_inputs()
    inputs.update(overrides)

    with pytest.raises(HCMCalcError, match=message):
        estimate_passing_lane_downstream_adjustment(**inputs)  # type: ignore[arg-type]


def test_step9_rejects_unmarked_downstream_context() -> None:
    inputs = _step9_inputs()
    inputs["downstream_segment_affected_by_passing_lane"] = False

    with pytest.raises(HCMCalcError, match="explicitly identified downstream segment"):
        estimate_passing_lane_downstream_adjustment(**inputs)  # type: ignore[arg-type]


def test_manual_single_segment_passing_lane_does_not_apply_step9() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        {
            "segment_type": "passing_lane",
            "segment_length_mi": 1.5,
            "posted_speed_mph": 55.0,
            "analysis_direction_volume_veh_h": 825.0,
            "peak_hour_factor": 0.95,
            "heavy_vehicle_percent": 8.0,
            "grade_percent": 0.0,
            "horizontal_alignment": "straight",
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
        }
    )

    assert "downstream_adjustment_applied" not in result.outputs
    assert any("downstream passing-lane effects" in warning for warning in result.warnings)


def test_validated_facility_downstream_segment_exposes_step9_audit_fields() -> None:
    fixture = load_yaml_fixture(ROOT / "references" / "example_inputs.yaml")
    case = next(case for case in fixture["cases"] if case["id"] == "TLH-CH15-004")
    result = TwoLaneHighwayChapter15Method().calculate(case["inputs"])
    downstream_segment = result.outputs["segments"][5]
    intermediate_names = {value.name for value in result.intermediate_values}

    assert downstream_segment["downstream_adjustment_applied"] is True
    assert downstream_segment["downstream_percent_followers_improvement"] == pytest.approx(
        18.0, abs=0.1
    )
    assert downstream_segment["downstream_speed_improvement"] == pytest.approx(
        2.2, abs=0.1
    )
    assert downstream_segment["adjusted_follower_density"] == pytest.approx(
        13.2, abs=0.1
    )
    assert downstream_segment["passing_lane_downstream_source_reference"] == (
        "HCM Eq. 15-36, HCM Eq. 15-37, HCM Eq. 15-38"
    )
    assert {
        "segment_6_downstream_adjustment_applied",
        "segment_6_downstream_distance",
        "segment_6_passing_lane_length",
        "segment_6_unadjusted_percent_followers",
        "segment_6_unadjusted_average_speed",
        "segment_6_unadjusted_flow_rate",
        "segment_6_unadjusted_follower_density",
        "segment_6_passing_lane_downstream_source_reference",
    } <= intermediate_names


def test_eq_15_38_rejects_non_finite_computed_density() -> None:
    with pytest.raises(HCMCalcError, match="computed adjusted follower density"):
        estimate_adjusted_downstream_follower_density(
            percent_followers=100.0,
            flow_rate=1e308,
            average_speed=5e-324,
            downstream_percent_followers_improvement=0.0,
            downstream_speed_improvement=0.0,
        )
