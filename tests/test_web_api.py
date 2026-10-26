# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""web.app: the HTTP routes over a workspace (an empty folder, and the real files when present)."""

import os

import numpy as np
import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("beamline_webkit")
from beamline_webkit.testing import array_of, meta_of  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from pyxpcsviewer.web.app import build_app  # noqa: E402

PAGE_A = {"X-Session-Id": "page-aaaaaaaa"}
PAGE_B = {"X-Session-Id": "page-bbbbbbbb"}


def test_app_over_an_empty_folder(tmp_path):
    client = TestClient(build_app(str(tmp_path)), base_url="http://localhost")
    info = client.get("/api/info").json()
    assert info["root"] == str(tmp_path) and "viridis" in info["colormaps"]
    assert info["schema_version"].count(".") == 2
    assert info["defaults"]["g2_bounds"]["single"][0] == [0.04, 1e-5, 0.5, 0.95]
    assert client.get("/api/files").json() == {"files": [], "total": 0, "version": 1}
    assert client.get("/api/colormaps").json()["jet"][0][0] == 0
    page = client.get("/")
    assert page.status_code == 200 and "pyXPCSViewer" in page.text
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/api/files/missing.hdf/summary").status_code == 404
    assert client.get("/api/files/..%2Fx.hdf/summary").status_code in (400, 404)
    assert client.get("/api/info", headers={"Host": "evil.example.com"}).status_code == 400
    health = client.get("/api/health").json()
    assert health["name"] == "xpcs-viewer" and health["schema_version"] == info["schema_version"]
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


def test_binary_routes_over_the_real_files(multitau_path, twotime_path):
    client = TestClient(build_app(os.path.dirname(multitau_path)), base_url="http://localhost")
    mt = os.path.basename(multitau_path)
    tt = os.path.basename(twotime_path)

    data = client.get(f"/api/files/{mt}/image/data", params={"max_size": 256})
    z, meta = array_of(data), meta_of(data)
    assert z.shape == (240, 229) and z.dtype == np.float32
    assert (
        meta["factor"] == 9 and meta["x0"] == 4.0 and meta["shape_full"] == [2162, 2068] and meta["zmin"] < meta["zmax"]
    )
    assert client.get(f"/api/files/{mt}/image/meta", params={"max_size": 256}).json() == meta
    region = client.get(
        f"/api/files/{mt}/image/data", params={"max_size": 0, "x_min": 10, "x_max": 110, "y_min": 20, "y_max": 70}
    )
    assert array_of(region).shape == (50, 100)
    assert meta_of(region)["factor"] == 1 and meta_of(region)["x0"] == 10 and meta_of(region)["y0"] == 20
    assert client.get(f"/api/files/{mt}/image/data", params={"x_min": 1}).status_code == 400
    assert client.get(f"/api/files/{mt}/image/data", params={"kind": "nope"}).status_code == 400
    assert (
        array_of(client.get(f"/api/files/{mt}/image/data", params={"kind": "mask", "max_size": 256})).dtype == np.uint8
    )
    assert client.get(f"/api/files/{mt}/summary").json()["geometry"]["shape"] == [2162, 2068]

    g2 = client.get(f"/api/files/{mt}/g2/data")
    assert array_of(g2).shape == (2, 44, 36) and len(meta_of(g2)["t"]) == 44 and len(meta_of(g2)["labels"]) == 36
    narrow = client.get(f"/api/files/{mt}/g2/data", params={"q_min": 0.004, "q_max": 0.008})
    assert 0 < array_of(narrow).shape[2] < 36
    assert client.get(f"/api/files/{mt}/g2/meta").json()["q"] == meta_of(g2)["q"]
    assert client.get(f"/api/files/{tt}/g2/data").status_code == 400

    c2 = client.get(f"/api/files/{tt}/twotime/c2/data", params={"selection": 1, "max_size": 256})
    assert max(array_of(c2).shape) <= 256 and array_of(c2).dtype == np.float32 and meta_of(c2)["qbin"] == 2
    assert client.get(f"/api/files/{tt}/twotime/c2/meta", params={"selection": 1, "max_size": 256}).json() == meta_of(
        c2
    )
    rest = client.get(
        f"/api/files/{tt}/twotime/c2", params={"selection": 1, "max_size": 256, "include_c2": "false"}
    ).json()
    assert rest["c2"] is None and rest["g2_full"]["shape"] == [2000]


def test_fits_belong_to_the_page_and_run_as_jobs(multitau_path, twotime_path):
    import time

    client = TestClient(build_app(os.path.dirname(multitau_path)), base_url="http://localhost")
    mt = os.path.basename(multitau_path)
    tt = os.path.basename(twotime_path)
    assert client.post("/api/g2", json={"names": [mt]}, headers=PAGE_A).json()["files"][0]["fit"] is None

    started = client.post("/api/jobs/g2-fit", json={"names": [mt, tt], "fit_func": "single"}, headers=PAGE_A)
    assert started.status_code == 202 and started.json()["name"] == "g2 fit"
    job_id = started.json()["id"]
    deadline = time.monotonic() + 60
    while (state := client.get(f"/api/jobs/{job_id}").json())["status"] not in ("done", "failed", "cancelled"):
        assert time.monotonic() < deadline, state
        time.sleep(0.05)
    assert state["status"] == "done", state
    assert state["result"]["fitted"] == [mt] and state["result"]["skipped"][0]["file"] == tt
    assert state["done"] == state["total"] > 0

    fit = client.get(f"/api/files/{mt}/g2/fit", headers=PAGE_A).json()
    assert fit["func"] == "single" and len(fit["success"]) == 36
    assert (
        len(
            client.get(f"/api/files/{mt}/g2/fit", params={"q_min": 0.004, "q_max": 0.008}, headers=PAGE_A).json()[
                "success"
            ]
        )
        < 36
    )
    assert client.post("/api/g2", json={"names": [mt]}, headers=PAGE_A).json()["files"][0]["fit"]["func"] == "single"
    assert (
        client.post("/api/tauq", json={"names": [mt], "fit": True}, headers=PAGE_A).json()["files"][0]["fit"]["b"] < 0
    )
    # another page sees none of it
    assert client.post("/api/g2", json={"names": [mt]}, headers=PAGE_B).json()["files"][0]["fit"] is None
    assert client.get(f"/api/files/{mt}/g2/fit", headers=PAGE_B).json() is None
    assert (
        client.post("/api/tauq", json={"names": [mt]}, headers=PAGE_B)
        .json()["skipped"][0]["reason"]
        .endswith("fit g2 first")
    )
    # a bad request fails before a job starts
    assert (
        client.post("/api/jobs/g2-fit", json={"names": [mt], "bounds": [[1], [2]]}, headers=PAGE_A).status_code == 400
    )
    # a client without a session header (the old page, curl) gets a cookie and its own fits
    plain = client.post("/api/g2/fit", json={"names": [mt], "fit_func": "single"})
    assert plain.json()["files"][0]["fit"]["func"] == "single" and "webkit_session" in plain.cookies
