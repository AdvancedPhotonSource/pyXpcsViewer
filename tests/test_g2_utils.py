# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for pyxpcsviewer.core.g2_utils.compute_g2_debug_bundle.

The bundle is what the G2 outlier debug dialog plots. It must mirror
compute_g2's preprocessing (dead-pixel masking, normalize_g2) and its
outlier pass (find_g2_pixel_outliers) exactly, so the dialog shows what
ReGroup actually sees.
"""

import numpy as np

from pyxpcsviewer.core.g2_utils import compute_g2_debug_bundle, find_g2_pixel_outliers, normalize_g2


def make_data():
    """(2 delays, 3 ch, 4x4) synthetic G2 with known outliers.

    Flat pixel index = row*4+col:
      0  = (0,0): IF1=IF2=0 at every delay -> dead
      15 = (3,3): g2_pixel=10 at delay 0 only (sq 2)
      8  = (2,0): g2_pixel=10 at delay 1 only (sq 2)
    sq 1 = rows 0-1 (pixels 0-7), sq 2 = rows 2-3 (pixels 8-15); single dq bin.
    """
    IP = np.ones((2, 4, 4), dtype=np.float32)
    IP[0, 3, 3] = 10.0
    IP[1, 2, 0] = 10.0
    IF = np.ones((2, 4, 4), dtype=np.float32)
    IF[:, 0, 0] = 0.0
    G2 = np.stack([IP, IF, IF], axis=1).astype(np.float32)  # (2, 3, 4, 4)
    sqmap = np.zeros((4, 4), dtype=np.uint16)
    sqmap[:2, :] = 1
    sqmap[2:, :] = 2
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap


def test_bundle_shapes():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    assert b["g2_pixel"].shape == (2, 16)
    assert b["g2_pixel"].dtype == np.float32
    assert b["bad"].shape == (2, 16)
    assert b["bad"].dtype == bool
    assert b["img_shape"] == (4, 4)
    assert b["n_delays"] == 2
    assert b["n_sq"] == 2
    assert b["n_dq"] == 1
    assert b["n_dead"] == 1


def test_bundle_dead_pixel_masked():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    assert b["sqmap_1d"][0] == 0  # dead pixel removed from its sq bin
    assert b["dqmap_1d"][0] == 0
    assert (b["sqmap_1d"][1:] != 0).all()
    assert sqmap[0, 0] == 1  # input not mutated


def test_bundle_g2_pixel_matches_normalize_g2():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    n_delays, n_channels, _, _ = G2.shape
    expected = normalize_g2(G2.reshape(n_delays, n_channels, -1))
    np.testing.assert_allclose(b["g2_pixel"], expected)


def test_bundle_bad_matches_outlier_pass():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, outlier_method="MeanAbsoluteDeviation")
    expected = find_g2_pixel_outliers(b["sqmap_1d"], b["g2_pixel"], threshold=3.0, method="MeanAbsoluteDeviation")
    np.testing.assert_array_equal(b["bad"], expected)
    assert b["bad"].sum() == 2
    assert b["bad"][0, 15]
    assert b["bad"][1, 8]


def test_bundle_known_outliers():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0)
    # bin of seven 1s + one 10: median 1, MAD 0 -> clamped to 1, hi = 1+3 = 4
    assert b["bad"][0, 15]
    assert b["bad"][1, 8]
    assert not b["bad"][0, 0]  # dead pixels are out of all sq bins
    b100 = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=100.0)
    assert b100["bad"].sum() == 0


def test_bundle_combine_outlier_union():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, combine_outlier=True)
    # sq 2 union = {8, 15} -> both flagged at every delay; sq 1 unaffected
    assert b["bad"][0, 8] and b["bad"][0, 15]
    assert b["bad"][1, 8] and b["bad"][1, 15]
    assert b["bad"].sum() == 4
