"""Verify the Vercel ASGI entrypoint from an installed wheel, not ``src``."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> None:
    with (ROOT / "pyproject.toml").open("rb") as file:
        entrypoint = tomllib.load(file)["tool"]["vercel"]["entrypoint"]
    assert entrypoint == "hcmcalc.api.vercel:app"

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
        smoke = """
            import re
            from pathlib import Path
            from fastapi.testclient import TestClient
            import hcmcalc
            from hcmcalc.api.vercel import app

            installed = Path(hcmcalc.__file__).resolve()
            assert "site-packages" in installed.parts, installed
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
        _run([sys.executable, "-c", textwrap.dedent(smoke)], cwd=temporary_dir, env=environment)


if __name__ == "__main__":
    main()
