"""HCM Version 7.0 Chapter 13 freeway weaving operational engine."""

from math import sqrt
from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError, IntermediateValue
from hcmcalc.freeway.method import (
    basic_freeway_capacity,
    estimated_free_flow_speed,
    general_terrain_passenger_car_equivalent,
    heavy_vehicle_adjustment_factor,
    lane_width_adjustment,
    right_lateral_clearance_adjustment,
)

from ..geometry import validate_v70_geometry
from ..models import WeavingSegmentInputs
from ..validation import validate_common
from .coefficients import DENSITY_AT_CAPACITY_PC_MI_LN, LOS_DENSITY_UPPER_BOUNDS, MIN_WEAVING_SPEED_MPH


class HCM70WeavingSegmentMethod:
    """Isolated freeway weaving-segment operational method, HCM 7.0 only."""

    facility_type = "freeway_weaving_segment"
    method_name = "hcm7_v70_freeway_weaving_segment"
    method_version = "hcm_7_0"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        try:
            parsed = WeavingSegmentInputs.from_mapping(inputs)
        except (TypeError, ValueError) as exc:
            raise HCMCalcError(str(exc)) from exc
        validate_common(parsed)
        if parsed.method_version != self.method_version:
            raise HCMCalcError("HCM 7.0 method requires method_version 'hcm_7_0'.")
        validate_v70_geometry(parsed)

        ffs = _free_flow_speed(parsed)
        pce = general_terrain_passenger_car_equivalent(parsed.terrain_type)
        fhv = heavy_vehicle_adjustment_factor(parsed.heavy_vehicle_percent, pce)
        movement = {name: value / (parsed.peak_hour_factor * fhv) for name, value in _volumes(parsed).items()}
        if parsed.configuration == "one_sided":
            weaving = movement["rf"] + movement["fr"]
            nonweaving = movement["ff"] + movement["rr"]
            lcmin = parsed.lc_rf * movement["rf"] + parsed.lc_fr * movement["fr"]
        else:
            weaving = movement["rr"]
            nonweaving = movement["ff"] + movement["fr"] + movement["rf"]
            lcmin = parsed.lc_rr * movement["rr"]
        total = weaving + nonweaving
        vr = weaving / total
        lmax = 5728.0 * (1.0 + vr) ** 1.6 - 1566.0 * parsed.number_of_weaving_lanes
        if parsed.segment_length_ft >= lmax:
            common = _base_outputs(parsed, ffs, pce, fhv, movement, weaving, nonweaving, total, vr, lcmin, lmax, None, None, None, None, None, None, None)
            common.update({
                "support_status": "hcm_handoff_required", "scope_status": "hcm_handoff_lmax",
                "capacity_status": "not_evaluated_after_handoff", "level_of_service": None,
                "weaving_speed_mph": None, "nonweaving_speed_mph": None, "mean_speed_mph": None,
                "density_pc_mi_ln": None,
                "stopping_handoff_reason": "LS >= LMAX; analyze merge/diverge areas under Chapter 14 and remaining area under Chapter 12.",
            })
            return _result(self, common)
        base_capacity = basic_freeway_capacity(ffs)
        density_capacity_per_lane = base_capacity - 438.2 * (1 + vr) ** 1.6 + 0.0765 * parsed.segment_length_ft + 119.8 * parsed.number_of_weaving_lanes
        density_capacity = density_capacity_per_lane * parsed.number_of_lanes * fhv
        weaving_flow_capacity = None
        if parsed.number_of_weaving_lanes in {2, 3}:
            weaving_flow_capacity = ({2: 2400.0, 3: 3500.0}[parsed.number_of_weaving_lanes] / vr) * fhv
        governing_unadjusted = min(value for value in (density_capacity, weaving_flow_capacity) if value is not None)
        prevailing_capacity = governing_unadjusted * parsed.capacity_adjustment_factor
        vc = total * fhv / prevailing_capacity
        common = _base_outputs(parsed, ffs, pce, fhv, movement, weaving, nonweaving, total, vr, lcmin, lmax, base_capacity, density_capacity_per_lane, density_capacity, weaving_flow_capacity, governing_unadjusted, prevailing_capacity, vc)
        if vc > 1.0:
            common.update({
                "capacity_status": "demand_exceeds_capacity", "level_of_service": "F",
                "weaving_speed_mph": None, "nonweaving_speed_mph": None, "mean_speed_mph": None,
                "density_pc_mi_ln": None,
                "stopping_handoff_reason": "Unrounded v/c exceeds 1.00; Chapter 13 does not predict oversaturated speed or density.",
            })
            return _result(self, common)

        lane_change_length = max(parsed.segment_length_ft, 300.0)
        lcw = lcmin + 0.39 * (sqrt(lane_change_length - 300.0) * parsed.number_of_lanes**2 * (1 + parsed.interchange_density_per_mi) ** 0.8)
        inw = parsed.segment_length_ft * parsed.interchange_density_per_mi * nonweaving / 10000.0
        lcnw1 = max(0.0, 0.206 * nonweaving + 0.542 * parsed.segment_length_ft - 192.6 * parsed.number_of_lanes)
        lcnw2 = 2135.0 + 0.223 * (nonweaving - 2000.0)
        if lcnw1 >= lcnw2:
            lcnw, lc_branch = lcnw2, "high_forced_by_discontinuity"
        elif inw <= 1300:
            lcnw, lc_branch = lcnw1, "low"
        elif inw >= 1950:
            lcnw, lc_branch = lcnw2, "high"
        else:
            lcnw, lc_branch = lcnw1 + (lcnw2 - lcnw1) * (inw - 1300.0) / 650.0, "interpolated"
        lcall = lcw + lcnw
        intensity = 0.226 * (lcall / parsed.segment_length_ft) ** 0.789
        sw = MIN_WEAVING_SPEED_MPH + (ffs * parsed.speed_adjustment_factor - MIN_WEAVING_SPEED_MPH) / (1 + intensity)
        snw = ffs * parsed.speed_adjustment_factor - 0.0072 * lcmin - 0.0048 * (total / parsed.number_of_lanes)
        mean_speed = total / (weaving / sw + nonweaving / snw)
        density = (total / parsed.number_of_lanes) / mean_speed
        common.update({
            "capacity_status": "within_capacity", "stopping_handoff_reason": None,
            "lane_change_length_used_ft": lane_change_length, "weaving_lane_changes_lc_h": lcw,
            "nonweaving_index": inw, "nonweaving_lane_changes_low_lc_h": lcnw1,
            "nonweaving_lane_changes_high_lc_h": lcnw2, "nonweaving_lane_changes_lc_h": lcnw,
            "nonweaving_lane_change_branch": lc_branch, "total_lane_changes_lc_h": lcall,
            "weaving_intensity": intensity, "weaving_speed_mph": sw, "nonweaving_speed_mph": snw,
            "mean_speed_mph": mean_speed, "density_pc_mi_ln": density, "level_of_service": _los(density),
        })
        return _result(self, common)


