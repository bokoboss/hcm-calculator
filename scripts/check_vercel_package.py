"""Verify Vercel's source entrypoint and the installed package adapter."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ENTRYPOINT = "hcmcalc.api.vercel:app"

HTTP_SMOKE = """
    import re
    from fastapi.testclient import TestClient

    client = TestClient(app)
    root = client.get("/")
    assert root.status_code == 200 and '<div id="root"></div>' in root.text
    assert client.get("/reference/methods/multilane_segment").status_code == 200
    asset = re.search(r'(?:src|href)="(/assets/[^\"]+)"', root.text)
    assert asset and client.get(asset.group(1)).status_code == 200
    assert client.get("/engineering-assets/ramp_influence/merge_right_on_ramp.svg").status_code == 200
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    missing = client.get("/api/v1/not-a-route")
    assert missing.status_code == 404 and missing.headers["content-type"].startswith("application/json")
"""


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _smoke(entrypoint: str, *, installed: bool = False) -> str:
    module, name = entrypoint.split(":")
    package_check = ""
    if installed:
        package_check = "import hcmcalc\nfrom pathlib import Path\nassert 'site-packages' in Path(hcmcalc.__file__).resolve().parts\n"
    return textwrap.dedent(
        f"import importlib\n{package_check}app = getattr(importlib.import_module({module!r}), {name!r})\n"
    ) + textwrap.dedent(HTTP_SMOKE)


def main() -> None:
    with (ROOT / "pyproject.toml").open("rb") as file:
        entrypoint = tomllib.load(file)["tool"]["vercel"]["entrypoint"]
    module, _ = entrypoint.split(":")
    assert (ROOT.joinpath(*module.split(".")).with_suffix(".py")).is_file()

    source_environment = os.environ.copy()
    source_environment.pop("PYTHONPATH", None)
    source_environment.pop("HCMCALC_FRONTEND_DIST", None)
    _run([sys.executable, "-c", _smoke(entrypoint)], cwd=ROOT, env=source_environment)

    scratch_dir = ROOT / ".tmp"
    scratch_dir.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(scratch_dir)
    os.environ["TMP"] = str(scratch_dir)
    os.environ["TMPDIR"] = str(scratch_dir)
    with tempfile.TemporaryDirectory(dir=scratch_dir, ignore_cleanup_errors=True) as temporary:
        temporary_dir = Path(temporary)
        environment = os.environ.copy()
        environment["TEMP"] = str(temporary_dir)
        environment["TMP"] = str(temporary_dir)
        environment["TMPDIR"] = str(temporary_dir)
        wheel_dir = temporary_dir / "wheel"
        _run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(wheel_dir)],
            cwd=ROOT,
            env=environment,
        )
        wheel = next(wheel_dir.glob("hcm_calculator-*.whl"))

        installed_dir = temporary_dir / "site-packages"
        _run(
            [sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(installed_dir), str(wheel)],
            cwd=temporary_dir,
            env=environment,
        )

        environment.pop("PYTHONPATH", None)
        environment.pop("HCMCALC_FRONTEND_DIST", None)
        environment["PYTHONPATH"] = str(installed_dir)
        _run(
            [sys.executable, "-c", _smoke(PACKAGE_ENTRYPOINT, installed=True)],
            cwd=temporary_dir,
            env=environment,
        )


if __name__ == "__main__":
    main()
