from copy import deepcopy

import pytest

from hcmcalc.cli import result_to_dict
from hcmcalc.core import UnsupportedScopeError
from hcmcalc.ui.manual_multilane import (
    build_manual_multilane_audit_record,
    clear_manual_multilane_state,
    load_multilane_template,
    multilane_display_outputs,
    multilane_engine_inputs_to_ui,
    multilane_template_options,
    multilane_template_ui_inputs,
    multilane_ui_inputs_to_engine,
    run_manual_multilane,
)
from hcmcalc.ui.units import MILES_TO_KILOMETERS


def test_multilane_template_options_expose_only_example_4_directions() -> None:
    assert multilane_template_options() == {
        "MLH-CH26-004-EB": "Chapter 26 Example 4 - Eastbound starting values",
        "MLH-CH26-004-WB": "Chapter 26 Example 4 - Westbound starting values",
    }


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
    inputs["number_of_lanes"] = 3

    with pytest.raises(UnsupportedScopeError, match="number_of_lanes"):
        run_manual_multilane(inputs)


@pytest.mark.parametrize("case_id", ["MLH-CH26-004-EB", "MLH-CH26-004-WB"])
def test_metric_template_loading_round_trips_to_engine_inputs(case_id: str) -> None:
    template_inputs = load_multilane_template(case_id)["inputs"]
    displayed = multilane_template_ui_inputs(case_id, "metric")

    assert displayed["segment_length"] == pytest.approx(2.01168)
    assert displayed["posted_speed_limit"] == pytest.approx(72.42048)
    assert displayed["lane_width"] == pytest.approx(3.6576)
    assert displayed["roadside_lateral_clearance"] == pytest.approx(3.6576)
    assert multilane_ui_inputs_to_engine(displayed, template_inputs, "metric") == (
        template_inputs
    )


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
    assert display["capacity"]["value"] == result["outputs"]["capacity_pc_h_ln"]
    assert display["capacity"]["unit"] == "pc/h/ln"


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


def test_unit_or_template_switch_clears_multilane_form_and_result_state() -> None:
    state = {
        "manual_multilane_input_length_MLH-CH26-004-EB_metric": 2.0,
        "manual_multilane_result": {"outputs": {}},
        "manual_multilane_error": "old error",
        "manual_multilane_audit": {"unit_system": "metric"},
        "manual_multilane_template_context": ("MLH-CH26-004-EB", "metric"),
        "unrelated": "preserved",
    }

    clear_manual_multilane_state(state)

    assert state == {
        "manual_multilane_template_context": ("MLH-CH26-004-EB", "metric"),
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
