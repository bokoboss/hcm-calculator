from copy import deepcopy
from pathlib import Path

import pytest

from hcmcalc.two_lane.fixture_schema import (
    VerticalFixtureSchemaError,
    validate_vertical_fixture,
    validate_vertical_fixture_document,
)
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = ROOT / "src" / "hcmcalc" / "two_lane" / "data"
DATA_MANIFEST = DATA_DIRECTORY / "vertical_data_manifest.yaml"
FIXTURE_MANIFEST = DATA_DIRECTORY / "vertical_fixture_manifest.yaml"
FIXTURE_TEMPLATE = ROOT / "references" / "vertical_fixture_template.yaml"
BACKFILLED_FIXTURE = (
    ROOT / "references" / "vertical_fixtures" / "tlh_ch15_004_segment_3.yaml"
)
EXAMPLE_INPUTS = ROOT / "references" / "example_inputs.yaml"
EXPECTED_OUTPUTS = ROOT / "references" / "expected_outputs.yaml"

REQUIRED_DATASET_FIELDS = {
    "dataset_id",
    "chapter",
    "method_area",
    "data_type",
    "required_lookup_keys",
    "required_output_fields",
    "source_required",
    "source_reference",
    "copyright_status",
    "verification_status",
    "implementation_status",
    "runtime_status",
    "notes",
}


def _placeholder_fixture() -> dict:
    document = load_yaml_fixture(FIXTURE_TEMPLATE)
    return deepcopy(document["fixtures"][0])


def test_vertical_data_manifest_loads_with_required_metadata() -> None:
    manifest = load_yaml_fixture(DATA_MANIFEST)

    assert manifest["metadata"]["manifest_id"] == "ch15_vertical_data_requirements"
    assert manifest["metadata"]["runtime_enabled"] is False
    assert manifest["datasets"]
    for dataset in manifest["datasets"]:
        assert REQUIRED_DATASET_FIELDS <= dataset.keys()


def test_vertical_manifests_are_not_runtime_enabled() -> None:
    data_manifest = load_yaml_fixture(DATA_MANIFEST)
    fixture_manifest = load_yaml_fixture(FIXTURE_MANIFEST)

    assert all(
        dataset["runtime_status"] == "not_runtime_enabled"
        and dataset["implementation_status"] == "not_populated"
        for dataset in data_manifest["datasets"]
    )
    assert all(
        requirement["runtime_status"] == "not_runtime_enabled"
        and requirement["implementation_status"] == "not_populated"
        for requirement in fixture_manifest["fixture_requirements"]
    )


def test_fixture_manifest_references_existing_valid_fixture_documents() -> None:
    manifest = load_yaml_fixture(FIXTURE_MANIFEST)

    for entry in manifest["fixture_registry"]:
        fixture_path = ROOT / entry["fixture_path"]
        assert fixture_path.is_file()
        document = load_yaml_fixture(fixture_path)
        validate_vertical_fixture_document(document)
        assert entry["fixture_id"] in {
            fixture["fixture_id"] for fixture in document["fixtures"]
        }


def test_backfilled_manual_fixture_matches_existing_repository_validation_data() -> None:
    fixture = load_yaml_fixture(BACKFILLED_FIXTURE)["fixtures"][0]
    inputs_case = _case_by_id(load_yaml_fixture(EXAMPLE_INPUTS), "TLH-CH15-004")
    expected_case = _case_by_id(load_yaml_fixture(EXPECTED_OUTPUTS), "TLH-CH15-004")
    source_segment = inputs_case["inputs"]["segments"][2]
    expected_segment = expected_case["expected_outputs"]["segments"][2]

    validate_vertical_fixture(fixture)
    assert fixture["validation_status"] == "manual_single_segment_validated"
    assert fixture["verification_status"] == "verified"
    assert fixture["runtime_status"] == "runtime_validated"
    assert fixture["implementation_status"] == "existing_runtime_support"
    assert fixture["segment_type"] == source_segment["segment_type"]
    assert fixture["horizontal_alignment"] == source_segment["horizontal_alignment"]
    assert fixture["grade_percent"] == source_segment["grade_percent"]
    assert fixture["grade_length"]["value"] == source_segment["segment_length_mi"]
    assert fixture["heavy_vehicle_percent"] == source_segment["heavy_vehicle_percent"]
    assert fixture["inputs"] == {
        "segment_length_mi": source_segment["segment_length_mi"],
        "posted_speed_mph": source_segment["posted_speed_mph"],
        "analysis_direction_volume_veh_h": source_segment[
            "analysis_direction_volume_veh_h"
        ],
        "peak_hour_factor": source_segment["peak_hour_factor"],
        "lane_width_ft": source_segment["lane_width_ft"],
        "shoulder_width_ft": source_segment["shoulder_width_ft"],
        "access_point_density_per_mi": source_segment[
            "access_point_density_per_mi"
        ],
    }
    assert fixture["expected_outputs"] == expected_segment
    assert fixture["tolerance"] == expected_case["tolerances"]


