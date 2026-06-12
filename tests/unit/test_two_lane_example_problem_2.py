import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import (
    HorizontalAlignmentSubsegment,
    TwoLaneHighwayChapter15Method,
    classify_horizontal_alignment,
    horizontal_curve_average_speed,
    horizontal_curve_base_free_flow_speed,
    horizontal_curve_free_flow_speed,
    horizontal_curve_speed_coefficient_m,
    horizontal_curve_subsegment_speeds,
    length_weighted_adjusted_average_speed,
)


EXAMPLE_2_SUBSEGMENTS = (
    HorizontalAlignmentSubsegment("tangent", 280.0),
    HorizontalAlignmentSubsegment("horizontal_curve", 432.0, 3.0, 450.0, 55.0, 3),
    HorizontalAlignmentSubsegment("tangent", 260.0),
    HorizontalAlignmentSubsegment("horizontal_curve", 366.5, 2.0, 300.0, 70.0, 4),
    HorizontalAlignmentSubsegment("tangent", 250.0),
    HorizontalAlignmentSubsegment("horizontal_curve", 216.0, 5.0, 275.0, 45.0, 5),
    HorizontalAlignmentSubsegment("tangent", 275.6),
    HorizontalAlignmentSubsegment("horizontal_curve", 458.0, 0.0, 750.0, 35.0, 2),
    HorizontalAlignmentSubsegment("tangent", 285.0),
    HorizontalAlignmentSubsegment("horizontal_curve", 767.9, 4.0, 1100.0, 40.0, 1),
    HorizontalAlignmentSubsegment("tangent", 369.0),
)

EXAMPLE_2_INPUTS = {
    "case_id": "TLH-CH15-002",
    "segment_length_mi": 0.75,
    "segment_type": "passing_constrained",
    "analysis_direction_volume_veh_h": 752.0,
    "peak_hour_factor": 0.94,
    "posted_speed_mph": 50.0,
    "heavy_vehicle_percent": 5.0,
    "grade_percent": 0.0,
    "horizontal_alignment": "horizontal_curves",
    "lane_width_ft": 12.0,
    "shoulder_width_ft": 6.0,
    "access_point_density_per_mi": 0.0,
    "upstream_passing_lane": False,
    "horizontal_alignment_subsegments": [
        {
            "type": subsegment.subsegment_type,
            "length_ft": subsegment.length_ft,
            "superelevation_percent": subsegment.superelevation_percent,
            "radius_ft": subsegment.radius_ft,
            "central_angle_deg": subsegment.central_angle_deg,
            "horizontal_class": subsegment.horizontal_class,
        }
        for subsegment in EXAMPLE_2_SUBSEGMENTS
    ],
}

EXPECTED_CURVE_VALUES = {
    2: (44.9656, 44.8381, 0.9145, 44.1),
    4: (38.0976, 37.9701, 0.4081, 37.6),
    6: (31.2296, 31.1021, 0.2770, 30.9),
    8: (51.8336, 51.7061, 1.4905, 50.5),
    10: (57.0000, 56.8725, 2.8036, 53.7),
}


@pytest.mark.parametrize(
    ("horizontal_class", "expected_bffs"),
    [(3, 44.9656), (4, 38.0976), (5, 31.2296), (2, 51.8336), (1, 57.0)],
)
def test_horizontal_curve_base_free_flow_speed(horizontal_class, expected_bffs) -> None:
    assert horizontal_curve_base_free_flow_speed(57.0, horizontal_class) == pytest.approx(
        expected_bffs,
        abs=0.1,
    )


def test_horizontal_curve_free_flow_speed() -> None:
    assert horizontal_curve_free_flow_speed(44.9656, 5.0) == pytest.approx(
        44.8381,
        abs=0.1,
    )


@pytest.mark.parametrize(
    ("horizontal_class", "curve_ffs", "expected_m"),
    [
        (3, 44.8381, 0.9145),
        (4, 37.9701, 0.4081),
        (5, 31.1021, 0.2770),
        (2, 51.7061, 1.4905),
        (1, 56.8725, 2.8036),
    ],
)
def test_horizontal_curve_speed_coefficient_m(
    horizontal_class, curve_ffs, expected_m
) -> None:
    assert horizontal_curve_speed_coefficient_m(curve_ffs, horizontal_class) == pytest.approx(
        expected_m,
        abs=0.0001,
    )


