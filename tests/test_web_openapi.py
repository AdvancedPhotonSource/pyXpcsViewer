# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""web.openapi: the committed API document is current, and the export command writes it."""

import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("beamline_webkit")

from pyxpcsviewer.web.app import API_SCHEMA_VERSION
from pyxpcsviewer.web.openapi import OPENAPI_PATH, export_openapi, openapi_text


def test_committed_document_is_current():
    assert OPENAPI_PATH.read_text(encoding="utf-8") == openapi_text(), (
        "src/pyxpcsviewer/web/openapi.json is stale: run "
        "`pyxpcsviewer-web --export-openapi src/pyxpcsviewer/web/openapi.json` and commit it"
    )


def test_document_shape():
    doc = json.loads(openapi_text())
    assert doc["info"]["version"] == API_SCHEMA_VERSION
    assert doc["info"]["title"] == "pyXPCSViewer web"
    api_paths = [path for path in doc["paths"] if path.startswith("/api/")]
    assert len(api_paths) == 23
    assert {"/api/info", "/api/files/{name}/image", "/api/files/{name}/twotime/c2", "/api/g2/fit"} <= set(api_paths)
    assert openapi_text() == openapi_text(), "the export is deterministic"
    # every API route declares its answer: a response model, or a binary body with its headers
    binary = {"/api/files/{name}/image/data", "/api/files/{name}/g2/data", "/api/files/{name}/twotime/c2/data"}
    for path in api_paths:
        for operation in doc["paths"][path].values():
            answer = operation["responses"]["200"]
            if path in binary:
                assert "application/octet-stream" in answer["content"], path
                assert {"X-Array-Shape", "X-Array-Dtype", "X-Array-Meta"} <= set(answer["headers"]), path
            else:
                assert "$ref" in answer["content"]["application/json"]["schema"], f"{path} has no response model"
    assert "schema_version" in doc["components"]["schemas"]["Info"]["properties"]
    assert {"ImageMeta", "G2Meta", "C2Meta", "Geometry"} <= set(doc["components"]["schemas"])


def test_export_writes_the_same_text(tmp_path):
    out = export_openapi(tmp_path / "nested" / "openapi.json")
    assert out.read_text(encoding="utf-8") == openapi_text()


def test_cli_export(tmp_path, capsys):
    from pyxpcsviewer.web.cli import main

    target = tmp_path / "x" / "openapi.json"
    assert main(["--export-openapi", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == openapi_text()
    assert main(["--export-openapi", "-"]) == 0
    assert capsys.readouterr().out == openapi_text()
