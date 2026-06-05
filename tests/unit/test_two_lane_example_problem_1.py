import pytest

from hcmcalc.methods.two_lane_highway_ch15 import (
    average_speed,
    base_free_flow_speed,
    demand_flow_rate,
    estimated_free_flow_speed,
    follower_density,
    level_of_service,
    passing_constrained_capacity,
    percent_followers,
    vertical_alignment_class,
)


def test_example_problem_1_formula_helpers() -> None:
    demand = demand_flow_rate(analysis_hour_volume_veh=760.0, peak_hour_factor=0.95)
    capacity = passing_constrained_capacity()
    vertical_class = vertical_alignment_class("level")
    bffs = base_free_flow_speed(
        posted_speed_mph=55.0,
        base_speed_over_posted_mph=2.0,
    )
    ffs = estimated_free_flow_speed(
        base_free_flow_speed_mph=bffs,
        lane_shoulder_adjustment_mph=0.17,
    )
    speed = average_speed(
        free_flow_speed_mph=ffs,
        demand_flow_rate_veh_h=demand,
        speed_demand_coefficient=0.0039125,
    )
    followers = percent_followers(
        demand_flow_rate_veh_h=demand,
        percent_followers_coefficient=0.00141262869469935,
    )
    density = follower_density(
        demand_flow_rate_veh_h=demand,
        average_speed_mph=speed,
        percent_followers_value=followers,
    )

    assert demand == 800.0
    assert capacity == 1700.0
    assert demand / capacity < 1.0
    assert vertical_class == 1
    assert bffs == 57.0
    assert ffs == pytest.approx(56.83, abs=0.1)
    assert speed == pytest.approx(53.7, abs=0.1)
    assert followers == pytest.approx(67.7, abs=0.2)
    assert density == pytest.approx(10.1, abs=0.1)
    assert level_of_service(density) == "D"
