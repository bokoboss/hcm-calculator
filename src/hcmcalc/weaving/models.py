"""Immutable, versioned input contracts for freeway weaving analysis."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class GeometryBasis:
    """Auditable evidence for configuration values; not an inferred lane graph."""

    entry_side: str
    exit_side: str
    reachable_origin_destination_lanes: dict[str, str]
    option_lane_status: dict[str, bool]
    nwl_basis: str
    lane_change_basis: str


@dataclass(frozen=True)
class WeavingSegmentInputs:
    """Family-level input contract. Version-local rules are validated by a method."""

    method_version: str
    case_id: str
    facility_type: str
    analysis_type: str
    direction: str
    configuration: str
    analysis_period_minutes: float
    peak_hour_factor: float
    segment_length_ft: float
    number_of_lanes: int
    number_of_weaving_lanes: int
    volume_ff_veh_h: float
    volume_fr_veh_h: float
    volume_rf_veh_h: float
    volume_rr_veh_h: float
    interchange_density_per_mi: float
    ffs_source: str
    free_flow_speed_mph: float | None
    base_free_flow_speed_mph: float | None
    lane_width_ft: float | None
    right_side_lateral_clearance_ft: float | None
    total_ramp_density_per_mi: float | None
    heavy_vehicle_percent: float
    terrain_type: str
    speed_adjustment_factor: float
    capacity_adjustment_factor: float
    speed_adjustment_factor_source: str
    capacity_adjustment_factor_source: str
    lc_rf: int | None
    lc_fr: int | None
    lc_rr: int | None
    geometry: GeometryBasis

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "WeavingSegmentInputs":
        required = {field for field in cls.__dataclass_fields__ if field != "geometry"}
        allowed = required | {"geometry"}
        extra = sorted(set(values) - allowed)
        if extra:
            raise ValueError("Weaving Segment does not accept unknown inputs: " + ", ".join(extra))
        missing = sorted(required - set(values))
        if missing:
            raise ValueError("Weaving Segment requires: " + ", ".join(missing))
        if "geometry" not in values or not isinstance(values["geometry"], dict):
            raise ValueError("geometry must be a mapping with explicit engineering basis.")
        geometry_fields = set(GeometryBasis.__dataclass_fields__)
        geometry_extra = sorted(set(values["geometry"]) - geometry_fields)
        geometry_missing = sorted(geometry_fields - set(values["geometry"]))
        if geometry_extra or geometry_missing:
            detail = geometry_extra or geometry_missing
            raise ValueError("geometry has unknown or missing fields: " + ", ".join(detail))
        normalized = {name: values[name] for name in required}
        normalized["geometry"] = GeometryBasis(**values["geometry"])
        return cls(**normalized)

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)
