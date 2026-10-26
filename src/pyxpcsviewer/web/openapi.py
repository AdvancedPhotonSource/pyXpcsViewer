# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""The committed API document, ``openapi.json`` beside this module, and its export.

``pyxpcsviewer-web --export-openapi FILE`` writes it; the web monorepo copies it into ``apps/xpcs``
and generates the TypeScript types from it; ``tests/test_web_openapi.py`` fails when the committed
copy is stale, so a pull request that changes the API regenerates it in the same change.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from beamline_webkit.openapi import openapi_text as render_openapi

from .app import API_SCHEMA_VERSION, build_app

OPENAPI_PATH = Path(__file__).parent / "openapi.json"


def openapi_text() -> str:
    """The API document as committed text: sorted keys, 2-space indent, the schema version in
    ``info.version`` (not the package version, which changes with every release)."""
    with tempfile.TemporaryDirectory() as empty_folder:
        return render_openapi(build_app(empty_folder), schema_version=API_SCHEMA_VERSION)


def export_openapi(path: str | Path = OPENAPI_PATH) -> Path:
    """Write :func:`openapi_text` to ``path`` (by default the committed copy) and return the path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(openapi_text(), encoding="utf-8")
    return target
