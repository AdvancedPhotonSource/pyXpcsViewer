# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests exercising real XPCS result files (tests/data/, see conftest.py).

Focus: get_analysis_type and XpcsFile must branch correctly on the three
shapes a real result file takes -- Multitau-only, Twotime-only, and both --
loading the fields for the file's actual analysis type(s) and leaving the
fields for the *other* type as None.
"""

import pytest

from pyxpcsviewer.core.file_io.hdf_reader import get, get_analysis_type


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
