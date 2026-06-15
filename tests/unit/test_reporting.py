import json
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook

from hcmcalc.cli import result_to_dict
from hcmcalc.ui.audit import build_manual_calculation_audit_record
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    load_facility_template,
    run_manual_facility,
)
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.manual_multilane import (
    MANUAL_MULTILANE_LIMITATIONS,
    build_manual_multilane_audit_record,
    load_multilane_template,
    multilane_template_ui_inputs,
    run_manual_multilane,
)
from hcmcalc.ui.reporting import (
    FACILITY_LIMITATIONS,
    SINGLE_SEGMENT_LIMITATIONS,
    ReportingError,
    build_report,
    export_report,
    report_filename,
)
from hcmcalc.ui.units import manual_defaults


def _single_segment_context(unit_system: str = "metric"):
    inputs = {
        **manual_defaults(unit_system),
        "unit_system": unit_system,
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "horizontal_alignment": "straight",
    }
    result = run_manual_single_segment(inputs)
    return inputs, result_to_dict(result), build_manual_calculation_audit_record(
        inputs, result=result
    )


def _facility_context(unit_system: str = "metric"):
    template = load_facility_template("mountainous_example_4", unit_system)
    result = run_manual_facility(
        template["template_id"], template["segments"], unit_system
    )
    return (
        template,
        result_to_dict(result),
        build_manual_facility_audit_record(
            template["template_id"], template["segments"], unit_system, result=result
        ),
    )


def _single_report(unit_system: str = "metric"):
    inputs, result, audit = _single_segment_context(unit_system)
    return build_report(
        "manual_single_segment", result, unit_system, inputs=inputs, audit_record=audit
    )


def _facility_report(unit_system: str = "metric"):
    template, result, audit = _facility_context(unit_system)
    return build_report(
        "manual_facility_v0",
        result,
        unit_system,
        inputs=template["segments"],
        audit_record=audit,
        template_id=template["template_id"],
    )


def _multilane_report(unit_system: str = "metric", template_id: str = "MLH-CH26-004-EB"):
    template = load_multilane_template(template_id)
    displayed = multilane_template_ui_inputs(template_id, unit_system)
    result = run_manual_multilane(template["inputs"])
    audit = build_manual_multilane_audit_record(
        template_id,
        template["inputs"],
        unit_system=unit_system,
        displayed_inputs=displayed,
        result=result,
    )
    return build_report(
        "manual_multilane_v0",
        result_to_dict(result),
        unit_system,
        inputs=displayed,
        audit_record=audit,
        template_id=template_id,
    )


def test_single_segment_report_json_generation_includes_units_and_limitations() -> None:
    report = _single_report()
    exported = json.loads(export_report(report, "json"))

    assert exported["schema_version"] == "0.1"
    assert exported["calculation_type"] == "manual_single_segment"
    assert any(item["unit"] == "km/h" for item in exported["results_summary"])
    assert exported["limitations"] == SINGLE_SEGMENT_LIMITATIONS
    assert exported["assumptions"]


def test_facility_report_json_generation_includes_segment_rows_and_limitations() -> None:
    report = _facility_report()
    exported = json.loads(export_report(report, "json"))

    assert exported["calculation_type"] == "manual_facility_v0"
    assert len(exported["segment_results"]) == 6
    assert "Average speed (km/h)" in exported["segment_results"][0]
    assert exported["limitations"] == FACILITY_LIMITATIONS
    assert exported["warnings"]


def test_multilane_report_json_includes_units_context_and_limitations() -> None:
    exported = json.loads(export_report(_multilane_report(), "json"))

    assert exported["calculation_type"] == "manual_multilane_v0"
    assert exported["selected_validated_template"] == "MLH-CH26-004-EB"
    assert any(item["unit"] == "km/h" for item in exported["results_summary"])
    assert any(
        item["unit"] == "ft (engine-native Imperial)"
        for item in exported["normalized_engine_inputs_summary"]
    )
    assert exported["limitations"] == MANUAL_MULTILANE_LIMITATIONS
    assert exported["assumptions"]
    assert exported["warnings"]
    assert exported["intermediate_values"]


