import json
from pathlib import Path

from hcmcalc.api.main import create_app


def test_committed_openapi_snapshot_matches_fastapi() -> None:
    snapshot = Path(__file__).parents[2] / "frontend" / "src" / "api" / "openapi.json"
    assert snapshot.is_file(), "Run scripts/check_openapi_contract.py --write to create the contract snapshot."
    expected = json.loads(snapshot.read_text(encoding="utf-8"))
    assert expected == create_app().openapi()
