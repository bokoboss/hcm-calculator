from copy import deepcopy

import pytest

from hcmcalc.cli import result_to_dict
from hcmcalc.core import UnsupportedScopeError
from hcmcalc.ui.manual_multilane import (
    BLANK_CASE_ID,
    build_manual_multilane_audit_record,
    clear_manual_multilane_state,
    heavy_vehicle_adjustment_method_from_ui_inputs,
    load_multilane_template,
    multilane_blank_ui_inputs,
    multilane_display_outputs,
    multilane_engine_inputs_to_ui,
    multilane_template_options,
    multilane_template_ui_inputs,
    multilane_ui_inputs_to_engine,
    run_manual_multilane,
)
from hcmcalc.ui.units import MILES_TO_KILOMETERS
from hcmcalc.ui.workflow_state import (
    STALE,
    mark_calculated,
    normalized_input_fingerprint,
    workflow_status,
)


def test_multilane_template_options_expose_only_example_4_directions() -> None:
    assert multilane_template_options() == {
        "MLH-CH26-004-EB": "Chapter 26 Example 4 - Eastbound starting values",
        "MLH-CH26-004-WB": "Chapter 26 Example 4 - Westbound starting values",
    }


def test_multilane_task_starter_exposes_examples_and_blank_case() -> None:
    options = multilane_template_options(include_blank=True)

    assert tuple(options) == (
        "MLH-CH26-004-EB",
        "MLH-CH26-004-WB",
        BLANK_CASE_ID,
    )
    assert options[BLANK_CASE_ID] == "Blank case"
    assert multilane_blank_ui_inputs()["heavy_vehicle_adjustment_method"] == "general_terrain"


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ({"pce_mode": "internal", "terrain_type": "level"}, "general_terrain"),
        ({"pce_mode": "internal", "terrain_type": "rolling"}, "general_terrain"),
        ({"pce_mode": "internal", "terrain_type": "specific_grade"}, "specific_grade"),
        ({"pce_mode": "external", "terrain_type": "specific_grade"}, "external_pce"),
        ({"heavy_vehicle_adjustment_method": "external_pce"}, "external_pce"),
    ],
)
def test_heavy_vehicle_method_adapter_uses_language_neutral_values(
    values: dict[str, str], expected: str
) -> None:
    assert heavy_vehicle_adjustment_method_from_ui_inputs(values) == expected


@pytest.mark.parametrize(
    ("case_id", "direction", "density", "speed"),
    [
        ("MLH-CH26-004-EB", "eastbound", 18.1, 49.5),
        ("MLH-CH26-004-WB", "westbound", 18.8, 52.0),
    ],
)
def test_multilane_template_runs_existing_validated_engine_path(
    case_id: str, direction: str, density: float, speed: float
) -> None:
    template = load_multilane_template(case_id)

    assert template["inputs"]["direction"] == direction
    result = result_to_dict(run_manual_multilane(template["inputs"]))

    assert result["outputs"]["density_pc_mi_ln"] == pytest.approx(density, abs=0.1)
    assert result["outputs"]["speed_used_for_density_mph"] == speed
    assert result["outputs"]["level_of_service"] == "C"


def test_unsupported_multilane_template_edit_rejects_clearly() -> None:
    inputs = deepcopy(load_multilane_template("MLH-CH26-004-EB")["inputs"])
    inputs["number_of_lanes"] = 4

    with pytest.raises(UnsupportedScopeError, match="two or three lanes"):
        run_manual_multilane(inputs)


@pytest.mark.parametrize("case_id", ["MLH-CH26-004-EB", "MLH-CH26-004-WB"])
def test_metric_template_loading_round_trips_to_engine_inputs(case_id: str) -> None:
    template_inputs = load_multilane_template(case_id)["inputs"]
    displayed = multilane_template_ui_inputs(case_id, "metric")

    assert displayed["segment_length"] == pytest.approx(2.01168)
    assert displayed["posted_speed_limit"] == pytest.approx(72.42048)
    assert displayed["lane_width"] == pytest.approx(3.6576)
    assert displayed["roadside_lateral_clearance"] == pytest.approx(3.6576)
    normalized = multilane_ui_inputs_to_engine(displayed, template_inputs, "metric")
    assert normalized["segment_length_ft"] == template_inputs["segment_length_ft"]
    assert normalized["free_flow_speed_mph"] is None
    assert normalized["left_side_lateral_clearance_ft"] is None
    assert normalized["passenger_car_equivalent"] is None


