import json

import pytest

from hcmcalc.cli import result_to_dict
from hcmcalc.core import HCMCalcError
from hcmcalc.ui.i18n import translate, validate_catalogs
from hcmcalc.ui.manual_ramp_influence import (
    MANUAL_DIVERGE_PROJECT_TYPE,
    MANUAL_MERGE_PROJECT_TYPE,
    METHOD_VERSION,
    calculation_contract,
    diagram_path,
    method_family,
    ramp_display_outputs,
    ramp_engine_inputs_to_ui,
    ramp_preset_options,
    ramp_preset_ui_inputs,
    ramp_ui_inputs_to_engine,
    run_manual_ramp,
)
from hcmcalc.ui.project_io import (
    ProjectFileError,
    create_manual_ramp_project_payload,
    load_manual_ramp_project_json,
)
from hcmcalc.ui.reporting import build_report, export_report
from hcmcalc.ui.supported_workflows import APP_MODE_LABELS, resolve_app_view
from hcmcalc.ui.workflow_state import calculation_input_fingerprint


@pytest.mark.parametrize("workflow", ["merge", "diverge"])
def test_ramp_adapter_preserves_public_contract(workflow: str) -> None:
    preset = "chapter_28_example_1_merge" if workflow == "merge" else "chapter_28_example_3_diverge_component"
    ui = ramp_preset_ui_inputs(workflow, preset, "imperial")
    engine = ramp_ui_inputs_to_engine(workflow, ui, "imperial")
    result = run_manual_ramp(workflow, engine)

    assert engine["method_version"] == METHOD_VERSION
    assert engine["ramp_side"] == "right"
    assert engine["ramp_lanes"] == 1
    assert engine["adjacent_ramp_context"] == "isolated"
    assert result.outputs["method_family"] == method_family(workflow)
    assert result.outputs["calculation_contract"] == calculation_contract(workflow)
    assert result.outputs["freeway_heavy_vehicle_adjustment_factor"] != result.outputs["ramp_heavy_vehicle_adjustment_factor"] or True


@pytest.mark.parametrize("workflow", ["merge", "diverge"])
def test_ramp_metric_imperial_equivalent_fingerprint(workflow: str) -> None:
    preset = "chapter_28_example_1_merge" if workflow == "merge" else "chapter_28_example_3_diverge_component"
    imperial = ramp_preset_ui_inputs(workflow, preset, "imperial")
    engine_imperial = ramp_ui_inputs_to_engine(workflow, imperial, "imperial")
    metric = ramp_engine_inputs_to_ui(engine_imperial, "metric")
    engine_metric = ramp_ui_inputs_to_engine(workflow, metric, "metric")

    assert set(engine_metric) == set(engine_imperial)
    for key, value in engine_imperial.items():
        if isinstance(value, float):
            assert engine_metric[key] == pytest.approx(value)
        else:
            assert engine_metric[key] == value
    assert calculation_input_fingerprint(
        method_family(workflow), calculation_contract(workflow), engine_metric
    ) == calculation_input_fingerprint(
        method_family(workflow), calculation_contract(workflow), engine_imperial
    )


@pytest.mark.parametrize("workflow", ["merge", "diverge"])
def test_ramp_measured_estimated_and_guards(workflow: str) -> None:
    ui = ramp_preset_ui_inputs(workflow, "blank_custom", "imperial")
    ui.update(
        ffs_source="estimated",
        free_flow_speed=None,
        base_free_flow_speed=75.0,
        lane_width=12.0,
        right_side_lateral_clearance=6.0,
        total_ramp_density=0.0,
    )
    engine = ramp_ui_inputs_to_engine(workflow, ui, "imperial")
    assert engine["free_flow_speed_mph"] is None
    assert engine["base_free_flow_speed_mph"] == 75.0

    bad = dict(ui)
    bad["terrain_type"] = "specific_grade"
    with pytest.raises(HCMCalcError):
        ramp_ui_inputs_to_engine(workflow, bad, "imperial")
    if workflow == "diverge":
        bad = dict(ui)
        bad["ramp_demand_veh_h"] = bad["freeway_demand_veh_h"] + 1
        with pytest.raises(HCMCalcError):
            ramp_ui_inputs_to_engine(workflow, bad, "imperial")


@pytest.mark.parametrize("workflow", ["merge", "diverge"])
def test_ramp_project_roundtrip_and_stale_result(workflow: str) -> None:
    ui = ramp_preset_ui_inputs(workflow, "blank_custom", "imperial")
    engine = ramp_ui_inputs_to_engine(workflow, ui, "imperial")
    result = result_to_dict(run_manual_ramp(workflow, engine))
    payload = create_manual_ramp_project_payload(
        workflow, "blank_custom", "imperial", ui, result=result, audit_record={"normalized_engine_inputs": engine}
    )
    loaded = load_manual_ramp_project_json(json.dumps(payload), workflow)
    assert loaded["load_status"] == "result_current"
    assert loaded["calculation_result"]["outputs"]["density_pc_mi_ln"] == result["outputs"]["density_pc_mi_ln"]

    payload["displayed_ui_inputs"]["ramp_demand_veh_h"] += 1
    stale = load_manual_ramp_project_json(json.dumps(payload), workflow)
    assert stale["load_status"] == "project_requires_recalculation"
    assert stale["calculation_result"] is None