def test_horizontal_curve_average_speed() -> None:
    assert horizontal_curve_average_speed(
        horizontal_curve_free_flow_speed_mph=44.8381,
        demand_flow_rate_veh_h=800.0,
        speed_coefficient_m=0.9145,
        tangent_average_speed_mph=53.7,
    ) == pytest.approx(44.1, abs=0.1)


def test_length_weighted_adjusted_average_speed() -> None:
    subsegment_results = horizontal_curve_subsegment_speeds(
        subsegments=EXAMPLE_2_SUBSEGMENTS,
        base_free_flow_speed_mph=57.0,
        heavy_vehicle_percent=5.0,
        demand_flow_rate_veh_h=800.0,
        tangent_average_speed_mph=53.7,
    )

    assert length_weighted_adjusted_average_speed(subsegment_results) == pytest.approx(
        49.5,
        abs=0.1,
    )


def test_example_problem_2_horizontal_curve_outputs() -> None:
    result = TwoLaneHighwayChapter15Method().calculate(EXAMPLE_2_INPUTS)

    assert result.outputs["base_free_flow_speed_mph"] == pytest.approx(57.0)
    assert result.outputs["tangent_free_flow_speed_mph"] == pytest.approx(56.83, abs=0.1)
    assert result.outputs["tangent_average_speed_mph"] == pytest.approx(53.7, abs=0.1)
    assert result.outputs["adjusted_average_speed_mph"] == pytest.approx(49.5, abs=0.1)
    assert result.outputs["horizontal_curve_adjustment_applied"] is True
    assert result.outputs["horizontal_curve_subsegment_count"] == 11
    assert result.outputs["horizontal_classification_source_reference"] == (
        "HCM7 Exhibit 15-22"
    )
    assert result.outputs["weighted_average_speed_source_reference"] == "HCM Eq. 15-16"

    curve_results = {
        subsegment["index"]: subsegment
        for subsegment in result.outputs["horizontal_curve_subsegments"]
        if subsegment["subsegment_type"] == "horizontal_curve"
    }

    for index, expected_values in EXPECTED_CURVE_VALUES.items():
        expected_bffs, expected_ffs, expected_m, expected_speed = expected_values
        assert curve_results[index]["base_free_flow_speed_mph"] == pytest.approx(
            expected_bffs,
            abs=0.1,
        )
        assert curve_results[index]["free_flow_speed_mph"] == pytest.approx(
            expected_ffs,
            abs=0.1,
        )
        assert curve_results[index]["speed_coefficient_m"] == pytest.approx(
            expected_m,
            abs=0.0001,
        )
        assert curve_results[index]["average_speed_mph"] == pytest.approx(
            expected_speed,
            abs=0.1,
        )
        assert curve_results[index]["horizontal_classification_source_reference"] == (
            "HCM7 Exhibit 15-22"
        )


@pytest.mark.parametrize(
    ("radius_ft", "superelevation_percent", "expected_class"),
    [
        (1100.0, 4.0, 1),
        (750.0, 0.0, 2),
        (450.0, 3.0, 3),
        (300.0, 2.0, 4),
        (275.0, 5.0, 5),
    ],
)
def test_exhibit_15_22_representative_classes(
    radius_ft, superelevation_percent, expected_class
) -> None:
    classification = classify_horizontal_alignment(radius_ft, superelevation_percent)

    assert classification.horizontal_class == expected_class
    assert classification.source_reference == "HCM7 Exhibit 15-22"


@pytest.mark.parametrize(
    ("radius_ft", "superelevation_percent", "expected_class"),
    [
        (299.999, 0.0, 5),
        (300.0, 0.0, 4),
        (449.999, 0.0, 4),
        (450.0, 0.0, 4),
        (599.999, 6.0, 3),
        (600.0, 6.0, 2),
        (2549.999, 0.0, 1),
    ],
)
def test_exhibit_15_22_radius_boundaries(
    radius_ft, superelevation_percent, expected_class
) -> None:
    assert (
        classify_horizontal_alignment(radius_ft, superelevation_percent).horizontal_class
        == expected_class
    )