def test_metric_access_density_converts_to_engine_native_per_mile() -> None:
    template_inputs = load_multilane_template("MLH-CH26-004-EB")["inputs"]
    displayed = multilane_engine_inputs_to_ui(template_inputs, "metric")

    assert displayed["access_point_density"] == pytest.approx(
        10.0 / MILES_TO_KILOMETERS
    )
    assert multilane_ui_inputs_to_engine(displayed, template_inputs, "metric")[
        "access_point_density_per_mi"
    ] == 10.0


def test_multilane_metric_outputs_convert_speed_and_density_only() -> None:
    result = result_to_dict(
        run_manual_multilane(load_multilane_template("MLH-CH26-004-EB")["inputs"])
    )

    display = multilane_display_outputs(result["outputs"], "metric")

    assert display["speed_used_for_density"] == {
        "value": pytest.approx(49.5 * MILES_TO_KILOMETERS),
        "unit": "km/h",
    }
    assert display["density"] == {
        "value": pytest.approx(
            result["outputs"]["density_pc_mi_ln"] / MILES_TO_KILOMETERS
        ),
        "unit": "pc/km/ln",
    }
    assert "adjusted_capacity" not in display
    assert display["capacity"]["value"] == result["outputs"]["capacity_pc_h_ln"]
    assert display["capacity"]["unit"] == "pc/h/ln"


def test_multilane_display_outputs_exposes_canonical_capacity_metric() -> None:
    result = result_to_dict(
        run_manual_multilane(load_multilane_template("MLH-CH26-004-EB")["inputs"])
    )

    display = multilane_display_outputs(result["outputs"], "imperial")

    assert set(display) == {
        "density",
        "speed_used_for_density",
        "adjusted_free_flow_speed",
        "base_free_flow_speed",
        "demand_flow_rate",
        "capacity",
    }
    assert display["capacity"] == {
        "value": result["outputs"]["capacity_pc_h_ln"],
        "unit": "pc/h/ln",
    }


@pytest.mark.parametrize("case_id", ["MLH-CH26-004-EB", "MLH-CH26-004-WB"])
def test_metric_and_imperial_modes_produce_equivalent_engine_results(
    case_id: str,
) -> None:
    template_inputs = load_multilane_template(case_id)["inputs"]
    imperial_inputs = multilane_ui_inputs_to_engine(
        multilane_template_ui_inputs(case_id, "imperial"), template_inputs, "imperial"
    )
    metric_inputs = multilane_ui_inputs_to_engine(
        multilane_template_ui_inputs(case_id, "metric"), template_inputs, "metric"
    )

    imperial_result = result_to_dict(run_manual_multilane(imperial_inputs))
    metric_result = result_to_dict(run_manual_multilane(metric_inputs))

    assert imperial_result == metric_result


def test_unit_or_template_switch_clears_stored_multilane_result() -> None:
    state = {
        "manual_multilane_input_length_MLH-CH26-004-EB_metric": 2.0,
        "manual_multilane_result": {"outputs": {}},
        "manual_multilane_error": "old error",
        "manual_multilane_audit": {"unit_system": "metric"},
        "manual_multilane_template_context": ("MLH-CH26-004-EB", "metric"),
        "calculation_workflow_state": {
            "manual_multilane": {"fingerprint": "old"},
            "other_workflow": {"fingerprint": "kept"},
        },
        "unrelated": "preserved",
    }

    clear_manual_multilane_state(state)

    assert state == {
        "manual_multilane_template_context": ("MLH-CH26-004-EB", "metric"),
        "calculation_workflow_state": {
            "other_workflow": {"fingerprint": "kept"},
        },
        "unrelated": "preserved",
    }


def test_multilane_audit_records_success_without_export_or_project_data() -> None:
    inputs = load_multilane_template("MLH-CH26-004-WB")["inputs"]
    result = run_manual_multilane(inputs)
    audit = build_manual_multilane_audit_record(
        "MLH-CH26-004-WB", inputs, result=result
    )

    assert audit["calculation_succeeded"] is True
    assert audit["unit_system"] == "imperial"
    assert audit["support_status"] == "bounded_multilane_segment_phase_8"
    assert "project_type" not in audit
    assert "export" not in audit


def test_multilane_metric_audit_preserves_display_and_engine_inputs() -> None:
    template_inputs = load_multilane_template("MLH-CH26-004-WB")["inputs"]
    displayed = multilane_engine_inputs_to_ui(template_inputs, "metric")
    audit = build_manual_multilane_audit_record(
        "MLH-CH26-004-WB",
        template_inputs,
        unit_system="metric",
        displayed_inputs=displayed,
        result=run_manual_multilane(template_inputs),
    )

    assert audit["unit_system"] == "metric"
    assert audit["displayed_inputs"] == displayed
    assert audit["submitted_inputs"] == template_inputs


