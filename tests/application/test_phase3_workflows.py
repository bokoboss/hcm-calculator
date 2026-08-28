from copy import deepcopy

import pytest

import hcmcalc.application.phase3_workflows as phase3_services
from hcmcalc.application.workflows import export_current_workflow, workflow_for_method


PHASE3_CASES = (
    ("two_lane_segment", "TLH-CH15-001", "hcm7_ch15_two_lane_motorized", "D"),
    ("basic_freeway_segment", "BF-CH26-001", "hcm7_basic_freeway_segment", "C"),
    ("weaving_segment", "WVG-CH27-001", "hcm7_v70_freeway_weaving_segment", "C"),
    ("merge_segment", "chapter_28_example_1_merge", "hcm7_v70_freeway_merge_segment", "D"),
    ("diverge_segment", "chapter_28_example_3_diverge_component", "hcm7_v70_freeway_diverge_segment", "D"),
)


@pytest.mark.parametrize("method_id, template_id, engine_method, expected_los", PHASE3_CASES)
def test_phase3_templates_validate_and_calculate_through_existing_engines(
    method_id: str,
    template_id: str,
    engine_method: str,
    expected_los: str,
) -> None:
    workflow = workflow_for_method(method_id)
    templates = workflow.templates()
    assert templates["groups"]
    assert any(item["template_id"] == template_id for item in templates["templates"])

    starting = workflow.starting_values(template_id, "imperial")
    validation = workflow.validate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=starting["displayed_inputs"],
    )
    assert validation["valid"] is True

    calculated = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=starting["displayed_inputs"],
    )
    assert calculated["result"]["method"] == engine_method
    assert calculated["presentation"]["answer"]["value"] == expected_los
    assert calculated["calculation_state"]["has_result"] is True
    assert calculated["audit"]


@pytest.mark.parametrize(
    "method_id, engine_name",
    (
        ("two_lane_segment", "run_manual_single_segment"),
        ("basic_freeway_segment", "run_manual_freeway"),
        ("weaving_segment", "run_manual_weaving"),
        ("merge_segment", "run_manual_ramp"),
        ("diverge_segment", "run_manual_ramp"),
    ),
)
def test_phase3_validation_never_executes_an_hcm_engine(
    monkeypatch: pytest.MonkeyPatch,
    method_id: str,
    engine_name: str,
) -> None:
    workflow = workflow_for_method(method_id)
    template_id = workflow.templates()["templates"][0]["template_id"]
    starting = workflow.starting_values(template_id, "imperial")

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"validation called {engine_name}")

    monkeypatch.setattr(phase3_services, engine_name, fail_if_called)
    validation = workflow.validate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=starting["displayed_inputs"],
    )
    assert validation["valid"] is True


def test_weaving_handoff_and_capacity_failure_remain_distinct() -> None:
    workflow = workflow_for_method("weaving_segment")
    starting = workflow.starting_values("WVG-CH27-001", "imperial")["displayed_inputs"]

    handoff_inputs = deepcopy(starting)
    handoff_inputs["segment_length"] = 5000.0
    handoff = workflow.calculate(
        template_id="WVG-CH27-001",
        unit_system="imperial",
        displayed_inputs=handoff_inputs,
    )
    assert handoff["calculation_state"]["presentation_state"] == "hcm_stopping_or_handoff"
    assert handoff["presentation"]["capacity"]["failure"] is False
    assert handoff["presentation"]["answer"]["available"] is False
    assert all(metric["availability"] == "not_predicted" for metric in handoff["presentation"]["metrics"][:-1])

    capacity_inputs = deepcopy(starting)
    for key in ("volume_ff_veh_h", "volume_fr_veh_h", "volume_rf_veh_h", "volume_rr_veh_h"):
        capacity_inputs[key] = 10000.0
    capacity = workflow.calculate(
        template_id="WVG-CH27-001",
        unit_system="imperial",
        displayed_inputs=capacity_inputs,
    )
    assert capacity["calculation_state"]["presentation_state"] == "capacity_failure"
    assert capacity["presentation"]["capacity"]["failure"] is True
    assert capacity["presentation"]["answer"]["value"] == "F"
    assert capacity["presentation"]["metrics"][0]["availability"] == "not_predicted"


@pytest.mark.parametrize("method_id, template_id", [(case[0], case[1]) for case in PHASE3_CASES])
def test_phase3_exports_use_supplied_result_without_rerunning(
    monkeypatch: pytest.MonkeyPatch,
    method_id: str,
    template_id: str,
) -> None:
    workflow = workflow_for_method(method_id)
    starting = workflow.starting_values(template_id, "imperial")
    snapshot = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=starting["displayed_inputs"],
    )

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("export must not rerun the HCM engine")

    for engine_name in ("run_manual_single_segment", "run_manual_freeway", "run_manual_weaving", "run_manual_ramp"):
        monkeypatch.setattr(phase3_services, engine_name, fail_if_called)

    exported = export_current_workflow(
        method_id,
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=starting["displayed_inputs"],
        calculation_fingerprint=snapshot["calculation_fingerprint"],
        input_snapshot_fingerprint=snapshot["input_snapshot_fingerprint"],
        result=snapshot["result"],
        export_format="markdown",
    )
    assert exported["recalculated"] is False
    assert exported["content"]
