"""Manual single-segment input adapter for the Streamlit worksheet."""

from __future__ import annotations

from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method
from hcmcalc.methods.two_lane_highway_models import PASSING_ZONE


def run_manual_single_segment(values: dict[str, Any]) -> CalculationResult:
    """Validate manual scope, build engine input, and run one segment."""

    engine_inputs = build_manual_segment_inputs(values)
    return TwoLaneHighwayChapter15Method().calculate_single_segment(engine_inputs)


def build_manual_segment_inputs(values: dict[str, Any]) -> dict[str, Any]:
    """Build one straight-segment engine input without duplicating formulas."""

    terrain_type = str(values.get("terrain_type", ""))
    if terrain_type not in {"level", "mountainous"}:
        raise HCMCalcError("terrain_type must be level or mountainous.")

    segment_type = str(values.get("segment_type", ""))
    grade = 0.0 if terrain_type == "level" else _required_float(values, "grade_percent")
    length = _required_float(values, "segment_length_mi")

    return {
        "segment_type": segment_type,
        "segment_length_mi": length,
        "posted_speed_mph": _required_float(values, "posted_speed_mph"),
        "analysis_direction_volume_veh_h": _required_float(
            values, "analysis_direction_volume_veh_h"
        ),
        "opposing_direction_volume_veh_h": (
            _required_float(values, "opposing_direction_volume_veh_h")
            if segment_type == PASSING_ZONE
            else None
        ),
        "peak_hour_factor": _required_float(values, "peak_hour_factor"),
        "heavy_vehicle_percent": _required_float(values, "heavy_vehicle_percent"),
        "grade_percent": grade,
        "horizontal_alignment": "straight",
        "lane_width_ft": _required_float(values, "lane_width_ft"),
        "shoulder_width_ft": _required_float(values, "shoulder_width_ft"),
        "access_point_density_per_mi": _required_float(
            values, "access_point_density_per_mi"
        ),
        "horizontal_alignment_subsegments": [],
    }


def _required_float(values: dict[str, Any], name: str) -> float:
    if name not in values or values[name] is None:
        raise HCMCalcError(f"Manual single-segment input requires {name}.")
    try:
        return float(values[name])
    except (TypeError, ValueError) as exc:
        raise HCMCalcError(f"{name} must be numeric.") from exc
