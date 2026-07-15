from copy import deepcopy

import pytest

from hcmcalc.cli import result_to_dict
from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.ui.manual_freeway import (
    build_manual_freeway_audit_record,
    clear_manual_freeway_state,
    freeway_display_outputs,
    freeway_engine_inputs_to_ui,
    freeway_preset_options,
    freeway_preset_ui_inputs,
    freeway_ui_inputs_to_engine,
    load_freeway_preset,
    run_manual_freeway,
)
from hcmcalc.ui.units import MILES_TO_KILOMETERS


def test_freeway_preset_options_expose_only_chapter_26_example_1() -> None:
    assert freeway_preset_options() == {
        "BF-CH26-001": "Chapter 26 Example 1 starting values",
    }


def test_freeway_preset_loads_starting_values_from_fixture() -> None:
    preset = load_freeway_preset("BF-CH26-001")

    assert preset["validation_status"] == "chapter_26_example_validated_v0_1"
    assert preset["inputs"]["case_id"] == "BF-CH26-001"
    assert preset["inputs"]["number_of_lanes"] == 2
    assert preset["inputs"]["demand_volume_veh_h"] == 2000.0
    assert preset["inputs"]["ffs_source"] == "estimated"


def test_freeway_preset_runs_existing_validated_engine_path() -> None:
    result = result_to_dict(
        run_manual_freeway(load_freeway_preset("BF-CH26-001")["inputs"])
    )

    outputs = result["outputs"]
    assert outputs["level_of_service"] == "C"
    assert outputs["density_pc_mi_ln"] == pytest.approx(18.8, abs=0.1)
    assert outputs["speed_used_for_density_mph"] == pytest.approx(60.8, abs=0.1)
    assert outputs["demand_flow_rate_pc_h_ln"] == pytest.approx(1142.0, abs=1.0)
    assert outputs["capacity_check"] == "within_capacity"


def test_unsupported_freeway_edit_rejects_clearly() -> None:
    inputs = deepcopy(load_freeway_preset("BF-CH26-001")["inputs"])
    inputs["grade_percent"] = 0.0

    with pytest.raises(HCMCalcError, match="only applicable"):
        run_manual_freeway(inputs)


def test_freeway_metric_template_loading_round_trips_to_engine_inputs() -> None:
    preset_inputs = load_freeway_preset("BF-CH26-001")["inputs"]
    displayed = freeway_preset_ui_inputs("BF-CH26-001", "metric")

    assert displayed["segment_length"] == pytest.approx(1.609344)
    assert displayed["base_free_flow_speed"] == pytest.approx(
        75.4 * MILES_TO_KILOMETERS
    )
    assert displayed["total_ramp_density"] == pytest.approx(4.0 / MILES_TO_KILOMETERS)
    assert freeway_ui_inputs_to_engine(displayed, preset_inputs, "metric") == (
        preset_inputs
    )


def test_freeway_metric_outputs_convert_speed_and_density_only() -> None:
    result = result_to_dict(
        run_manual_freeway(load_freeway_preset("BF-CH26-001")["inputs"])
    )

    display = freeway_display_outputs(result["outputs"], "metric")

    assert display["speed_used_for_density"] == {
        "value": pytest.approx(
            result["outputs"]["speed_used_for_density_mph"] * MILES_TO_KILOMETERS
        ),
        "unit": "km/h",
    }
    assert display["density"] == {
        "value": pytest.approx(
            result["outputs"]["density_pc_mi_ln"] / MILES_TO_KILOMETERS
        ),
        "unit": "pc/km/ln",
    }
    assert display["capacity"]["value"] == result["outputs"]["capacity_pc_h_ln"]
    assert display["capacity"]["unit"] == "pc/h/ln"


def test_freeway_display_preserves_absent_above_capacity_speed_and_density() -> None:
    inputs = load_freeway_preset("BF-CH26-001")["inputs"] | {
        "demand_volume_veh_h": 20000.0,
    }
    outputs = result_to_dict(run_manual_freeway(inputs))["outputs"]

    display = freeway_display_outputs(outputs, "imperial")

    assert outputs["level_of_service"] == "F"
    assert display["speed_used_for_density"]["value"] is None
    assert display["density"]["value"] is None


def test_freeway_metric_and_imperial_modes_produce_equivalent_engine_results() -> None:
    preset_inputs = load_freeway_preset("BF-CH26-001")["inputs"]
    imperial_inputs = freeway_ui_inputs_to_engine(
        freeway_preset_ui_inputs("BF-CH26-001", "imperial"),
        preset_inputs,
        "imperial",
    )
    metric_inputs = freeway_ui_inputs_to_engine(
        freeway_preset_ui_inputs("BF-CH26-001", "metric"),
        preset_inputs,
        "metric",
    )

    imperial_result = result_to_dict(run_manual_freeway(imperial_inputs))
    metric_result = result_to_dict(run_manual_freeway(metric_inputs))

    assert imperial_result == metric_result


def test_unit_or_preset_switch_preserves_freeway_result_for_audit() -> None:
    state = {
        "manual_freeway_input_length_BF-CH26-001_metric": 1.6,
        "manual_freeway_result": {"outputs": {}},
        "manual_freeway_error": "old error",
        "manual_freeway_audit": {"unit_system": "metric"},
        "manual_freeway_preset_context": ("BF-CH26-001", "metric"),
        "unrelated": "preserved",
    }

    clear_manual_freeway_state(state)

    assert state == {
        "manual_freeway_result": {"outputs": {}},
        "manual_freeway_audit": {"unit_system": "metric"},
        "manual_freeway_preset_context": ("BF-CH26-001", "metric"),
        "unrelated": "preserved",
    }


def test_freeway_audit_records_guarded_save_load_and_export_scope() -> None:
    inputs = load_freeway_preset("BF-CH26-001")["inputs"]
    audit = build_manual_freeway_audit_record(
        "BF-CH26-001", inputs, result=run_manual_freeway(inputs)
    )

    assert audit["calculation_succeeded"] is True
    assert audit["unit_system"] == "imperial"
    assert audit["support_status"] == "supported_basic_freeway_segment_v0_1"
    assert "project_type" not in audit
    assert any(
        "Save/Load and export/reporting preserve only this bounded" in note
        for note in audit["unsupported_behavior_notes"]
    )


def test_freeway_engine_inputs_to_ui_preserves_measured_ffs_path_shape() -> None:
    inputs = deepcopy(load_freeway_preset("BF-CH26-001")["inputs"])
    inputs.update(
        {
            "ffs_source": "measured",
            "free_flow_speed_mph": 65.0,
            "base_free_flow_speed_mph": None,
            "lane_width_ft": None,
            "right_side_lateral_clearance_ft": None,
            "total_ramp_density_per_mi": None,
        }
    )

    displayed = freeway_engine_inputs_to_ui(inputs, "imperial")

    assert displayed["ffs_source"] == "measured"
    assert displayed["free_flow_speed"] == 65.0
    assert displayed["base_free_flow_speed"] is None