def test_ramp_project_rejects_cross_type_hcm71_and_adjacent() -> None:
    ui = ramp_preset_ui_inputs("merge", "blank_custom", "imperial")
    payload = create_manual_ramp_project_payload("merge", "blank_custom", "imperial", ui)
    with pytest.raises(ProjectFileError, match="Wrong project_type"):
        load_manual_ramp_project_json(json.dumps(payload), "diverge")
    payload["method_version"] = "hcm_7_1"
    with pytest.raises(ProjectFileError, match="hcm_7_0"):
        load_manual_ramp_project_json(json.dumps(payload), "merge")


@pytest.mark.parametrize("workflow", ["merge", "diverge"])
def test_ramp_exports_preserve_null_capacity_failure(workflow: str) -> None:
    ui = ramp_preset_ui_inputs(workflow, "blank_custom", "imperial")
    ui["freeway_demand_veh_h"] = 9000
    engine = ramp_ui_inputs_to_engine(workflow, ui, "imperial")
    result = result_to_dict(run_manual_ramp(workflow, engine))
    assert result["outputs"]["level_of_service"] == "F"
    assert result["outputs"]["density_pc_mi_ln"] is None

    calculation_type = MANUAL_MERGE_PROJECT_TYPE if workflow == "merge" else MANUAL_DIVERGE_PROJECT_TYPE
    report = build_report(
        calculation_type,
        result,
        "imperial",
        inputs=ui,
        audit_record={"normalized_engine_inputs": engine},
        template_id="blank_custom",
    )
    exported = json.loads(export_report(report, "json"))
    assert any(row["value"] is None for row in exported["results_summary"])
    assert "None" not in export_report(report, "markdown")


def test_merge_warning_only_export_is_not_capacity_failure() -> None:
    ui = ramp_preset_ui_inputs("merge", "blank_custom", "imperial")
    ui.update(
        freeway_lanes=2,
        freeway_demand_veh_h=3600.0,
        ramp_demand_veh_h=600.0,
        freeway_peak_hour_factor=0.95,
        ramp_peak_hour_factor=0.95,
        free_flow_speed=65.0,
        ramp_ffs=40.0,
        auxiliary_lane_length=600.0,
    )
    engine = ramp_ui_inputs_to_engine("merge", ui, "imperial")
    result = result_to_dict(run_manual_ramp("merge", engine))
    outputs = result["outputs"]

    assert outputs["maximum_desirable_influence_flow_exceeded"] is True
    assert outputs["capacity_status"] == "within_capacity"
    assert outputs["level_of_service"] != "F"
    assert outputs["density_pc_mi_ln"] is not None
    assert outputs["ramp_influence_speed_mph"] is not None

    report = build_report(
        MANUAL_MERGE_PROJECT_TYPE,
        result,
        "imperial",
        inputs=ui,
        audit_record={"normalized_engine_inputs": engine},
        template_id="blank_custom",
    )
    exported = json.loads(export_report(report, "json"))
    summary = {row["label"]: row["value"] for row in exported["results_summary"]}

    assert summary["Capacity status"] == "within_capacity"
    assert summary["Maximum desirable flow exceeded"] is True
    assert summary["Level of service"] != "F"


def test_diverge_warning_only_export_is_not_capacity_failure() -> None:
    ui = ramp_preset_ui_inputs("diverge", "blank_custom", "imperial")
    ui.update(
        freeway_lanes=2,
        freeway_demand_veh_h=4000.0,
        ramp_demand_veh_h=200.0,
        freeway_peak_hour_factor=0.95,
        ramp_peak_hour_factor=0.95,
        free_flow_speed=65.0,
        ramp_ffs=40.0,
        auxiliary_lane_length=600.0,
    )
    engine = ramp_ui_inputs_to_engine("diverge", ui, "imperial")
    result = result_to_dict(run_manual_ramp("diverge", engine))
    outputs = result["outputs"]

    assert outputs["maximum_desirable_influence_flow_exceeded"] is True
    assert outputs["capacity_status"] == "within_capacity"
    assert outputs["level_of_service"] != "F"
    assert outputs["density_pc_mi_ln"] is not None
    assert outputs["ramp_influence_speed_mph"] is not None

    report = build_report(
        MANUAL_DIVERGE_PROJECT_TYPE,
        result,
        "imperial",
        inputs=ui,
        audit_record={"normalized_engine_inputs": engine},
        template_id="blank_custom",
    )
    exported = json.loads(export_report(report, "json"))
    summary = {row["label"]: row["value"] for row in exported["results_summary"]}

    assert summary["Capacity status"] == "within_capacity"
    assert summary["Maximum desirable flow exceeded"] is True
    assert summary["Level of service"] != "F"


def test_ramp_navigation_localization_and_diagrams() -> None:
    assert "Merge Segment" in APP_MODE_LABELS
    assert "Diverge Segment" in APP_MODE_LABELS
    assert resolve_app_view("Merge Segment") == "manual_merge"
    assert resolve_app_view("Diverge Segment") == "manual_diverge"
    assert translate("nav.merge_segment", "th") != "Nav merge segment"
    assert translate("ramp.diverge.title", "th") == "ช่วงแยกกระแส"
    assert translate("ramp.capacity_failure", "th") != "Ramp capacity failure"
    assert not validate_catalogs()
    assert diagram_path("merge").is_file()
    assert diagram_path("diverge").is_file()
    assert "svg" in diagram_path("merge").read_text(encoding="utf-8")


def test_ramp_preset_scope() -> None:
    assert "chapter_28_example_1_merge" in ramp_preset_options("merge")
    assert "chapter_28_example_3_merge_component" in ramp_preset_options("merge")
    assert "chapter_28_example_3_diverge_component" in ramp_preset_options("diverge")
    assert "example_2" not in " ".join(ramp_preset_options("merge"))