def test_measured_mode_normalizes_inactive_geometry_and_ignores_hidden_values() -> None:
    template = load_multilane_template("MLH-CH26-004-EB")["inputs"]
    values = multilane_template_ui_inputs("MLH-CH26-004-EB", "imperial") | {
        "ffs_source": "measured", "free_flow_speed": 60.0,
    }
    normalized = multilane_ui_inputs_to_engine(values, template, "imperial")
    changed_hidden_values = values | {
        "posted_speed_limit": 35.0, "lane_width": 10.0,
        "roadside_lateral_clearance": 0.0, "access_point_density": 40.0,
        "median_type": "divided", "left_side_lateral_clearance": 0.0,
    }

    assert all(normalized[key] is None for key in (
        "posted_speed_limit_mph", "lane_width_ft", "roadside_lateral_clearance_ft",
        "median_type", "access_point_density_per_mi", "left_side_lateral_clearance_ft",
    ))
    assert normalized == multilane_ui_inputs_to_engine(changed_hidden_values, template, "imperial")


def test_estimated_mode_ignores_hidden_measured_speed_and_mode_switch_is_stale() -> None:
    template = load_multilane_template("MLH-CH26-004-EB")["inputs"]
    estimated = multilane_template_ui_inputs("MLH-CH26-004-EB", "imperial") | {
        "ffs_source": "estimated", "pce_mode": "internal", "free_flow_speed": 45.0,
    }
    normalized = multilane_ui_inputs_to_engine(estimated, template, "imperial")
    assert normalized["free_flow_speed_mph"] is None
    assert normalized_input_fingerprint(normalized) == normalized_input_fingerprint(
        multilane_ui_inputs_to_engine(estimated | {"free_flow_speed": 70.0}, template, "imperial")
    )

    state: dict[str, object] = {}
    mark_calculated(state, "multilane", normalized)
    measured = multilane_ui_inputs_to_engine(
        estimated | {"ffs_source": "measured", "free_flow_speed": 55.0}, template, "imperial"
    )
    assert workflow_status(state, "multilane", measured) == STALE


def test_divided_median_and_external_pce_are_normalized_explicitly() -> None:
    template = load_multilane_template("MLH-CH26-004-EB")["inputs"]
    values = multilane_template_ui_inputs("MLH-CH26-004-EB", "imperial") | {
        "median_type": "divided", "left_side_lateral_clearance": 2.0,
        "pce_mode": "external", "passenger_car_equivalent": 3.25,
    }
    normalized = multilane_ui_inputs_to_engine(values, template, "imperial")

    assert normalized["left_side_lateral_clearance_ft"] == 2.0
    assert normalized["passenger_car_equivalent"] == 3.25
    assert run_manual_multilane(normalized).outputs["pce_source"] == "external_user_supplied_override"


@pytest.mark.parametrize("invalid", [True, float("nan"), float("inf")])
def test_multilane_normalization_rejects_non_finite_or_boolean_ui_numbers(
    invalid: float | bool,
) -> None:
    template = load_multilane_template("MLH-CH26-004-EB")
    displayed = multilane_template_ui_inputs("MLH-CH26-004-EB") | {
        "demand_volume_veh_h": invalid
    }

    with pytest.raises(
        ValueError, match="demand_volume_veh_h must be a finite numeric value"
    ):
        multilane_ui_inputs_to_engine(displayed, template["inputs"], "imperial")


def _equivalent_legacy_and_task_values(
    method: str,
    *,
    truck_mix: str = "default_30_sut_70_tt",
    demand_volume: float = 1500.0,
    ffs_source: str = "estimated",
) -> tuple[dict[str, object], dict[str, object]]:
    base = multilane_template_ui_inputs("MLH-CH26-004-EB", "imperial")
    base.update(
        {
            "demand_volume_veh_h": demand_volume,
            "ffs_source": ffs_source,
            "grade_percent": 3.0,
        }
    )
    if ffs_source == "measured":
        base["free_flow_speed"] = 55.0
    legacy = deepcopy(base)
    task = {
        key: base[key]
        for key in (
            "number_of_lanes",
            "segment_length",
            "demand_volume_veh_h",
            "peak_hour_factor",
            "heavy_vehicle_percent",
            "ffs_source",
        )
        if key in base
    }
    task["heavy_vehicle_adjustment_method"] = method
    if ffs_source == "measured":
        task["free_flow_speed"] = base["free_flow_speed"]
    else:
        task.update(
            {
                key: base[key]
                for key in (
                    "posted_speed_limit",
                    "lane_width",
                    "roadside_lateral_clearance",
                    "median_type",
                    "access_point_density",
                )
            }
        )
    if method == "general_terrain":
        legacy.update({"terrain_type": "level", "grade_percent": 0.0})
        task["terrain_type"] = "level"
    elif method == "specific_grade":
        legacy.update({"terrain_type": "specific_grade", "truck_mix": truck_mix})
        task.update({"grade_percent": 3.0, "truck_mix": truck_mix})
    else:
        legacy.update(
            {
                "pce_mode": "external",
                "passenger_car_equivalent": 2.5,
                "grade_percent": 0.0,
            }
        )
        task["passenger_car_equivalent"] = 2.5
    return legacy, task


