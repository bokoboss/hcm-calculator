from pathlib import Path

from fastapi.testclient import TestClient

from hcmcalc.api.main import (
    HASHED_ASSET_CACHE_CONTROL,
    SPA_SHELL_CACHE_CONTROL,
    create_app,
)


def _build_test_spa(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<html><body><div id='root'>cache-test</div></body></html>",
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index-AbCd1234.js").write_text(
        "console.log('cache-test')",
        encoding="utf-8",
    )


def test_spa_shell_is_not_stored_or_conditionally_reused(tmp_path: Path) -> None:
    _build_test_spa(tmp_path)
    client = TestClient(create_app(static_dir=tmp_path))

    root = client.get("/")
    assert root.status_code == 200
    assert root.headers["cache-control"] == SPA_SHELL_CACHE_CONTROL
    assert "etag" not in root.headers
    assert "last-modified" not in root.headers

    conditional = client.get("/", headers={"If-None-Match": '"stale-deployment"'})
    assert conditional.status_code == 200
    assert conditional.headers["cache-control"] == SPA_SHELL_CACHE_CONTROL
    assert "cache-test" in conditional.text

    deep_link = client.get("/reference/methods/multilane_segment")
    assert deep_link.status_code == 200
    assert deep_link.headers["cache-control"] == SPA_SHELL_CACHE_CONTROL
    assert "etag" not in deep_link.headers


def test_hashed_frontend_assets_are_long_lived_and_immutable(tmp_path: Path) -> None:
    _build_test_spa(tmp_path)
    client = TestClient(create_app(static_dir=tmp_path))

    asset = client.get("/assets/index-AbCd1234.js")
    assert asset.status_code == 200
    assert asset.headers["cache-control"] == HASHED_ASSET_CACHE_CONTROL
    assert asset.text == "console.log('cache-test')"

    missing_asset = client.get("/assets/index-OLDHASH.js")
    assert missing_asset.status_code == 404

    missing_api = client.get("/api/v1/not-a-route")
    assert missing_api.status_code == 404
    assert missing_api.headers["content-type"].startswith("application/json")
