from copy import deepcopy
from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient

from hcmcalc.api.main import create_app
from hcmcalc.application.workflows import (
    FacilityWorkflow,
    MultilaneWorkflow,
    StaleResultError,
    export_current_workflow,
)
from hcmcalc.application.workflow_state import MetricAvailability
from hcmcalc.ui.manual_facility import run_manual_facility
from hcmcalc.ui.manual_multilane import (
    load_multilane_template,
    multilane_ui_inputs_to_engine,
    run_manual_multilane,
)
from hcmcalc.ui.units import MILES_TO_KILOMETERS


def multilane_inputs() -> dict:
    workflow = MultilaneWorkflow()
    return workflow.starting_values("MLH-CH26-004-EB", "imperial")["displayed_inputs"]


def facility_inputs() -> dict:
    workflow = FacilityWorkflow()
    return {"rows": workflow.starting_values("level_example_3", "imperial")["segments"]}


def test_multilane_validation_is_ready_without_running_engine() -> None:
    workflow = MultilaneWorkflow()
    response = workflow.validate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=multilane_inputs(),
    )
    assert response["valid"] is True
    assert response["ready"] is True
    assert response["calculation_state"]["presentation_state"] == "prerun"
    assert response["calculation_fingerprint"]


def test_multilane_calculation_preserves_qualified_result_and_audit() -> None:
    response = MultilaneWorkflow().calculate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=multilane_inputs(),
    )
    assert response["result"]["method"] == "hcm7_multilane_los"
    assert response["result"]["outputs"]["level_of_service"] == "C"
    assert response["result"]["outputs"]["density_pc_mi_ln"] == pytest.approx(18.0875420875)
    assert response["presentation"]["answer"]["value"] == "C"
    assert response["presentation"]["metrics"][0]["available"] is True
    assert response["audit"]["calculation_succeeded"] is True
    assert response["result"]["intermediate_values"]


def test_multilane_capacity_failure_marks_unavailable_metrics_as_not_predicted() -> None:
    values = multilane_inputs()
    values["demand_volume_veh_h"] = 5000.0
    response = MultilaneWorkflow().calculate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=values,
    )

    assert response["calculation_state"]["presentation_state"] == "capacity_failure"
    metrics = {item["key"]: item for item in response["presentation"]["metrics"]}
    for key in ("density", "speed_used_for_density"):
        assert metrics[key]["value"] is None
        assert metrics[key]["available"] is False
        assert metrics[key]["availability"] == MetricAvailability.NOT_PREDICTED.value
    assert metrics["adjusted_free_flow_speed"]["availability"] == MetricAvailability.CALCULATED.value
    assert metrics["demand_flow_rate"]["availability"] == MetricAvailability.CALCULATED.value


def test_multilane_application_and_api_match_qualified_adapter() -> None:
    template_id = "MLH-CH26-004-EB"
    unit_system = "imperial"
    displayed = multilane_inputs()
    normalized = multilane_ui_inputs_to_engine(
        displayed,
        load_multilane_template(template_id)["inputs"],
        unit_system,
    )
    qualified = asdict(run_manual_multilane(normalized))
    application = MultilaneWorkflow().calculate(
        template_id=template_id,
        unit_system=unit_system,
        displayed_inputs=displayed,
    )
    api = TestClient(create_app()).post(
        "/api/v1/analyses/multilane_segment/calculate",
        json={
            "template_id": template_id,
            "unit_system": unit_system,
            "displayed_inputs": displayed,
        },
    )
    assert api.status_code == 200
    assert {key: value for key, value in application["result"].items() if key != "result_contract_version"} == qualified
    assert {key: value for key, value in api.json()["result"].items() if key != "result_contract_version"} == qualified


def test_multilane_invalid_branch_is_explicit() -> None:
    values = multilane_inputs()
    values["ffs_source"] = "measured"
    values["free_flow_speed"] = None
    response = MultilaneWorkflow().validate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=values,
    )
    assert response["valid"] is False
    assert response["validation_status"] == "invalid_input"
    assert "free_flow_speed" in response["errors"][0]["message"]


@pytest.mark.parametrize(
    ("changes", "expected_pce_source"),
    [
        ({"heavy_vehicle_adjustment_method": "general_terrain", "terrain_type": "level"}, "internal_hcm7_exhibit_12_25"),
        ({"heavy_vehicle_adjustment_method": "specific_grade", "grade_percent": -3.5}, "internal_hcm7_exhibit_12_26_12_28"),
        ({"heavy_vehicle_adjustment_method": "external_pce", "passenger_car_equivalent": 2.5}, "external_user_supplied_override"),
    ],
)
def test_multilane_heavy_vehicle_branches_remain_explicit(
    changes: dict[str, object], expected_pce_source: str
) -> None:
    values = multilane_inputs()
    values.update(changes)
    response = MultilaneWorkflow().calculate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=values,
    )
    assert response["result"]["outputs"]["pce_source"] == expected_pce_source


def test_multilane_measured_and_divided_median_branches_are_calculable() -> None:
    measured = multilane_inputs()
    measured.update({"ffs_source": "measured", "free_flow_speed": 55.0})
    measured_result = MultilaneWorkflow().calculate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=measured,
    )
    assert measured_result["result"]["outputs"]["ffs_source"] == "measured"

    divided = multilane_inputs()
    divided.update({"median_type": "divided", "left_side_lateral_clearance": 4.0})
    divided_result = MultilaneWorkflow().calculate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=divided,
    )
    assert divided_result["normalized_inputs"]["median_type"] == "divided"


