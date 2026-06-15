"""Typed contracts for the Chapter 26 Multilane Highway Example Problem 4 path."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MultilaneBasicSegmentInputs:
    """One-direction inputs validated only for Chapter 26 Example Problem 4."""

    case_id: str
    facility_type: str
    analysis_type: str
    direction: str
    number_of_lanes: int
    segment_length_ft: float
    demand_volume_veh_h: float
    peak_hour_factor: float
    heavy_vehicle_percent: float
    truck_mix: str
    grade_percent: float
    posted_speed_limit_mph: float
    lane_width_ft: float
    roadside_lateral_clearance_ft: float
    median_type: str
    access_point_density_per_mi: float

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "MultilaneBasicSegmentInputs":
        """Parse required fields without silently supplying engineering defaults."""

        required = tuple(cls.__dataclass_fields__)
        missing = [field for field in required if field not in values]
        if missing:
            raise ValueError(
                "Multilane Basic Segment v0.1 requires: " + ", ".join(missing) + "."
            )
        return cls(**{field: values[field] for field in required})
