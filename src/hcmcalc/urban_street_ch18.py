"""Bounded HCM 7 Chapter 18 motorized urban street segment engine."""

from dataclasses import asdict, dataclass
from math import isfinite
from numbers import Real
from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError, IntermediateValue


LOS_THRESHOLDS_MPH = {
    "A": (20.0, 24.0, 28.0, 32.0, 36.0, 40.0, 44.0),
    "B": (17.0, 20.0, 23.0, 27.0, 30.0, 34.0, 37.0),
    "C": (13.0, 15.0, 18.0, 20.0, 23.0, 25.0, 28.0),
    "D": (10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0),
    "E": (8.0, 9.0, 11.0, 12.0, 14.0, 15.0, 17.0),
}
LOS_BFFS_COLUMNS_MPH = (25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0)

_INPUT_FIELDS = {
    "segment_length_ft",
    "upstream_intersection_width_ft",
    "signal_control_spacing_ft",
    "through_lane_count",
    "subject_direction",
    "through_movement_id",
    "posted_speed_limit_mph",
    "s_calib_mph",
    "restrictive_median_proportion",
    "curb_proportion",
    "parking_proportion",
    "subject_side_access_count",
    "opposing_side_access_count",
    "v_m_veh_h",
    "access_point_delays_s_veh",
    "d_other_s_veh",
    "analysis_period_min",
    "control_type",
    "demand_balanced",
    "demand_adjustments_resolved",
    "capacity_effects_resolved",
    "spillback_present",
    "external_through",
}
_EXTERNAL_FIELDS = {
    "source_class",
    "source_tool",
    "source_method_note",
    "hcm_edition_note",
    "direction",
    "through_movement_id",
    "analysis_period_min",
    "scenario_note",
    "v_th_veh_h",
    "c_th_veh_h",
    "d_t_s_veh",
}


@dataclass(frozen=True)
class ExternalThroughPerformance:
    source_class: str
    source_tool: str
    source_method_note: str
    hcm_edition_note: str
    direction: str
    through_movement_id: str
    analysis_period_min: int
    scenario_note: str
    v_th_veh_h: float
    c_th_veh_h: float
    d_t_s_veh: float


@dataclass(frozen=True)
class UrbanStreetSegmentInputs:
    segment_length_ft: float
    upstream_intersection_width_ft: float
    signal_control_spacing_ft: float
    through_lane_count: int
    subject_direction: str
    through_movement_id: str
    posted_speed_limit_mph: float
    s_calib_mph: float
    restrictive_median_proportion: float
    curb_proportion: float
    parking_proportion: float
    subject_side_access_count: int
    opposing_side_access_count: int
    v_m_veh_h: float
    access_point_delays_s_veh: tuple[float, ...]
    d_other_s_veh: float
    analysis_period_min: int
    control_type: str
    demand_balanced: bool
    demand_adjustments_resolved: bool
    capacity_effects_resolved: bool
    spillback_present: bool
    external_through: ExternalThroughPerformance

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "UrbanStreetSegmentInputs":
        if not isinstance(values, dict):
            raise HCMCalcError("Chapter 18 inputs must be a mapping.")
        _require_fields(values, _INPUT_FIELDS, "Chapter 18")
        if set(values) - _INPUT_FIELDS:
            raise HCMCalcError(
                "Chapter 18 does not accept unknown inputs: "
                + ", ".join(sorted(set(values) - _INPUT_FIELDS))
                + "."
            )
        external = values["external_through"]
        if not isinstance(external, dict):
            raise HCMCalcError("external_through must be a mapping.")
        _require_fields(external, _EXTERNAL_FIELDS, "External through performance")
        if set(external) - _EXTERNAL_FIELDS:
            raise HCMCalcError("external_through contains unknown fields.")

        delays = values["access_point_delays_s_veh"]
        if not isinstance(delays, (list, tuple)):
            raise HCMCalcError("access_point_delays_s_veh must be an explicit list.")
        return cls(
            **{
                name: values[name]
                for name in _INPUT_FIELDS - {"external_through", "access_point_delays_s_veh"}
            },
            access_point_delays_s_veh=tuple(delays),
            external_through=ExternalThroughPerformance(**external),
        )


