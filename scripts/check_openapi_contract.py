"""Check the committed frontend OpenAPI snapshot against FastAPI."""

from __future__ import annotations

import argparse
from difflib import unified_diff
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "frontend" / "src" / "api" / "openapi.json"


def generated_contract() -> dict[str, object]:
    from hcmcalc.api.main import create_app

    return create_app().openapi()


def serialized(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="refresh the committed snapshot")
    args = parser.parse_args()

    expected = serialized(generated_contract())
    if args.write:
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(expected, encoding="utf-8")
        print(f"Wrote {SNAPSHOT}")
        return 0

    if not SNAPSHOT.exists():
        print(f"Missing OpenAPI snapshot: {SNAPSHOT}", file=sys.stderr)
        return 1
    actual = SNAPSHOT.read_text(encoding="utf-8")
    if actual == expected:
        print("OpenAPI snapshot matches FastAPI application.")
        return 0

    diff = unified_diff(
        actual.splitlines(), expected.splitlines(),
        fromfile=str(SNAPSHOT), tofile="generated FastAPI OpenAPI",
        lineterm="",
    )
    print("\n".join(diff), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
