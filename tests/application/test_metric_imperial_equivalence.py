from collections.abc import Mapping
from copy import deepcopy
from typing import Any

import pytest

from hcmcalc.application.project import (
    load_project,
    project_to_json,
    save_analysis_to_project,
)
from hcmcalc.application.workflows import (
    normalized_workflow_inputs,
    workflow_for_method,
)
from hcmcalc.freeway.method import breakpoint_flow_rate
from hcmcalc.ui.units import FEET_TO_METERS, MILES_TO_KILOMETERS


ENGINE_ARITHMETIC_ABS_TOLERANCE = 1e-12

WORKFLOW_CASES = (
    ("two_lane_segment", "TLH-CH15-002"),
    ("two_lane_facility", "mountainous_example_4"),
    ("multilane_segment", "MLH-CH26-004-EB"),
    ("basic_freeway_segment", "BF-CH26-001"),
    ("weaving_segment", "WVG-CH27-001"),
    ("weaving_segment", "WVG-CH27-003"),
    ("merge_segment", "chapter_28_example_1_merge"),
    ("diverge_segment", "chapter_28_example_3_diverge_component"),
)


def _displayed_inputs(
    method_id: str, template_id: str, unit_system: str
) -> dict[str, Any]:
    starting = workflow_for_method(method_id).starting_values(
        template_id, unit_system
    )
    if method_id == "two_lane_facility":
        return {"rows": starting["segments"]}
    return starting["displayed_inputs"]


def _assert_equivalent(left: Any, right: Any, path: str = "value") -> None:
    if left is None or right is None:
        assert left is right, path
        return
    if isinstance(left, bool) or isinstance(right, bool):
        assert left is right, path
        return
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        assert float(left) == pytest.approx(
            float(right), rel=0.0, abs=ENGINE_ARITHMETIC_ABS_TOLERANCE
        ), path
        return
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        assert set(left) == set(right), path
        for key in left:
            _assert_equivalent(left[key], right[key], f"{path}.{key}")
        return
    if isinstance(left, list) and isinstance(right, list):
        assert len(left) == len(right), path
        for index, (left_item, right_item) in enumerate(
            zip(left, right, strict=True)
        ):
            _assert_equivalent(
                left_item, right_item, f"{path}[{index}]"
            )
        return
    assert left == right, path


def _assert_pair_semantics(
    metric: dict[str, Any], imperial: dict[str, Any]
) -> None:
    _assert_equivalent(
        metric["normalized_inputs"],
        imperial["normalized_inputs"],
        "normalized",
    )
    _assert_equivalent(metric["result"], imperial["result"], "result")
    assert (
        metric["calculation_state"]["presentation_state"]
        == imperial["calculation_state"]["presentation_state"]
    )
    assert (
        metric["presentation"]["answer"]["available"]
        is imperial["presentation"]["answer"]["available"]
    )
    assert (
        metric["presentation"]["capacity"]["failure"]
        is imperial["presentation"]["capacity"]["failure"]
    )


@pytest.mark.parametrize("method_id, template_id", WORKFLOW_CASES)
def test_metric_imperial_equivalence_through_application_workflows(
    method_id: str, template_id: str
) -> None:
    workflow = workflow_for_method(method_id)
    metric = workflow.calculate(
        template_id=template_id,
        unit_system="metric",
        displayed_inputs=_displayed_inputs(
            method_id, template_id, "metric"
        ),
    )
    imperial = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=_displayed_inputs(
            method_id, template_id, "imperial"
        ),
    )

    _assert_pair_semantics(metric, imperial)

    metric_outputs = metric["result"]["outputs"]
    imperial_outputs = imperial["result"]["outputs"]
    for key in (
        "support_status",
        "scope_status",
        "capacity_status",
        "capacity_check",
        "level_of_service",
        "demand_exceeds_capacity",
    ):
        if key in imperial_outputs:
            assert metric_outputs[key] == imperial_outputs[key]

    if method_id == "two_lane_facility":
        for metric_row, imperial_row in zip(
            metric["displayed_inputs"]["rows"],
            imperial["displayed_inputs"]["rows"],
            strict=True,
        ):
            for key in (
                "segment_id",
                "segment_type",
                "passing_lane",
                "passing_lane_role",
                "downstream_affected",
            ):
                assert metric_row[key] == imperial_row[key]
    elif method_id == "weaving_segment":
        metric_geometry = metric["normalized_inputs"]["geometry"]
        imperial_geometry = imperial["normalized_inputs"]["geometry"]
        for key in ("entry_side", "exit_side", "option_lane_status"):
            assert metric_geometry[key] == imperial_geometry[key]
    elif method_id in {"merge_segment", "diverge_segment"}:
        assert metric["normalized_inputs"]["method_version"] == "hcm_7_0"
        assert imperial["normalized_inputs"]["method_version"] == "hcm_7_0"
        assert metric["normalized_inputs"]["ramp_side"] == "right"
        assert imperial["normalized_inputs"]["ramp_side"] == "right"


