import json
from io import StringIO
from pathlib import Path

import pytest
import yaml

from hcmcalc.cli import main


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_INPUTS = ROOT / "references" / "example_inputs.yaml"


def test_run_example_1_returns_json_with_expected_los(capsys) -> None:
    exit_code = main(["run", str(EXAMPLE_INPUTS), "--case", "TLH-CH15-001"])

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert exit_code == 0
    assert result["outputs"]["level_of_service"] == "D"
    assert isinstance(result["outputs"]["follower_density_followers_mi_ln"], float)
    assert captured.err == ""


def test_run_example_4_returns_expected_facility_results(capsys) -> None:
    exit_code = main(["run", str(EXAMPLE_INPUTS), "--case", "TLH-CH15-004"])

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert exit_code == 0
    assert result["outputs"]["facility_level_of_service"] == "E"
    assert result["outputs"]["facility_follower_density_followers_mi_ln"] == pytest.approx(
        20.0, abs=0.1
    )


def test_unknown_case_id_returns_nonzero(capsys) -> None:
    exit_code = main(["run", str(EXAMPLE_INPUTS), "--case", "UNKNOWN"])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert captured.out == ""
    assert "Case id not found: UNKNOWN" in captured.err


def test_missing_file_returns_nonzero(capsys) -> None:
    missing_file = ROOT / "references" / "missing.yaml"

    exit_code = main(["run", str(missing_file), "--case", "TLH-CH15-001"])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert captured.out == ""
    assert "Input file does not exist" in captured.err


def test_run_json_fixture_returns_json(capsys, monkeypatch) -> None:
    fixture = yaml.safe_load(EXAMPLE_INPUTS.read_text(encoding="utf-8"))
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    monkeypatch.setattr(
        Path, "open", lambda self, *args, **kwargs: StringIO(json.dumps(fixture))
    )

    exit_code = main(["run", "example_inputs.json", "--case", "TLH-CH15-001"])

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert exit_code == 0
    assert result["outputs"]["level_of_service"] == "D"


def test_malformed_file_returns_nonzero(capsys, monkeypatch) -> None:
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    monkeypatch.setattr(
        Path, "open", lambda self, *args, **kwargs: StringIO('{"cases": [')
    )

    exit_code = main(["run", "malformed.json", "--case", "TLH-CH15-001"])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert captured.out == ""
    assert "Input file is malformed" in captured.err
