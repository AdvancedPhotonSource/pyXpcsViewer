# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""web.workspace on the real result files under tests/data/ (skipped without them)."""

import base64
import os

import numpy as np
import pytest

from pyxpcsviewer.web.workspace import Workspace, WorkspaceError

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


def _array(spec):
    dtype = {"f4": "<f4", "f8": "<f8", "i4": "<i4", "u1": "u1", "u2": "<u2"}[spec["dtype"]]
    return np.frombuffer(base64.b64decode(spec["bdata"]), dtype=dtype).reshape(spec["shape"])


@pytest.fixture(scope="module")
def workspace(multitau_path, twotime_path, both_path):
    return Workspace(os.path.dirname(multitau_path), cache_size=3)


@pytest.fixture(scope="module")
def names(multitau_path, twotime_path, both_path):
    return {
        "mt": os.path.basename(multitau_path),
        "tt": os.path.basename(twotime_path),
        "both": os.path.basename(both_path),
    }


def test_files_carry_their_analysis_types(workspace, names):
    rows = {row["id"]: row for row in workspace.files()}
    assert rows[names["mt"]]["atype"] == ["Multitau"]
    assert rows[names["tt"]]["atype"] == ["Twotime"]
    assert rows[names["both"]]["atype"] == ["Multitau", "Twotime"]
    assert rows[names["mt"]]["label"] == "D0131_multitau"
    assert workspace.count_files("multitau") == 1
    assert [r["id"] for r in workspace.files("multitau")] == [names["mt"]]
    newest = workspace.files(sort="time", reverse=True)[0]
    assert newest["mtime"] == max(r["mtime"] for r in rows.values())


def test_names_outside_the_folder_are_refused(workspace, names):
    with pytest.raises(WorkspaceError):
        workspace.path_of("../" + names["mt"])
    with pytest.raises(WorkspaceError, match="no such file"):
        workspace.open("missing.hdf")


def test_open_is_cached_and_bounded(workspace, names):
    first = workspace.open(names["mt"])
    assert workspace.open(names["mt"]) is first
    workspace.open(names["tt"])
    workspace.open(names["both"])
    assert len(workspace._open) <= 3


def test_summary_rows(workspace, names):
    rows = dict(workspace.summary(names["both"]))
    assert rows["Analysis"] == "Twotime, Multitau"
    assert rows["Detector"] == "2162 × 2068 px"  # noqa: RUF001
    assert "Two-time bins" in rows and "g2 delays" in rows
    assert "/entry/instrument" in workspace.hdf_info(names["mt"])


def test_image_is_downsampled_with_levels(workspace, names):
    image = workspace.image(names["mt"], max_size=1024)
    assert image["factor"] == 3 and image["shape"] == [720, 689] and image["shape_full"] == [2162, 2068]
    z = _array(image["z"])
    assert z.dtype == np.float32 and z.shape == (720, 689)
    levels = _array(image["levels"])
    assert levels.shape == (201,) and np.all(np.diff(levels) >= 0)
    assert image["zmin"] < image["zmax"]
    assert workspace.image(names["mt"], max_size=1024) is image  # cached
    linear = workspace.image(names["mt"], scale="linear", max_size=512)
    assert linear["factor"] == 5 and np.all(_array(linear["z"]) >= 0)
    dq = workspace.image(names["mt"], kind="dqmap", max_size=512)
    assert dq["scale"] == "linear" and np.nanmax(_array(dq["z"])) == 36
    mask = workspace.image(names["mt"], kind="mask", max_size=512)
    assert _array(mask["z"]).dtype == np.uint8
    with pytest.raises(WorkspaceError):
        workspace.image(names["mt"], kind="nope")


def test_pixel_readout(workspace, names):
    xf = workspace.open(names["mt"])
    p = workspace.pixel(names["mt"], xf.bcx, xf.bcy)
    assert p["on_detector"] and p["q"] < 1e-3 and p["x"] == round(xf.bcx)
    assert workspace.pixel(names["mt"], -5, 10)["on_detector"] is False
    rows, cols = np.nonzero(xf.dqmap)
    p = workspace.pixel(names["mt"], cols[0], rows[0])
    assert p["dq_bin"] == int(xf.dqmap[rows[0], cols[0]]) and p["dq_label"].startswith("q=")


def test_g2_fit_and_tauq(workspace, names):
    g2 = workspace.g2([names["mt"], names["tt"]])
    assert [f["file"] for f in g2["files"]] == [names["mt"]]
    assert [s["file"] for s in g2["skipped"]] == [names["tt"]]
    f = g2["files"][0]
    assert len(f["q"]) == 36 and _array(f["g2"]).shape == (44, 36) and _array(f["t"]).shape == (44,)
    assert f["fit"] is None
    assert workspace.tauq([names["mt"]])["skipped"][0]["reason"].endswith("fit g2 first")

    narrow = workspace.g2([names["mt"]], q_range=[0.004, 0.008], t_range=[1e-4, 1e-2])
    assert 0 < len(narrow["files"][0]["q"]) < 36 and _array(narrow["files"][0]["t"]).shape[0] < 44

    fitted = workspace.fit_g2([names["mt"]], None, None, fit_func="single")
    fit = fitted["files"][0]["fit"]
    assert fit["func"] == "single" and fit["param_names"] == ["a", "b", "c", "d"]
    assert any(fit["success"]) and _array(fit["fit_y"]).shape == (36, 128)
    assert all(len(p) == 4 for p in fit["params"] if p)

    tauq = workspace.tauq([names["mt"]], q_range=None, fit=True)
    entry = tauq["files"][0]
    assert entry["fit"] is not None and entry["fit"]["b"] < 0
    assert len(entry["q"]) == len(entry["tau"]) == len(entry["tau_err"])
    assert entry["params_vs_q"]["titles"][1] == "τ (s)"
    with pytest.raises(WorkspaceError):
        workspace.fit_g2([names["mt"]], None, None, bounds=[[1, 2], [3, 4]])


