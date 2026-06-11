import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.ui.curve_editor import (
    curve_setup_defaults,
    generate_curve_subsegments,
)
from hcmcalc.ui.manual_segment import build_manual_segment_inputs


def _curve_setup(**overrides) -> dict:
    setup = {
        "total_curve_length": 1100.0,
        "radius": 450.0,
        "superelevation_percent": 3.0,
        "central_angle_deg": 55.0,
        "horizontal_class": 3,
        "subsegment_count": 11,
    }
    setup.update(overrides)
    return setup


def test_generate_11_horizontal_curve_subsegments_from_setup() -> None:
    subsegments = generate_curve_subsegments(_curve_setup())

    assert len(subsegments) == 11
    assert sum(row["length"] for row in subsegments) == pytest.approx(1100.0)


def test_generated_subsegments_preserve_engine_curve_fields() -> None:
    subsegments = generate_curve_subsegments(_curve_setup())

    assert subsegments[0] == {
        "type": "horizontal_curve",
        "length": 100.0,
        "superelevation_percent": 3.0,
        "radius": 450.0,
        "central_angle_deg": 55.0,
        "horizontal_class": 3,
    }


@pytest.mark.parametrize("count", [0, -1, 1.5, 101, "invalid"])
def test_invalid_subsegment_count_is_rejected(count) -> None:
    with pytest.raises(HCMCalcError, match="Number of subsegments"):
        generate_curve_subsegments(_curve_setup(subsegment_count=count))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("total_curve_length", 0.0, "Curve Length must be positive"),
        ("radius", -1.0, "Curve Radius must be positive"),
    ],
)
def test_invalid_length_and_radius_are_rejected(field, value, message) -> None:
    with pytest.raises(HCMCalcError, match=message):
        generate_curve_subsegments(_curve_setup(**{field: value}))


def test_metric_generated_curve_values_convert_through_existing_unit_path() -> None:
    setup = curve_setup_defaults("metric", segment_length=1.2)
    setup.update(radius=137.16, central_angle_deg=55.0)
    subsegments = generate_curve_subsegments(setup)
    values = {
        "unit_system": "metric",
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "segment_length": 1.2,
        "posted_speed": 80.0,
        "lane_width": 3.5,
        "shoulder_width": 1.8,
        "access_point_density": 0.0,
        "analysis_direction_volume": 750.0,
        "peak_hour_factor": 0.94,
        "heavy_vehicle_percent": 5.0,
        "horizontal_alignment": "horizontal_curves",
        "horizontal_alignment_subsegments": subsegments,
    }

    engine_inputs = build_manual_segment_inputs(values)

    assert sum(
        row["length_ft"] for row in engine_inputs["horizontal_alignment_subsegments"]
    ) == pytest.approx(1200.0 / 0.3048)
    assert engine_inputs["horizontal_alignment_subsegments"][0][
        "radius_ft"
    ] == pytest.approx(450.0)
