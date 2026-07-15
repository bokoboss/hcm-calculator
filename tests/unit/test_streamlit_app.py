from pathlib import Path

import pytest

from hcmcalc.ui.result_view import (
    compact_rows,
    format_display_metric,
    los_colors,
    result_summary_items,
)
from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.manual_facility import clear_manual_facility_result_state
from hcmcalc.ui.supported_workflows import (
    APP_MODE_LABELS,
    APP_MODE_TO_VIEW,
    AUDIT_EXPANDER_LABEL,
    BASIC_FREEWAY_RAMP_DENSITY_HELP,
    BASIC_FREEWAY_RAMP_DENSITY_LABEL,
    CALCULATION_DETAILS_LABEL,
    EXPORT_REPORT_LABEL,
    EXAMPLE_WORKFLOW_NOTE,
    PROJECT_LOAD_LABEL,
    PROJECT_OUTPUT_LABEL,
    PRERUN_RESULTS_PLACEHOLDER,
    STARTING_VALUES_CAPTION,
    STARTING_VALUES_LABEL,
    SUPPORTED_WORKFLOW_SECTIONS,
    VALIDATION_EXPANDER_LABEL,
    resolve_app_view,
)
from hcmcalc.ui.units import display_outputs


def test_supported_segment_types_map_to_existing_schematics() -> None:
    expected_filenames = {
        "passing_constrained": "passing_constrained.png",
        "passing_zone": "passing_zone.png",
        "passing_lane": "passing_lane.png",
    }

    for segment_type, expected_filename in expected_filenames.items():
        schematic_path = get_segment_schematic_path(segment_type)

        assert schematic_path is not None
        assert schematic_path.name == expected_filename
        assert schematic_path.is_file()


def test_unknown_segment_type_has_no_schematic() -> None:
    assert get_segment_schematic_path("unknown") is None


def test_required_two_lane_schematic_assets_exist() -> None:
    schematic_paths = {
        get_segment_schematic_path(segment_type)
        for segment_type in ("passing_constrained", "passing_zone", "passing_lane")
    }

    assert {path.name for path in schematic_paths if path is not None} == {
        "passing_constrained.png",
        "passing_zone.png",
        "passing_lane.png",
    }
    assert all(path is not None and path.is_file() for path in schematic_paths)


def test_compact_rows_excludes_nested_outputs() -> None:
    outputs = {
        "level_of_service": "D",
        "average_speed_mph": 45.2,
        "segments": [{"segment_id": 1}],
        "metadata": {"status": "validated"},
    }

    assert compact_rows(outputs) == [
        {"output": "level_of_service", "value": "D"},
        {"output": "average_speed_mph", "value": 45.2},
    ]


def test_los_colors_use_distinct_professional_palette() -> None:
    assert los_colors("A") == ("#17643a", "#e8f4ec")
    assert los_colors("F") == ("#721c24", "#f5dddd")
    assert los_colors("unknown") == ("#374151", "#f3f4f6")


def test_primary_metric_formatting_is_consistent() -> None:
    assert format_display_metric(
        "average_speed", {"value": 80.4672, "unit": "km/h"}, "metric"
    ) == "80.5 km/h"
    assert format_display_metric(
        "follower_density", {"value": 12.345, "unit": "fol/km/ln"}, "metric"
    ) == "12.35 fol/km/ln"
    assert format_display_metric(
        "follower_density", {"value": 12.345, "unit": "fol/mi/ln"}, "imperial"
    ) == "12.3 fol/mi/ln"
    assert format_display_metric(
        "demand_flow_rate", {"value": 800.0, "unit": "veh/h"}, "metric"
    ) == "800 veh/h"


