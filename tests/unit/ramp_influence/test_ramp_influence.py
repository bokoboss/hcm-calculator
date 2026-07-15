import copy
import inspect

import pytest
import yaml

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.ramp_influence import DivergeSegmentMethod, MergeSegmentMethod
from hcmcalc.ramp_influence.diverge.v7_0 import method as diverge_v70
from hcmcalc.ramp_influence.merge.v7_0 import method as merge_v70
from hcmcalc.ramp_influence.registry import get_diverge_method, get_merge_method


def merge_inputs() -> dict:
    return {
        "method_version": "hcm_7_0",
        "case_id": "unit_merge",
        "facility_type": "freeway_merge_segment",
        "analysis_type": "operational_analysis",
        "analysis_period_minutes": 15,
        "freeway_lanes": 3,
        "ramp_side": "right",
        "ramp_lanes": 1,
        "freeway_demand_veh_h": 3600,
        "ramp_demand_veh_h": 500,
        "freeway_peak_hour_factor": 0.95,
        "ramp_peak_hour_factor": 0.95,
        "freeway_heavy_vehicle_percent": 5,
        "ramp_heavy_vehicle_percent": 5,
        "terrain_type": "level",
        "ffs_source": "measured",
        "free_flow_speed_mph": 65,
        "base_free_flow_speed_mph": None,
        "lane_width_ft": None,
        "right_side_lateral_clearance_ft": None,
        "total_ramp_density_per_mi": None,
        "ramp_ffs_mph": 40,
        "speed_adjustment_factor": 1.0,
        "capacity_adjustment_factor": 1.0,
        "speed_adjustment_factor_source": "hcm_base_conditions",
        "capacity_adjustment_factor_source": "hcm_base_conditions",
        "adjacent_ramp_context": "isolated",
        "geometry_evidence": {"source": "unit", "configuration": "isolated_right_on", "reviewed_by": "test", "notes": "unit"},
        "acceleration_lane_length_ft": 600,
        "downstream_freeway_demand_veh_h": None,
        "lane_addition": False,
        "major_merge": False,
    }


def diverge_inputs() -> dict:
    values = merge_inputs()
    values.update(
        {
            "case_id": "unit_diverge",
            "facility_type": "freeway_diverge_segment",
            "ramp_demand_veh_h": 450,
            "geometry_evidence": {"source": "unit", "configuration": "isolated_right_off", "reviewed_by": "test", "notes": "unit"},
            "deceleration_lane_length_ft": 500,
            "continuing_freeway_demand_veh_h": None,
            "lane_drop": False,
            "option_lane": False,
            "major_diverge": False,
        }
    )
    for key in ("acceleration_lane_length_ft", "downstream_freeway_demand_veh_h", "lane_addition", "major_merge"):
        values.pop(key)
    return values


@pytest.mark.parametrize("lanes", [2, 3, 4])
def test_merge_each_lane_distribution_branch(lanes: int) -> None:
    values = merge_inputs()
    values["freeway_lanes"] = lanes
    output = MergeSegmentMethod().calculate(values).outputs
    assert output["method_family"] == "merge_segment"
    assert output["scope_status"] == "supported"
    assert output["adjusted_v12_pc_h"] > 0


@pytest.mark.parametrize("lanes", [2, 3, 4])
def test_diverge_each_lane_distribution_branch(lanes: int) -> None:
    values = diverge_inputs()
    values["freeway_lanes"] = lanes
    output = DivergeSegmentMethod().calculate(values).outputs
    assert output["method_family"] == "diverge_segment"
    assert output["scope_status"] == "supported"
    assert output["adjusted_v12_pc_h"] > 0


def test_strict_unknown_boolean_nonfinite_and_version_guards() -> None:
    unknown = merge_inputs()
    unknown["surprise"] = 1
    with pytest.raises(HCMCalcError):
        MergeSegmentMethod().calculate(unknown)
    boolean = merge_inputs()
    boolean["freeway_demand_veh_h"] = True
    with pytest.raises(HCMCalcError):
        MergeSegmentMethod().calculate(boolean)
    nonfinite = diverge_inputs()
    nonfinite["ramp_ffs_mph"] = float("inf")
    with pytest.raises(HCMCalcError):
        DivergeSegmentMethod().calculate(nonfinite)
    with pytest.raises(UnsupportedScopeError, match="known but unqualified"):
        get_merge_method("hcm_7_1")
    with pytest.raises(UnsupportedScopeError, match="known but unqualified"):
        get_diverge_method("hcm_7_1")
    mismatch = merge_inputs()
    mismatch["method_version"] = "hcm_7_1"
    with pytest.raises(HCMCalcError, match="exactly match"):
        MergeSegmentMethod().calculate(mismatch)


