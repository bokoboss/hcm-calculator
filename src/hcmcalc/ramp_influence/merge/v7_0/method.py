"""HCM 7.0 isolated freeway merge segment operational engine."""

from math import exp
from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError, IntermediateValue

from ...capacity import MAX_DESIRABLE_MERGE_PC_H, ramp_roadway_capacity_pc_h
from ...common import (
    adjust_v12_reasonableness,
    component_flows,
    freeway_capacity_pc_h,
    freeway_ffs,
    los_for_density,
    outer_lane_speed_merge,
)
from ...models import MergeSegmentInputs
from ...validation import validate_merge


class HCM70MergeSegmentMethod:
    facility_type = "freeway_merge_segment"
    method_name = "hcm7_v70_freeway_merge_segment"
    method_version = "hcm_7_0"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        try:
            parsed = MergeSegmentInputs.from_mapping(inputs)
        except (TypeError, ValueError) as exc:
            raise HCMCalcError(str(exc)) from exc
        validate_merge(parsed)
        ffs = freeway_ffs(parsed)
        flows = component_flows(parsed)
        v_f = flows["freeway_flow_pc_h"]
        v_r = flows["ramp_flow_pc_h"]
        v_fo = v_f + v_r
        pfm, branch = _pfm(parsed.freeway_lanes, v_f, v_r, parsed.acceleration_lane_length_ft, parsed.ramp_ffs_mph)
        v12_initial = v_f * pfm
        v12, adjustment_reason, reasonableness = adjust_v12_reasonableness(parsed.freeway_lanes, v_f, v12_initial)
        v_r12 = v12 + v_r
        freeway_capacity, adjusted_freeway_capacity = freeway_capacity_pc_h(ffs, parsed.freeway_lanes, parsed.capacity_adjustment_factor)
        ramp_capacity = ramp_roadway_capacity_pc_h(parsed.ramp_ffs_mph, parsed.ramp_lanes)
        ramp_adjusted_capacity = ramp_capacity * parsed.capacity_adjustment_factor
        freeway_vc = v_fo / adjusted_freeway_capacity
        ramp_vc = v_r / ramp_adjusted_capacity
        max_desirable_exceeded = v_r12 > MAX_DESIRABLE_MERGE_PC_H
        outputs = _base_outputs(parsed, ffs, flows, v_fo, pfm, branch, v12_initial, v12, adjustment_reason, reasonableness, v_r12, freeway_capacity, adjusted_freeway_capacity, ramp_capacity, ramp_adjusted_capacity, freeway_vc, ramp_vc, max_desirable_exceeded)
        if freeway_vc > 1.0 or ramp_vc > 1.0:
            reason = "downstream_freeway_capacity" if freeway_vc >= ramp_vc else "on_ramp_roadway_capacity"
            outputs.update({"capacity_status": "demand_exceeds_capacity", "governing_capacity_failure": reason, "level_of_service": "F", "density_pc_mi_ln": None, "ramp_influence_speed_mph": None, "outer_lane_speed_mph": None, "all_lanes_speed_mph": None})
            return _result(self, outputs)
        density = 5.475 + 0.00734 * v_r + 0.0078 * v12 - 0.00627 * parsed.acceleration_lane_length_ft
        speeds = _speeds(parsed, ffs, v_f, v_r, v12, v_r12)
        outputs.update({"capacity_status": "within_capacity", "governing_capacity_failure": None, "density_pc_mi_ln": density, "level_of_service": los_for_density(density), **speeds})
        return _result(self, outputs)


def _pfm(lanes: int, v_f: float, v_r: float, la: float, sfr: float) -> tuple[float, str]:
    if lanes == 2:
        return 1.0, "eq_14_8_four_lane_all_freeway_flow_in_lanes_1_2"
    if lanes == 3:
        return 0.5775 + 0.000028 * la, "eq_14_3_six_lane_isolated"
    if v_f / sfr <= 72:
        return 0.2178 - 0.000125 * v_r + 0.01115 * (la / sfr), "eq_14_8_eight_lane_low_vf_sfr"
    return 0.2178 - 0.000125 * v_r, "eq_14_8_eight_lane_high_vf_sfr"


def _speeds(inputs: MergeSegmentInputs, ffs: float, v_f: float, v_r: float, v12: float, v_r12: float) -> dict[str, float | None]:
    capped_vr12 = min(v_r12, MAX_DESIRABLE_MERGE_PC_H)
    ms = 0.321 + 0.0039 * exp(capped_vr12 / 1000.0) - 0.002 * (inputs.acceleration_lane_length_ft * inputs.ramp_ffs_mph * inputs.speed_adjustment_factor / 1000.0)
    sr = ffs * inputs.speed_adjustment_factor - (ffs * inputs.speed_adjustment_factor - 42.0) * ms
    outer_lanes = inputs.freeway_lanes - 2
    if outer_lanes <= 0:
        return {"merge_speed_index": ms, "ramp_influence_speed_mph": sr, "outer_lane_speed_mph": None, "all_lanes_speed_mph": sr}
    outer_flow = (v_f - v12) / outer_lanes
    so = outer_lane_speed_merge(ffs, inputs.speed_adjustment_factor, outer_flow)
    total_speed = (v_r12 + outer_flow * outer_lanes) / ((v_r12 / sr) + ((outer_flow * outer_lanes) / so))
    return {"merge_speed_index": ms, "outer_lane_flow_pc_h_ln": outer_flow, "ramp_influence_speed_mph": sr, "outer_lane_speed_mph": so, "all_lanes_speed_mph": min(total_speed, ffs)}