def _volumes(inputs: WeavingSegmentInputs) -> dict[str, float]:
    return {"ff": inputs.volume_ff_veh_h, "fr": inputs.volume_fr_veh_h, "rf": inputs.volume_rf_veh_h, "rr": inputs.volume_rr_veh_h}


def _free_flow_speed(inputs: WeavingSegmentInputs) -> float:
    if inputs.ffs_source == "measured":
        ffs = inputs.free_flow_speed_mph
    else:
        ffs = estimated_free_flow_speed(inputs.base_free_flow_speed_mph, lane_width_adjustment(inputs.lane_width_ft), right_lateral_clearance_adjustment(inputs.right_side_lateral_clearance_ft, inputs.number_of_lanes), inputs.total_ramp_density_per_mi)
    if not 55.0 <= ffs <= 75.0:
        raise HCMCalcError("The qualified freeway weaving FFS must be from 55 through 75 mi/h.")
    return ffs


def _los(density: float) -> str:
    for level, bound in LOS_DENSITY_UPPER_BOUNDS:
        if density <= bound:
            return level
    return "F"


def _base_outputs(inputs: WeavingSegmentInputs, ffs: float, pce: float, fhv: float, movement: dict[str, float], weaving: float, nonweaving: float, total: float, vr: float, lcmin: float, lmax: float, base_capacity: float | None, density_capacity_per_lane: float | None, density_capacity: float | None, weaving_flow_capacity: float | None, governing_unadjusted: float | None, prevailing_capacity: float | None, vc: float | None) -> dict[str, Any]:
    assumptions = ["HCM Version 7.0 Chapter 13 isolated freeway operational analysis.", "One common segment-level Chapter 12 heavy-vehicle factor is applied to every movement.", "No C-D roadway, multilane highway, Design/Sensitivity, facility, queue, or oversaturated performance analysis."]
    warnings = ["LS is the Chapter 13 short length; no length or table input is silently clipped or extrapolated."]
    if inputs.segment_length_ft > 2800:
        warnings.append("The Chapter 13 maximum-length equation is documented as calibrated only to approximately 2,800 ft.")
    return {"calculation_type": "freeway_weaving_segment_operational", "method_family": "weaving_segment", "method_name": "hcm7_v70_freeway_weaving_segment", "method_version": "hcm_7_0", "calculation_contract": "hcm7_v70_chapter_13_isolated_freeway_operational", "facility_type": "freeway_weaving_segment", "analysis_type": "operational_analysis", "engine_native_units": "US_customary", "support_status": "qualified_hcm_7_0", "scope_status": "supported", "input_summary": inputs.to_mapping(), "normalized_geometry": inputs.geometry.__dict__, "ffs_source": inputs.ffs_source, "free_flow_speed_mph": ffs, "passenger_car_equivalent": pce, "pce_source": f"HCM7 Exhibit 12-25 general terrain {inputs.terrain_type}", "heavy_vehicle_adjustment_factor": fhv, "ideal_movement_flow_pc_h": movement, "weaving_flow_pc_h": weaving, "nonweaving_flow_pc_h": nonweaving, "total_flow_pc_h": total, "volume_ratio": vr, "minimum_lane_changes_lc_h": lcmin, "maximum_weaving_length_ft": lmax, "basic_freeway_capacity_pc_h_ln": base_capacity, "density_governed_capacity_pc_h_ln": density_capacity_per_lane, "density_governed_capacity_veh_h": density_capacity, "weaving_flow_capacity_veh_h": weaving_flow_capacity, "governing_unadjusted_capacity_veh_h": governing_unadjusted, "capacity_adjustment_factor": inputs.capacity_adjustment_factor, "adjusted_prevailing_capacity_veh_h": prevailing_capacity, "demand_capacity_ratio": vc, "assumptions": assumptions, "warnings": warnings, "unsupported_scope_notes": ["HCM 7.1 is a separately versioned, presently unqualified method.", "Input/output roadway capacity checks and Chapter 14 analysis are outside this isolated engine."], "source_references": ["HCM 7.0 Chapter 13 Eqs. 13-1 through 13-23 and Exhibit 13-6", "HCM 7.0 Chapter 12 Eq. 12-2, Eq. 12-6, Eq. 12-10, Exhibits 12-20, 12-21, and 12-25"]}


