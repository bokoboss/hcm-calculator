"""Cross-method product contracts that do not derive expected values from exports."""

from __future__ import annotations

import json

import pytest

from hcmcalc.cli import result_to_dict
from hcmcalc.ui.audit import build_manual_calculation_audit_record
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    load_facility_template,
    run_manual_facility,
)
from hcmcalc.ui.manual_freeway import (
    build_manual_freeway_audit_record,
    freeway_preset_ui_inputs,
    load_freeway_preset,
    run_manual_freeway,
)
from hcmcalc.ui.manual_multilane import (
    build_manual_multilane_audit_record,
    load_multilane_template,
    multilane_template_ui_inputs,
    run_manual_multilane,
)
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.reporting import build_report, export_report
from hcmcalc.ui.units import manual_defaults


def _contexts() -> list[tuple[str, str, dict, dict, object, str | None, str]]:
    segment_inputs = manual_defaults("metric") | {
        "unit_system": "metric",
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "horizontal_alignment": "straight",
    }
    segment_result = run_manual_single_segment(segment_inputs)

    facility = load_facility_template("level_example_3", "metric")
    facility_result = run_manual_facility(
        facility["template_id"], facility["segments"], "metric"
    )

    multilane = load_multilane_template("MLH-CH26-004-EB")
    multilane_displayed = multilane_template_ui_inputs("MLH-CH26-004-EB", "metric")
    multilane_result = run_manual_multilane(multilane["inputs"])

    freeway = load_freeway_preset("BF-CH26-001")
    freeway_displayed = freeway_preset_ui_inputs("BF-CH26-001", "metric")
    freeway_result = run_manual_freeway(freeway["inputs"])

    return [
        (
            "manual_single_segment", "metric", result_to_dict(segment_result),
            segment_inputs,
            build_manual_calculation_audit_record(segment_inputs, result=segment_result),
            None, "D",
        ),
        (
            "manual_two_lane_facility_v1", "metric", result_to_dict(facility_result),
            facility["segments"],
            build_manual_facility_audit_record(
                facility["template_id"], facility["segments"], "metric", result=facility_result
            ),
            facility["template_id"], "C",
        ),
        (
            "manual_multilane_v0", "metric", result_to_dict(multilane_result),
            multilane_displayed,
            build_manual_multilane_audit_record(
                "MLH-CH26-004-EB", multilane["inputs"], unit_system="metric",
                displayed_inputs=multilane_displayed, result=multilane_result,
            ),
            "MLH-CH26-004-EB", "C",
        ),
        (
            "manual_basic_freeway_v0", "metric", result_to_dict(freeway_result),
            freeway_displayed,
            build_manual_freeway_audit_record(
                "BF-CH26-001", freeway["inputs"], unit_system="metric",
                displayed_inputs=freeway_displayed, result=freeway_result,
            ),
            "BF-CH26-001", "C",
        ),
    ]


@pytest.mark.parametrize(
    ("calculation_type", "unit_system", "result", "inputs", "audit", "template_id", "expected_los"),
    _contexts(),
)
def test_cross_method_result_and_export_contract(
    calculation_type: str,
    unit_system: str,
    result: dict,
    inputs: dict | list[dict],
    audit: dict,
    template_id: str | None,
    expected_los: str,
) -> None:
    """Each export surface represents the same already-calculated result."""

    assert result["method"]
    assert result["result_contract_version"] != "unversioned"
    assert result["facility_type"]
    assert isinstance(result["assumptions"], list)
    assert isinstance(result["warnings"], list)
    assert result["intermediate_values"]
    assert any(row.get("source") for row in result["intermediate_values"])

    report = build_report(
        calculation_type, result, unit_system, inputs=inputs,
        audit_record=audit, template_id=template_id,
        generated_at="2026-07-15T00:00:00+00:00",
    )
    report_json = json.loads(export_report(report, "json"))
    summary_values = {row["value"] for row in report_json["results_summary"]}

    assert report_json["method_identifier"] == result["method"]
    assert report_json["method_version"] == result["result_contract_version"]
    assert expected_los in summary_values
    assert export_report(report, "csv")
    assert "Method:" in export_report(report, "markdown")
    assert export_report(report, "xlsx")[:2] == b"PK"
