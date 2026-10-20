# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests exercising real XPCS result files (tests/data/, see conftest.py).

Focus: get_analysis_type and XpcsFile must branch correctly on the three
shapes a real result file takes -- Multitau-only, Twotime-only, and both --
loading the fields for the file's actual analysis type(s) and leaving the
fields for the *other* type as None.
"""

import shutil

import h5py
import pytest

from pyxpcsviewer.core.file_io.aps_8idi import key as hdf_key
from pyxpcsviewer.core.file_io.hdf_reader import get, get_analysis_type
from pyxpcsviewer.core.xpcs_file import XpcsFile


def test_get_analysis_type_multitau_only(multitau_path):
    assert get_analysis_type(multitau_path) == ("Multitau",)


def test_get_analysis_type_twotime_only(twotime_path):
    assert get_analysis_type(twotime_path) == ("Twotime",)


def test_get_analysis_type_both(both_path):
    assert set(get_analysis_type(both_path)) == {"Multitau", "Twotime"}


def test_get_reads_raw_fields_via_alias(multitau_path):
    result = get(multitau_path, ["saxs_2d", "X_energy", "pix_dim_x"], mode="alias")
    assert result["saxs_2d"].ndim == 2
    assert result["X_energy"] > 0
    assert result["pix_dim_x"] > 0


def test_multitau_file_loads_multitau_fields_only(multitau_xf):
    xf = multitau_xf
    assert xf.atype == ("Multitau",)
    assert xf.g2 is not None and xf.g2_err is not None and xf.t_el is not None
    assert xf.c2_g2 is None and xf.c2_processed_bins is None
    assert xf.has_field("g2") is True
    assert xf.has_field("c2_g2") is False


def test_twotime_file_loads_twotime_fields_only(twotime_xf):
    xf = twotime_xf
    assert xf.atype == ("Twotime",)
    assert xf.c2_g2 is not None and xf.c2_processed_bins is not None
    assert xf.g2 is None and xf.g2_err is None and xf.t_el is None
    assert xf.has_field("c2_g2") is True
    assert xf.has_field("g2") is False


def test_both_file_loads_all_fields(both_xf):
    xf = both_xf
    assert set(xf.atype) == {"Multitau", "Twotime"}
    assert xf.g2 is not None and xf.c2_g2 is not None
    assert xf.has_field("g2") is True
    assert xf.has_field("c2_g2") is True


def test_get_g2_data_shapes_match_across_multitau_files(multitau_xf, both_xf):
    for xf in (multitau_xf, both_xf):
        q_val, t_el, g2, g2_err, labels = xf.get_g2_data()
        assert g2.shape == (t_el.size, q_val.size)
        assert g2_err.shape == g2.shape
        assert len(labels) == q_val.size


def test_twotime_c2_matrix_is_square_and_matches_frame_count(twotime_xf, both_xf):
    for xf in (twotime_xf, both_xf):
        labels = xf.get_twotime_qbin_labels()
        assert len(labels) == len(xf.c2_processed_bins)

        c2 = xf.get_twotime_c2(selection=0)
        n_frames = xf.Int_t.shape[1]
        assert c2["c2_mat"].shape == (n_frames, n_frames)


@pytest.mark.parametrize("fixture_name", ["multitau_xf", "twotime_xf", "both_xf"])
def test_common_fields_present_regardless_of_analysis_type(fixture_name, request):
    xf = request.getfixturevalue(fixture_name)
    assert xf.saxs_2d.shape == xf.mask.shape
    assert xf.saxs_1d["Iq"].shape[1] == xf.saxs_1d["q"].shape[0]
    assert xf.Int_t.shape[0] == 2
    assert xf.label


def _copy_without(src, tmp_path, *fields):
    """Copy *src* into *tmp_path* with the given alias fields deleted; returns the new path."""
    path = tmp_path / "copy.hdf"
    shutil.copy(src, path)
    with h5py.File(path, "a") as f:
        for field in fields:
            del f[hdf_key["nexus"][field]]
    return str(path)


@pytest.mark.parametrize("field", ["start_time", "t1", "static_num_pts"])
def test_file_without_unused_field_still_loads(multitau_path, tmp_path, field):
    """No view reads these fields, so a file lacking one must still load, with the value as None."""
    xf = XpcsFile(_copy_without(multitau_path, tmp_path, field))
    assert getattr(xf, field) is None
    assert xf.g2 is not None


def test_twotime_file_without_stride_avg_config_assumes_no_striding(twotime_path, tmp_path):
    path = _copy_without(twotime_path, tmp_path, "c2_stride_frame", "c2_avg_frame")
    frame_time = get(path, ["t0"], "alias", ftype="nexus")["t0"]
    assert XpcsFile(path).c2_t0 == pytest.approx(frame_time)


def test_twotime_c2_time_step_includes_twotime_stride(twotime_path, tmp_path):
    """The C2 image and its g2 trace are scaled by frame_time * twotime stride * avg."""
    path = tmp_path / "stride2.hdf"
    shutil.copy(twotime_path, path)
    with h5py.File(path, "a") as f:
        f[hdf_key["nexus"]["c2_stride_frame"]][()] = 2
    frame_time = get(str(path), ["t0"], "alias", ftype="nexus")["t0"]

    c2 = XpcsFile(str(path)).get_twotime_c2(selection=0)
    assert c2["acquire_period"] == pytest.approx(2 * frame_time)