class UrbanStreetSegmentMethod:
    """HCM 7 signalized-boundary segment calculation for the qualified scope."""

    facility_type = "urban_street_segment"
    method_name = "urban_street_segment_ch18_v0_1"

    def calculate(self, values: dict[str, Any]) -> CalculationResult:
        inputs = UrbanStreetSegmentInputs.from_mapping(values)
        _validate_inputs(inputs)

        length = inputs.segment_length_ft
        link_length = length - inputs.upstream_intersection_width_ft
        lanes = inputs.through_lane_count
        external = inputs.external_through
        access_density = 5280.0 * (
            inputs.subject_side_access_count + inputs.opposing_side_access_count
        ) / link_length
        s0 = 25.6 + 0.47 * inputs.posted_speed_limit_mph
        f_cs = (
            1.5 * inputs.restrictive_median_proportion
            - 0.47 * inputs.curb_proportion
            - 3.7 * inputs.curb_proportion * inputs.restrictive_median_proportion
        )
        f_a = -0.078 * access_density / lanes
        f_pk = -3.0 * inputs.parking_proportion
        s_fo = inputs.s_calib_mph + s0 + f_cs + f_a + f_pk
        f_l = min(
            1.0,
            1.02 - 4.7 * (s_fo - 19.5) / max(inputs.signal_control_spacing_ft, 400.0),
        )
        s_f = max(s_fo * f_l, inputs.posted_speed_limit_mph)
        f_v = vehicle_proximity_factor(inputs.v_m_veh_h, lanes, s_f)
        access_delay = sum(inputs.access_point_delays_s_veh)
        running_time = (
            (6.0 - 2.0) / (0.0025 * length)
            + 3600.0 * length / (5280.0 * s_f) * f_v
            + access_delay
            + inputs.d_other_s_veh
        )
        if running_time <= 0 or not isfinite(running_time):
            raise HCMCalcError("Computed running time must be finite and positive.")
        running_speed = 3600.0 * length / (5280.0 * running_time)
        total_travel_time = running_time + external.d_t_s_veh
        if total_travel_time <= 0 or not isfinite(total_travel_time):
            raise HCMCalcError("Computed travel time must be finite and positive.")
        travel_speed = 3600.0 * length / (5280.0 * total_travel_time)
        through_v_c = external.v_th_veh_h / external.c_th_veh_h
        los_thresholds = interpolated_los_thresholds(s_fo)
        los = level_of_service(travel_speed, s_fo, through_v_c)

        outputs = {
            "calculation_type": self.method_name,
            "support_status": "supported_bounded_hcm7_signalized_15min",
            "segment_length_ft": length,
            "link_length_ft": link_length,
            "s0_mph": s0,
            "f_cs_mph": f_cs,
            "access_density_per_mi": access_density,
            "f_a_mph": f_a,
            "f_pk_mph": f_pk,
            "base_free_flow_speed_mph": s_fo,
            "signal_control_spacing_ft": inputs.signal_control_spacing_ft,
            "f_l": f_l,
            "free_flow_speed_mph": s_f,
            "f_v": f_v,
            "f_x": 1.0,
            "l_1_s": 2.0,
            "total_access_delay_s_veh": access_delay,
            "d_other_s_veh": inputs.d_other_s_veh,
            "running_time_s": running_time,
            "running_speed_mph": running_speed,
            "external_through_delay_used_s_veh": external.d_t_s_veh,
            "total_travel_time_s": total_travel_time,
            "travel_speed_mph": travel_speed,
            "v_m_veh_h": inputs.v_m_veh_h,
            "v_th_veh_h": external.v_th_veh_h,
            "c_th_veh_h": external.c_th_veh_h,
            "through_v_c": through_v_c,
            "displayed_through_v_c": round(through_v_c, 2),
            "los_speed_thresholds_mph": los_thresholds,
            "level_of_service": los,
            "external_through_provenance": asdict(external),
            "input_summary": asdict(inputs),
        }
        intermediate_sources = {
            "link_length_ft": ("ft", "HCM7 Chapter 18 segment/link geometry"),
            "s0_mph": ("mi/h", "HCM7 Exhibit 18-11"),
            "f_cs_mph": ("mi/h", "HCM7 Exhibit 18-11"),
            "access_density_per_mi": ("points/mi", "HCM7 Exhibit 18-11; explicit counts"),
            "f_a_mph": ("mi/h", "HCM7 Exhibit 18-11"),
            "f_pk_mph": ("mi/h", "HCM7 Exhibit 18-11"),
            "base_free_flow_speed_mph": ("mi/h", "HCM7 Eq. 18-3"),
            "f_l": ("ratio", "HCM7 Eq. 18-4"),
            "free_flow_speed_mph": ("mi/h", "HCM7 Eq. 18-5"),
            "f_v": ("ratio", "HCM7 Eq. 18-6; explicit v_m"),
            "f_x": ("ratio", "HCM7 Eq. 18-8; signalized boundary"),
            "l_1_s": ("s", "HCM7 Eq. 18-8; signalized boundary"),
            "total_access_delay_s_veh": ("s/veh", "HCM7 Eq. 18-7; explicit supplied delays"),
            "d_other_s_veh": ("s/veh", "Explicit supported other delay input"),
            "running_time_s": ("s", "HCM7 Eqs. 18-7 and 18-8"),
            "running_speed_mph": ("mi/h", "Segment length and running time"),
            "external_through_delay_used_s_veh": ("s/veh", "Externally qualified final through delay"),
            "total_travel_time_s": ("s", "Running time plus external final through delay, once"),
            "travel_speed_mph": ("mi/h", "HCM7 Eq. 18-15"),
            "through_v_c": ("ratio", "HCM7 Exhibit 18-1; v_th/c_th"),
            "level_of_service": (None, "HCM7 Exhibit 18-1"),
        }
        intermediates = [
            IntermediateValue(name, outputs[name], units, source)
            for name, (units, source) in intermediate_sources.items()
        ]
        return CalculationResult(
            method=self.method_name,
            facility_type=self.facility_type,
            outputs=outputs,
            intermediate_values=intermediates,
            assumptions=[
                "HCM7 right-hand-traffic reference semantics; no Thailand/LHT qualification.",
                "Demand balancing/adjustments and applicable capacity effects are externally resolved.",
                "No unresolved spillback invalidates this 15-minute operational result.",
                "Final signalized downstream through delay is external and consumed once.",
                "Access-point delays are explicit qualified inputs; no planning estimate is used.",
            ],
        )


