"""Two-lane highway Chapter 15 input models and scoped constants."""

from dataclasses import dataclass


PASSING_CONSTRAINED = "passing_constrained"
PASSING_LANE = "passing_lane"
PASSING_ZONE = "passing_zone"
OPPOSING_FLOW_EXAMPLE_1_VEH_H = 1500.0
STRAIGHT_ALIGNMENT = "straight"
HORIZONTAL_CURVES_ALIGNMENT = "horizontal_curves"


@dataclass(frozen=True)
class TwoLaneExampleProblem1Inputs:
    """Validated input shape for HCM Chapter 26 Two-Lane Example Problem 1."""

    segment_length_mi: float
    segment_type: str
    analysis_direction_volume_veh_h: float
    peak_hour_factor: float
    posted_speed_mph: float
    heavy_vehicle_percent: float
    grade_percent: float
    horizontal_alignment: str
    lane_width_ft: float
    shoulder_width_ft: float
    access_point_density_per_mi: float
    upstream_passing_lane: bool


@dataclass(frozen=True)
class HorizontalAlignmentSubsegment:
    """Horizontal alignment subsegment for HCM Chapter 26 Example Problem 2."""

    subsegment_type: str
    length_ft: float
    superelevation_percent: float | None = None
    radius_ft: float | None = None
    central_angle_deg: float | None = None
    horizontal_class: int | None = None


@dataclass(frozen=True)
class TwoLaneExampleProblem2Inputs(TwoLaneExampleProblem1Inputs):
    """Validated input shape for HCM Chapter 26 Two-Lane Example Problem 2."""

    horizontal_alignment_subsegments: tuple[HorizontalAlignmentSubsegment, ...]


@dataclass(frozen=True)
class TwoLaneFacilitySegmentInputs:
    """Validated segment input shape for HCM Chapter 26 facility examples."""

    segment_id: int
    segment_type: str
    segment_length_mi: float
    posted_speed_mph: float
    analysis_direction_volume_veh_h: float
    opposing_direction_volume_veh_h: float | None
    peak_hour_factor: float
    heavy_vehicle_percent: float
    grade_percent: float
    horizontal_alignment: str
    lane_width_ft: float
    shoulder_width_ft: float
    access_point_density_per_mi: float
    horizontal_alignment_subsegments: tuple[HorizontalAlignmentSubsegment, ...]
    terrain_type: str | None = None
    grade_length_mi: float | None = None
    vertical_class: int | None = None


@dataclass(frozen=True)
class TwoLaneExampleProblem3Inputs:
    """Validated facility input shape for HCM Chapter 26 Two-Lane facilities."""

    case_id: str
    facility_length_mi: float
    upstream_passing_lane: bool
    segments: tuple[TwoLaneFacilitySegmentInputs, ...]