@pytest.mark.parametrize(
    ("superelevation_percent", "expected_class"),
    [(0.999, 4), (1.0, 3), (1.999, 3), (2.0, 3), (10.0, 3)],
)
def test_exhibit_15_22_superelevation_boundaries(
    superelevation_percent, expected_class
) -> None:
    assert (
        classify_horizontal_alignment(450.0, superelevation_percent).horizontal_class
        == expected_class
    )


@pytest.mark.parametrize(
    ("radius_ft", "superelevation_percent"),
    [(2550.0, 0.0), (1500.0, 8.0), (1350.0, 10.0)],
)
def test_exhibit_15_22_dash_cells_are_rejected(
    radius_ft, superelevation_percent
) -> None:
    with pytest.raises(HCMCalcError, match="Unsupported radius/superelevation"):
        classify_horizontal_alignment(radius_ft, superelevation_percent)


def test_horizontal_class_is_computed_when_not_supplied() -> None:
    subsegments = (
        HorizontalAlignmentSubsegment("tangent", 100.0),
        HorizontalAlignmentSubsegment("horizontal_curve", 100.0, 3.0, 450.0),
    )

    results = horizontal_curve_subsegment_speeds(
        subsegments,
        base_free_flow_speed_mph=57.0,
        heavy_vehicle_percent=5.0,
        demand_flow_rate_veh_h=800.0,
        tangent_average_speed_mph=53.7,
    )

    assert results[1]["horizontal_class"] == 3
    assert results[1]["matched_radius_bin"] == "450-599 ft"
    assert results[1]["matched_superelevation_bin"] == ">=3 to <4%"


@pytest.mark.parametrize(
    ("radius_ft", "superelevation_percent", "message"),
    [
        (None, 3.0, "requires radius_ft"),
        (0.0, 3.0, "positive finite"),
        (450.0, None, "requires superelevation_percent"),
        (450.0, -1.0, "nonnegative finite"),
    ],
)
def test_horizontal_classification_rejects_invalid_inputs(
    radius_ft, superelevation_percent, message
) -> None:
    with pytest.raises(HCMCalcError, match=message):
        classify_horizontal_alignment(radius_ft, superelevation_percent)


def test_horizontal_curve_subsegment_speed_requires_demand_and_tangent_speed() -> None:
    with pytest.raises(HCMCalcError, match="demand flow"):
        horizontal_curve_average_speed(44.8381, None, 0.9145, 53.7)
    with pytest.raises(HCMCalcError, match="Tangent comparison speed"):
        horizontal_curve_average_speed(44.8381, 800.0, 0.9145, None)


def test_weighted_average_uses_and_validates_segment_length() -> None:
    subsegments = [
        {"length_ft": 100.0, "average_speed_mph": 50.0},
        {"length_ft": 200.0, "average_speed_mph": 40.0},
    ]

    assert length_weighted_adjusted_average_speed(
        subsegments, segment_length_ft=300.0
    ) == pytest.approx(43.333333)
    with pytest.raises(HCMCalcError, match="must match the segment length"):
        length_weighted_adjusted_average_speed(subsegments, segment_length_ft=400.0)


def test_example_problem_2_rejects_missing_subsegment_length() -> None:
    inputs = {
        **EXAMPLE_2_INPUTS,
        "horizontal_alignment_subsegments": [
            dict(subsegment)
            for subsegment in EXAMPLE_2_INPUTS["horizontal_alignment_subsegments"]
        ],
    }
    del inputs["horizontal_alignment_subsegments"][1]["length_ft"]

    with pytest.raises(HCMCalcError, match="requires length_ft"):
        TwoLaneHighwayChapter15Method().calculate(inputs)


def test_supplied_horizontal_class_must_match_exhibit_15_22() -> None:
    inputs = {
        **EXAMPLE_2_INPUTS,
        "horizontal_alignment_subsegments": [
            dict(subsegment)
            for subsegment in EXAMPLE_2_INPUTS["horizontal_alignment_subsegments"]
        ],
    }
    inputs["horizontal_alignment_subsegments"][1]["horizontal_class"] = 4

    with pytest.raises(HCMCalcError, match="does not match HCM7 Exhibit 15-22"):
        TwoLaneHighwayChapter15Method().calculate(inputs)