def vehicle_proximity_factor(v_m_veh_h: float, through_lanes: int, free_flow_speed_mph: float) -> float:
    """HCM7 Eq. 18-6; reject the non-real fractional-power domain."""
    v_m = _finite_number("v_m_veh_h", v_m_veh_h, minimum=0.0)
    lanes = _positive_integer("through_lane_count", through_lanes)
    speed = _finite_number("free_flow_speed_mph", free_flow_speed_mph, minimum=0.0, strict=True)
    denominator = 52.8 * lanes * speed
    if denominator <= 0.0:
        raise HCMCalcError("Equation 18-6 denominator must be positive.")
    base = 1.0 - v_m / denominator
    if base < 0.0:
        raise HCMCalcError("Equation 18-6 fractional-power base must be nonnegative.")
    return 2.0 / (1.0 + base**0.21)


def interpolated_los_thresholds(base_free_flow_speed_mph: float) -> dict[str, float]:
    """Interpolate Exhibit 18-1 thresholds within its 25–55 mi/h domain."""
    speed = _finite_number("base_free_flow_speed_mph", base_free_flow_speed_mph)
    if not LOS_BFFS_COLUMNS_MPH[0] <= speed <= LOS_BFFS_COLUMNS_MPH[-1]:
        raise HCMCalcError("Exhibit 18-1 supports base FFS from 25 through 55 mi/h.")
    lower_index = max(i for i, value in enumerate(LOS_BFFS_COLUMNS_MPH) if value <= speed)
    upper_index = min(i for i, value in enumerate(LOS_BFFS_COLUMNS_MPH) if value >= speed)
    lower = LOS_BFFS_COLUMNS_MPH[lower_index]
    upper = LOS_BFFS_COLUMNS_MPH[upper_index]
    proportion = 0.0 if lower == upper else (speed - lower) / (upper - lower)
    return {
        level: row[lower_index] + (row[upper_index] - row[lower_index]) * proportion
        for level, row in LOS_THRESHOLDS_MPH.items()
    }


def level_of_service(travel_speed_mph: float, base_free_flow_speed_mph: float, through_v_c: float) -> str:
    """HCM7 Exhibit 18-1 strict speed thresholds and through v/c rule."""
    travel_speed = _finite_number("travel_speed_mph", travel_speed_mph, minimum=0.0)
    ratio = _finite_number("through_v_c", through_v_c, minimum=0.0)
    thresholds = interpolated_los_thresholds(base_free_flow_speed_mph)
    if ratio > 1.0:
        return "F"
    for level, threshold in thresholds.items():
        if travel_speed > threshold:
            return level
    return "F"


