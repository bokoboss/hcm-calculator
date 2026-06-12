import math

import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import (
    PASSING_CONSTRAINED,
    PASSING_LANE,
    TwoLaneHighwayChapter15Method,
    estimate_passing_lane_flow_split,
    estimate_passing_lane_heavy_vehicles,
    estimate_passing_lane_midpoint_measures,
    estimate_passing_lane_midpoint_speeds,
    passing_lane_faster_lane_flow_proportion,
)


DEMAND_FLOW_RATE = 825.0 / 0.95
HEAVY_VEHICLE_PERCENT = 8.0


def test_eq_15_24_through_eq_15_30_passing_lane_flow_and_heavy_vehicle_split() -> None:
    estimate = estimate_passing_lane_flow_split(
        segment_type=PASSING_LANE,
        demand_flow_rate_veh_h=DEMAND_FLOW_RATE,
        heavy_vehicle_percent=HEAVY_VEHICLE_PERCENT,
    )

    expected_number_heavy_vehicles = DEMAND_FLOW_RATE * 0.08
    expected_proportion = (
        0.92183
        - 0.05022 * math.log(DEMAND_FLOW_RATE)
        - 0.00030 * expected_number_heavy_vehicles
    )
    expected_faster_flow = DEMAND_FLOW_RATE * expected_proportion
    expected_slower_flow = DEMAND_FLOW_RATE * (1.0 - expected_proportion)
    expected_faster_hv_percent = HEAVY_VEHICLE_PERCENT * 0.4
    expected_slower_hv_count = (
        expected_number_heavy_vehicles
        - expected_faster_flow * expected_faster_hv_percent / 100.0
    )

    assert estimate.number_heavy_vehicles == pytest.approx(
        expected_number_heavy_vehicles
    )
    assert estimate.faster_lane_flow_proportion == pytest.approx(expected_proportion)
    assert estimate.faster_lane_flow_rate == pytest.approx(expected_faster_flow)
    assert estimate.slower_lane_flow_rate == pytest.approx(expected_slower_flow)
    assert estimate.faster_lane_heavy_vehicle_percent == pytest.approx(
        expected_faster_hv_percent
    )
    assert estimate.slower_lane_heavy_vehicle_count == pytest.approx(
        expected_slower_hv_count
    )
    assert estimate.slower_lane_heavy_vehicle_percent == pytest.approx(
        expected_slower_hv_count / expected_slower_flow * 100.0
    )
    assert estimate.source_references == tuple(
        f"HCM Eq. 15-{equation}" for equation in range(24, 31)
    )


def test_eq_15_31_through_eq_15_33_passing_lane_midpoint_speeds() -> None:
    differential, faster_speed, slower_speed = estimate_passing_lane_midpoint_speeds(
        segment_type=PASSING_LANE,
        demand_flow_rate_veh_h=DEMAND_FLOW_RATE,
        heavy_vehicle_percent=HEAVY_VEHICLE_PERCENT,
        faster_lane_initial_speed_mph=60.7,
        slower_lane_initial_speed_mph=60.6,
    )

    expected_differential = (
        2.750 + 0.00056 * DEMAND_FLOW_RATE + 3.8521 * HEAVY_VEHICLE_PERCENT / 100.0
    )
    assert differential == pytest.approx(expected_differential)
    assert faster_speed == pytest.approx(60.7 + expected_differential / 2.0)
    assert slower_speed == pytest.approx(60.6 - expected_differential / 2.0)


def test_step7_combined_estimate_exposes_eq_15_24_through_eq_15_33_sources() -> None:
    estimate = estimate_passing_lane_midpoint_measures(
        segment_type=PASSING_LANE,
        demand_flow_rate_veh_h=DEMAND_FLOW_RATE,
        heavy_vehicle_percent=HEAVY_VEHICLE_PERCENT,
        faster_lane_initial_speed_mph=60.7,
        slower_lane_initial_speed_mph=60.6,
    )

    assert estimate.faster_lane_flow_rate > estimate.slower_lane_flow_rate
    assert estimate.faster_lane_midpoint_speed > 60.7
    assert estimate.slower_lane_midpoint_speed < 60.6
    assert estimate.source_references == tuple(
        f"HCM Eq. 15-{equation}" for equation in range(24, 34)
    )


