"""Typed contracts for the bounded HCM7 Basic Freeway Segment method."""

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
    speed_adjustment_factor_source: str = "hcm_base_conditions"
    capacity_adjustment_factor_source: str = "hcm_base_conditions"
    driver_population_category: str = "regular"
    grade_percent: float | None = None
    passenger_car_equivalent: float | None = None
    passenger_car_equivalent_provenance: str | None = None

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "BasicFreewaySegmentInputs":
        """Parse input and apply only documented neutral contract defaults."""

        required = (
            "case_id", "facility_type", "analysis_type", "direction",
            "number_of_lanes", "segment_length_mi", "demand_volume_veh_h",
            "peak_hour_factor", "heavy_vehicle_percent", "truck_mix",
            "terrain_type", "ffs_source", "free_flow_speed_mph",
            "base_free_flow_speed_mph", "lane_width_ft",
            "right_side_lateral_clearance_ft", "total_ramp_density_per_mi",
            "speed_adjustment_factor", "capacity_adjustment_factor",
        )
        missing = [field for field in required if field not in values]
        if missing:
            raise ValueError(
                "Basic Freeway Segment v0.1 requires: " + ", ".join(missing) + "."
            )
        normalized = {field: values[field] for field in required}
        for field in (
            "speed_adjustment_factor_source", "capacity_adjustment_factor_source",
            "driver_population_category", "grade_percent",
            "passenger_car_equivalent", "passenger_car_equivalent_provenance",
        ):
            if field in values:
                normalized[field] = values[field]
        return cls(**normalized)
