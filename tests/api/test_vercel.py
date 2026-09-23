import importlib
import json
from pathlib import Path
import re
import tomllib

from fastapi.testclient import TestClient

from hcmcalc.api.vercel import app
from scripts.build_hosted_frontend import _sync_frontend_dist


def test_vercel_entrypoint_targets_source_adapter() -> None:
    with (Path(__file__).parents[2] / "pyproject.toml").open("rb") as file:
        entrypoint = tomllib.load(file)["tool"]["vercel"]["entrypoint"]
    module, name = entrypoint.split(":")

    assert module == "vercel_app"
    assert (Path(__file__).parents[2] / f"{module}.py").is_file()
    assert getattr(importlib.import_module(module), name) is app


def test_vercel_adapter_keeps_routes_and_reports_preview_identity(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL_ENV", "preview")
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "abc123")
    monkeypatch.setenv("VERCEL_DEPLOYMENT_ID", "dpl_test")

    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["application_version"]
    assert response.headers["x-hcmcalc-application-version"] == response.json()["application_version"]
    assert response.headers["x-hcmcalc-environment"] == "preview"
    assert response.headers["x-vercel-commit-sha"] == "abc123"
    assert response.headers["x-vercel-deployment-id"] == "dpl_test"
    root = client.get("/")
    assert root.status_code == 200
    assert '<div id="root"></div>' in root.text
    assert client.get("/reference/methods/multilane_segment").status_code == 200
    asset = re.search(r'(?:src|href)="(/assets/[^\"]+)"', root.text)
    assert asset and client.get(asset.group(1)).status_code == 200
    assert client.get("/engineering-assets/ramp_influence/merge_right_on_ramp.svg").status_code == 200
    missing_api = client.get("/api/v1/not-a-route")
    assert missing_api.status_code == 404
    assert missing_api.headers["content-type"].startswith("application/json")


def test_vercel_build_command_rebuilds_hosted_frontend() -> None:
    config_path = Path(__file__).parents[2] / "vercel.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["framework"] == "fastapi"
    assert config["buildCommand"] == "python scripts/build_hosted_frontend.py"


def test_hosted_frontend_sync_replaces_stale_packaged_bundle(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (assets / "index-NEW123.js").write_text("console.log('new')", encoding="utf-8")
    (assets / "index-NEW123.css").write_text("body{}", encoding="utf-8")
    (dist / "index.html").write_text(
        '<div id="root"></div>'
        '<script type="module" src="/assets/index-NEW123.js"></script>'
        '<link rel="stylesheet" href="/assets/index-NEW123.css">',
        encoding="utf-8",
    )

    target = tmp_path / "static"
    old_assets = target / "assets"
    old_assets.mkdir(parents=True)
    (old_assets / "index-OLD999.js").write_text("stale", encoding="utf-8")
    (target / "index.html").write_text(
        '<div id="root"></div><script src="/assets/index-OLD999.js"></script>',
        encoding="utf-8",
    )

    _sync_frontend_dist(dist, target)

    assert (target / "assets" / "index-NEW123.js").is_file()
    assert (target / "assets" / "index-NEW123.css").is_file()
    assert not (target / "assets" / "index-OLD999.js").exists()
    assert "index-NEW123.js" in (target / "index.html").read_text(encoding="utf-8")