def test_metric_normalization_preserves_accepted_canonicalization() -> None:
    multilane = _displayed_inputs(
        "multilane_segment", "MLH-CH26-004-EB", "metric"
    )
    multilane.update(
        {
            "segment_length": 1.23456789,
            "posted_speed_limit": 48.7654321,
            "lane_width": 3.3333333,
            "roadside_lateral_clearance": 1.1111111,
            "access_point_density": 4.3210987,
            "median_type": "divided",
            "left_side_lateral_clearance": 1.5555555,
        }
    )
    multilane_normalized = normalized_workflow_inputs(
        "multilane_segment",
        template_id="MLH-CH26-004-EB",
        unit_system="metric",
        displayed_inputs=multilane,
    )
    for key, raw_value in {
        "segment_length_ft": (
            multilane["segment_length"] * 1000.0 / FEET_TO_METERS
        ),
        "posted_speed_limit_mph": (
            multilane["posted_speed_limit"] / MILES_TO_KILOMETERS
        ),
        "lane_width_ft": multilane["lane_width"] / FEET_TO_METERS,
        "roadside_lateral_clearance_ft": (
            multilane["roadside_lateral_clearance"] / FEET_TO_METERS
        ),
        "access_point_density_per_mi": (
            multilane["access_point_density"] * MILES_TO_KILOMETERS
        ),
        "left_side_lateral_clearance_ft": (
            multilane["left_side_lateral_clearance"] / FEET_TO_METERS
        ),
    }.items():
        assert multilane_normalized[key] == round(raw_value, 10)

    freeway = _displayed_inputs(
        "basic_freeway_segment", "BF-CH26-001", "metric"
    )
    freeway.update(
        {
            "segment_length": 1.23456789,
            "base_free_flow_speed": 73.1234567,
            "lane_width": 3.3333333,
            "right_side_lateral_clearance": 0.9876543,
            "total_ramp_density": 2.3210987,
        }
    )
    freeway_normalized = normalized_workflow_inputs(
        "basic_freeway_segment",
        template_id="BF-CH26-001",
        unit_system="metric",
        displayed_inputs=freeway,
    )
    for key, raw_value in {
        "segment_length_mi": (
            freeway["segment_length"] / MILES_TO_KILOMETERS
        ),
        "base_free_flow_speed_mph": (
            freeway["base_free_flow_speed"] / MILES_TO_KILOMETERS
        ),
        "lane_width_ft": freeway["lane_width"] / FEET_TO_METERS,
        "right_side_lateral_clearance_ft": (
            freeway["right_side_lateral_clearance"] / FEET_TO_METERS
        ),
        "total_ramp_density_per_mi": (
            freeway["total_ramp_density"] * MILES_TO_KILOMETERS
        ),
    }.items():
        assert freeway_normalized[key] == round(raw_value, 10)