def test_result_summary_items_preserve_primary_first_ordering() -> None:
    assert result_summary_items(
        "Level of service",
        "D",
        [
            {"label": "Density", "value": "18.0 pc/mi/ln"},
            {"label": "Speed used for density", "value": "55.0 mph"},
            {"label": "Demand flow rate", "value": "1,100 pc/h/ln"},
            {"label": "Capacity", "value": "2,200 pc/h/ln"},
        ],
    ) == [
        {"label": "Level of service", "value": "D"},
        {"label": "Density", "value": "18.0 pc/mi/ln"},
        {"label": "Speed used for density", "value": "55.0 mph"},
        {"label": "Demand flow rate", "value": "1,100 pc/h/ln"},
        {"label": "Capacity", "value": "2,200 pc/h/ln"},
    ]


def test_two_lane_summary_grid_omits_hero_supporting_metric() -> None:
    metrics = display_outputs(
        {
            "follower_density_followers_mi_ln": 12.3,
            "average_speed_mph": 48.2,
            "percent_followers": 61.0,
            "demand_flow_rate_veh_h": 800.0,
            "capacity_veh_h": 1700.0,
            "free_flow_speed_mph": 55.0,
        },
        "imperial",
    )

    secondary_metrics = [
        {
            "label": metric["label"],
            "value": format_display_metric(name, metric, "imperial"),
        }
        for name, metric in metrics.items()
        if name != "follower_density"
    ]

    assert [metric["label"] for metric in secondary_metrics] == [
        "Average speed",
        "Percent followers",
        "Demand flow rate",
        "Capacity",
        "Free-flow speed",
    ]


def test_template_switching_preserves_facility_results_for_audit() -> None:
    state = {
        "manual_facility_result": {"outputs": {}},
        "manual_facility_result_context": ("level_example_3", "imperial"),
        "manual_facility_result_rows": [{"segment_id": 1}],
        "manual_facility_audit": {"template_id": "level_example_3"},
        "manual_facility_error": "old error",
        "unrelated": "preserved",
    }

    clear_manual_facility_result_state(state)

    assert state == {
        "manual_facility_result": {"outputs": {}},
        "manual_facility_result_context": ("level_example_3", "imperial"),
        "manual_facility_result_rows": [{"segment_id": 1}],
        "manual_facility_audit": {"template_id": "level_example_3"},
        "unrelated": "preserved",
    }


def test_app_mode_list_includes_supported_workflows() -> None:
    assert APP_MODE_LABELS == (
        "Two-Lane Segment",
        "Two-Lane Facility",
        "Multilane Segment",
        "Basic Freeway Segment",
        "Weaving Segment",
        "Supported Workflows",
    )
    assert APP_MODE_LABELS[0] == "Two-Lane Segment"
    assert APP_MODE_TO_VIEW["Supported Workflows"] == "supported_workflows"
    assert APP_MODE_TO_VIEW["Two-Lane Segment"] == "manual_single_segment"
    assert APP_MODE_TO_VIEW["Basic Freeway Segment"] == "manual_basic_freeway"
    assert APP_MODE_TO_VIEW["Weaving Segment"] == "manual_weaving"
    assert "Validation Examples" not in APP_MODE_LABELS


def test_internal_validation_examples_route_is_not_public_navigation() -> None:
    assert resolve_app_view("Two-Lane Segment", {}) == "manual_single_segment"
    assert (
        resolve_app_view("Two-Lane Segment", {"qa_view": "validated_examples"})
        == "validated_examples"
    )


def test_calculator_ui_shared_grammar_labels_are_standardized() -> None:
    assert VALIDATION_EXPANDER_LABEL == "Validation basis and limitations"
    assert CALCULATION_DETAILS_LABEL == "Calculation details"
    assert AUDIT_EXPANDER_LABEL == "Audit / intermediate values"
    assert STARTING_VALUES_LABEL == "Optional defaults"
    assert PROJECT_LOAD_LABEL == "Load saved project"
    assert PROJECT_OUTPUT_LABEL == "Project output"
    assert EXPORT_REPORT_LABEL == "Export / Report"
    assert PRERUN_RESULTS_PLACEHOLDER == "Results will appear after calculation."
    assert STARTING_VALUES_CAPTION == (
        "Optional defaults only prefill supported inputs. You may edit values before "
        "running the calculation."
    )
    assert BASIC_FREEWAY_RAMP_DENSITY_LABEL == "Ramp density for FFS adjustment"
    assert BASIC_FREEWAY_RAMP_DENSITY_HELP == (
        "Used for Basic Freeway speed adjustment only; not a ramp analysis workflow."
    )


