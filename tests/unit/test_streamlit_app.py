import json
import math
import os
from pathlib import Path

import pytest

from hcmcalc.cli import result_to_dict
from hcmcalc.ui.audit import build_manual_calculation_audit_record
from hcmcalc.ui.result_view import (
    compact_rows,
    format_display_metric,
    los_colors,
    result_summary_items,
)
from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    clear_manual_facility_result_state,
    load_facility_template,
    run_manual_facility,
)
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.manual_multilane import (
    build_manual_multilane_audit_record,
    load_multilane_template,
    multilane_template_ui_inputs,
    multilane_ui_inputs_to_engine,
    run_manual_multilane,
)
from hcmcalc.ui.manual_freeway import (
    build_manual_freeway_audit_record,
    freeway_preset_ui_inputs,
    freeway_ui_inputs_to_engine,
    load_freeway_preset,
    run_manual_freeway,
)
from hcmcalc.ui.manual_ramp_influence import (
    build_manual_ramp_audit_record,
    ramp_preset_ui_inputs,
    ramp_ui_inputs_to_engine,
    run_manual_ramp,
)
from hcmcalc.ui.i18n import translate
from hcmcalc.ui.project_io import (
    create_manual_facility_project_json,
    create_manual_freeway_project_json,
    create_manual_multilane_project_json,
    create_manual_project_json,
    create_manual_ramp_project_json,
)
from hcmcalc.ui.supported_workflows import (
    APP_MODE_LABELS,
    APP_MODE_TO_VIEW,
    APP_VIEW_TO_MODE,
    APP_VIEW_TO_NAV_KEY,
    NAVIGATION_GROUPS,
    NAVIGATION_GROUP_VIEWS,
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
    SUPPORTED_PAGE_CAPABILITIES,
    SUPPORTED_PAGE_LIMITATIONS,
    SUPPORTED_PAGE_WORKFLOW_GROUPS,
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
        "Merge Segment",
        "Diverge Segment",
        "Supported Workflows",
    )
    assert APP_MODE_LABELS[0] == "Two-Lane Segment"
    assert APP_MODE_TO_VIEW["Supported Workflows"] == "supported_workflows"
    assert APP_MODE_TO_VIEW["Two-Lane Segment"] == "manual_single_segment"
    assert APP_MODE_TO_VIEW["Basic Freeway Segment"] == "manual_basic_freeway"
    assert APP_MODE_TO_VIEW["Weaving Segment"] == "manual_weaving"
    assert APP_VIEW_TO_MODE["supported_workflows"] == "Supported Workflows"
    assert APP_VIEW_TO_NAV_KEY["manual_facility"] == "nav.two_lane_facility"
    assert "Validation Examples" not in APP_MODE_LABELS
    assert NAVIGATION_GROUPS == (
        ("roadways", ("Two-Lane Segment", "Two-Lane Facility", "Multilane Segment")),
        ("freeways", ("Basic Freeway Segment", "Weaving Segment", "Merge Segment", "Diverge Segment")),
        ("reference", ("Supported Workflows",)),
    )
    assert NAVIGATION_GROUP_VIEWS == (
        ("roadways", ("manual_single_segment", "manual_facility", "manual_multilane")),
        (
            "freeways",
            (
                "manual_basic_freeway",
                "manual_weaving",
                "manual_merge",
                "manual_diverge",
            ),
        ),
        ("reference", ("supported_workflows",)),
    )


def test_grouped_navigation_can_open_each_public_workflow() -> None:
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    for group, views in NAVIGATION_GROUP_VIEWS:
        app.selectbox[1].set_value(group).run()
        for view in views:
            app.selectbox[2].set_value(view).run()
            assert not app.exception
            assert app.session_state["selected_calculator_view"] == view
            assert app.session_state["selected_calculator_mode"] == APP_VIEW_TO_MODE[view]


def test_grouped_navigation_opens_each_public_workflow_in_thai() -> None:
    AppTest = _apptest()
    for group, views in NAVIGATION_GROUP_VIEWS:
        for view in views:
            app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
            app.run()
            app.selectbox[0].set_value("th").run()
            app.selectbox[1].set_value(group).run()
            app.selectbox[2].set_value(view).run()
            assert not app.exception
            assert translate(APP_VIEW_TO_NAV_KEY[view], "th") in str(app)


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
        "Freeway Merge and Diverge Segments",
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


def test_supported_workflows_localized_page_metadata_is_complete() -> None:
    assert SUPPORTED_PAGE_WORKFLOW_GROUPS == (
        ("roadways", ("manual_single_segment", "manual_facility", "manual_multilane")),
        (
            "freeways",
            (
                "manual_basic_freeway",
                "manual_weaving",
                "manual_merge",
                "manual_diverge",
            ),
        ),
    )
    assert "stale_result_protection" in SUPPORTED_PAGE_CAPABILITIES
    assert "hcm_7_1" in SUPPORTED_PAGE_LIMITATIONS

    for locale in ("en", "th"):
        assert translate("supported.title", locale)
        for group, workflow_ids in SUPPORTED_PAGE_WORKFLOW_GROUPS:
            assert translate(f"supported.section.{group}", locale)
            for workflow_id in workflow_ids:
                assert translate(f"supported.workflow.{workflow_id}.summary", locale)
                assert translate(f"supported.workflow.{workflow_id}.supported.1", locale)
                assert translate(f"supported.workflow.{workflow_id}.limit.1", locale)
        for capability in SUPPORTED_PAGE_CAPABILITIES:
            assert translate(f"supported.capability.{capability}", locale)
        for limitation in SUPPORTED_PAGE_LIMITATIONS:
            assert translate(f"supported.limit.{limitation}", locale)


def test_supported_workflows_page_renders_english_and_thai() -> None:
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    app.selectbox[1].set_value("reference").run()
    app.selectbox[2].set_value("supported_workflows").run()
    assert translate("supported.title", "en") in str(app)
    assert any(
        translate("supported.section.product_capabilities", "en") in markdown.value
        for markdown in app.markdown
    )

    app.selectbox[0].set_value("th").run()
    assert any(title.value == translate("supported.title", "th") for title in app.title)
    assert any(
        translate("supported.section.product_capabilities", "th") in markdown.value
        for markdown in app.markdown
    )
    thai_visible_text = " ".join(
        [
            *[title.value for title in app.title],
            *[markdown.value for markdown in app.markdown],
            *[caption.value for caption in app.caption],
        ]
    )
    for english in (
        "Supported Workflows",
        "Roadways",
        "Freeways",
        "Product capabilities",
        "Current method limitations",
        "Choose a calculator",
    ):
        assert english not in thai_visible_text
    assert not app.exception


