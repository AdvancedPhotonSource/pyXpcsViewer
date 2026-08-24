# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for XpcsFile.get_G2_data's partial HDF5 reads.

The unnormalized G2 cube is hundreds of MB, but displaying it needs one
detector frame, so get_G2_data must slice the dataset in the file rather than
load the whole thing into the XpcsFile.G2 cache. These call the method unbound
on a stand-in object: it only touches ``self.fname`` and the ``G2`` cache entry,
so no real (heavy) XpcsFile construction is needed.
"""

import types

import h5py
import numpy as np
import pytest

from pyxpcsviewer.core.file_io.aps_8idi import key as hdf_key
from pyxpcsviewer.core.xpcs_file import XpcsFile

G2_PATH = hdf_key["nexus"]["G2"]


@pytest.fixture
def g2_file(tmp_path):
    """A file with a (4 delays, 3 channels, 5x6) G2 cube; returns (path, cube)."""
    rng = np.random.default_rng(0)
    cube = rng.random((4, 3, 5, 6)).astype(np.float32)
    cube[2, 1, 0, 0] = 0.0  # zero denominator for the g2_per_pixel path
    cube[2, 2, 0, 0] = 0.0
    path = tmp_path / "g2.hdf"
    with h5py.File(path, "w") as f:
        f.create_dataset(G2_PATH, data=cube)
    return str(path), cube


def _stub(fname):
    return types.SimpleNamespace(fname=fname)


@pytest.mark.parametrize(("target", "channel"), [("G2", 0), ("IP", 1), ("IF", 2)])
def test_get_G2_data_reads_one_channel(g2_file, target, channel):
    fname, cube = g2_file
    stub = _stub(fname)
    np.testing.assert_array_equal(XpcsFile.get_G2_data(stub, target, 2), cube[2, channel])


def test_get_G2_data_does_not_fill_the_full_cube_cache(g2_file):
    """The point of the partial read: displaying must not pull in the whole cube."""
    fname, _ = g2_file
    stub = _stub(fname)
    XpcsFile.get_G2_data(stub, "G2", 0)
    assert "G2" not in stub.__dict__


def test_get_G2_data_clamps_delay_index(g2_file):
    fname, cube = g2_file
    np.testing.assert_array_equal(XpcsFile.get_G2_data(_stub(fname), "G2", 999), cube[-1, 0])


def test_get_G2_data_g2_per_pixel(g2_file):
    fname, cube = g2_file
    denominator = cube[2, 1] * cube[2, 2]
    denominator[denominator == 0] = 1
    expected = cube[2, 0] / denominator
    np.testing.assert_allclose(XpcsFile.get_G2_data(_stub(fname), "g2_per_pixel", 2), expected)
    assert np.isfinite(expected).all()  # the zeroed pixel must not divide by zero


def test_get_G2_data_uses_the_cache_when_already_loaded(g2_file):
    """With the cube cached (e.g. after a regroup), no file read happens at all."""
    _, cube = g2_file
    stub = _stub("/nonexistent/never-opened.hdf")
    stub.__dict__["G2"] = cube
    np.testing.assert_array_equal(XpcsFile.get_G2_data(stub, "IF", 1), cube[1, 2])


def test_get_G2_data_without_G2_field(tmp_path):
    path = tmp_path / "empty.hdf"
    with h5py.File(path, "w") as f:
        f.create_dataset("/xpcs/multitau/normalized_g2", data=np.ones((3, 2)))
    with pytest.raises(ValueError, match="no unnormalized G2 data"):
        XpcsFile.get_G2_data(_stub(str(path)), "G2", 0)
