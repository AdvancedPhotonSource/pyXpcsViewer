# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""The synthetic result files read back like a beamline result, through the core and the web API."""

import numpy as np
import pytest

from pyxpcsviewer.core.file_io.synthetic import main, write_synthetic_folder, write_synthetic_result
from pyxpcsviewer.core.xpcs_file import XpcsFile


def test_a_synthetic_file_reads_back(tmp_path):
    path = write_synthetic_result(tmp_path / "both.hdf", frames=120, nq=5, twotime_bins=2)
    xf = XpcsFile(str(path))
    assert set(xf.atype) == {"Multitau", "Twotime"}
    assert xf.saxs_2d.shape == (256, 240) and xf.dqmap.max() == 5
    q, t_el, g2, _g2_err, labels = xf.get_g2_data()
    assert len(q) == 5 and g2.shape == (t_el.size, 5) and labels[0].startswith("qbin=1, q=")
    assert np.all(g2[0] > g2[-1] + 0.01), "every bin decays within the delays"
    _, iq, _, _ = xf.get_saxs1d_data()
    assert iq.shape == (1, 5) and np.all(np.diff(iq[0]) < 0), "the intensity falls with q"
    assert xf.Iqp.shape[0] == 4
    c2 = xf.get_twotime_c2(selection=1, max_size=64)
    assert c2["c2_mat"].shape[0] <= 64 and c2["g2_full"].shape == (120,)
    assert xf.get_twotime_qbin_labels()[1].startswith("qbin=2")
    assert "/entry/instrument" in xf.get_hdf_info()


def test_the_folder_and_the_command(tmp_path, capsys):
    paths = write_synthetic_folder(tmp_path / "data", seed=3)
    assert [p.name.split("_")[-1] for p in paths] == ["multitau.hdf", "twotime.hdf", "both.hdf"]
    assert XpcsFile(str(paths[0])).atype == ("Multitau",)
    assert XpcsFile(str(paths[1])).atype == ("Twotime",)
    assert main([str(tmp_path / "cli")]) == 0
    assert "both.hdf" in capsys.readouterr().err


def test_the_web_api_over_synthetic_files(tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("beamline_webkit")
    from beamline_webkit.testing import array_of, client_for

    from pyxpcsviewer.web.app import build_app

    write_synthetic_folder(tmp_path)
    client = client_for(build_app(str(tmp_path)), raise_server_exceptions=True)
    files = client.get("/api/files").json()["files"]
    assert len(files) == 3 and files[2]["atype"] == ["Multitau", "Twotime"]
    both = files[2]["id"]
    assert client.get(f"/api/files/{both}/summary").json()["geometry"]["shape"] == [256, 240]
    assert array_of(client.get(f"/api/files/{both}/image/data", params={"max_size": 128})).shape == (128, 120)
    g2 = client.get(f"/api/files/{both}/g2/data")
    assert array_of(g2).shape[1:] == (31, 8)
    fit = client.post("/api/g2/fit", json={"names": [both], "fit_func": "single"}).json()
    assert sum(fit["files"][0]["fit"]["success"]) >= 6
    assert client.post("/api/tauq", json={"names": [both], "fit": True}).json()["files"][0]["fit"]["b"] < 0
    c2 = client.get(f"/api/files/{both}/twotime/c2/data", params={"selection": 0, "max_size": 128})
    assert array_of(c2).shape[0] <= 128
    assert client.post("/api/intt", json={"names": [both]}).json()["files"][0]["frames"] == 400
    assert client.get(f"/api/files/{both}/g2_stability").json()["g2"]["shape"][0] == 4
