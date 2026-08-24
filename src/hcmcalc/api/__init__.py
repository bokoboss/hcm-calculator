"""Thin FastAPI boundary for the rebuilt HCM workspace."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import API_VERSION, DEFAULT_HOST, create_app

__all__ = ["API_VERSION", "DEFAULT_HOST", "create_app"]


def __getattr__(name: str):
    """Load the server module lazily so ``python -m hcmcalc.api.main`` is clean."""

    if name in __all__:
        from .main import API_VERSION, DEFAULT_HOST, create_app

        return {
            "API_VERSION": API_VERSION,
            "DEFAULT_HOST": DEFAULT_HOST,
            "create_app": create_app,
        }[name]
    raise AttributeError(name)
