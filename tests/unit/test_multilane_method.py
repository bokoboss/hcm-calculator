import pytest

from hcmcalc.core import UnsupportedScopeError
from hcmcalc.multilane.method import (
    access_point_adjustment,
    adjusted_free_flow_speed,
    demand_flow_rate,
    example_4_passenger_car_equivalent,
    heavy_vehicle_adjustment_factor,
    lane_width_adjustment,
    level_of_service,
    mean_speed_below_breakpoint,
    multilane_capacity,
    total_lateral_clearance,
    total_lateral_clearance_adjustment,
    traffic_density,
)


def test_example_4_free_flow_speed_adjustments_and_capacity() -> None:
    assert lane_width_adjustment(12.0) == 0.0
    assert total_lateral_clearance(12.0, "twltl") == 12.0
    assert total_lateral_clearance_adjustment(12.0) == 0.0
    assert total_lateral_clearance_adjustment(11.0) == pytest.approx(0.2)
    assert access_point_adjustment(0.0) == 0.0
    assert access_point_adjustment(10.0) == 2.5
    assert access_point_adjustment(40.0) == 10.0
    assert adjusted_free_flow_speed(52.0, 0.0, 0.0, 0.0, 2.5) == 49.5
    assert multilane_capacity(49.5) == 1990.0
    assert multilane_capacity(52.0) == 2040.0


def test_example_4_heavy_vehicle_flow_density_and_los() -> None:
    pce = example_4_passenger_car_equivalent(
        -3.5, 1.25, 6.0, "default_30_sut_70_tt"
    )
    hv_factor = heavy_vehicle_adjustment_factor(6.0, pce)
    flow = demand_flow_rate(1500.0, 0.90, 2, hv_factor)
    speed = mean_speed_below_breakpoint(flow, 49.5)
    density = traffic_density(flow, speed)

    assert pce == 2.24
    assert hv_factor == pytest.approx(0.93, abs=0.01)
    assert flow == pytest.approx(896.0, abs=1.0)
    assert density == pytest.approx(18.1, abs=0.1)
    assert level_of_service(density) == "C"


@pytest.mark.parametrize(
    ("density", "expected"),
    [(11.0, "A"), (18.0, "B"), (26.0, "C"), (35.0, "D"), (45.0, "E"), (45.1, "F")],
)
def test_los_boundaries(density: float, expected: str) -> None:
    assert level_of_service(density) == expected


def test_formula_helpers_reject_unimplemented_branches() -> None:
    with pytest.raises(UnsupportedScopeError, match="below-breakpoint"):
        mean_speed_below_breakpoint(1400.1, 50.0)
    with pytest.raises(UnsupportedScopeError, match="between 0 and 40"):
        access_point_adjustment(40.1)
