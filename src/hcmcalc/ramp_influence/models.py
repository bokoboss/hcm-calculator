"""Immutable input models for HCM merge and diverge segment analysis."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class GeometryEvidence:
    source: str
    configuration: str
    reviewed_by: str
    notes: str


@dataclass(frozen=True)
class BaseRampInfluenceInputs:
    method_version: str
    case_id: str
    facility_type: str
    analysis_type: str
    analysis_period_minutes: float
    freeway_lanes: int
    ramp_side: str
    ramp_lanes: int
    freeway_demand_veh_h: float
    ramp_demand_veh_h: float
    freeway_peak_hour_factor: float
    ramp_peak_hour_factor: float
    freeway_heavy_vehicle_percent: float
    ramp_heavy_vehicle_percent: float
    terrain_type: str
    ffs_source: str
    free_flow_speed_mph: float | None
    base_free_flow_speed_mph: float | None
    lane_width_ft: float | None
    right_side_lateral_clearance_ft: float | None
    total_ramp_density_per_mi: float | None
    ramp_ffs_mph: float
    speed_adjustment_factor: float
    capacity_adjustment_factor: float
    speed_adjustment_factor_source: str
    capacity_adjustment_factor_source: str
    adjacent_ramp_context: str
    geometry_evidence: GeometryEvidence

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MergeSegmentInputs(BaseRampInfluenceInputs):
    acceleration_lane_length_ft: float
    downstream_freeway_demand_veh_h: float | None
    lane_addition: bool
    major_merge: bool

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "MergeSegmentInputs":
        return _from_mapping(cls, values)


@dataclass(frozen=True)
class DivergeSegmentInputs(BaseRampInfluenceInputs):
    deceleration_lane_length_ft: float
    continuing_freeway_demand_veh_h: float | None
    lane_drop: bool
    option_lane: bool
    major_diverge: bool

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "DivergeSegmentInputs":
        return _from_mapping(cls, values)


def _from_mapping(cls: type, values: dict[str, Any]):
    fields = set(cls.__dataclass_fields__)
    allowed = fields
    extra = sorted(set(values) - allowed)
    if extra:
        raise ValueError(f"{cls.__name__} does not accept unknown inputs: " + ", ".join(extra))
    missing = sorted(fields - set(values))
    if missing:
        raise ValueError(f"{cls.__name__} requires: " + ", ".join(missing))
    if not isinstance(values["geometry_evidence"], dict):
        raise ValueError("geometry_evidence must be a mapping.")
    geometry_fields = set(GeometryEvidence.__dataclass_fields__)
    geometry_extra = sorted(set(values["geometry_evidence"]) - geometry_fields)
    geometry_missing = sorted(geometry_fields - set(values["geometry_evidence"]))
    if geometry_extra or geometry_missing:
        detail = geometry_extra or geometry_missing
        raise ValueError("geometry_evidence has unknown or missing fields: " + ", ".join(detail))
    normalized = {field: values[field] for field in fields if field != "geometry_evidence"}
    normalized["geometry_evidence"] = GeometryEvidence(**values["geometry_evidence"])
    return cls(**normalized)
