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


def test_vertical_fixture_template_loads_and_validates() -> None:
    document = load_yaml_fixture(FIXTURE_TEMPLATE)

    assert document["metadata"]["status"] == "placeholder_template"
    assert document["metadata"]["runtime_enabled"] is False
    validate_vertical_fixture_document(document)


def test_fixture_schema_accepts_structurally_valid_placeholder() -> None:
    validate_vertical_fixture(_placeholder_fixture())


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
