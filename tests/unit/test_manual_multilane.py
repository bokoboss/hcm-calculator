from copy import deepcopy

import pytest

from hcmcalc.cli import result_to_dict
from hcmcalc.core import UnsupportedScopeError
from hcmcalc.ui.manual_multilane import (
    build_manual_multilane_audit_record,
    load_multilane_template,
    multilane_template_options,
    run_manual_multilane,
)


def test_multilane_template_options_expose_only_example_4_directions() -> None:
    assert multilane_template_options() == {
        "MLH-CH26-004-EB": "Example 4 — Eastbound direction",
        "MLH-CH26-004-WB": "Example 4 — Westbound direction",
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