def test_supported_passing_lane_exposes_step7_audit_values() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        {
            "segment_type": PASSING_LANE,
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
    names = {value.name for value in result.intermediate_values}

    assert result.outputs["passing_lane_number_heavy_vehicles"] == pytest.approx(
        DEMAND_FLOW_RATE * 0.08
    )
    assert result.outputs["passing_lane_faster_lane_midpoint_speed"] == pytest.approx(
        result.outputs["faster_lane_midpoint_average_speed_mph"]
    )
    assert "HCM Eq. 15-24" in result.outputs["passing_lane_step7_source_reference"]
    assert "HCM Eq. 15-33" in result.outputs["passing_lane_step7_source_reference"]
    assert {
        "passing_lane_number_heavy_vehicles",
        "passing_lane_faster_lane_flow_proportion",
        "passing_lane_faster_lane_flow_rate",
        "passing_lane_slower_lane_flow_rate",
        "passing_lane_faster_lane_heavy_vehicle_percent",
        "passing_lane_slower_lane_heavy_vehicle_percent",
        "passing_lane_speed_differential_adjustment",
        "passing_lane_faster_lane_midpoint_speed",
        "passing_lane_slower_lane_midpoint_speed",
        "passing_lane_step7_source_reference",
    } <= names


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"segment_type": PASSING_CONSTRAINED}, "require a Passing Lane segment"),
        ({"demand_flow_rate_veh_h": None}, "demand flow rate is required"),
        ({"demand_flow_rate_veh_h": 0.0}, "demand flow rate must be greater than zero"),
        ({"demand_flow_rate_veh_h": float("nan")}, "demand flow rate must be a finite"),
        ({"heavy_vehicle_percent": None}, "heavy vehicle percent is required"),
        ({"heavy_vehicle_percent": -0.1}, "heavy vehicle percent must be between"),
        ({"heavy_vehicle_percent": 100.1}, "heavy vehicle percent must be between"),
        (
            {"heavy_vehicle_proportion_multiplier_faster_lane": None},
            "proportion multiplier is required",
        ),
        (
            {"heavy_vehicle_proportion_multiplier_faster_lane": 0.5},
            "supports only the HCM-defined",
        ),
    ],
)
def test_step7_flow_split_invalid_inputs_are_rejected_clearly(
    overrides: dict[str, object],
    message: str,
) -> None:
    inputs: dict[str, object] = {
        "segment_type": PASSING_LANE,
        "demand_flow_rate_veh_h": DEMAND_FLOW_RATE,
        "heavy_vehicle_percent": HEAVY_VEHICLE_PERCENT,
        "heavy_vehicle_proportion_multiplier_faster_lane": 0.4,
    }
    inputs.update(overrides)

    with pytest.raises(HCMCalcError, match=message):
        estimate_passing_lane_flow_split(**inputs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"faster_lane_initial_speed_mph": None}, "initial speed is required"),
        ({"faster_lane_initial_speed_mph": 0.0}, "initial speed must be greater"),
        ({"slower_lane_initial_speed_mph": -1.0}, "initial speed must be greater"),
        ({"slower_lane_initial_speed_mph": float("inf")}, "initial speed must be a finite"),
        (
            {"slower_lane_initial_speed_mph": 1.0},
            "computed slower-lane midpoint speed must be greater than zero",
        ),
    ],
)
def test_step7_midpoint_speed_invalid_inputs_are_rejected_clearly(
    overrides: dict[str, object],
    message: str,
) -> None:
    inputs: dict[str, object] = {
        "segment_type": PASSING_LANE,
        "demand_flow_rate_veh_h": DEMAND_FLOW_RATE,
        "heavy_vehicle_percent": HEAVY_VEHICLE_PERCENT,
        "faster_lane_initial_speed_mph": 60.7,
        "slower_lane_initial_speed_mph": 60.6,
    }
    inputs.update(overrides)

    with pytest.raises(HCMCalcError, match=message):
        estimate_passing_lane_midpoint_speeds(**inputs)  # type: ignore[arg-type]


def test_step7_invalid_computed_faster_lane_flow_proportion_is_rejected() -> None:
    with pytest.raises(HCMCalcError, match="faster-lane flow proportion"):
        passing_lane_faster_lane_flow_proportion(
            demand_flow_rate_veh_h=1000.0,
            heavy_vehicle_count_veh_h=10000.0,
        )


def test_eq_15_24_rejects_zero_demand_flow() -> None:
    with pytest.raises(HCMCalcError, match="demand flow rate must be greater than zero"):
        estimate_passing_lane_heavy_vehicles(
            segment_type=PASSING_LANE,
            demand_flow_rate_veh_h=0.0,
            heavy_vehicle_percent=8.0,
        )