def test_multilane_streamlit_source_does_not_reference_missing_capacity_key() -> None:
    source = Path("src/hcmcalc/ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "display['adjusted_capacity']" not in source
    assert 'display["adjusted_capacity"]' not in source
    assert "display['capacity']" in source


def _apptest():
    os.environ["PYTHONPATH"] = str(Path("src").resolve())
    streamlit_testing = pytest.importorskip("streamlit.testing.v1")
    return streamlit_testing.AppTest


def _open_two_lane_app(locale: str = "en"):
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    if locale != "en":
        app.selectbox[0].set_value(locale).run()
    app.selectbox[1].set_value("roadways").run()
    app.selectbox[2].set_value("manual_single_segment").run()
    return app


def _open_facility_app(locale: str = "en"):
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    if locale != "en":
        app.selectbox[0].set_value(locale).run()
    app.selectbox[1].set_value("roadways").run()
    app.selectbox[2].set_value("manual_facility").run()
    return app


def _facility_editor_key(app) -> str:
    return next(
        key
        for key in app.session_state.filtered_state
        if str(key).startswith("facility_segment_editor_")
    )


def _open_multilane_app(locale: str = "en"):
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    if locale != "en":
        app.selectbox[0].set_value(locale).run()
    app.selectbox[1].set_value("roadways").run()
    app.selectbox[2].set_value("manual_multilane").run()
    return app


def _open_freeway_app(locale: str = "en"):
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    if locale != "en":
        app.selectbox[0].set_value(locale).run()
    app.selectbox[1].set_value("freeways").run()
    app.selectbox[2].set_value("manual_basic_freeway").run()
    return app


def _open_merge_app(locale: str = "en"):
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    if locale != "en":
        app.selectbox[0].set_value(locale).run()
    app.selectbox[1].set_value("freeways").run()
    app.selectbox[2].set_value("manual_merge").run()
    return app


def _open_diverge_app(locale: str = "en"):
    AppTest = _apptest()
    app = AppTest.from_file("src/hcmcalc/ui/streamlit_app.py", default_timeout=20)
    app.run()
    if locale != "en":
        app.selectbox[0].set_value(locale).run()
    app.selectbox[1].set_value("freeways").run()
    app.selectbox[2].set_value("manual_diverge").run()
    return app


def _two_lane_project_inputs() -> dict[str, object]:
    return {
        "unit_system": "metric",
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "posted_speed": 80.0,
        "segment_length": 1.2,
        "lane_width": 3.5,
        "shoulder_width": 1.8,
        "access_point_density": 0.0,
        "analysis_direction_volume": 750.0,
        "peak_hour_factor": 0.94,
        "heavy_vehicle_percent": 5.0,
        "grade_percent": 0.0,
        "opposing_direction_volume": None,
        "horizontal_alignment": "straight",
        "horizontal_alignment_subsegments": [],
    }


def test_two_lane_segment_streamlit_stable_english_result_and_exports() -> None:
    app = _open_two_lane_app()

    app.button[1].click().run()

    assert not app.exception
    assert translate("two_lane.title", "en") in str(app)
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Average travel speed"] == "85.4 km/h"
    assert metrics["Percent followers"] == "67.8 %"
    assert metrics["Demand flow rate"] == "798 veh/h"
    assert metrics["Capacity"] == "1700 veh/h"
    assert metrics["Free-flow speed"] == "90.3 km/h"
    assert any("LOS D" in markdown.value for markdown in app.markdown)
    assert any(
        "Follower density <strong>6.34 fol/km/ln</strong>" in markdown.value
        for markdown in app.markdown
    )
    assert any(button.label == "Download CSV" for button in app.download_button)
    assert any(button.label == "Download Excel" for button in app.download_button)
    assert any(button.label == "Download Markdown" for button in app.download_button)
    assert any(button.label == "Download Report JSON" for button in app.download_button)


def test_two_lane_segment_thai_result_has_localized_visible_surfaces() -> None:
    app = _open_two_lane_app("th")

    app.button[1].click().run()

    assert not app.exception
    assert translate("two_lane.title", "th") in str(app)
    metric_labels = {metric.label for metric in app.metric}
    assert translate("result.average_travel_speed", "th") in metric_labels
    assert translate("result.percent_followers", "th") in metric_labels
    assert translate("result.demand_flow_rate", "th") in metric_labels
    assert translate("result.capacity", "th") in metric_labels
    visible_labels = [
        *[button.label for button in app.button],
        *[button.label for button in app.download_button],
        *[select.label for select in app.selectbox],
        *[control.label for control in app.segmented_control],
        *[metric.label for metric in app.metric],
    ]
    for english in (
        "Calculate",
        "Result summary",
        "Roadway geometry",
        "Save project",
        "Project JSON file",
    ):
        assert english not in visible_labels


def test_two_lane_segment_stale_state_hides_metrics_and_blocks_report_exports() -> None:
    app = _open_two_lane_app()
    app.button[1].click().run()

    app.number_input[0].set_value(1.3).run()

    assert not app.exception
    assert any(translate("two_lane.stale", "en") in warning.value for warning in app.warning)
    assert not {metric.label for metric in app.metric}
    assert all(button.label != "Download CSV" for button in app.download_button)

    app.button[1].click().run()
    assert {metric.label: metric.value for metric in app.metric}["Capacity"] == "1700 veh/h"


def test_two_lane_segment_grade_curve_and_passing_lane_paths_render() -> None:
    grade = _open_two_lane_app()
    grade.selectbox[4].set_value("mountainous").run()
    assert "Grade (%)" in {control.label for control in grade.number_input}
    grade.button[1].click().run()
    assert not grade.exception
    assert "Average travel speed" in {metric.label for metric in grade.metric}

    curve = _open_two_lane_app()
    curve.selectbox[5].set_value("horizontal_curves").run()
    assert "Curve radius (m)" in {control.label for control in curve.number_input}
    curve.button[2].click().run()
    assert not curve.exception
    assert "Free-flow speed" in {metric.label for metric in curve.metric}

    passing = _open_two_lane_app()
    passing.selectbox[3].set_value("passing_lane").run()
    passing.button[1].click().run()
    assert not passing.exception
    assert "Percent followers" in {metric.label for metric in passing.metric}


def test_two_lane_segment_invalid_and_unsupported_states_have_no_metrics() -> None:
    invalid = _open_two_lane_app()
    invalid.number_input[0].set_value(0.0).run()
    invalid.button[1].click().run()

    assert not invalid.exception
    assert any(translate("two_lane.invalid", "en") in error.value for error in invalid.error)
    assert not {metric.label for metric in invalid.metric}

    unsupported = _open_two_lane_app()
    unsupported.number_input[0].set_value(0.1).run()
    unsupported.button[1].click().run()

    assert not unsupported.exception
    assert any(
        translate("two_lane.unsupported", "en") in warning.value
        for warning in unsupported.warning
    )
    assert not {metric.label for metric in unsupported.metric}


def test_two_lane_segment_project_load_current_wrong_type_and_malformed_smoke() -> None:
    inputs = _two_lane_project_inputs()
    result = run_manual_single_segment(inputs)
    project_json = create_manual_project_json(
        inputs,
        result=result_to_dict(result),
        audit_record=build_manual_calculation_audit_record(inputs, result=result),
        locale="th",
    )
    app = _open_two_lane_app()
    app.file_uploader[0].upload(
        "two-lane-segment-project.json",
        project_json.encode("utf-8"),
        "application/json",
    ).run()
    app.button[0].click().run()

    assert not app.exception
    assert app.selectbox[0].value == "th"
    assert any(translate("project.load_current", "th") in success.value for success in app.success)
    assert "ความเร็วเดินทางเฉลี่ย" in {metric.label for metric in app.metric}

    wrong_project = create_manual_multilane_project_json(
        "MLH-CH26-004-EB", "metric", multilane_template_ui_inputs("MLH-CH26-004-EB", "metric")
    )
    wrong = _open_two_lane_app("th")
    wrong.file_uploader[0].upload(
        "multilane-project.json", wrong_project.encode("utf-8"), "application/json"
    ).run()
    wrong.button[0].click().run()
    assert not wrong.exception
    assert any(
        translate("two_lane.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in wrong.error
    )

    malformed = _open_two_lane_app("th")
    malformed.file_uploader[0].upload(
        "bad-project.json", b'{"project_type":"wrong"}', "application/json"
    ).run()
    malformed.button[0].click().run()
    assert not malformed.exception
    assert any(
        translate("two_lane.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in malformed.error
    )


def test_two_lane_segment_navigation_isolation_from_multilane() -> None:
    app = _open_two_lane_app()
    app.button[1].click().run()
    assert "Average travel speed" in {metric.label for metric in app.metric}

    app.selectbox[2].set_value("manual_multilane").run()

    assert not app.exception
    assert not {metric.label for metric in app.metric}
    assert any(translate("multilane.prerun", "en") in info.value for info in app.info)

    app.selectbox[2].set_value("manual_single_segment").run()

    assert "Average travel speed" in {metric.label for metric in app.metric}


def test_two_lane_facility_streamlit_stable_english_result_and_exports() -> None:
    app = _open_facility_app()

    app.button[1].click().run()

    assert not app.exception
    assert translate("facility.title", "en") in str(app)
    assert len(app.dataframe) >= 2
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Weighted average speed"] == "94.4 km/h"
    assert metrics["Facility length"] == "8.85 km"
    assert metrics["Segments"] == "5"
    assert any("LOS C" in markdown.value for markdown in app.markdown)
    assert any(
        "Facility follower density <strong>4.53 fol/km/ln</strong>" in markdown.value
        for markdown in app.markdown
    )
    assert any(button.label == "Download CSV" for button in app.download_button)
    assert any(button.label == "Download Excel" for button in app.download_button)
    assert any(button.label == "Download Markdown" for button in app.download_button)
    assert any(button.label == "Download Report JSON" for button in app.download_button)
    audit_rows = app.session_state["manual_facility_audit"]["facility_inputs"]["segments"]
    assert all(
        row["opposing_direction_volume_veh_h"] is None
        for row in audit_rows
        if row["segment_type"] != "passing_zone"
    )
    json.dumps(app.session_state["manual_facility_audit"], allow_nan=False)


def test_two_lane_facility_default_app_calculates_with_inactive_opposing_nan() -> None:
    app = _open_facility_app()
    editor_key = _facility_editor_key(app)
    app.session_state[editor_key] = {
        "edited_rows": {
            0: {"opposing_direction_volume_veh_h": math.nan},
            1: {"opposing_direction_volume_veh_h": math.nan},
            2: {"opposing_direction_volume_veh_h": math.nan},
        },
        "added_rows": [],
        "deleted_rows": [],
    }

    app.button[1].click().run()

    assert not app.exception
    assert "Weighted average speed" in {metric.label for metric in app.metric}
    audit_rows = app.session_state["manual_facility_audit"]["facility_inputs"]["segments"]
    json.dumps(audit_rows, allow_nan=False)
    assert all(
        row["opposing_direction_volume_veh_h"] is None
        for row in audit_rows
        if row["segment_type"] != "passing_zone"
    )


def test_two_lane_facility_thai_result_has_localized_visible_surfaces() -> None:
    app = _open_facility_app("th")

    app.button[1].click().run()

    assert not app.exception
    assert translate("facility.title", "th") in str(app)
    metric_labels = {metric.label for metric in app.metric}
    assert translate("facility.average_speed", "th") in metric_labels
    assert translate("facility.length", "th") in metric_labels
    assert translate("facility.segment_count", "th") in metric_labels
    visible_labels = [
        *[button.label for button in app.button],
        *[button.label for button in app.download_button],
        *[select.label for select in app.selectbox],
        *[control.label for control in app.segmented_control],
        *[metric.label for metric in app.metric],
    ]
    for english in (
        "Calculate",
        "Facility template",
        "Unit system",
        "Facility length",
        "Save project",
        "Download facility result JSON",
    ):
        assert english not in visible_labels


def test_two_lane_facility_locale_switch_canonicalizes_unit_state() -> None:
    app = _open_facility_app()

    app.session_state["facility_unit_label"] = translate("facility.unit.metric", "th")
    app.selectbox[0].set_value("th").run()

    assert "unit_system must be metric or imperial" not in str(app)
    assert translate("facility.title", "th") in str(app)
    assert any(translate("facility.prerun", "th") in info.value for info in app.info)


def test_two_lane_facility_table_edit_stale_hides_metrics_and_blocks_exports() -> None:
    app = _open_facility_app()
    app.button[1].click().run()
    assert {metric.label for metric in app.metric}

    app.session_state[_facility_editor_key(app)] = {
        "edited_rows": {0: {"segment_length": 2.0}},
        "added_rows": [],
        "deleted_rows": [],
    }
    app.run()

    assert not app.exception
    assert any(translate("facility.stale", "en") in warning.value for warning in app.warning)
    assert not {metric.label for metric in app.metric}
    assert all(button.label != "Download CSV" for button in app.download_button)

    app.button[1].click().run()
    assert "Weighted average speed" in {metric.label for metric in app.metric}


def test_two_lane_facility_template_change_clears_current_result() -> None:
    app = _open_facility_app()
    app.button[1].click().run()
    assert {metric.label for metric in app.metric}

    app.selectbox[3].set_value("mountainous_example_4").run()

    assert not app.exception
    assert not {metric.label for metric in app.metric}
    assert any(translate("facility.prerun", "en") in info.value for info in app.info)

    app.button[1].click().run()
    assert {metric.label: metric.value for metric in app.metric}["Segments"] == "6"


def test_two_lane_facility_invalid_row_uses_typed_state_without_metrics() -> None:
    app = _open_facility_app()
    app.session_state[_facility_editor_key(app)] = {
        "edited_rows": {0: {"segment_length": 0.0}},
        "added_rows": [],
        "deleted_rows": [],
    }

    app.button[1].click().run()

    assert not app.exception
    assert any(translate("facility.invalid", "en") in error.value for error in app.error)
    assert any("Segment 1: segment_length" in caption.value for caption in app.caption)
    assert not {metric.label for metric in app.metric}


def test_two_lane_facility_unsupported_combination_has_no_false_result() -> None:
    app = _open_facility_app()
    app.session_state[_facility_editor_key(app)] = {
        "edited_rows": {
            0: {"segment_type": "passing_lane", "passing_lane_role": "none"}
        },
        "added_rows": [],
        "deleted_rows": [],
    }

    app.button[1].click().run()

    assert not app.exception
    assert any(translate("facility.unsupported", "en") in warning.value for warning in app.warning)
    assert not {metric.label for metric in app.metric}


def test_two_lane_facility_project_load_current_wrong_type_and_malformed_smoke() -> None:
    template = load_facility_template("level_example_3", "metric")
    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )
    project_json = create_manual_facility_project_json(
        template["template_id"],
        template["unit_system"],
        template["segments"],
        result=result_to_dict(result),
        audit_record=build_manual_facility_audit_record(
            template["template_id"],
            template["segments"],
            template["unit_system"],
            result=result,
        ),
        locale="th",
    )
    app = _open_facility_app()
    app.file_uploader[0].upload(
        "facility-project.json", project_json.encode("utf-8"), "application/json"
    ).run()
    app.button[0].click().run()
    app.run()

    assert not app.exception
    assert app.selectbox[0].value == "th"
    assert {metric.label for metric in app.metric}

    segment_json = create_manual_project_json(_two_lane_project_inputs())
    wrong_type = _open_facility_app("th")
    wrong_type.file_uploader[0].upload(
        "segment-project.json", segment_json.encode("utf-8"), "application/json"
    ).run()
    wrong_type.button[0].click().run()
    assert any(
        translate("facility.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in wrong_type.error
    )

    malformed = _open_facility_app("th")
    malformed.file_uploader[0].upload(
        "bad-project.json", b'{"project_type":"wrong"}', "application/json"
    ).run()
    malformed.button[0].click().run()
    assert any(
        translate("facility.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in malformed.error
    )


def test_two_lane_facility_navigation_isolation_from_segment_and_multilane() -> None:
    app = _open_facility_app()
    app.button[1].click().run()
    assert "Weighted average speed" in {metric.label for metric in app.metric}

    app.selectbox[2].set_value("manual_single_segment").run()

    assert not app.exception
    assert "Weighted average speed" not in {metric.label for metric in app.metric}

    app.selectbox[2].set_value("manual_multilane").run()

    assert not app.exception
    assert "Weighted average speed" not in {metric.label for metric in app.metric}


def test_multilane_streamlit_result_panel_uses_canonical_capacity_display_key() -> None:
    app = _open_multilane_app()

    app.button[1].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Speed used for density"] == "79.7 km/h"
    assert metrics["Demand flow rate"] == "895 pc/h/ln"
    assert metrics["Capacity"] == "1990 pc/h/ln"
    assert metrics["Capacity status"] == "Within capacity"
    assert "Adjusted capacity" not in metrics
    assert any("LOS C" in markdown.value for markdown in app.markdown)
    assert any("Density <strong>11.2 pc/km/ln</strong>" in markdown.value for markdown in app.markdown)

    app.number_input[6].set_value(1600.0)
    app.run()

    assert not app.exception
    assert any("Previous results are not current" in warning.value for warning in app.warning)
    assert not {metric.label for metric in app.metric}
    assert all(button.label != "Download CSV" for button in app.download_button)

    app.button[1].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Demand flow rate"] == "955 pc/h/ln"
    assert metrics["Capacity"] == "1990 pc/h/ln"

    app.segmented_control[0].set_value("imperial").run()

    assert not app.exception
    assert not {metric.label for metric in app.metric}
    assert all(button.label != "Download CSV" for button in app.download_button)


def test_multilane_streamlit_above_capacity_preserves_not_predicted_outputs() -> None:
    app = _open_multilane_app()
    app.number_input[6].set_value(10000.0)
    app.run()

    app.button[1].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Speed used for density"] == "Not predicted"
    assert metrics["Demand flow rate"] == "5969 pc/h/ln"
    assert metrics["Capacity"] == "1990 pc/h/ln"
    assert metrics["Capacity status"] == "Demand exceeds capacity"
    assert any("LOS F" in markdown.value for markdown in app.markdown)
    assert any("Density <strong>Not predicted</strong>" in markdown.value for markdown in app.markdown)
    assert any(button.label == "Download CSV" for button in app.download_button)


def test_multilane_thai_route_uses_localized_header_and_prerun_state() -> None:
    app = _open_multilane_app("th")

    assert not app.exception
    assert translate("multilane.title", "th") in str(app)
    assert any(translate("multilane.prerun", "th") in info.value for info in app.info)


def test_multilane_thai_stable_result_has_localized_key_surfaces() -> None:
    app = _open_multilane_app("th")

    app.button[1].click().run()

    assert not app.exception
    metric_labels = {metric.label for metric in app.metric}
    assert translate("multilane.speed_used_for_density", "th") in metric_labels
    assert translate("result.demand_flow_rate", "th") in metric_labels
    assert translate("result.capacity", "th") in metric_labels
    assert translate("multilane.capacity_check", "th") in metric_labels
    assert any(
        button.label == translate("multilane.save_project", "th")
        for button in app.download_button
    )
    visible_labels = [
        *[button.label for button in app.button],
        *[button.label for button in app.download_button],
        *[select.label for select in app.selectbox],
        *[control.label for control in app.segmented_control],
        *[metric.label for metric in app.metric],
    ]
    for english in (
        "Calculate",
        "Result summary",
        "Roadway geometry",
        "Capacity status",
        "Save project",
    ):
        assert english not in visible_labels


def test_multilane_unsupported_scope_uses_typed_state_without_traceback() -> None:
    app = _open_multilane_app()
    app.number_input[0].set_value(4).run()

    app.button[1].click().run()

    assert not app.exception
    assert any(
        "outside the implemented support envelope" in warning.value
        for warning in app.warning
    )
    assert not {metric.label for metric in app.metric}


def test_multilane_project_load_and_malformed_project_smoke() -> None:
    displayed = multilane_template_ui_inputs("MLH-CH26-004-EB", "metric")
    template = load_multilane_template("MLH-CH26-004-EB")
    normalized = multilane_ui_inputs_to_engine(displayed, template["inputs"], "metric")
    result = run_manual_multilane(normalized)
    project_json = create_manual_multilane_project_json(
        "MLH-CH26-004-EB",
        "metric",
        displayed,
        result=result_to_dict(result),
        audit_record=build_manual_multilane_audit_record(
            "MLH-CH26-004-EB",
            normalized,
            unit_system="metric",
            displayed_inputs=displayed,
            result=result,
        ),
        locale="th",
    )
    app = _open_multilane_app()
    app.file_uploader[0].upload(
        "multilane-project.json", project_json.encode("utf-8"), "application/json"
    ).run()
    app.button[0].click().run()

    assert not app.exception
    assert app.selectbox[0].value == "th"
    assert any(translate("project.load_current", "th") in success.value for success in app.success)

    malformed = _open_multilane_app("th")
    malformed.file_uploader[0].upload(
        "bad-project.json", b'{"project_type":"wrong"}', "application/json"
    ).run()
    malformed.button[0].click().run()

    assert not malformed.exception
    assert any(
        translate("multilane.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in malformed.error
    )


def test_freeway_streamlit_stable_english_result_and_exports() -> None:
    app = _open_freeway_app()

    app.button[1].click().run()

    assert not app.exception
    assert translate("freeway.title", "en") in str(app)
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Speed used for density"] == "97.8 km/h"
    assert metrics["Demand flow rate"] == "1141 pc/h/ln"
    assert metrics["Capacity"] == "2308 pc/h/ln"
    assert metrics["Capacity status"] == "Within capacity"
    assert metrics["FFS source"] == "estimated"
    assert any("LOS C" in markdown.value for markdown in app.markdown)
    assert any(
        "Density <strong>11.7 pc/km/ln</strong>" in markdown.value
        for markdown in app.markdown
    )
    assert any(button.label == "Download CSV" for button in app.download_button)
    assert any(button.label == "Download Excel" for button in app.download_button)
    assert any(button.label == "Download Markdown" for button in app.download_button)
    assert any(button.label == "Download Report JSON" for button in app.download_button)


def test_freeway_thai_result_has_localized_visible_surfaces() -> None:
    app = _open_freeway_app("th")

    app.button[1].click().run()

    assert not app.exception
    assert translate("freeway.title", "th") in str(app)
    metric_labels = {metric.label for metric in app.metric}
    assert translate("freeway.speed_used_for_density", "th") in metric_labels
    assert translate("result.demand_flow_rate", "th") in metric_labels
    assert translate("result.capacity", "th") in metric_labels
    assert translate("freeway.capacity_check", "th") in metric_labels
    visible_labels = [
        *[button.label for button in app.button],
        *[button.label for button in app.download_button],
        *[select.label for select in app.selectbox],
        *[control.label for control in app.segmented_control],
        *[metric.label for metric in app.metric],
    ]
    for english in (
        "Calculate",
        "Result summary",
        "Roadway geometry",
        "Capacity status",
        "Save project",
        "FFS mode",
    ):
        assert english not in visible_labels


def test_freeway_measured_ffs_mode_calculates_without_estimated_fields() -> None:
    app = _open_freeway_app()
    app.segmented_control[1].set_value("measured").run()

    assert "Measured FFS (km/h)" in {control.label for control in app.number_input}
    assert "Total ramp density (ramps/km)" not in {
        control.label for control in app.number_input
    }

    app.number_input[4].set_value(105.0).run()
    app.button[1].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["FFS source"] == "measured"
    assert metrics["Speed used for density"] == "105.0 km/h"


def test_freeway_estimated_ffs_mode_exposes_ramp_density_as_ffs_variable() -> None:
    app = _open_freeway_app()

    assert "Total ramp density (ramps/km)" in {
        control.label for control in app.number_input
    }
    assert any(
        translate("freeway.estimated_ffs_help", "en") in caption.value
        for caption in app.caption
    )

    app.button[1].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["FFS source"] == "estimated"


def test_freeway_stale_state_hides_metrics_and_blocks_report_exports() -> None:
    app = _open_freeway_app()
    app.button[1].click().run()

    app.number_input[2].set_value(2100.0).run()

    assert not app.exception
    assert any(translate("freeway.stale", "en") in warning.value for warning in app.warning)
    assert not {metric.label for metric in app.metric}
    assert all(button.label != "Download CSV" for button in app.download_button)

    app.button[1].click().run()
    assert {metric.label: metric.value for metric in app.metric}["Capacity"] == "2308 pc/h/ln"


def test_freeway_capacity_failure_preserves_current_exports_and_null_predictions() -> None:
    app = _open_freeway_app()
    app.number_input[2].set_value(20000.0).run()

    app.button[1].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Speed used for density"] == "Not predicted"
    assert metrics["Demand flow rate"] == "11413 pc/h/ln"
    assert metrics["Capacity"] == "2308 pc/h/ln"
    assert metrics["Capacity status"] == "Demand exceeds capacity"
    assert any("LOS F" in markdown.value for markdown in app.markdown)
    assert any(
        "Density <strong>Not predicted</strong>" in markdown.value
        for markdown in app.markdown
    )
    assert any(translate("freeway.capacity_failure", "en") in warning.value for warning in app.warning)
    assert any(button.label == "Download CSV" for button in app.download_button)


def test_freeway_invalid_input_uses_typed_state_without_metrics() -> None:
    app = _open_freeway_app()
    app.segmented_control[2].set_value("external").run()

    app.button[1].click().run()

    assert not app.exception
    assert any(translate("freeway.invalid", "en") in error.value for error in app.error)
    assert not {metric.label for metric in app.metric}


def test_freeway_unsupported_scope_uses_typed_state_without_traceback() -> None:
    app = _open_freeway_app()
    app.segmented_control[1].set_value("measured").run()

    app.button[1].click().run()

    assert not app.exception
    assert any(translate("freeway.unsupported", "en") in warning.value for warning in app.warning)
    assert not {metric.label for metric in app.metric}


def test_freeway_project_load_current_and_malformed_project_smoke() -> None:
    displayed = freeway_preset_ui_inputs("BF-CH26-001", "metric")
    preset = load_freeway_preset("BF-CH26-001")
    normalized = freeway_ui_inputs_to_engine(displayed, preset["inputs"], "metric")
    result = run_manual_freeway(normalized)
    project_json = create_manual_freeway_project_json(
        "BF-CH26-001",
        "metric",
        displayed,
        result=result_to_dict(result),
        audit_record=build_manual_freeway_audit_record(
            "BF-CH26-001",
            normalized,
            unit_system="metric",
            displayed_inputs=displayed,
            result=result,
        ),
        locale="th",
    )
    app = _open_freeway_app()
    app.file_uploader[0].upload(
        "freeway-project.json", project_json.encode("utf-8"), "application/json"
    ).run()
    app.button[0].click().run()

    assert not app.exception
    assert app.selectbox[0].value == "th"
    assert any(translate("project.load_current", "th") in success.value for success in app.success)

    malformed = _open_freeway_app("th")
    malformed.file_uploader[0].upload(
        "bad-project.json", b'{"project_type":"wrong"}', "application/json"
    ).run()
    malformed.button[0].click().run()

    assert not malformed.exception
    assert any(
        translate("freeway.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in malformed.error
    )


def test_freeway_navigation_isolation_from_multilane() -> None:
    app = _open_freeway_app()
    app.button[1].click().run()
    assert {metric.label for metric in app.metric}

    app.selectbox[1].set_value("roadways").run()
    app.selectbox[2].set_value("manual_multilane").run()

    assert not app.exception
    assert not {metric.label for metric in app.metric}
    assert any(translate("multilane.prerun", "en") in info.value for info in app.info)

    app.selectbox[1].set_value("freeways").run()
    app.selectbox[2].set_value("manual_basic_freeway").run()

    assert "Speed used for density" in {metric.label for metric in app.metric}


def test_merge_streamlit_stable_english_result_and_exports() -> None:
    app = _open_merge_app()

    assert translate("ramp.merge.title", "en") in str(app)
    assert any("Merge Segment configuration diagram" in markdown.value for markdown in app.markdown)

    app.button[0].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Ramp influence speed"] == "85.3 km/h"
    assert metrics["Downstream combined flow"] == "3541 pc/h"
    assert metrics["Governing capacity"] == "4600 pc/h"
    assert metrics["Capacity status"] == "Within capacity"
    assert metrics["FFS source"] == "measured"
    assert any("LOS D" in markdown.value for markdown in app.markdown)
    assert any("Density <strong>17.5 pc/km/ln</strong>" in markdown.value for markdown in app.markdown)
    assert any(button.label == "Download CSV" for button in app.download_button)
    assert any(button.label == "Download Excel" for button in app.download_button)
    assert any(button.label == "Download Markdown" for button in app.download_button)
    assert any(button.label == "Download Report JSON" for button in app.download_button)


def test_merge_thai_stable_result_has_localized_visible_surfaces() -> None:
    app = _open_merge_app("th")

    app.button[0].click().run()

    assert not app.exception
    assert translate("ramp.merge.title", "th") in str(app)
    metric_labels = {metric.label for metric in app.metric}
    assert translate("ramp.ramp_influence_speed", "th") in metric_labels
    assert translate("ramp.downstream_flow", "th") in metric_labels
    assert translate("ramp.capacity_status", "th") in metric_labels
    visible_labels = [
        *[button.label for button in app.button],
        *[button.label for button in app.download_button],
        *[select.label for select in app.selectbox],
        *[control.label for control in app.segmented_control],
        *[metric.label for metric in app.metric],
    ]
    for english in (
        "Run HCM 7.0 calculation",
        "Result summary",
        "Freeway geometry",
        "Capacity status",
        "Save project",
    ):
        assert english not in visible_labels


def test_merge_warning_only_preserves_valid_result_and_exports() -> None:
    app = _open_merge_app()
    app.number_input[0].set_value(182.88).run()
    app.number_input[1].set_value(3600.0).run()
    app.number_input[2].set_value(600.0).run()
    app.number_input[3].set_value(104.60736).run()
    app.number_input[4].set_value(64.37376).run()
    app.number_input[5].set_value(0.95).run()
    app.number_input[7].set_value(0.95).run()

    app.button[0].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Capacity status"] == "Within capacity"
    assert metrics["Ramp influence speed"] == "80.1 km/h"
    assert any("LOS E" in markdown.value for markdown in app.markdown)
    assert not any(translate("ramp.capacity_failure", "en") in warning.value for warning in app.warning)
    assert any("Maximum desirable influence-area flow warning" in info.value for info in app.info)
    assert any(button.label == "Download CSV" for button in app.download_button)


def test_merge_capacity_failure_preserves_exports_and_null_predictions() -> None:
    app = _open_merge_app()
    app.number_input[1].set_value(9000.0).run()

    app.button[0].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Ramp influence speed"] == "Not predicted"
    assert metrics["All-lanes speed"] == "Not predicted"
    assert metrics["Capacity status"] == "Demand exceeds capacity"
    assert metrics["Governing reason"] == "downstream_freeway_capacity"
    assert any("LOS F" in markdown.value for markdown in app.markdown)
    assert any("Density <strong>Not predicted</strong>" in markdown.value for markdown in app.markdown)
    assert any(translate("ramp.capacity_failure", "en") in warning.value for warning in app.warning)
    assert any(button.label == "Download CSV" for button in app.download_button)


def test_merge_stale_state_hides_metrics_and_blocks_report_exports() -> None:
    app = _open_merge_app()
    app.button[0].click().run()

    app.number_input[2].set_value(600.0).run()

    assert not app.exception
    assert any(translate("ramp.stale_info", "en") in warning.value for warning in app.warning)
    assert not {metric.label for metric in app.metric}
    assert all(button.label != "Download CSV" for button in app.download_button)

    app.button[0].click().run()
    assert {metric.label: metric.value for metric in app.metric}["Downstream combined flow"] == "3617 pc/h"


def test_merge_measured_and_estimated_ffs_modes_are_distinct() -> None:
    app = _open_merge_app()

    assert "Measured freeway FFS (km/h)" in {control.label for control in app.number_input}
    assert "Total ramp density (ramps/km)" not in {control.label for control in app.number_input}

    app.selectbox[5].set_value("estimated").run()

    labels = {control.label for control in app.number_input}
    assert "Measured freeway FFS (km/h)" not in labels
    assert "Base freeway FFS (km/h)" in labels
    assert "Total ramp density (ramps/km)" in labels
    assert "Ramp FFS (km/h)" in labels

    app.number_input[5].set_value(105.0).run()
    app.button[0].click().run()
    assert not app.exception
    assert {metric.label: metric.value for metric in app.metric}["FFS source"] == "estimated"


def test_merge_invalid_input_uses_typed_state_without_metrics() -> None:
    app = _open_merge_app()
    app.text_input[0].set_value("").run()

    app.button[0].click().run()

    assert not app.exception
    assert any(translate("ramp.invalid", "en") in error.value for error in app.error)
    assert not {metric.label for metric in app.metric}


def test_merge_project_load_current_hcm71_and_malformed_project_smoke() -> None:
    displayed = ramp_preset_ui_inputs("merge", "blank_custom", "metric")
    normalized = ramp_ui_inputs_to_engine("merge", displayed, "metric")
    result = run_manual_ramp("merge", normalized)
    project_json = create_manual_ramp_project_json(
        "merge",
        "blank_custom",
        "metric",
        displayed,
        result=result_to_dict(result),
        audit_record=build_manual_ramp_audit_record(
            "merge",
            "blank_custom",
            normalized,
            unit_system="metric",
            displayed_inputs=displayed,
            result=result,
        ),
        locale="th",
    )
    app = _open_merge_app()
    app.file_uploader[0].upload(
        "merge-project.json", project_json.encode("utf-8"), "application/json"
    ).run()
    app.button[0].click().run()

    assert not app.exception
    assert app.selectbox[0].value == "th"
    assert any(translate("project.load_current", "th") in success.value for success in app.success)

    hcm71_payload = json.loads(project_json)
    hcm71_payload["method_version"] = "hcm_7_1"
    hcm71 = _open_merge_app("th")
    hcm71.file_uploader[0].upload(
        "merge-hcm71-project.json",
        json.dumps(hcm71_payload).encode("utf-8"),
        "application/json",
    ).run()
    hcm71.button[0].click().run()

    assert not hcm71.exception
    assert any(
        translate("ramp.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in hcm71.error
    )

    malformed = _open_merge_app("th")
    malformed.file_uploader[0].upload(
        "bad-project.json", b'{"project_type":"wrong"}', "application/json"
    ).run()
    malformed.button[0].click().run()

    assert not malformed.exception
    assert any(
        translate("ramp.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in malformed.error
    )


def test_merge_navigation_isolation_from_basic_freeway() -> None:
    app = _open_merge_app()
    app.button[0].click().run()
    assert "Downstream combined flow" in {metric.label for metric in app.metric}

    app.selectbox[2].set_value("manual_basic_freeway").run()

    assert not app.exception
    assert not {metric.label for metric in app.metric}
    assert any(translate("freeway.prerun", "en") in info.value for info in app.info)

    app.selectbox[2].set_value("manual_merge").run()

    assert "Downstream combined flow" in {metric.label for metric in app.metric}


def test_diverge_streamlit_stable_english_result_and_exports() -> None:
    app = _open_diverge_app()

    assert translate("ramp.diverge.title", "en") in str(app)
    assert any("Diverge Segment configuration diagram" in markdown.value for markdown in app.markdown)
    assert any("LD 79.2 m" in caption.value for caption in app.caption)
    assert any("upstream freeway demand - off-ramp demand" in caption.value for caption in app.caption)

    app.button[0].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Ramp influence speed"] == "81.6 km/h"
    assert metrics["Continuing freeway flow"] == "6181 pc/h"
    assert metrics["Governing capacity"] == "9400 pc/h"
    assert metrics["Capacity status"] == "Within capacity"
    assert metrics["FFS source"] == "measured"
    assert any("LOS D" in markdown.value for markdown in app.markdown)
    assert any("Density <strong>19.3 pc/km/ln</strong>" in markdown.value for markdown in app.markdown)
    assert any(button.label == "Download CSV" for button in app.download_button)
    assert any(button.label == "Download Excel" for button in app.download_button)
    assert any(button.label == "Download Markdown" for button in app.download_button)
    assert any(button.label == "Download Report JSON" for button in app.download_button)


def test_diverge_thai_stable_result_has_localized_visible_surfaces() -> None:
    app = _open_diverge_app("th")

    app.button[0].click().run()

    assert not app.exception
    assert translate("ramp.diverge.title", "th") in str(app)
    metric_labels = {metric.label for metric in app.metric}
    assert translate("ramp.ramp_influence_speed", "th") in metric_labels
    assert translate("ramp.continuing_flow", "th") in metric_labels
    assert translate("ramp.capacity_status", "th") in metric_labels
    assert any(translate("ramp.diverge.diagram_title", "th") in markdown.value for markdown in app.markdown)
    visible_labels = [
        *[button.label for button in app.button],
        *[button.label for button in app.download_button],
        *[select.label for select in app.selectbox],
        *[control.label for control in app.segmented_control],
        *[metric.label for metric in app.metric],
    ]
    for english in (
        "Run HCM 7.0 calculation",
        "Result summary",
        "Freeway geometry",
        "Capacity status",
        "Save project",
        "Diverge Segment configuration diagram",
    ):
        assert english not in visible_labels


def test_diverge_warning_only_preserves_valid_result_and_exports() -> None:
    app = _open_diverge_app()
    app.selectbox[4].set_value(2).run()
    app.number_input[0].set_value(182.88).run()
    app.number_input[1].set_value(4000.0).run()
    app.number_input[2].set_value(200.0).run()
    app.number_input[3].set_value(104.60736).run()
    app.number_input[4].set_value(64.37376).run()
    app.number_input[5].set_value(0.95).run()
    app.number_input[7].set_value(0.95).run()

    app.button[0].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Capacity status"] == "Within capacity"
    assert metrics["Ramp influence speed"] == "90.4 km/h"
    assert metrics["Continuing freeway flow"] == "4400 pc/h"
    assert any("LOS E" in markdown.value for markdown in app.markdown)
    assert not any(translate("ramp.capacity_failure", "en") in warning.value for warning in app.warning)
    assert any("Maximum desirable influence-area flow warning" in info.value for info in app.info)
    assert any(button.label == "Download CSV" for button in app.download_button)


def test_diverge_capacity_failure_preserves_exports_and_null_predictions() -> None:
    app = _open_diverge_app()
    app.number_input[1].set_value(9000.0).run()

    app.button[0].click().run()

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Ramp influence speed"] == "Not predicted"
    assert metrics["All-lanes speed"] == "Not predicted"
    assert metrics["Capacity status"] == "Demand exceeds capacity"
    assert metrics["Governing reason"] == "upstream_freeway_capacity"
    assert any("LOS F" in markdown.value for markdown in app.markdown)
    assert any("Density <strong>Not predicted</strong>" in markdown.value for markdown in app.markdown)
    assert any(translate("ramp.capacity_failure", "en") in warning.value for warning in app.warning)
    assert any(button.label == "Download CSV" for button in app.download_button)


def test_diverge_invalid_continuing_demand_uses_typed_state_without_metrics() -> None:
    app = _open_diverge_app()
    app.number_input[2].set_value(6000.0).run()

    app.button[0].click().run()

    assert not app.exception
    assert any(translate("ramp.invalid", "en") in error.value for error in app.error)
    assert any(
        translate("ramp.diverge.invalid_continuing_detail", "en") in caption.value
        for caption in app.caption
    )
    assert not {metric.label for metric in app.metric}


def test_diverge_stale_state_hides_metrics_and_blocks_report_exports() -> None:
    app = _open_diverge_app()
    app.button[0].click().run()

    app.number_input[2].set_value(650.0).run()

    assert not app.exception
    assert any(translate("ramp.stale_info", "en") in warning.value for warning in app.warning)
    assert not {metric.label for metric in app.metric}
    assert all(button.label != "Download CSV" for button in app.download_button)

    app.button[0].click().run()
    assert {metric.label: metric.value for metric in app.metric}["Continuing freeway flow"] == "6122 pc/h"


def test_diverge_measured_and_estimated_ffs_modes_are_distinct() -> None:
    app = _open_diverge_app()

    assert "Measured freeway FFS (km/h)" in {control.label for control in app.number_input}
    assert "Total ramp density (ramps/km)" not in {control.label for control in app.number_input}
    assert "Ramp FFS (km/h)" in {control.label for control in app.number_input}

    app.selectbox[5].set_value("estimated").run()

    labels = {control.label for control in app.number_input}
    assert "Measured freeway FFS (km/h)" not in labels
    assert "Base freeway FFS (km/h)" in labels
    assert "Total ramp density (ramps/km)" in labels
    assert "Ramp FFS (km/h)" in labels

    app.number_input[5].set_value(105.0).run()
    app.button[0].click().run()
    assert not app.exception
    assert {metric.label: metric.value for metric in app.metric}["FFS source"] == "estimated"


def test_diverge_project_load_current_hcm71_adjacent_wrong_type_and_malformed_smoke() -> None:
    displayed = ramp_preset_ui_inputs("diverge", "blank_custom", "metric")
    normalized = ramp_ui_inputs_to_engine("diverge", displayed, "metric")
    result = run_manual_ramp("diverge", normalized)
    project_json = create_manual_ramp_project_json(
        "diverge",
        "blank_custom",
        "metric",
        displayed,
        result=result_to_dict(result),
        audit_record=build_manual_ramp_audit_record(
            "diverge",
            "blank_custom",
            normalized,
            unit_system="metric",
            displayed_inputs=displayed,
            result=result,
        ),
        locale="th",
    )
    app = _open_diverge_app()
    app.file_uploader[0].upload(
        "diverge-project.json", project_json.encode("utf-8"), "application/json"
    ).run()
    app.button[0].click().run()

    assert not app.exception
    assert app.selectbox[0].value == "th"
    assert any(translate("project.load_current", "th") in success.value for success in app.success)

    hcm71_payload = json.loads(project_json)
    hcm71_payload["method_version"] = "hcm_7_1"
    hcm71 = _open_diverge_app("th")
    hcm71.file_uploader[0].upload(
        "diverge-hcm71-project.json",
        json.dumps(hcm71_payload).encode("utf-8"),
        "application/json",
    ).run()
    hcm71.button[0].click().run()
    assert not hcm71.exception
    assert any(
        translate("ramp.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in hcm71.error
    )

    adjacent_payload = json.loads(project_json)
    adjacent_payload["normalized_engine_inputs"]["adjacent_ramp_context"] = "downstream_off_ramp"
    adjacent = _open_diverge_app("th")
    adjacent.file_uploader[0].upload(
        "diverge-adjacent-project.json",
        json.dumps(adjacent_payload).encode("utf-8"),
        "application/json",
    ).run()
    adjacent.button[0].click().run()
    assert not adjacent.exception
    assert any(
        translate("ramp.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in adjacent.error
    )

    merge_json = create_manual_ramp_project_json("merge", "blank_custom", "metric", displayed)
    wrong_type = _open_diverge_app("th")
    wrong_type.file_uploader[0].upload(
        "merge-project.json", merge_json.encode("utf-8"), "application/json"
    ).run()
    wrong_type.button[0].click().run()
    assert not wrong_type.exception
    assert any(
        translate("ramp.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in wrong_type.error
    )

    malformed = _open_diverge_app("th")
    malformed.file_uploader[0].upload(
        "bad-project.json", b'{"project_type":"wrong"}', "application/json"
    ).run()
    malformed.button[0].click().run()

    assert not malformed.exception
    assert any(
        translate("ramp.project_load_error", "th", error="").split(":")[0]
        in error.value
        for error in malformed.error
    )


def test_diverge_navigation_isolation_from_merge_and_basic_freeway() -> None:
    app = _open_diverge_app()
    app.button[0].click().run()
    assert "Continuing freeway flow" in {metric.label for metric in app.metric}

    app.selectbox[2].set_value("manual_merge").run()

    assert not app.exception
    assert not {metric.label for metric in app.metric}
    assert any(translate("ramp.prerun", "en") in info.value for info in app.info)

    app.selectbox[2].set_value("manual_basic_freeway").run()

    assert not app.exception
    assert not {metric.label for metric in app.metric}
    assert any(translate("freeway.prerun", "en") in info.value for info in app.info)

    app.selectbox[2].set_value("manual_diverge").run()

    assert "Continuing freeway flow" in {metric.label for metric in app.metric}
