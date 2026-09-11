"""Vercel's source-layout ASGI bootstrap.

Vercel discovers this root module before installing the ``src``-layout package.
"""

from __future__ import annotations

from pathlib import Path
import sys


source_root = Path(__file__).resolve().parent / "src"
if str(source_root) not in sys.path:
    sys.path.insert(0, str(source_root))

from hcmcalc.api.vercel import app