def _result(method: HCM70WeavingSegmentMethod, outputs: dict[str, Any]) -> CalculationResult:
    sources = {"ideal_movement_flow_pc_h": ("pc/h", "HCM7 Eq. 13-1"), "volume_ratio": (None, "HCM7 Chapter 13 Step 3"), "minimum_lane_changes_lc_h": ("lc/h", "HCM7 Eq. 13-2 or Eq. 13-3"), "maximum_weaving_length_ft": ("ft", "HCM7 Eq. 13-4"), "density_governed_capacity_veh_h": ("veh/h", "HCM7 Eq. 13-5 and Eq. 13-6"), "weaving_flow_capacity_veh_h": ("veh/h", "HCM7 Eq. 13-7 and Eq. 13-8"), "adjusted_prevailing_capacity_veh_h": ("veh/h", "HCM7 Eq. 13-9"), "demand_capacity_ratio": (None, "HCM7 Eq. 13-10"), "weaving_lane_changes_lc_h": ("lc/h", "HCM7 Eq. 13-11"), "nonweaving_index": (None, "HCM7 Eq. 13-12"), "nonweaving_lane_changes_lc_h": ("lc/h", "HCM7 Eqs. 13-13 through 13-16"), "total_lane_changes_lc_h": ("lc/h", "HCM7 Eq. 13-17"), "weaving_intensity": (None, "HCM7 Eq. 13-20"), "weaving_speed_mph": ("mi/h", "HCM7 Eq. 13-19"), "nonweaving_speed_mph": ("mi/h", "HCM7 Eq. 13-21"), "mean_speed_mph": ("mi/h", "HCM7 Eq. 13-22"), "density_pc_mi_ln": ("pc/mi/ln", "HCM7 Eq. 13-23"), "level_of_service": (None, "HCM7 Exhibit 13-6")}
    intermediates = [IntermediateValue(name, outputs.get(name), units=unit, source=source) for name, (unit, source) in sources.items() if name in outputs]
    return CalculationResult(method=method.method_name, facility_type=method.facility_type, outputs=outputs, intermediate_values=intermediates, assumptions=outputs["assumptions"], warnings=outputs["warnings"])
