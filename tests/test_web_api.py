# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""web.app: the HTTP routes over a workspace (an empty folder, and the real files when present)."""

import os

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from pyxpcsviewer.web.app import build_app, trusted_hosts  # noqa: E402


def test_trusted_hosts():
    assert trusted_hosts("0.0.0.0") is None
    assert "localhost" in trusted_hosts("127.0.0.1") and "10.0.0.5" not in trusted_hosts("127.0.0.1")
    assert "10.0.0.5" in trusted_hosts("10.0.0.5")
    assert "[::1]" in trusted_hosts("::1")


def test_app_over_an_empty_folder(tmp_path):
    client = TestClient(build_app(str(tmp_path)), base_url="http://localhost")
    info = client.get("/api/info").json()
    assert info["root"] == str(tmp_path) and "viridis" in info["colormaps"]
    assert info["defaults"]["g2_bounds"]["single"][0] == [0.04, 1e-5, 0.5, 0.95]
    assert client.get("/api/files").json() == {"files": [], "total": 0, "version": 1}
    assert client.get("/api/colormaps").json()["jet"][0][0] == 0
    page = client.get("/")
    assert page.status_code == 200 and "pyXPCSViewer" in page.text
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/api/files/missing.hdf/summary").status_code == 404
    assert client.get("/api/files/..%2Fx.hdf/summary").status_code in (400, 404)
    assert client.get("/api/info", headers={"Host": "evil.example.com"}).status_code == 400
    assert client.post("/api/g2", json={"names": ["missing.hdf"]}).json() == {
        "files": [],
        "skipped": [{"file": "missing.hdf", "reason": "no such file: missing.hdf"}],
    }


def test_app_over_the_real_files(multitau_path, twotime_path):
    client = TestClient(build_app(os.path.dirname(multitau_path)), base_url="http://localhost")
    mt = os.path.basename(multitau_path)
    tt = os.path.basename(twotime_path)
    files = client.get("/api/files", params={"pattern": "multitau"}).json()
    assert [f["id"] for f in files["files"]] == [mt] and files["total"] == 1
    assert client.get(f"/api/files/{mt}/summary").json()["rows"][1] == ["Analysis", "Multitau"]
    image = client.get(f"/api/files/{mt}/image", params={"max_size": 256}).json()
    assert image["shape"] == [240, 229] and image["z"]["dtype"] == "f4"
    assert client.get(f"/api/files/{mt}/image", params={"kind": "nope"}).status_code == 400
    pixel = client.get(f"/api/files/{mt}/pixel", params={"x": 800, "y": 800}).json()
    assert pixel["on_detector"] and "q" in pixel
    g2 = client.post("/api/g2", json={"names": [mt, tt], "q_range": [0.004, 0.008]}).json()
    assert len(g2["files"]) == 1 and g2["skipped"][0]["file"] == tt
    fit = client.post("/api/g2/fit", json={"names": [mt], "fit_func": "single", "q_range": [0.004, 0.008]}).json()
    assert fit["files"][0]["fit"]["func"] == "single"
    tauq = client.post("/api/tauq", json={"names": [mt], "fit": True}).json()
    assert tauq["files"][0]["fit"]["b"] < 0
    assert client.post("/api/saxs1d", json={"names": [mt], "norm": "q4"}).json()["files"][0]["ylabel"].endswith("q^4")
    assert client.post("/api/saxs1d", json={"names": [mt], "norm": "bad"}).status_code == 400
    assert client.get(f"/api/files/{mt}/stability").json()["I"]["shape"] == [9, 360]
    assert client.get(f"/api/files/{mt}/g2_stability").status_code == 400
    assert client.post("/api/intt", json={"names": [mt], "window": 3}).json()["files"][0]["frames"] == 5000
    bins = client.get(f"/api/files/{tt}/twotime/bins").json()
    assert len(bins["bins"]) == 3
    c2 = client.get(f"/api/files/{tt}/twotime/c2", params={"selection": 2, "max_size": 128}).json()
    assert c2["qbin"] == 3 and max(c2["shape"]) <= 128
    assert client.get(f"/api/files/{tt}/twotime/c2", params={"selection": 9}).status_code == 400
    assert client.get(f"/api/files/{mt}/twotime/bins").status_code == 400
    assert client.get(f"/api/files/{tt}/hdf").json()["groups"]["/xpcs/twotime/config"]