def _validate_inputs(inputs: UrbanStreetSegmentInputs) -> None:
    numeric = (
        ("segment_length_ft", inputs.segment_length_ft, 0.0, True),
        ("upstream_intersection_width_ft", inputs.upstream_intersection_width_ft, 0.0, False),
        ("signal_control_spacing_ft", inputs.signal_control_spacing_ft, 0.0, True),
        ("posted_speed_limit_mph", inputs.posted_speed_limit_mph, 0.0, True),
        ("s_calib_mph", inputs.s_calib_mph, None, False),
        ("v_m_veh_h", inputs.v_m_veh_h, 0.0, False),
        ("d_other_s_veh", inputs.d_other_s_veh, 0.0, False),
    )
    for name, value, minimum, strict in numeric:
        _finite_number(name, value, minimum=minimum, strict=strict)
    if inputs.upstream_intersection_width_ft >= inputs.segment_length_ft:
        raise HCMCalcError("upstream_intersection_width_ft must be less than segment_length_ft.")
    _positive_integer("through_lane_count", inputs.through_lane_count)
    _nonnegative_integer("subject_side_access_count", inputs.subject_side_access_count)
    _nonnegative_integer("opposing_side_access_count", inputs.opposing_side_access_count)
    for name, value in (
        ("restrictive_median_proportion", inputs.restrictive_median_proportion),
        ("curb_proportion", inputs.curb_proportion),
        ("parking_proportion", inputs.parking_proportion),
    ):
        _finite_number(name, value, minimum=0.0)
        if value > 1.0:
            raise HCMCalcError(f"{name} must be between 0 and 1.")
    for delay in inputs.access_point_delays_s_veh:
        _finite_number("access point delay", delay, minimum=0.0)
    if (
        inputs.subject_side_access_count + inputs.opposing_side_access_count > 0
        and not inputs.access_point_delays_s_veh
    ):
        raise HCMCalcError("Explicit qualified access point delays are required when access points exist.")

    for name, value in (
        ("demand_balanced", inputs.demand_balanced),
        ("demand_adjustments_resolved", inputs.demand_adjustments_resolved),
        ("capacity_effects_resolved", inputs.capacity_effects_resolved),
        ("spillback_present", inputs.spillback_present),
    ):
        if not isinstance(value, bool):
            raise HCMCalcError(f"{name} must be an explicit boolean.")

    if inputs.analysis_period_min != 15:
        raise HCMCalcError("The qualified Chapter 18 operational period is exactly 15 minutes.")
    if inputs.control_type != "signalized":
        raise HCMCalcError("The qualified Chapter 18 boundary control is signalized only.")
    if not (
        inputs.demand_balanced
        and inputs.demand_adjustments_resolved
        and inputs.capacity_effects_resolved
    ):
        raise HCMCalcError(
            "Demand must be balanced/adjusted and capacity effects resolved externally."
        )
    if inputs.spillback_present:
        raise HCMCalcError("Unresolved spillback invalidates the bounded operational result.")
    for name, value in (
        ("subject_direction", inputs.subject_direction),
        ("through_movement_id", inputs.through_movement_id),
        ("control_type", inputs.control_type),
    ):
        _nonempty_text(name, value)

    external = inputs.external_through
    for name in ("source_class", "source_tool", "source_method_note", "hcm_edition_note", "direction", "through_movement_id", "scenario_note"):
        _nonempty_text("external_through." + name, getattr(external, name))
    if external.direction != inputs.subject_direction:
        raise HCMCalcError("External through direction must match subject direction.")
    if external.through_movement_id != inputs.through_movement_id:
        raise HCMCalcError("External through movement must match the subject through movement.")
    if external.analysis_period_min != inputs.analysis_period_min:
        raise HCMCalcError("External through analysis period must match the segment period.")
    _positive_integer("external_through.analysis_period_min", external.analysis_period_min)
    _finite_number("v_th_veh_h", external.v_th_veh_h, minimum=0.0, strict=True)
    _finite_number("c_th_veh_h", external.c_th_veh_h, minimum=0.0, strict=True)
    _finite_number("d_t_s_veh", external.d_t_s_veh, minimum=0.0)
    # Validate the accepted table domain before returning any qualified result.
    base_speed = inputs.s_calib_mph + 25.6 + 0.47 * inputs.posted_speed_limit_mph
    link_length = inputs.segment_length_ft - inputs.upstream_intersection_width_ft
    access_density = 5280.0 * (inputs.subject_side_access_count + inputs.opposing_side_access_count) / link_length
    base_speed += (
        1.5 * inputs.restrictive_median_proportion
        - 0.47 * inputs.curb_proportion
        - 3.7 * inputs.curb_proportion * inputs.restrictive_median_proportion
        - 0.078 * access_density / inputs.through_lane_count
        - 3.0 * inputs.parking_proportion
    )
    interpolated_los_thresholds(base_speed)


def _finite_number(name: str, value: Any, *, minimum: float | None = None, strict: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value)):
        raise HCMCalcError(f"{name} must be a finite number.")
    number = float(value)
    if minimum is not None and (number <= minimum if strict else number < minimum):
        bound = "greater than" if strict else "at least"
        raise HCMCalcError(f"{name} must be {bound} {minimum}.")
    return number


def _positive_integer(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise HCMCalcError(f"{name} must be a positive integer.")
    return value


def _nonnegative_integer(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise HCMCalcError(f"{name} must be a nonnegative integer.")
    return value


def _nonempty_text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise HCMCalcError(f"{name} must be a nonempty string.")


def _require_fields(values: dict[str, Any], required: set[str], name: str) -> None:
    missing = sorted(required - values.keys())
    if missing:
        raise HCMCalcError(f"{name} requires explicit fields: " + ", ".join(missing) + ".")