@pytest.mark.parametrize(
    ("method", "truck_mix"),
    [
        ("general_terrain", "default_30_sut_70_tt"),
        ("specific_grade", "default_30_sut_70_tt"),
        ("specific_grade", "equal_50_sut_50_tt"),
        ("specific_grade", "majority_70_sut_30_tt"),
        ("external_pce", "default_30_sut_70_tt"),
    ],
)
def test_task_method_mapping_preserves_legacy_engine_inputs_and_results(
    method: str, truck_mix: str
) -> None:
    template = load_multilane_template("MLH-CH26-004-EB")["inputs"]
    legacy, task = _equivalent_legacy_and_task_values(method, truck_mix=truck_mix)

    legacy_engine = multilane_ui_inputs_to_engine(legacy, template, "imperial")
    task_engine = multilane_ui_inputs_to_engine(task, template, "imperial")

    assert task_engine == legacy_engine
    assert result_to_dict(run_manual_multilane(task_engine)) == result_to_dict(
        run_manual_multilane(legacy_engine)
    )


def test_task_general_terrain_mapping_preserves_rolling_engine_path() -> None:
    template = load_multilane_template("MLH-CH26-004-EB")["inputs"]
    base = multilane_template_ui_inputs("MLH-CH26-004-EB", "imperial")
    legacy = base | {
        "pce_mode": "internal",
        "terrain_type": "rolling",
        "grade_percent": 0.0,
        "truck_mix": "default_30_sut_70_tt",
    }
    task = base | {
        "heavy_vehicle_adjustment_method": "general_terrain",
        "terrain_type": "rolling",
    }

    legacy_engine = multilane_ui_inputs_to_engine(legacy, template, "imperial")
    task_engine = multilane_ui_inputs_to_engine(task, template, "imperial")

    assert task_engine == legacy_engine
    assert result_to_dict(run_manual_multilane(task_engine)) == result_to_dict(
        run_manual_multilane(legacy_engine)
    )


def test_task_method_mapping_preserves_measured_and_capacity_failure_cases() -> None:
    template = load_multilane_template("MLH-CH26-004-EB")["inputs"]
    for method, demand in (("specific_grade", 1500.0), ("external_pce", 10000.0)):
        legacy, task = _equivalent_legacy_and_task_values(
            method,
            demand_volume=demand,
            ffs_source="measured",
        )
        legacy_engine = multilane_ui_inputs_to_engine(legacy, template, "imperial")
        task_engine = multilane_ui_inputs_to_engine(task, template, "imperial")
        assert task_engine == legacy_engine
        assert result_to_dict(run_manual_multilane(task_engine)) == result_to_dict(
            run_manual_multilane(legacy_engine)
        )


def test_task_method_hidden_fields_are_neutral_for_validation_and_fingerprint() -> None:
    template = load_multilane_template("MLH-CH26-004-EB")["inputs"]
    _, external = _equivalent_legacy_and_task_values("external_pce")
    baseline = multilane_ui_inputs_to_engine(external, template, "imperial")
    hidden_changed = external | {
        "grade_percent": float("nan"),
        "terrain_type": "not-an-engine-terrain",
        "truck_mix": "not-an-engine-truck-mix",
        "free_flow_speed": float("nan"),
    }
    assert multilane_ui_inputs_to_engine(hidden_changed, template, "imperial") == baseline
    assert normalized_input_fingerprint(baseline) == normalized_input_fingerprint(
        multilane_ui_inputs_to_engine(hidden_changed, template, "imperial")
    )

    active_change = external | {"passenger_car_equivalent": 2.6}
    changed_engine = multilane_ui_inputs_to_engine(active_change, template, "imperial")
    assert normalized_input_fingerprint(changed_engine) != normalized_input_fingerprint(baseline)
    state: dict[str, object] = {}
    mark_calculated(state, "manual_multilane", baseline)
    assert workflow_status(state, "manual_multilane", changed_engine) == STALE