def test_supported_workflows_content_names_current_scope() -> None:
    sections = {section["title"]: section for section in SUPPORTED_WORKFLOW_SECTIONS}

    assert set(sections) == {
        "Two-Lane Highway",
        "Two-Lane Facility",
        "Multilane Highway",
        "Basic Freeway",
        "Freeway Weaving Segment",
        "Validation Evidence",
    }
    assert "Manual Single Segment Calculator" in sections["Two-Lane Highway"]["supported"]
    assert "Manual Facility Calculator" in sections["Two-Lane Facility"]["supported"]
    assert "Save/Load" in sections["Two-Lane Highway"]["save_load_export"]
    assert (
        "bounded HCM Multilane Highway Segment one-direction analysis"
        in sections["Multilane Highway"]["supported"]
    )
    assert (
        "Chapter 26 Example 4 optional defaults and regression evidence"
        in sections["Multilane Highway"]["supported"]
    )
    assert (
        "bounded Chapter 12 one-direction, one-segment uninterrupted-flow analysis"
        in sections["Basic Freeway"]["supported"]
    )
    assert (
        "Chapter 26 Example 1 optional defaults and regression evidence"
        in sections["Basic Freeway"]["supported"]
    )
    assert "not a general freeway facility calculator" in sections["Basic Freeway"]["limitations"]
    assert "not a Basic Freeway calculator" in sections["Multilane Highway"]["limitations"]
    assert (
        "Regression/reference evidence for implemented fixture cases"
        in sections["Validation Evidence"]["supported"]
    )
    assert "not user-facing workflows" in EXAMPLE_WORKFLOW_NOTE


def test_multilane_streamlit_source_does_not_reference_missing_capacity_key() -> None:
    source = Path("src/hcmcalc/ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "display['adjusted_capacity']" not in source
    assert 'display["adjusted_capacity"]' not in source
    assert "display['capacity']" in source


def _apptest():
    streamlit_testing = pytest.importorskip("streamlit.testing.v1")
    return streamlit_testing.AppTest


def test_multilane_streamlit_result_panel_uses_canonical_capacity_display_key() -> None:
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    app.radio[0].set_value("Multilane Segment")
    app.run()

    app.button[1].click()
    app.run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Speed used for density"] == "79.7 km/h"
    assert metrics["Demand flow rate"] == "895 pc/h/ln"
    assert metrics["Capacity"] == "1990 pc/h/ln"
    assert metrics["Capacity check"] == "within capacity"
    assert "Adjusted capacity" not in metrics
    assert any("LOS C" in markdown.value for markdown in app.markdown)
    assert any("Density <strong>11.2 pc/km/ln</strong>" in markdown.value for markdown in app.markdown)

    app.number_input[6].set_value(1600.0)
    app.run()

    assert not app.exception
    assert any(
        "Input changed" in caption.value and "recalculate required" in caption.value
        for caption in app.caption
    )

    app.button[1].click()
    app.run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Demand flow rate"] == "955 pc/h/ln"
    assert metrics["Capacity"] == "1990 pc/h/ln"


def test_multilane_streamlit_above_capacity_preserves_not_predicted_outputs() -> None:
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    app.radio[0].set_value("Multilane Segment")
    app.run()
    app.number_input[6].set_value(10000.0)
    app.run()

    app.button[1].click()
    app.run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Speed used for density"] == "Not predicted"
    assert metrics["Demand flow rate"] == "5969 pc/h/ln"
    assert metrics["Capacity"] == "1990 pc/h/ln"
    assert metrics["Capacity check"] == "demand exceeds capacity"
    assert any("LOS F" in markdown.value for markdown in app.markdown)
    assert any("Density <strong>Not predicted</strong>" in markdown.value for markdown in app.markdown)
