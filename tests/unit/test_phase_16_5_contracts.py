import json
import math
from copy import deepcopy

import pytest

from hcmcalc.cli import result_to_dict
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method
from hcmcalc.ui.manual_facility import (
    build_manual_facility_inputs,
    canonicalize_manual_facility_rows,
    load_facility_template,
    run_manual_facility,
)
from hcmcalc.ui.manual_segment import build_manual_segment_inputs, run_manual_single_segment
from hcmcalc.ui.manual_weaving import (
    weaving_preset_ui_inputs,
    weaving_ui_inputs_to_engine,
    run_manual_weaving,
)
from hcmcalc.ui.project_io import (
    create_manual_facility_project_json,
    load_manual_facility_project_json,
)
from hcmcalc.ui.workflow_state import calculation_input_fingerprint
from hcmcalc.weaving import WeavingSegmentMethod


def test_weaving_ui_adapter_preserves_public_engine_result_for_current_and_handoff_cases() -> None:
    for displayed, unit_system in (
        (weaving_preset_ui_inputs("WVG-CH27-001", "metric"), "metric"),
        (weaving_preset_ui_inputs("WVG-CH27-003", "imperial"), "imperial"),
    ):
        normalized = weaving_ui_inputs_to_engine(displayed, unit_system)
        adapted = run_manual_weaving(normalized)
        direct = WeavingSegmentMethod().calculate(normalized)
        assert result_to_dict(adapted) == result_to_dict(direct)

    handoff_displayed = weaving_preset_ui_inputs("WVG-CH27-001", "imperial")
    handoff_displayed["segment_length"] = 6000.0
    handoff_inputs = weaving_ui_inputs_to_engine(handoff_displayed, "imperial")
    handoff = run_manual_weaving(handoff_inputs)
    assert handoff.outputs["support_status"] == "hcm_handoff_required"
    assert handoff.outputs["level_of_service"] is None


def test_two_lane_segment_ui_adapter_preserves_public_engine_result() -> None:
    values = {
        "unit_system": "metric",
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "posted_speed": 80.0,
        "segment_length": 1.2,
        "lane_width": 3.5,
        "shoulder_width": 1.8,
        "access_point_density": 0.0,
        "analysis_direction_volume": 750.0,
        "peak_hour_factor": 0.94,
        "heavy_vehicle_percent": 5.0,
        "grade_percent": 0.0,
        "opposing_direction_volume": None,
        "horizontal_alignment": "straight",
        "horizontal_alignment_subsegments": [],
    }
    normalized = build_manual_segment_inputs(values)
    adapted = run_manual_single_segment(values)
    direct = TwoLaneHighwayChapter15Method().calculate_single_segment(normalized)

    assert result_to_dict(adapted) == result_to_dict(direct)


def test_facility_inactive_nan_canonicalization_preserves_fingerprint_and_json_contract() -> None:
    template = load_facility_template("level_example_3", "metric")
    clean_rows = deepcopy(template["segments"])
    dirty_rows = deepcopy(clean_rows)
    for row in dirty_rows:
        if row["segment_type"] != "passing_zone":
            row["opposing_direction_volume_veh_h"] = math.nan

    clean_inputs = build_manual_facility_inputs(
        template["template_id"], clean_rows, template["unit_system"]
    )
    dirty_inputs = build_manual_facility_inputs(
        template["template_id"], dirty_rows, template["unit_system"]
    )
    assert clean_inputs == dirty_inputs
    assert calculation_input_fingerprint(
        "hcm7_two_lane_highway_facility", "phase_5_product_integration", clean_inputs
    ) == calculation_input_fingerprint(
        "hcm7_two_lane_highway_facility", "phase_5_product_integration", dirty_inputs
    )

    result = run_manual_facility(template["template_id"], dirty_rows, template["unit_system"])
    payload = create_manual_facility_project_json(
        template["template_id"],
        template["unit_system"],
        dirty_rows,
        result=result_to_dict(result),
        locale="th",
    )
    assert "NaN" not in payload
    json.loads(payload)
    loaded = load_manual_facility_project_json(payload)
    assert loaded["load_status"] == "result_current"
    assert loaded["segment_rows"] == canonicalize_manual_facility_rows(dirty_rows)


@pytest.mark.parametrize("unit_system", ["metric", "imperial"])
def test_weaving_metric_and_imperial_display_paths_keep_same_engine_inputs(unit_system: str) -> None:
    displayed = weaving_preset_ui_inputs("WVG-CH27-001", unit_system)
    reference = weaving_preset_ui_inputs(
        "WVG-CH27-001", "imperial" if unit_system == "metric" else "metric"
    )
    assert weaving_ui_inputs_to_engine(displayed, unit_system) == weaving_ui_inputs_to_engine(
        reference, "imperial" if unit_system == "metric" else "metric"
    )
