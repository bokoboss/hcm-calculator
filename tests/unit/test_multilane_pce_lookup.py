"""Independent checks for HCM7 Exhibits 12-25 through 12-28."""

import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.multilane.coefficients import (
    PCE_GRADE_LENGTHS_MI,
    PCE_TRUCK_PERCENT_COLUMNS,
    SPECIFIC_GRADE_PCE,
)
from hcmcalc.multilane.method import (
    heavy_vehicle_adjustment_factor,
    specific_grade_passenger_car_equivalent,
    total_lateral_clearance,
    total_lateral_clearance_adjustment,
)


def test_exhibits_12_26_to_12_28_have_complete_reviewed_grid_structure() -> None:
    """Every stored row is complete and keys match the visually reviewed exhibits."""

    assert set(SPECIFIC_GRADE_PCE) == {30, 50, 70}
    assert PCE_TRUCK_PERCENT_COLUMNS == (2, 4, 5, 6, 8, 10, 15, 20, 25)
    for grid in SPECIFIC_GRADE_PCE.values():
        assert set(grid) == set(PCE_GRADE_LENGTHS_MI)
        for grade, rows in grid.items():
            assert tuple(rows) == PCE_GRADE_LENGTHS_MI[grade]
            assert all(len(row) == len(PCE_TRUCK_PERCENT_COLUMNS) for row in rows.values())
            # PCE decreases as total heavy-vehicle share grows at every table row.
            assert all(all(a >= b for a, b in zip(row, row[1:])) for row in rows.values())


@pytest.mark.parametrize(
    ("sut_share", "grade", "length", "truck_percent", "expected"),
    [
        (30, -2, 1.25, 6, 2.24),  # Exhibit 12-26 / Ch. 26 Example 4 downgrade
        (30, 3.5, 1.25, 6, 3.97),  # Exhibit 12-26 / Ch. 26 Example 4 upgrade
        (50, 6, 1.0, 2, 12.15),  # Exhibit 12-27 endpoint
        (70, 4.5, 0.625, 10, 3.10),  # Exhibit 12-28 sentinel row
    ],
)
def test_specific_grade_pce_exact_exhibit_cells(
    sut_share: float, grade: float, length: float, truck_percent: float, expected: float
) -> None:
    assert specific_grade_passenger_car_equivalent(
        sut_percent=sut_share,
        grade_percent=grade,
        grade_length_mi=length,
        heavy_vehicle_percent=truck_percent,
    ) == pytest.approx(expected)


def test_specific_grade_pce_interpolates_each_exhibit_axis() -> None:
    # HCM7 Exhibits 12-26--12-28 permit interpolation. Expected values are
    # independently hand-computed linear midpoints of printed table cells.
    assert specific_grade_passenger_car_equivalent(
        sut_percent=30, grade_percent=3.5, grade_length_mi=0.5, heavy_vehicle_percent=6
    ) == pytest.approx((3.05 + 3.58) / 2)
    assert specific_grade_passenger_car_equivalent(
        sut_percent=30, grade_percent=3.5, grade_length_mi=0.625, heavy_vehicle_percent=7
    ) == pytest.approx((3.58 + 3.20) / 2)
    assert specific_grade_passenger_car_equivalent(
        sut_percent=30, grade_percent=3.0, grade_length_mi=0.625, heavy_vehicle_percent=6
    ) == pytest.approx((3.11 + 3.58) / 2)


def test_specific_grade_pce_rejects_extrapolation_and_unsupported_sparse_cells() -> None:
    with pytest.raises(UnsupportedScopeError, match="extrapolation"):
        specific_grade_passenger_car_equivalent(
            sut_percent=30, grade_percent=6, grade_length_mi=1.1, heavy_vehicle_percent=6
        )
    with pytest.raises(UnsupportedScopeError, match="grades"):
        specific_grade_passenger_car_equivalent(
            sut_percent=30, grade_percent=6.1, grade_length_mi=1, heavy_vehicle_percent=6
        )
    with pytest.raises(UnsupportedScopeError, match="above 20%"):
        specific_grade_passenger_car_equivalent(
            sut_percent=30, grade_percent=3.5, grade_length_mi=0.625, heavy_vehicle_percent=20.1
        )


def test_equation_12_10_and_divided_median_clearance_are_not_double_applied() -> None:
    # Eq. 12-10 uses total heavy-vehicle share once with the selected composite PCE.
    assert heavy_vehicle_adjustment_factor(6, 3.97) == pytest.approx(1 / (1 + 0.06 * (3.97 - 1)))
    assert heavy_vehicle_adjustment_factor(0, 12.15) == 1
    assert total_lateral_clearance(4, "divided", 2) == 6
    assert total_lateral_clearance_adjustment(6, 2) == 1.3
    with pytest.raises(HCMCalcError, match="requires"):
        total_lateral_clearance(4, "divided")
    with pytest.raises(HCMCalcError, match="not applicable"):
        total_lateral_clearance(4, "twltl", 2)
