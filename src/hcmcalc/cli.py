"""Command-line runner for validated HCM calculation fixtures."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any, Sequence

import yaml

from hcmcalc.core import CalculationResult, HCMCalcError
from hcmcalc.methods import get_method


class CLIInputError(HCMCalcError):
    """Raised when a CLI input file cannot supply a runnable case."""


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(prog="hcmcalc")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run a validated fixture case")
    run_parser.add_argument("input_file", type=Path)
    run_parser.add_argument("--case", dest="case_id", required=True)
    return parser


def load_input_file(path: Path) -> dict[str, Any]:
    """Load a YAML or JSON fixture file."""

    if not path.is_file():
        raise CLIInputError(f"Input file does not exist: {path}")

    try:
        with path.open("r", encoding="utf-8") as input_file:
            if path.suffix.lower() == ".json":
                loaded = json.load(input_file)
            else:
                loaded = yaml.safe_load(input_file)
    except (json.JSONDecodeError, yaml.YAMLError, UnicodeDecodeError) as exc:
        raise CLIInputError(f"Input file is malformed: {path}: {exc}") from exc
    except OSError as exc:
        raise CLIInputError(f"Could not read input file: {path}: {exc}") from exc

    if not isinstance(loaded, dict) or not isinstance(loaded.get("cases"), list):
        raise CLIInputError(
            f"Input file is malformed: {path}: expected a top-level cases list."
        )
    return loaded


def find_case(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
    """Find a case by id in a validation fixture."""

    for case in fixture["cases"]:
        if isinstance(case, dict) and case.get("id") == case_id:
            return case
    raise CLIInputError(f"Case id not found: {case_id}")


def run_case(case: dict[str, Any]) -> CalculationResult:
    """Dispatch a fixture case to its registered calculation method."""

    try:
        method_key = case["method"]
        facility_type = case["facility_type"]
        inputs = case["inputs"]
    except KeyError as exc:
        raise CLIInputError(f"Selected case is malformed: missing {exc.args[0]}.") from exc

    if not all(isinstance(value, str) for value in (method_key, facility_type)):
        raise CLIInputError(
            "Selected case is malformed: method and facility_type must be strings."
        )
    if not isinstance(inputs, dict):
        raise CLIInputError("Selected case is malformed: inputs must be an object.")

    return get_method(method_key, facility_type).calculate(inputs)


def result_to_dict(result: CalculationResult) -> dict[str, Any]:
    """Convert an auditable calculation result to stable JSON-ready data."""

    result_data = asdict(result)
    return {
        "method": result_data["method"],
        "facility_type": result_data["facility_type"],
        "outputs": result_data["outputs"],
        "intermediate_values": result_data["intermediate_values"],
        "assumptions": result_data["assumptions"],
        "warnings": result_data["warnings"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return a process exit code."""

    args = build_parser().parse_args(argv)
    try:
        fixture = load_input_file(args.input_file)
        case = find_case(fixture, args.case_id)
        result = run_case(case)
    except HCMCalcError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result_to_dict(result), indent=2))
    return 0
