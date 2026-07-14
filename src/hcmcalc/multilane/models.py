"""Typed contracts for bounded Multilane Highway Segment v0.1."""

from dataclasses import MISSING, dataclass
from typing import Any


@dataclass(frozen=True)
class MultilaneBasicSegmentInputs:
    """One-direction Multilane Highway Segment inputs."""

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
    posted_speed_limit_mph: float | None
    lane_width_ft: float | None
    roadside_lateral_clearance_ft: float | None
    median_type: str | None
    access_point_density_per_mi: float | None
    ffs_source: str = "estimated"
    free_flow_speed_mph: float | None = None
    passenger_car_equivalent: float | None = None
    left_side_lateral_clearance_ft: float | None = None
    terrain_type: str = "specific_grade"

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "MultilaneBasicSegmentInputs":
        """Parse required fields while preserving legacy Example 4 payloads."""

        required = tuple(
            name
            for name, field in cls.__dataclass_fields__.items()
            if field.default is MISSING and field.default_factory is MISSING
        )
        missing = [field for field in required if field not in values]
        if missing:
            raise ValueError(
                "Multilane Basic Segment v0.1 requires: " + ", ".join(missing) + "."
            )
        return cls(
            **{
                field: values[field]
                for field in cls.__dataclass_fields__
                if field in values
            }
        )