def test_facility_template_locks_are_enforced_before_calculation() -> None:
    values = facility_inputs()
    values["rows"][0]["terrain_type"] = "mountainous"
    response = FacilityWorkflow().validate(
        template_id="level_example_3",
        unit_system="imperial",
        displayed_inputs=values,
    )
    assert response["valid"] is False
    assert response["validation_status"] == "unsupported_scope"
    assert "locked" in response["errors"][0]["message"]


def test_facility_calculation_exposes_facility_and_segment_evidence() -> None:
    response = FacilityWorkflow().calculate(
        template_id="level_example_3",
        unit_system="imperial",
        displayed_inputs=facility_inputs(),
    )
    assert response["result"]["outputs"]["facility_level_of_service"] == "C"
    assert response["result"]["outputs"]["facility_follower_density_followers_mi_ln"] == pytest.approx(7.3, abs=0.1)
    assert len(response["presentation"]["segments"]) == 5
    assert response["presentation"]["capacity"]["critical_segment_id"] == response["result"]["outputs"]["critical_segment_id"]
    assert any(item["code"] == "facility_length_weighted" for item in response["presentation"]["interpretations"])


def test_facility_metric_presentation_converts_aggregate_speed_and_density_only() -> None:
    workflow = FacilityWorkflow()
    imperial_rows = workflow.starting_values("level_example_3", "imperial")["segments"]
    metric_rows = workflow.starting_values("level_example_3", "metric")["segments"]
    imperial = workflow.calculate(
        template_id="level_example_3",
        unit_system="imperial",
        displayed_inputs={"rows": imperial_rows},
    )
    metric = workflow.calculate(
        template_id="level_example_3",
        unit_system="metric",
        displayed_inputs={"rows": metric_rows},
    )

    imperial_outputs = imperial["result"]["outputs"]
    metric_outputs = metric["result"]["outputs"]
    assert metric_outputs["facility_average_speed_mph"] == pytest.approx(
        imperial_outputs["facility_average_speed_mph"]
    )
    assert metric_outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        imperial_outputs["facility_follower_density_followers_mi_ln"]
    )
    imperial_metrics = {item["key"]: item for item in imperial["presentation"]["metrics"]}
    metric_metrics = {item["key"]: item for item in metric["presentation"]["metrics"]}
    assert metric_metrics["facility_average_speed"]["value"] == pytest.approx(
        imperial_metrics["facility_average_speed"]["value"] * MILES_TO_KILOMETERS
    )
    assert metric_metrics["facility_average_speed"]["unit"] == "km/h"
    assert metric_metrics["facility_density"]["value"] == pytest.approx(
        imperial_metrics["facility_density"]["value"] / MILES_TO_KILOMETERS
    )
    assert metric_metrics["facility_density"]["unit"] == "fol/km/ln"
    for imperial_segment, metric_segment in zip(
        imperial["presentation"]["segments"],
        metric["presentation"]["segments"],
        strict=True,
    ):
        assert metric_segment["average_speed"] == pytest.approx(
            imperial_segment["average_speed"] * MILES_TO_KILOMETERS
        )
        assert metric_segment["follower_density"] == pytest.approx(
            imperial_segment["follower_density"] / MILES_TO_KILOMETERS
        )


def test_facility_application_and_api_match_qualified_adapter() -> None:
    template_id = "mountainous_example_4"
    unit_system = "metric"
    rows = FacilityWorkflow().starting_values(template_id, unit_system)["segments"]
    qualified = asdict(run_manual_facility(template_id, rows, unit_system))
    application = FacilityWorkflow().calculate(
        template_id=template_id,
        unit_system=unit_system,
        displayed_inputs={"rows": rows},
    )
    api = TestClient(create_app()).post(
        "/api/v1/analyses/two_lane_facility/calculate",
        json={
            "template_id": template_id,
            "unit_system": unit_system,
            "displayed_inputs": {"rows": rows},
        },
    )
    assert api.status_code == 200
    assert {key: value for key, value in application["result"].items() if key != "result_contract_version"} == qualified
    assert {key: value for key, value in api.json()["result"].items() if key != "result_contract_version"} == qualified


def test_export_uses_supplied_result_without_rerunning(monkeypatch: pytest.MonkeyPatch) -> None:
    workflow = MultilaneWorkflow()
    response = workflow.calculate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=multilane_inputs(),
    )

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("export must not rerun the HCM method")

    monkeypatch.setattr("hcmcalc.application.workflows.run_manual_multilane", fail_if_called)
    exported = export_current_workflow(
        "multilane_segment",
        template_id=response["template_id"],
        unit_system=response["unit_system"],
        displayed_inputs=response["displayed_inputs"],
        calculation_fingerprint=response["calculation_fingerprint"],
        input_snapshot_fingerprint=response["input_snapshot_fingerprint"],
        result=response["result"],
        export_format="markdown",
    )
    assert exported["recalculated"] is False
    assert "Summary Result" in (exported["content"] or "")


def test_export_rejects_displayed_input_snapshot_mismatch() -> None:
    response = MultilaneWorkflow().calculate(
        template_id="MLH-CH26-004-EB",
        unit_system="imperial",
        displayed_inputs=multilane_inputs(),
    )
    changed = deepcopy(response["displayed_inputs"])
    changed.pop("pce_mode")
    with pytest.raises(StaleResultError, match="not current"):
        export_current_workflow(
            "multilane_segment",
            template_id=response["template_id"],
            unit_system=response["unit_system"],
            displayed_inputs=changed,
            calculation_fingerprint=response["calculation_fingerprint"],
            input_snapshot_fingerprint=response["input_snapshot_fingerprint"],
            result=response["result"],
            export_format="markdown",
        )
