"""Typed contracts for Basic Freeway Segment v0.1."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BasicFreewaySegmentInputs:
    """One-direction, one-segment Basic Freeway operational inputs."""

    case_id: str
    facility_type: str
    analysis_type: str
    direction: str
    number_of_lanes: int
    segment_length_mi: float
    demand_volume_veh_h: float
    peak_hour_factor: float
    heavy_vehicle_percent: float
    truck_mix: str
    terrain_type: str
    ffs_source: str
    free_flow_speed_mph: float | None
    base_free_flow_speed_mph: float | None
    lane_width_ft: float | None
    right_side_lateral_clearance_ft: float | None
    total_ramp_density_per_mi: float | None
    speed_adjustment_factor: float
    capacity_adjustment_factor: float

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "BasicFreewaySegmentInputs":
        """Parse required fields without silently supplying engineering defaults."""

        required = tuple(cls.__dataclass_fields__)
        missing = [field for field in required if field not in values]
        if missing:
            raise ValueError(
                "Basic Freeway Segment v0.1 requires: " + ", ".join(missing) + "."
            )
        return cls(**{field: values[field] for field in required})
