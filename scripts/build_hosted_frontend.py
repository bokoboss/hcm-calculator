"""Build and synchronize the React SPA for hosted Vercel deployments.

The FastAPI application can serve either a freshly built frontend/dist tree
or the packaged fallback under src/hcmcalc/ui/static. Hosted deployments
must never silently fall back to an older committed SPA, so Vercel runs this
script before packaging the Python function.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
PACKAGED_STATIC_DIR = ROOT / "src" / "hcmcalc" / "ui" / "static"
ASSET_PATTERN = re.compile(r'(?:src|href)="(/assets/[^"]+)"')


def _pnpm_spec() -> str:
    package = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
    package_manager = str(package.get("packageManager", "")).strip()
    if not package_manager.startswith("pnpm@"):
        raise RuntimeError("frontend/package.json must pin packageManager to pnpm@<version>.")
    return package_manager


def _validate_frontend_dist(dist_dir: Path) -> None:
    index = dist_dir / "index.html"
    if not index.is_file():
        raise RuntimeError(f"Frontend build did not create {index}.")

    html = index.read_text(encoding="utf-8")
    if '<div id="root"></div>' not in html:
        raise RuntimeError("Frontend index is missing the React root element.")

    asset_paths = ASSET_PATTERN.findall(html)
    if not asset_paths:
        raise RuntimeError("Frontend index does not reference a hashed Vite asset.")

    for asset_path in asset_paths:
        asset = dist_dir / asset_path.removeprefix("/")
        if not asset.is_file():
            raise RuntimeError(f"Frontend index references missing asset: {asset_path}")


def _sync_frontend_dist(dist_dir: Path, target_dir: Path) -> None:
    _validate_frontend_dist(dist_dir)

    staging = target_dir.with_name(f".{target_dir.name}.staging")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(dist_dir, staging)
    _validate_frontend_dist(staging)

    if target_dir.exists():
        shutil.rmtree(target_dir)
    staging.replace(target_dir)


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise RuntimeError("npx is required to build the hosted React frontend.")

    pnpm = _pnpm_spec()
    _run([npx, "--yes", pnpm, "install", "--frozen-lockfile"], cwd=FRONTEND_DIR)
    _run([npx, "--yes", pnpm, "build"], cwd=FRONTEND_DIR)
    _sync_frontend_dist(DIST_DIR, PACKAGED_STATIC_DIR)

    print(
        "Hosted frontend ready: "
        f"{DIST_DIR.relative_to(ROOT)} -> {PACKAGED_STATIC_DIR.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
