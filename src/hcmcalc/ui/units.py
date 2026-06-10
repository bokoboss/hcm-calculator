"""Unit conversion helpers for the manual Streamlit worksheet."""

from __future__ import annotations

from typing import Any

from hcmcalc.core import HCMCalcError


MILES_TO_KILOMETERS = 1.609344
FEET_TO_METERS = 0.3048
DEFAULT_UNIT_SYSTEM = "metric"
SUPPORTED_UNIT_SYSTEMS = {"metric", "imperial"}

METRIC_DEFAULTS: dict[str, float] = {
    "segment_length": 1.20,
    "posted_speed": 80.0,
    "lane_width": 3.50,
    "shoulder_width": 1.80,
    "access_point_density": 0.0,
    "analysis_direction_volume": 750.0,
    "peak_hour_factor": 0.94,
    "heavy_vehicle_percent": 5.0,
    "opposing_direction_volume": 500.0,
    "grade_percent": 4.0,
}

IMPERIAL_DEFAULTS: dict[str, float] = {
    "segment_length": 0.75,
    "posted_speed": 50.0,
    "lane_width": 12.0,
    "shoulder_width": 6.0,
    "access_point_density": 0.0,
    "analysis_direction_volume": 752.0,
    "peak_hour_factor": 0.94,
    "heavy_vehicle_percent": 5.0,
    "opposing_direction_volume": 500.0,
    "grade_percent": 4.0,
}


def manual_defaults(unit_system: str = DEFAULT_UNIT_SYSTEM) -> dict[str, float]:
    """Return user-facing defaults for the selected unit system."""

    unit_system = _normalize_unit_system(unit_system)
    defaults = METRIC_DEFAULTS if unit_system == "metric" else IMPERIAL_DEFAULTS
    return dict(defaults)


def manual_values_to_engine_inputs(
    values: dict[str, Any], unit_system: str
) -> dict[str, Any]:
    """Convert user-facing manual values to engine-native imperial keys."""

    unit_system = _normalize_unit_system(unit_system)
    if unit_system == "imperial":
        return {
            **values,
            "unit_system": unit_system,
            "segment_length_mi": _convert_user_value(
                values, "segment_length", "segment_length_mi"
            ),
            "posted_speed_mph": _convert_user_value(
                values, "posted_speed", "posted_speed_mph"
            ),
            "lane_width_ft": _convert_user_value(values, "lane_width", "lane_width_ft"),
            "shoulder_width_ft": _convert_user_value(
                values, "shoulder_width", "shoulder_width_ft"
            ),
            "access_point_density_per_mi": _convert_user_value(
                values, "access_point_density", "access_point_density_per_mi"
            ),
            "analysis_direction_volume_veh_h": _convert_user_value(
                values,
                "analysis_direction_volume",
                "analysis_direction_volume_veh_h",
            ),
            "opposing_direction_volume_veh_h": _convert_user_value(
                values,
                "opposing_direction_volume",
                "opposing_direction_volume_veh_h",
            ),
        }

    return {
        **values,
        "unit_system": unit_system,
        "segment_length_mi": _convert_user_value(
            values, "segment_length", "segment_length_mi", 1.0 / MILES_TO_KILOMETERS
        ),
        "posted_speed_mph": _convert_user_value(
            values, "posted_speed", "posted_speed_mph", 1.0 / MILES_TO_KILOMETERS
        ),
        "lane_width_ft": _convert_user_value(
            values, "lane_width", "lane_width_ft", 1.0 / FEET_TO_METERS
        ),
        "shoulder_width_ft": _convert_user_value(
            values, "shoulder_width", "shoulder_width_ft", 1.0 / FEET_TO_METERS
        ),
        "access_point_density_per_mi": _convert_user_value(
            values,
            "access_point_density",
            "access_point_density_per_mi",
            MILES_TO_KILOMETERS,
        ),
        "analysis_direction_volume_veh_h": _convert_user_value(
            values, "analysis_direction_volume", "analysis_direction_volume_veh_h"
        ),
        "opposing_direction_volume_veh_h": _convert_user_value(
            values, "opposing_direction_volume", "opposing_direction_volume_veh_h"
        ),
    }


def display_outputs(
    engine_outputs: dict[str, Any], unit_system: str
) -> dict[str, dict[str, Any]]:
    """Build the six primary result metrics in the selected display units."""

    unit_system = _normalize_unit_system(unit_system)
    metric = unit_system == "metric"
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0

    return {
        "follower_density": {
            "label": "Follower density",
            "value": float(engine_outputs["follower_density_followers_mi_ln"])
            * density_factor,
            "unit": "fol/km/ln" if metric else "fol/mi/ln",
        },
        "average_speed": {
            "label": "Average speed",
            "value": float(engine_outputs["average_speed_mph"]) * speed_factor,
            "unit": "km/h" if metric else "mph",
        },
        "percent_followers": {
            "label": "Percent followers",
            "value": float(engine_outputs["percent_followers"]),
            "unit": "%",
        },
        "demand_flow_rate": {
            "label": "Demand flow rate",
            "value": float(engine_outputs["demand_flow_rate_veh_h"]),
            "unit": "veh/h",
        },
        "capacity": {
            "label": "Capacity",
            "value": float(engine_outputs["capacity_veh_h"]),
            "unit": "veh/h",
        },
        "free_flow_speed": {
            "label": "Free-flow speed",
            "value": float(engine_outputs["free_flow_speed_mph"]) * speed_factor,
            "unit": "km/h" if metric else "mph",
        },
    }


def _normalize_unit_system(unit_system: str) -> str:
    unit_system = str(unit_system).strip().lower()
    if unit_system not in SUPPORTED_UNIT_SYSTEMS:
        raise HCMCalcError("unit_system must be metric or imperial.")
    return unit_system


def _convert_user_value(
    values: dict[str, Any],
    user_key: str,
    engine_key: str,
    factor: float = 1.0,
) -> Any:
    if user_key not in values:
        return values.get(engine_key)

    value = values[user_key]
    if value is None:
        return None
    return float(value) * factor