def test_fixture_manifest_distinguishes_validated_backfill_from_template() -> None:
    registry = load_yaml_fixture(FIXTURE_MANIFEST)["fixture_registry"]
    entries = {entry["fixture_id"]: entry for entry in registry}

    validated = entries["TLH-CH15-004-SEGMENT-3"]
    assert validated["validation_status"] == "manual_single_segment_validated"
    assert validated["runtime_status"] == "runtime_validated"

    template = entries["PLACEHOLDER-CH15-VERTICAL-001"]
    assert template["validation_status"] == "template_only"
    assert template["runtime_status"] == "not_runtime_enabled"


def test_vertical_fixture_template_loads_and_validates() -> None:
    document = load_yaml_fixture(FIXTURE_TEMPLATE)

    assert document["metadata"]["status"] == "placeholder_template"
    assert document["metadata"]["runtime_enabled"] is False
    validate_vertical_fixture_document(document)


def test_fixture_schema_accepts_structurally_valid_placeholder() -> None:
    validate_vertical_fixture(_placeholder_fixture())


def test_fixture_schema_accepts_existing_runtime_validated_fixture() -> None:
    fixture = load_yaml_fixture(BACKFILLED_FIXTURE)["fixtures"][0]

    validate_vertical_fixture(fixture)


def test_fixture_schema_rejects_missing_source_reference() -> None:
    fixture = _placeholder_fixture()
    fixture.pop("source_reference")

    with pytest.raises(VerticalFixtureSchemaError, match="source_reference"):
        validate_vertical_fixture(fixture)


def test_fixture_schema_rejects_missing_expected_outputs() -> None:
    fixture = _placeholder_fixture()
    fixture.pop("expected_outputs")

    with pytest.raises(VerticalFixtureSchemaError, match="expected_outputs"):
        validate_vertical_fixture(fixture)


def test_fixture_schema_rejects_missing_tolerance() -> None:
    fixture = _placeholder_fixture()
    fixture.pop("tolerance")

    with pytest.raises(VerticalFixtureSchemaError, match="tolerance"):
        validate_vertical_fixture(fixture)


@pytest.mark.parametrize("verification_status", ["unverified", "data_required"])
def test_fixture_schema_rejects_runtime_enabled_unverified_fixture(
    verification_status: str,
) -> None:
    fixture = _placeholder_fixture()
    fixture["placeholder"] = False
    fixture["verification_status"] = verification_status
    fixture["runtime_status"] = "runtime_enabled"

    with pytest.raises(VerticalFixtureSchemaError, match="cannot be runtime enabled"):
        validate_vertical_fixture(fixture)


def test_fixture_schema_rejects_runtime_enabled_placeholder_fixture() -> None:
    fixture = _placeholder_fixture()
    fixture["verification_status"] = "verified"
    fixture["runtime_status"] = "runtime_validated"

    with pytest.raises(VerticalFixtureSchemaError, match="cannot be runtime enabled"):
        validate_vertical_fixture(fixture)


def test_fixture_schema_rejects_runtime_enabled_without_validated_status() -> None:
    fixture = _placeholder_fixture()
    fixture["placeholder"] = False
    fixture["verification_status"] = "verified"
    fixture["validation_status"] = "reviewed"
    fixture["runtime_status"] = "runtime_validated"

    with pytest.raises(VerticalFixtureSchemaError, match="cannot be runtime enabled"):
        validate_vertical_fixture(fixture)


def _case_by_id(fixture: dict, case_id: str) -> dict:
    return next(case for case in fixture["cases"] if case["id"] == case_id)