@pytest.mark.parametrize(
    ("key", "value"),
    [("ramp_side", "left"), ("ramp_lanes", 2), ("adjacent_ramp_context", "downstream_off_ramp"), ("lane_addition", True)],
)
def test_merge_unsupported_geometry_is_guarded(key: str, value: object) -> None:
    values = merge_inputs()
    values[key] = value
    with pytest.raises(UnsupportedScopeError):
        MergeSegmentMethod().calculate(values)


@pytest.mark.parametrize(
    ("key", "value"),
    [("ramp_side", "left"), ("ramp_lanes", 2), ("adjacent_ramp_context", "upstream_on_ramp"), ("lane_drop", True), ("option_lane", True)],
)
def test_diverge_unsupported_geometry_is_guarded(key: str, value: object) -> None:
    values = diverge_inputs()
    values[key] = value
    with pytest.raises(UnsupportedScopeError):
        DivergeSegmentMethod().calculate(values)


def test_capacity_failure_has_los_f_and_null_predictions() -> None:
    merge = merge_inputs()
    merge["freeway_demand_veh_h"] = 8000
    merge_output = MergeSegmentMethod().calculate(merge).outputs
    assert merge_output["capacity_status"] == "demand_exceeds_capacity"
    assert merge_output["level_of_service"] == "F"
    assert merge_output["density_pc_mi_ln"] is None
    diverge = diverge_inputs()
    diverge["ramp_demand_veh_h"] = 2300
    diverge_output = DivergeSegmentMethod().calculate(diverge).outputs
    assert diverge_output["capacity_status"] == "demand_exceeds_capacity"
    assert diverge_output["ramp_influence_speed_mph"] is None


def test_exact_capacity_continues_and_max_desirable_is_warning_only() -> None:
    values = merge_inputs()
    initial = MergeSegmentMethod().calculate(values).outputs
    scale = initial["adjusted_freeway_capacity_pc_h"] / initial["downstream_freeway_flow_pc_h"]
    values["freeway_demand_veh_h"] *= scale
    values["ramp_demand_veh_h"] *= scale
    exact = MergeSegmentMethod().calculate(values).outputs
    assert exact["downstream_freeway_demand_capacity_ratio"] == pytest.approx(1.0, abs=1e-12)
    assert exact["density_pc_mi_ln"] is not None

    warning = merge_inputs()
    warning["freeway_lanes"] = 2
    warning["freeway_demand_veh_h"] = 3600
    warning["ramp_demand_veh_h"] = 600
    output = MergeSegmentMethod().calculate(warning).outputs
    assert output["maximum_desirable_influence_flow_exceeded"] is True
    assert output["capacity_status"] == "within_capacity"
    assert output["level_of_service"] != "F"


def test_estimated_ffs_reuses_chapter_12_foundation() -> None:
    values = diverge_inputs()
    values.update(
        {
            "ffs_source": "estimated",
            "free_flow_speed_mph": None,
            "base_free_flow_speed_mph": 75.0,
            "lane_width_ft": 12.0,
            "right_side_lateral_clearance_ft": 6.0,
            "total_ramp_density_per_mi": 0.0,
        }
    )
    assert DivergeSegmentMethod().calculate(values).outputs["freeway_ffs_mph"] == 75.0


def test_chapter_28_compatible_examples() -> None:
    with open("references/merge_diverge_example_inputs.yaml", encoding="utf-8") as handle:
        cases = yaml.safe_load(handle)["examples"]
    for case in cases:
        method = MergeSegmentMethod() if case["method_family"] == "merge_segment" else DivergeSegmentMethod()
        output = method.calculate(case["inputs"]).outputs
        for key, expected in case["expected"].items():
            if isinstance(expected, (int, float)):
                tolerance = 4.0 if key.endswith("_pc_h") else 0.75 if key == "all_lanes_speed_mph" else 0.15
                assert output[key] == pytest.approx(expected, abs=tolerance), case["id"] + ":" + key
            else:
                assert output[key] == expected


def test_v70_modules_do_not_reference_hcm_71_or_each_other() -> None:
    merge_source = inspect.getsource(merge_v70)
    diverge_source = inspect.getsource(diverge_v70)
    assert "hcm_7_1" not in merge_source
    assert "hcm_7_1" not in diverge_source
    assert "diverge.v7_0" not in merge_source
    assert "merge.v7_0" not in diverge_source