def test_saxs1d_stability_and_background(workspace, names):
    one = workspace.saxs1d([names["mt"]])
    assert _array(one["files"][0]["I"]).shape == (1, 360) and one["files"][0]["ylabel"].startswith("Intensity")
    normed = workspace.saxs1d([names["mt"]], norm="q2", q_range=[0.01, 0.03], sampling=2, all_phi=True)
    q = _array(normed["files"][0]["q"])
    assert q.min() >= 0.01 and q.max() <= 0.03 and "q^2" in normed["files"][0]["ylabel"]
    subtracted = workspace.saxs1d([names["mt"]], background=names["mt"], bkg_weight=1.0)
    values = _array(subtracted["files"][0]["I"])
    assert np.all(np.nan_to_num(values) == 0)
    stability = workspace.stability(names["mt"])
    assert _array(stability["I"]).shape == (9, 360) and stability["labels"][0] == "segment 1"
    with pytest.raises(WorkspaceError, match="partial g2"):
        workspace.g2_stability(names["mt"])


def test_intt(workspace, names):
    result = workspace.intt([names["mt"]], window=5, sampling=2)
    f = result["files"][0]
    assert f["frames"] == 5000 and _array(f["x"]).shape == (2498,) and _array(f["y"]).shape == (2498,)
    assert _array(f["fft_x"]).shape == (2500,)
    capped = workspace.intt([names["mt"]], max_points=1000)["files"][0]
    assert capped["points"] == 1000 and _array(capped["y"]).shape == (1000,)
    assert _array(capped["fft_y"]).shape == _array(capped["fft_x"]).shape and _array(capped["fft_y"]).shape[0] <= 1000
    assert np.isclose(_array(capped["y"]).mean(), _array(f["y"]).mean(), rtol=0.05)


def test_twotime(workspace, names):
    bins = workspace.twotime_bins(names["tt"])
    assert [b["qbin"] for b in bins["bins"]] == [1, 2, 3] and bins["bins"][0]["label"].startswith("qbin=1")
    c2 = workspace.twotime_c2(names["tt"], selection=1, max_size=256)
    assert c2["qbin"] == 2 and max(c2["shape"]) <= 256
    assert _array(c2["c2"]).shape == tuple(c2["shape"])
    assert _array(c2["g2_full"]).shape == (2000,) and _array(c2["g2_partial"]).shape == (5, 400)
    assert c2["delta_t"] == c2["acquire_period"] * (2000 // 256 + 1)
    xf = workspace.open(names["tt"])
    rows, cols = np.nonzero(xf.dqmap == 2)
    hit = workspace.twotime_bin_at(names["tt"], cols[0], rows[0])
    assert hit["qbin"] == 2 and hit["selection"] == 1
    assert workspace.twotime_bin_at(names["tt"], 0, 0)["selection"] is None
    with pytest.raises(WorkspaceError):
        workspace.twotime_c2(names["tt"], selection=7)
    with pytest.raises(WorkspaceError, match="no two-time"):
        workspace.twotime_bins(names["mt"])


def test_image_arrays_and_regions(workspace, names):
    z, meta = workspace.image_array(names["mt"], max_size=1024)
    assert z.shape == (720, 689) and meta["factor"] == 3 and meta["x0"] == 1.0
    # columns 4 .. 9 are covered by sent pixels 1 (4 // 3) up to 3 (10 / 3 rounded up, excluded)
    part, meta = workspace.image_array(names["mt"], max_size=1024, region=(4, 10, 0, 3))
    assert part.shape == (1, 3) and meta["x0"] == 4.0 and meta["y0"] == 1.0
    full, meta = workspace.image_array(names["mt"], max_size=0, region=(0, 5, 0, 2))
    assert full.shape == (2, 5) and meta["factor"] == 1 and meta["x0"] == 0.0 and meta["shape_full"] == [2162, 2068]
    with pytest.raises(WorkspaceError):
        workspace.image_array(names["mt"], region=(5, 5, 0, 1))
    with pytest.raises(WorkspaceError, match="outside"):
        workspace.image_array(names["mt"], region=(5000, 6000, 0, 1))
    geometry = workspace.geometry(names["mt"])
    assert workspace.image(names["mt"], max_size=1024)["beam_center"] == geometry["beam_center"]
    assert geometry["shape"] == [2162, 2068] and len(geometry["extent_q"]) == 4


def test_g2_and_c2_arrays(workspace, names):
    data, meta = workspace.g2_array(names["mt"])
    assert data.shape == (2, 44, 36) and data.dtype == np.float32
    assert len(meta["labels"]) == 36 and len(meta["t"]) == 44 and len(meta["q"]) == 36
    narrow, meta = workspace.g2_array(names["mt"], q_range=[0.004, 0.008])
    assert 0 < narrow.shape[2] < 36 and len(meta["q"]) == narrow.shape[2]
    with pytest.raises(WorkspaceError):
        workspace.g2_array(names["tt"])
    c2, meta = workspace.twotime_c2_array(names["tt"], selection=1, max_size=256)
    assert c2.dtype == np.float32 and max(c2.shape) <= 256 and meta["qbin"] == 2 and meta["zmin"] < meta["zmax"]
    assert workspace.twotime_c2(names["tt"], selection=1, max_size=256, include_c2=False)["c2"] is None
