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


ALL_DELIVERED_METHODS = (
    "two_lane_segment",
    "two_lane_facility",
    "multilane_segment",
    "basic_freeway_segment",
    "weaving_segment",
    "merge_segment",
    "diverge_segment",
)


def test_all_delivered_workflows_identify_a_default_and_starter_semantics() -> None:
    expected_defaults = {
        "two_lane_segment": "TLH-CH15-001",
        "two_lane_facility": "level_example_3",
        "multilane_segment": "MLH-CH26-004-EB",
        "basic_freeway_segment": "BF-CH26-001",
        "weaving_segment": "WVG-CH27-001",
        "merge_segment": "chapter_28_example_1_merge",
        "diverge_segment": "chapter_28_example_3_diverge_component",
    }
    for method_id in ALL_DELIVERED_METHODS:
        templates = workflow_for_method(method_id).templates()
        assert templates["default_template_id"] == expected_defaults[method_id]
        default = next(item for item in templates["templates"] if item["template_id"] == templates["default_template_id"])
        assert default["starter_kind"] in {"example", "facility_template"}


def test_phase3_asset_metadata_reuses_qualified_package_assets() -> None:
    assert workflow_for_method("two_lane_segment").templates()["branches"]["engineering_assets"]["variants"]
    weaving_assets = workflow_for_method("weaving_segment").templates()["branches"]["engineering_assets"]["variants"]
    assert {item["asset_path"] for item in weaving_assets} == {
        "weaving/one_sided_weave.png",
        "weaving/two_sided_weave.png",
    }
    assert workflow_for_method("merge_segment").templates()["branches"]["engineering_assets"]["asset_path"].endswith("merge_right_on_ramp.svg")
    assert workflow_for_method("diverge_segment").templates()["branches"]["engineering_assets"]["asset_path"].endswith("diverge_right_off_ramp.svg")


def test_multilane_blank_access_density_is_explicit_zero_but_clear_is_invalid() -> None:
    workflow = workflow_for_method("multilane_segment")
    blank = workflow.starting_values("blank_custom", "metric")
    assert blank["displayed_inputs"]["access_point_density"] == 0.0
    starting = workflow.starting_values("MLH-CH26-004-EB", "metric")
    cleared = dict(starting["displayed_inputs"])
    cleared["access_point_density"] = None
    validation = workflow.validate(
        template_id="MLH-CH26-004-EB",
        unit_system="metric",
        displayed_inputs=cleared,
    )
    assert validation["valid"] is False
    assert any(issue["field"] == "access_point_density" for issue in validation["errors"])


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


@pytest.mark.parametrize(
    "method_id, updates, expected_state, max_exceeded, capacity_failure",
    (
        ("merge_segment", {}, "valid_current_result", False, False),
        (
            "merge_segment",
            {
                "freeway_lanes": 2,
                "freeway_demand_veh_h": 3600.0,
                "ramp_demand_veh_h": 600.0,
                "freeway_peak_hour_factor": 0.95,
                "ramp_peak_hour_factor": 0.95,
                "free_flow_speed": 65.0,
                "ramp_ffs": 40.0,
                "auxiliary_lane_length": 600.0,
            },
            "valid_current_result_with_warning",
            True,
            False,
        ),
        ("merge_segment", {"freeway_demand_veh_h": 8000.0}, "capacity_failure", True, True),
        ("diverge_segment", {}, "valid_current_result", False, False),
        (
            "diverge_segment",
            {
                "freeway_lanes": 2,
                "freeway_demand_veh_h": 4000.0,
                "ramp_demand_veh_h": 200.0,
                "freeway_peak_hour_factor": 0.95,
                "ramp_peak_hour_factor": 0.95,
                "free_flow_speed": 65.0,
                "ramp_ffs": 40.0,
                "auxiliary_lane_length": 600.0,
            },
            "valid_current_result_with_warning",
            True,
            False,
        ),
        ("diverge_segment", {"ramp_demand_veh_h": 2300.0}, "capacity_failure", True, True),
    ),
)
def test_ramp_presentation_state_preserves_qualified_warning_taxonomy(
    method_id: str,
    updates: dict[str, object],
    expected_state: str,
    max_exceeded: bool,
    capacity_failure: bool,
) -> None:
    workflow = workflow_for_method(method_id)
    template_id = workflow.templates()["default_template_id"]
    displayed = workflow.starting_values(template_id, "imperial")["displayed_inputs"]
    displayed.update(updates)

    calculated = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=displayed,
    )
    outputs = calculated["result"]["outputs"]

    assert calculated["calculation_state"]["presentation_state"] == expected_state
    assert outputs["maximum_desirable_influence_flow_exceeded"] is max_exceeded
    assert calculated["presentation"]["capacity"]["failure"] is capacity_failure
    assert calculated["result"]["warnings"]
    assert calculated["calculation_state"]["warnings"] == calculated["result"]["warnings"]
    assert calculated["presentation"]["evidence"]["warnings"] == calculated["result"]["warnings"]
    if expected_state == "valid_current_result_with_warning":
        assert "Maximum desirable" in calculated["presentation"]["warning"]
        assert calculated["presentation"]["answer"]["value"] != "F"
        assert all(metric["availability"] == "calculated" for metric in calculated["presentation"]["metrics"])
    else:
        assert calculated["presentation"]["warning"] is None or expected_state == "capacity_failure"


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
