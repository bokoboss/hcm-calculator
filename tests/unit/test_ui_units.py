import pytest

from hcmcalc.ui.manual_segment import build_manual_segment_inputs
from hcmcalc.ui.units import (
    DEFAULT_UNIT_SYSTEM,
    MILES_TO_KILOMETERS,
    display_outputs,
    manual_defaults,
    manual_horizontal_curve_defaults,
)


def _conceptual_values(unit_system: str) -> dict:
    return {
        "unit_system": unit_system,
        "segment_type": "passing_zone",
        "terrain_type": "mountainous",
        "segment_length": 1.609344 if unit_system == "metric" else 1.0,
        "posted_speed": 80.4672 if unit_system == "metric" else 50.0,
        "lane_width": 3.6576 if unit_system == "metric" else 12.0,
        "shoulder_width": 1.8288 if unit_system == "metric" else 6.0,
        "access_point_density": 2.0 if unit_system == "metric" else 2.0,
        "analysis_direction_volume": 750.0,
        "opposing_direction_volume": 500.0,
        "peak_hour_factor": 0.94,
        "heavy_vehicle_percent": 5.0,
        "grade_percent": 4.0,
    }


def test_metric_manual_inputs_convert_to_engine_native_imperial_keys() -> None:
    inputs = build_manual_segment_inputs(_conceptual_values("metric"))

    assert inputs["segment_length_mi"] == pytest.approx(1.0)
    assert inputs["posted_speed_mph"] == pytest.approx(50.0)
    assert inputs["lane_width_ft"] == pytest.approx(12.0)
    assert inputs["shoulder_width_ft"] == pytest.approx(6.0)
    assert inputs["access_point_density_per_mi"] == pytest.approx(
        2.0 * MILES_TO_KILOMETERS
    )
    assert inputs["analysis_direction_volume_veh_h"] == 750.0
    assert inputs["opposing_direction_volume_veh_h"] == 500.0


def test_imperial_manual_inputs_pass_through_to_engine_native_keys() -> None:
    inputs = build_manual_segment_inputs(_conceptual_values("imperial"))

    assert inputs["segment_length_mi"] == 1.0
    assert inputs["posted_speed_mph"] == 50.0
    assert inputs["lane_width_ft"] == 12.0
    assert inputs["shoulder_width_ft"] == 6.0
    assert inputs["access_point_density_per_mi"] == 2.0


def test_metric_curve_inputs_convert_to_engine_native_feet() -> None:
    values = {
        **_conceptual_values("metric"),
        "horizontal_alignment": "horizontal_curves",
        "horizontal_alignment_subsegments": manual_horizontal_curve_defaults("metric"),
    }

    inputs = build_manual_segment_inputs(values)

    assert inputs["horizontal_alignment_subsegments"][1]["length_ft"] == pytest.approx(
        432.0
    )
    assert inputs["horizontal_alignment_subsegments"][1]["radius_ft"] == pytest.approx(
        450.0
    )


def test_imperial_curve_inputs_pass_through_to_engine_native_feet() -> None:
    values = {
        **_conceptual_values("imperial"),
        "horizontal_alignment": "horizontal_curves",
        "horizontal_alignment_subsegments": manual_horizontal_curve_defaults(
            "imperial"
        ),
    }

    inputs = build_manual_segment_inputs(values)

    assert inputs["horizontal_alignment_subsegments"][1]["length_ft"] == 432.0
    assert inputs["horizontal_alignment_subsegments"][1]["radius_ft"] == 450.0


def test_curve_defaults_scale_subsegment_lengths_to_selected_segment_length() -> None:
    subsegments = manual_horizontal_curve_defaults("metric", segment_length=1.20)

    assert sum(float(subsegment["length"]) for subsegment in subsegments) == (
        pytest.approx(1200.0)
    )


def test_metric_display_outputs_convert_speeds_and_follower_density() -> None:
    outputs = {
        "follower_density_followers_mi_ln": 8.0,
        "average_speed_mph": 50.0,
        "percent_followers": 40.0,
        "demand_flow_rate_veh_h": 800.0,
        "capacity_veh_h": 1700.0,
        "free_flow_speed_mph": 55.0,
    }

    displayed = display_outputs(outputs, "metric")

    assert displayed["average_speed"]["value"] == pytest.approx(80.4672)
    assert displayed["average_speed"]["unit"] == "km/h"
    assert displayed["free_flow_speed"]["value"] == pytest.approx(88.51392)
    assert displayed["follower_density"]["value"] == pytest.approx(
        8.0 / MILES_TO_KILOMETERS
    )
    assert displayed["follower_density"]["unit"] == "fol/km/ln"


def test_manual_ui_defaults_to_metric() -> None:
    assert DEFAULT_UNIT_SYSTEM == "metric"
    assert manual_defaults()["segment_length"] == 1.20
    assert manual_defaults("Metric") == manual_defaults("metric")
