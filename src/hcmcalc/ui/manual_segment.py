"""Manual single-segment input adapter for the Streamlit worksheet."""

from __future__ import annotations

from typing import Any

from hcmcalc.core import (
    CalculationResult,
    HCMCalcError,
    IntermediateValue,
    MethodNotImplementedError,
)
from hcmcalc.methods.two_lane_highway_ch15 import (
    TwoLaneHighwayChapter15Method,
    _calculate_facility_segment,
    _parse_facility_segment,
)
from hcmcalc.methods.two_lane_highway_models import (
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
)


SUPPORTED_MOUNTAINOUS_COMBINATIONS = {
    (-3.0, 0.5),
    (4.0, 1.3),
    (6.0, 0.5),
    (6.0, 1.0),
}


def run_manual_single_segment(values: dict[str, Any]) -> CalculationResult:
    """Validate manual scope, build engine input, and run one segment."""

    engine_inputs = build_manual_segment_inputs(values)
    segment = _parse_facility_segment({"segment_id": 1, **engine_inputs})
    _validate_engine_inputs(segment)
    outputs = _calculate_facility_segment(segment)
    warnings = []
    if segment.segment_type == PASSING_LANE:
        warnings.append(
            "Single-segment passing lane results do not represent downstream "
            "passing-lane effects or full facility performance. Use facility "
            "analysis for corridor-level evaluation."
        )
    return CalculationResult(
        method=TwoLaneHighwayChapter15Method.method_name,
        facility_type=TwoLaneHighwayChapter15Method.facility_type,
        outputs=outputs,
        intermediate_values=_intermediate_values(outputs),
        assumptions=[
            "Analysis is limited to one straight two-lane highway segment.",
            "Motorized Vehicle LOS is based on follower density.",
            "Passing Constrained calculations use the HCM-required 1,500 veh/h opposing-flow assumption.",
            "No upstream passing lane or downstream facility-wide effects are applied.",
        ],
        warnings=warnings,
    )


def build_manual_segment_inputs(values: dict[str, Any]) -> dict[str, Any]:
    """Build one straight-segment engine input without duplicating formulas."""

    terrain_type = str(values.get("terrain_type", ""))
    if terrain_type not in {"level", "mountainous"}:
        raise HCMCalcError("terrain_type must be level or mountainous.")

    segment_type = str(values.get("segment_type", ""))
    grade = 0.0 if terrain_type == "level" else _required_float(values, "grade_percent")
    length = _required_float(values, "segment_length_mi")
    if terrain_type == "mountainous":
        combination = (grade, length)
        if grade != 0.0 and combination not in SUPPORTED_MOUNTAINOUS_COMBINATIONS:
            raise MethodNotImplementedError(
                "Unsupported mountainous grade/length combination. Supported "
                "combinations are level Class 1, -3% / 0.5 mi, 4% / 1.3 mi, "
                "6% / 0.5 mi, and 6% / 1.0 mi."
            )
    if segment_type == PASSING_ZONE and values.get("opposing_direction_volume_veh_h") is None:
        raise HCMCalcError(
            "Passing Zone requires opposing_direction_volume_veh_h."
        )
    if segment_type == PASSING_LANE and float(values.get("heavy_vehicle_percent", -1.0)) != 8.0:
        raise MethodNotImplementedError(
            "Manual Passing Lane calculation is currently supported only at 8% heavy vehicles."
        )
    if (
        segment_type == PASSING_LANE
        and terrain_type == "mountainous"
        and grade != 0.0
        and (grade, length) != (-3.0, 0.5)
    ):
        raise MethodNotImplementedError(
            "Manual Passing Lane calculation is currently supported only for "
            "vertical Class 1 terrain; downstream facility effects are not included."
        )

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


def _validate_engine_inputs(segment) -> None:
    if segment.segment_type not in {PASSING_CONSTRAINED, PASSING_ZONE, PASSING_LANE}:
        raise MethodNotImplementedError(
            f"Unsupported manual single-segment type: {segment.segment_type}."
        )
    if segment.segment_length_mi <= 0.0:
        raise HCMCalcError("segment_length_mi must be greater than zero.")
    if segment.posted_speed_mph <= 0.0:
        raise HCMCalcError("posted_speed_mph must be greater than zero.")
    if segment.analysis_direction_volume_veh_h < 0.0:
        raise HCMCalcError("analysis_direction_volume_veh_h cannot be negative.")
    if not 0.0 < segment.peak_hour_factor <= 1.0:
        raise HCMCalcError("peak_hour_factor must be greater than zero and at most 1.0.")
    if segment.heavy_vehicle_percent < 0.0:
        raise HCMCalcError("heavy_vehicle_percent cannot be negative.")
    if (
        segment.opposing_direction_volume_veh_h is not None
        and segment.opposing_direction_volume_veh_h < 0.0
    ):
        raise HCMCalcError("opposing_direction_volume_veh_h cannot be negative.")


def _intermediate_values(outputs: dict[str, Any]) -> list[IntermediateValue]:
    specs = [
        ("demand_flow_rate", "demand_flow_rate_veh_h", "veh/h", "HCM Eq. 15-1"),
        ("capacity", "capacity_veh_h", "veh/h", "HCM Ch. 15 Step 2"),
        ("vertical_alignment_class", "vertical_class", None, "HCM Exhibit 15-11"),
        ("base_free_flow_speed", "base_free_flow_speed_mph", "mph", "HCM Eq. 15-2"),
        ("free_flow_speed", "free_flow_speed_mph", "mph", "HCM Eq. 15-3"),
        ("average_speed", "average_speed_mph", "mph", "HCM Eq. 15-7"),
        ("percent_followers", "percent_followers", "%", "HCM Eq. 15-17"),
        (
            "follower_density",
            "follower_density_followers_mi_ln",
            "followers/mi/ln",
            "HCM Eq. 15-35 or Eq. 15-34 for Passing Lane midpoint",
        ),
    ]
    return [
        IntermediateValue(name, outputs[key], units, source)
        for name, key, units, source in specs
    ]
