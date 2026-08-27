"""FastAPI application factory and loopback-safe local static serving."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from hcmcalc import __version__
from hcmcalc.api.routes.health import router as health_router
from hcmcalc.api.routes.methods import router as methods_router


API_VERSION = "v1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def create_app(
    *,
    static_dir: str | Path | None = None,
    allow_dev_origins: Sequence[str] = (),
) -> FastAPI:
    """Create the API boundary without starting a server.

    CORS is absent by default.  Development callers may provide an explicit
    allowlist; wildcard origins are rejected so a local API cannot silently
    become broadly cross-origin accessible.
    """

    origins = tuple(allow_dev_origins)
    if "*" in origins:
        raise ValueError("Wildcard CORS is not permitted for the local API.")

    app = FastAPI(
        title="HCM Calculator API",
        version=API_VERSION,
        description="Local application boundary for the rebuilt HCM workspace.",
    )
    app.include_router(health_router)
    app.include_router(methods_router)

    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(origins),
            allow_credentials=False,
            allow_methods=["GET"],
            allow_headers=["Accept", "Content-Type"],
        )

    resolved_static_dir = _resolve_static_dir(static_dir)
    if resolved_static_dir is not None:
        _mount_compiled_spa(app, resolved_static_dir)
    else:
        @app.get("/", include_in_schema=False)
        def runtime_without_frontend() -> JSONResponse:
            return JSONResponse(
                {
                    "service": "hcmcalc-api",
                    "api_version": API_VERSION,
                    "application_version": __version__,
                    "frontend": "not_built",
                }
            )

    return app


def _resolve_static_dir(static_dir: str | Path | None) -> Path | None:
    if static_dir is None:
        import os

        configured = os.environ.get("HCMCALC_FRONTEND_DIST")
        candidate = Path(configured) if configured else Path(__file__).resolve().parents[3] / "frontend" / "dist"
    else:
        candidate = Path(static_dir)
    candidate = candidate.resolve()
    return candidate if (candidate / "index.html").is_file() else None


def _mount_compiled_spa(app: FastAPI, static_dir: Path) -> None:
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    def compiled_root() -> FileResponse:
        return FileResponse(static_dir / "index.html", media_type="text/html")

    @app.get("/{path:path}", include_in_schema=False)
    def compiled_spa_fallback(path: str) -> FileResponse:
        """Serve the SPA entry for client-side routes.

        API and asset routes are registered before this fallback.  The R1 shell
        has no user-uploaded filesystem route, so arbitrary project content is
        never executed or exposed by this handler.
        """

        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        return FileResponse(static_dir / "index.html", media_type="text/html")


def serve(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    static_dir: str | Path | None = None,
) -> None:
    """Run the local release-like server, loopback-bound by default."""

    import uvicorn

    uvicorn.run(create_app(static_dir=static_dir), host=host, port=port)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local HCM Calculator API.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--static-dir", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    serve(host=args.host, port=args.port, static_dir=args.static_dir)