@pytest.mark.parametrize(
    ("report_factory", "expected"),
    [
        (_single_report, "Manual Single Segment"),
        (_facility_report, "Manual Facility Calculator v0.1"),
        (_multilane_report, "Manual Multilane Highway Segment v0.1"),
    ],
)
def test_markdown_generation(report_factory, expected: str) -> None:
    markdown = export_report(report_factory(), "markdown")

    assert expected in markdown
    assert "## Limitations" in markdown
    assert "km/h" in markdown
    assert "## Assumptions" in markdown


@pytest.mark.parametrize("report_factory", [_single_report, _facility_report, _multilane_report])
def test_csv_generation_includes_units_limitations_and_warnings(report_factory) -> None:
    csv_text = export_report(report_factory(), "csv")

    assert "Limitations" in csv_text
    assert "Warnings" in csv_text
    assert "km/h" in csv_text
    assert "Assumptions" in csv_text


@pytest.mark.parametrize("report_factory", [_single_report, _facility_report, _multilane_report])
def test_excel_generation_has_required_sheets_units_and_limitations(report_factory) -> None:
    workbook = load_workbook(BytesIO(export_report(report_factory(), "xlsx")))

    assert workbook.sheetnames == [
        "Summary",
        "Inputs",
        "Segment Results",
        "Assumptions Warnings Limits",
        "Audit",
    ]
    cells = " ".join(
        str(cell.value)
        for sheet in workbook.worksheets
        for row in sheet.iter_rows()
        for cell in row
        if cell.value is not None
    )
    assert "km/h" in cells
    assert any(limitation in cells for limitation in report_factory()["limitations"])


def test_facility_csv_contains_segment_result_rows() -> None:
    csv_text = export_report(_facility_report("imperial"), "csv")

    assert "Segment Results" in csv_text
    assert "Segment ID,Segment type,Length (mi)" in csv_text
    assert csv_text.count("passing_constrained") >= 1


def test_multilane_metric_and_imperial_exports_use_selected_display_units() -> None:
    metric_report = _multilane_report("metric")
    imperial_report = _multilane_report("imperial")
    metric_csv = export_report(metric_report, "csv")
    imperial_csv = export_report(imperial_report, "csv")

    assert "pc/km/ln" in metric_csv
    assert "km/h" in metric_csv
    assert "pc/mi/ln" in imperial_csv
    assert "mph" in imperial_csv
    assert "Normalized Engine Inputs" in metric_csv
    assert "engine-native Imperial" in metric_csv
    assert next(
        item for item in imperial_report["inputs_summary"]
        if item["label"] == "Segment Length"
    )["unit"] == "ft"
    assert "Manual Multilane v0.1 is limited" in metric_csv
    assert "## Intermediate Values" in export_report(
        _multilane_report("metric"), "markdown"
    )
    assert "## Normalized Engine Inputs" in export_report(
        _multilane_report("metric"), "markdown"
    )


def test_report_generation_rejects_missing_result() -> None:
    with pytest.raises(ReportingError, match="calculated result is required"):
        build_report("manual_single_segment", None, "metric")


def test_report_generation_rejects_unsupported_calculation_type() -> None:
    with pytest.raises(ReportingError, match="Unsupported calculation_type"):
        build_report("validated_example", {"outputs": {}}, "metric")


def test_report_generation_rejects_malformed_result() -> None:
    with pytest.raises(ReportingError, match="Malformed result object"):
        build_report("manual_single_segment", {"outputs": {}}, "metric")


def test_report_export_rejects_unsupported_format() -> None:
    with pytest.raises(ReportingError, match="Unsupported export format"):
        export_report(_single_report(), "pdf")


def test_report_export_rejects_non_serializable_field() -> None:
    report = _single_report()
    report["inputs_summary"][0]["value"] = object()

    with pytest.raises(ReportingError, match="Non-serializable report field"):
        export_report(report, "json")


def test_reporting_module_is_streamlit_independent() -> None:
    source = Path("src/hcmcalc/ui/reporting.py").read_text(encoding="utf-8")

    assert "import streamlit" not in source


def test_report_filename_uses_required_pattern() -> None:
    report = _single_report()
    report["generated_at"] = "2026-06-12T10:11:12+00:00"

    assert (
        report_filename(report, "xlsx")
        == "hcm_ch15_single_segment_report_20260612_101112.xlsx"
    )
