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


@pytest.mark.parametrize(
    ("report_factory", "expected"),
    [
        (_single_report, "Manual Single Segment"),
        (_facility_report, "Manual Facility Calculator v0.1"),
    ],
)
def test_markdown_generation(report_factory, expected: str) -> None:
    markdown = export_report(report_factory(), "markdown")

    assert expected in markdown
    assert "## Limitations" in markdown
    assert "km/h" in markdown
    assert "## Assumptions" in markdown


@pytest.mark.parametrize("report_factory", [_single_report, _facility_report])
def test_csv_generation_includes_units_limitations_and_warnings(report_factory) -> None:
    csv_text = export_report(report_factory(), "csv")

    assert "Limitations" in csv_text
    assert "Warnings" in csv_text
    assert "km/h" in csv_text
    assert "Assumptions" in csv_text


@pytest.mark.parametrize("report_factory", [_single_report, _facility_report])
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
    assert "Unsupported combinations remain guarded." in cells


def test_facility_csv_contains_segment_result_rows() -> None:
    csv_text = export_report(_facility_report("imperial"), "csv")

    assert "Segment Results" in csv_text
    assert "Segment ID,Segment type,Length (mi)" in csv_text
    assert csv_text.count("passing_constrained") >= 1


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