@pytest.mark.parametrize(
    "method_id, template_id, display_updates, expected_native",
    (
        (
            "multilane_segment",
            "MLH-CH26-004-EB",
            {
                "lane_width": 3.5,
                "roadside_lateral_clearance": 1.8,
            },
            {
                "lane_width_ft": round(3.5 / FEET_TO_METERS, 10),
                "roadside_lateral_clearance_ft": round(
                    1.8 / FEET_TO_METERS, 10
                ),
            },
        ),
        (
            "basic_freeway_segment",
            "BF-CH26-001",
            {
                "lane_width": 3.5,
                "right_side_lateral_clearance": 1.8,
            },
            {
                "lane_width_ft": round(3.5 / FEET_TO_METERS, 10),
                "right_side_lateral_clearance_ft": round(
                    1.8 / FEET_TO_METERS, 10
                ),
            },
        ),
    ),
)
def test_prechange_metric_project_v2_remains_current(
    method_id: str,
    template_id: str,
    display_updates: dict[str, float],
    expected_native: dict[str, float],
) -> None:
    workflow = workflow_for_method(method_id)
    displayed = _displayed_inputs(method_id, template_id, "metric")
    displayed.update(display_updates)
    snapshot = workflow.calculate(
        template_id=template_id,
        unit_system="metric",
        displayed_inputs=displayed,
    )

    for key, expected in expected_native.items():
        assert snapshot["normalized_inputs"][key] == expected

    project = save_analysis_to_project(
        snapshot, project_name=f"{method_id} metric compatibility"
    )
    original = project["analyses"][0]["scenarios"][0]
    loaded = load_project(project_to_json(project))
    scenario = loaded["analyses"][0]["scenarios"][0]

    assert scenario["result_status"] == "current"
    assert scenario["result"] is not None
    assert (
        scenario["calculation_fingerprint"]
        == original["calculation_fingerprint"]
    )
    assert (
        scenario["result"]["calculation_fingerprint"]
        == original["result"]["calculation_fingerprint"]
    )
    for key, expected in expected_native.items():
        assert scenario["normalized_inputs"][key] == expected


def test_two_lane_metric_imperial_pair_preserves_exhibit_length_boundary() -> None:
    method_id = "two_lane_segment"
    template_id = "TLH-CH15-001"
    imperial_inputs = _displayed_inputs(
        method_id, template_id, "imperial"
    )
    metric_inputs = _displayed_inputs(method_id, template_id, "metric")
    imperial_inputs["segment_length"] = 0.25
    metric_inputs["segment_length"] = 0.25 * MILES_TO_KILOMETERS

    workflow = workflow_for_method(method_id)
    imperial = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=imperial_inputs,
    )
    metric = workflow.calculate(
        template_id=template_id,
        unit_system="metric",
        displayed_inputs=metric_inputs,
    )
    _assert_pair_semantics(metric, imperial)
    assert (
        metric["result"]["outputs"]["segment_length_applicability_status"]
        == "within_exhibit_15_10"
    )
    assert (
        imperial["result"]["outputs"]["segment_length_applicability_status"]
        == "within_exhibit_15_10"
    )


def _near_capacity_pair(
    method_id: str,
    template_id: str,
    metric_updates: dict[str, Any],
    imperial_updates: dict[str, Any],
    ratio: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    workflow = workflow_for_method(method_id)
    imperial_inputs = _displayed_inputs(
        method_id, template_id, "imperial"
    )
    metric_inputs = _displayed_inputs(method_id, template_id, "metric")
    imperial_inputs.update(imperial_updates)
    metric_inputs.update(metric_updates)
    baseline = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=imperial_inputs,
    )
    outputs = baseline["result"]["outputs"]
    capacity = outputs.get(
        "adjusted_capacity_pc_h_ln", outputs.get("capacity_pc_h_ln")
    )
    flow_per_demand = (
        outputs["demand_flow_rate_pc_h_ln"]
        / imperial_inputs["demand_volume_veh_h"]
    )
    demand = capacity * ratio / flow_per_demand
    imperial_inputs["demand_volume_veh_h"] = demand
    metric_inputs["demand_volume_veh_h"] = demand
    return (
        workflow.calculate(
            template_id=template_id,
            unit_system="metric",
            displayed_inputs=metric_inputs,
        ),
        workflow.calculate(
            template_id=template_id,
            unit_system="imperial",
            displayed_inputs=imperial_inputs,
        ),
    )


