import copy
import inspect

import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.weaving import WeavingSegmentMethod
from hcmcalc.weaving.registry import get_weaving_method
from hcmcalc.weaving.v7_0 import method as v70_method


def _inputs() -> dict:
    return {"method_version":"hcm_7_0","case_id":"unit","facility_type":"freeway_weaving_segment","analysis_type":"operational_analysis","direction":"northbound","configuration":"one_sided","analysis_period_minutes":15,"peak_hour_factor":1.0,"segment_length_ft":1000,"number_of_lanes":4,"number_of_weaving_lanes":2,"volume_ff_veh_h":3000,"volume_fr_veh_h":300,"volume_rf_veh_h":600,"volume_rr_veh_h":100,"interchange_density_per_mi":1.0,"ffs_source":"measured","free_flow_speed_mph":65,"base_free_flow_speed_mph":None,"lane_width_ft":None,"right_side_lateral_clearance_ft":None,"total_ramp_density_per_mi":None,"heavy_vehicle_percent":0,"terrain_type":"level","speed_adjustment_factor":1.0,"capacity_adjustment_factor":1.0,"speed_adjustment_factor_source":"hcm_base_conditions","capacity_adjustment_factor_source":"hcm_base_conditions","lc_rf":1,"lc_fr":1,"lc_rr":None,"geometry":{"entry_side":"right","exit_side":"right","reachable_origin_destination_lanes":{"ff":"mainline","fr":"exit","rf":"mainline","rr":"ramp"},"option_lane_status":{"fr":False,"rf":False,"rr":False},"nwl_basis":"reviewed plans","lane_change_basis":"reviewed plans"}}


def test_lmax_equality_and_above_return_handoff_not_exception() -> None:
    values = _inputs()
    initial = WeavingSegmentMethod().calculate(values).outputs
    for length in (initial["maximum_weaving_length_ft"], initial["maximum_weaving_length_ft"] + 0.01):
        case = copy.deepcopy(values); case["segment_length_ft"] = length
        result = WeavingSegmentMethod().calculate(case).outputs
        assert result["scope_status"] == "hcm_handoff_lmax"
        assert result["mean_speed_mph"] is None and result["level_of_service"] is None
        assert result["adjusted_prevailing_capacity_veh_h"] is None


def test_above_capacity_has_los_f_and_no_predicted_speed_or_density() -> None:
    values = _inputs(); values["volume_ff_veh_h"] = 9000
    result = WeavingSegmentMethod().calculate(values).outputs
    assert result["demand_capacity_ratio"] > 1.0
    assert result["capacity_status"] == "demand_exceeds_capacity"
    assert result["level_of_service"] == "F"
    assert result["weaving_speed_mph"] is None and result["density_pc_mi_ln"] is None


def test_unrounded_exact_capacity_continues_to_speed_and_density() -> None:
    values = _inputs()
    initial = WeavingSegmentMethod().calculate(values).outputs
    scale = initial["adjusted_prevailing_capacity_veh_h"] / (
        initial["total_flow_pc_h"] * initial["heavy_vehicle_adjustment_factor"]
    )
    for name in ("volume_ff_veh_h", "volume_fr_veh_h", "volume_rf_veh_h", "volume_rr_veh_h"):
        values[name] *= scale
    result = WeavingSegmentMethod().calculate(values).outputs
    assert result["demand_capacity_ratio"] == pytest.approx(1.0, abs=1e-12)
    assert result["capacity_status"] == "within_capacity"
    assert result["mean_speed_mph"] is not None and result["density_pc_mi_ln"] is not None


@pytest.mark.parametrize(("lanes", "nwl"), [(3, 2), (3, 3), (4, 2), (4, 3)])
def test_each_qualified_one_sided_lane_domain_is_accepted(lanes: int, nwl: int) -> None:
    values = _inputs(); values["number_of_lanes"] = lanes; values["number_of_weaving_lanes"] = nwl
    assert WeavingSegmentMethod().calculate(values).outputs["scope_status"] == "supported"


def test_strict_contract_rejects_unknown_bool_and_ambiguous_geometry() -> None:
    unknown = _inputs(); unknown["surprise"] = 1
    with pytest.raises(HCMCalcError): WeavingSegmentMethod().calculate(unknown)
    boolean = _inputs(); boolean["segment_length_ft"] = True
    with pytest.raises(HCMCalcError): WeavingSegmentMethod().calculate(boolean)
    ambiguous = _inputs(); ambiguous["geometry"]["option_lane_status"] = {"fr": False}
    with pytest.raises(HCMCalcError): WeavingSegmentMethod().calculate(ambiguous)


def test_version_registry_is_explicit_and_71_cannot_execute_as_70() -> None:
    with pytest.raises(UnsupportedScopeError, match="known but unqualified"): get_weaving_method("hcm_7_1")
    with pytest.raises(UnsupportedScopeError, match="Unknown"): get_weaving_method("hcm_9_0")
    inputs = _inputs(); inputs["method_version"] = "hcm_7_1"
    with pytest.raises(HCMCalcError, match="exactly match"): WeavingSegmentMethod().calculate(inputs)


def test_v70_has_no_v71_import_or_runtime_reference() -> None:
    assert "v7_1" not in inspect.getsource(v70_method)


def test_estimated_ffs_path_is_supported_without_measured_input() -> None:
    values = _inputs()
    values.update({"ffs_source": "estimated", "free_flow_speed_mph": None,
                   "base_free_flow_speed_mph": 75.0, "lane_width_ft": 12.0,
                   "right_side_lateral_clearance_ft": 6.0,
                   "total_ramp_density_per_mi": 0.0})
    output = WeavingSegmentMethod().calculate(values).outputs
    assert output["free_flow_speed_mph"] == 75.0
