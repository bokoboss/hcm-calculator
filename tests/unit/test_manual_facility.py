from copy import deepcopy

import pytest

from hcmcalc.core import MethodNotImplementedError
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    build_manual_facility_inputs,
    facility_segment_result_rows,
    facility_template_options,
    load_facility_template,
    run_manual_facility,
)


@pytest.mark.parametrize("template_id", facility_template_options())
def test_facility_templates_load_successfully(template_id: str) -> None:
    template = load_facility_template(template_id, "imperial")

    assert template["template_id"] == template_id
    assert template["segments"]
    assert template["template_source_reference"].startswith("HCM Chapter 26")
    assert template["template_basis"].startswith("Example Problem")
    assert template["supported_context"]
    assert template["safe_edit_summary"]
    assert template["locked_summary"]
    assert template["unsupported_behavior_notes"]


def test_example_3_like_template_matches_validated_facility_outputs() -> None:
    template = load_facility_template("level_example_3", "imperial")

    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )

    assert result.outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        7.3, abs=0.1
    )
    assert result.outputs["facility_level_of_service"] == "C"
    assert len(result.outputs["segments"]) == 5


def test_example_4_like_template_matches_validated_facility_outputs() -> None:
    template = load_facility_template("mountainous_example_4", "metric")

    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )

    assert result.outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        20.0, abs=0.1
    )
    assert result.outputs["facility_level_of_service"] == "E"
    assert len(result.outputs["segments"]) == 6


def test_facility_result_table_includes_segment_metrics_and_flags() -> None:
    template = load_facility_template("level_example_3", "imperial")
    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )

    rows = facility_segment_result_rows(result, template["segments"])

    assert rows[0]["segment_name"] == "Segment 1"
    assert rows[0]["average_speed_mph"]
    assert rows[0]["percent_followers"]
    assert rows[0]["follower_density_followers_mi_ln"]
    assert rows[0]["level_of_service"]
    assert rows[0]["vertical_class"] == 1
    assert rows[1]["passing_lane"] is True
    assert rows[2]["downstream_adjustment_applied"] is True


@pytest.mark.parametrize(
    ("template_id", "row_index", "field", "value"),
    [
        ("level_example_3", 0, "grade_percent", 4.0),
        ("level_example_3", 1, "segment_type", "passing_constrained"),
        ("level_example_3", 1, "passing_lane", False),
        ("level_example_3", 2, "downstream_affected", False),
        ("mountainous_example_4", 0, "segment_length", 2.0),
        ("mountainous_example_4", 0, "horizontal_alignment", "straight"),
    ],
)
def test_unsupported_template_edits_are_rejected(
    template_id: str, row_index: int, field: str, value: object
) -> None:
    template = load_facility_template(template_id, "imperial")
    rows = deepcopy(template["segments"])
    rows[row_index][field] = value

    with pytest.raises(MethodNotImplementedError, match="Unsupported combination"):
        build_manual_facility_inputs(template_id, rows, "imperial")


def test_arbitrary_nonlevel_facility_remains_unsupported() -> None:
    template = load_facility_template("level_example_3", "imperial")
    rows = deepcopy(template["segments"])
    rows[0]["terrain_type"] = "mountainous"
    rows[0]["grade_percent"] = 4.0

    with pytest.raises(MethodNotImplementedError, match="locked"):
        run_manual_facility(template["template_id"], rows, "imperial")


def test_arbitrary_passing_lane_facility_remains_unsupported() -> None:
    template = load_facility_template("level_example_3", "imperial")
    rows = deepcopy(template["segments"])
    rows[0]["segment_type"] = "passing_lane"
    rows[0]["passing_lane"] = True

    with pytest.raises(MethodNotImplementedError, match="locked"):
        run_manual_facility(template["template_id"], rows, "imperial")


def test_manual_downstream_adjustment_remains_unsupported() -> None:
    template = load_facility_template("level_example_3", "imperial")
    rows = deepcopy(template["segments"])
    rows[2]["manual_downstream_adjustment"] = True

    with pytest.raises(MethodNotImplementedError, match="manual downstream adjustment"):
        run_manual_facility(template["template_id"], rows, "imperial")


def test_facility_audit_contains_template_inputs_outputs_and_limitations() -> None:
    template = load_facility_template("level_example_3", "imperial")
    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )

    audit = build_manual_facility_audit_record(
        template["template_id"],
        template["segments"],
        template["unit_system"],
        result=result,
    )

    assert audit["calculation_type"] == "manual_facility_v0"
    assert audit["template_id"] == "level_example_3"
    assert audit["normalized_segment_inputs"]
    assert audit["segment_outputs"]
    assert audit["facility_outputs"]["facility_level_of_service"] == "C"
    assert audit["unsupported_behavior_notes"]
    assert audit["generated_at"]
    assert audit["app_version"]