@pytest.mark.parametrize(
    "ratio, capacity_failure", [(0.999, False), (1.001, True)]
)
def test_multilane_near_capacity_pair_preserves_left_side_hcm_source(
    ratio: float, capacity_failure: bool
) -> None:
    metric, imperial = _near_capacity_pair(
        "multilane_segment",
        "MLH-CH26-004-EB",
        {
            "median_type": "divided",
            "left_side_lateral_clearance": 6.0 * FEET_TO_METERS,
        },
        {
            "median_type": "divided",
            "left_side_lateral_clearance": 6.0,
        },
        ratio,
    )
    _assert_pair_semantics(metric, imperial)
    assert metric["normalized_inputs"][
        "left_side_lateral_clearance_ft"
    ] == pytest.approx(6.0)
    assert imperial["normalized_inputs"][
        "left_side_lateral_clearance_ft"
    ] == pytest.approx(6.0)
    for response in (metric, imperial):
        outputs = response["result"]["outputs"]
        assert outputs["capacity_status"] == (
            "demand_exceeds_capacity"
            if capacity_failure
            else "within_capacity"
        )
        assert outputs["demand_exceeds_capacity"] is capacity_failure
        assert (outputs["mean_speed_mph"] is None) is capacity_failure
        assert (outputs["density_pc_mi_ln"] is None) is capacity_failure


@pytest.mark.parametrize(
    "ratio, capacity_failure", [(0.999, False), (1.001, True)]
)
def test_basic_freeway_saf_caf_and_near_capacity_pair(
    ratio: float, capacity_failure: bool
) -> None:
    metric, imperial = _near_capacity_pair(
        "basic_freeway_segment",
        "BF-CH26-001",
        {
            "ffs_source": "measured",
            "free_flow_speed": 65.0 * MILES_TO_KILOMETERS,
            "driver_population_category": "mostly_unfamiliar",
        },
        {
            "ffs_source": "measured",
            "free_flow_speed": 65.0,
            "driver_population_category": "mostly_unfamiliar",
        },
        ratio,
    )
    _assert_pair_semantics(metric, imperial)
    for response in (metric, imperial):
        outputs = response["result"]["outputs"]
        assert outputs["speed_adjustment_factor"] == pytest.approx(0.913)
        assert outputs["capacity_adjustment_factor"] == pytest.approx(0.898)
        assert outputs["capacity_pc_h_ln"] == pytest.approx(2350.0)
        assert outputs["adjusted_capacity_pc_h_ln"] == pytest.approx(
            2350.0 * 0.898
        )
        assert outputs["breakpoint_flow_rate_pc_h_ln"] == pytest.approx(
            breakpoint_flow_rate(
                outputs["adjusted_free_flow_speed_mph"],
                outputs["capacity_adjustment_factor"],
            )
        )
        assert outputs["demand_exceeds_capacity"] is capacity_failure
        assert (outputs["mean_speed_mph"] is None) is capacity_failure
        assert (outputs["density_pc_mi_ln"] is None) is capacity_failure


def test_weaving_lmax_handoff_pair_preserves_null_and_side_semantics() -> None:
    method_id = "weaving_segment"
    template_id = "WVG-CH27-001"
    workflow = workflow_for_method(method_id)
    imperial_inputs = _displayed_inputs(
        method_id, template_id, "imperial"
    )
    baseline = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=imperial_inputs,
    )
    handoff_length = (
        baseline["result"]["outputs"]["maximum_weaving_length_ft"] + 1.0
    )
    metric_inputs = _displayed_inputs(method_id, template_id, "metric")
    imperial_inputs = deepcopy(imperial_inputs)
    imperial_inputs["segment_length"] = handoff_length
    metric_inputs["segment_length"] = handoff_length * FEET_TO_METERS

    metric = workflow.calculate(
        template_id=template_id,
        unit_system="metric",
        displayed_inputs=metric_inputs,
    )
    imperial = workflow.calculate(
        template_id=template_id,
        unit_system="imperial",
        displayed_inputs=imperial_inputs,
    )
    _assert_pair_semantics(metric, imperial)
    for response in (metric, imperial):
        assert (
            response["result"]["outputs"]["support_status"]
            == "hcm_handoff_required"
        )
        assert (
            response["result"]["outputs"]["capacity_status"]
            == "not_evaluated_after_handoff"
        )
        assert response["result"]["outputs"]["level_of_service"] is None
        assert (
            response["calculation_state"]["presentation_state"]
            == "hcm_stopping_or_handoff"
        )
        assert response["presentation"]["answer"]["available"] is False
        assert response["presentation"]["capacity"]["failure"] is False