def _base_outputs(inputs: MergeSegmentInputs, ffs: float, flows: dict[str, Any], v_fo: float, pfm: float, branch: str, v12_initial: float, v12: float, adjustment_reason: str, reasonableness: dict[str, float], v_r12: float, freeway_capacity: float, adjusted_freeway_capacity: float, ramp_capacity: float, adjusted_ramp_capacity: float, freeway_vc: float, ramp_vc: float, max_desirable_exceeded: bool) -> dict[str, Any]:
    warnings = ["Adjacent-ramp branches are deferred and rejected unless adjacent_ramp_context is 'isolated'."]
    if max_desirable_exceeded:
        warnings.append("Maximum desirable merge influence-area flow is exceeded; this is an interpretation warning, not automatic LOS F.")
    return {"calculation_type": "freeway_merge_segment_operational", "method_family": "merge_segment", "method_name": "hcm7_v70_freeway_merge_segment", "method_version": "hcm_7_0", "calculation_contract": "hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational", "facility_type": "freeway_merge_segment", "analysis_type": "operational_analysis", "support_status": "qualified_hcm_7_0_isolated", "scope_status": "supported", "input_summary": inputs.to_mapping(), "geometry_evidence": inputs.geometry_evidence.__dict__, "freeway_ffs_mph": ffs, **flows, "downstream_freeway_flow_pc_h": v_fo, "lane_distribution_branch": branch, "pfm": pfm, "initial_v12_pc_h": v12_initial, "adjusted_v12_pc_h": v12, "v12_adjustment_reason": adjustment_reason, **reasonableness, "merge_influence_entering_flow_vr12_pc_h": v_r12, "freeway_capacity_pc_h": freeway_capacity, "adjusted_freeway_capacity_pc_h": adjusted_freeway_capacity, "ramp_roadway_capacity_pc_h": ramp_capacity, "adjusted_ramp_roadway_capacity_pc_h": adjusted_ramp_capacity, "downstream_freeway_demand_capacity_ratio": freeway_vc, "ramp_demand_capacity_ratio": ramp_vc, "maximum_desirable_merge_flow_pc_h": MAX_DESIRABLE_MERGE_PC_H, "maximum_desirable_influence_flow_exceeded": max_desirable_exceeded, "assumptions": ["HCM 7.0 Chapter 14 isolated one-lane right-side on-ramp operational analysis.", "Freeway and ramp component demand conversions preserve separate PHF and heavy-vehicle factors."], "warnings": warnings, "limitations": ["No left-side ramps, two-lane ramps, lane additions, major merges, managed lanes, C-D roads, service-volume analysis, queues, delay, or spillback prediction.", "HCM 7.1 is known but unqualified."], "source_references": ["HCM 7.0 Chapter 14 Eq. 14-1 through Eq. 14-22, Exhibits 14-3, 14-8, 14-10, 14-12, 14-13, and 14-15."]}


def _result(method: HCM70MergeSegmentMethod, outputs: dict[str, Any]) -> CalculationResult:
    sources = {"freeway_flow_pc_h": ("pc/h", "HCM7 Eq. 14-1"), "ramp_flow_pc_h": ("pc/h", "HCM7 Eq. 14-1"), "pfm": (None, "HCM7 Exhibit 14-8"), "initial_v12_pc_h": ("pc/h", "HCM7 Eq. 14-2"), "adjusted_v12_pc_h": ("pc/h", "HCM7 Eqs. 14-14 through 14-19"), "merge_influence_entering_flow_vr12_pc_h": ("pc/h", "HCM7 Eq. 14-20"), "adjusted_freeway_capacity_pc_h": ("pc/h", "HCM7 Eq. 14-21 and Exhibit 14-10"), "adjusted_ramp_roadway_capacity_pc_h": ("pc/h", "HCM7 Eq. 14-21 and Exhibit 14-12"), "density_pc_mi_ln": ("pc/mi/ln", "HCM7 Eq. 14-22"), "level_of_service": (None, "HCM7 Exhibit 14-3"), "ramp_influence_speed_mph": ("mi/h", "HCM7 Exhibit 14-13"), "outer_lane_speed_mph": ("mi/h", "HCM7 Exhibit 14-13"), "all_lanes_speed_mph": ("mi/h", "HCM7 Exhibit 14-15")}
    return CalculationResult(method=method.method_name, facility_type=method.facility_type, outputs=outputs, intermediate_values=[IntermediateValue(name, outputs.get(name), units=unit, source=source) for name, (unit, source) in sources.items() if name in outputs], assumptions=outputs["assumptions"], warnings=outputs["warnings"])
