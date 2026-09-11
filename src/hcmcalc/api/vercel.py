"""Vercel's importable ASGI adapter for the existing FastAPI application."""

from __future__ import annotations

import os

from fastapi import Request

from hcmcalc import __version__
from hcmcalc.api.main import create_app


app = create_app()


@app.middleware("http")
async def add_runtime_traceability(request: Request, call_next):
    """Expose non-sensitive deployment identity without changing API bodies."""

    response = await call_next(request)
    response.headers["X-HCMCalc-Application-Version"] = __version__
    response.headers["X-HCMCalc-Environment"] = os.environ.get("VERCEL_ENV", "local")
    for variable, header in (
        ("VERCEL_GIT_COMMIT_SHA", "X-Vercel-Commit-SHA"),
        ("VERCEL_DEPLOYMENT_ID", "X-Vercel-Deployment-ID"),
    ):
        value = os.environ.get(variable)
        if value:
            response.headers[header] = value
    return response
