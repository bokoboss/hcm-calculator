from pathlib import Path

from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def test_placeholder_validation_fixtures_load() -> None:
    inputs = load_yaml_fixture(ROOT / "references" / "example_inputs.yaml")
    expected = load_yaml_fixture(ROOT / "references" / "expected_outputs.yaml")

    assert inputs["metadata"]["status"] == "scaffold_only"
    assert expected["metadata"]["status"] == "scaffold_only"
    assert inputs["cases"][0]["id"] == expected["cases"][0]["id"]
